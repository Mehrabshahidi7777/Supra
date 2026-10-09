"""Engine demo / self-test: 6 s on shots from the channel's own edits (repo footage) — every engine path once:
flow slow-mo, 3D tilt, light trails, shake, look (old film), beat punch, plate hook text, 5 numbered transitions,
glow end card, loop seam, tape-stop audio.  Run:  python3 kit/engine.py render projects/engine_demo/recipe.py --no-4k
"""
N5 = 'repo:Night5_MEHRAB7w7_Reveal/Night5_MEHRAB7w7_Reveal_1080p_60fps.mp4'
SP = 'repo:BMW_M_Space_Edit/BMW_M_Lost_in_Space_1080p.mp4'
CL = 'repo:CLS63_AMG_Edit/CLS63_AMG_Edit_1080p_60fps.mp4'
N6 = 'repo:Night6_BMW_Multiverse/Night6_BMW_Multiverse_1080p_60fps.mp4'

RECIPE = dict(
    name='engine_demo',
    song=N5, song_in=4.3191, beat=0.51801,          # beats.py grid: period 0.51801, beat at 4.3191 (the drop)
    shots=[
        dict(src=N5, at=0.10, beats=2, zoom=1.15, cy=0.40, push=0.06, trans=34, tdur=0.45,
             text=dict(text='OLD SCHOOL?', style='plate', size=150, y=0.28)),
        dict(src=SP, at=7.40, beats=2, zoom=1.2, cy=0.42, fx=[20], trans=7, tdur=0.6),
        dict(src=N5, at=4.45, beats=2, zoom=1.15, cy=0.42, speed=0.25, trans=29, tdur=0.5),
        dict(src=CL, at=14.60, beats=2, zoom=1.2, cy=0.40, speed=0.25, fx=[23], trans=26, tdur=0.6),
        dict(src=N6, at=0.00, beats=2, zoom=1.2, cy=0.42, speed=0.8, fx=[21], trans=47, tdur=0.4),
    ],
    look=[dict(n=52, mix=0.7)],
    punch=dict(every=2, zoom=0.03),
    outro=dict(beats=2, text='MEHRAB.7w7', style='glow', bg='blur'),
    loop=dict(trans=33, dur=0.30),
    cover=dict(t=0.45),
)
