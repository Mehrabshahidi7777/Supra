"""Cover for Night 5: the P1 right after the drop (orange P1 in the studio, fire embers), 1080x1920 JPG.
  WORK=$WORK python3 cover5.py out.jpg [T]
"""
import sys, cv2
import render5 as R

T = float(sys.argv[2]) if len(sys.argv) > 2 else 4.70
img = R.render(int(round(T * R.FPS)))
cv2.imwrite(sys.argv[1], cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 93])
print('cover', sys.argv[1], 'T =', T)
