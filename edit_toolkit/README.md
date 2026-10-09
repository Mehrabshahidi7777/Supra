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
- اسم MEHRAB.7w7 با حروف کرومی تیغ‌دار (مثل لوگوی ZS3 رفرنس) که روی ضرب می‌کوبه تو کادر و مشکی‌کرومی هم می‌شه — فقط برای آخر ویدیو؛ آیدی بزرگ وسط ویدیو نیاد (شب ۵)
- رنگ سرد زمستونی (فیلتر برفی) روی هر کلیپی و ماشین بعدی که مثل برچسب می‌پره تو کادر (شب ۵)
- پاک کردن تابلو و نوشته‌ی پلاک‌ها از کلیپ‌ها (شب ۵)
- ترنزیشن‌های نرم بین صحنه‌ها بدون فلش سفید: زوم به داخل (مثلاً زوم توی چراغ ماشین و رسیدن به نمای نزدیک چراغ) و چرخش با تاری (شب ۵)
- ترند مولتی‌ورس اسپایدرمنی (شب ۶): گلیچ اسپایدرورسی، برچسب‌های نارنجی کمیکی «Earth-XX» و اسم ماشین، پورتال قرمز چرخان با ماشین‌های کوچیک، سوراخ کاغذپاره که به دنیای بعد باز می‌شه، دنیای سفید با خط‌دور قرمز، ترنزیشن قلم‌موی جوهری، دوربین مداربسته‌ی سیاه‌وسفید با ماشین شبح فیروزه‌ای، دنیای فیروزه‌ای کمیکی، اسم نورانی لرزون آخر و لوپی که از روشن‌ترین نقطه‌ها شروع می‌شه
- پایان آهنگِ آروم و کلفت (مثل نوار کاست)
- صدای ‎-14 LUFS

**🛠️ موتور ادیت (`kit/engine.py`):** هر الگو تبدیل می‌شه به یه «نقشه»ی کوتاه (`projects/<شب>/recipe.py`): آهنگ و ضرب‌ها، شات‌ها روی ضرب، شماره‌ی ترنزیشن و افکت از پک پایین، متن‌ها، اسم آخر و لوپ. بقیه رو موتور خودش می‌سازه: کادر عمودی، اسلوموشن نرم، آیدی MEHRAB.7w7 سرِ جاش، صدای ‎-14، خروجی فورکی ۶۰ فریم و کاور. نقشه‌ی هر الگو توی پوشه‌ی `projects` می‌مونه که هر وقت همون ترند رو خواستی دوباره آماده باشه.

**🎞️ پک ترنزیشن و افکت شماره‌دار (۱ تا ۵۹)** (از پروژه‌های متن‌باز گیت‌هاب، بدون فلش سفید و ذرات دون‌دونه) — دو ویدیوی نمونه با همین شماره‌ها توی پوشه‌ی `VFX_Pack_Showcase` ریپوئه (ویدیوی ۱: شماره‌ی ۱ تا ۲۴، ویدیوی ۲: شماره‌ی ۲۵ تا ۵۹). توی چت فقط بگو مثلاً «ترنزیشن ۳ و ۹ و افکت ۲۰»:

| شماره | ترنزیشن | شماره | ترنزیشن / افکت |
|---|---|---|---|
| ۱ | مکعب سه‌بعدی | ۱۳ | برگشتن کاشی‌ها مثل کارت |
| ۲ | پیچ‌وتاب از چپ به راست | ۱۴ | لنز چشم حشره با رنگ‌های جدا |
| ۳ | باز شدن در و اومدن صحنه‌ی بعد | ۱۵ | هل دادن کارت به بالا |
| ۴ | گرداب | ۱۶ | کرکره |
| ۵ | جابه‌جایی کارت‌ها | ۱۷ | کالیدوسکوپ |
| ۶ | پیچ‌وتاب مورب | ۱۸ | تغییر سرعت: آهسته بعد تند |
| ۷ | چرخش و زوم با تاری حرکت | ۱۹ | اسلوموشن نرم |
| ۸ | موج آب | ۲۰ | دوربین سه‌بعدی |
| ۹ | ورق خوردن کتاب | ۲۱ | لرزش روی ضرب |
| ۱۰ | ذوب شدن رنگ‌ها | ۲۲ | ضربه‌ی لنز |
| ۱۱ | چرخیدن از گوشه با تاری | ۲۳ | رد نور چراغ‌ها |
| ۱۲ | فشرده شدن به یه خط | ۲۴ | نور رنگی گرم یا سرد |

