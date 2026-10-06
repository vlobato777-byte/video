#!/usr/bin/env python3
"""Condo Lua — reel renderer.

Builds the vertical 1080x1920 Reels ad from the editable project file
(project/condo_lua_reel.json): photos and video clips with gentle motion,
clean cuts or short dissolves, per-shot colour balance, captions kept inside
the Reels safe zone and an optional licensed music bed.

Missing sources are replaced by labelled placeholder cards, so the timing and
the captions can be reviewed before all the footage is available.

Usage
  python3 tools/render_reel.py                     # versions A and B, final quality
  python3 tools/render_reel.py --version A --preview --guides
  python3 tools/render_reel.py --storyboard        # contact sheet PNG
  python3 tools/render_reel.py --overlays          # caption PNGs + SRT for CapCut/Canva
  python3 tools/render_reel.py --check             # validate the project only

Requires Python 3.9+, Pillow, numpy and ffmpeg/ffprobe (with zscale for HDR).
"""

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECT = ROOT / "project" / "condo_lua_reel.json"
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic", ".heif"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}

# BT.2020 -> BT.709 primaries, linear light.
BT2020_TO_709 = np.array([[1.6605, -0.5876, -0.0728],
                          [-0.1246, 1.1329, -0.0083],
                          [-0.0182, -0.1006, 1.1187]], np.float32)
LUMA_709 = np.array([0.2126, 0.7152, 0.0722], np.float32)


# --------------------------------------------------------------------------- helpers

def warn(msg):
    print(f"  ! {msg}", file=sys.stderr)


def rgba(value):
    s = value.lstrip("#")
    if len(s) == 6:
        s += "FF"
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4, 6))


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def ease_out(p):
    p = clamp(p, 0.0, 1.0)
    return 1 - (1 - p) ** 3


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


# --------------------------------------------------------------------------- colour

def merge_grade(look, grade):
    g = dict(look)
    for k, v in (grade or {}).items():
        g[k] = g.get(k, 1.0) * v if k in ("contrast", "saturation") else g.get(k, 0.0) + v
    return g


def grade_lut(g):
    """Per-channel LUT: exposure + white balance in linear light, then tone shaping."""
    x = np.arange(256, dtype=np.float64) / 255.0
    lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    temp, tint = g.get("temperature", 0.0), g.get("tint", 0.0)
    gains = (1 + 0.08 * temp, 1 - 0.05 * tint, 1 - 0.08 * temp)
    expo = 2.0 ** g.get("exposure", 0.0)
    lut = []
    for gain in gains:
        y = np.clip(lin * expo * gain, 0, 1)
        y = np.where(y <= 0.0031308, 12.92 * y, 1.055 * y ** (1 / 2.4) - 0.055)
        y = 0.5 + (y - 0.5) * g.get("contrast", 1.0)
        y = y + g.get("shadows", 0.0) * 0.25 * (y * (1 - y) ** 3) / 0.105
        y = y + g.get("highlights", 0.0) * 0.25 * (y ** 3 * (1 - y)) / 0.105
        lut.extend(np.clip(np.round(y * 255), 0, 255).astype(int).tolist())
    return lut


def apply_grade(img, g, lut):
    img = img.point(lut)
    sat = g.get("saturation", 1.0)
    return ImageEnhance.Color(img).enhance(sat) if abs(sat - 1.0) > 1e-3 else img


def hdr_to_sdr(lin2020, knee=0.75):
    """Linear BT.2020 (already tone mapped) -> 8-bit sRGB/BT.709 with soft gamut compression."""
    rgb = lin2020 @ BT2020_TO_709.T
    y = np.maximum((rgb @ LUMA_709)[..., None], 1e-6)
    s = (y - rgb.min(-1, keepdims=True)) / y          # 1.0 = gamut boundary
    sc = np.where(s > knee, knee + (1 - knee) * np.tanh((s - knee) / (1 - knee)), s)
    rgb = np.where(s > knee, y - (y - rgb) * (sc / np.maximum(s, 1e-6)), rgb)
    x = np.clip(rgb, 0, 1)
    x = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    return (x * 255 + 0.5).astype(np.uint8)


# --------------------------------------------------------------------------- geometry

