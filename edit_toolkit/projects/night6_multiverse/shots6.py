# Night 6 — "BMW Multiverse" on the Spider-Verse template (reference: YouTube Short @miot7 / miot.vfx,
# "50% Spiderman Polyster bm…": Spider-Man rides a BMW, "???…" -> "BMW Multiverse?", a red portal shows small cars in
# Earth-XX tags, a torn-paper hole opens into a white world (black M4 + red outline), ink smear, CCTV night scene with a
# teal ghost car, teal sky world with a white M4 GT3, glowing "miot.vfx" outro, black -> stencil reveal loop).
# No Spider-Man shot was found -> the home universe is a black M4 in the snow at night (the channel's best vibe).
#
# Song = the template's own audio from the reference recording (the recording's audio stream starts 0.0778 s into the
# container): $WORK/song6.wav = container [0.9338 : 15.1748] = one loop (14.241 s). Video time T = song6 time.
# Beat grid (beats.py on song6): onset grid 0.1233 + 0.5614 k; the low kicks attack ~0.02 s later -> cuts on beat(k).
B = 0.5614
K0 = 0.1383


def beat(k):
    return K0 + k * B


T_END = 14.241                 # loop length (the template's whole audio, silence gap included)
FPS_OUT = 60
PBOX = (20, 96, 1060, 1936)    # Pinterest pin video area in the 1080x2340 recordings

# sections (T)
T_I2, T_I3, T_I4, T_I5 = 1.488, 2.000, 2.384, 3.003      # intro cuts on the vocal / snare onsets (measured)
T_PORTAL = beat(6)             # 3.507 zoom-through the red headlight into the portal
T_P2, T_P3, T_P4 = beat(7), beat(8), beat(8.5)
T_HOLE = beat(9)               # 5.19 Earth-??? torn hole opens
T_WHITE = beat(10)             # 5.752 Earth-67 white world (blue M4)
T_INK0, T_INK1, T_W2 = 6.62, 7.16, beat(12)  # ink smear wipes W1 -> W2 (reference 6.61-7.14), cut on beat 12
T_CCTV = beat(14)              # 7.998 CCTV night
T_GHOST = 9.62                 # teal ghost car materialises
T_TEAL = beat(18)              # 10.244 Earth-928 teal world
T_T2, T_T3, T_T4 = beat(19), beat(20), beat(21)
T_FL1, T_FL2 = beat(21), beat(21.5)                       # text flashes on the car (reference: MIOT / VFX)
T_OUT0 = beat(22)              # 12.489 last kick -> glitch into the outro
T_NAME = 12.62                 # glowing MEHRAB.7w7 (reference miot.vfx 12.63-13.75)
T_NAME_END = 13.80
T_REVEAL = 13.84               # black -> brightness-ordered reveal of frame 0 (seamless loop)

# footage shots (name, clip, src_in, t0, t1, zoom, cx, cy, speed)   zoom >= 1.10 keeps the Pinterest back button out
# src_in = REAL timestamps (ffmpeg); pick them on kit/strip_ff.py strips — OpenCV seek times drift on these VFR recordings
SHOTS = {
    'I1': ('n16', 8.25, 0.0, T_I2, 1.10, None, None, 1.0),        # black M4, rear, red taillights, snow
    'I2': ('n16', 4.40, T_I2, T_I3, 1.12, None, None, 1.0),       # front, red angel eyes, snowy street
    'I3': ('n16', 5.60, T_I3, T_I4, 1.12, None, None, 1.0),       # front centred
    'I4': ('n16', 6.20, T_I4, T_I5, 1.10, None, None, 1.0),       # angel eye close-up
    'I5': ('n16', 0.60, T_I5, T_PORTAL + 0.02, 1.10, None, None, 1.0),   # front corner drift -> zoom into the headlight
    'W1': ('n20', 1.60, T_HOLE, T_INK1, 1.10, None, None, 1.0),        # blue M4 front low (runs inside the hole first)
    'W2': ('n20', 7.45, T_W2 - 0.25, T_CCTV + 0.02, 1.10, None, None, 1.0),  # camera roll around the M4
    'C1': ('n17', 10.40, T_CCTV, T_TEAL + 0.02, 1.10, None, None, 1.0),   # night road, grey M4 drifts past
    'T1': ('n10', 1.20, T_TEAL, T_T2, 1.10, None, None, 1.0),     # M3 front close
    'T2': ('n10', 4.42, T_T2, T_T3, 1.10, None, None, 1.0),       # rear 3/4 side
    'T3': ('n10', 2.50, T_T3, T_T4, 1.10, None, None, 1.0),       # roundel close
    'T4': ('n10', 7.66, T_T4, T_OUT0 + 0.15, 1.10, None, None, 1.0),  # front centred (flashes M3 / G80)
}

# portal Earths: (sprite, t0, t1, earth number, car name, outline colour)
PORTAL = [
    ('e30', T_PORTAL, T_P2, '138', 'BMW M3 E30', '#ff3a2e'),
    ('e36', T_P2, T_P3, '42', 'BMW E36', '#b46bff'),
    ('m2', T_P3, T_P4, '65', 'BMW M2', '#4fc8ff'),
    ('m4d', T_P4, T_HOLE, '1610', 'BMW M4 G82', '#ff2b45'),
]
EARTH_WHITE = ('67', 'BMW M4 G82')
EARTH_TEAL = ('928', 'BMW M3 G80')
# plates / brand decals blanked on the sprites (pin px boxes)
SPRITE_PLATES = {'e36': [(890, 1100, 1012, 1172)], 'm2': [(112, 985, 218, 1062)]}
SPRITE_PAINT = {'m4d': [(792, 836, 856, 866)]}      # "CYBER GARAGE" decal on the trunk -> painted out
# licence plates on footage (pin px search box, bright thr, text delta) -> letters replaced by the plate's own shading
PLATES = {'I1': [(380, 790, 720, 1000, 36, 13)]}
WM_CY = 1452                   # MEHRAB.7w7 line: ~3/4 height, above the YouTube / Instagram / Facebook / WhatsApp overlays
CARS = ['BMW M4 (snow, home universe)', 'BMW M3 E30', 'BMW E36', 'BMW M2', 'BMW M4 G82 (dark)', 'BMW M4 G82 (blue)',
        'BMW M4 (CCTV)', 'BMW M3 G80 (teal)']
