#!/usr/bin/env python3
"""Laboratorio de dibujo sensorial: reel 30 s (1080 x 1920).

Builds the reel described in laboratorio-dibujo-sensorial/reel.json:

- photo shots of the conceptual studio scenes (media/escenas/) with a slow
  camera move; one charcoal drawing is laid onto the paper roll in
  perspective, behind hands and arms, and keeps every earlier layer;
- macro shots rendered straight from that same drawing, so the layers
  accumulate and never disappear between shots;
- captions on cream labels (Barlow Condensed / DM Sans) inside the Reels
  safe zone;
- closing card on cream paper with the workshop data (datos.json) and logo;
- original procedural music plus the sound of charcoal on paper.

Usage
  python3 tools/reel_laboratorio.py               # final MP4 + review copy
  python3 tools/reel_laboratorio.py --preview     # half resolution, fast
  python3 tools/reel_laboratorio.py --guides      # draw the Reels safe zone
  python3 tools/reel_laboratorio.py --stills      # cover, storyboard and text layers only
"""

import argparse
import json
import math
import subprocess
import sys
import tempfile
import wave
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sonido_lab as snd  # noqa: E402
import trazos as tz  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "laboratorio-dibujo-sensorial"
OUT = PROJECT / "exports" / "reel"

SHEET = (900, 2600)                 # paper roll in sheet units (~90 x 260 cm)
PAPEL_MACRO = (228, 219, 210)        # roll paper seen up close
SAFE_TOP, SAFE_BOTTOM, SAFE_SIDE = 0.14, 0.35, 0.06

# Paper corners in each photo (TL, TR, BR, BL), in source pixels, and the
# charcoal tip where a stroke has to arrive.
ESCENAS = {
    "rollo_gesto": {"quad": [(440, 225), (880, 205), (790, 1560), (345, 1470)], "punta": (663, 318)},
    "rollo_pausa": {"quad": [(485, 90), (1250, -28), (1062, 2182), (297, 2300)]},
    "rollo_amplio": {"quad": [(432, 225), (828, 195), (780, 1395), (378, 1335)]},
    "textura": {},
}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def font(path, size):
    return ImageFont.truetype(str(ROOT / path), max(1, int(round(size))))