def base_window(src_w, src_h, aspect):
    """Largest rectangle with the output aspect (w/h) that fits in the source."""
    if src_w / src_h > aspect:
        return src_h * aspect, src_h
    return src_w, src_w / aspect


def window(src_w, src_h, aspect, cx, cy, zoom):
    bw, bh = base_window(src_w, src_h, aspect)
    zoom = max(zoom, 1.0)
    w, h = bw / zoom, bh / zoom
    x0 = clamp(cx * src_w - w / 2, 0, src_w - w)
    y0 = clamp(cy * src_h - h / 2, 0, src_h - h)
    return x0, y0, w, h


# --------------------------------------------------------------------------- sources

def probe_video(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,color_transfer:stream_side_data=rotation:stream_tags=rotate:format=duration",
         "-of", "json", str(path)], capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    st = info["streams"][0]
    w, h = st["width"], st["height"]
    rot = int(float(st.get("tags", {}).get("rotate", 0)))
    for sd in st.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if abs(rot) % 180 == 90:
        w, h = h, w
    hdr = st.get("color_transfer") in ("arib-std-b67", "smpte2084")
    return w, h, float(info["format"]["duration"]), hdr


def placeholder_image(shot, W, H):
    """Storyboard card shown while the real footage is missing."""
    w, h = int(W * 1.25), int(H * 1.25)
    top, bottom = np.array(rgba("#C9B79C")[:3]), np.array(rgba("#7E6650")[:3])
    t = np.linspace(0, 1, h)[:, None, None]
    grad = (top * (1 - t) + bottom * t).astype(np.uint8)
    img = Image.fromarray(np.broadcast_to(grad, (h, w, 3)).copy())
    d = ImageDraw.Draw(img)
    s = W / 1080
    f_small = ImageFont.truetype(str(ROOT / "assets/fonts/Inter-SemiBold.otf"), int(34 * s))
    f_title = ImageFont.truetype(str(ROOT / "assets/fonts/Inter-Bold.otf"), int(64 * s))
    f_need = ImageFont.truetype(str(ROOT / "assets/fonts/Inter-Medium.otf"), int(38 * s))
    ph = shot.get("placeholder", {})
    x, y = w * 0.5, h * 0.70
    d.text((x, y), "MATERIAL PENDIENTE · " + shot["id"], font=f_small, fill=(255, 245, 230), anchor="ms")
    d.text((x, y + 80 * s), ph.get("title", shot["id"]), font=f_title, fill=(255, 255, 255), anchor="ms")
    words, lines, cur = ph.get("need", "").split(), [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if d.textlength(test, font=f_need) > W * 0.78:
            lines.append(cur)
            cur = word
        else:
            cur = test
    if cur:
        lines.append(cur)
    for i, line in enumerate(lines):
        d.text((x, y + (150 + i * 52) * s), line, font=f_need, fill=(255, 248, 238), anchor="ms")
    return img


class ShotSource:
    """Produces graded, framed W x H frames for one shot at any timeline time."""

    def __init__(self, shot, ctx):
        self.shot, self.ctx = shot, ctx
        self.start, self.end = shot["start"], shot["end"]
        self.dur = self.end - self.start
        self.pre = self.post = 0.0
        self.trans = shot.get("transition_in", {"type": "cut"})
        self.path = resolve(shot["source"]) if shot.get("source") else None
        self.draft = False
        if not (self.path and self.path.exists()) and shot.get("draft") and resolve(shot["draft"]).exists():
            self.path, self.draft = resolve(shot["draft"]), True   # interim still from the WhatsApp edit
        self.missing = not (self.path and self.path.exists())
        self.kind = "photo" if self.missing or self.path.suffix.lower() in PHOTO_EXT else "video"
        self.grade = merge_grade(ctx["look"], shot.get("grade"))
        self.lut = grade_lut(self.grade)
        self.img = None
        self.proc = None
        self.shade = self._shade_mask(shot.get("shade"))

    # -- framing --------------------------------------------------------------
    def _zoom_range(self):
        z0, z1 = self.shot["from"]["zoom"], self.shot["to"]["zoom"]
        return max(1.0, min(z0, z1) / 1.03)

    def _frame_at(self, tau):
        a, b = self.shot["from"], self.shot["to"]
        p = tau / self.dur if self.dur > 0 else 0.0
        cx = a["cx"] + (b["cx"] - a["cx"]) * p
        cy = a["cy"] + (b["cy"] - a["cy"]) * p
        zoom = a["zoom"] * (b["zoom"] / a["zoom"]) ** p
        return cx, cy, zoom

    def _shade_mask(self, shade):
        if not shade:
            return None
        W, H = self.ctx["W"], self.ctx["H"]
        y = (np.arange(H) / H)[:, None]
        a = shade["amount"] * np.exp(-((y - shade.get("center_y", 0.4)) / shade.get("spread", 0.3)) ** 2)
        a = a + shade.get("base", 0.0)
        mask = np.broadcast_to(np.clip(a * 255, 0, 255).astype(np.uint8), (H, W))
        return Image.fromarray(mask.copy(), "L")

    def _scale_for(self, src_w, src_h):
        W, H = self.ctx["W"], self.ctx["H"]
        bw, _ = base_window(src_w, src_h, W / H)
        k = W / (bw / self._zoom_range())
        if k > 1.15:
            warn(f"{self.shot['id']}: source is {k:.2f}x smaller than needed - may look soft")
        return k

    # -- photo ----------------------------------------------------------------
    def _load_photo(self):
        if self.missing:
            img = placeholder_image(self.shot, self.ctx["W"], self.ctx["H"])
        else:
            if self.path.suffix.lower() in (".heic", ".heif"):
                try:
                    import pillow_heif
                    pillow_heif.register_heif_opener()
                except ImportError:
                    sys.exit(f"{self.path.name}: install pillow-heif or export the photo as JPG")
            img = ImageOps.exif_transpose(Image.open(self.path)).convert("RGB")
        k = self._scale_for(*img.size)
        size = (max(1, round(img.width * k)), max(1, round(img.height * k)))
        img = img.resize(size, Image.LANCZOS)
        self.img = img if self.missing else apply_grade(img, self.grade, self.lut)

    # -- video ----------------------------------------------------------------
    def _open_video(self, tau):
        w, h, dur, hdr = probe_video(self.path)
        k = self._scale_for(w, h)
        self.vw, self.vh = max(2, round(w * k / 2) * 2), max(2, round(h * k / 2) * 2)
        self.hdr = hdr
        src_in = self.shot.get("source_in", 0.0)
        seek = max(0.0, src_in + tau)
        self.v_t0 = seek - src_in            # shot-local time of the first decoded frame
        fps = self.ctx["fps"]
        if hdr:
            tm = self.shot.get("tonemap", "mobius:param=0.3")
            vf = (f"fps={fps},zscale=t=linear:npl=203,format=gbrpf32le,tonemap={tm}:desat=0,"
                  f"zscale=w={self.vw}:h={self.vh}:f=lanczos")
            pix, self.bpf = "gbrpf32le", self.vw * self.vh * 12
        else:
            vf = f"fps={fps},scale={self.vw}:{self.vh}:flags=lanczos"
            pix, self.bpf = "rgb24", self.vw * self.vh * 3
        span = self.dur + self.post - tau + 0.5
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{seek:.3f}", "-i", str(self.path), "-t", f"{span:.3f}",
             "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix, "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)  # closed early on purpose
        self.v_idx, self.v_frame = -1, None
        if src_in + self.dur + self.post > dur + 0.01:
            warn(f"{self.shot['id']}: clip is shorter than the shot - last frame will hold")

    def _read_video(self, tau):
        n = round((tau - self.v_t0) * self.ctx["fps"]) if self.proc else -1
        if self.proc is None or n < self.v_idx:
            self.close()
            self._open_video(tau)
            n = 0
        while self.v_idx < n:
            raw = self.proc.stdout.read(self.bpf)
            if len(raw) < self.bpf:
                break
            self.v_idx += 1
            if self.hdr:
                planes = np.frombuffer(raw, np.float32).reshape(3, self.vh, self.vw)
                arr = hdr_to_sdr(np.stack([planes[2], planes[0], planes[1]], -1))
            else:
                arr = np.frombuffer(raw, np.uint8).reshape(self.vh, self.vw, 3)
            self.v_frame = apply_grade(Image.fromarray(arr), self.grade, self.lut)
        if self.v_frame is None:
            sys.exit(f"{self.shot['id']}: could not decode {self.path}")
        return self.v_frame

    # -- public ---------------------------------------------------------------
    def frame(self, t):
        tau = t - self.start
        if self.kind == "photo":
            if self.img is None:
                self._load_photo()
            src = self.img
        else:
            src = self._read_video(tau)
        W, H = self.ctx["W"], self.ctx["H"]
        cx, cy, zoom = self._frame_at(tau)
        x0, y0, w, h = window(src.width, src.height, W / H, cx, cy, zoom)
        out = src.transform((W, H), Image.AFFINE, (w / W, 0, x0, 0, h / H, y0), resample=Image.BICUBIC)
        if self.shade is not None:
            out = Image.composite(Image.new("RGB", (W, H), (20, 14, 10)), out, self.shade)
        return out

    def close(self):
        if self.proc:
            self.proc.stdout.close()
            self.proc.kill()
            self.proc.wait()
            self.proc = None


