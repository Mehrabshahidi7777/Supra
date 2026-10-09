"""gltrans.py — scene transitions ported from gl-transitions (GLSL) to numpy + OpenCV.

Source: https://github.com/gl-transitions/gl-transitions (MIT License,
Copyright (c) 2017-present gl-transitions contributors; each port names its original author below).
The GLSL math is kept 1:1 (uv origin bottom-left, y up) so results match the originals; only the
sampling runs on the CPU with cv2.remap. No GPU, no pip installs: numpy + opencv only.

Use in a renderer:
    from gltrans import transition, NAMES
    out = transition('cube', frame_a, frame_b, p)      # p = 0..1, uint8 HxWx3 in, uint8 out
    out = transition('crosswarp', a, b, p, ease='inout')   # optional easing on p

Quick look from the shell (two clips -> short preview mp4, or a contact sheet):
    python3 kit/gltrans.py demo A.mp4 2.0 B.mp4 5.0 cube out.mp4 [--dur 0.6 --fps 60 --size 1080x1920]
    python3 kit/gltrans.py sheet A.mp4 2.0 B.mp4 5.0 cube sheet.jpg
    python3 kit/gltrans.py list

All ports avoid white flashes and particles (house taste). Frames are any size; renders are usually 1080x1920
and upscaled later by finish4k.sh. Typical length: 0.4–0.8 s, cut so p = 0.5 lands on the beat.
"""
import sys
import numpy as np
import cv2

# ----------------------------------------------------------------------------- core helpers
_GRID = {}


def _grid(h, w):
    """GL-style uv for pixel centres: u right, v UP (0 at bottom)."""
    k = (h, w)
    if k not in _GRID:
        u = (np.arange(w, dtype=np.float32) + 0.5) / w
        v = 1.0 - (np.arange(h, dtype=np.float32) + 0.5) / h
        U, V = np.meshgrid(u, v)
        _GRID[k] = (U, V)
    return _GRID[k]


_BORDER = {'clamp': cv2.BORDER_REPLICATE, 'black': cv2.BORDER_CONSTANT, 'wrap': cv2.BORDER_WRAP}


def samp(img, u, v, border='clamp'):
    """Sample img (uint8 HxWx3) at GL uv arrays -> float32 HxWx3 in 0..255 (bilinear)."""
    h, w = img.shape[:2]
    mx = (u * w - 0.5).astype(np.float32)
    my = ((1.0 - v) * h - 0.5).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=_BORDER[border], borderValue=(0, 0, 0))
    return out.astype(np.float32)


def mix(a, b, m):
    """GLSL mix for images: m scalar or HxW mask."""
    if np.isscalar(m):
        return a + (b - a) * np.float32(m)
    return a + (b - a) * m[..., None]


def where(mask, a, b):
    return np.where(mask[..., None], a, b)


def inb(u, v):
    return (u > 0) & (u < 1) & (v > 0) & (v < 1)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def step(edge, x):
    return (np.asarray(x) >= edge).astype(np.float32)


def _f(img):
    return img.astype(np.float32)


def _u8(x):
    return np.clip(x + 0.5, 0, 255).astype(np.uint8)


def _ratio(img):
    return img.shape[1] / img.shape[0]


def _hash(x, y):
    """GLSL rand(vec2): fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453)."""
    s = np.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return s - np.floor(s)


# ----------------------------------------------------------------------------- 3D / perspective
def cube(a, b, p, persp=0.7, unzoom=0.3, reflection=0.4, floating=3.0, bg=None):
    """3D cube turning from A to B. Author: gre."""
    U, V = _grid(*a.shape[:2])
    uz = unzoom * 2.0 * (0.5 - abs(0.5 - p))
    X = -uz * 0.5 + (1 + uz) * U
    Y = -uz * 0.5 + (1 + uz) * V

    def xskew(px, py, pr, center):
        x = px if center < 0.5 else 1.0 - px
        y = (py - 0.5 * (1.0 - pr) * x) / (1.0 + (pr - 1.0) * x)
        return (x, y) if center < 0.5 else (1.0 - x, y)

    fu, fv = xskew((X - p) / (1.0 - p), Y, 1.0 - p * (1.0 - persp), 0.0)
    tu, tv = xskew(X / p, Y, p * p * (1.0 - persp) + persp, 1.0)
    return _persp_compose(a, b, (fu, fv), (tu, tv), reflection, floating, bg, p)


