# 🎬 جعبه‌ابزار ادیت MEHRAB.7w7

این پوشه همه‌ی اسکریپت‌ها و افکت‌هاییه که ادیت‌ها باهاشون ساخته شدن، به‌اضافه‌ی روش کار و ایده‌ها.
توی چت جدید فقط بگو:

> «متن CHAT_START رو بخون. این رفرنس و این کلیپ‌ها رو با جعبه‌ابزار edit_toolkit توی ریپوی Supra و ایده‌های خودت ترکیب کن و یه ادیت تمیز بده.»

بعد ویدیوی رفرنس و کلیپ‌ها یا عکس‌هات رو بفرست.

**افکت‌هایی که آماده‌ان:**
- متن سه‌بعدی براق با درخشش (قرمز یا هر رنگ دیگه)
- متن و قلب نئونی، قلبی که می‌تپه و می‌شکنه
- اکولایزر آهنگ، رعد و برق، موج ضربه، جرقه، ذرات آتیش، پرتو نور، دود
- گلیچ، فلش، لرزش و زوم روی ضرب
- ترنزیشن تند و تار بین شات‌ها
- بیرون اومدن ماشین بعدی با خط‌دور نورانی به رنگ خودش
- رنگ تند و تیره با لبه‌های تار مثل لنز
- سؤال SMASH OR PASS؟ با شماره‌ی ماشین‌ها برای کامنت
- ترند «انگشتت رو با ریتم بکش»: دایره‌ی نئونی که روی هر ضرب حرکت می‌کنه و هر حرکت انگشت ماشین بعدی رو از خود دایره میاره تو کادر (شب ۴)
- خط‌های نئونی روی خطوط خود ماشین روی ضرب
- اوترو MEHRAB.7w7 با عوض شدن فونت که لوپ می‌خوره
- پایان آهنگِ آروم و کلفت (مثل نوار کاست)
- صدای ‎-14 LUFS

---

## For the assistant (technical guide)

### Layout
```
edit_toolkit/
  kit/                      reusable code (import from here)
    lib.py                  3D glossy text plates (text_mask, build_plate), compositing (over, place), easing, noise
    beats.py                music analysis: onset events, kicks, tempo, fitted beat grid (+ plot)
    clips.py                screen-recording tools: video box, timeline sheets, scene cuts, audio, per-shot extraction
    strip.py                dense time strips of a clip range (pick exact in-points)
    framing.py              9:16 crop window with zoom/centre (keeps Pinterest back button out)
    cutout.py               GrabCut car cutouts for pop transitions
    audio_finish.py         trim on beat, tape-stop ending, anti-click fades, -14 LUFS
    finish.sh               mux + x264 encode (< 30 MiB for chat delivery)
  projects/
    night3_smash_or_pass/   footage montage engine (render3.py) + shots.py + notes.md  ← template for car montages
    red_title_scene/        pure-graphics title scene (render.py) + song analysis data + notes.md
    night4_finger_rhythm/   "slide your finger along the rhythm": beat-locked finger dot + brush reveal montage (render4.py)
```
Heavy data never goes in the repo: set `export WORK=/home/claude/work_edit` and keep `clips/`, `seg/`, `cut/`, `check/`,
songs and renders there. Python deps are preinstalled (numpy, scipy, opencv, pillow, matplotlib) + ffmpeg.
pip/npm/web downloads are usually blocked → no librosa/rembg/new fonts; everything here uses only the preinstalled set.
Fonts on the box: Inter Display Black (`kit/lib.py FONT`), Inter Black, TeX Gyre Heros Cn, DejaVu, Poppins, Latin Modern, Chorus.

