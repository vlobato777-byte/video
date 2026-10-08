"""Laboratorio de dibujo sensorial: paper and charcoal engine.

Procedural drawing shared by the flyer, the carousel and the reel: a warm
art-paper texture and gestural charcoal strokes that can be drawn all at once
(stills) or progressively (animation), always identical for the same seed.

A drawing is a list of Stroke objects in sheet units (1 unit = 1 px of a
1080 px wide piece); Canvas renders them at any pixel scale, so the same
composition works for a 1080 px post and a 2160 px reel camera plate.

Tools
  carbon   side of a willow charcoal stick: wide ribbon with streaks
  punta    charcoal tip: medium grainy line
  grafito  graphite: thin, steady grey line
  punto    single dabs (rhythmic dots)
"""

import math

import numpy as np
from PIL import Image

# Campaign palette (see laboratorio-dibujo-sensorial/project/datos.json).
CREMA = (0xF4, 0xEB, 0xDD)
CARBON = (0x27, 0x25, 0x22)
TERRACOTA = (0xD8, 0x5B, 0x35)
OLIVO = (0x78, 0x83, 0x4B)

# ink: colour, max coverage, how much the paper tooth breaks it up (0-1)
INKS = {
    "carbon": (CARBON, 0.94, 0.85),
    "grafito": ((0x4A, 0x48, 0x46), 0.80, 0.55),
    "terracota": (TERRACOTA, 0.92, 0.75),
    "olivo": (OLIVO, 0.90, 0.75),
}

TOOL_SPACING = {"carbon": 0.10, "punta": 0.22, "grafito": 0.30, "punto": 1.0}


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------- noise

