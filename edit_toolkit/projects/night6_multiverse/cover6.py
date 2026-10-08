"""Cover for Night 6: the blue M4 in the white Earth-67 world (red outline) + a big "BMW Multiverse?" caption, 1080x1920.
  WORK=$WORK python3 cover6.py out.jpg [T]
"""
import sys, cv2, numpy as np
import render6 as R

T = float(sys.argv[2]) if len(sys.argv) > 2 else 6.45
f = R.white_frame(T, 0)
rgb, a = R.tag('mv')
f = R.put(f, rgb, a, 540, 360, scale=1.55, anchor='c')
rgb, a = R.tag('E:67')
f = R.put(f, rgb, a, 540, 515, scale=1.15, anchor="c")
img = R.finish(f, 0)
cv2.imwrite(sys.argv[1], cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 93])
print('cover', sys.argv[1], 'T =', T)