# --------------------------------------------------------------------------- captions

_FONTS = {}


def load_font(style, S):
    key = (style["font"], style.get("weight"), round(style["size"] * S))
    if key not in _FONTS:
        f = ImageFont.truetype(str(resolve(style["font"])), key[2])
        if style.get("weight"):          # variable fonts: wght axis (300-700)
            f.set_variation_by_axes([style["weight"]])
        _FONTS[key] = f
    return _FONTS[key]


def render_line(text, style, S):
    """Return (RGBA layer, content box (x, y, w, h) inside the layer)."""
    font = load_font(style, S)
    size = style["size"] * S
    lines = text.split("\n")
    if style.get("uppercase"):
        lines = [ln.upper() for ln in lines]
    track = style.get("tracking", 0.0) * size

    def width(s):
        if not track:
            return font.getlength(s)
        return sum(font.getlength(ch) for ch in s) + track * (len(s) - 1)

    cap = -font.getbbox("H", anchor="ls")[1]
    desc = font.getbbox("gjpy", anchor="ls")[3]
    lh = size * style.get("line_height", 1.15)
    cw = max(width(s) for s in lines)
    ch = cap + desc + lh * (len(lines) - 1)

    pill = style.get("pill")
    glow = style.get("glow", 0.0)
    if pill:
        px, py = pill["pad_x"] * S, pill["pad_y"] * S
        bw, bh = cw + 2 * px, cap + 2 * py + lh * (len(lines) - 1)
        pad = 24 * S
        lw, lh_ = int(bw + 2 * pad), int(bh + 2 * pad)
        layer = Image.new("RGBA", (lw, lh_), (0, 0, 0, 0))
        shadow = Image.new("L", (lw, lh_), 0)
        ImageDraw.Draw(shadow).rounded_rectangle((pad, pad + 4 * S, pad + bw, pad + bh + 4 * S),
                                                 radius=bh / 2 if len(lines) == 1 else 24 * S, fill=90)
        shadow = shadow.filter(ImageFilter.GaussianBlur(10 * S))
        layer.paste((10, 6, 4, 255), (0, 0), shadow)
        box = Image.new("RGBA", (lw, lh_), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle((pad, pad, pad + bw, pad + bh),
                                              radius=bh / 2 if len(lines) == 1 else 24 * S,
                                              fill=rgba(pill["fill"]))
        layer = Image.alpha_composite(layer, box)
        ox, oy = pad + px, pad + py
        content = (pad, pad, bw, bh)
    else:
        pad = int(size * (1.2 if glow else 0.3))
        lw, lh_ = int(cw + 2 * pad), int(ch + 2 * pad)
        layer = Image.new("RGBA", (lw, lh_), (0, 0, 0, 0))
        ox, oy = pad, pad
        content = (pad, pad, cw, ch)

    mask = Image.new("L", layer.size, 0)
    d = ImageDraw.Draw(mask)
    for i, s in enumerate(lines):
        x = ox + (cw - width(s)) / 2
        y = oy + cap + i * lh
        if track:
            for chr_ in s:
                d.text((x, y), chr_, font=font, fill=255, anchor="ls")
                x += font.getlength(chr_) + track
        else:
            d.text((x, y), s, font=font, fill=255, anchor="ls")

    if glow and not pill:
        soft = mask.filter(ImageFilter.GaussianBlur(size * 0.42)).point(lambda v: min(255, int(v * 2.4 * glow)))
        tight = mask.filter(ImageFilter.GaussianBlur(max(2, size * 0.05)))
        tight = ImageChops.offset(tight, 0, int(max(1, size * 0.03))).point(lambda v: int(v * 0.65))
        dark = ImageChops.lighter(soft, tight)
        shade = Image.new("RGBA", layer.size, (22, 15, 10, 255))
        shade.putalpha(dark)
        layer = Image.alpha_composite(layer, shade)

    fill = Image.new("RGBA", layer.size, rgba(style["color"]))
    fill.putalpha(mask)
    layer = Image.alpha_composite(layer, fill)
    return layer, content


class CaptionLine:
    def __init__(self, layer, x, y, content, start, end, fade_in, fade_out, rise):
        self.layer, self.x, self.y, self.content = layer, x, y, content
        self.start, self.end = start, end
        self.fade_in, self.fade_out, self.rise = fade_in, fade_out, rise
        self.alpha = layer.getchannel("A")

    def opacity(self, t):
        if t < self.start or t >= self.end:
            return 0.0, 0.0
        a_in = ease_out((t - self.start) / self.fade_in) if self.fade_in > 0 else 1.0
        a_out = clamp((self.end - t) / self.fade_out, 0, 1) if self.fade_out > 0 else 1.0
        return min(a_in, a_out), (1 - a_in) * self.rise

    def draw(self, frame, t):
        op, dy = self.opacity(t)
        if op <= 0.003:
            return
        mask = self.alpha if op >= 0.997 else self.alpha.point(lambda v: int(v * op))
        frame.paste(self.layer.convert("RGB"), (int(self.x), int(round(self.y + dy))), mask)


def build_captions(proj, S, W, H, check=True):
    styles, safe = proj["styles"], proj["safe_zone"]
    sx0, sx1 = W * safe["side"], W * (1 - safe["side"])
    sy0, sy1 = H * safe["top"], H * (1 - safe["bottom"])
    out = []
    for cap in proj["captions"]:
        rendered = [(ln, *render_line(ln["text"], styles[ln["style"]], S)) for ln in cap["lines"]]
        heights = [c[3] for _, _, c in rendered]
        gaps = [0] + [ln.get("gap_before", cap.get("gap", 24)) * S for ln, _, _ in rendered[1:]]
        total = sum(heights) + sum(gaps)
        y = cap["y"] * H - total / 2
        for (ln, layer, content), g in zip(rendered, gaps):
            y += g
            cx_, cy_, cw, ch = content
            x = (W - cw) / 2 - cx_
            top = y - cy_
            if check and (x + cx_ < sx0 - 1 or x + cx_ + cw > sx1 + 1 or y < sy0 - 1 or y + ch > sy1 + 1):
                warn(f"caption {cap['id']} '{ln['text'][:24]}' leaves the Reels safe zone")
            start = cap["start"] + ln.get("delay", 0.0)
            out.append(CaptionLine(layer, x, top, (cap["id"], ln["text"]), start, cap["end"],
                                   cap.get("fade_in", 0.35), cap.get("fade_out", 0.22), cap.get("rise", 14) * S))
            y += ch
    return out


def guides_layer(proj, W, H):
    safe = proj["safe_zone"]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    red = (230, 40, 40, 70)
    top, bot, side = H * safe["top"], H * (1 - safe["bottom"]), W * safe["side"]
    d.rectangle((0, 0, W, top), fill=red)
    d.rectangle((0, bot, W, H), fill=red)
    d.rectangle((0, top, side, bot), fill=red)
    d.rectangle((W - side, top, W, bot), fill=red)
    f = ImageFont.truetype(str(ROOT / "assets/fonts/Inter-SemiBold.otf"), int(H * 0.016))
    d.text((W / 2, top / 2), "Zona de interfaz de Reels (no poner texto)", font=f, fill=(255, 255, 255, 200), anchor="mm")
    d.text((W / 2, bot + (H - bot) / 2), "Zona de interfaz de Reels (no poner texto)", font=f, fill=(255, 255, 255, 200), anchor="mm")
    return layer


# --------------------------------------------------------------------------- timeline

def shots_for(proj, version):
    shots = sorted((s for s in proj["shots"] if s.get("only") in (None, version)), key=lambda s: s["start"])
    return shots


def validate(proj):
    ok = True
    dur = proj["output"]["duration"]
    for v in proj["versions"]:
        shots = shots_for(proj, v)
        if abs(shots[0]["start"]) > 1e-6 or abs(shots[-1]["end"] - dur) > 1e-6:
            warn(f"version {v}: shots must cover 0-{dur}s")
            ok = False
        for a, b in zip(shots, shots[1:]):
            if abs(a["end"] - b["start"]) > 1e-6:
                warn(f"version {v}: gap/overlap between {a['id']} and {b['id']}")
                ok = False
    for s in proj["shots"]:
        if s.get("source") and resolve(s["source"]).exists():
            continue
        if s.get("draft") and resolve(s["draft"]).exists():
            warn(f"{s['id']}: original missing ({s.get('source')}) - using draft still from WhatsApp")
        else:
            warn(f"{s['id']}: no source - placeholder card ({s.get('source')})")
    return ok


def make_sources(proj, version, ctx):
    srcs = [ShotSource(s, ctx) for s in shots_for(proj, version)]
    for a, b in zip(srcs, srcs[1:]):
        if b.trans.get("type") == "dissolve":
            d = b.trans.get("duration", 0.2)
            a.post, b.pre = d / 2, d / 2
    return srcs


def compose(srcs, t):
    active = [s for s in srcs if s.start - s.pre <= t < s.end + s.post]
    if not active:
        active = [srcs[-1]]
    if len(active) == 1:
        return active[0].frame(t)
    a, b = active[0], active[1]
    d = b.pre * 2
    alpha = clamp((t - (b.start - b.pre)) / d, 0, 1)
    return Image.blend(a.frame(t), b.frame(t), alpha)


# --------------------------------------------------------------------------- audio

def build_audio(proj, dur, tmp):
    m = proj.get("music") or {}
    wav = Path(tmp) / "music.wav"
    if not m.get("file"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", f"{dur}", str(wav)], check=True)
        return wav
    src = resolve(m["file"])
    if not src.exists():
        sys.exit(f"music file not found: {src}")
    fo = m.get("fade_out", 2.5)
    base = (f"atrim=0:{dur},asetpts=N/SR/TB,afade=t=in:d={m.get('fade_in', 0.4)},"
            f"afade=t=out:st={dur - fo}:d={fo}")
    target = m.get("target_lufs", -14.0)
    inp = ["-stream_loop", "-1", "-ss", f"{m.get('offset', 0.0)}", "-i", str(src)]
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-y", *inp, "-af",
                           f"{base},loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True, check=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-af", f"{base},{ln},aresample=48000",
                    "-ac", "2", "-t", f"{dur}", str(wav)], check=True)
    return wav


