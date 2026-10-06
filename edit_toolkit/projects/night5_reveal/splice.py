"""Re-render frame ranges of render5 and splice them into an existing render (fast fixes):
  WORK=$WORK python3 splice.py src.mp4 dst.mp4 182-323 505-640
"""
import sys, os, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('WORK', '/home/claude/work_edit')
import numpy as np
import render5 as R
from multiprocessing import Pool
src, dst = sys.argv[1], sys.argv[2]
ranges = [tuple(int(v) for v in a.split('-')) for a in sys.argv[3:]]
idx = [f for a, b in ranges for f in range(a, b + 1)]
t = time.time()
with Pool(2) as p:
    new = dict(zip(idx, p.map(R.render, idx, chunksize=2)))
print('rendered', len(new), f'{time.time() - t:.1f}s', flush=True)
W, H = R.W, R.H
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(R.FPS), '-i', '-',
                        '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    enc.stdin.write(new[n].tobytes() if n in new else buf)
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('frames', n, f'{time.time() - t:.1f}s')