| شماره | ترنزیشن | شماره | ترنزیشن / افکت |
|---|---|---|---|
| ۲۵ | ورق خوردن از گوشه | ۴۳ | لبه‌های نورانی |
| ۲۶ | شکستن و پرت شدن تکه‌ها | ۴۴ | موج بال پروانه |
| ۲۷ | دیوار کاشی‌ها | ۴۵ | گلیچ رنگی لرزون |
| ۲۸ | آب شدن ستون‌ها | ۴۶ | کشیده شدن دو نیمه |
| ۲۹ | گلیچ تلویزیونی | ۴۷ | زوم به داخل و بیرون |
| ۳۰ | ذوب شدن قسمت‌های تیره | ۴۸ | باد |
| ۳۱ | افتادن و بالا پریدن | ۴۹ | انعکاس روی زمین خیس |
| ۳۲ | موج رویایی | ۵۰ | مینیاتوری |
| ۳۳ | تار و واضح شدن لنز | ۵۱ | تلویزیون قدیمی |
| ۳۴ | زوم با تاری حرکت | ۵۲ | فیلم قدیمی |
| ۳۵ | حلقه‌های زوم | ۵۳ | تصویر با حروف |
| ۳۶ | چرخیدن و کوچیک شدن | ۵۴ | طراحی با خودکار |
| ۳۷ | تا شدن | ۵۵ | برجسته‌ی فلزی |
| ۳۸ | موج کاشی‌ها | ۵۶ | پیچ خوردن |
| ۳۹ | شش‌ضلعی‌ها | ۵۷ | تاری لنز با نورهای گرد |
| ۴۰ | حل شدن ابری | ۵۸ | خط‌دور جوهری |
| ۴۱ | سوختن و باز شدن سوراخ | ۵۹ | خطوط نئونی |
| ۴۲ | کالیدوسکوپ چرخان | | |

---

## For the assistant (technical guide)

