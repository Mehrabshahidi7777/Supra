"""vfx.py — camera / time effects for velocity-style car edits (numpy + OpenCV, CPU only).

What is here (everything else — glow, grain, RGB split, zoom/whip blur, glitch — already lives in the
project renderers, see edit_toolkit/README.md):

  Clip(path, t0, t1, size)        frames of a source range in memory; .at(t) gives ANY time, also between
                                  source frames, using optical flow (smooth slow motion from 30/60 fps clips)
  Clip.shutter(t0, t1, taps)      average of several times = real motion blur for the fast part of a ramp
  ramp_times(n, fps, keys)        speed-ramp curve -> source time of every output frame (velocity edit)
  ramp_frames(clip, n, fps, keys) the whole ramp rendered: slow parts flow-interpolated, fast parts blurred
  flow_interp(a, b, t)            in-between frame of two frames (optical flow, DIS)
  tilt3d(img, yaw, pitch, roll)   3D camera swing of a shot (perspective plane), auto-zoomed so no borders show
  shake(img, t, amp, ...)         smooth handheld / impact shake with motion blur along the movement
  lens_warp(img, k)               barrel (k>0) or pinch (k<0) lens pulse, auto-cover
  echo(history, decay)            light / ghost trails of the last frames (taillights at night)
  light_leak(h, w, t, ...)        soft coloured leak (warm or teal) to screen over a shot — never white

Typical velocity shot (60 fps output):
    from vfx import Clip, ramp_frames
    clip = Clip('clips/m4.mp4', 1.2, 3.0, (1080, 1920))
    frames = ramp_frames(clip, n=90, fps=60, keys=[(0, 1.0), (0.35, 0.2), (1.0, 0.2), (1.2, 3.0), (1.5, 1.0)])

Self-test: python3 kit/vfx.py selftest <video> <t> out_dir
"""
import subprocess
import sys
import numpy as np
import cv2