### House rules (from CHAT_START.txt — re-read it)
Master = vertical 4K 2160×3840 at 60 fps (smooth), very high quality; also a lighter 1080p copy for chat (< 30 MiB) ·
MEHRAB.7w7 (no @) on the whole video, low but **not stuck to the bottom and not in the middle**: above the YouTube /
Instagram / Facebook overlays (≈ 3/4 of the height, centred) — and again as the end card · clean frames: no people,
shadows, text or watermarks (inpaint or crop them out), only the car and scenery · variety of shots and transitions ·
first second = strongest full-frame shot (unless the trend itself starts differently) · outro ≈ 1 s and the video must
loop on the beat · -14 LUFS · reply in Persian; titles, descriptions and hashtags for YouTube, Instagram and Facebook
always in English (one title + 3-line description + 5 hashtags, line 3 = "New car edit every night 🔥 Follow
MEHRAB.7w7", credits for the song and the clip sources); WhatsApp status = always only the Persian follow text from
CHAT_START.txt, no title · every edit gets its own repo folder: cover + title/description text + the 4K video, plus a
README section with raw/main direct links · update the night log in CHAT_START.txt · the user liked the tape-stop
"deep" ending (Night 3) — offer/keep it · understand the reference's mechanism first and keep it (Night 4 lesson).

### Workflow
1. **Reference**: copy to `$WORK/ref.mp4`.
   `python3 kit/clips.py box ref.mp4` → video area; `python3 kit/clips.py sheet ref.mp4 ref_sheet.png --step 1`;
   `python3 kit/clips.py cuts ref.mp4` → cut times; `python3 kit/clips.py audio ref.mp4 ref.wav`;
   `python3 kit/beats.py ref.wav --from <song start> --drop <big hit> --plot audio.png`.
   Note: the first ~0.3 s of a Shorts recording may be the previous video; recordings have ~0.1 s A/V offset —
   map the reference's cuts onto the audio grid (e.g. "every 2 beats after the drop, 4 beats in the intro").
   Describe the style: rhythm, shots per subject, transitions, colour, text, outro.
2. **Plan**: choose song window (start on a grid beat / vocal entry; end = outro start + 2–3 beats so it loops),
   hook for the first second, subject order (colour story), outro. Tell the user what to send if footage is missing
   (subjects, colours, 3–4 shots each: front with lights, detail, rear, moving; vertical, 2–5 s, no text).
3. **Footage**: copy uploads to `$WORK/clips/` with short names; `clips.py sheet` per clip (step 0.5–1),
   `strip.py clip t0 t1 0.25 out.png` around candidates, `clips.py cuts clip t0 t1` to stay inside one source shot.
   Avoid: Pinterest back button (top-left), pause icon/time bar after taps, "More to explore", notification banners.
4. **Shot list**: copy `projects/night3_smash_or_pass/` to a new project folder, edit `shots.py`
   (name, subject#, clip, in-point, zoom, cx, cy, box), `SPEED` for shots that are slightly short.
   Preview framing, then `python3 kit/clips.py extract <project>`.
5. **Cutouts** (pop transitions): `kit/cutout.py` → `segment(img, rect_frac)`; save `$WORK/cut/<key>_img.png` + `_mask.npy`;
   pick a frame where the whole car is visible; tighten the rect until no background leaks.
6. **Render**: adjust `render3.py` (CARS names/colours, POP sprites, hook text, labels), test stills with
   `render3.py frames <times>` and look at a contact sheet before the full `render3.py video`.
7. **Audio + encode**: `kit/audio_finish.py` (with `--tapestop <outro start>`), `kit/finish.sh`. Check: frame count,
   duration, -14 LUFS, file < 30 MiB (SendUserFile limit), contact sheet of the final file.
8. **Deliver**: send the file, push to the repo (folder + cover + text + README section), update CHAT_START log,
   give title/description in a code block.

### Effect library — where to find each piece
| effect | where |
|---|---|
| glossy 3D text plate (any colour via top/mid/low/bottom/ext colours) | `kit/lib.py build_plate` |
| hook title, numbered labels, name plates, bottom watermark | `night3 render3.py` (TITLE, NUM, NAMES, WM) |
| whip-pan directional blur, zoom punch, shake on cuts, beat pulse | `render3.py render()` + `dir_blur`, `zoom_blur` |
| colour-outline cutout pop between subjects | `render3.py POP_SPRITE / place_sprite` |
| grade: S-curve LUT, saturation, top darkening, lens edge blur, sharpen, radial RGB split, vignette, grain | `render3.py grade()` |
| font-flicker + warp outro | `render3.py outro()` |
| neon text / neon heart (whole ↔ broken) | `red_title_scene render.py or_plate, heart_layers` |
| music spectrum bars | `render.py` (SPEC precompute + bars) |
| lightning, shockwave rings, sparks, embers, god rays, smoke, anamorphic flare | `render.py render()` |
| glitch slices, invert-red flash, power flicker, flash/exposure punch | `render.py render()` |
| beat-synced envelopes (pulse / decay_sum / energy) | `render.py` |
| tape-stop deep ending, -14 LUFS | `kit/audio_finish.py` |
| beat-locked finger dot (path, slides landing on beats), lane rails, corner targets, swipe trail | `night4 render4.py move_state / dot_pos / draw_orb / draw_rails` |
| brush reveal painted from the dot (next shot appears from the finger, neon edge) | `night4 render4.py reveal_mask / blend_reveal` |
| neon edges of the footage on the beat (Sobel + bloom), light sweep | `night4 render4.py neon_edges / leak` |
| seamless loop (outro rebuilds frame 0; smoke/dust on a loop clock) | `night4 render4.py outro_frame` |
| loop-spliced song from a Shorts recording (find loop length + silent gap) | `night4 notes.md` |

### Idea bank (mix with each new reference)
- Smash or Pass with numbers (done, Night 3) → also works for characters or "which wheel / which colour".
- Rate This Car 1–10: animated score meter that fills on the beat, final number slams in 3D.
- Pick One (M5 / C63 / RS6): 3 cutouts in a row with coloured outlines, numbers, "comment 1-2-3".
- Raw vs Edit: same clip, wipe line on the drop from flat raw to the full grade.
- Night Drive: slow → fast speed ramp into the drop, neon light streaks, rain/fog grade, taillight glow.
- Pure Engine Sound: spectrum bars + rev counter graphic synced to the engine audio.
- MEHRAB.7w7 Reveal: glitch + flicker logo, then the car reveal behind it.
- Slide your finger (done, Night 4): reuse the engine with any path (zig-zag, circle) or for characters; the finger
  can also "bring" text, numbers or a Rate-This-Car score.
- Always first understand the reference's mechanism (what the viewer does, what causes what) and keep it; make only the
  effects heavier (user feedback on Night 4).
- Always: strongest shot + hook text in frame 0, colour story between subjects, 1 s looping outro, tape-stop ending.