def homography(src, dst):
    """Coefficients (a..h) that map src points to dst points (PIL PERSPECTIVE order)."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float))


def apply_h(h, x, y):
    d = h[6] * x + h[7] * y + 1
    return (h[0] * x + h[1] * y + h[2]) / d, (h[3] * x + h[4] * y + h[5]) / d


def sheet_corners(scale=1.0):
    w, h = SHEET[0] * scale, SHEET[1] * scale
    return [(0, 0), (w, 0), (w, h), (0, h)]


# --------------------------------------------------------------------------- drawing

def llegar(pts, tip, frac=0.06):
    """Bend the last part of a path so it ends exactly at the charcoal tip."""
    pts = np.array(pts, float)
    n = len(pts)
    k = max(2, int(n * frac))
    w = tz.smoothstep(np.linspace(0, 1, k))[:, None]
    pts[-k:] = pts[-k:] * (1 - w) + (pts[-k:] + (np.array(tip) - pts[-1])) * w
    pts[-1] = tip
    return pts


def dibujo():
    """The one drawing of the reel, in sheet units, with absolute times.

    Two kinds of marks, each with its own handwriting:
    - answers to a sound: rhythmic, with accents, oscillations and staccato;
    - answers to a texture touched with the eyes covered: searching, broken,
      hesitant lines that turn suddenly.
    All of them carry the tremor of the hand, uneven speed and pressure.
    """
    rng = np.random.default_rng(8)
    quad = ESCENAS["rollo_gesto"]["quad"]
    h = homography(quad, sheet_corners())
    tip = apply_h(h, *ESCENAS["rollo_gesto"]["punta"])
    S = []

    # 1 · sound: the gesture that opens the reel, drawn with the edge of the
    #     charcoal; it sweeps, presses on the accents, trembles and ends
    #     at her hand
    ctrl = [(150, 2060), (300, 1850), (470, 1620), (640, 1360), (520, 1130), (290, 1010),
            (260, 800), (430, 650), (560, 470), (515, 330), tip]
    base = tz.hand(tz.spline(ctrl, 900), 20, rng, cell=90)
    pts = llegar(tz.pulso(base, rng, amp=4.8, wl=24, micro=1.7), tip)
    n = len(pts)
    pres = (tz.presion_ritmo(n, [0.1, 0.13, 0.35, 0.39, 0.57, 0.6, 0.85], rng, base=0.72, acento=0.55, ancho=0.02)
            * tz.presion_titubeo(n, rng, base=1.0, saltos=3, var=0.22))
    S.append(tz.Stroke(pts, "punta", 17, pres, t0=0.06, dur=3.8, ease="mano", pausas=2, seed=101, taper=0.03,
                       grosor=tz.grosor_giro(n, rng, 0.3, 1.7, cell=n / 18)))

    # 2 · texture with the eyes covered: mapping the bark that was touched —
    #     fissures along the trunk, lost and found again, and ridges across
    t = 10.6
    for k, path in enumerate(tz.corteza(480, 1380, 380, 450, rng, lineas=7)):
        pts = tz.pulso(path, rng, amp=1.3, wl=15, micro=0.8)
        if len(pts) < 3:
            continue
        n = len(pts)
        ridge = n < 40
        d = (0.06 if ridge else 0.2) + rng.uniform(0, 0.05)
        S.append(tz.Stroke(pts, "punta", rng.uniform(4.5, 6.5) if ridge else rng.uniform(6, 10),
                           tz.presion_titubeo(n, rng, base=0.9, saltos=0 if ridge else 2, var=0.3),
                           t0=t, dur=d, ease="mano", pausas=1, seed=150 + k, taper=0.12,
                           grosor=tz.grosor_giro(n, rng, 0.6, 1.4)))
        t += d * 0.58

    # 3 · sound: a beat heard — dots and dashes of different weight ...
    path = tz.pulso(tz.spline([(110, 1090), (260, 1050), (420, 1120), (575, 1075)], 300), rng, amp=6, wl=60)
    seg = np.hypot(*np.diff(path, axis=0).T)
    arc = np.concatenate([[0], np.cumsum(seg)])
    ritmo = [("p", 1.0), ("p", 0.7), ("r", 1.6), ("p", 0.9), ("r", 2.4), ("p", 0.6), ("p", 0.6),
             ("p", 1.1), ("r", 1.3), ("p", 0.8), ("r", 3.0), ("p", 1.0), ("p", 0.7)]
    total = sum(v for _, v in ritmo) + 0.6 * len(ritmo)
    pos, t = 0.0, 13.2
    for i, (kind, v) in enumerate(ritmo):
        a0 = pos / total * arc[-1]
        a1 = (pos + v) / total * arc[-1]
        x0, y0 = np.interp(a0, arc, path[:, 0]), np.interp(a0, arc, path[:, 1])
        if kind == "p":
            S.append(tz.Stroke([(x0 + rng.normal(0, 3), y0 + rng.normal(0, 5))], "punto", 14 + 16 * v,
                               min(1.3, 0.6 + 0.5 * v), t0=t, dur=0.01, ease="lineal", seed=130 + i))
            t += 0.06 + 0.06 * v
        else:
            x1, y1 = np.interp(a1, arc, path[:, 0]), np.interp(a1, arc, path[:, 1]) + rng.normal(0, 6)
            dash = tz.pulso(tz.spline([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + rng.normal(0, 4)), (x1, y1)], 40),
                            rng, amp=1.5, wl=12, micro=0.9)
            S.append(tz.Stroke(dash, "carbon", 15, tz.presion_ritmo(len(dash), [0.05], rng, 0.75, 0.6, 0.08),
                               t0=t, dur=0.1 * v, ease="gesto", seed=130 + i, taper=0.15))
            t += 0.1 * v + 0.05
        pos += v + 0.6
    # ... and a line that shivers after each beat, like a sound ringing out
    golpes = [(0.1, 1.0), (0.24, 0.6), (0.33, 0.9), (0.52, 0.5), (0.6, 1.0), (0.78, 0.7), (0.88, 0.45)]
    x = np.linspace(100, 590, 900)
    f = (x - 100) / 490
    y = 1238 + 9 * tz.noise1d(len(x), 160, rng)
    for b, s_ in golpes:
        g = np.clip(f - b, 0, None)
        lam = rng.uniform(0.007, 0.012)
        y += (34 * s_ * np.exp(-g / rng.uniform(0.02, 0.04)) * np.sin(2 * np.pi * g / lam + 0.3)
              * (f >= b) * (0.7 + 0.3 * rng.random()))
    pts = tz.pulso(np.stack([x, y], 1), rng, amp=1.3, wl=18, micro=0.9)
    n = len(pts)
    S.append(tz.Stroke(pts, "punta", 5.5, tz.presion_ritmo(n, [b for b, _ in golpes], rng, 0.5, 0.7, 0.02),
                       ink="grafito", t0=13.45, dur=1.45, ease="mano", pausas=1, seed=104, taper=0.03))

    # 4 · a sensation: very fine lines that fall like threads in the wind,
    #     one of them a discreet olive
    hilos = [(300, 330, 760), (390, 300, 900), (470, 360, 680), (560, 320, 820), (640, 380, 640), (250, 420, 560)]
    for k, (x, y, largo) in enumerate(hilos):
        pts = tz.pulso(tz.hilo(x, y, largo, rng, viento=rng.uniform(0.7, 1.3)), rng, amp=0.8, wl=10, micro=0.5)
        n = len(pts)
        olivo = k == 3
        S.append(tz.Stroke(pts, "grafito" if not olivo else "punta", rng.uniform(1.6, 2.6) if not olivo else 3.2,
                           tz.presion_titubeo(n, rng, base=0.55 if not olivo else 0.8, saltos=2, var=0.25),
                           ink="grafito" if not olivo else "olivo", t0=15.3 + 0.2 * k, dur=rng.uniform(0.9, 1.3),
                           ease="mano", pausas=1, seed=160 + k, taper=0.1))
        S[-1].t0, S[-1].dur = 15.25 + 0.15 * k, min(S[-1].dur, 1.6 - 0.15 * k)

    # 5 · a memory: a terracotta loop retraced as it is remembered
    pts = tz.pulso(tz.lazo(380, 545, 120, 88, 2.3, rng, drift=(130, -50), wobble=0.3, phase=2.2),
                   rng, amp=3.0, wl=40, micro=1.0)
    n = len(pts)
    S.append(tz.Stroke(pts, "carbon", 20, tz.presion_titubeo(n, rng, base=1.2, saltos=3, var=0.35),
                       ink="terracota", t0=17.15, dur=1.6, ease="mano", pausas=3, seed=107, taper=0.06,
                       grosor=tz.grosor_giro(n, rng, 0.55, 1.2)))

    # 6 · sound again: a fast, nervous line with sharp turns that arrives at her hand
    ctrl = [(860, 2380), (720, 1830), (880, 1520), (760, 1260), (840, 1050), (640, 830),
            (700, 640), (570, 500), tip]
    pts = tz.vibra(tz.hand(tz.spline(ctrl, 500), 10, rng), rng, amp=6, onda=(28, 110))
    pts = llegar(tz.pulso(pts, rng, amp=3.5, wl=26, micro=1.2), tip)
    n = len(pts)
    S.append(tz.Stroke(pts, "punta", 14, tz.presion_ritmo(n, [0.15, 0.33, 0.4, 0.58, 0.77, 0.86], rng, 0.8, 0.6),
                       t0=19.2, dur=2.1, ease="mano", pausas=2, seed=108, taper=0.03,
                       grosor=tz.grosor_giro(n, rng, 0.6, 1.3)))
    return S


def cierre_trazos(S):
    """Charcoal detail and terracotta accent of the closing card, in output pixels."""
    rng = np.random.default_rng(31)
    out = []
    ctrl = [(-60, 1560), (180, 1440), (420, 1530), (600, 1660), (820, 1520), (1000, 1420), (1160, 1470)]
    base = tz.hand(tz.spline([(x * S, y * S) for x, y in ctrl], 600), 10 * S, rng)
    pts = tz.pulso(base, rng, amp=3 * S, wl=30 * S, micro=1.0 * S, step=1.5 * S)
    n = len(pts)
    out.append(tz.Stroke(pts, "punta", 18 * S, tz.presion_ritmo(n, [0.2, 0.45, 0.7], rng, 1.0, 0.4, 0.03),
                         t0=24.05, dur=1.35, ease="mano", pausas=1, seed=201, taper=0.04,
                         grosor=tz.grosor_giro(n, rng, 0.35, 1.5)))
    pts = tz.pulso(tz.hilo(900 * S, 1300 * S, 520 * S, rng, viento=0.8 * S, step=2.5 * S), rng,
                   amp=0.8 * S, wl=10 * S, micro=0.5 * S, step=1.5 * S)
    out.append(tz.Stroke(pts, "grafito", 2.2 * S, tz.presion_titubeo(len(pts), rng, 0.6, 2, 0.25), ink="grafito",
                         t0=24.6, dur=1.2, ease="mano", pausas=1, seed=203, taper=0.1))
    return out


# --------------------------------------------------------------------------- canvases

def factor_image(canvas):
    """Multiply factor (paper = 1) for the charcoal on a canvas, as an RGB image."""
    f = np.ones((canvas.h, canvas.w, 3), np.float32)
    for ink, (color, _, _) in tz.INKS.items():
        a = canvas.coverage(ink)
        if a is None:
            continue
        c = np.array(color, np.float32) / 232.0
        f *= 1 - a[..., None] + a[..., None] * c
    return Image.fromarray(np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8))


class Hoja:
    """The paper roll in sheet space, shared by all photo shots."""

    def __init__(self, strokes, scale=1.0):
        self.scale = scale
        self.canvas = tz.Canvas(int(SHEET[0] * scale), int(SHEET[1] * scale), scale, paper_seed=21)
        self.strokes = strokes
        self.state = None
        self.img = None

    def at(self, t):
        state = tuple(round(s.progress(t), 4) for s in self.strokes)
        if state != self.state:
            for s, p in zip(self.strokes, state):
                if p > 0:
                    self.canvas.draw(s, p)
            self.state = state
            self.img = factor_image(self.canvas)
        return self.img


def paper_mask(img, quad):
    """Where the paper is visible (not hands, arms or clothes), feathered."""
    a = img.astype(np.float32)
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    m = np.clip((lum - 105) / 55, 0, 1) * np.clip((0.21 - sat) / 0.07, 0, 1)
    poly = Image.new("L", (img.shape[1], img.shape[0]), 0)
    ImageDraw.Draw(poly).polygon([tuple(p) for p in quad], fill=255)
    poly = np.asarray(poly.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    m = Image.fromarray((m * poly * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(m, np.float32)[..., None] / 255


def window(sw, sh, aspect, cx, cy, zoom):
    bw, bh = (sh * aspect, sh) if sw / sh > aspect else (sw, sw / aspect)
    w, h = bw / zoom, bh / zoom
    x0 = min(max(cx * sw - w / 2, 0), sw - w)
    y0 = min(max(cy * sh - h / 2, 0), sh - h)
    return x0, y0, w, h


class Pulso:
    """Small handheld drift so the stills breathe like a camera on a shoulder."""

    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        self.k = rng.uniform(0, 2 * math.pi, 6)

    def __call__(self, t):
        k = self.k
        dx = 0.0016 * math.sin(1.3 * t + k[0]) + 0.0008 * math.sin(2.9 * t + k[1])
        dy = 0.0014 * math.sin(1.1 * t + k[2]) + 0.0007 * math.sin(3.3 * t + k[3])
        dz = 0.004 * math.sin(0.7 * t + k[4])
        return dx, dy, dz


class Foto:
    def __init__(self, toma, hoja, W, H):
        self.toma, self.hoja, self.W, self.H = toma, hoja, W, H
        esc = ESCENAS[toma["escena"]]
        self.img = np.asarray(Image.open(PROJECT / "media" / "escenas" / f"{toma['escena']}.jpg").convert("RGB"))
        self.ih, self.iw = self.img.shape[:2]
        self.quad = esc.get("quad")
        if self.quad:
            self.mask = paper_mask(self.img, self.quad)
            self.coef = homography(self.quad, sheet_corners(hoja.scale))
        self.base = self.img.astype(np.float32)
        self.pulso = Pulso(zlib.crc32(toma["id"].encode()))

    def frame(self, t):
        if self.quad:
            f = self.hoja.at(t).transform((self.iw, self.ih), Image.PERSPECTIVE, tuple(self.coef),
                                          Image.BICUBIC, fillcolor=(255, 255, 255))
            f = np.asarray(f.filter(ImageFilter.GaussianBlur(0.5)), np.float32) / 255
            src = self.base * (1 - self.mask * (1 - f))
            src = Image.fromarray(np.clip(src + 0.5, 0, 255).astype(np.uint8))
        else:
            src = Image.fromarray(self.img)
        a, b = self.toma["de"], self.toma["a"]
        p = (t - self.toma["inicio"]) / (self.toma["fin"] - self.toma["inicio"])
        dx, dy, dz = self.pulso(t)
        cx = a[0] + (b[0] - a[0]) * p + dx
        cy = a[1] + (b[1] - a[1]) * p + dy
        zoom = a[2] * (b[2] / a[2]) ** p * (1 + dz) + 0.01
        x0, y0, w, h = window(self.iw, self.ih, self.W / self.H, cx, cy, zoom)
        out = src.transform((self.W, self.H), Image.AFFINE, (w / self.W, 0, x0, 0, h / self.H, y0),
                            resample=Image.BICUBIC)
        return out.filter(ImageFilter.UnsharpMask(radius=1.4 * self.W / 1080, percent=45, threshold=2))


class Macro:
    """A close shot of the drawing itself, on paper like the roll's."""

    def __init__(self, toma, strokes, W, H):
        self.toma, self.strokes, self.W, self.H = toma, strokes, W, H
        u0, v0, u1 = toma["region"][:3]
        self.scale = W / (u1 - u0)
        du, dv = toma.get("deriva", [0, 0])
        m = 12
        ox, oy = u0 - max(0, -du) - m, v0 - max(0, -dv) - m
        cw = int((u1 - u0 + abs(du) + 2 * m) * self.scale)
        ch = int((H / self.scale + abs(dv) + 2 * m) * self.scale)
        self.origin = (ox, oy)
        self.view0 = ((u0 - ox) * self.scale, (v0 - oy) * self.scale)
        self.drift = (du * self.scale, dv * self.scale)
        self.canvas = tz.Canvas(cw, ch, self.scale, paper_seed=33, paper_strength=1.0,
                                tone=PAPEL_MACRO, origin=self.origin)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        light = 1.05 - 0.10 * (xx / W * 0.6 + yy / H * 0.4)
        vig = 1 - 0.20 * ((xx / W - 0.5) ** 2 + (yy / H - 0.45) ** 2) * 2.2
        self.light = (light * vig)[..., None]
        self.pulso = Pulso(zlib.crc32(toma["id"].encode()) + 7)

    def frame(self, t):
        for s in self.strokes:
            p = s.progress(t)
            if p > 0:
                self.canvas.draw(s, p)
        p = (t - self.toma["inicio"]) / (self.toma["fin"] - self.toma["inicio"])
        dx, dy, _ = self.pulso(t)
        x = self.view0[0] + self.drift[0] * p + dx * self.W * 0.6
        y = self.view0[1] + self.drift[1] * p + dy * self.H * 0.6
        x = min(max(x, 0), self.canvas.w - self.W)
        y = min(max(y, 0), self.canvas.h - self.H)
        img = self.canvas.compose().crop((int(x), int(y), int(x) + self.W, int(y) + self.H))
        a = np.asarray(img, np.float32) * self.light
        warm = np.array([1.0, 0.985, 0.955], np.float32)
        return Image.fromarray(np.clip(a * warm + 0.5, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------- text

def runs(text, base, accent):
    """Split text so the punctuation takes the terracotta accent."""
    out = []
    for ch in text:
        col = accent if ch in "¿?.,¡!" else base
        if out and out[-1][1] == col:
            out[-1][0] += ch
        else:
            out.append([ch, col])
    return out


def label(text, style, cfg, S, size=None):
    """Cream label with charcoal text: RGBA image and the label box inside it."""
    pal = {k: rgb(v) for k, v in cfg["paleta"].items()}
    T = cfg["tipografia"]
    if style == "titulo":
        size = (size or 100) * S
        f, lh = font(T["titulos"], size), 1.0
    else:
        size = (size or 54) * S
        f, lh = font(T["cuerpo_semi"], size), 1.2
    lines = text.split("\n")
    widths = [f.getlength(ln) for ln in lines]
    asc = -f.getbbox("ÁH", anchor="ls")[1]
    desc = f.getbbox("gjpy,", anchor="ls")[3]
    step = size * lh
    px, py = 38 * S, 24 * S
    bw = max(widths) + 2 * px
    bh = asc + desc + step * (len(lines) - 1) + 2 * py
    pad = int(28 * S)
    img = Image.new("RGBA", (int(bw + 2 * pad), int(bh + 2 * pad)), (0, 0, 0, 0))
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 6 * S, pad + bw, pad + bh + 6 * S), radius=8 * S, fill=70)
    sh = sh.filter(ImageFilter.GaussianBlur(12 * S))
    img.paste((20, 16, 12, 255), (0, 0), sh)
    box = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((pad, pad, pad + bw, pad + bh), radius=8 * S,
                                          fill=pal["crema"] + (244,))
    img = Image.alpha_composite(img, box)
    d = ImageDraw.Draw(img)
    for i, (ln, w) in enumerate(zip(lines, widths)):
        x = pad + (bw - w) / 2
        y = pad + py + asc + i * step
        for chunk, col in runs(ln, pal["carbon"], pal["terracota"]):
            d.text((x, y), chunk, font=f, fill=col + (255,), anchor="ls")
            x += f.getlength(chunk)
    return img


