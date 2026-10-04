# shot list on the reference song (orig song time T). grid: beat k at 5.568 + k*0.3682
B = 0.3682
def beat(k): return 5.568 + k * B
S0 = 1.12
CUTS = [S0, beat(-10), beat(-6), beat(-2), beat(0)] + [beat(k) for k in range(2, 36, 2)] + [beat(34) + 3 * B]
# (name, car, clip, src_in, zoom, cx, cy, box)  box: content box in recording (x0,y0,x1,y1)
BOX = (23, 95, 1058, 1935)
BOX45 = (23, 94, 1058, 1388)
SHOTS = [
 ('G1', 1, 'p02', 39.10, 1.09, None, None, BOX),
 ('G2', 1, 'p02', 14.73, 1.15, None, None, BOX),
 ('G3', 1, 'p01', 22.80, 1.45, 518, 1200, BOX),
 ('G4', 1, 'p02', 36.33, 1.09, None, None, BOX),
 ('G5', 1, 'p02', 37.40, 1.09, None, None, BOX),
 ('P1', 2, 'x1', 7.80, 1.20, 518, 1060, BOX),
 ('P2', 2, 'x1', 2.30, 1.09, None, None, BOX),
 ('P3', 2, 'x1', 9.60, 1.25, 518, 1080, BOX),
 ('P4', 2, 'x2', 7.10, 1.00, 500, None, BOX45),
 ('B1', 3, 'x3', 4.40, 1.20, 518, 1000, BOX),
 ('B2', 3, 'p03', 2.30, 1.60, 470, 880, BOX),
 ('B3', 3, 'p03', 4.58, 1.09, None, None, BOX),
 ('B4', 3, 'p03', 9.03, 1.10, 480, None, BOX),
 ('O1', 4, 'p06', 12.95, 1.15, 518, 1150, BOX),
 ('O2', 4, 'p08', 2.65, 1.09, None, None, BOX),
 ('O3', 4, 'p08', 13.50, 1.20, 518, 1150, BOX),
 ('O4', 4, 'p06', 10.70, 1.15, 518, 1100, BOX),
 ('R1', 5, 'p09', 32.04, 1.40, 518, 800, BOX),
 ('R2', 5, 'p09', 19.20, 1.09, None, None, BOX),
 ('R3', 5, 'p09', 35.92, 1.09, None, None, BOX),
 ('R4', 5, 'p09', 40.45, 1.09, None, None, BOX),
]
assert len(CUTS) == len(SHOTS) + 2, (len(CUTS), len(SHOTS))
T_OUT = CUTS[-2]; T_END = CUTS[-1]
CARS = {1: ('AMG GT', '#39ff6a'), 2: ('FERRARI', '#ff5fc8'), 3: ('BMW M4 CSL', '#ffd21a'), 4: ('McLAREN', '#ff8a1a'), 5: ('LAMBORGHINI', '#ff2020')}

SPEED = {'B4': 0.91}
