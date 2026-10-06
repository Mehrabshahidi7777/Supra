"""Cover for Night 4: first car (M5 G90 head-on) + the finger orb mid-swipe + the trend text.
  WORK=$WORK python3 cover4.py out.jpg
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np, cv2
import render4 as R
import shots as S

T = S.CUTS[0] + 0.40
f = R.grade(R.shot_frame(0, T)) * R.VIG
G4 = np.zeros((R.H4, R.W4, 3), np.float32)
C = np.zeros((R.H, R.W, 3), np.float32)
t_end = 10.0


def pos(t):      # a slide from bottom-left to bottom-right, caught near its end
    q = R.smoother((t - (t_end - 0.5)) / 0.5)
    return R.BL * (1 - q) + R.BR * q


R.draw_orb(C, G4, t_end - 0.10, 1.05, 1.1, pos_fn=pos)
R.draw_ring(C, G4, *R.BR, 0.10, 0.42, 34, 260, 0.9)
R.glow_from_block(G4, R.TXT, 330, R.ACC, 0.45)
f = f + R.up(R.blur_glow(G4)) + C
R.put_mask(f, R.TXT, 330, R.WHITE * 0.98, 1.0, 1.0, shadow=R.TXT_SH, sh_k=0.8)
img = R.finish(f, 3)
cv2.imwrite(sys.argv[1], cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
print('cover ->', sys.argv[1])
