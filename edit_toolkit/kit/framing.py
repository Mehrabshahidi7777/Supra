import cv2, numpy as np
def crop_window(src_shape, z, cx, cy):
    h, w = src_shape[:2]
    # base: largest 9:16 window inside src
    if w / h > 9 / 16:
        bh = h; bw = h * 9 / 16
    else:
        bw = w; bh = w * 16 / 9
    ww, wh = bw / z, bh / z
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    cx = min(max(cx, ww / 2), w - ww / 2)
    cy = min(max(cy, wh / 2), h - wh / 2)
    # keep Pinterest back button (content x<132, y<142) out of the window
    if cx - ww / 2 < 132 and cy - wh / 2 < 142:
        cy = min(142 + wh / 2, h - wh / 2)
    return cx, cy, ww, wh
