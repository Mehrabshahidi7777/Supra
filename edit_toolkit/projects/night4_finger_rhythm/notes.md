# Night 4 — Slide Your Finger Along the Rhythm 👆 BMW Edit (engine + shot list)

Final (v3, new house rules): `Night4_SlideYourFinger_BMW/Night4_SlideYourFinger_BMW_4K_60fps.mp4` (2160x3840 upscale of the
1080x1920 60 fps render, 17.67 s = 1060 frames, -14 LUFS, tape-stop ending, seamless loop: last frame == first frame)
+ `…_1080p_60fps.mp4` chat copy. v2 (first delivery) was 1080p 30 fps with the ID at the very bottom.
v3 changes: 60 fps (`N4_FPS`, footage extracted to `$WORK/seg60`), MEHRAB.7w7 line centred at y 1452 (`WM_CY`, above
the app overlays), finger path moved up 60 px, 'davidjames' dealer plate on S07 blanked (`CLEAN` → `clean_plate()`).

## Reference (understand the mechanism first!)
YouTube Short (XTREME CARS, song chip "CLIMA LINDO (SLOWED) · GXM…", caption "SLIDE YOUR FINGER ALONG…").
Black screen, text "slide your finger along the rhythm", a white dot that makes ONE simple slide per beat along the
bottom and the right edge: top-right -> bottom-right -> bottom-left -> bottom-right -> top-right … (cycle down, left,
right, up). The viewer follows it with a finger; on the drop (~8 s) a BMW montage starts, one cut per beat (14 shots),
~18 s loop.
**Lesson (user feedback):** the first draft made the dot trace the car's outline — the user said that was a different
style. The trend is the finger following the dot's simple slides, and the finger "bringing" the car. Keep the
reference's mechanism; only make the effects heavier.

Song analysis: recording loop length 18.1665 s; loop-1 audio starts at rec 0.5835 (loop 2 at 18.75 after a silent gap).
`$WORK/song4.wav` = rec[18.75 : +6 s] + rec[0.5835+6 : …] (20 ms crossfade). Grid 84.98 BPM: beat k = 0.1221 + 0.70608 k,
drop = beat 11 = 7.889, riser 6.48–7.889, outro = beat 24 = 17.068. Video S0 = 0.08 → T_END = 17.747 (25 beats → the
loop seam stays on the beat).

## Our build (render4.py)
* Finger path `shots.py TR/BR/BL` = (860,560)/(860,1330)/(180,1330) — kept off the Shorts like/comment column.
  Move k lands exactly on beat k; intro slides 0.50 s, montage swipes 0.32 s (`TRAVEL_*`).
* Intro: neon orb (motion-blurred core, swipe trail, halo, anamorphic streak, breathing touch ring), faint lane rails
  with the stretch just slid lit, corner targets (the next one pulses), shockwave + sparks + shake on landings,
  orb-lit smoke + dust, text "slide your finger / along the rhythm" (Poppins Bold, centred x=470), riser speed lines.
* The finger brings the car: `reveal_mask()` = brush reveal within r(q) of the stretch slid so far, neon edge ring.
  Last intro slide paints shot 1 in (power 4 → mostly in the last 0.2 s), orb drawn on top; drop = flash, two rings,
  48 sparks, glitch, RGB split.
* Montage: small dot keeps sliding; each swipe paints the next shot in from the dot (power 1.8); landing = cut with
  punch, shake, neon Sobel edges on the beat (+ half-beat), light sweep on odd shots, flash on 'right' landings,
  glitch on 'left', zoom blur on 'up', vertical RGB split on up/down.
* Outro: the last swipe paints in MEHRAB.7w7 (font flicker 0.36 s, then dissolve), the dot rests top-right, rails +
  text fade back in; smoke/dust run on the intro clock (`Tl`) so the seam is invisible.
* Cover: `cover4.py` (shot 1 + orb mid-swipe + trend text).

## Clip files ($WORK/clips) → user's uploads (6 Oct, all Pinterest recordings, pin box (20,96,1060,1936))
| name | upload | content | used |
|---|---|---|---|
| p1 | …_050013_Pinterest | white BMW X4 M40i, dealer (AliancaAutomoveisBH) | S12 8.60 |
| p2 | …_050128_Pinterest | silver X4 M turntable 0–31 s; blue M3 Competition 48–63 s (David James Limited) | S07 58.55 |
| p3 | …_050351_Pinterest | dark BMW X5, snow, orange interior (Anhelika) | S08 7.85 |
| p4 | …_050637_Pinterest | M5 CS yellow DRLs 0–27 s (SUPERVELOCE); night garage M5 blue lasers 32–51 s (sup3rch4rg3d), white loading frame at 32.35! | S09 10.20, S04 32.70, S05 34.32 |
| p5 | …_050726_Pinterest | M5 F90 cobblestones 0–21 s (FLVSHOW); garage angel eyes 25–33 s; drift 33.6–38.5 s (ИСАГИ) | S10 2.70, S06 25.30, S13 34.85 |
| p6 | …_050803_Pinterest | M5 G90 night gas station, glowing kidneys (official shagun); pin loops every 12.68 s, head-on = 12.82–13.45 only | S01 12.84 (speed 0.62), S02 2.50, S03 6.38 |
| p7 | 5df4eb73 (2.7 s) | AI clip: M3 Touring floating in a showroom (VERA AI KREATOR) | S11 0.80 |

## Re-run
```
export WORK=/home/claude/work_edit            # clips/, seg/, check/, song4.wav
python3 render4.py extract                    # per-shot frames incl. pre-roll (PRE / TRAVEL_MONT before each cut)
python3 render4.py frames 0.08 7.7 8.3 17.74  # stills -> $WORK/check
python3 render4.py video $WORK/n4_60_noaudio.mp4   # 60 fps: ~9 min with 2 workers (N4_FPS=30 for quick tests)
python3 ../../kit/audio_finish.py $WORK/song4.wav $WORK/n4_audio.wav --start 0.08 --end 17.7467 --tapestop 17.068
bash ../../kit/finish4k.sh $WORK/n4_60_noaudio.mp4 $WORK/n4_audio.wav $WORK/out_4k.mp4 $WORK/out_1080p.mp4
python3 cover4.py $WORK/cover.jpg
```