def nota(text, cfg, S):
    """Small 'Imágenes ilustrativas' tag, like the one on the flyer."""
    pal = {k: rgb(v) for k, v in cfg["paleta"].items()}
    f = font(cfg["tipografia"]["cuerpo_medio"], 24 * S)
    w, h = int(f.getlength(text) + 30 * S), int(40 * S)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h / 2, fill=pal["carbon"] + (150,))
    d.text((w / 2, h / 2), text, font=f, fill=pal["crema"] + (255,), anchor="mm")
    return img


class Texto:
    def __init__(self, spec, cfg, W, H, S):
        self.spec = spec
        self.img = label(spec["texto"], spec.get("estilo", "titulo"), cfg, S, spec.get("tam"))
        self.x = (W - self.img.width) / 2
        self.y = spec["y"] * S - self.img.height / 2
        self.rise = 14 * S
        self.alpha = self.img.getchannel("A")

    def draw(self, frame, t):
        s, e = self.spec["inicio"], self.spec["fin"]
        if t < s or t >= e:
            return
        a_in = smooth((t - s) / 0.24)
        a = min(a_in, min(1.0, (e - t) / 0.18))
        if a <= 0.003:
            return
        y = self.y + (1 - a_in) * self.rise
        mask = self.alpha if a > 0.997 else self.alpha.point(lambda v: int(v * a))
        frame.paste(self.img.convert("RGB"), (int(self.x), int(round(y))), mask)