### Layout
```
edit_toolkit/
  kit/                      reusable code (import from here)
    lib.py                  3D glossy text plates (text_mask, build_plate), compositing (over, place), easing, noise
    beats.py                music analysis: onset events, kicks, tempo, fitted beat grid (+ plot)
    clips.py                screen-recording tools: video box, timeline sheets, scene cuts, audio, per-shot extraction
    strip.py                dense time strips of a clip range (OpenCV seek: times drift on VFR recordings!)
    strip_ff.py             the same strip decoded with ffmpeg = real timestamps -> pick in-points HERE
    framing.py              9:16 crop window with zoom/centre (keeps Pinterest back button out)
    cutout.py               GrabCut car cutouts for pop transitions
    overlay_find.py         find logos / watermarks burned into a clip (skip or crop those clips)
    audio_finish.py         trim on beat, tape-stop ending, anti-click fades, -14 LUFS
    finish.sh               mux + x264 encode (< 30 MiB for chat delivery)
    finish4k.sh             master delivery: 4K 2160x3840 upscale + encode, plus the 1080p chat copy
    engine.py               RECIPE-DRIVEN EDIT ENGINE (start here for a new reference): recipe.py = song window +
                            beat grid + shot list + transition / effect numbers + texts + end card + loop ->
                            plan | stills | sheet | cover | render (2 workers, 4K60 master + 1080p copy, -14 LUFS)
    gltrans.py              41 scene transitions ported 1:1 from gl-transitions (MIT; page_curl BSD-3 HP),
                            GLSL -> numpy/cv2.remap: transition(name, a, b, p, ease=None); NUMBERS = number -> name for
                            all 59 pack items; CLI: list | demo A tA B tB name out.mp4 | sheet
    vfx.py                  Clip (any time incl. between frames via DIS optical flow = smooth slow-mo), ramp_times /
                            ramp_frames (speed ramps + shutter motion blur), tilt3d, shake, lens_warp, echo, light_leak;
                            looks from pixi-filters + glfx.js (MIT): reflection, tilt_shift, crt, old_film, ascii_art,
                            cross_hatch, emboss, twist, lens_blur, ink, edge_work
  projects/
    engine_demo/            6 s self-test recipe of the engine on repo footage (every engine path once)
    vfx_showcase/           numbered reels of the whole pack: showcase.py (#1-24), showcase2.py (#25-59)
                            -> VFX_Pack_Showcase/ in the repo root. Both render in parallel parts (2 workers, resumable).
                            The user picks effects BY THESE NUMBERS (tables at the top of this README, gltrans.NUMBERS).
    night3_smash_or_pass/   footage montage engine (render3.py) + shots.py + notes.md  ← template for car montages
    red_title_scene/        pure-graphics title scene (render.py) + song analysis data + notes.md
    night4_finger_rhythm/   "slide your finger along the rhythm": beat-locked finger dot + brush reveal montage (render4.py)
    night5_reveal/          "ELA PEIDA FUNK" edit: cold intro + flashes, sticker pops, blur-in cuts, spiky chrome MEHRAB.7w7
                            end card, sign/plate cleaning (render5.py, logo5.py, shots5.py, cover5.py, splice.py, notes.md)
    night6_multiverse/      Spider-Verse "BMW Multiverse": glitch, comic Earth tags, red vortex portal, torn-paper hole,
                            white world + red outline, brush-ink wipe, CCTV + teal ghost, teal duotone world, glowing
                            flicker name, brightest-first loop reveal (render6.py, shots6.py, make_cuts6.py, cover6.py)
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

### Edit engine (`kit/engine.py`) — the default way to build an edit (since Night 7)
1. Analyse the reference (step 1 below), write down its mechanism and timeline in the recipe's docstring.
2. `projects/<nightN_name>/recipe.py` with `RECIPE = dict(...)` — full key list in the engine docstring
   (`python3 kit/engine.py`). Copy `projects/engine_demo/recipe.py` as a start. Paths: relative to `$WORK`,
   `repo:...` for repo files. Song: `song` + `song_in` (a grid beat) + `beat` (period) or `grid` (beat list).
3. Shots: `src, at, beats|dur, zoom, cx, cy, push, speed (number or ramp keys), fx [numbers|fn], trans (number),
   tdur, text, pre [clean-up fns]`. Transitions are centred on the cut (p = 0.5 on the beat). Effects 18/19 =
   default ramp / slow-mo; 20–24 and 49–59 per shot or as `look` for the whole video; `punch` = beat zoom pulses.
4. Reference-specific graphics (charts, logo equations, portals …) = plain functions in the project folder used as
   `fx` / `pre` / custom shots (`src` may be a still image; an fx may ignore the frame and draw everything).
5. `plan` (timeline + source-length checks) → `stills` / `sheet` → look → `render` → `cover`. Outputs in
   `$WORK/<name>/`: `<name>_4K_60fps.mp4`, `<name>_1080p_60fps.mp4`, `<name>_cover.jpg`.
6. Speed: ~1 s per frame per worker with flow in-betweens + a global look; 2 workers (the box OOM-kills at
   ~5.5 GB, each worker keeps ≤ 2 shots of 150 frames). A 15 s Short ≈ 8–10 min.

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
| spiky chrome lettering (blade strokes + thorn tips + barbs, chrome / black-chrome gradient maps, light sweep) | `night5 logo5.py` |
| chrome logo slam over footage (dark stroke + shadow, scene reflection via normals, punch on kicks) — titles / end cards, not the ID mid-video | `night5 render5.py logo_layer` |
| clean frames: inpaint a red street sign (wall texture copy) / blank dealer or licence plates (letters -> plate shading) | `night5 render5.py remove_red_sign / blank_plate` |
| re-render frame ranges and splice them into a finished render (fast fixes) | `night5 splice.py` |
| user re-edited our video in CapCut: remove something we baked in (e.g. the top band) from THEIR export while keeping their filters/effects (3D LUT of their filter + band delta) | `night5 capcut/fix_band.py, lut3d.py` |
| scene transitions without white flashes: zoom-through (radial blur, custom centre), spin (spin blur), timed to peak on the cut | `night5 render5.py zoom_fx / spin_fx / apply_trans` + `shots5.TRANS` |
| snowy look on any clip (milky cold grade keeping the blue paint, frost edges; falling-snow particles exist but the user didn't like them) | `night5 render5.py grade_cold / draw_snow` |
| fire ember streaks + bokeh embers (user didn't like dotty particles — ask first) | `night5 render5.py draw_embers` |
| next-car sticker: slide in (motion blur) or pop with white rim flash, contact shadow; plate fill | `night5 render5.py stickers / place / clean_rect` |
| dark top band with a violet edge line on flashes (ELA PEIDA template look) | `night5 render5.py finish` |
| logo / watermark detector for screen recordings (persistent edges across shots) | `kit/overlay_find.py` |
| Spider-Verse glitch: misaligned bands, red/cyan channel split, blocky pixel chunks (cuts + onset bursts) | `night6 render6.py glitch` |
| orange comic caption boxes ("Earth-" red + number blue, car name, "???...", "BMW Multiverse?"), pop-in | `night6 render6.py _tag / tag_anim` |
| red vortex portal (log-spiral streaks from periodic FFT noise, rings, core glow — no particles) | `night6 render6.py vortex` |
| car sprite with coloured outline glow + rim (portal Earths), dark car lift | `night6 render6.py sprite / place_car` |
| torn-paper hole opening onto the next shot (jagged contour, paper rim, shadow) | `night6 render6.py hole_masks / hole_frame` |
| high-key white world, blue paint kept, red outline from the colour mask + comic ink edges | `night6 render6.py grade_white` |
| brush-ink wipe: curved tapered strokes, bristles, dry-brush gaps, pulled out from the tails | `night6 render6.py ink_mask` |
| CCTV look (B&W, noise, rolling bar, scanlines, barrel lens) + REC / CAM / timestamp / corners overlay | `night6 render6.py grade_cctv / cctv_overlay` |
| hologram ghost car (teal recolour, flicker, glitch slices) | `night6 render6.py ghost` |
| teal comic duotone + bloom + cyan edges + light halftone (shadows only) | `night6 render6.py grade_teal` |
| big glowing text flash on the beat (white, dark rim, teal glow) | `night6 render6.py flash_layer` |
| glowing flickering name outro (per-letter switch-on + flicker dips, halftone, bloom) | `night6 render6.py outro_frame` |
| loop seam: frame 0 appears from black brightest-first (lights first) | `night6 render6.py reveal_frame` |
| licence plate on a NIGHT shot (dim plate next to red taillights): low-saturation blob, merged pieces | `night6 render6.py blank_plate` |
| ID line readable on white backgrounds (adaptive shadow + dark rim) | `night6 render6.py finish` |
| **VFX pack #1–17** transitions: cube, crosswarp, doorway, swirl, swap, directional_warp, revolve, ripple, book_flip, morph, tangent_blur, squeeze, grid_flip, flyeye, push_scaled, window_slice, kaleidoscope (numbers = showcase order) | `kit/gltrans.py` (`showcase.ORDER` maps number -> name) |
| 3D-stage transitions (cube / doorway / swap) on a dark blurred stage instead of black: `bg='blur'` | `kit/gltrans.py` |
| **#18** speed ramp: slow parts optical-flow interpolated, fast parts shutter-blurred; keys = (out time, speed) | `kit/vfx.py ramp_frames` |
| **#19** smooth slow motion from any clip (DIS flow, ~170 ms/frame at 1080p) | `kit/vfx.py Clip.at` |
| **#20** 3D camera swing of a flat shot, auto-zoom so no border shows | `kit/vfx.py tilt3d` |
| **#21** smooth impact shake with motion blur along the move (drive `strength` with a beat envelope) | `kit/vfx.py shake` |
| **#22** lens punch (barrel bulge / pinch) | `kit/vfx.py lens_warp` |
| **#23** light trails (lighten echo of the last ~10 frames; 'mean' = ghost car) | `kit/vfx.py echo` |
| **#24** soft colour leak, warm / teal / red, capped so it never goes white | `kit/vfx.py light_leak` |

| **VFX pack #25–48** transitions: page_curl (back of the page shows A darkened; `back='paper'` = original white sheet), shatter, mosaic, doom_melt, datamosh (strobe removed), luma_melt, bounce, dreamy, defocus, cross_zoom, zoom_circles, rotate_vanish, fold, tiles_wave, hexagonalize, perlin, burn_out, power_kaleido, edge_glow, butterfly, glitch_memories, split_slide, zoom_in_out (`max_zoom` 0.8), wind | `kit/gltrans.py` (`NUMBERS`) |
| **#49** wet-floor / water reflection under `boundary` (set it at the tyres), animate `t` for waves | `kit/vfx.py reflection` |
| **#50** tilt-shift miniature (sharp band at `y`) | `kit/vfx.py tilt_shift` |
| **#51** CRT TV lines + vignette, **#52** old film (sepia, scratches; new `seed` per frame) | `kit/vfx.py crt / old_film` |
| **#53** ASCII glyph picture, **#54** pen cross-hatch, **#55** emboss metal, **#58** comic ink outlines | `kit/vfx.py ascii_art / cross_hatch / emboss / ink` |
| **#56** local twist (animate `angle`) | `kit/vfx.py twist` |
| **#57** lens blur with hexagon bokeh; `keep=mask` keeps the car sharp (mask from `cutout.py`) | `kit/vfx.py lens_blur` |
| **#59** neon edge drawing (`tint` = line colour on black; without tint = glfx black/white) | `kit/vfx.py edge_work` |

Speed at 1080x1920 on this 2-core box (ms per frame): window_slice 45, ripple 60, crosswarp 100, squeeze 110,
swirl 110, morph 120, push_scaled 140, flyeye 140, book_flip 170, doorway / grid_flip / directional_warp ~200,
swap 220, cube 270, revolve 590 (9 blur taps), kaleidoscope 650, tangent_blur 1100 (12 taps). A 0.6 s transition at
60 fps = 36 frames, so even the heaviest is well under a minute. Pack 2: doom_melt / luma_melt / dreamy / fold /
zoom_in_out / wind 60–70, split_slide 90, bounce 100, zoom_circles / rotate_vanish 120, burn_out 170, tiles_wave /
hexagonalize 200, perlin / glitch_memories 230, mosaic 240, defocus 500, butterfly 580, edge_glow 830,
power_kaleido 1340, page_curl / shatter 1540, cross_zoom 1730 (16 taps), datamosh 2600. Looks: twist 40, edge_work /
ink 110, emboss 140, reflection 150, cross_hatch 190, ascii_art 260, crt 380, tilt_shift 390, old_film 440,
lens_blur 620. Memory: the box OOM-kills at ~5.5 GB — keep at most ~2 shots of 1080p frames in memory per process.

### Idea bank (mix with each new reference)
- Smash or Pass with numbers (done, Night 3) → also works for characters or "which wheel / which colour".
- Rate This Car 1–10: animated score meter that fills on the beat, final number slams in 3D.
- Pick One (M5 / C63 / RS6): 3 cutouts in a row with coloured outlines, numbers, "comment 1-2-3".
- Raw vs Edit: same clip, wipe line on the drop from flat raw to the full grade.
- Night Drive: slow → fast speed ramp into the drop, neon light streaks, rain/fog grade, taillight glow.
- Pure Engine Sound: spectrum bars + rev counter graphic synced to the engine audio.
- MEHRAB.7w7 Reveal (done, Night 5): one cut per beat, next car pops in as a sticker, white flash on the last car,
  spiky chrome MEHRAB.7w7 as the end card. User feedback: **no big ID in the middle of the video** (only the bottom
  line + the end, `shots5.MID_LOGO = False`), **no dotty particles** (falling snow, embers, stars: `SNOW`/`EMBERS`
  off), **no white blinking flashes** — use real transitions (zoom-through, spin, whip) between scenes instead — and
  **no dark/blurred band at the top** (`shots5.BAND = False`). The user sometimes adds their own CapCut filters/effects
  on top of our edit (Night 5: published their CapCut version) — keep the ID off the effects' path if possible.
  The cold grade itself was liked. Reuse `logo5.py` for any chrome title (car names, "SMASH OR PASS", …).
- Slide your finger (done, Night 4): reuse the engine with any path (zig-zag, circle) or for characters; the finger
  can also "bring" text, numbers or a Rate-This-Car score.
- BMW Multiverse (done, Night 6): Spider-Verse jumps between "Earths", one BMW variant per Earth (colour per Earth),
  car tags so viewers learn the models; works for any brand or for characters ("Spider-Man variants"), and the
  Earth tags make an easy comment hook ("Which Earth would you live in?").
- Screen recordings are VFR: pick in-points with `kit/strip_ff.py`, never with OpenCV seek times (Night 6 lesson).
- Always first understand the reference's mechanism (what the viewer does, what causes what) and keep it; make only the
  effects heavier (user feedback on Night 4).
- Always: strongest shot + hook text in frame 0, colour story between subjects, 1 s looping outro, tape-stop ending.
