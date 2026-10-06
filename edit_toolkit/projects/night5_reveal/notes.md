# Night 5 — MEHRAB.7w7 Reveal (chrome-logo reveal on the "ELA PEIDA FUNK" template)

Status (6 Oct 2026 = 14 Mehr, evening): reference analysed, car list sent to the user, **waiting for clips**.
The user wants this edit to follow the reference exactly ("حق رو این نمونه"): same mechanism, same timings, heavier
effects, and MEHRAB.7w7 in place of the creator's "ZS3" logo. `ref_sheet.jpg` = one frame per shot of the reference.

## Reference
* Upload: `Screen_Recording_20261006_214440_YouTube.mp4` (1080x2340, 14.96 s, YouTube Shorts "use this template" page).
  - rec 0.0–1.0: previous Short — @OpN…Music, sound chip "ELA PEIDA FUNK🔥", a still of a red 992 GT3 RS in a Porsche
    showroom (the song's page; no editing style to copy).
  - rec 1.0–14.3: **the template** — @Zs3riyx, caption "Thank you for my 400 hundred subscribe 🎉❤️",
    sound chip "ELA PEIDA FUNK (SLOWED)". Loops at rec 14.30.
* Song: **ELA PEIDA FUNK (Slowed)** — Dj v2be, DJ SMG, XSKAY11 & DJ llz (EP "ELA PEIDA FUNK", Echo8, 2026, baile funk).
  Other versions on the EP: original, Super Slowed, Sped Up — use the **Slowed** one.
* Time base: **template t = rec_video − 1.015 = rec_audio − 1.15** (recording A/V offset 0.135 s; after correction every
  cut lands exactly on a kick). Loop period 13.286 s (audio restarts at rec 1.221 and 14.507).
  Song inside the template: t 0.07 → 13.015, then silence until the loop.
* Grid: 115.74 BPM, P = 0.51841 s. **Drop = beat 0 at t 4.333** (quiet vocal/melody intro before it; a heavy
  808/kick on every beat after it). Beat k = 4.333 + 0.51841·k. Last kick k = 16 ≈ 12.63 s. Template = 13.29 s ≈ 25.6 beats.
* `$WORK/song5.wav` = rec audio [1.221 : 14.1646] (template t 0.071 → 13.015):
  `ffmpeg -ss 1.221 -to 14.1646 -i rec.mp4 -vn -ac 2 -ar 48000 -c:a pcm_s16le song5.wav`

## Mechanism (keep it!)
1. **Calm intro, 4.33 s (≈8.4 beats):** car 1 (blue 992 GT3 RS) in snow, 3 shots — wide, front-corner close-up,
   rear 3/4 drifting. White exposure flashes (car turns to a white silhouette, purple/blue chromatic line at the frame
   edge, yellow fringe on the car) on the vocal accents ≈ t 0.0, 0.7, 1.44 (cut), 2.4, 2.7, 3.05 (cut), 3.4, 3.9.
   The video *starts* with a flash, which also hides the loop seam.
2. **Next cars arrive as stickers:** t ≈ 3.9–4.3 two orange P1 cutouts slide in from the right and park in front of
   the Porsche, still inside the snow shot.
3. **Drop (t 4.333):** heavy directional/zoom blur → real footage of those cars. From here **one cut per beat**,
   every new shot enters with a strong motion blur that clears in ~0.15–0.25 s; orange fire embers float over
   everything until the end.
4. **4 beats per car;** on the 4th beat a cutout of the NEXT car pops into the current shot (plain cutout, no outline).
5. **Reveal (beat 8, t 8.48):** white flash, the creator's name in huge spiky chrome letters (Y2K / tribal chrome,
   ~90 % of the width, upper-middle ≈ 20–48 % of the frame height) slams in with blur over the silver car; it stays
   4 beats over changing shots and turns **black chrome** on its 4th beat while a silver-car cutout pops in.
6. **Ending:** 4 more silver shots without the logo, the last one holds ~1.5 beats, fade to black with embers
   (t 12.94–13.29), loop back to the snow flash.
* Look: the top ~21 % of the frame is a dark grey band (darkened/blurred top) over every shot; snow part cold and
  milky, real footage warm and contrasty (gold grass, blue sky).

