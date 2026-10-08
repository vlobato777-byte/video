#!/usr/bin/env python3
"""Laboratorio de dibujo sensorial: campaign pieces.

Renders the flyer (1080 x 1350) from laboratorio-dibujo-sensorial/datos.json:

  canva/papel_1080x1350.png        warm art paper (#F4EBDD, very subtle texture)
  canva/trazos_1080x1350.png       charcoal gestures on transparency, placed
                                   only where there is no text
  canva/nota_imagen_ilustrativa.png  small label for a generated photo
  flyer_maqueta.png                the whole flyer with the exact fonts; uses
                                   the photo and logo from datos.json when the
                                   files exist, otherwise marks their slots

The editable version lives in Canva and uses the same coordinates (LAYOUT).

Usage
  python3 tools/laboratorio.py flyer
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trazos as tz  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "laboratorio-dibujo-sensorial"

# Flyer layout, 1080 x 1350 px: (left, top) of each text box, photo and logo
# slots. The Canva design uses the same numbers.
LAYOUT = {
    "margin": 72,
    "foto": (560, 0, 520, 693),
    "logo": (830, 1000, 178, 210),
    "banda": (0, 1240, 1080, 110),
    "frase": (72, 40, 140, 129),            # x, y, size, line step
    "nombre": (72, 486, 54, 57),
    "pregunta": (72, 716, 40, 48),
    "invitacion": (72, 826, 32),
    "sin_experiencia": (72, 870, 32),
    "imparten_label": (72, 978, 26),
    "imparten": (72, 1008, 30),
    "fecha_horario": (72, 1058, 29),
    "sede": (72, 1102, 26, 33),
    "costo": (72, 1180, 29),
    "reserva": (72, 1281, 30),
    "whatsapp": (330, 1258, 60),
}


def rgb(hex_):
    s = hex_.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def font(path, size):
    return ImageFont.truetype(str(ROOT / path), size)


def flyer_strokes(canvas, seed=21):
    """Gestures in the free areas of the layout (never under the text)."""
    rng = np.random.default_rng(seed)
    strokes = []
    # a trace that runs under the workshop name and disappears behind the photo
    ctrl = [(-20, 668), (120, 640), (250, 662), (330, 690), (380, 655), (350, 615),
            (300, 628), (310, 668), (420, 676), (560, 640), (700, 650)]
    pts = tz.hand(tz.spline(ctrl, 700), 3, rng)
    strokes.append(tz.Stroke(pts, "carbon", 34, tz.pressure_curve(len(pts), rng, 0.85, 0.35, cell=150),
                             seed=31, taper=0.06))
    # terracotta underline for TRAZA.
    pts = tz.hand(tz.spline([(70, 452), (180, 458), (300, 450), (395, 440), (440, 424)], 300), 1.5, rng)
    strokes.append(tz.Stroke(pts, "carbon", 13, tz.pressure_curve(len(pts), rng, 0.9, 0.2),
                             ink="terracota", seed=32, taper=0.15))
    # breathing: three graphite waves as the divider before the practical data
    for k, (amp, ph) in enumerate([(6, 0.0), (8, 0.9), (5, 1.7)]):
        pts = tz.onda(72, 1008, 940 + k * 11, amp, 300 + 40 * k, rng, wobble=1.2, phase=ph)
        strokes.append(tz.Stroke(pts, "grafito", 2.4, tz.pressure_curve(len(pts), rng, 0.75, 0.3),
                                 ink="grafito", seed=40 + k, taper=0.1))
    # a heard rhythm: dots in groups, next to "No necesitas experiencia previa."
    path = tz.spline([(660, 890), (780, 884), (890, 892), (1000, 886)], 200)
    dots = tz.ritmo(path, [3, 1, 2, 4], rng, spread=0.8)
    strokes.append(tz.Stroke(dots, "punto", 12, 0.9 + 0.1 * rng.random(len(dots)), seed=50))
    for s in strokes:
        canvas.draw(s)


def cover(img, w, h, cx=0.5, cy=0.5):
    k = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    x0 = round((img.width - w) * cx)
    y0 = round((img.height - h) * cy)
    return img.crop((x0, y0, x0 + w, y0 + h))


def text_block(draw, xy, text, fnt, fill, step=None):
    x, y = xy
    for i, line in enumerate(text.split("\n")):
        draw.text((x, y + i * (step or round(fnt.size * 1.2))), line, font=fnt, fill=fill)


def label_png(text, path, cfg):
    """Small 'Imagen ilustrativa' tag: cream text on a soft charcoal pill."""
    f = font(cfg["tipografia"]["cuerpo_medio"], 20)
    w = int(f.getlength(text)) + 28
    img = Image.new("RGBA", (w, 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, 33), radius=17, fill=rgb(cfg["paleta"]["carbon"]) + (150,))
    d.text((w / 2, 17), text, font=f, fill=rgb(cfg["paleta"]["crema"]) + (255,), anchor="mm")
    img.save(path)


def render_flyer(cfg, out):
    W, H = 1080, 1350
    canva = out / "canva"
    canva.mkdir(parents=True, exist_ok=True)
    pal = {k: rgb(v) for k, v in cfg["paleta"].items()}
    cv = tz.Canvas(W, H, 1.0, paper_seed=11, paper_strength=0.55, tone=pal["crema"])
    flyer_strokes(cv)
    paper = Image.fromarray(np.clip(cv.rgb + 0.5, 0, 255).astype(np.uint8))
    paper.save(canva / "papel_1080x1350.png")
    cv.alpha_layer().save(canva / "trazos_1080x1350.png")
    fl = cfg["flyer"]
    label_png(fl["nota_foto"], canva / "nota_imagen_ilustrativa.png", cfg)

    # full mock-up with the exact fonts
    im = cv.compose()
    L = LAYOUT
    fx, fy, fw, fh = L["foto"]
    photo = ROOT / fl["foto"]
    d = ImageDraw.Draw(im)
    if photo.exists():
        im.paste(cover(ImageOps.exif_transpose(Image.open(photo)).convert("RGB"), fw, fh, 0.5, 0.35), (fx, fy))
    else:
        d.rectangle((fx, fy, fx + fw, fy + fh), fill=(214, 204, 188))
        d.text((fx + fw / 2, fy + fh / 2), "FOTO PRINCIPAL\n(ver Canva)", font=font(cfg["tipografia"]["cuerpo_medio"], 28),
               fill=pal["carbon"], anchor="mm", align="center")
    lx, ly, lw, lh = L["logo"]
    logo = ROOT / fl["logo"]
    if logo.exists():
        lg = Image.open(logo).convert("RGBA")
        k = min(lw / lg.width, lh / lg.height)
        lg = lg.resize((round(lg.width * k), round(lg.height * k)), Image.LANCZOS)
        im.paste(lg, (lx + (lw - lg.width) // 2, ly + (lh - lg.height) // 2), lg)
    else:
        d.rectangle((lx, ly, lx + lw, ly + lh), outline=(190, 180, 168), width=2)
        d.text((lx + lw / 2, ly + lh / 2), "LOGO", font=font(cfg["tipografia"]["cuerpo_medio"], 22),
               fill=(150, 140, 130), anchor="mm")

    T, dat = cfg["tipografia"], cfg["datos"]
    x, y, s, step = L["frase"]
    text_block(d, (x, y), fl["frase"], font(T["titulos"], s), pal["carbon"], step)
    x, y, s, step = L["nombre"]
    text_block(d, (x, y), fl["nombre"], font(T["titulos"], s), pal["terracota"], step)
    x, y, s, step = L["pregunta"]
    text_block(d, (x, y), fl["pregunta"], font(T["cuerpo_negrita"], s), pal["carbon"], step)
    x, y, s = L["invitacion"]
    text_block(d, (x, y), fl["invitacion"], font(T["cuerpo"], s), pal["carbon"])
    x, y, s = L["sin_experiencia"]
    text_block(d, (x, y), fl["sin_experiencia"], font(T["cuerpo_semi"], s), pal["olivo"])
    x, y, s = L["imparten_label"]
    text_block(d, (x, y), fl["imparten_label"], font(T["cuerpo_semi"], s), pal["olivo"])
    x, y, s = L["imparten"]
    text_block(d, (x, y), dat["imparten"], font(T["cuerpo_negrita"], s), pal["carbon"])
    x, y, s = L["fecha_horario"]
    text_block(d, (x, y), dat["fecha_horario"], font(T["cuerpo_negrita"], s), pal["carbon"])
    x, y, s, step = L["sede"]
    d.text((x, y), dat["sede"], font=font(T["cuerpo_semi"], s), fill=pal["carbon"])
    d.text((x, y + step), dat["direccion"], font=font(T["cuerpo_medio"], s), fill=pal["carbon"])
    x, y, s = L["costo"]
    text_block(d, (x, y), dat["costo"], font(T["cuerpo_semi"], s), pal["carbon"])
    bx, by, bw, bh = L["banda"]
    d.rectangle((bx, by, bx + bw, by + bh), fill=pal["terracota"])
    x, y, s = L["reserva"]
    text_block(d, (x, y), fl["reserva"], font(T["cuerpo_medio"], s), pal["crema"])
    x, y, s = L["whatsapp"]
    text_block(d, (x, y), "WhatsApp " + dat["whatsapp"], font(T["titulos"], s), pal["crema"])
    if photo.exists() and fl.get("foto_ilustrativa"):
        tag = Image.open(canva / "nota_imagen_ilustrativa.png")
        im.paste(tag, (fx + fw - tag.width - 16, fy + fh - tag.height - 16), tag)
    im.save(out / "flyer_maqueta.png")
    print(f"  flyer -> {out.relative_to(ROOT)}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pieza", choices=["flyer"])
    args = ap.parse_args()
    cfg = json.loads((PROJECT / "datos.json").read_text(encoding="utf-8"))
    if args.pieza == "flyer":
        render_flyer(cfg, PROJECT / "exports" / "flyer")


if __name__ == "__main__":
    main()
