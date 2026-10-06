"""60 fps final of the user's CapCut version (their export was 30 fps, the end looked laggy):
  intro 0-4.33 s (their colour filter only) -> their filter (3D LUT) on our 60 fps band-free frames
  frames carrying their CapCut effects (shatter, beams, echo, prism) -> their (band-fixed) 30 fps frames
  untouched shots -> our 60 fps band-free frames; their dark effect is gone from the GT3 shots
  end card -> rendered fresh at 60 fps with the dark 'opening' reveal, slow push-in and a glint (render5.outro_frame)
  python3 final60.py cc_fixed_noaudio.mp4 n5_noaudio_v6.mp4 out60.mp4
"""
import os, sys, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('N5_DIR', '/home/claude/supra/edit_toolkit/projects/night5_reveal'))
import lut3d
import render5 as R
import shots5 as S
W, H = 1080, 1920
LUT = np.load(os.path.join(HERE, 'lut_intro.npy'))
EFFECT_30 = [(130, 152), (193, 237), (243, 271)]          # their CapCut effect frames (30 fps indices)
INTRO_END_J = 260                                        # first 60 fps frame of the shatter (their frame 130)

def is_effect(k):
    return any(a <= k <= b for a, b in EFFECT_30)

def reader(path):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

def read(p):
    buf = p.stdout.read(W * H * 3)
    return None if len(buf) < W * H * 3 else np.frombuffer(buf, np.uint8).reshape(H, W, 3)

def main(cc_fixed, noband60, out):
    pc, pn = reader(cc_fixed), reader(noband60)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60',
                            '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', out],
                           stdin=subprocess.PIPE)
    cur_c = None
    j = 0
    while True:
        n = read(pn)
        if n is None:
            break
        k = j // 2
        if j % 2 == 0:
            cur_c = read(pc)
        t = j / 60
        if j < INTRO_END_J:
            o = (np.clip(lut3d.apply(LUT, n.astype(np.float32) / 255), 0, 1) * 255 + 0.5).astype(np.uint8)
        elif is_effect(k) and cur_c is not None:
            o = cur_c
        elif t < S.T_OUT:
            o = n
        else:
            o = R.render(j)
        enc.stdin.write(np.ascontiguousarray(o).tobytes())
        j += 1
        if j % 120 == 0:
            print('frame', j, flush=True)
    enc.stdin.close(); enc.wait()
    print('frames', j)

if __name__ == '__main__':
    main(*sys.argv[1:4])
