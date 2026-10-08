"""Laboratorio de dibujo sensorial: procedural sound for the reel.

Everything is synthesised here, so the audio is original and has no licence
restrictions:

  musica()   warm instrumental bed: soft pad, plucked notes with a gentle
             pulse and a brushed shaker, with a small room reverb
  roce()     charcoal on paper: band-passed grainy noise whose loudness
             follows the drawing speed of the strokes on screen
  toque()    short tap for each dot

All functions return float32 mono or stereo arrays at RATE.
"""

import numpy as np

RATE = 48000


def _env(n, a, r, sustain=1.0):
    t = np.arange(n) / RATE
    e = np.minimum(1.0, t / max(a, 1e-4)) * sustain
    rel = np.clip((n / RATE - t) / max(r, 1e-4), 0, 1)
    return e * rel


def _pluck(freq, dur, rng, bright=0.5, decay=0.996):
    """Karplus-Strong plucked string."""
    n = int(dur * RATE)
    period = max(2, int(RATE / freq))
    buf = rng.uniform(-1, 1, period)
    # soften the excitation for a warm, felt-like attack
    for _ in range(int(3 - 2 * bright)):
        buf = 0.5 * (buf + np.roll(buf, 1))
    out = np.empty(n, np.float64)
    for i in range(n):
        j = i % period
        v = buf[j]
        out[i] = v
        buf[j] = decay * 0.5 * (v + buf[(j + 1) % period])
    return out * _env(n, 0.002, 0.08)


