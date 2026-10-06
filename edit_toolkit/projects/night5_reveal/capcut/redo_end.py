import os, sys, subprocess, numpy as np
sys.path.insert(0, '/home/claude/supra/edit_toolkit/projects/night5_reveal')
import render5 as R, shots5 as S
W, H = 1080, 1920
src, dst = sys.argv[1], sys.argv[2]
j0 = int(np.ceil(S.T_OUT * 60))
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60', '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
j = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    enc.stdin.write(R.render(j).tobytes() if j >= j0 else buf)
    j += 1
enc.stdin.close(); enc.wait(); print('frames', j, 'end card from', j0)
