"""Move the user's 'black that opens' CapCut effect from the GT3 shots (10.23-12.70 s) to the end card (ID reveal).

frames 0-306   : their (band-fixed) frames, unchanged
frames 307-378 : our band-free frames (= their edit without the dark effect; nothing else was changed there)
frames 379-409 : end card (band-free) x the 'black opening' mask: black -> diagonal light snaps open (their
                 diagonal: edge through (840,0)-(0,1500), lit side upper-left) -> holds -> opens fully -> loop zoom
"""
import sys, subprocess, numpy as np
W, H = 1080, 1920
T_OUT = 12.62735          # beat 16 (shots5)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
U = (1500 * xx + 840 * yy) / np.hypot(1500, 840)        # 0 at top-left -> ~1880 at bottom-right; their edge at u=733
DARK = 0.18

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def edge_pos(lt):
    if lt < 0.07:
        return -150.0
    if lt < 0.15:                                          # snap open to their diagonal
        return -150 + (733 + 150) * float(smooth(0, 1, (lt - 0.07) / 0.08))
    if lt < 0.38:                                          # hold: half lit, like their effect
        return 733.0
    if lt < 0.62:                                          # open fully
        return 733 + (2100 - 733) * float(smooth(0, 1, (lt - 0.38) / 0.24))
    return 2100.0

def mask(lt):
    e = edge_pos(lt)
    lit = 1 - smooth(e - 45, e + 45, U)
    return (DARK + (1 - DARK) * lit)[..., None]

def reader(path):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

def read(p):
    buf = p.stdout.read(W * H * 3)
    return None if len(buf) < W * H * 3 else np.frombuffer(buf, np.uint8).reshape(H, W, 3)

def main(fixed, noband60, out):
    pf, pn = reader(fixed), reader(noband60)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                            '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', out],
                           stdin=subprocess.PIPE)
    k = 0
    while True:
        f = read(pf); n = read(pn); _ = read(pn)
        if f is None or n is None:
            break
        t = k / 30
        if k < 307:
            o = f
        elif t < T_OUT:
            o = n
        else:
            o = np.clip(n.astype(np.float32) * mask(t - T_OUT), 0, 255).astype(np.uint8)
        enc.stdin.write(np.ascontiguousarray(o).tobytes())
        k += 1
    enc.stdin.close(); enc.wait()
    print('frames', k)

if __name__ == '__main__':
    main(*sys.argv[1:4])
