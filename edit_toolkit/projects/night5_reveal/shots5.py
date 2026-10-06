# Night 5 — MEHRAB.7w7 Reveal on the "ELA PEIDA FUNK (Slowed)" template (reference: YouTube Shorts @Zs3riyx).
# Song = the template's audio cut from the reference recording: $WORK/song5.wav = rec audio [1.221 : 14.1646].
# Video time T = song5 time. Beat grid (beats.py on song5.wav): period 0.51821 s, drop (first 808 hit) at 4.336.
B = 0.51821
T_DROP = 4.336


def beat(k):
    return T_DROP + k * B


S0 = 0.0
T_OUT = beat(16)               # 12.627 last kick -> chrome MEHRAB.7w7 end card
T_END = beat(18)               # 13.664 loop point (the song's 808 tail gets a tape-stop over the end card)
FPS_OUT = 60

# intro: 3 shots of the blue GT3 RS (cuts on the half beats like the reference), then one cut per beat from the drop
CUTS = [0.0, beat(-5.5), beat(-2.5)] + [beat(k) for k in range(0, 17)]      # 20 times -> 19 shots + T_OUT

PBOX = (20, 96, 1060, 1936)    # Pinterest pin video area in the 1080x2340 recordings
# (name, chapter, clip, src_in, zoom, cx, cy, speed)   zoom >= 1.10 keeps the Pinterest back button out (framing.py)
SHOTS = [
    ('S01', 'blue', 'p02', 9.70, 1.10, None, None, 1.00),    # GT3 RS (Miami blue) rolling, skyline at dusk
    ('S02', 'blue', 'p02', 41.93, 1.12, None, None, 0.56),   # GT3 RS headlight / front corner (CGI studio), slow-mo
    ('S03', 'blue', 'p02', 43.95, 1.10, None, None, 1.00),   # GT3 RS wide rear 3/4, white studio floor (+ P1 stickers)
    ('S04', 'orange', 'p06', 3.20, 1.10, None, None, 1.00),  # DROP: P1, doors up, studio
    ('S05', 'orange', 'q1', 6.05, 1.10, None, None, 1.00),   # P1 rear, night garage
    ('S06', 'orange', 'p06', 7.58, 1.32, 610, None, 1.00),   # P1 front 3/4 close (zoom keeps the dealer plate out)
    ('S07', 'orange', 'q1', 13.05, 1.10, None, None, 1.00),  # P1 driving away (+ black Turbo S sticker)
    ('S08', 'black', 'p08', 1.95, 1.10, None, None, 1.00),   # 911 Turbo S close side pass
    ('S09', 'black', 'p07', 16.15, 1.38, 385, 905, 1.00),    # Turbo S rear close, light bar (side mirror cropped out)
    ('S10', 'black', 'p07', 2.35, 1.14, 455, None, 1.00),    # Turbo S on the highway, skyline (mirror cropped out)
    ('S11', 'black', 'p08', 1.30, 1.10, None, None, 1.00),   # Turbo S donuts, tyre marks (+ silver sticker)
    ('S12', 'silver', 'p10', 4.62, 1.10, None, None, 1.00),  # LOGO SLAM: GT3 front 3/4, sky
    ('S13', 'silver', 'p10', 13.95, 1.10, None, None, 1.00), # GT3 rear centred
    ('S14', 'silver', 'p10', 1.60, 1.10, None, None, 1.00),  # GT3 headlight close
    ('S15', 'silver', 'p10', 0.92, 1.10, None, None, 1.00),  # GT3 rear light bar (logo -> black chrome) + silver sticker
    ('S16', 'silver', 'p10', 9.85, 1.10, None, None, 1.00),  # GT3 rear 3/4 wide
    ('S17', 'silver', 'p10', 11.30, 1.10, None, None, 1.00), # GT3 headlight close, other side
    ('S18', 'silver', 'p10', 7.97, 1.10, None, None, 1.00),  # GT3 seat, door open
    ('S19', 'silver', 'p10', 3.30, 1.10, None, None, 1.00),  # GT3 wheel close
]
INTERP = {'S02'}
# clean frames (house rule): S12 has a red STOP sign on the building -> inpainted per frame (search box, pin coords)
CLEAN = {'S12': (600, 500, 1040, 1000)}
# plates with text -> letters inpainted (box x0, y0, x1, y1, bright thr, text delta): FIRST MOTORS dealer plates, P1 licence plate
PLATES = {'S03': [(130, 980, 350, 1045, 115, 30)], 'S04': [(250, 1170, 430, 1232, 160, 50)],
          'S05': [(430, 1030, 620, 1160, 150, 35)]}               # slow-mo shots extracted with motion interpolation (120 fps)

