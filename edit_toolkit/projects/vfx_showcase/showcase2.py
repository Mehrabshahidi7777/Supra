"""VFX pack showcase, reel 2: transitions #25-48 (more gl-transitions) and looks #49-59 (pixi-filters + glfx.js),
numbered, on shots from the channel's own edits. Run from the repo root:

    python3 edit_toolkit/projects/vfx_showcase/showcase2.py out.mp4            # full reel (parallel parts, resumable)
    python3 edit_toolkit/projects/vfx_showcase/showcase2.py out.mp4 --part 29  # one transition, or --part fx
"""
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import showcase as S  # noqa: E402  (label, Shot, VID, sizes, encoder)

G, vfx = S.G, S.vfx
W, H, FPS, HOLD = S.W, S.H, S.FPS, S.HOLD
FIRST = 25  # number of the first transition in this reel

SHOTS = [
    ('N5', 4.45, 4.80),    # P1 doors up
    ('SP', 10.00, 10.62),  # yellow DRL M5
    ('N5', 0.05, 0.95),    # blue GT3 RS skyline
    ('CL', 10.56, 10.97),  # CLS rear, moving
    ('N5', 9.60, 9.95),    # headlight reflections
    ('SP', 7.30, 9.80),    # black M3
    ('N5', 4.95, 5.30),    # P1 rear, dark
    ('N4', 15.60, 15.95),  # white X3
    ('N6', 0.00, 1.35),    # taillights in snow
    ('N5', 12.12, 12.55),  # red wheel
    ('CL', 13.10, 13.50),  # snowy CLS
    ('N5', 2.05, 2.95),    # blue headlight
    ('SP', 10.75, 11.70),  # grille light
    ('N4', 16.30, 16.75),  # grey M5 drift
    ('N5', 10.70, 11.05),  # white 911
    ('CL', 14.60, 15.04),  # taillights, garage
    ('N5', 5.45, 5.85),    # orange P1 close
    ('SP', 11.90, 13.90),  # M5 headlights
    ('N5', 3.20, 3.70),    # GT3 studio
    ('CL', 10.10, 10.45),  # CLS tunnel
    ('N4', 12.00, 12.55),  # blue M3
    ('N5', 9.12, 9.45),    # white 911 rear
    ('CL', 15.12, 15.55),  # snowy CLS lights
    ('N5', 11.20, 11.55),  # headlight close
    ('SP', 8.00, 9.80),    # black M3
]
ORDER = [G.NUMBERS[n] for n in range(FIRST, FIRST + 24)]
assert len(ORDER) == len(SHOTS) - 1 and all(n in G.TRANSITIONS for n in ORDER)


def _durs():
    return [G.TRANSITIONS[n][1] for n in ORDER]


def make_shot(i):
    durs = _durs()
    need = (durs[i - 1] if i > 0 else 0) + HOLD + (durs[i] if i < len(ORDER) else 0)
    sh = S.Shot(*SHOTS[i], need)
    print(f'shot {i:2d} {SHOTS[i]} speed {sh.speed:.2f}', flush=True)
    return sh


def transition_part(write, i):
    durs = _durs()
    name = ORDER[i]
    a, b = make_shot(i), make_shot(i + 1)
    a_off = durs[i - 1] if i > 0 else 0.0
    txt = f'{FIRST + i:02d}  {name.upper().replace("_", " ")}'
    for k in range(int(round(HOLD * FPS))):
        write(S.label(a.frame(a_off + k / FPS), txt))
    n = int(round(durs[i] * FPS))
    for k in range(n):
        p = (k + 0.5) / n
        write(S.label(G.transition(name, a.frame(a_off + HOLD + k / FPS), b.frame(k / FPS), p), txt))
    if i == len(ORDER) - 1:
        for k in range(int(round(HOLD * FPS))):
            write(S.label(b.frame(durs[i] + k / FPS), txt))
    print(f'  done {txt}', flush=True)


def _clip(key, t0, t1):
    return vfx.Clip(S.VID[key], t0, t1, (W, H))


def _play(c, n, i):
    """Local time for output frame i of n, stretched over the whole clip window."""
    return i / max(n - 1, 1) * (c.dur - 1.0 / c.fps)