# --------------------------------------------------------------------------- closing card

class Cierre:
    def __init__(self, toma, cfg, reel, W, H, S):
        self.toma, self.W, self.H, self.S = toma, W, H, S
        pal = {k: rgb(v) for k, v in cfg["paleta"].items()}
        T, dat, c = cfg["tipografia"], cfg["datos"], reel["cierre"]
        self.canvas = tz.Canvas(W, H, 1.0, paper_seed=11, paper_strength=0.55, tone=pal["crema"])
        self.strokes = cierre_trazos(S)
        x = 96 * S
        layers = []

        def layer():
            return Image.new("RGBA", (W, H), (0, 0, 0, 0))

        logo = Image.open(PROJECT / "media" / "logo" / "concentrica.png").convert("RGBA")
        k = 340 * S / logo.width
        logo = logo.resize((int(logo.width * k), int(logo.height * k)), Image.LANCZOS)
        L = layer()
        L.paste(logo, (int(x), int(300 * S)), logo)
        layers.append((24.2, L))

        fb = font(T["titulos"], 168 * S)
        for i, ln in enumerate(c["frase"].split("\n")):
            L = layer()
            ImageDraw.Draw(L).text((x, (566 + i * 156) * S), ln, font=fb, fill=pal["carbon"] + (255,), anchor="ls")
            layers.append((24.35 + 0.3 * i, L))
        traza_w = fb.getlength(c["frase"].split("\n")[-1])

        L = layer()
        ImageDraw.Draw(L).text((x, 990 * S), c["nombre"], font=font(T["titulos"], 62 * S),
                               fill=pal["terracota"] + (255,), anchor="ls")
        layers.append((25.45, L))

        L = layer()
        d = ImageDraw.Draw(L)
        d.text((x, 1064 * S), dat["fecha"], font=font(T["cuerpo_negrita"], 42 * S), fill=pal["carbon"] + (255,), anchor="ls")
        d.text((x, 1114 * S), f"{dat['sede']} · {dat['ciudad']}", font=font(T["cuerpo_medio"], 37 * S),
               fill=pal["carbon"] + (255,), anchor="ls")
        layers.append((25.8, L))

        L = layer()
        d = ImageDraw.Draw(L)
        d.rounded_rectangle((x, 1146 * S, W - x, 1232 * S), radius=10 * S, fill=pal["terracota"] + (255,))
        d.text((W / 2, 1203 * S), c["reserva"].format(whatsapp=dat["whatsapp"]), font=font(T["cuerpo_negrita"], 40 * S),
               fill=pal["crema"] + (255,), anchor="ms")
        layers.append((26.2, L))
        self.layers = layers

        rng = np.random.default_rng(5)
        y = 908 * S
        pts = tz.hand(tz.spline([(x - 4 * S, y + 4 * S), (x + traza_w * 0.4, y + 8 * S), (x + traza_w * 0.8, y),
                                 (x + traza_w + 30 * S, y - 12 * S)], 200), 1.5 * S, rng)
        pts = tz.pulso(pts, rng, amp=1.6 * S, wl=22 * S, micro=0.7 * S, step=1.5 * S)
        n = len(pts)
        self.strokes.append(tz.Stroke(pts, "carbon", 15 * S, tz.presion_titubeo(n, rng, 1.0, 1, 0.25),
                                      ink="terracota", t0=25.05, dur=0.6, ease="mano", pausas=1, seed=202,
                                      taper=0.12, grosor=tz.grosor_giro(n, rng, 0.6, 1.25)))

    def frame(self, t):
        for s in self.strokes:
            p = s.progress(t)
            if p > 0:
                self.canvas.draw(s, p)
        img = self.canvas.compose().convert("RGBA")
        for t0, L in self.layers:
            a = smooth((t - t0) / 0.4)
            if a <= 0:
                continue
            if a < 1:
                L = L.copy()
                L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))
            img.alpha_composite(L)
        return img.convert("RGB")

    def text_layer(self):
        out = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        for _, L in self.layers:
            out.alpha_composite(L)
        return out


