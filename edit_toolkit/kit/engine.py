"""engine.py — recipe-driven edit engine for MEHRAB.7w7 Shorts. Effect / transition numbers = the VFX pack (1-59).

A reference becomes a RECIPE (projects/<night>/recipe.py): song window + beat grid, a shot list on the beats, a
transition number on each cut, effect numbers per shot or for the whole video, hook text, end card and loop. The
engine does the rest: 9:16 framing, optical-flow in-betweens (smooth 60 fps from 30 fps clips, slow-mo, speed
ramps with shutter blur), transitions centred on the beat, looks, beat punches, the MEHRAB.7w7 line (3/4 height,
adaptive shadow), end card, seamless loop, -14 LUFS audio with tape-stop ending, 4K60 master + 1080p chat copy,
cover. Anything reference-specific stays in the recipe as plain python functions (fx / pre / texts).

  export WORK=/home/claude/work_edit
  python3 kit/engine.py plan   projects/x/recipe.py                 # timeline table + source-length checks
  python3 kit/engine.py stills projects/x/recipe.py 0.1 2.4 5.0    # chosen times -> $WORK/<name>/check/stills.jpg
  python3 kit/engine.py sheet  projects/x/recipe.py [--step 0.5]   # whole edit as a contact sheet
  python3 kit/engine.py cover  projects/x/recipe.py                 # 1080x1920 cover JPG (recipe 'cover')
  python3 kit/engine.py render projects/x/recipe.py [--workers 2] [--no-4k]

RECIPE (python dict; times in seconds; paths relative to $WORK, 'repo:<path>' = repo root, or absolute):
  name      outputs go to $WORK/<name>/
  song      audio or video file with the song;  song_in = song time at video frame 0 (put it on a beat)
  beat      beat period in s (beats.py 'period')   — or —   grid = [song times of beats] for a free grid
  shots     list of shots (below), back to back on the beat grid
  look      [numbers | {'n': 52, 'mix': .8, ...params} | fn(img, ctx)] applied to every frame
  punch     {'every': 1, 'zoom': 0.035, 'shake': 0.0, 'decay': 0.09, 'from': 0.0} zoom pulse on the beats
  texts     [{'text', 't0', 't1', 'y': .30, 'size': 120, 'color': '#ffffff', 'style': 'clean'|'plate',
              'colors': {...build_plate colours}, 'skew': -0.1, 'font': path}]
  outro     {'beats': 2 (or 'dur'), 'text': 'MEHRAB.7w7', 'style': 'glow', 'color': '#ffffff', 'bg': 'blur'|'black',
              'trans': number (cut from the last shot into the card), 'tdur': .4, 'size': 150}
  loop      {'trans': 33, 'dur': .30}  last part of the end card turns into frame 0, so the Short loops
  tapestop  True (deep slowed ending from the outro start);  lufs -14;  grain 0.010;  id_line True
  cover     {'t': 0.4, 'texts': [...]}   frame used for the cover + optional cover-only texts

SHOT keys:
  src       video or image;  at = in-point (s);  beats = length in beats (0.5 ok)  or  dur = seconds
  zoom 1.0 (= largest 9:16 crop), cx / cy 0..1 (crop centre in the source), flip False
  push      extra zoom over the shot (0.06 = slow push in; negative = pull out); focus (fx, fy) 0..1
  speed     number, or ramp keys [(q, speed), ...] with q 0..1 over the shot (18 / 19 in fx = default ramp / slow-mo)
  flow      True: optical-flow in-betweens (smooth); shutter blur kicks in above speed 1.6
  fx        [numbers | {'n': .., ...} | fn(img, ctx)]  (ctx: q 0..1 in shot, u local s, t global s, fi, env, rng)
  pre       [fn(img, ctx)] clean-up before framing effects (inpaint plates, logos ...)
  trans     transition number into the NEXT shot (None = hard cut);  tdur seconds;  ease None|'inout'
  text      shorthand: a text shown over this shot ({'text': ..} or a string)

Numbers: 1-17 and 25-48 = transitions (gltrans.NUMBERS); 18-24 and 49-59 = effects (FX below).
"""
import importlib.util
import json
import os
import subprocess
import sys
import time

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

KIT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(KIT, '..', '..'))
sys.path.insert(0, KIT)
import gltrans as G  # noqa: E402
import vfx  # noqa: E402
from lib import text_mask, build_plate, place, hexc, dilate, ease_out_back, FONT, FONT_REG  # noqa: E402

W, H, FPS = 1080, 1920, 60
WM_CY = 1452          # MEHRAB.7w7 line: ~3/4 height, above the YouTube / Instagram / Facebook / WhatsApp overlays
WORK = os.environ.get('WORK', '/home/claude/work_edit')


# ============================================================================ recipe loading
def path_of(p):
    if p is None:
        return None
    if p.startswith('repo:'):
        return os.path.join(REPO, p[5:])
    return p if os.path.isabs(p) else os.path.join(WORK, p)


