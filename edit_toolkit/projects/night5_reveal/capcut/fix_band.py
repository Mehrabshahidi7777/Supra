"""Usage: python3 fix_band.py their_capcut.mp4 our_file_they_edited.mp4 our_render_without_band_60fps.mp4 out.mp4

Remove the baked-in top band from the user's CapCut export while keeping all of their CapCut edits.

T = their frame everywhere except the band region (y < ~404 px), where the band is undone:
  intro (their colour filter):   T = Fc + L(Fn) - L(Fb)   L = 33^3 3D LUT of their filter (lut_intro.npy, Fb -> Fc)
  dark ending (spatial shading): T = Fc + g * (Fn - Fb)   g = local gain field smooth(Fc)/smooth(Fb) in the band area
  everything else (effects / untouched): T = Fc + (Fn - Fb)
Fb = the file they edited (v5 1080p, even frames), Fn = the same render without the band (even frames), Fc = theirs.
In the dark ending the MEHRAB.7w7 line is re-stamped white (their filter had dimmed it).
"""
import os, sys, subprocess, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fitlib import fit, apply
import lut3d
LUT_INTRO = np.load(os.path.join(HERE, 'lut_intro.npy'))
W, H = 1080, 1920
BY = 0.205 * H
yy = np.arange(H, dtype=np.float32)
BANDM = (1 - np.clip((yy - (BY - 14)) / 24.0, 0, 1))          # 1 above the band edge, 0 below 404
BANDM = BANDM * BANDM * (3 - 2 * BANDM)
YB = int(BY + 12)                                               # rows to process
DARK = (10.20, 12.63)
INTRO = (0.0, 4.30)

def reader(path):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                            stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)

def read(p):
    buf = p.stdout.read(W * H * 3)
    return None if len(buf) < W * H * 3 else np.frombuffer(buf, np.uint8).reshape(H, W, 3)

# watermark (same as render5)
import importlib, os
os.environ.setdefault('WORK', '/home/claude/work_edit')
from PIL import Image, ImageDraw, ImageFont
FONT_REG = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
_wm = Image.new('L', (W, 110), 0); _d = ImageDraw.Draw(_wm)
_f = ImageFont.truetype(FONT_REG, 44); _tx = 'MEHRAB.7w7'
_tw = sum(_f.getlength(c) for c in _tx) + 3 * (len(_tx) - 1); _xx = (W - _tw) / 2
for c in _tx:
    _d.text((_xx, 30), c, font=_f, fill=255); _xx += _f.getlength(c) + 3
WM = np.asarray(_wm, np.float32) / 255
WM_SH = cv2.GaussianBlur(WM, (0, 0), 4)
_wr = np.where(WM.max(1) > 0.5)[0]
WM_Y = int(1452 - (_wr.min() + _wr.max()) / 2)

def main(cc, fb, fn, out):
    pc, pb, pn = reader(cc), reader(fb), reader(fn)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                            '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', out],
                           stdin=subprocess.PIPE)
    k = 0
    while True:
        Fc = read(pc)
        Fb = read(pb); _ = read(pb)          # 60 fps -> even frames
        Fn = read(pn); _ = read(pn)
        if Fc is None or Fb is None or Fn is None:
            break
        t = k / 30
        c = Fc.astype(np.float32) / 255
        b = Fb[:YB].astype(np.float32) / 255
        n = Fn[:YB].astype(np.float32) / 255
        top = c[:YB]
        if INTRO[0] <= t < INTRO[1]:
            delta = lut3d.apply(LUT_INTRO, n) - lut3d.apply(LUT_INTRO, b)   # their intro filter as a 3D LUT
        elif DARK[0] <= t < DARK[1]:
            g = cv2.GaussianBlur(top, (0, 0), 25) / np.maximum(cv2.GaussianBlur(b, (0, 0), 25), 0.02)
            g = np.clip(g, 0.1, 1.6)
            delta = g * (n - b)
        else:
            delta = n - b
        top = np.clip(top + delta, 0, 1)                         # delta = m*(content - band): already blended
        c[:YB] = top
        if DARK[0] <= t < DARK[1]:                                  # keep the bottom ID white
            reg = c[WM_Y:WM_Y + 110]
            reg[:] = reg * (1 - WM_SH[..., None] * 0.55)
            reg[:] = reg * (1 - WM[..., None] * 0.95) + WM[..., None] * 0.95
        enc.stdin.write((c * 255 + 0.5).astype(np.uint8).tobytes())
        k += 1
        if k % 60 == 0:
            print('frame', k, flush=True)
    enc.stdin.close(); enc.wait()
    print('frames', k)

if __name__ == '__main__':
    main(*sys.argv[1:5])