# --------------------------------------------------------------------------- audio

def audio(reel, strokes, cierre, tomas, dur, path):
    n = int(dur * snd.RATE)
    fps = 200
    times = np.arange(int(dur * fps)) / fps
    speed = np.zeros(len(times))
    taps = []
    tool_gain = {"carbon": 1.0, "punta": 0.55, "grafito": 0.35}
    for toma in tomas:
        gain = {"macro": 1.0, "foto": 0.5, "cierre": 0.8}.get(toma["tipo"], 0)
        if not gain:
            continue
        sel = (times >= toma["inicio"]) & (times < toma["fin"])
        pool = cierre.strokes if toma["tipo"] == "cierre" else strokes
        for s in pool:
            if s.tool == "punto":
                if s.t0 < toma["fin"] and s.t1 > toma["inicio"]:
                    k = len(s.pts)
                    for i in range(k):
                        ti = s.t0 + s.dur * i / max(1, k - 1)
                        if toma["inicio"] <= ti < toma["fin"]:
                            taps.append((ti, gain))
                continue
            sp = np.array([s.speed(t, 1 / fps) for t in times[sel]])
            speed[sel] += sp * tool_gain[s.tool] * gain
    level = np.interp(np.arange(n) / snd.RATE, times, speed)
    roce = snd.roce(level)
    for ti, g in taps:
        tap = snd.toque(int(ti * 1000)) * 0.9 * g
        i = int(ti * snd.RATE)
        roce[i:i + len(tap)] += tap[:max(0, n - i)]
    music = snd.musica(dur, bpm=reel["musica"]["bpm"])
    duck = np.clip(np.interp(np.arange(n) / snd.RATE, times, speed) / 900, 0, 1)
    duck = 1 - 0.3 * np.convolve(duck, np.ones(4800) / 4800, "same")
    mix = music[:n] * duck[:, None] * 0.9 + np.stack([roce, roce], 1) * np.array([0.62, 0.58])
    mix = np.clip(mix / max(1e-6, np.abs(mix).max()) * 0.9, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(snd.RATE)
        w.writeframes((mix * 32767).astype("<i2").tobytes())


def loudnorm(src, dst, target):
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", str(src), "-af",
                           f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True, check=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f"{ln},aresample=48000", str(dst)], check=True)