# --------------------------------------------------------------------------- outputs

def render_version(proj, version, args, out_path):
    o = proj["output"]
    S = 0.5 if args.preview else 1.0
    W, H, fps, dur = int(o["width"] * S), int(o["height"] * S), o["fps"], o["duration"]
    ctx = {"W": W, "H": H, "fps": fps, "look": proj.get("look", {})}
    srcs = make_sources(proj, version, ctx)
    caps = build_captions(proj, S, W, H)
    guides = guides_layer(proj, W, H) if args.guides else None
    n = int(round(dur * fps))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = build_audio(proj, dur, tmp)
        enc = ["-c:v", "libx264", "-preset", "veryfast" if args.preview else "slow",
               "-crf", "23" if args.preview else "16", "-profile:v", "high",
               "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-framerate", str(fps), "-i", "-", "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
               "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", *enc,
               "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{dur}", "-movflags", "+faststart",
               str(out_path)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            t = i / fps
            frame = compose(srcs, t)
            for c in caps:
                c.draw(frame, t)
            if guides:
                frame.paste(guides.convert("RGB"), (0, 0), guides)
            proc.stdin.write(frame.tobytes())
            for s in srcs:
                if s.proc and t >= s.end + s.post:
                    s.close()
            if i % fps == 0:
                print(f"\r  {version}: {t:5.1f}/{dur:.0f}s", end="", flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            sys.exit("ffmpeg encode failed")
    for s in srcs:
        s.close()
    print(f"\r  {version}: done -> {out_path.relative_to(ROOT)}")


def render_storyboard(proj, out_path):
    o = proj["output"]
    S = 0.5
    W, H = int(o["width"] * S), int(o["height"] * S)
    ctx = {"W": W, "H": H, "fps": o["fps"], "look": proj.get("look", {})}
    caps = build_captions(proj, S, W, H, check=False)
    tiles = []
    b_open = [s for s in proj["shots"] if s.get("only") == "B"]
    for version, shots in (("A", shots_for(proj, "A")), ("B", b_open)):
        srcs = make_sources(proj, version, ctx) if version == "A" else [ShotSource(s, ctx) for s in shots]
        for src in srcs:
            t = src.start + min(src.dur * 0.6, max(src.dur - 0.3, 0))
            # show the caption state at its fullest within the shot
            frame = src.frame(t)
            for c in caps:
                if c.start <= t:
                    c.draw(frame, max(t, c.start + 0.6) if c.start + 0.6 < c.end else t)
            tag = f"{'B · ' if version == 'B' else ''}{src.start:g}–{src.end:g} s · {src.shot['id']}"
            tiles.append((frame, tag))
            src.close()
    tw, th = W // 2, H // 2
    cols = 5
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * (tw + 16) + 16, rows * (th + 56) + 16), (246, 241, 233))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(str(ROOT / "assets/fonts/Inter-Medium.otf"), 17)
    for i, (frame, tag) in enumerate(tiles):
        x, y = 16 + (i % cols) * (tw + 16), 16 + (i // cols) * (th + 56)
        sheet.paste(frame.resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 10), tag, font=f, fill=(60, 45, 35))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    print(f"  storyboard -> {out_path.relative_to(ROOT)}")