# ----------------------------------------------------------------------------- reading
def read_frames(path, t0, t1, size, fps=None):
    """Decode [t0, t1) at the source frame rate (or `fps`), scaled+cropped to size=(w, h). RGB uint8 (N,h,w,3)."""
    w, h = size
    vf = f'scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}'
    if fps:
        vf = f'fps={fps},' + vf
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t0:.4f}', '-i', path, '-t', f'{t1 - t0:.4f}', '-vf', vf,
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def source_fps(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate',
                        '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    n, d = r.split('/')
    return float(n) / float(d)


# ----------------------------------------------------------------------------- optical flow
_DIS = None


def _dis():
    global _DIS
    if _DIS is None:
        _DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return _DIS


def flow_pair(a, b, scale=0.5):
    """Forward (a->b) and backward (b->a) flow in full-res pixels, computed at `scale` for speed."""
    h, w = a.shape[:2]
    sw, sh = int(w * scale), int(h * scale)
    ga = cv2.cvtColor(cv2.resize(a, (sw, sh), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor(cv2.resize(b, (sw, sh), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    fab = _dis().calc(ga, gb, None)
    fba = _dis().calc(gb, ga, None)
    up = lambda f: cv2.resize(f, (w, h), interpolation=cv2.INTER_LINEAR) / scale
    return up(fab), up(fba)


_BASE = {}


def _base(h, w):
    if (h, w) not in _BASE:
        X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        _BASE[(h, w)] = (X, Y)
    return _BASE[(h, w)]


def flow_interp(a, b, t, flows=None, scale=0.5):
    """Frame at fraction t between a (t=0) and b (t=1). Linear-motion flow projection (Super-SloMo style)."""
    t = float(t)  # numpy float64 scalars would turn the maps into float64 (cv2.remap needs float32)
    if t <= 1e-3:
        return a.copy()
    if t >= 1 - 1e-3:
        return b.copy()
    fab, fba = flows if flows is not None else flow_pair(a, b, scale)
    h, w = a.shape[:2]
    X, Y = _base(h, w)
    ft0 = -(1 - t) * t * fab + t * t * fba
    ft1 = (1 - t) * (1 - t) * fab - t * (1 - t) * fba
    wa = cv2.remap(a, X + ft0[..., 0], Y + ft0[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(b, X + ft1[..., 0], Y + ft1[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return cv2.addWeighted(wa, 1 - t, wb, t, 0)


class Clip:
    """A source range held in memory. Times are seconds from t0 (local clip time)."""

    def __init__(self, path, t0, t1, size=(1080, 1920), flow_scale=0.5):
        self.fps = source_fps(path)
        self.frames = read_frames(path, t0, t1, size)
        self.n = len(self.frames)
        self.dur = self.n / self.fps
        self.flow_scale = flow_scale
        self._flows = {}

    def _flow(self, i):
        if i not in self._flows:
            self._flows[i] = flow_pair(self.frames[i], self.frames[i + 1], self.flow_scale)
            if len(self._flows) > 6:  # keep memory small
                self._flows.pop(next(iter(self._flows)))
        return self._flows[i]

    def at(self, t, smooth=True):
        """Frame at local time t; between source frames uses optical flow (smooth=True) or a blend."""
        x = float(min(max(t * self.fps, 0.0), self.n - 1.0))
        i = int(np.floor(x))
        f = x - i
        if i >= self.n - 1 or f < 0.02:
            return self.frames[min(i, self.n - 1)].copy()
        if f > 0.98:
            return self.frames[i + 1].copy()
        if not smooth:
            return cv2.addWeighted(self.frames[i], 1 - f, self.frames[i + 1], f, 0)
        return flow_interp(self.frames[i], self.frames[i + 1], f, self._flow(i))

    def shutter(self, t0, t1, taps=5):
        """Motion blur: mean of `taps` samples between t0 and t1 (use for speeds > 1.5x)."""
        if taps <= 1 or abs(t1 - t0) * self.fps < 0.6:
            return self.at((t0 + t1) / 2)
        acc = np.zeros(self.frames[0].shape, np.float32)
        for k in range(taps):
            acc += self.at(t0 + (t1 - t0) * (k + 0.5) / taps, smooth=False)
        return np.clip(acc / taps + 0.5, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- speed ramps
def ramp_times(n, fps, keys, start=0.0):
    """Source time for each of n output frames. keys = [(out_time_s, speed), ...]; speed eases (smoothstep)
    between keys. Returns (times, speeds)."""
    ko = np.array([k[0] for k in keys], np.float64)
    ks = np.array([k[1] for k in keys], np.float64)
    sub = 8
    to = np.arange(n * sub + 1) / (fps * sub)
    j = np.clip(np.searchsorted(ko, to, side='right') - 1, 0, len(ko) - 1)
    j2 = np.clip(j + 1, 0, len(ko) - 1)
    span = np.maximum(ko[j2] - ko[j], 1e-9)
    f = np.clip((to - ko[j]) / span, 0, 1)
    f = f * f * (3 - 2 * f)
    sp = ks[j] + (ks[j2] - ks[j]) * f
    src = start + np.concatenate([[0], np.cumsum((sp[1:] + sp[:-1]) / 2) / (fps * sub)])
    return src[::sub][:n], sp[::sub][:n]


def ramp_frames(clip, n, fps, keys, start=0.0, blur_from=1.6, taps=5):
    """Render a speed ramp from a Clip: slow parts flow-interpolated, fast parts with shutter blur."""
    times, speeds = ramp_times(n + 1, fps, keys, start)
    out = []
    for i in range(n):
        if speeds[i] >= blur_from:
            out.append(clip.shutter(times[i], times[i + 1], taps))
        else:
            out.append(clip.at(times[i]))
    return out


# ----------------------------------------------------------------------------- camera moves
def _rot(yaw, pitch, roll):
    y, p, r = np.radians([yaw, pitch, roll])
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    Rz = np.array([[np.cos(r), -np.sin(r), 0], [np.sin(r), np.cos(r), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def tilt3d(img, yaw=0.0, pitch=0.0, roll=0.0, zoom=1.0, fov=50.0, cover=True, shift=(0.0, 0.0)):
    """Rotate the shot like a card in 3D (degrees). cover=True zooms just enough that no border shows.
    shift: extra pan in fractions of width/height. Swing yaw 0->12 over a shot = cheap 3D camera move."""
    h, w = img.shape[:2]
    f = (h / 2) / np.tan(np.radians(fov) / 2)
    R = _rot(yaw, pitch, roll)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    c = src - [w / 2, h / 2]
    P = (R @ np.c_[c, np.zeros(4)].T).T
    dst = f * P[:, :2] / (f + P[:, 2:3])
    H0 = cv2.getPerspectiveTransform(src, np.float32(dst))

    def full(z):
        S = np.array([[z, 0, w / 2 + shift[0] * w], [0, z, h / 2 + shift[1] * h], [0, 0, 1]])
        return S @ H0

    z = zoom
    if cover:
        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h], [w / 2, 0], [w, h / 2], [w / 2, h], [0, h / 2]])
        for _ in range(60):
            back = cv2.perspectiveTransform(corners[None], np.linalg.inv(full(z)))[0]
            if (back[:, 0] >= -0.5).all() and (back[:, 0] <= w + 0.5).all() and \
               (back[:, 1] >= -0.5).all() and (back[:, 1] <= h + 0.5).all():
                break
            z *= 1.02
    return cv2.warpPerspective(img, full(z), (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def _noise1(t, freq, seed, octaves=3):
    rng = np.random.default_rng(seed)
    v = 0.0
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        ph = rng.random(2) * 2 * np.pi
        fr = freq * (1.93 ** o)
        v += amp * (np.sin(2 * np.pi * fr * t + ph[0]) * 0.6 + np.sin(2 * np.pi * fr * 1.37 * t + ph[1]) * 0.4)
        tot += amp
        amp *= 0.5
    return v / tot


def _line_kernel(dx, dy):
    L = int(min(max(abs(dx), abs(dy)), 80))
    if L < 2:
        return None
    k = np.zeros((2 * L + 1, 2 * L + 1), np.float32)
    n = max(abs(dx), abs(dy))
    cv2.line(k, (int(L - dx * L / n), int(L - dy * L / n)), (int(L + dx * L / n), int(L + dy * L / n)), 1.0, 1,
             cv2.LINE_AA)
    return k / k.sum()


def shake(img, t, amp=0.015, freq=7.0, rot=1.2, seed=0, blur=True, strength=1.0):
    """Smooth shake at time t (seconds). amp = fraction of width, rot = degrees. strength scales it (e.g. a
    decaying envelope after a beat hit). Adds motion blur along the movement. Zooms to hide edges."""
    h, w = img.shape[:2]
    s = strength
    if s <= 1e-3:
        return img.copy()
    pos = lambda tt: (_noise1(tt, freq, seed) * amp * w * s, _noise1(tt, freq, seed + 1) * amp * w * s,
                      _noise1(tt, freq * 0.8, seed + 2) * rot * s)
    dx, dy, da = pos(t)
    z = 1.0 + 2.2 * amp * s + abs(np.radians(rot * s)) * 0.6
    M = cv2.getRotationMatrix2D((w / 2, h / 2), da, z)
    M[:, 2] += (dx, dy)
    out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if blur:
        dt = 1 / 60
        nx, ny, _ = pos(t + dt)
        k = _line_kernel((nx - dx) * 0.5, (ny - dy) * 0.5)
        if k is not None:
            out = cv2.filter2D(out, -1, k, borderType=cv2.BORDER_REFLECT)
    return out


def lens_warp(img, k=0.25, center=(0.5, 0.5), cover=True):
    """Barrel bulge (k > 0) or pinch (k < 0). Animate k with a beat envelope for a lens 'punch'."""
    h, w = img.shape[:2]
    X, Y = _base(h, w)
    cx, cy = center[0] * w, center[1] * h
    nx, ny = (X - cx) / (h / 2), (Y - cy) / (h / 2)
    r2 = nx * nx + ny * ny
    fac = 1.0 / (1.0 + k * r2)
    if cover and k < 0:
        rmax2 = ((w / 2) ** 2 + (h / 2) ** 2) / (h / 2) ** 2
        fac = fac * (1.0 + k * rmax2)
    mx = (cx + nx * fac * (h / 2)).astype(np.float32)
    my = (cy + ny * fac * (h / 2)).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ----------------------------------------------------------------------------- trails + leaks
def echo(history, decay=0.62, mode='lighten'):
    """Trails from the last frames (history[-1] = current). 'lighten' keeps only bright things (lights, chrome);
    'mean' gives a ghost of the whole car."""
    cur = history[-1].astype(np.float32)
    if mode == 'lighten':
        out = cur.copy()
        wgt = 1.0
        for fr in reversed(history[:-1]):
            wgt *= decay
            out = np.maximum(out, fr.astype(np.float32) * wgt)
        return np.clip(out, 0, 255).astype(np.uint8)
    acc, tot, wgt = cur.copy(), 1.0, 1.0
    for fr in reversed(history[:-1]):
        wgt *= decay
        acc += fr.astype(np.float32) * wgt
        tot += wgt
    return np.clip(acc / tot, 0, 255).astype(np.uint8)


LEAK_WARM = ((255, 120, 40), (255, 60, 30), (255, 190, 90))
LEAK_TEAL = ((40, 200, 255), (90, 80, 255), (40, 255, 200))
LEAK_RED = ((255, 30, 40), (200, 20, 80), (255, 90, 40))


def light_leak(img, t, palette=LEAK_WARM, strength=0.55, speed=0.35, seed=3):
    """Soft moving colour leak from the frame edges, screen-blended. Palette in RGB; never goes white
    (highlights are capped) — house taste: no white flashes."""
    h, w = img.shape[:2]
    sw, sh = 54, 96
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    layer = np.zeros((sh, sw, 3), np.float32)
    for i, col in enumerate(palette):
        ph = rng.random(3) * 2 * np.pi
        side = rng.random()
        cx = (0.0 if side < 0.5 else 1.0) * sw + np.sin(t * speed * 2 * np.pi + ph[0]) * sw * 0.35
        cy = (0.2 + 0.6 * rng.random()) * sh + np.sin(t * speed * 1.3 * 2 * np.pi + ph[1]) * sh * 0.3
        rad = (0.45 + 0.25 * np.sin(t * speed * 2 * np.pi + ph[2])) * sw
        g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad * rad)))
        layer += g[..., None] * np.float32(col) / 255.0
    layer = np.clip(layer, 0, 0.85) * strength
    layer = cv2.resize(layer, (w, h), interpolation=cv2.INTER_CUBIC)
    base = img.astype(np.float32) / 255.0
    out = 1.0 - (1.0 - base) * (1.0 - layer)
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- self-test
def _selftest(video, t, out_dir):
    import os
    import time
    os.makedirs(out_dir, exist_ok=True)
    clip = Clip(video, t, t + 1.0, (1080, 1920))
    a = clip.frames[0]
    tiles = []
    tm = {}

    def run(name, fn):
        t0 = time.time()
        r = fn()
        tm[name] = (time.time() - t0) * 1000
        tiles.append((name, r))

    run('original', lambda: a)
    run('flow t=0.5', lambda: clip.at(0.5 / clip.fps))
    run('tilt3d y14 p6', lambda: tilt3d(a, yaw=14, pitch=6))
    run('shake', lambda: shake(a, 0.37, amp=0.03, rot=2.5))
    run('lens +0.35', lambda: lens_warp(a, 0.35))
    run('lens -0.25', lambda: lens_warp(a, -0.25))
    run('echo', lambda: echo(list(clip.frames[:12]), 0.75))
    run('leak warm', lambda: light_leak(a, 0.4))
    run('leak teal', lambda: light_leak(a, 0.8, LEAK_TEAL))
    rows = []
    for name, im in tiles:
        s = cv2.resize(im, (270, 480), interpolation=cv2.INTER_AREA)
        cv2.putText(s, name, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        rows.append(s)
    sheet = np.concatenate(rows, 1)
    cv2.imwrite(os.path.join(out_dir, 'vfx_selftest.jpg'), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
    for k, v in tm.items():
        print(f'{k:16s} {v:7.0f} ms')
    times, sp = ramp_times(120, 60, [(0, 1.0), (0.4, 0.2), (1.2, 0.2), (1.5, 3.0), (2.0, 1.0)])
    print('ramp: 2.0 s out uses', round(times[-1], 3), 's of source; min/max speed', sp.min().round(2), sp.max())


if __name__ == '__main__':
    if len(sys.argv) >= 5 and sys.argv[1] == 'selftest':
        _selftest(sys.argv[2], float(sys.argv[3]), sys.argv[4])
    else:
        print(__doc__)