def _persp_compose(a, b, fp, tp, reflection, floating, bg, p, to_first=False):
    fu, fv = fp
    tu, tv = tp
    base = _background(a, b, p, bg)
    # floor reflection (y is mirrored below the image, fading with height)
    for img, (qu, qv) in ((a, fp), (b, tp)):
        ru, rv = qu, -1.2 * qv - floating / 100.0
        m = inb(ru, rv)
        if m.any() and reflection > 0:
            w = (reflection * (1.0 - rv)) * m
            base = base + samp(img, ru, rv) * w[..., None]
    mf, mt = inb(fu, fv), inb(tu, tv)
    out = base
    if to_first:
        out = where(mf, samp(a, fu, fv), out)
        out = where(mt, samp(b, tu, tv), out)
    else:
        out = where(mt, samp(b, tu, tv), out)
        out = where(mf, samp(a, fu, fv), out)
    return _u8(out)


def _background(a, b, p, bg):
    """None/'black' = original black stage; 'blur' = dark blurred mix of both shots (cleaner on vertical)."""
    if bg in (None, 'black'):
        return np.zeros(a.shape, np.float32)
    if bg == 'blur':
        h, w = a.shape[:2]
        sm = cv2.resize(_u8(mix(_f(a), _f(b), p)), (w // 8, h // 8), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), 6)
        return cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.45
    return np.zeros(a.shape, np.float32) + np.float32(bg)


def doorway(a, b, p, reflection=0.4, perspective=0.4, depth=3.0, bg=None):
    """A opens like two doors, B comes forward from behind. Author: gre."""
    U, V = _grid(*a.shape[:2])
    slit = 2.0 * np.abs(U - 0.5) - p
    open_ = slit > 0
    fu = U + np.where(U > 0.5, -1.0, 1.0) * 0.5 * p
    d = 1.0 / (1.0 + perspective * p * (1.0 - slit))
    fv = (V - d / 2) * d + d / 2
    fu = np.where(open_, fu, -1.0)
    fv = np.where(open_, fv, -1.0)
    size = 1.0 + (depth - 1.0) * (1.0 - p)
    tu = (U - 0.5) * size + 0.5
    tv = (V - 0.5) * size + 0.5
    base = _background(a, b, p, bg)
    ru, rv = tu, -1.2 * tv - 0.02
    m = inb(ru, rv)
    if m.any():
        base = base + samp(b, ru, rv) * (reflection * (1.0 - rv) * m)[..., None]
    out = where(inb(tu, tv), samp(b, tu, tv), base)
    out = where(inb(fu, fv), samp(a, fu, fv), out)
    return _u8(out)


def swap(a, b, p, reflection=0.4, perspective=0.2, depth=3.0, bg=None):
    """Cards swap in 3D: A swings back-left, B comes in from the right. Author: gre."""
    U, V = _grid(*a.shape[:2])
    size = 1.0 + (depth - 1.0) * p
    ps = perspective * p
    fu = U * (size / (1.0 - perspective * p))
    fv = (V - 0.5) * (size / (1.0 - size * ps * U)) + 0.5
    size2 = 1.0 + (depth - 1.0) * (1.0 - p)
    ps2 = perspective * (1.0 - p)
    tu = (U - 1.0) * (size2 / (1.0 - perspective * (1.0 - p))) + 1.0
    tv = (V - 0.5) * (size2 / (1.0 - size2 * ps2 * (0.5 - U))) + 0.5
    return _persp_compose(a, b, (fu, fv), (tu, tv), reflection, 2.0, bg, p, to_first=(p >= 0.5))


def book_flip(a, b, p):
    """Page turn from right to left, with page shading. Author: hong."""
    U, V = _grid(*a.shape[:2])
    e = 1e-4
    dr = 0.5 - p if abs(0.5 - p) > e else e
    dl = p - 0.5 if abs(p - 0.5) > e else e
    rx = (U - p) / dr * 0.5
    ry = (V - 0.5) / (0.5 + p * (U - 0.5) / 0.5) * 0.5 + 0.5
    lx = (U - 0.5) / dl * 0.5 + 0.5
    ly = (V - 0.5) / (0.5 + (1.0 - p) * (0.5 - U) / 0.5) * 0.5 + 0.5
    shade = max(0.7, abs(p - 0.5) * 2.0)
    pr = step(1.0 - p, U)
    left = U < 0.5
    A, B = _f(a), _f(b)
    out_l = mix(A, samp(b, lx, ly) * shade, pr)
    out_r = mix(samp(a, rx, ry) * shade, B, pr)
    return _u8(where(left, out_l, out_r))


def grid_flip(a, b, p, cols=3, rows=5, pause=0.1, divider=0.05, randomness=0.1):
    """Tiles flip one by one like cards (black grid lines). Author: TimDonselaar. Default grid fits 9:16."""
    U, V = _grid(*a.shape[:2])
    sx, sy = float(cols), float(rows)
    rw, rh = 1.0 / sx, 1.0 / sy
    px, py = np.floor(sx * U), np.floor(sy * V)
    minx = np.minimum(np.abs(U - rw * px), np.abs(U - rw * (px + 1)))
    miny = np.minimum(np.abs(V - rh * (py + 1)), np.abs(V - rh * py))
    on_div = np.minimum(minx, miny) < min(rw, rh) * divider
    A, B = _f(a), _f(b)
    black = np.zeros_like(A)
    if p < pause:
        al = np.where(on_div, 1.0 - p / pause, 1.0).astype(np.float32)
        return _u8(mix(black, A, al))
    if p >= 1.0 - pause:
        al = np.where(on_div, (p - 1.0 + pause) / pause, 1.0).astype(np.float32)
        return _u8(mix(black, B, al))
    cp_ = (p - pause) / (1.0 - 2 * pause)
    r = _hash(px, py) - randomness
    cp = smoothstep(0.0, 1.0 - r, cp_)
    delta = px * rw
    off = rw / 2 + delta
    k = np.maximum(np.abs(cp - 0.5), 1e-4)
    qu = (U - off) / k * 0.5 + off
    fa, fb = samp(a, qu, V), samp(b, qu, V)
    s = (k >= np.abs(sx * (U - delta) - 0.5)).astype(np.float32)
    face = where(cp <= 0.5, fa, fb)
    out = mix(black, face, s)
    out = where(on_div, black, out)
    return _u8(out)


# ----------------------------------------------------------------------------- warps
def crosswarp(a, b, p):
    """Left-to-right warp: A shrinks into the right edge, B grows out of the left. Author: Eke Péter."""
    U, V = _grid(*a.shape[:2])
    x = smoothstep(0.0, 1.0, p * 2.0 + U - 1.0)
    A = samp(a, (U - 0.5) * (1 - x) + 0.5, (V - 0.5) * (1 - x) + 0.5)
    B = samp(b, (U - 0.5) * x + 0.5, (V - 0.5) * x + 0.5)
    return _u8(mix(A, B, x))


def directional_warp(a, b, p, direction=(-1.0, 1.0), smoothness=0.1):
    """Diagonal warp wipe (default: towards the top-left). Author: pschroen."""
    U, V = _grid(*a.shape[:2])
    vx, vy = np.array(direction, np.float32) / np.linalg.norm(direction)
    s = abs(vx) + abs(vy)
    vx, vy = vx / s, vy / s
    d = vx * 0.5 + vy * 0.5
    m = 1.0 - smoothstep(-smoothness, 0.0, vx * U + vy * V - (d - 0.5 + p * (1.0 + smoothness)))
    A = samp(a, (U - 0.5) * (1 - m) + 0.5, (V - 0.5) * (1 - m) + 0.5)
    B = samp(b, (U - 0.5) * m + 0.5, (V - 0.5) * m + 0.5)
    return _u8(mix(A, B, m))


def swirl(a, b, p, radius=1.0, turns=4.0):
    """Whirlpool twist in the middle of the cut. Author: Sergey Kosarevsky (port by gre).
    turns: original 8 (very heavy); 4 keeps the car readable longer."""
    U, V = _grid(*a.shape[:2])
    x, y = U - 0.5, V - 0.5
    dist = np.sqrt(x * x + y * y)
    pct = np.clip((radius - dist) / radius, 0, None)
    amt = p / 0.5 if p <= 0.5 else 1.0 - (p - 0.5) / 0.5
    th = pct * pct * amt * turns * np.pi
    c, s = np.cos(th), np.sin(th)
    qx = x * c - y * s
    qy = x * s + y * c
    qx = np.where(dist < radius, qx, x) + 0.5
    qy = np.where(dist < radius, qy, y) + 0.5
    return _u8(mix(samp(a, qx, qy), samp(b, qx, qy), p))


def ripple(a, b, p, amplitude=100.0, speed=50.0):
    """Water ripple from the centre. Author: gre."""
    U, V = _grid(*a.shape[:2])
    dx, dy = U - 0.5, V - 0.5
    dist = np.sqrt(dx * dx + dy * dy)
    k = (np.sin(p * dist * amplitude - p * speed) + 0.5) / 30.0 * p
    A = samp(a, U + dx * k, V + dy * k)
    return _u8(mix(A, _f(b), float(smoothstep(0.2, 1.0, p))))


def morph(a, b, p, strength=0.1):
    """Colours push the pixels: A melts into B along its own shapes. Author: paniq."""
    U, V = _grid(*a.shape[:2])
    A, B = _f(a) / 255.0, _f(b) / 255.0
    oa_x, oa_y = A[..., 0] + A[..., 2] - 1.0, A[..., 1] + A[..., 2] - 1.0
    ob_x, ob_y = B[..., 0] + B[..., 2] - 1.0, B[..., 1] + B[..., 2] - 1.0
    ox, oy = (oa_x + ob_x) * 0.5 * strength, (oa_y + ob_y) * 0.5 * strength
    w0, w1 = p, 1.0 - p
    fa = samp(a, U + ox * w0, V + oy * w0)
    fb = samp(b, U - ox * w1, V - oy * w1)
    return _u8(mix(fa, fb, p))


def kaleidoscope(a, b, p, speed=1.0, angle=1.0, power=1.5):
    """Mirror-kaleidoscope burst at the middle of the cut. Author: nwoeanhinnogaehr."""
    U, V = _grid(*a.shape[:2])
    t = (p ** power) * speed
    x, y = U - 0.5, V - 0.5
    for _ in range(7):
        x, y = np.sin(t) * x + np.cos(t) * y, np.sin(t) * y - np.cos(t) * x
        t += angle
        x = np.abs(np.mod(x, 2.0) - 1.0)
        y = np.abs(np.mod(y, 2.0) - 1.0)
    plain = mix(_f(a), _f(b), p)
    kal = mix(samp(a, x, y), samp(b, x, y), p)
    return _u8(mix(plain, kal, 1.0 - 2.0 * abs(p - 0.5)))


def flyeye(a, b, p, size=0.04, zoom=50.0, separation=0.3):
    """Insect-eye lens grid with RGB split. Author: gre."""
    U, V = _grid(*a.shape[:2])
    inv = 1.0 - p
    dx, dy = size * np.cos(zoom * U), size * np.sin(zoom * V)
    to = samp(b, U + inv * dx, V + inv * dy)
    fr = np.empty_like(to)
    for ch, k in ((0, 1.0 - separation), (1, 1.0), (2, 1.0 + separation)):
        fr[..., ch] = samp(a, U + p * dx * k, V + p * dy * k)[..., ch]
    return _u8(to * p + fr * inv)


def squeeze(a, b, p, separation=0.04):
    """A squeezes flat to a line (with RGB split), revealing B. Author: gre."""
    U, V = _grid(*a.shape[:2])
    if p >= 1:
        return b.copy()
    y = 0.5 + (V - 0.5) / (1.0 - p)
    inside = (y >= 0) & (y <= 1)
    off = p * separation
    c = samp(a, U, y)
    out = c.copy()
    out[..., 0] = samp(a, U, y - off)[..., 0]
    out[..., 2] = samp(a, U, y + off)[..., 2]
    return _u8(where(inside, out, _f(b)))


# ----------------------------------------------------------------------------- spins / pushes with motion blur
def revolve(a, b, p, center=(0.46, 0.52), direction=-1.0, max_rot=1.95, peak_zoom=2.22, swirl_amt=2.85,
            barrel=0.38, blur=1.0, switch=(0.30, 0.50), shadow=0.16, samples=9):
    """Spin + zoom + lens barrel with real motion blur — a heavy, smooth 'revolve' cut. Author: Revolve_Left.

    samples: motion-blur taps (original 17; 9 looks the same at 1080p and is 2x faster)."""
    if p <= 0:
        return a.copy()
    if p >= 1:
        return b.copy()
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    sat = lambda x: min(max(x, 0.0), 1.0)
    ease = lambda x: sat(x) * sat(x) * (3 - 2 * sat(x))
    env = lambda t: ease((t - 0.10) / 0.33) * (1.0 - ease((t - 0.43) / 0.29))
    cx, cy = center
    X0 = (U - cx) * ratio
    Y0 = V - cy
    R0 = np.sqrt(X0 * X0 + Y0 * Y0)
    core = np.power(1.0 - np.clip(R0 / 0.96, 0, 1), 1.55)

    def warp(t):
        e = env(t)
        ang = direction * (max_rot * e + swirl_amt * e * core)
        c, s = np.cos(-ang), np.sin(-ang)
        x, y = c * X0 - s * Y0, s * X0 + c * Y0
        sc = 1.0 + (peak_zoom - 1.0) * e ** 0.85
        x, y = x / sc, y / sc
        rr2 = x * x + y * y
        k = 1.0 + barrel * e * rr2 * 2.8
        x, y = x * k / ratio, y * k
        return np.clip(x + cx, 0.001, 0.999), np.clip(y + cy, 0.001, 0.999)

    e = env(p)
    span = 0.060 * blur * e
    n = max(1, samples // 2)
    acc, tot = 0.0, 0.0
    taps = [0.0] if span < 1e-4 else [i / n for i in range(-n, n + 1)]
    for x in taps:
        w = (1.0 - abs(x)) ** 2 + 0.01
        t = sat(p + x * span)
        qu, qv = warp(t)
        rv = float(smoothstep(switch[0], switch[1], t))
        col = samp(a, qu, qv) if rv <= 0 else (samp(b, qu, qv) if rv >= 1 else mix(samp(a, qu, qv), samp(b, qu, qv), rv))
        acc = acc + col * w
        tot += w
    col = acc / tot
    qx, qy = (U - 0.5) * ratio, V - 0.5
    vig = 1.0 - shadow * e * smoothstep(0.35, 0.95, np.sqrt(qx * qx + qy * qy))
    return _u8(col * vig[..., None])


def _keyspline(x, x1, y1, x2, y2):
    A = lambda a1, a2: 1 - 3 * a2 + 3 * a1
    B = lambda a1, a2: 3 * a2 - 6 * a1
    C = lambda a1: 3 * a1
    bez = lambda t, a1, a2: ((A(a1, a2) * t + B(a1, a2)) * t + C(a1)) * t
    slope = lambda t, a1, a2: 3 * A(a1, a2) * t * t + 2 * B(a1, a2) * t + C(a1)
    t = x
    for _ in range(4):
        sl = slope(t, x1, x2)
        if sl == 0:
            break
        t -= (bez(t, x1, x2) - x) / sl
    return bez(t, y1, y2)


def tangent_blur(a, b, p, samples=12, seed=0):
    """A swings away around the corner with heavy motion blur, B swings in. Author: chenkai."""
    h, w = a.shape[:2]
    U, V = _grid(h, w)
    ratio = _ratio(a)
    et = _keyspline(p, .68, .01, .17, .98)
    blur = np.exp(-20.0 * (et - 0.5) ** 2)
    rot = np.pi

    def rot_uv(t):
        r = rot * t if t <= 0.5 else -rot + rot * t
        y = V / ratio
        c, s = np.cos(r), np.sin(r)
        x0, y0 = U - 1.0, y
        x1 = c * x0 + s * y0
        y1 = -s * x0 + c * y0
        return x1 + 1.0, y1 * ratio

    cu, cv_ = rot_uv(et)
    dt = 0.0167 * 2.0
    nu, nv = rot_uv(et + dt)
    spu, spv = (nu - cu) / dt * blur * 0.5, (nv - cv_) / dt * blur * 0.5
    src = a if et <= 0.5 else b
    rng = np.random.default_rng(seed)
    off = rng.random((h, w), dtype=np.float32)
    acc = np.zeros((h, w, 3), np.float32)
    tot = 0.0
    for i in range(samples + 1):
        pc = (i + off) / samples
        wt = 4.0 * (pc - pc * pc)
        qu, qv = cu + spu * pc, cv_ + spv * pc
        qu, qv = qu - np.floor(qu), qv - np.floor(qv)
        acc += samp(src, qu, qv, 'wrap') * wt[..., None]
        tot = tot + wt
    return _u8(acc / tot[..., None])


def push_scaled(a, b, p, direction=(0.0, 1.0), scale=0.7):
    """A pushes out as a shrinking card while B pushes in (default: upwards). Author: Thibaut Foussard."""
    U, V = _grid(*a.shape[:2])
    ep = np.sin(p * np.pi / 2) ** 3
    sx, sy = np.sign(direction[0]), np.sign(direction[1])
    px, py = U + ep * sx, V + ep * sy
    fx, fy = px - np.floor(px), py - np.floor(py)
    s = 1.0 - (1.0 - 1.0 / scale) * np.sin(p * np.pi)
    fx, fy = (fx - 0.5) * s + 0.5, (fy - 0.5) * s + 0.5
    on_a = (px >= 0) & (px <= 1) & (py >= 0) & (py <= 1)
    col = where(on_a, samp(a, fx, fy), samp(b, fx, fy))
    border = (fx >= 0) & (fx <= 1) & (fy >= 0) & (fy <= 1)
    return _u8(col * border[..., None])


def window_slice(a, b, p, count=6.0, smoothness=0.5):
    """Venetian-blind slices sweep across. Author: gre. count=6 suits 9:16."""
    U, V = _grid(*a.shape[:2])
    pr = smoothstep(-smoothness, 0.0, U - p * (1.0 + smoothness))
    fr = count * U
    s = (fr - np.floor(fr) >= pr).astype(np.float32)
    return _u8(mix(_f(a), _f(b), s))


# ----------------------------------------------------------------------------- registry + easing
TRANSITIONS = {
    # name: (function, suggested seconds, one-line description)
    'cube': (cube, 0.7, '3D cube turn (black stage + floor reflection; bg="blur" for a cleaner stage)'),
    'doorway': (doorway, 0.7, 'A opens like doors, B flies forward'),
    'swap': (swap, 0.7, '3D cards swap places'),
    'book_flip': (book_flip, 0.7, 'page turn with shading'),
    'grid_flip': (grid_flip, 0.9, 'tiles flip like cards'),
    'crosswarp': (crosswarp, 0.5, 'warp wipe left -> right'),
    'directional_warp': (directional_warp, 0.5, 'diagonal warp wipe'),
    'swirl': (swirl, 0.6, 'whirlpool twist'),
    'ripple': (ripple, 0.6, 'water ripple'),
    'morph': (morph, 0.6, 'colour-driven melt'),
    'kaleidoscope': (kaleidoscope, 0.7, 'mirror burst'),
    'flyeye': (flyeye, 0.5, 'insect-eye lens + RGB split'),
    'squeeze': (squeeze, 0.4, 'squeeze to a line + RGB split'),
    'revolve': (revolve, 0.8, 'spin + zoom + barrel with motion blur (heavy)'),
    'tangent_blur': (tangent_blur, 0.6, 'swing around the corner with motion blur'),
    'push_scaled': (push_scaled, 0.6, 'card push upwards with scale'),
    'window_slice': (window_slice, 0.5, 'blinds sweep'),
}
NAMES = list(TRANSITIONS)


def ease_p(p, kind):
    if kind in (None, 'linear'):
        return p
    if kind == 'in':
        return p * p * p
    if kind == 'out':
        return 1 - (1 - p) ** 3
    if kind == 'inout':
        return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2
    raise ValueError(kind)


def transition(name, a, b, p, ease=None, **kw):
    """Run transition `name` at progress p (0..1). a, b: uint8 HxWx3 of the same size."""
    p = float(min(max(ease_p(float(p), ease), 0.0), 1.0))
    if p <= 0:
        return a.copy()
    if p >= 1:
        return b.copy()
    return TRANSITIONS[name][0](a, b, p, **kw)


# ----------------------------------------------------------------------------- CLI previews
def _read_at(path, t, size):
    import subprocess
    w, h = size
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1',
           '-vf', f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3).copy()


def _read_range(path, t, n, fps, size):
    import subprocess
    w, h = size
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', str(n),
           '-vf', f'fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    if len(fr) < n:  # hold the last frame if the source is short
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr


def _main(argv):
    import argparse
    import subprocess
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['demo', 'sheet', 'list'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--dur', type=float, default=None)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--size', default='1080x1920')
    ap.add_argument('--hold', type=float, default=0.5, help='seconds of A before and B after (demo)')
    ap.add_argument('--ease', default=None)
    o = ap.parse_args(argv)
    if o.cmd == 'list':
        for k, (_, d, desc) in TRANSITIONS.items():
            print(f'{k:18s} {d:.1f}s  {desc}')
        return
    A, ta, B, tb, name, out = o.args
    ta, tb = float(ta), float(tb)
    size = tuple(int(x) for x in o.size.split('x'))
    dur = o.dur or TRANSITIONS[name][1]
    if o.cmd == 'sheet':
        a, b = _read_at(A, ta, size), _read_at(B, tb, size)
        ps = [0.0, 0.15, 0.3, 0.45, 0.55, 0.7, 0.85, 1.0]
        tiles = [cv2.resize(transition(name, a, b, q, ease=o.ease), (size[0] // 4, size[1] // 4),
                            interpolation=cv2.INTER_AREA) for q in ps]
        img = np.concatenate(tiles, axis=1)
        cv2.imwrite(out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(out)
        return
    nh, nt = int(round(o.hold * o.fps)), int(round(dur * o.fps))
    fa = _read_range(A, ta, nh + nt, o.fps, size)
    fb = _read_range(B, tb, nt + nh, o.fps, size)
    w, h = size
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
                            '-r', str(o.fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                            '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(nh):
        enc.stdin.write(fa[i].tobytes())
    for i in range(nt):
        q = (i + 0.5) / nt
        enc.stdin.write(transition(name, fa[nh + i], fb[i], q, ease=o.ease).tobytes())
    for i in range(nh):
        enc.stdin.write(fb[nt + i].tobytes())
    enc.stdin.close()
    enc.wait()
    print(out)


if __name__ == '__main__':
    _main(sys.argv[1:])