def export_overlays(proj, out_dir):
    o = proj["output"]
    W, H = o["width"], o["height"]
    out_dir.mkdir(parents=True, exist_ok=True)
    caps = build_captions(proj, 1.0, W, H, check=False)
    srt = []
    for i, cap in enumerate(proj["captions"], 1):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for c in caps:
            if c.content[0] == cap["id"]:
                layer.alpha_composite(c.layer, (int(c.x), int(round(c.y))))
        name = f"{i:02d}_{cap['id']}_{cap['start']:05.2f}-{cap['end']:05.2f}s.png"
        layer.save(out_dir / name)

        def ts(x):
            ms = int(round(x * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        text = "\n".join(ln["text"].replace("\n", " ") for ln in cap["lines"])
        srt.append(f"{i}\n{ts(cap['start'])} --> {ts(cap['end'])}\n{text}\n")
    (out_dir / "textos_en_pantalla.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"  overlays -> {out_dir.relative_to(ROOT)}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=str(DEFAULT_PROJECT))
    ap.add_argument("--version", choices=["A", "B", "all"], default="all")
    ap.add_argument("--preview", action="store_true", help="half resolution, fast encode")
    ap.add_argument("--guides", action="store_true", help="draw the Reels safe-zone guides")
    ap.add_argument("--storyboard", action="store_true")
    ap.add_argument("--overlays", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out-dir", default=str(ROOT / "exports"))
    args = ap.parse_args()

    proj = json.loads(Path(args.project).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    print(proj["project"])
    ok = validate(proj)
    if args.check:
        build_captions(proj, 1.0, proj["output"]["width"], proj["output"]["height"])
        sys.exit(0 if ok else 1)
    if not ok:
        sys.exit("fix the timeline first")
    if args.storyboard:
        render_storyboard(proj, out_dir / "storyboard.png")
    if args.overlays:
        export_overlays(proj, out_dir / "overlays")
    if args.storyboard or args.overlays:
        return
    versions = list(proj["versions"]) if args.version == "all" else [args.version]
    for v in versions:
        name = proj["versions"][v]["file"]
        if args.preview:
            name += "_preview"
        if args.guides:
            name += "_guias"
        render_version(proj, v, args, out_dir / f"{name}.mp4")


if __name__ == "__main__":
    main()