def effects_part(write):
    sec = lambda s: int(round(s * FPS))
    bump = lambda q: np.sin(np.pi * q)           # 0 -> 1 -> 0 over the demo
    ease_in = lambda q: min(1.0, q / 0.25)        # look fades in over the first quarter

    def demo(num, name, sub, key, t0, t1, fn, dur=1.4):
        c = _clip(key, t0, t1)
        n = sec(dur)
        for i in range(n):
            q = i / (n - 1)
            fr = c.at(_play(c, n, i))
            write(S.label(fn(fr, q, i), f'{num}  {name}', sub))
        print(f'  done {num} {name}', flush=True)

    def blend(fr, fx, k):
        return np.clip(fr.astype(np.float32) + (fx.astype(np.float32) - fr) * k + 0.5, 0, 255).astype(np.uint8)

    demo(49, 'REFLECTION', 'wet floor / water', 'N5', 4.45, 4.80,
         lambda fr, q, i: blend(fr, vfx.reflection(fr, boundary=0.70, t=q * 8.0), ease_in(q)))
    demo(50, 'TILT SHIFT', 'miniature look', 'N5', 0.05, 0.95,
         lambda fr, q, i: blend(fr, vfx.tilt_shift(fr, blur=80, gradient=420, y=0.62), ease_in(q)))
    demo(51, 'CRT', 'old TV screen', 'N4', 12.00, 12.55,
         lambda fr, q, i: blend(fr, vfx.crt(fr, t=q * 30, line_width=3.0, line_contrast=0.45), ease_in(q)))
    demo(52, 'OLD FILM', 'sepia + scratches', 'N5', 10.70, 11.05,
         lambda fr, q, i: blend(fr, vfx.old_film(fr, seed=float(np.random.default_rng(i // 3).random()),
                                                 sepia=0.6, scratch_density=0.6), ease_in(q)))
    demo(53, 'ASCII', 'made of letters', 'N5', 5.45, 5.85,
         lambda fr, q, i: blend(fr, vfx.ascii_art(fr, size=12), ease_in(q)))
    demo(54, 'CROSS HATCH', 'pen drawing', 'N5', 9.12, 9.45,
         lambda fr, q, i: blend(fr, vfx.cross_hatch(fr, spacing=12, width=2), ease_in(q)))
    demo(55, 'EMBOSS', 'metal relief', 'N5', 12.12, 12.55,
         lambda fr, q, i: blend(fr, vfx.emboss(fr, 4.0), ease_in(q)))
    demo(56, 'TWIST', 'spin in and out', 'N5', 3.20, 3.70,
         lambda fr, q, i: vfx.twist(fr, radius=0.5, angle=6.0 * bump(q), center=(0.5, 0.55)))
    demo(57, 'LENS BLUR', 'focus pull, bokeh', 'N6', 0.00, 1.35,
         lambda fr, q, i: vfx.lens_blur(fr, radius=22 * bump(q), brightness=0.8))
    demo(58, 'INK', 'comic outlines', 'CL', 13.10, 13.50,
         lambda fr, q, i: blend(fr, vfx.ink(fr, 0.3), ease_in(q)))
    demo(59, 'NEON EDGES', 'edge drawing', 'SP', 7.30, 8.70,
         lambda fr, q, i: blend(fr, vfx.edge_work(fr, radius=8, tint=(0, 230, 255)), ease_in(q)), dur=1.6)


def render_part(part, out):
    enc, write = S.encoder(out)
    if part == 'fx':
        effects_part(write)
    else:
        transition_part(write, int(part) - FIRST)
    enc.stdin.close()
    enc.wait()


def main():
    out = sys.argv[1]
    if '--part' in sys.argv:
        render_part(sys.argv[sys.argv.index('--part') + 1], out)
        return
    tmp = os.path.splitext(out)[0] + '_parts'
    os.makedirs(tmp, exist_ok=True)
    nums = [str(FIRST + i) for i in range(len(ORDER))]
    # heavy parts first so the two workers finish together
    heavy = {'29', '25', '26', '34', '42', '43'}
    parts = ['fx'] + sorted(nums, key=lambda x: x not in heavy)
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
            continue
        while len(running) >= 2:
            reap(False)
            time.sleep(1)
        log = open(seg + '.log', 'w')
        running[seg] = subprocess.Popen([sys.executable, me, seg, '--part', part], stdout=log, stderr=subprocess.STDOUT)
    reap(True)
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for part in nums + ['fx']:
            f.write(f"file '{os.path.abspath(os.path.join(tmp, f'part_{part}.mp4'))}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