# stickers: the next car pops into the current shot (the reference's mechanism)
#   (sprite, t_in, t_hold_end, x, y, width, mode, flip)
STICKERS = [
    ('p1a', 3.80, T_DROP, 300, 1235, 500, 'slide', False),
    ('p1b', 3.95, T_DROP, 790, 1262, 540, 'slide', True),
    ('blk', 6.17, beat(4), 545, 1030, 760, 'pop', False),
    ('slv', 8.24, beat(8), 400, 1110, 640, 'pop', False),
    ('slv', 10.30, beat(12), 565, 1090, 600, 'pop', True),
]
# logo: slam on beat 8, black chrome from 10.30, gone on beat 12; end card from T_OUT
# MID_LOGO = False: the user prefers the ID NOT in the middle of the video (only the bottom line + the end card);
# beat 8 keeps the reference's white flash on the silver car. Set True to get the reference's mid-video name slam.
MID_LOGO = False
# particles: the user did not like the dotty overlays (falling snow, fire embers) -> off; the cold "snow" grade stays
SNOW = False
EMBERS = False
LOGO_IN, LOGO_DARK, LOGO_OFF = beat(8), 10.30, beat(12)
LOGO_CY = 700                  # centre of the two-line logo (reference: upper middle, 20-48 % of the height)
END_CY = 860
# intro flashes (template times, measured on the reference recording): (time, strength)
REF_FLASHES = [(0.00, 0.35), (0.20, 0.75), (0.73, 0.5), (0.86, 0.6), (1.03, 0.35), (1.39, 0.8), (1.66, 0.4), (2.17, 0.6),
               (2.42, 0.45), (2.70, 0.55), (3.04, 1.0), (3.38, 0.7), (3.86, 0.5), (4.03, 0.45), (4.18, 0.5)]
# user feedback: no white blinking flashes at all -> FLASHES empty, every white flash replaced by real transitions
FLASHES = []
# scene transitions, keyed by the index of the incoming shot (cut time = CUTS[k]; k = 19 is the end card):
#   (kind, out seconds before the cut, in seconds after it, zoom centre or None)
#   zoom = zoom-through with radial blur, spin = rotation with spin blur, whip = slide with motion blur
TRANS = {
    1: ('zoom', 0.24, 0.32, (420, 1180)),   # GT3 RS rolling -> zoom into its headlight -> headlight close-up
    2: ('spin', 0.22, 0.30, None),          # headlight -> studio rear 3/4
    3: ('zoom', 0.24, 0.32, None),          # the drop: snowy GT3 RS + P1 stickers -> P1
    7: ('spin', 0.18, 0.28, None),          # P1 -> black Turbo S (new car)
    11: ('zoom', 0.20, 0.30, None),         # Turbo S -> silver GT3 (new car, beat 8)
    19: ('zoom', 0.20, 0.0, None),          # last GT3 shot -> chrome MEHRAB.7w7 end card
}
LOOP_OUT = 0.22                # end card zooms through at the very end -> clean cut to frame 0 (seamless loop)
WM_CY = 1452                   # MEHRAB.7w7 line: ~3/4 height, above the YouTube / Instagram / Facebook overlays
BAND_Y = 0.205                 # reference look: dark band over the top ~20 % of the frame
CARS = {'blue': 'Porsche 911 GT3 RS (992)', 'orange': 'McLaren P1', 'black': 'Porsche 911 Turbo S (992)',
        'silver': 'Porsche 911 GT3 (992)'}
