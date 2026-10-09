"""VFX pack showcase: every gl-transition port + the vfx.py camera/time effects, numbered, on shots taken from
the channel's own finished edits in this repo. Run from the repo root:

    python3 edit_toolkit/projects/vfx_showcase/showcase.py out.mp4             # full reel, 1080x1920 @ 60 fps
    python3 edit_toolkit/projects/vfx_showcase/showcase.py out.mp4 --part 6    # just transition #6 (or --part fx)

The full reel renders in parts, two processes at a time (the box has 2 cores and ~5.5 GB before the OOM killer:
never load every shot at once), and resumes finished parts if it is run again; parts are joined with concat.

Shot windows were picked from dense strips so no window crosses a cut of the source edit; shots shorter than
the time they are on screen are slowed down with optical flow (vfx.Clip.at), which is itself part of the demo.
"""
import os
import subprocess
import sys
import time

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit')
sys.path.insert(0, KIT)
import gltrans as G  # noqa: E402
import vfx  # noqa: E402

W, H, FPS = 1080, 1920, 60
FONT = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
VID = {
    'N5': 'Night5_MEHRAB7w7_Reveal/Night5_MEHRAB7w7_Reveal_1080p_60fps.mp4',
    'N4': 'Night4_SlideYourFinger_BMW/Night4_SlideYourFinger_BMW_1080p_60fps.mp4',
    'SP': 'BMW_M_Space_Edit/BMW_M_Lost_in_Space_1080p.mp4',
    'N6': 'Night6_BMW_Multiverse/Night6_BMW_Multiverse_1080p_60fps.mp4',
    'CL': 'CLS63_AMG_Edit/CLS63_AMG_Edit_1080p_60fps.mp4',
}
# (video, start, end) — clean windows inside one source shot
SHOTS = [
    ('N5', 0.05, 0.95),    # blue GT3 RS, skyline
    ('CL', 14.60, 15.04),  # CLS taillights, garage
    ('N5', 5.45, 5.85),    # orange P1 close
    ('SP', 7.30, 9.80),    # black M3
    ('N5', 2.05, 2.95),    # blue headlight
    ('N6', 0.00, 1.35),    # taillights in snow
    ('N5', 4.45, 4.80),    # P1 doors up
    ('SP', 10.00, 10.62),  # yellow DRL M5
    ('N5', 10.70, 11.05),  # white 911
    ('CL', 10.10, 10.45),  # CLS tunnel
    ('N4', 12.00, 12.55),  # blue M3
    ('N5', 12.12, 12.55),  # red wheel
    ('SP', 10.75, 11.70),  # grille light
    ('N5', 3.20, 3.70),    # GT3 studio
    ('CL', 15.12, 15.55),  # snowy CLS
    ('N5', 9.12, 9.45),    # white 911 rear
    ('SP', 11.90, 13.90),  # M5 headlights
    ('N5', 11.20, 11.55),  # headlight close
]
ORDER = ['cube', 'crosswarp', 'doorway', 'swirl', 'swap', 'directional_warp', 'revolve', 'ripple', 'book_flip',
         'morph', 'tangent_blur', 'squeeze', 'grid_flip', 'flyeye', 'push_scaled', 'window_slice', 'kaleidoscope']
HOLD = 0.40
assert len(ORDER) == len(SHOTS) - 1 and set(ORDER) == set(G.NAMES)


def label(img, text, sub=None):
    """Small numbered label near the top (white, soft dark rim — no band)."""
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 58)
    tw = d.textlength(text, font=f)
    x, y = (W - tw) / 2, 150
    for r in (6, 4, 2):
        d.text((x, y), text, font=f, fill=(0, 0, 0), stroke_width=r, stroke_fill=(0, 0, 0))
    d.text((x, y), text, font=f, fill=(255, 255, 255))
    if sub:
        f2 = ImageFont.truetype(FONT, 34)
        sw = d.textlength(sub, font=f2)
        d.text(((W - sw) / 2, y + 74), sub, font=f2, fill=(255, 220, 120), stroke_width=4, stroke_fill=(0, 0, 0))
    return np.asarray(im)


