# Night 6 — BMW Multiverse 🕷️🌀 (Spider-Verse template)

Final: `Night6_BMW_Multiverse/Night6_BMW_Multiverse_4K_60fps.mp4` (2160x3840 upscale of the 1080x1920 60 fps render,
854 frames = 14.233 s, -14 LUFS, tape-stop tail, seamless loop) + `…_1080p_60fps.mp4` chat copy + cover + title/description.
Night 6 of the plan was "Night Drive #2"; the user brought this template instead ("اگه خودم ادیت دیگه‌ای آوردم، همون ملاکه").

## Reference (understand the mechanism first)
* Upload: `Screen_Recording_20261005_020459_YouTube.mp4` (1080x2340, 16.3 s). rec 0–0.9: previous Short (light-blue
  BMW 3 Series). From rec ~0.9: **@miot7, "50% Spiderman Polyster bm…"**, a square (1:1) video in the Shorts player,
  loops at rec 15.10 (loop 14.241 s). No song name in the recording (generic sound icon) -> we used its own audio.
* Mechanism: Spider-Man rides a black BMW 5 Series (G60, from the *Spider-Man: Brand New Day* trailer — BMW is the film's
  car partner), Spider-Verse glitches, orange comic captions "???..." then "BMW Multiverse?" -> a white burst into a
  red portal where small cars float, each with an "Earth-XX" caption (69 red, 928 cyan, 42 dark) + a car-name caption
  -> "Earth-???" torn-paper hole opens onto Earth-67 (white high-key world, black M4 CS with a red outline + red/cyan
  fringes) -> black ink smear -> drift -> CCTV black & white night scene (REC, CAM 03, timestamp) where a teal ghost
  car materialises -> teal halftone sky world with a white M4 GT3, the creator's name "MIOT" / "VFX" flashing on the
  car on the last beats -> glowing flickering "miot.vfx" outro -> black -> stencil reveal back to the start.
