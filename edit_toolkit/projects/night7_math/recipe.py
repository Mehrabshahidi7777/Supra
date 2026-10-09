"""Night 7 — Old School BMW x "Math ahh edit" (@miot7 template). 23 beats @ 101 BPM = 13.66 s, song from the reference
recording (beat grid: period 0.59384 s, beat at 0.3831; drop on beat 5 = 3.35 s).

  beats  0-1.5   title OLD SCHOOL / M3 MATH over a dark-teal E46 M3 (angel eyes)       [glitch in/out]
  1.5-3.5        Mercedes star as a teal neon outline in dark fog                          [cross zoom]
  3.5-5          Jaguar as a white neon outline                                           [datamosh on the drop]
  5-9            equation  sqrt(Mercedes x Audi) + McLaren/(Tesla - Lexus) x Jaguar = BMW, terms pop on half
                 beats, camera dollies along, dives into the BMW roundel                  [cross zoom]
  9-13           3D chart "BMW M3 Power Evolution": roundel draws the line, E30 195 / E36 286 / E46 343 PS
                 (launch outputs, BMW M)                                                  [revolve]
  13-16          white E36 tumbling through dark space, orange light beams               [defocus]
  16-21          velocity, one cut per beat, film grain (old-school test): red E30 B&W -> colour pop,
                 blue E30 headlights, E46 drift in smoke + red ghost, E46 M3 wheels, E46 M3 angel eyes slow-mo
  21-23          MEHRAB.7w7 glowing end card -> loops into frame 0
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes as S  # noqa: E402

PIN = (20, 96, 1060, 1936)          # Pinterest video area on a 1080x2340 recording
# keep zoom/cy so the crop top stays below y=150 of the box: the Pinterest back button sits at its top-left
REC = 'n7/in/rec{}.mp4'.format
FILM = S.OLD_FILM

RECIPE = dict(
    name='night7_math',
    song='n7/ref.wav', song_in=0.3831, beat=0.59384,
    shots=[
        dict(src=REC(6), box=PIN, at=15.02, beats=1.5, zoom=1.15, cy=0.57, push=0.05, fx=[S.title_fx],
             trans=45, tdur=0.30),
        dict(draw=S.outline_scene('logo_mercedes', (0.25, 1.0, 0.82), drift=(1, -1)), beats=2.0, trans=34, tdur=0.32),
        dict(draw=S.outline_scene('logo_jaguar', (1.0, 0.86, 0.92), drift=(-1, 1), tint=(0.12, 0.11, 0.13)),
             beats=1.5, trans=29, tdur=0.42),
        dict(draw=S.equation, beats=4.0, trans=34, tdur=0.30),
        dict(draw=S.chart, beats=4.0, trans=7, tdur=0.55),
        dict(draw=S.tumble, beats=3.0, trans=33, tdur=0.32),
        dict(src=REC(10), box=(20, 648, 1060, 1856), at=1.9, beats=1.0, zoom=1.0, cy=0.5, push=0.06,
             fx=[S.velocity_grade, S.bw_pop, FILM], trans=34, tdur=0.26),
        dict(src=REC(2), box=(24, 96, 1060, 1936), rot='ccw', at=4.1, beats=1.0, zoom=1.0, cx=0.5, push=0.08,
             fx=[S.velocity_grade, FILM, 21], trans=7, tdur=0.42),
        dict(src=REC(5), box=PIN, at=25.05, beats=1.0, zoom=1.08, cy=0.55, speed=0.8,
             fx=[S.velocity_grade, S.red_ghost, FILM], trans=34, tdur=0.26),
        dict(src=REC(6), box=PIN, at=3.45, beats=1.0, zoom=1.12, cy=0.57,
             fx=[S.velocity_grade, FILM, S.radial_punch], trans=47, tdur=0.28),
        dict(src=REC(6), box=PIN, at=12.75, beats=1.0, zoom=1.12, cy=0.55, speed=0.55, push=0.10,
             fx=[S.velocity_grade, FILM]),
    ],
    punch=dict(every=1, zoom=0.025, **{'from': 9.40}),
    grain=0.012,
    outro=dict(beats=2, text='MEHRAB.7w7', style='glow', color='#f2fffb', bg='blur', trans=29, tdur=0.30, y=0.45),
    loop=dict(trans=33, dur=0.30),
    cover=dict(t=0.45),
)