# --------------------------------------------------------------------------- assembly

class Reel:
    def __init__(self, S=1.0):
        self.cfg = json.loads((PROJECT / "datos.json").read_text(encoding="utf-8"))
        self.reel = json.loads((PROJECT / "reel.json").read_text(encoding="utf-8"))
        o = self.reel["salida"]
        self.S = S
        self.W, self.H = int(o["ancho"] * S), int(o["alto"] * S)
        self.fps, self.dur = o["fps"], o["duracion"]
        self.strokes = dibujo()
        self.hoja = Hoja(self.strokes)
        self.tomas = self.reel["tomas"]
        self.textos = [Texto(s, self.cfg, self.W, self.H, S) for s in self.reel["textos"]]
        self.shots = {}
        self.cierre = None
        self.nota = nota(self.reel["nota_imagenes"], self.cfg, S) if self.reel.get("nota_imagenes") else None
        self.check()

    def check(self):
        t = 0.0
        for toma in self.tomas:
            if abs(toma["inicio"] - t) > 1e-6:
                sys.exit(f"gap/overlap before {toma['id']}")
            t = toma["fin"]
        if abs(t - self.dur) > 1e-6:
            sys.exit("shots must cover the whole reel")
        top, bottom = self.H * SAFE_TOP, self.H * (1 - SAFE_BOTTOM)
        for tx in self.textos:
            if tx.y + 28 * self.S < top or tx.y + tx.img.height - 28 * self.S > bottom or tx.x < self.W * SAFE_SIDE - 28 * self.S:
                print(f"  ! texto {tx.spec['id']} sale de la zona segura de Reels", file=sys.stderr)

    def shot(self, toma):
        key = toma["id"]
        if key not in self.shots:
            if toma["tipo"] == "foto":
                self.shots[key] = Foto(toma, self.hoja, self.W, self.H)
            elif toma["tipo"] == "macro":
                self.shots[key] = Macro(toma, self.strokes, self.W, self.H)
            else:
                self.shots[key] = self.get_cierre(toma)
        return self.shots[key]

    def get_cierre(self, toma=None):
        if self.cierre is None:
            toma = toma or next(x for x in self.tomas if x["tipo"] == "cierre")
            self.cierre = Cierre(toma, self.cfg, self.reel, self.W, self.H, self.S)
        return self.cierre

    def frame(self, t, grain_rng=None, texts=True):
        toma = next(x for x in self.tomas if x["inicio"] <= t < x["fin"]) if t < self.dur else self.tomas[-1]
        img = self.shot(toma).frame(t)
        if grain_rng is not None and toma["tipo"] != "cierre":
            a = np.asarray(img, np.int16) + grain_rng.normal(0, 2.2, (self.H, self.W, 1)).astype(np.int16)
            img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        if texts:
            if self.nota and toma["tipo"] != "cierre":
                img.paste(self.nota.convert("RGB"), (int(self.W * (1 - SAFE_SIDE) - self.nota.width),
                                                    int(self.H * SAFE_TOP + 16 * self.S)), self.nota)
            for tx in self.textos:
                tx.draw(img, t)
        for key in list(self.shots):
            done = next(x for x in self.tomas if x["id"] == key)
            if done["fin"] <= toma["inicio"] and done["tipo"] != "cierre":
                del self.shots[key]          # free memory of finished shots
        return img