## Shot map (template time; rec = t + 1.015)
| shot | t | beats | content |
|---|---|---|---|
| S1 | 0.00–1.44 | intro | blue 992 GT3 RS in snow, wide (power line, misty hills) — flash in |
| S2 | 1.44–3.05 | intro | front-corner close-up (headlight, forged-carbon bonnet) |
| S3 | 3.05–4.33 | intro | rear 3/4 drifting in snow; 2 orange P1 cutouts slide in from the right at 3.9 |
| S4 | 4.33–4.84 | 0 drop | orange P1s parked in a row (event car park) |
| S5 | 4.84–5.39 | 1 | same lot, closer |
| S6 | 5.39–5.92 | 2 | orange P1 (wing up) approaching |
| S7 | 5.92–6.43 | 3 | P1 rear 3/4 + black 992 GT3 RS cutout pops in |
| S8 | 6.43–6.94 | 4 | black 992 GT3 RS, fisheye low rear: swan-neck wing, red light bar |
| S9 | 6.94–7.46 | 5 | black RS rear close (light bar) |
| S10 | 7.46–8.00 | 6 | black RS interior, door open (bucket seats, red belts) |
| S11 | 8.00–8.48 | 7 | black RS wing + silver 991 GT3 cutout pops in at the left |
| S12 | 8.48–9.02 | 8 | **flash + chrome logo slam**, silver 991 GT3 3/4 front on a grass field (event tents) |
| S13 | 9.02–9.53 | 9 | logo + silver rear (central twin exhausts, wing, yellow UK plate) |
| S14 | 9.53–10.06 | 10 | logo + silver front close (headlight) |
| S15 | 10.06–10.57 | 11 | logo turns black chrome; silver front cutout over the rear-deck louvres |
| S16 | 10.57–11.09 | 12 | silver front, far (field, tents) — logo gone |
| S17 | 11.09–11.60 | 13 | bonnet close-up, dutch angle (crest, plate) |
| S18 | 11.60–12.14 | 14 | side window at the tent ("GT" sticker) |
| S19 | 12.14–12.94 | 15–16 | side profile, black centre-lock wheel, yellow calipers → fade to black with embers 12.94–13.29 |

## Our version (plan)
* Same structure and timings; cars in the same order and colours: **blue 992 GT3 RS in snow → orange McLaren P1 →
  black 992 GT3 RS → silver 991 GT3** (colour story cold → fire → dark → chrome; the silver car matches the chrome logo).
* "ZS3" → **MEHRAB.7w7** in spiky chrome (two lines "MEHRAB" / "7w7" if one line gets too small — test both).
  No spiky/chrome font on the box → build it: thick letters (Inter Black) + thorn polygons on stroke ends/corners,
  chrome shading from the distance transform (env-map bands, dark reflections, specular streaks), light sweep on
  the beat, slam with blur + shake + shockwave/sparks (`red_title_scene render.py`), black-chrome switch on beat 11.
* Heavier: stronger whip/zoom blur in (`render3.py dir_blur / zoom_blur`), punch + shake on every kick, denser embers
  with glow, flash with RGB split in the intro, cutout pops with a short squash/bounce (`render3.py POP_SPRITE`,
  `kit/cutout.py`), keep the dark top band.
* End: instead of a plain black fade, chrome MEHRAB.7w7 on black with embers (~1 s end card), then the loop seam
  into the snow flash. House rules: 4K 60 fps master + 1080p chat copy, MEHRAB.7w7 line at ~3/4 height on the whole
  video, -14 LUFS, title/description in English with credits for the song and clip sources.

## Requested from the user (6 Oct)
1. Porsche 911 GT3 RS (992), blue, in snow — 3 clips: wide, front close-up with headlight, rear moving/drifting.
2. McLaren P1, orange — 4 clips: parked (several together is best), coming at the camera, rear with the wing, one
   with the whole car visible (for the sticker).
3. Porsche 911 GT3 RS (992), black — 4 clips: low rear with the big wing and red light bar, side, interior with the
   door open, one with the whole car visible.
4. Porsche 911 GT3 (991), silver — 6–8 clips (8 beats on screen): front, rear with the exhausts, bonnet close-up,
   side with the wheel, one with the whole car visible.
Every clip 2–5 s, vertical if possible, no text, best quality, sent as files. If no blue one in snow turns up, any
colour of the same car in snow works.