def value_noise(h, w, cell, rng, octaves=4, falloff=0.55):
    """Smooth multi-octave noise in [0, 1], built by upscaling random grids."""
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for _ in range(octaves):
        gh, gw = max(2, int(h / cell) + 2), max(2, int(w / cell) + 2)
        grid = rng.random((gh, gw)).astype(np.float32)
        img = Image.fromarray(grid, "F").resize((int(gw * cell), int(gh * cell)), Image.BICUBIC)
        out += amp * np.asarray(img, np.float32)[:h, :w]
        total += amp
        amp *= falloff
        cell = max(1.0, cell / 2)
    out /= total
    lo, hi = np.percentile(out, (1, 99))
    return np.clip((out - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)


def noise1d(n, cell, rng):
    """Smooth 1-D noise in [-1, 1] with n samples and features every `cell` samples."""
    k = max(2, int(n / max(cell, 1)) + 3)
    knots = rng.uniform(-1, 1, k)
    x = np.linspace(0, k - 3, n) + 1
    i = np.floor(x).astype(int)
    f = x - i
    p0, p1, p2, p3 = knots[i - 1], knots[i], knots[i + 1], knots[np.minimum(i + 2, k - 1)]
    return 0.5 * (2 * p1 + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f ** 2
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


def paper(w, h, seed=7, tone=CREMA, strength=1.0):
    """Warm art paper: RGB float32 (h, w, 3) in 0-255 and tooth map (h, w) in 0-1.

    `strength` scales the visible texture (the campaign asks for a very subtle
    one); the tooth that breaks up the charcoal is always full strength.
    """
    rng = np.random.default_rng(seed)
    s = w / 1080
    mottle = value_noise(h, w, 300 * s, rng, octaves=3)
    fine = value_noise(h, w, 2.6 * s, rng, octaves=2, falloff=0.6)
    fibres = value_noise(max(2, int(h / 7)), w, 2.2 * s, rng, octaves=2)
    fibres = np.asarray(Image.fromarray(fibres, "F").resize((w, h), Image.BICUBIC), np.float32)
    speck = rng.random((h, w)).astype(np.float32)
    tooth = np.clip(0.50 * fine + 0.22 * fibres + 0.18 * speck + 0.10 * mottle, 0, 1)
    tooth = (tooth - tooth.min()) / max(float(tooth.max() - tooth.min()), 1e-6)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vign = (xx / w - 0.5) ** 2 + 0.8 * (yy / h - 0.5) ** 2
    shade = (1.0
             - strength * 0.022 * (mottle - 0.5)
             - strength * 0.016 * (fibres - 0.5)
             - strength * 0.020 * (fine - 0.5)
             - strength * 0.040 * vign)
    rgb = np.array(tone, np.float32)[None, None, :] * shade[..., None]
    rgb[..., 2] *= 1 - strength * 0.25 * (1 - shade)          # warmer where it is shaded
    return np.clip(rgb, 0, 255), tooth


# --------------------------------------------------------------------------- strokes

class Stroke:
    """One gesture: a polyline in sheet units with pressure and timing."""

    def __init__(self, pts, tool="carbon", width=20.0, pressure=None, ink="carbon",
                 t0=0.0, dur=1.0, ease="gesto", seed=0, taper=0.12, grosor=None, pausas=2):
        self.pts = np.asarray(pts, np.float64)
        self.tool, self.width, self.ink = tool, float(width), ink
        n = len(self.pts)
        p = np.ones(n) if pressure is None else np.broadcast_to(np.asarray(pressure, np.float64), (n,)).copy()
        if taper and n > 2 and tool != "punto":
            f = np.linspace(0, 1, n)
            p *= smoothstep(f / taper) * smoothstep((1 - f) / (taper * 1.4)) * 0.85 + 0.15
        self.pressure = p
        self.t0, self.dur, self.ease, self.seed = t0, dur, ease, seed
        seg = np.hypot(*np.diff(self.pts, axis=0).T) if n > 1 else np.zeros(0)
        self.arc = np.concatenate([[0.0], np.cumsum(seg)])
        self.length = float(self.arc[-1])
        # width factor per point: the stick turns in the fingers (side -> edge)
        self.grosor = None if grosor is None else np.broadcast_to(np.asarray(grosor, np.float64), (n,)).copy()
        self.timing = None
        if ease == "mano":
            self.timing = hand_timing(seed, pausas)
            tau, prog, spd = self.timing
            # the charcoal lingers where the hand slows down: more deposit there
            s = np.interp(self.arc / max(self.length, 1e-9), prog, spd) / spd.max()
            self.pressure = self.pressure * (1 + 0.8 * (1 - s) ** 2)

    @property
    def t1(self):
        return self.t0 + self.dur

    def progress(self, t):
        """Fraction of the stroke drawn at time t (0-1), with a hand-like speed curve."""
        if t <= self.t0:
            return 0.0
        p = min(1.0, (t - self.t0) / max(self.dur, 1e-6))
        if self.ease == "lineal":
            return p
        if self.ease == "respira":       # slow start and end, like an exhale
            return 0.5 - 0.5 * math.cos(math.pi * p)
        if self.ease == "mano":          # uneven hand speed with hesitations
            tau, prog, _ = self.timing
            return float(np.interp(p, tau, prog))
        if self.ease == "llega":         # steady speed, settles where the hand stops
            m0, m1 = 1.15, 0.3           # Hermite end slopes
            return m0 * (p ** 3 - 2 * p ** 2 + p) + (3 * p ** 2 - 2 * p ** 3) + m1 * (p ** 3 - p ** 2)
        return 1 - (1 - p) ** 1.8        # "gesto": fast attack, slows down at the end

    def speed(self, t, dt=1 / 30):
        """Drawn length per second at time t (drives the scratch sound)."""
        return (self.progress(t + dt) - self.progress(t)) * self.length / dt


def hand_timing(seed, pausas=2):
    """Uneven drawing speed of a real hand: surges, hesitations and short stops.

    Returns normalised time, drawn fraction and relative speed (all arrays).
    """
    rng = np.random.default_rng(seed + 7919)
    n = 400
    tau = np.linspace(0.0, 1.0, n)
    spd = np.exp(0.5 * noise1d(n, 45, rng) + 0.2 * noise1d(n, 9, rng))
    for _ in range(pausas):
        c, w = rng.uniform(0.12, 0.88), rng.uniform(0.012, 0.035)
        spd *= 1 - 0.93 * np.exp(-((tau - c) / w) ** 2)
    spd *= 0.25 + 0.75 * smoothstep(tau / 0.05)
    prog = np.concatenate([[0.0], np.cumsum((spd[1:] + spd[:-1]) / 2)])
    return tau, prog / prog[-1], spd


def resample(stroke, step):
    """Dab positions along the stroke every `step` units: xy, angle, pressure, arc fraction."""
    d = np.arange(0.0, stroke.length + 1e-9, step)
    if len(d) < 2:
        d = np.array([0.0, stroke.length])
    x = np.interp(d, stroke.arc, stroke.pts[:, 0])
    y = np.interp(d, stroke.arc, stroke.pts[:, 1])
    p = np.interp(d, stroke.arc, stroke.pressure)
    dx, dy = np.gradient(x), np.gradient(y)
    return np.stack([x, y], 1), np.arctan2(dy, dx), p, d / max(stroke.length, 1e-9)


def spline(ctrl, n=200, closed=False):
    """Catmull-Rom spline through control points (sheet units)."""
    c = np.asarray(ctrl, np.float64)
    c = np.vstack([c[-1], c, c[0], c[1]]) if closed else np.vstack([2 * c[0] - c[1], c, 2 * c[-1] - c[-2]])
    segs = len(c) - 3
    per = max(2, n // segs)
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = c[i], c[i + 1], c[i + 2], c[i + 3]
        t = np.linspace(0, 1, per, endpoint=False)[:, None]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(c[-2][None, :])
    return np.vstack(out)


def hand(pts, amount, rng, cell=40):
    """Displace a path with smooth noise so it reads as drawn by hand."""
    pts = np.asarray(pts, np.float64)
    n = len(pts)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    length = seg.sum() if n > 1 else 1.0
    c = max(2.0, n * cell / max(length, 1.0))
    return pts + amount * np.stack([noise1d(n, c, rng), noise1d(n, c, rng)], 1)


def pressure_curve(n, rng, base=0.75, var=0.25, cell=60):
    return np.clip(base + var * noise1d(n, cell, rng), 0.05, 1.2)


# --------------------------------------------------------------------------- gestures

def lazo(cx, cy, rx, ry, turns, rng, drift=(0, 0), wobble=0.18, n_per_turn=140, phase=0.0):
    """Continuous looping scribble: the arm circling while it travels (`drift`)."""
    n = int(turns * n_per_turn)
    t = np.linspace(0, 1, n)
    a = phase + 2 * math.pi * turns * t
    rmod = 1 + wobble * noise1d(n, n_per_turn * 0.6, rng)
    x = cx + drift[0] * (t - 0.5) + rx * rmod * np.cos(a)
    y = cy + drift[1] * (t - 0.5) + ry * rmod * np.sin(a)
    return np.stack([x, y], 1)


def onda(x0, x1, y, amp, period, rng, n=400, wobble=3.0, phase=0.0):
    """Long horizontal wave (breathing): amplitude swells and settles."""
    x = np.linspace(x0, x1, n)
    env = 0.6 + 0.4 * np.sin(np.linspace(0, math.pi, n))
    yy = y + amp * env * np.sin(2 * math.pi * (x - x0) / period + phase)
    return hand(np.stack([x, yy], 1), wobble, rng)


def ritmo(path, groups, rng, spread=4.0):
    """Dots along a path in rhythmic groups, e.g. groups=[3, 1, 4] (a heard rhythm)."""
    path = np.asarray(path, np.float64)
    total = sum(groups) + len(groups) * 1.6
    pos, out = 0.0, []
    for g in groups:
        for _ in range(g):
            out.append(pos)
            pos += 1.0
        pos += 1.6
    f = np.array(out) / total
    seg = np.hypot(*np.diff(path, axis=0).T)
    arc = np.concatenate([[0], np.cumsum(seg)])
    d = f * arc[-1]
    pts = np.stack([np.interp(d, arc, path[:, 0]), np.interp(d, arc, path[:, 1])], 1)
    return pts + rng.normal(0, spread, pts.shape)


def trama(x0, y0, w, h, angle, gap, rng, amp=0.5):
    """Zig-zag hatching filling a box (touch / texture), as one continuous stroke."""
    ca, sa = math.cos(angle), math.sin(angle)
    diag = math.hypot(w, h)
    k = int(diag / gap)
    pts = []
    for i in range(k):
        s = (i - k / 2) * gap
        a = -diag / 2 * (0.6 + amp * rng.random())
        b = diag / 2 * (0.6 + amp * rng.random())
        p0 = (a, s) if i % 2 == 0 else (b, s)
        p1 = (b, s + gap * 0.5) if i % 2 == 0 else (a, s + gap * 0.5)
        pts += [p0, p1]
    pts = np.array(pts, np.float64)
    rot = np.array([[ca, -sa], [sa, ca]])
    pts = pts @ rot.T + (x0 + w / 2, y0 + h / 2)
    pts[:, 0] = np.clip(pts[:, 0], x0, x0 + w)
    pts[:, 1] = np.clip(pts[:, 1], y0, y0 + h)
    dense = spline(pts, len(pts) * 8)
    return hand(dense, gap * 0.15, rng)


def pulso(pts, rng, amp=2.0, wl=30.0, micro=0.6, step=1.5):
    """The pulse of the hand: a wobble across the line at two scales.

    `amp` / `wl` give the visible tremble (units / wavelength in units); `micro`
    adds the fine shake of the fingers. Returns the path resampled every `step`.
    """
    pts = np.asarray(pts, np.float64)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    d = np.arange(0.0, arc[-1] + 1e-9, step)
    if len(d) < 3:
        return pts
    x, y = np.interp(d, arc, pts[:, 0]), np.interp(d, arc, pts[:, 1])
    n = len(d)
    tx, ty = np.gradient(x), np.gradient(y)
    nrm = np.hypot(tx, ty) + 1e-9
    tx, ty = tx / nrm, ty / nrm
    off = amp * noise1d(n, wl / step, rng) + micro * noise1d(n, max(2.0, wl / 7 / step), rng)
    along = 0.5 * micro * noise1d(n, max(2.0, wl / 5 / step), rng)
    return np.stack([x - ty * off + tx * along, y + tx * off + ty * along], 1)


def vibra(pts, rng, amp=22.0, onda=(24.0, 70.0), envolvente=None, step=2.0):
    """A line that answers a sound: it oscillates across its path, denser and
    wider where the sound is louder (`envolvente` 0-1 along the line)."""
    pts = np.asarray(pts, np.float64)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    d = np.arange(0.0, arc[-1] + 1e-9, step)
    x, y = np.interp(d, arc, pts[:, 0]), np.interp(d, arc, pts[:, 1])
    n = len(d)
    f = d / max(d[-1], 1e-9)
    env = np.clip(0.55 + 0.45 * noise1d(n, n / 6, rng), 0.05, 1) if envolvente is None else envolvente(f)
    wavelength = onda[1] - (onda[1] - onda[0]) * env
    phase = np.cumsum(2 * np.pi * step / wavelength)
    tx, ty = np.gradient(x), np.gradient(y)
    nrm = np.hypot(tx, ty) + 1e-9
    off = amp * env * np.sin(phase) * (1 + 0.25 * noise1d(n, 15, rng))
    return np.stack([x - ty / nrm * off, y + tx / nrm * off], 1)


def rizos(pts, donde, rng, radio=(30, 55), step=2.0):
    """Loops where the hand circles back for a moment (positions 0-1 along the line)."""
    pts = np.asarray(pts, np.float64)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    d = np.arange(0.0, arc[-1] + 1e-9, step)
    x, y = np.interp(d, arc, pts[:, 0]), np.interp(d, arc, pts[:, 1])
    tx, ty = np.gradient(x), np.gradient(y)
    out, last = [], 0
    for f in sorted(donde):
        i = int(f * (len(d) - 1))
        out.append(np.stack([x[last:i], y[last:i]], 1))
        th = math.atan2(ty[i], tx[i])
        side = rng.choice([-1, 1])
        r = rng.uniform(*radio)
        c = np.array([x[i] - side * r * math.sin(th), y[i] + side * r * math.cos(th)])
        phi0 = math.atan2(y[i] - c[1], x[i] - c[0])
        a = np.linspace(0, 2 * math.pi, max(12, int(2 * math.pi * r / step)))
        rr = r * (1 + 0.15 * np.sin(a * 1.5 + rng.uniform(0, 6)))
        fwd = a / (2 * math.pi) * r * 0.6
        out.append(np.stack([c[0] + rr * np.cos(phi0 + side * a) + fwd * math.cos(th),
                             c[1] + rr * np.sin(phi0 + side * a) + fwd * math.sin(th)], 1))
        shift = r * 0.6
        j = min(len(d) - 1, i + int(shift / step))
        last = j
    out.append(np.stack([x[last:], y[last:]], 1))
    return np.vstack([o for o in out if len(o)])


def ciego(cx, cy, w, h, length, rng, step=3.0, giro=0.09, quiebres=0.03):
    """Blind contour: drawing a texture felt with the eyes covered. The line
    searches, hesitates, turns sharply, doubles back and stays inside the area."""
    n = max(4, int(length / step))
    pts = np.empty((n, 2))
    p = np.array([cx + w * rng.uniform(-0.25, 0.25), cy + h * rng.uniform(-0.25, 0.25)])
    ang, curv = rng.uniform(0, 2 * math.pi), 0.0
    for i in range(n):
        curv = 0.8 * curv + rng.normal(0, giro)
        if rng.random() < quiebres:                       # a ridge under the fingers
            ang += rng.choice([-1, 1]) * rng.uniform(0.8, 2.4)
        dx, dy = p[0] - cx, p[1] - cy
        if abs(dx) > 0.45 * w or abs(dy) > 0.45 * h:      # the hand comes back to the object
            target = math.atan2(-dy, -dx)
            curv += 0.12 * ((target - ang + math.pi) % (2 * math.pi) - math.pi)
        ang += curv
        p = p + step * (0.6 + 0.8 * rng.random()) * np.array([math.cos(ang), math.sin(ang)])
        pts[i] = p
    return pts


def hilo(x, y, largo, rng, viento=1.0, step=2.5):
    """A very fine line that falls like a thread in the wind: it drifts sideways,
    sways and flutters a little on its way down."""
    n = max(4, int(largo / step))
    yy = y + np.cumsum(step * (0.75 + 0.25 * np.abs(noise1d(n, n / 4, rng))))
    sway = viento * (45 * noise1d(n, n / 2.5, rng) + 14 * noise1d(n, n / 9, rng))
    lean = viento * np.linspace(0, rng.uniform(-60, 90), n)
    return np.stack([x + sway + lean, yy], 1)


def corteza(x0, y0, w, h, rng, lineas=6, gap_frac=(0.15, 0.4)):
    """Mapping the tactile memory of a bark: fissures that run along the trunk,
    meander together, break where the finger lost them, and short ridges across.

    Returns a list of polylines in drawing order."""
    ys = np.linspace(y0, y0 + h, 160)
    shared = noise1d(len(ys), 35, rng)
    xs = np.linspace(x0 + w * 0.08, x0 + w * 0.92, lineas)
    paths, cols = [], []
    for i, xb in enumerate(xs):
        own = noise1d(len(ys), rng.uniform(12, 30), rng)
        x = xb + 0.12 * w * shared + 0.045 * w * own + np.linspace(0, rng.uniform(-0.06, 0.06) * w, len(ys))
        cols.append(x)
        f = rng.uniform(0, 0.12)
        while f < 1:                                         # the finger loses the fissure now and then
            g = min(1, f + rng.uniform(0.3, 0.75))
            sel = (ys >= y0 + f * h) & (ys <= y0 + g * h)
            if sel.sum() > 3:
                paths.append(np.stack([x[sel], ys[sel]], 1))
            f = g + rng.uniform(*gap_frac) * 0.2
    for _ in range(lineas * 2):                              # ridges felt between two fissures
        i = int(rng.integers(0, lineas - 1))
        j = int(rng.integers(10, len(ys) - 10))
        a, b = np.array([cols[i][j], ys[j]]), np.array([cols[i + 1][j + int(rng.integers(-6, 6))], ys[j]])
        mid = (a + b) / 2 + np.array([0, rng.normal(0, 8)])
        paths.append(spline([a + rng.normal(0, 3, 2), mid, b + rng.normal(0, 3, 2)], 30))
    return paths


def presion_titubeo(n, rng, base=0.7, saltos=4, var=0.25):
    """Hesitant pressure: it wavers and almost lifts off in a few places."""
    i = np.arange(n)
    p = base + var * noise1d(n, max(3, n / 25), rng) + 0.12 * noise1d(n, 5, rng)
    for _ in range(saltos):
        c, w = rng.uniform(0.05, 0.95) * n, rng.uniform(0.004, 0.015) * n + 1
        p *= 1 - 0.97 * np.exp(-((i - c) / w) ** 2)
    return np.clip(p, 0.0, 1.5)


def presion_ritmo(n, golpes, rng, base=0.6, acento=0.75, ancho=0.012):
    """Pressure accents along the line, one per beat heard (positions 0-1)."""
    f = np.linspace(0, 1, n)
    p = np.full(n, base) + 0.12 * noise1d(n, 8, rng)
    for b in golpes:
        p += acento * rng.uniform(0.6, 1.0) * np.exp(-((f - b) / ancho) ** 2)
    return np.clip(p, 0.05, 1.8)


def grosor_giro(n, rng, lo=0.4, hi=1.15, cell=None):
    """Width factor as the stick turns between its side and its edge."""
    g = 0.5 + 0.5 * noise1d(n, cell or max(4, n / 5), rng)
    return lo + (hi - lo) * np.clip(g, 0, 1)


# --------------------------------------------------------------------------- canvas

class Canvas:
    """Accumulates charcoal deposit per ink at a given pixel scale."""

    def __init__(self, w, h, scale, paper_seed=7, paper_strength=1.0, tone=CREMA, origin=(0, 0)):
        self.w, self.h, self.scale = w, h, scale     # scale = px per sheet unit
        self.origin = np.array(origin, np.float64)   # sheet coords of the top-left pixel
        self.rgb, self.tooth = paper(w, h, paper_seed, tone, paper_strength)
        self.dep = {}
        self.cursor = {}
        self.cache = {}

    def _deposit(self, ink):
        if ink not in self.dep:
            self.dep[ink] = np.zeros((self.h, self.w), np.float32)
        return self.dep[ink]

    def _dabs(self, stroke):
        key = id(stroke)
        if key not in self.cache:
            rng = np.random.default_rng(stroke.seed + 1000)
            wpx = stroke.width * self.scale
            if stroke.tool == "punto":   # every point is one dab
                n = len(stroke.pts)
                xy, ang, pres, frac = stroke.pts, rng.uniform(0, math.pi, n), stroke.pressure, np.linspace(0, 1, n)
            else:
                step = max(0.5, wpx * TOOL_SPACING[stroke.tool]) / self.scale
                xy, ang, pres, frac = resample(stroke, step)
            n = len(xy)
            # the stick's edge: a fixed streak profile that drifts slowly along the stroke
            prof = 0.45 + 0.55 * np.clip(np.convolve(rng.random(64), np.ones(4) / 4, "same"), 0, 1)
            drift = 0.06 * noise1d(n, 80, rng)
            side = 0.05 * noise1d(n, 12, rng)            # ragged edges
            wid = 1 + 0.30 * noise1d(n, 70, rng)               # the stick turns in the hand
            flick = np.clip(1 + 0.30 * noise1d(n, 9, rng) + 0.25 * noise1d(n, 140, rng), 0.3, 1.6)
            shape = rng.uniform(0, 2 * math.pi, (n, 2))
            px = (xy - self.origin) * self.scale
            gro = (np.ones(n) if stroke.grosor is None else
                   np.interp(frac, stroke.arc / max(stroke.length, 1e-9), stroke.grosor))
            self.cache[key] = dict(xy=px, ang=ang, pres=pres, frac=frac, prof=prof, drift=drift,
                                   side=side, wid=wid, flick=flick, shape=shape, wpx=wpx, gro=gro)
        return self.cache[key]

    def draw(self, stroke, upto=1.0):
        """Stamp the stroke up to the given fraction (call repeatedly for animation)."""
        c = self._dabs(stroke)
        key = id(stroke)
        start = self.cursor.get(key, 0)
        end = int(np.searchsorted(c["frac"], upto, side="right"))
        if end <= start:
            return
        D = self._deposit(stroke.ink)
        wpx, tool = c["wpx"], stroke.tool
        for i in range(start, end):
            p = c["pres"][i]
            if p <= 0.02:
                continue
            x, y = c["xy"][i]
            if tool == "carbon":
                hw = 0.5 * wpx * c["wid"][i] * c["gro"][i] * (0.7 + 0.3 * min(p, 1.0))
                off = c["side"][i] * wpx
                ox, oy = -math.sin(c["ang"][i]) * off, math.cos(c["ang"][i]) * off
                self._ribbon(D, x + ox, y + oy, c["ang"][i], hw, max(1.0, 2 * wpx * TOOL_SPACING["carbon"]),
                             c["prof"], c["drift"][i], 0.26 * p * c["flick"][i])
            elif tool == "punto":
                r = 0.5 * wpx * c["gro"][i] * (0.65 + 0.45 * p)
                self._blob(D, x, y, r, r * 0.9, c["ang"][i], c["shape"][i], 0.9 * min(p, 1.2), irregular=0.12)
            else:
                r = max(0.55, 0.5 * wpx * c["gro"][i] * (0.55 + 0.45 * min(p, 1.0)))
                gain = 0.16 if tool == "punta" else 0.22
                self._blob(D, x, y, r, r, 0.0, c["shape"][i], gain * p, irregular=0.0)
        self.cursor[key] = end

    def _window(self, x, y, r):
        r = int(math.ceil(r)) + 1
        x0, x1 = max(0, int(x) - r), min(self.w, int(x) + r + 1)
        y0, y1 = max(0, int(y) - r), min(self.h, int(y) + r + 1)
        if x0 >= x1 or y0 >= y1:
            return None
        yy = (np.arange(y0, y1, dtype=np.float32) - y)[:, None]
        xx = (np.arange(x0, x1, dtype=np.float32) - x)[None, :]
        return x0, x1, y0, y1, xx, yy

    def _ribbon(self, D, x, y, ang, hw, hl, prof, drift, alpha):
        win = self._window(x, y, max(hw, hl))
        if win is None:
            return
        x0, x1, y0, y1, xx, yy = win
        c, s = math.cos(ang), math.sin(ang)
        u = (-xx * s + yy * c) / hw            # across the stroke, -1..1
        v = (xx * c + yy * s) / hl             # along the stroke
        idx = np.clip(((u + 1 + drift) * 0.5 * (len(prof) - 1)).astype(np.int32), 0, len(prof) - 1)
        along = np.where(np.abs(v) < 1, 0.5 + 0.5 * np.cos(np.pi * np.clip(v, -1, 1)), 0.0)
        wgt = prof[idx] * smoothstep((1 - np.abs(u)) * 7) * along
        D[y0:y1, x0:x1] += (alpha * wgt).astype(np.float32)

    def _blob(self, D, x, y, rx, ry, ang, shape, alpha, irregular=0.0):
        win = self._window(x, y, max(rx, ry) * (1 + irregular))
        if win is None:
            return
        x0, x1, y0, y1, xx, yy = win
        c, s = math.cos(ang), math.sin(ang)
        u = (xx * c + yy * s) / rx
        v = (-xx * s + yy * c) / ry
        rr = np.sqrt(u * u + v * v)
        if irregular:
            th = np.arctan2(v, u)
            rr = rr / (1 + irregular * (0.6 * np.sin(3 * th + shape[0]) + 0.4 * np.sin(5 * th + shape[1])))
        wgt = smoothstep((1 - rr) * 2.5)
        D[y0:y1, x0:x1] += (alpha * wgt).astype(np.float32)

    def coverage(self, ink):
        """Visible charcoal (0-1) for one ink: the paper tooth breaks up light deposit."""
        _, maxa, grain = INKS[ink]
        D = self.dep.get(ink)
        if D is None:
            return None
        thresh = grain * 0.55 * (1 - self.tooth)
        eff = np.maximum(0.0, D * (1 - 0.35 * grain + 0.35 * grain * self.tooth) - thresh * 0.35)
        return maxa * (1 - np.exp(-3.2 * eff))

    def compose(self, inks=None):
        """Paper + charcoal as an RGB image."""
        out = self.rgb.copy()
        for name in (inks or INKS):
            a = self.coverage(name)
            if a is None:
                continue
            color = np.array(INKS[name][0], np.float32)
            out = out * (1 - a[..., None]) + color * a[..., None]
        return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))

    def alpha_layer(self, inks=None):
        """Charcoal only, as a transparent RGBA image (for layouts in other tools)."""
        rgb = np.zeros((self.h, self.w, 3), np.float32)
        acc = np.zeros((self.h, self.w), np.float32)
        for name in (inks or INKS):
            a = self.coverage(name)
            if a is None:
                continue
            color = np.array(INKS[name][0], np.float32)
            rgb = rgb * (1 - a[..., None]) + color * a[..., None]
            acc = acc + a * (1 - acc)
        safe = np.maximum(acc, 1e-6)[..., None]
        col = np.clip(rgb / safe, 0, 255)
        arr = np.dstack([col, acc[..., None] * 255]).astype(np.float32)
        return Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8), "RGBA")