class Shot:
    """One source window, loaded only when needed (2 shots in memory at a time: 1080p frames are 6 MB each)."""

    def __init__(self, key, t0, t1, need):
        avail = t1 - t0
        self.speed = min(1.0, (avail - 1.0 / 60) / need)
        if self.speed >= 1.0:
            t1 = min(t1, t0 + need + 0.1)
        self.clip = vfx.Clip(VID[key], t0, t1, (W, H), flow_scale=0.5)
        self.speed = min(1.0, (self.clip.dur - 1.0 / self.clip.fps) / need)

    def frame(self, t):
        return self.clip.at(t * self.speed)


def _durs():
    return [G.TRANSITIONS[n][1] for n in ORDER]


def make_shot(i):
    durs = _durs()
    need = (durs[i - 1] if i > 0 else 0) + HOLD + (durs[i] if i < len(ORDER) else 0)
    sh = Shot(*SHOTS[i], need)
    print(f'shot {i:2d} {SHOTS[i]} speed {sh.speed:.2f}', flush=True)
    return sh


def transition_part(write, i):
    """Hold of shot i + transition #i+1 into shot i+1 (+ the final hold after the last transition)."""
    durs = _durs()
    name = ORDER[i]
    a, b = make_shot(i), make_shot(i + 1)
    a_off = durs[i - 1] if i > 0 else 0.0
    txt = f'{i + 1:02d}  {name.upper().replace("_", " ")}'
    for k in range(int(round(HOLD * FPS))):
        write(label(a.frame(a_off + k / FPS), txt))
    n = int(round(durs[i] * FPS))
    for k in range(n):
        p = (k + 0.5) / n
        write(label(G.transition(name, a.frame(a_off + HOLD + k / FPS), b.frame(k / FPS), p), txt))
    if i == len(ORDER) - 1:
        for k in range(int(round(HOLD * FPS))):
            write(label(b.frame(durs[i] + k / FPS), txt))
    print(f'  done {txt}', flush=True)