def load_recipe(path):
    path = os.path.abspath(path)
    if path.endswith('.json'):
        R = json.load(open(path))
    else:
        spec = importlib.util.spec_from_file_location('recipe', path)
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.dirname(path))
        spec.loader.exec_module(mod)
        R = mod.RECIPE
    R = dict(R)
    R.setdefault('name', os.path.basename(os.path.dirname(path)))
    R['_dir'] = os.path.join(WORK, R['name'])
    os.makedirs(os.path.join(R['_dir'], 'check'), exist_ok=True)
    return R


# ============================================================================ media probing
def probe(path):
    """(width, height, fps, duration) of a video with rotation applied; images: fps 0."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp'):
        im = cv2.imread(path)
        return im.shape[1], im.shape[0], 0.0, 1e9
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,avg_frame_rate:stream_side_data=rotation:stream_tags=rotate:'
                          'format=duration', '-of', 'json', path], capture_output=True, text=True).stdout
    j = json.loads(out)
    st = j['streams'][0]
    w, h = st['width'], st['height']
    rot = 0
    for sd in st.get('side_data_list', []) or []:
        if 'rotation' in sd:
            rot = int(sd['rotation'])
    rot = int(st.get('tags', {}).get('rotate', rot))
    if abs(rot) % 180 == 90:
        w, h = h, w
    n, d = st['avg_frame_rate'].split('/')
    fps = float(n) / float(d) if float(d) else 30.0
    return w, h, fps, float(j['format'].get('duration', 0) or 0)


def crop_box(sw, sh, zoom=1.0, cx=0.5, cy=0.5):
    """Largest 9:16 window in the source / zoom, centred at (cx, cy) fractions, clamped inside the frame."""
    if sw / sh > W / H:
        bh, bw = sh, sh * W / H
    else:
        bw, bh = sw, sw * H / W
    ww, wh = bw / zoom, bh / zoom
    x = min(max(cx * sw - ww / 2, 0), sw - ww)
    y = min(max(cy * sh - wh / 2, 0), sh - wh)
    return int(round(x)), int(round(y)), max(2, int(round(ww))) // 2 * 2, max(2, int(round(wh))) // 2 * 2


# ============================================================================ shot source
class Source:
    """Frames of one shot's source window, framed to 1080x1920, with flow in-betweens and shutter blur."""
    MAX_FRAMES = 150   # memory guard: 150 frames x 6.2 MB ≈ 0.9 GB per shot

    def __init__(self, spec, span, tmap):
        self.spec = spec
        self.path = path_of(spec['src'])
        self.tmap = tmap                      # local u (s) -> source time (s)
        sw, sh, fps, dur = probe(self.path)
        self.still = fps == 0
        x, y, cw, ch = crop_box(sw, sh, spec.get('zoom', 1.0), spec.get('cx', 0.5), spec.get('cy', 0.5))
        if self.still:
            im = cv2.cvtColor(cv2.imread(self.path), cv2.COLOR_BGR2RGB)[y:y + ch, x:x + cw]
            im = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA if cw > W else cv2.INTER_LANCZOS4)
            if spec.get('flip'):
                im = im[:, ::-1].copy()
            self.frames = [im]
            self.fps, self.t0 = 1.0, 0.0
            return
        s0, s1 = tmap(0.0), tmap(span)
        lo, hi = min(s0, s1), max(s0, s1)
        lo, hi = max(0.0, lo - 1.0 / fps), min(dur, hi + 2.0 / fps) if dur else hi + 2.0 / fps
        need = max(hi - lo, 1.0 / fps)
        self.fps = fps if need * fps <= self.MAX_FRAMES else self.MAX_FRAMES / need
        vf = f'crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos'
        if spec.get('flip'):
            vf += ',hflip'
        if self.fps < fps - 0.01:
            vf = f'fps={self.fps:.4f},' + vf
        cmd = ['ffmpeg', '-v', 'error', '-ss', f'{lo:.4f}', '-i', self.path, '-t', f'{need:.4f}', '-vf', vf,
               '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
        if len(fr) == 0:
            raise RuntimeError(f'no frames from {self.path} at {lo:.2f}s')
        self.frames = list(fr)
        self.t0 = lo
        self._flows = {}

    def _flow(self, i):
        if i not in self._flows:
            self._flows[i] = vfx.flow_pair(self.frames[i], self.frames[i + 1], 0.5)
            if len(self._flows) > 4:
                self._flows.pop(next(iter(self._flows)))
        return self._flows[i]

    def at_src(self, st, smooth=True):
        if self.still:
            return self.frames[0]
        x = float(min(max((st - self.t0) * self.fps, 0.0), len(self.frames) - 1.0))
        i = int(np.floor(x))
        f = x - i
        if i >= len(self.frames) - 1 or f < 0.03:
            return self.frames[min(i, len(self.frames) - 1)]
        if f > 0.97:
            return self.frames[i + 1]
        if not smooth:
            return cv2.addWeighted(self.frames[i], 1 - f, self.frames[i + 1], f, 0)
        return vfx.flow_interp(self.frames[i], self.frames[i + 1], f, self._flow(i))

    def frame(self, u):
        st = self.tmap(u)
        st2 = self.tmap(u + 1.0 / FPS)
        sp = abs(st2 - st) * FPS
        if not self.still and sp > 1.6:              # fast: real shutter blur instead of strobing
            taps = int(min(6, 2 + sp))
            acc = np.zeros((H, W, 3), np.float32)
            for k in range(taps):
                acc += self.at_src(st + (st2 - st) * (k + 0.5) / taps, smooth=False)
            return np.clip(acc / taps + 0.5, 0, 255).astype(np.uint8)
        return self.at_src(st, smooth=self.spec.get('flow', True))


def make_tmap(spec, span, visible):
    """Local time u (0..span) -> source time. Speed keys are over the visible part of the shot (q 0..1)."""
    at = float(spec.get('at', 0.0))
    sp = spec.get('speed', None)
    fx = [f for f in spec.get('fx', []) if isinstance(f, int)]
    if sp is None and 18 in fx:
        sp = [(0.0, 1.6), (0.25, 0.3), (0.7, 0.3), (1.0, 1.8)]
    if sp is None and 19 in fx:
        sp = 0.4
    if sp is None:
        sp = 1.0
    if np.isscalar(sp):
        return lambda u, s=float(sp): at + u * s
    din, (v0, v1) = visible
    keys = np.array(sp, np.float64)
    us = np.linspace(-0.5, span + 0.5, 2048)
    q = np.clip((us - v0) / max(v1 - v0, 1e-6), 0, 1)
    j = np.clip(np.searchsorted(keys[:, 0], q, side='right') - 1, 0, len(keys) - 1)
    j2 = np.clip(j + 1, 0, len(keys) - 1)
    f = np.clip((q - keys[j, 0]) / np.maximum(keys[j2, 0] - keys[j, 0], 1e-9), 0, 1)
    f = f * f * (3 - 2 * f)
    s = keys[j, 1] + (keys[j2, 1] - keys[j, 1]) * f
    src = np.concatenate([[0], np.cumsum((s[1:] + s[:-1]) / 2 * np.diff(us))])
    src -= np.interp(0.0, us, src)
    return lambda u: at + float(np.interp(u, us, src))


# ============================================================================ effects by number
def _bump(q):
    return float(np.sin(np.pi * min(max(q, 0.0), 1.0)))


FX = {
    20: lambda im, c, **k: vfx.tilt3d(im, **{**dict(yaw=-7 + 14 * c['q'], pitch=3 - 6 * c['q'],
                                                     roll=-1.5 + 3 * c['q']), **k}),
    21: lambda im, c, **k: vfx.shake(im, c['t'], **{**dict(amp=0.025, rot=2.0, freq=11, strength=c['env']), **k}),
    22: lambda im, c, **k: vfx.lens_warp(im, k.get('k', 0.32) * c['env']),
    23: lambda im, c, **k: vfx.echo(c['hist'][-k.get('n', 9):], k.get('decay', 0.78)),
    24: lambda im, c, **k: vfx.light_leak(im, c['t'], **{**dict(strength=0.55), **k}),
    49: lambda im, c, **k: vfx.reflection(im, **{**dict(boundary=0.72, t=c['u'] * 6.0), **k}),
    50: lambda im, c, **k: vfx.tilt_shift(im, **{**dict(blur=80, gradient=420, y=0.6), **k}),
    51: lambda im, c, **k: vfx.crt(im, **{**dict(t=c['u'] * 25, line_width=3.0, line_contrast=0.4), **k}),
    52: lambda im, c, **k: vfx.old_film(im, **{**dict(seed=float(np.random.default_rng(c['fi'] // 2).random()),
                                                      sepia=0.55, scratch_density=0.5, noise=0.10,
                                                      vignetting=0.22, vignetting_alpha=0.75), **k}),
    53: lambda im, c, **k: vfx.ascii_art(im, **{**dict(size=12), **k}),
    54: lambda im, c, **k: vfx.cross_hatch(im, **{**dict(spacing=12, width=2), **k}),
    55: lambda im, c, **k: vfx.emboss(im, **{**dict(strength=4.0), **k}),
    56: lambda im, c, **k: vfx.twist(im, **{**dict(radius=0.5, angle=6.0 * _bump(c['q'])), **k}),
    57: lambda im, c, **k: vfx.lens_blur(im, **{**dict(radius=20 * _bump(c['q']), brightness=0.8), **k}),
    58: lambda im, c, **k: vfx.ink(im, **{**dict(strength=0.3), **k}),
    59: lambda im, c, **k: vfx.edge_work(im, **{**dict(radius=8, tint=(0, 230, 255)), **k}),
}
TIME_FX = {18, 19}   # handled by make_tmap


def apply_fx(img, items, ctx):
    for it in items or []:
        if callable(it):
            img = it(img, ctx)
            continue
        kw = dict(it) if isinstance(it, dict) else {'n': it}
        n = kw.pop('n')
        mixk = kw.pop('mix', 1.0)
        if n in TIME_FX:
            continue
        if n not in FX:
            raise ValueError(f'{n} is not an effect number (transitions go in "trans"): {sorted(FX)}')
        out = FX[n](img, ctx, **kw)
        if mixk < 1.0:
            out = cv2.addWeighted(img, 1 - mixk, out, mixk, 0)
        img = out
    return img


# ============================================================================ text layers
_TEXT = {}


def text_layer(spec):
    """Premultiplied (rgb float 0..1, alpha) layer for a text spec (cached)."""
    key = json.dumps({k: v for k, v in spec.items() if k in ('text', 'size', 'color', 'style', 'colors', 'skew',
                                                             'font', 'depth')}, sort_keys=True)
    if key in _TEXT:
        return _TEXT[key]
    size = spec.get('size', 120)
    font = spec.get('font', FONT)
    style = spec.get('style', 'clean')
    m = text_mask(spec['text'], size, font=font, stretch=(1.0, 1.0) if style == 'clean' else (0.88, 1.10),
                  skew=spec.get('skew', 0.0 if style == 'clean' else -0.13), pad=60)
    if style == 'plate':
        cols = dict(top='#ff5040', mid='#ff0d18', low='#d8000e', bottom='#7a0009', ext_near='#6a0008',
                    ext_far='#100002')
        cols.update(spec.get('colors', {}))
        rgb, a, _ = build_plate(m, depth=spec.get('depth', max(8, size // 6)), **cols)
    else:
        col = hexc(spec.get('color', '#ffffff'))
        sh = cv2.GaussianBlur(dilate(m, max(2, size // 22)), (0, 0), max(2, size / 14)) * 0.65
        rim = cv2.GaussianBlur(dilate(m, max(2, size // 30)), (0, 0), 1.2) * 0.9
        rgb = np.zeros(m.shape + (3,), np.float32)
        a = np.zeros(m.shape, np.float32)
        for lay_a, lay_c in ((sh, (0, 0, 0)), (rim, (0.02, 0.02, 0.03)), (m, col)):
            rgb = np.float32(lay_c)[None, None] * lay_a[..., None] + rgb * (1 - lay_a[..., None])
            a = lay_a + a * (1 - lay_a)
    _TEXT[key] = (rgb.astype(np.float32), a.astype(np.float32))
    return _TEXT[key]


def draw_text(f, spec, t):
    t0, t1 = spec['t0'], spec['t1']
    if not (t0 <= t < t1):
        return f
    q_in = (t - t0) / spec.get('in', 0.18)
    q_out = (t1 - t) / spec.get('out', 0.12)
    sc = float(0.6 + 0.4 * ease_out_back(min(q_in, 1.0))) if spec.get('pop', True) else 1.0
    al = float(np.clip(min(q_in * 1.5, q_out, 1.0), 0, 1))
    rgb, a = text_layer(spec)
    cx = spec.get('x', 0.5) * W
    cy = spec.get('y', 0.30) * H
    r, aa = place(f, np.ones((H, W), np.float32), rgb, a, cx, cy, scale=sc * spec.get('scale', 1.0), alpha=al)
    return r


def name_masks(text, size, font=FONT, skew=-0.08, track=0.03, pad=60):
    """Per-letter masks of `text` on one canvas (italic skew), plus the full mask — for letter-by-letter reveals."""
    f = ImageFont.truetype(font, size)
    widths = [f.getlength(c) for c in text]
    trk = size * track
    tw = sum(widths) + trk * (len(text) - 1)
    asc, desc = f.getmetrics()
    hh = asc + desc + 2 * pad
    ww = int(tw + 2 * pad + abs(skew) * hh)
    per, x = [], pad + (abs(skew) * hh if skew < 0 else 0)
    M = np.float32([[1, skew, -skew * hh / 2], [0, 1, 0]])
    for c, wd in zip(text, widths):
        im = Image.new('L', (ww, hh), 0)
        ImageDraw.Draw(im).text((x, pad), c, font=f, fill=255)
        m = cv2.warpAffine(np.asarray(im, np.float32) / 255, M, (ww, hh), flags=cv2.INTER_LINEAR)
        per.append(m)
        x += wd + trk
    full = np.max(per, 0)
    ys, xs = np.where(full > 0.01)
    y0, y1, x0, x1 = max(0, ys.min() - 20), ys.max() + 21, max(0, xs.min() - 20), xs.max() + 21
    return full[y0:y1, x0:x1], [m[y0:y1, x0:x1] for m in per]


# ============================================================================ ID line + finish
def _id_layers():
    wm = Image.new('L', (W, 110), 0)
    d = ImageDraw.Draw(wm)
    f = ImageFont.truetype(FONT_REG, 44)
    tx = 'MEHRAB.7w7'
    tw = sum(f.getlength(c) for c in tx) + 3 * (len(tx) - 1)
    xx = (W - tw) / 2
    for c in tx:
        d.text((xx, 30), c, font=f, fill=255)
        xx += f.getlength(c) + 3
    m = np.asarray(wm, np.float32) / 255
    sh = cv2.GaussianBlur(m, (0, 0), 4)
    ol = np.clip(cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)), (0, 0), 1.0) - m, 0, 1)
    rows = np.where(m.max(1) > 0.5)[0]
    return m, sh, ol, int(WM_CY - (rows.min() + rows.max()) / 2)


WM, WM_SH, WM_OL, WM_Y = _id_layers()
GRAIN = None


def finish(f, fi, R):
    """float 0..1 frame -> uint8 with the MEHRAB.7w7 line and grain."""
    global GRAIN
    if R.get('id_line', True):
        reg = f[WM_Y:WM_Y + 110]
        bgl = float(reg[20:90, 300:780].mean())
        kb = float(np.clip((bgl - 0.50) / 0.35, 0, 1))
        reg[:] = reg * (1 - WM_SH[..., None] * (0.55 + 0.40 * kb))
        if kb > 0.01:
            reg[:] = reg * (1 - WM_OL[..., None] * 0.85 * kb)
        reg[:] = reg * (1 - WM[..., None] * 0.95) + WM[..., None] * 0.95
    g = R.get('grain', 0.010)
    if g > 0:
        if GRAIN is None:
            GRAIN = [np.random.default_rng(60 + i).normal(0, 1, (H, W)).astype(np.float16) for i in range(6)]
        f = f + (GRAIN[fi % 6].astype(np.float32) * g)[..., None]
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


# ============================================================================ the edit
class Edit:
    def __init__(self, R):
        self.R = R
        self.song_in = float(R.get('song_in', 0.0))
        if 'grid' in R:
            g = np.array(R['grid'], np.float64) - self.song_in
            per = float(np.median(np.diff(g))) if len(g) > 1 else 0.5
            self._bt = np.concatenate([g, g[-1] + per * np.arange(1, 400)])
        else:
            self._bt = np.arange(0, 2000) * float(R.get('beat', 0.5))
        self._build()

    # beat index <-> video time (fractional beats allowed)
    def bt(self, x):
        return float(np.interp(x, np.arange(len(self._bt)), self._bt))

    def bi(self, t):
        return float(np.interp(t, self._bt, np.arange(len(self._bt))))

    def _build(self):
        R = self.R
        segs = []
        t = 0.0
        for i, s in enumerate(R['shots']):
            if 'beats' in s:
                e = self.bt(self.bi(t) + s['beats'])
            else:
                e = t + float(s['dur'])
            segs.append(dict(kind='shot', i=i, spec=s, s=t, e=e))
            t = e
        o = dict(R.get('outro', {}))
        oe = self.bt(self.bi(t) + o['beats']) if 'beats' in o else t + float(o.get('dur', 1.0))
        segs.append(dict(kind='outro', spec=o, s=t, e=oe))
        # transitions: into the next segment, centred on the cut
        for k, sg in enumerate(segs):
            nxt = sg['spec'].get('trans') if sg['kind'] == 'shot' else None
            if k == len(segs) - 2:
                nxt = sg['spec'].get('trans', o.get('trans'))
            sg['tout'] = None
            sg['dout'] = 0.0
            if nxt is not None and k < len(segs) - 1:
                name = G.NUMBERS.get(nxt)
                if name not in G.TRANSITIONS:
                    raise ValueError(f'shot {k}: {nxt} is not a transition number')
                d = float(sg['spec'].get('tdur', o.get('tdur') if k == len(segs) - 2 else None)
                          or G.TRANSITIONS[name][1])
                d = min(d, (sg['e'] - sg['s']) * 0.9, (segs[k + 1]['e'] - segs[k + 1]['s']) * 0.9)
                sg['tout'], sg['dout'] = name, d
        for k, sg in enumerate(segs):
            sg['din'] = segs[k - 1]['dout'] if k else 0.0
            sg['a'] = sg['s'] - sg['din'] / 2            # first visible time (incl. transition)
            sg['b'] = sg['e'] + sg['dout'] / 2           # last visible time
        self.segs = segs
        self.T = segs[-1]['e']
        self.N = int(round(self.T * FPS))
        lp = R.get('loop', {'trans': 33, 'dur': 0.30})
        self.loop = None
        if lp:
            self.loop = (G.NUMBERS[lp['trans']], float(lp.get('dur', 0.30)))
        self.texts = [dict(x) for x in R.get('texts', [])]
        for sg in segs:
            tx = sg['spec'].get('text') if sg['kind'] == 'shot' else None
            if tx:
                d = {'text': tx} if isinstance(tx, str) else dict(tx)
                d.setdefault('t0', sg['s'])
                d.setdefault('t1', sg['e'])
                self.texts.append(d)
        p = R.get('punch')
        self.hits = []
        if p:
            k, every = 0, int(p.get('every', 1))
            while self.bt(k) < self.T:
                if self.bt(k) >= p.get('from', 0.0) and k % every == 0:
                    self.hits.append(self.bt(k))
                k += 1
        self.cache = {}
        self.hist = {}
        self._frame0 = None
        self._outro_bg = None

    # ------------------------------------------------------------------ sources
    def source(self, k):
        if k not in self.cache:
            sg = self.segs[k]
            span = sg['b'] - sg['a']
            vis = (sg['din'], (sg['s'] - sg['a'], sg['e'] - sg['a']))
            sg['tmap'] = make_tmap(sg['spec'], span, vis)
            self.cache[k] = Source(sg['spec'], span, sg['tmap'])
        return self.cache[k]

    def evict(self, t):
        for k in list(self.cache):
            if self.segs[k]['b'] < t - 0.05:
                del self.cache[k]
                self.hist.pop(k, None)

    def env(self, t, decay=0.09):
        past = [h for h in self.hits if h <= t + 1e-6]
        return float(np.exp(-(t - past[-1]) / decay)) if past else 0.0

    def ctx(self, k, t, fi):
        sg = self.segs[k]
        q = (t - sg['s']) / max(sg['e'] - sg['s'], 1e-6)
        beats = [self.bt(j) for j in range(int(self.bi(t)) - 1, int(self.bi(t)) + 2)]
        last = max([b for b in beats if b <= t + 1e-6] or [0.0])
        return dict(q=float(np.clip(q, 0, 1)), u=t - sg['a'], t=t, fi=fi, k=k, seg=sg,
                    env=float(np.exp(-(t - last) / 0.09)), rng=np.random.default_rng(1000 + fi),
                    hist=self.hist.get(k, []))

    def shot_frame(self, k, t, fi):
        sg = self.segs[k]
        if sg['kind'] == 'outro':
            return self.outro_frame(t, fi)
        src = self.source(k)
        c = self.ctx(k, t, fi)
        img = src.frame(c['u'])
        if sg['spec'].get('pre'):
            img = apply_fx(img, sg['spec']['pre'], c)
        push = sg['spec'].get('push', 0.0)
        if push:
            z = 1.0 + push * c['q'] if push > 0 else 1.0 - push * (1 - c['q'])
            fx_, fy_ = sg['spec'].get('focus', (0.5, 0.5))
            M = cv2.getRotationMatrix2D((fx_ * W, fy_ * H), 0, z)
            img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fxs = sg['spec'].get('fx', [])
        if any((i == 23 or (isinstance(i, dict) and i.get('n') == 23)) for i in fxs):
            self.hist[k] = (self.hist.get(k, []) + [img])[-12:]
            c['hist'] = self.hist[k]
        return apply_fx(img, fxs, c)

    # ------------------------------------------------------------------ end card
    def outro_frame(self, t, fi):
        o = self.segs[-1]['spec']
        sg = self.segs[-1]
        q = (t - sg['s']) / max(sg['e'] - sg['s'], 1e-6)
        if self._outro_bg is None:
            if o.get('bg', 'blur') == 'blur' and len(self.segs) > 1:
                last = self.shot_frame(len(self.segs) - 2, self.segs[-2]['e'] - 1e-3, fi).astype(np.float32)
                sm = cv2.resize(last, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
                bg = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 5), (W, H)) * 0.35
            else:
                bg = np.zeros((H, W, 3), np.float32) + 5
            self._outro_bg = bg.astype(np.float32)
        f = self._outro_bg.copy() / 255.0
        text = o.get('text', 'MEHRAB.7w7')
        size = o.get('size', 150)
        font = o.get('font', FONT)
        key = ('outro', text, size, font)
        if key not in _TEXT:
            _TEXT[key] = name_masks(text, size, font, skew=o.get('skew', -0.08))
        full, per = _TEXT[key]
        acc = np.zeros_like(full)
        for j, m in enumerate(per):
            acc = np.maximum(acc, m * float(np.clip((q - 0.03 * j) / 0.10, 0, 1)))
        hh, ww = full.shape
        sc = min(1.0, o.get('width', 0.86) * W / ww) * (1.0 + 0.04 * q)
        M = cv2.getRotationMatrix2D((ww / 2, hh / 2), 0, sc)
        M[0, 2] += W / 2 - ww / 2
        M[1, 2] += o.get('y', 0.46) * H - hh / 2
        a = cv2.warpAffine(acc, M, (W, H), flags=cv2.INTER_LINEAR)
        col = hexc(o.get('color', '#ffffff'))
        sm = cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        g1 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3), (W, H))
        g2 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 12), (W, H))
        glow = (g1 * 0.55 + g2 * 0.35) * (1.0 if o.get('style', 'glow') == 'glow' else 0.0)
        f = f * (1 - a[..., None]) + col * a[..., None] + col * glow[..., None]
        return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)

    # ------------------------------------------------------------------ composition
    def content(self, t, fi):
        """uint8 frame of shots / outro with transitions (before look, punch, texts)."""
        k = max(j for j, sg in enumerate(self.segs) if sg['s'] <= t + 1e-9) if t >= 0 else 0
        sg = self.segs[k]
        if k > 0 and sg['din'] > 0 and t < sg['s'] + sg['din'] / 2:
            p = (t - sg['a']) / sg['din']
            return G.transition(self.segs[k - 1]['tout'], self.shot_frame(k - 1, t, fi), self.shot_frame(k, t, fi),
                                p, ease=self.segs[k - 1]['spec'].get('ease'))
        if sg['dout'] > 0 and t >= sg['e'] - sg['dout'] / 2:
            p = (t - (sg['e'] - sg['dout'] / 2)) / sg['dout']
            return G.transition(sg['tout'], self.shot_frame(k, t, fi), self.shot_frame(k + 1, t, fi), p,
                                ease=sg['spec'].get('ease'))
        return self.shot_frame(k, t, fi)

    def raw(self, t, fi):
        """float 0..1 frame: content + look + beat punch + texts."""
        img = self.content(t, fi)
        R = self.R
        in_outro = t >= self.segs[-1]['s']
        if R.get('look') and not (in_outro and self.segs[-1]['spec'].get('look') is False):
            k = max(j for j, sg in enumerate(self.segs) if sg['s'] <= t + 1e-9)
            img = apply_fx(img, R['look'], self.ctx(k, t, fi))
        p = R.get('punch')
        if p and not in_outro:
            e = self.env(t, p.get('decay', 0.09))
            if e > 0.01:
                z = 1.0 + p.get('zoom', 0.035) * e
                M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
                sh = p.get('shake', 0.0) * e * W
                if sh:
                    r = np.random.default_rng(fi)
                    M[:, 2] += r.normal(0, sh, 2)
                img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        f = img.astype(np.float32) / 255.0
        for tx in self.texts:
            f = draw_text(f, tx, t)
        return f

    def frame0(self):
        if self._frame0 is None:
            self._frame0 = self.raw(0.0, 0)
        return self._frame0

    def frame(self, fi):
        t = fi / FPS
        self.evict(t)
        f = self.raw(t, fi)
        if self.loop and t > self.T - self.loop[1]:
            p = (t - (self.T - self.loop[1])) / self.loop[1]
            a8 = (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)
            b8 = (np.clip(self.frame0(), 0, 1) * 255 + 0.5).astype(np.uint8)
            f = G.transition(self.loop[0], a8, b8, p, ease='inout').astype(np.float32) / 255.0
        return finish(f, fi, self.R)

    # ------------------------------------------------------------------ report
    def plan(self):
        print(f"{self.R['name']}: {self.T:.2f} s, {self.N} frames @ {FPS} fps, song {self.song_in:.3f} -> "
              f"{self.song_in + self.T:.3f}")
        print(' #  start   end    beats  src / at            trans in -> out           fx')
        for k, sg in enumerate(self.segs):
            s = sg['spec']
            nb = self.bi(sg['e']) - self.bi(sg['s'])
            if sg['kind'] == 'outro':
                src = f"END CARD '{s.get('text', 'MEHRAB.7w7')}'"
            else:
                src = f"{os.path.basename(s['src'])} @{s.get('at', 0):.2f}"
            tin = self.segs[k - 1]['tout'] if k else '-'
            print(f"{k:2d} {sg['s']:6.2f} {sg['e']:6.2f}  {nb:5.2f}  {src:20.20s} {str(tin):>13s} -> "
                  f"{str(sg['tout']):13s} {s.get('fx', '')}")
            if sg['kind'] == 'shot':
                w, h, fps, dur = probe(path_of(s['src']))
                span = sg['b'] - sg['a']
                tm = make_tmap(s, span, (sg['din'], (sg['s'] - sg['a'], sg['e'] - sg['a'])))
                hi = max(tm(0), tm(span))
                if fps and hi > dur + 0.02:
                    print(f'    !! needs source up to {hi:.2f}s but the clip is {dur:.2f}s — '
                          f'lower "at", slow it ("speed"), or shorten the shot')
                if fps and w / h > 0.60 and s.get('zoom', 1.0) < 1.0:
                    print('    !! zoom < 1 on a wide clip would show borders')
        if self.loop:
            print(f'loop: {self.loop[0]} over the last {self.loop[1]:.2f}s into frame 0')


# ============================================================================ commands
def _encoder(out, crf=12):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
                             '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)


def render_range(recipe_path, f0, f1, out):
    E = Edit(load_recipe(recipe_path))
    enc = _encoder(out)
    t0 = time.time()
    for fi in range(f0, f1):
        enc.stdin.write(E.frame(fi).tobytes())
        if (fi - f0) % 60 == 0:
            print(f'  frame {fi}/{f1} ({time.time() - t0:.0f}s)', flush=True)
    enc.stdin.close()
    enc.wait()


def song_wav(R):
    src = path_of(R['song'])
    if src.lower().endswith('.wav'):
        return src
    out = os.path.join(R['_dir'], 'song.wav')
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', '48000',
                        '-c:a', 'pcm_s16le', out], check=True)
    return out


def render(recipe_path, workers=2, do_4k=True):
    R = load_recipe(recipe_path)
    E = Edit(R)
    E.plan()
    d = R['_dir']
    parts = []
    bounds = np.linspace(0, E.N, workers + 1).astype(int)
    procs = []
    for w in range(workers):
        seg = os.path.join(d, f'part{w}.mp4')
        parts.append(seg)
        log = open(seg + '.log', 'w')
        procs.append(subprocess.Popen([sys.executable, os.path.abspath(__file__), '_range', recipe_path,
                                       str(bounds[w]), str(bounds[w + 1]), seg], stdout=log, stderr=subprocess.STDOUT))
    for p, seg in zip(procs, parts):
        if p.wait() != 0:
            sys.exit(f'render part failed, see {seg}.log')
    lst = os.path.join(d, 'parts.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    video = os.path.join(d, 'video_noaudio.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', video],
                   check=True)
    # audio: song window, tape-stop from the end card, -14 LUFS
    audio = os.path.join(d, 'audio.wav')
    cmd = [sys.executable, os.path.join(KIT, 'audio_finish.py'), song_wav(R), audio, '--start', f'{E.song_in:.4f}',
           '--end', f'{E.song_in + E.T + 3.0 / FPS:.4f}', '--lufs', str(R.get('lufs', -14.0))]
    if R.get('tapestop', True):
        cmd += ['--tapestop', f'{E.song_in + E.segs[-1]["s"]:.4f}']
    subprocess.run(cmd, check=True)
    name = R['name']
    o4 = os.path.join(d, f'{name}_4K_60fps.mp4')
    o1 = os.path.join(d, f'{name}_1080p_60fps.mp4')
    if do_4k:
        subprocess.run(['bash', os.path.join(KIT, 'finish4k.sh'), video, audio, o4, o1], check=True)
    else:
        subprocess.run(['bash', os.path.join(KIT, 'finish.sh'), video, audio, o1, '12M'], check=True)
    print('done:', o4 if do_4k else '', o1)


def stills(recipe_path, times, out=None, tile=(270, 480)):
    R = load_recipe(recipe_path)
    E = Edit(R)
    ims = []
    for t in times:
        fi = int(round(t * FPS))
        im = cv2.resize(E.frame(fi), tile, interpolation=cv2.INTER_AREA)
        cv2.putText(im, f'{t:.2f}', (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        ims.append(im)
    cols = min(len(ims), 10)
    rows = [np.concatenate(ims[i:i + cols] + [np.zeros_like(ims[0])] * (cols - len(ims[i:i + cols])), 1)
            for i in range(0, len(ims), cols)]
    out = out or os.path.join(R['_dir'], 'check', 'stills.jpg')
    cv2.imwrite(out, cv2.cvtColor(np.concatenate(rows, 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(out)
    return out


def cover(recipe_path):
    R = load_recipe(recipe_path)
    E = Edit(R)
    c = R.get('cover', {})
    fi = int(round(c.get('t', 0.0) * FPS))
    f = E.raw(fi / FPS, fi)
    for tx in c.get('texts', []):
        d = dict(tx, t0=-1, t1=1e9, pop=False)
        f = draw_text(f, d, 0.0)
    img = finish(f, fi, dict(R, grain=0.0))
    out = os.path.join(R['_dir'], f"{R['name']}_cover.jpg")
    cv2.imwrite(out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(out)


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd = argv[0]
    if cmd == '_range':
        render_range(argv[1], int(argv[2]), int(argv[3]), argv[4])
    elif cmd == 'plan':
        Edit(load_recipe(argv[1])).plan()
    elif cmd == 'stills':
        stills(argv[1], [float(x) for x in argv[2:]])
    elif cmd == 'sheet':
        R = load_recipe(argv[1])
        step = float(argv[argv.index('--step') + 1]) if '--step' in argv else 0.5
        T = Edit(R).T
        stills(argv[1], list(np.arange(0, T - 1e-6, step)), os.path.join(R['_dir'], 'check', 'sheet.jpg'),
               tile=(162, 288))
    elif cmd == 'cover':
        cover(argv[1])
    elif cmd == 'render':
        wk = int(argv[argv.index('--workers') + 1]) if '--workers' in argv else 2
        render(argv[1], wk, '--no-4k' not in argv)
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
