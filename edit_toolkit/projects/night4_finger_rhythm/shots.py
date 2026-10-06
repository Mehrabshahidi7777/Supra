# Night 4 — "slide your finger along the rhythm" trend (the user's reference: Clima Lindo (Slowed) BMW edit).
# Song = Clima Lindo (Slowed) from the reference recording, rebuilt seamless as $WORK/song4.wav
# (loop-2 audio for 0-6 s, loop-1 for the rest). Beat grid (beats.py): period 0.70608 s, beat 0 at 0.1221.
B = 0.70608
B0 = 0.1221


def beat(k):
    return B0 + k * B


S0 = 0.08                      # video starts 42 ms before beat 0 -> 25 beats per loop
INTRO_BEATS = 11               # finger slides before the drop; the 11th lands on the drop
T_DROP = beat(INTRO_BEATS)     # 7.889 drop
T_RISE = 6.48                  # riser / build-up starts
T_OUT = beat(24)               # 17.068 outro (MEHRAB.7w7) on the last beat
T_END = S0 + 530 / 30          # 17.747 = beat 25 - 42 ms  (530 frames)

# ---- the finger path = the reference's white dot: one slide per beat along the bottom and the right edge
# dot starts top-right; move k (k >= 1) = MOVES[(k-1) % 4]; it lands exactly on beat k
TR, BR, BL = (860, 500), (860, 1270), (180, 1270)   # bottom row kept above the MEHRAB.7w7 line + app overlays
MOVES = ['down', 'left', 'right', 'up']
TRAVEL_INTRO = 0.50            # slide time before the drop (like the reference)
TRAVEL_MONT = 0.32             # quicker swipes in the montage; each one paints the next car in

# one cut per beat from the drop to the outro (shot i lands on beat 11 + i)
CUTS = [beat(k) for k in range(INTRO_BEATS, 25)]          # 14 times -> 13 shots + T_OUT

PBOX = (20, 96, 1060, 1936)    # Pinterest pin video area in the 1080x2340 recordings
# (name, car, clip, src_in, zoom, cx, cy, box)
#   src_in = source time where the shot starts being painted in (PRE seconds before its cut)
#   zoom >= 1.09 keeps the Pinterest back button out of frame (kit/framing.py)
SHOTS = [
    ('S01', 1, 'p6', 12.84, 1.18, 495, 990, PBOX),    # M5 G90 head-on, glowing kidneys, night gas station
    ('S02', 1, 'p6', 2.50, 1.09, None, None, PBOX),   # M5 G90 close 3/4 front, grille glow
    ('S03', 1, 'p6', 6.38, 1.09, None, None, PBOX),   # M5 G90 red taillight close
    ('S04', 2, 'p4', 32.70, 1.09, None, None, PBOX),  # M5 (F90 LCI) blue laser headlight, night garage
    ('S05', 2, 'p4', 34.32, 1.15, None, 1000, PBOX),  # same car rear, taillights in the yellow box
    ('S06', 3, 'p5', 25.30, 1.09, None, None, PBOX),  # M5 F90 blue angel eyes close
    ('S07', 4, 'p2', 58.55, 1.20, 520, 1030, PBOX),   # blue M3 Competition head-on, lights on (showroom)
    ('S08', 5, 'p3', 7.85, 1.09, None, None, PBOX),   # X5 rear 3/4 taillights, snow
    ('S09', 6, 'p4', 10.20, 1.15, 400, 1000, PBOX),   # M5 CS front 3/4, yellow DRLs
    ('S10', 3, 'p5', 2.70, 1.09, None, None, PBOX),   # M5 F90 front 3/4 low, cobblestones
    ('S11', 7, 'p7', 0.80, 1.25, None, 878, PBOX),    # M3 Touring floating in a showroom (AI clip)
    ('S12', 8, 'p1', 8.60, 1.09, None, None, PBOX),   # white X4 M40i front 3/4
    ('S13', 3, 'p5', 34.85, 1.10, None, None, PBOX),  # M5 drift, tyre smoke
]
PRE = {'S01': 0.30}            # default: TRAVEL_MONT
SPEED = {'S01': 0.62, 'S03': 0.95, 'S05': 0.82}
CARS = {1: 'BMW M5 G90', 2: 'BMW M5', 3: 'BMW M5 F90', 4: 'BMW M3 Competition', 5: 'BMW X5',
        6: 'BMW M5 CS', 7: 'BMW M3 Touring', 8: 'BMW X4 M40i'}
ACCENT = '#36e7ff'
# clean frames (house rule): text on the footage to remove. S07: 'davidjames limited' dealer plate on the blue M3
# -> per frame: dark plate found inside this search box (pin-box coords), its white letters inpainted
CLEAN = {'S07': (330, 1250, 700, 1410)}
WM_CY = 1452                   # centre of the MEHRAB.7w7 line: ~3/4 height, above YouTube/Instagram/Facebook overlays