def effects_part(write):
    sec = lambda s: int(round(s * FPS))

    # 18 speed ramp: real -> slow-mo (flow) -> fast with shutter blur -> real
    c = vfx.Clip(VID['CL'], 10.56, 10.98, (W, H))
    keys = [(0, 1.0), (0.25, 0.12), (0.95, 0.12), (1.15, 1.8), (1.4, 1.0)]
    n = sec(1.4)
    t, _ = vfx.ramp_times(n + 1, FPS, keys)
    k = (c.dur - 1 / c.fps) / t[-1]
    keys = [(a, s * k) for a, s in keys]
    for i, fr in enumerate(vfx.ramp_frames(c, n, FPS, keys, blur_from=1.2 * k)):
        write(label(fr, '18  SPEED RAMP', 'slow-mo + motion blur'))
    print('  done speed ramp', flush=True)

    # 19 smooth slow motion (optical flow) — 0.35 s of source stretched to 1.4 s
    c = vfx.Clip(VID['N5'], 4.45, 4.80, (W, H))
    n = sec(1.4)
    for i in range(n):
        write(label(c.at(i / n * (c.dur - 1 / c.fps)), '19  SMOOTH SLOW-MO', 'optical flow, 4x slower'))
    print('  done slow-mo', flush=True)

    # 20 3D tilt camera
    c = vfx.Clip(VID['SP'], 7.30, 8.70, (W, H))
    n = sec(1.4)
    for i in range(n):
        q = i / (n - 1)
        e = q * q * (3 - 2 * q)
        fr = vfx.tilt3d(c.at(q * (c.dur - 1 / c.fps)), yaw=-14 + 26 * e, pitch=6 - 9 * e, roll=-2 + 3 * e)
        write(label(fr, '20  3D TILT', 'camera swing'))
    print('  done tilt', flush=True)

    # 21 impact shake on beats (every 0.35 s, decaying)
    c = vfx.Clip(VID['SP'], 11.90, 13.30, (W, H))
    n = sec(1.4)
    for i in range(n):
        tt = i / FPS
        env = np.exp(-((tt % 0.35) / 0.09))
        fr = vfx.shake(c.at(tt), tt, amp=0.03, rot=2.5, freq=11, strength=env)
        write(label(fr, '21  SHAKE', 'hits on the beat'))
    print('  done shake', flush=True)

    # 22 lens punch (barrel pulse on beats)
    c = vfx.Clip(VID['N5'], 0.05, 0.95, (W, H))
    n = sec(1.4)
    for i in range(n):
        tt = i / FPS
        env = np.exp(-((tt % 0.35) / 0.10))
        fr = vfx.lens_warp(c.at(tt * 0.6), 0.45 * env)
        write(label(fr, '22  LENS PUNCH'))
    print('  done lens', flush=True)

    # 23 light trails (echo, lighten) on a swinging taillight shot
    c = vfx.Clip(VID['N6'], 0.0, 1.35, (W, H))
    n = sec(1.4)
    hist = []
    for i in range(n):
        q = i / (n - 1)
        fr = vfx.tilt3d(c.at(q * (c.dur - 1 / c.fps)), yaw=10 * np.sin(q * 2 * np.pi), roll=4 * np.sin(q * 4 * np.pi))
        hist = (hist + [fr])[-10:]
        write(label(vfx.echo(hist, 0.78), '23  LIGHT TRAILS'))
    print('  done trails', flush=True)

    # 24 light leak (warm, then teal)
    c = vfx.Clip(VID['N5'], 2.05, 2.95, (W, H))
    n = sec(1.6)
    for i in range(n):
        q = i / (n - 1)
        fr = c.at(q * (c.dur - 1 / c.fps))
        pal = vfx.LEAK_WARM if q < 0.5 else vfx.LEAK_TEAL
        s = np.sin(min(q, 0.5) * 2 * np.pi) if q < 0.5 else np.sin((q - 0.5) * 2 * np.pi)
        write(label(vfx.light_leak(fr, q * 1.6, pal, strength=0.8 * s + 0.05), '24  LIGHT LEAK', 'warm / teal'))
    print('  done leak', flush=True)


def encoder(out):
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
                            '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    return enc, (lambda fr: enc.stdin.write(np.ascontiguousarray(fr, np.uint8).tobytes()))


def render_part(part, out):
    enc, write = encoder(out)
    if part == 'fx':
        effects_part(write)
    else:
        transition_part(write, int(part) - 1)
    enc.stdin.close()
    enc.wait()


def main():
    """showcase.py out.mp4                -> all parts, 2 at a time, then joined
       showcase.py out.mp4 --part 7       -> only transition #7 (or --part fx for the effects)"""
    out = sys.argv[1]
    if '--part' in sys.argv:
        render_part(sys.argv[sys.argv.index('--part') + 1], out)
        return
    tmp = os.path.splitext(out)[0] + '_parts'
    os.makedirs(tmp, exist_ok=True)
    parts = ['fx'] + [str(i + 1) for i in range(len(ORDER))]
    me = os.path.abspath(__file__)
    running = {}

    def reap(block):
        while True:
            for seg, pr in list(running.items()):
                rc = pr.poll()
                if rc is None:
                    continue
                del running[seg]
                if rc != 0:
                    sys.exit(f'part failed: {seg} (see {seg}.log)')
                open(seg + '.ok', 'w').close()
            if not block or not running:
                return
            time.sleep(1)

    for part in parts:
        seg = os.path.join(tmp, f'part_{part}.mp4')
        if os.path.exists(seg + '.ok'):
            continue  # resume
        while len(running) >= 2:
            reap(False)
            time.sleep(1)
        log = open(seg + '.log', 'w')
        running[seg] = subprocess.Popen([sys.executable, me, seg, '--part', part], stdout=log, stderr=subprocess.STDOUT)
    reap(True)
    order = [str(i + 1) for i in range(len(ORDER))] + ['fx']
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for part in order:
            f.write(f"file '{os.path.abspath(os.path.join(tmp, f'part_{part}.mp4'))}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