def guides(W, H):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    red = (230, 40, 40, 70)
    top, bot, side = H * SAFE_TOP, H * (1 - SAFE_BOTTOM), W * SAFE_SIDE
    d.rectangle((0, 0, W, top), fill=red)
    d.rectangle((0, bot, W, H), fill=red)
    d.rectangle((0, top, side, bot), fill=red)
    d.rectangle((W - side, top, W, bot), fill=red)
    return layer


def render_video(args):
    S = 0.5 if args.preview else 1.0
    r = Reel(S)
    name = r.reel["salida"]["archivo"] + ("_preview" if args.preview else "") + ("_guias" if args.guides else "")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.mp4"
    g = guides(r.W, r.H) if args.guides else None
    n = int(round(r.dur * r.fps))
    rng = np.random.default_rng(4)
    with tempfile.TemporaryDirectory() as tmp:
        raw, wav = Path(tmp) / "mix.wav", Path(tmp) / "norm.wav"
        print("  audio…", flush=True)
        audio(r.reel, r.strokes, r.get_cierre(), r.tomas, r.dur, raw)
        loudnorm(raw, wav, r.reel["musica"]["nivel_lufs"])
        enc = ["-c:v", "libx264", "-preset", "veryfast" if args.preview else "slow",
               "-crf", "24" if args.preview else "17", "-profile:v", "high",
               "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{r.W}x{r.H}",
               "-framerate", str(r.fps), "-i", "-", "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
               "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", *enc,
               "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{r.dur}", "-movflags", "+faststart", str(out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            t = i / r.fps
            frame = r.frame(t, rng)
            if g:
                frame.paste(g.convert("RGB"), (0, 0), g)
            proc.stdin.write(frame.tobytes())
            if i % r.fps == 0:
                print(f"\r  video: {t:4.0f}/{r.dur:.0f} s", end="", flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            sys.exit("ffmpeg failed")
    print(f"\r  reel -> {out.relative_to(ROOT)}")
    if not args.preview and not args.guides:
        rev = OUT / "revision" / f"{name}_revision.mp4"
        rev.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-vf", "scale=540:960", "-c:v", "libx264",
                        "-crf", "27", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", str(rev)], check=True)
        print(f"  revisión -> {rev.relative_to(ROOT)}")


def render_stills():
    r = Reel(1.0)
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, reel = r.cfg, r.reel
    pal = {k: rgb(v) for k, v in cfg["paleta"].items()}
    T = cfg["tipografia"]

    # cover: the wide gesture finished at her hand, title in the central zone
    p = reel["portada"]
    toma = {"id": "portada", "escena": p["escena"], "inicio": 0, "fin": 1, "de": [0.53, 0.44, 1.12],
            "a": [0.53, 0.44, 1.12], "tipo": "foto"}
    img = Foto(toma, r.hoja, r.W, r.H).frame(p["tiempo"]).convert("RGBA")
    f1, f2 = font(T["titulos"], 96), font(T["titulos"], 52)
    w1, w2 = f1.getlength(p["frase"]), f2.getlength(p["nombre"].upper())
    bw, bh = max(w1, w2) + 84, 96 * 0.72 + 52 * 0.72 + 30 + 2 * 34
    x0, y0 = (r.W - bw) / 2, 1210 - bh / 2
    box = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 6, x0 + bw, y0 + bh + 6), radius=8, fill=80)
    img.paste((20, 16, 12, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(12)))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=8, fill=pal["crema"] + (246,))
    xx = (r.W - w1) / 2
    for chunk, col in runs(p["frase"], pal["carbon"], pal["terracota"]):
        d.text((xx, y0 + 34 + 96 * 0.72), chunk, font=f1, fill=col + (255,), anchor="ls")
        xx += f1.getlength(chunk)
    d.text((r.W / 2, y0 + bh - 34), p["nombre"].upper(), font=f2, fill=pal["terracota"] + (255,), anchor="ms")
    img = Image.alpha_composite(img, box)
    if r.nota:
        img.alpha_composite(r.nota, (int(r.W * (1 - SAFE_SIDE) - r.nota.width), int(r.H * SAFE_TOP + 16)))
    img = img.convert("RGB")
    img.save(OUT / "portada_1080x1920.png")
    img.crop((0, 285, 1080, 1635)).save(OUT / "portada_recorte_4x5.png")

    # storyboard: one frame per shot, captions at their fullest
    tiles = []
    for toma in r.tomas:
        t = toma["inicio"] + (toma["fin"] - toma["inicio"]) * (0.85 if toma["tipo"] != "cierre" else 0.95)
        frame = r.frame(t, texts=False)
        for tx in r.textos:
            if tx.spec["inicio"] <= t < tx.spec["fin"] or (toma["inicio"] <= tx.spec["inicio"] < toma["fin"]
                                                         and t >= tx.spec["fin"]):
                tx.draw(frame, min(max(t, tx.spec["inicio"] + 0.5), tx.spec["fin"] - 0.01))
        tiles.append((frame, f"{toma['inicio']:g}–{toma['fin']:g} s · {toma['id']}"))
    tw, th = 270, 480
    cols = 6
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * (tw + 16) + 16, rows * (th + 50) + 16), pal["crema"])
    d = ImageDraw.Draw(sheet)
    f = font(T["cuerpo_medio"], 16)
    for i, (frame, tag) in enumerate(tiles):
        x, y = 16 + (i % cols) * (tw + 16), 16 + (i // cols) * (th + 50)
        sheet.paste(frame.resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 10), tag, font=f, fill=pal["carbon"])
    sheet.save(OUT / "storyboard.png")

    # editable text layers: one PNG per caption + SRT, and the closing card texts
    lay = OUT / "textos"
    lay.mkdir(parents=True, exist_ok=True)
    srt = []

    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    for i, tx in enumerate(r.textos, 1):
        L = Image.new("RGBA", (r.W, r.H), (0, 0, 0, 0))
        L.alpha_composite(tx.img, (int(tx.x), int(round(tx.y))))
        s = tx.spec
        L.save(lay / f"{i:02d}_{s['id']}_{s['inicio']:05.2f}-{s['fin']:05.2f}s.png")
        srt.append(f"{i}\n{ts(s['inicio'])} --> {ts(s['fin'])}\n{s['texto'].replace(chr(10), ' ')}\n")
    (lay / "textos_en_pantalla.srt").write_text("\n".join(srt), encoding="utf-8")
    r.get_cierre().text_layer().save(lay / "cierre_textos_y_logo.png")
    print(f"  portada, storyboard y textos -> {OUT.relative_to(ROOT)}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", action="store_true", help="half resolution, fast encode")
    ap.add_argument("--guides", action="store_true", help="draw the Reels safe-zone guides")
    ap.add_argument("--stills", action="store_true", help="cover, storyboard and text layers only")
    args = ap.parse_args()
    if args.stills:
        render_stills()
    else:
        render_video(args)


if __name__ == "__main__":
    main()