def _onepole(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def _bandpass(x, lo, hi):
    """FFT band-pass with soft shoulders."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1 / RATE)
    X = np.fft.rfft(x)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, n)


def _reverb(x, seconds=1.8, mix=0.25, seed=3):
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    ir_l = rng.standard_normal(n) * np.exp(-t * 6.9 / seconds)
    ir_r = rng.standard_normal(n) * np.exp(-t * 6.9 / seconds)
    ir_l, ir_r = _bandpass(ir_l, 150, 5000), _bandpass(ir_r, 150, 5000)
    ir_l /= np.sqrt((ir_l ** 2).sum())
    ir_r /= np.sqrt((ir_r ** 2).sum())
    m = len(x) + n
    size = 1 << int(np.ceil(np.log2(m)))
    X = np.fft.rfft(x, size)
    wl = np.fft.irfft(X * np.fft.rfft(ir_l, size), size)[:len(x)]
    wr = np.fft.irfft(X * np.fft.rfft(ir_r, size), size)[:len(x)]
    dry = np.stack([x, x], 1)
    return (1 - mix) * dry + mix * np.stack([wl, wr], 1)


def nota(name):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    pc = names[name[0]] + (1 if "#" in name else 0)
    octave = int(name[-1])
    return 440.0 * 2 ** ((pc + 12 * (octave + 1) - 69) / 12)


def musica(dur, bpm=84, seed=11):
    """Warm instrumental bed in D major (pentatonic melody, slow chords)."""
    rng = np.random.default_rng(seed)
    n = int(dur * RATE)
    beat = 60 / bpm
    t = np.arange(n) / RATE

    # pad: four chords, two bars each, additive sines with slow vibrato
    chords = [("D3", "A3", "E4", "F#4"), ("B2", "F#3", "D4", "A4"),
              ("G2", "D3", "B3", "F#4"), ("A2", "E3", "C#4", "G4")]
    bar = 4 * beat
    pad = np.zeros(n)
    for k in range(int(np.ceil(dur / (2 * bar))) + 1):
        notes = chords[k % len(chords)]
        s0 = k * 2 * bar
        i0, i1 = int(s0 * RATE), min(n, int((s0 + 2 * bar + 1.2) * RATE))
        if i0 >= n:
            break
        tt = t[i0:i1] - s0
        env = np.minimum(1, tt / 1.2) * np.clip((2 * bar + 1.2 - tt) / 1.2, 0, 1)
        for name in notes:
            f = nota(name)
            vib = 1 + 0.002 * np.sin(2 * np.pi * 0.23 * tt + rng.uniform(0, 6))
            ph = 2 * np.pi * f * tt * vib
            pad[i0:i1] += env * (0.6 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
    pad = _onepole(pad, 1400) * 0.05

    # plucks: gentle eighth-note pulse on a pentatonic line, sparse in the first bar
    scale = ["D4", "E4", "F#4", "A4", "B4", "D5", "E5"]
    plucks = np.zeros(n)
    step = beat / 2
    i = 0
    idx = 2
    while i * step < dur - 0.3:
        s = i * step
        bar_pos = i % 8
        play = (bar_pos in (0, 3, 4, 6)) if s < 2 * bar else (bar_pos in (0, 2, 3, 4, 6, 7))
        if s > dur - 4.5:          # breathe out towards the end
            play = bar_pos in (0, 4)
        if play:
            idx = int(np.clip(idx + rng.choice([-2, -1, 1, 1, 2]), 0, len(scale) - 1))
            vel = 0.55 + 0.35 * rng.random() + (0.15 if bar_pos == 0 else 0)
            p = _pluck(nota(scale[idx]), 1.6, rng, bright=0.4)
            a = int(s * RATE)
            b = min(n, a + len(p))
            plucks[a:b] += vel * p[:b - a]
        i += 1
    plucks *= 0.16

    # low pulse: soft sine thump on beats 1 and 3
    pulse = np.zeros(n)
    for k in range(int(dur / beat) + 1):
        if k % 2:
            continue
        a = int(k * beat * RATE)
        m = int(0.35 * RATE)
        tt = np.arange(m) / RATE
        thump = np.sin(2 * np.pi * (58 + 30 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
        b = min(n, a + m)
        pulse[a:b] += thump[:b - a]
    pulse *= 0.10

    # brushed shaker on off-beats
    shaker = np.zeros(n)
    noise = _bandpass(rng.standard_normal(n), 3000, 11000)
    for k in range(int(dur / (beat / 2)) + 1):
        if k % 2 == 0 or k * beat / 2 < 2 * bar:
            continue
        a = int(k * beat / 2 * RATE)
        m = int(0.09 * RATE)
        b = min(n, a + m)
        tt = np.arange(b - a) / RATE
        shaker[a:b] += noise[a:b] * np.exp(-tt * 45) * (0.5 + 0.5 * rng.random())
    shaker *= 0.05

    mono = pad + plucks + pulse + shaker
    st = _reverb(mono, 2.2, 0.3)
    fade = np.minimum(1, t / 0.6) * np.clip((dur - t) / 2.5, 0, 1)
    return (st * fade[:, None]).astype(np.float32)


def roce(speed, seed=5):
    """Charcoal on paper. `speed` is drawn length per second, one value per sample."""
    rng = np.random.default_rng(seed)
    n = len(speed)
    grain = rng.standard_normal(n)
    # paper tooth: random amplitude flutter
    flutter = np.repeat(rng.uniform(0.3, 1.0, n // 120 + 1), 120)[:n]
    body = _bandpass(grain * flutter, 700, 5200)
    hiss = _bandpass(rng.standard_normal(n), 4000, 12000) * 0.25
    level = np.clip(speed / 900.0, 0, 1.4) ** 0.7
    level = _onepole(level, 30)
    sig = (body + hiss) * level
    return (sig / (np.abs(sig).max() + 1e-9) * 0.5).astype(np.float32)


def toque(seed=0):
    """A single soft tap of charcoal on paper (for dots)."""
    rng = np.random.default_rng(seed)
    m = int(0.06 * RATE)
    tt = np.arange(m) / RATE
    x = _bandpass(rng.standard_normal(m), 400, 6000) * np.exp(-tt * 70)
    x += 0.4 * np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 60)
    return (x / (np.abs(x).max() + 1e-9) * 0.5).astype(np.float32)
