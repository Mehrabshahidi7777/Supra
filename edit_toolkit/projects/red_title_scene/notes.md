# Red SMASH OR PASS title scene (12 Mehr, not a numbered night)

Final: `SmashOrPass_Red_Scene/SmashOrPass_Red_1080p.mp4` (14.5 s, -14 LUFS).
Pure graphics, no footage: glossy red 3D "SMASH" / neon "OR" / "PASS", neon heart that beats and cracks on PASS,
music spectrum bars, embers, god rays, smoke, lightning, shockwaves, sparks, anamorphic flare, glitch slices,
red invert flash, power-flicker in the quiet part, camera shake/zoom punches, MEHRAB.7w7 bottom + 1 s outro that loops.

Song: audio of the cats "Smash or Pass" Short ("edit 1 · @Yosoyandresvigevani"); `events.json` / `rms60.npy` are its onset
events and energy (times in the original recording). Video window: OFF = 1.24 → AUD_END = 15.747 (loops on the beat).

Re-run: put the song as `$WORK/music_raw.wav`, then
```
WORK=$WORK python3 render.py frames 1.24 8.5
WORK=$WORK python3 render.py video $WORK/red_noaudio.mp4
```
Every visual event is a pure function of time (closed-form particles), so frames render in parallel.
Re-usable pieces to lift: `pulse()/decay_sum()` envelopes, `bolt()` lightning, `heart_layers()` (whole / broken heart),
spectrum bars, ember field, glitch + invert flash blocks.