* The user could not find the Spider-Man BMW shot (only Spider-Man fan edits, one with a CapCut logo) -> our home
  universe is a black M4 in the snow at night with red lights (the channel's best-performing vibe).

## Song
`$WORK/song6.wav` = the template audio = recording container [0.9338 : 15.1748]. **The recording's audio stream starts
0.0778 s into the container** (`ffprobe stream start_time`): `clips.py audio` / `ref.wav` times are container - 0.0778;
`ffmpeg -ss` uses container time. Beat grid on song6: onset grid 0.1233 + 0.5614 k (106.9 BPM), low kicks attack
~0.02 s later -> `shots6.beat(k) = 0.1383 + 0.5614 k`. Visual cuts in the screen recording run ~0.09 s ahead of its
audio. Tape-stop from 13.0 (over the outro), trimmed to 854/60 s.

## Build (render6.py + shots6.py + make_cuts6.py + cover6.py)
* Home Earth 0–3.51: 5 shots of n16 (I1 rear 8.25, I2 4.40, I3 5.60, I4 6.20 close-up, I5 0.60 drift), cuts on the
  vocal onsets 1.488 / 2.000 / 2.384 / 3.003; `grade_night` (all desaturated except red); Spider-Verse `glitch()` on
  cuts and onsets (misaligned bands, red/cyan channel split, blocky pixel chunks); captions `tag('q')` / `tag('mv')`;
  zoom-through the red angel eye into the portal (no white burst).
* Portal 3.51–5.19: `vortex()` = procedural red tunnel (log-spiral streaks from periodic FFT noise via cv2.remap at half
  res, rings, core glow — smooth, no particles); `place_car()` sprite + coloured outline glow; Earths E30 red
  (Earth-138), E36 purple (Earth-42), M2 blue (Earth-65), M4 dark (Earth-1610) — the last two on half beats
  (acceleration into the drop); spin transitions; Earth tag + car tag stacked top-left (clear of the app overlays).
* Earth-??? 5.19–5.75: `hole_masks()` jagged radial contour + paper rim + shadow; W1 footage runs inside the hole;
  grows with ease-out-back, swallows the frame on the kick.
* Earth-67 5.75–8.00: `grade_white()` high-key world, the blue paint kept (blue mask) -> red outline from the mask's
  dilation edge + comic ink edges + red/cyan split; kick punches. Ink transition `ink_mask()`: three curved tapered
  brush strokes (bristle striations, dry-brush gaps at the edges, ragged wet edges), cut W1 -> W2 (camera roll) on
  beat 12 under the ink, strokes pulled out from their tails.
* CCTV 8.00–10.24: `grade_cctv()` (B&W, noise, rolling bar, scanlines, barrel lens, vignette) + `cctv_overlay()`
  (REC dot blinking, CAM 03, CH-04, ticking timestamp, corners, crosshair); `ghost()` = teal hologram of the M3
  cutout, flickering, growing; zoom-through it into
* Earth-928 10.24–12.49: n10 shots one per beat, `grade_teal()` duotone + bloom + cyan edges + light halftone in the
  shadows only; "M3" / "G80" flash on beats 21 / 21.5 (`flash_layer`, in place of the creator's name).
* Outro 12.62–13.80: glowing MEHRAB.7w7 (TeX Gyre Bonum Bold 128, tilt 7°, halftone texture, per-letter staggered
  switch-on + random flicker dips, bloom), glitch in/out. 13.84 -> end: `reveal_frame()` = frame 0 appears
  brightest-first (the taillights first) -> the loop seam is invisible.
* Clean frames: STOP signs avoided by in-points; I1 licence plate blanked per frame (`PLATES`, low-saturation blob so
  the red taillights are untouched, pieces split by letters merged); sprite plates (E36, M2) blanked, "CYBER GARAGE"
  decal on the dark M4 painted out. Excluded: AZN-logo BMW, vicrez-logo M2 clip, CapCut-logo Spider-Man edit, the
  Mercedes (not a BMW). Persons: the grinder/sparks part of n17 not used.
* **Lesson: Pinterest/phone recordings are VFR** (r_frame_rate 120, avg ~35 fps, frames bunched). OpenCV seek
  (`CAP_PROP_POS_MSEC`) and index/fps times are off by 0.1–0.8 s from ffmpeg's real timestamps — first try showed a
  STOP sign that was "gone" on the OpenCV strip. Pick in-points on `kit/strip_ff.py` strips (ffmpeg-decoded).

## Clips ($WORK/clips) — user's uploads (8 Oct, 20 Pinterest recordings, pin box (20,96,1060,1936)), names by recording time
| name | content | used |
|---|---|---|
| n01 / n02 | Spider-Man (Brand New Day) fan edits, n02 with a CapCut logo, no BMW | — |
| n03 / n04 | red BMW M3 E30 rolling | sprite e30 (n04 4.0) |
| n05 | black E30 M3 + dark green E36 | — |
| n06 / n07 | blue M2 F87 (n07 ends on a vicrez logo) | sprite m2 (n06 8.8) |
| n08 | light-blue M4 F82 | — |
| n09 | white marble-wrap M3 F80 | — |
| n10 | white/teal marble-wrap M3 G80 at a warehouse | T1 1.20, T2 4.42, T3 2.50, T4 7.66, ghost sprite m3g (0.9) |
| n11 / n12 | purple E36 (WIN THIS CAR overlay at the end, driver visible in n11) | sprite e36 (n12 3.0) |
| n13 | black Mercedes 560 SEC | — (not a BMW) |
| n14 | black M4 G82 CGI studio ("Cyber Garage") | sprite m4d (3.4) |
| n15 | dark widebody M4 G82 in the rain (notification banner 7.8–10.2) | — |
| n16 | black M4 in the snow at night, red lights (STOP signs 5.0–5.5, 6.9–8.1) | I1–I5 |
| n17 | grey M4 night road drift (person + grinder sparks at the start) | C1 10.40 |
| n18 | black M4 G82 with exhaust flames, sunset rolling shot | — |
| n19 | purple-wrap BMW, scissor doors — AZN logo | — (logo) |
| n20 | blue M4 G82 (Portimao) parking lot, camera rolls | W1 1.60, W2 7.45 |

## Re-run
```
export WORK=/home/claude/work_edit            # clips/ (n01..n20 links), cut6/, seg6/, song6.wav
python3 make_cuts6.py                         # sprites
python3 render6.py extract                    # 60 fps frames per shot (+ plate blanking)
python3 render6.py frames 0 3.8 5.4 6.2 8.6 10.5 12.05 13 14.2   # stills -> $WORK/check6
python3 render6.py video $WORK/n6_noaudio.mp4 # ~5.5 min on 2 cores
python3 ../../kit/audio_finish.py $WORK/song6.wav $WORK/n6_audio.wav --start 0 --end 14.23333 --tapestop 13.0
bash ../../kit/finish4k.sh $WORK/n6_noaudio.mp4 $WORK/n6_audio.wav $WORK/out_4k.mp4 $WORK/out_1080p.mp4
python3 cover6.py $WORK/cover6.jpg            # white-world M4 + "BMW Multiverse?" caption
```
