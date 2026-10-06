# Night 5 — Porsche GT3 RS & McLaren P1 — Snow to Fire ❄️🔥 ("MEHRAB.7w7 Reveal" on the "ELA PEIDA FUNK" template)

Final: `Night5_MEHRAB7w7_Reveal/Night5_MEHRAB7w7_Reveal_4K_60fps.mp4` (2160x3840 upscale of the 1080x1920 60 fps render,
13.66 s, -14 LUFS, tape-stop tail, loops) + `…_1080p_60fps.mp4` chat copy + cover + title/description.
The user wanted it to follow the reference exactly ("حق رو این نمونه"): same mechanism and timings, heavier effects,
MEHRAB.7w7 in place of the creator's "ZS3" logo. `ref_sheet.jpg` = one frame per shot of the reference.
**User feedback after the preview: no big ID in the middle of the video** — only the bottom MEHRAB.7w7 line and the
chrome name at the end. So the mid-video slam (beats 8–12) is off: `shots5.MID_LOGO = False` (beat 8 keeps the white
flash). The logo engine stays for end cards (and `MID_LOGO = True` brings the reference's slam back if ever wanted).
**Second feedback: the user didn't like the dotty particles** ("ستاره‌ها و برف دون‌دونه") — falling snow in the intro and
the fire embers are OFF (`SNOW = False`, `EMBERS = False`); the cold snowy grade ("the filter") stays, they liked it.
**Third feedback: no white blinking** ("صحنه سفید شده چشمک میزنه") — all white flashes are gone (intro flashes
`FLASHES = []`, drop / chapter / beat-8 / sticker / end-card / loop flashes) and every scene change got a real
transition instead (`shots5.TRANS`): zoom-through into the GT3 RS headlight -> headlight close-up, spin -> studio
shot, zoom-through on the drop (stickers fly with it), spin into the Turbo S, zoom-through into the GT3, zoom into the
end card, and the end card zooms through at the very end -> clean cut to frame 0 (loop). Same-car cuts keep the
reference's blur-in whip; impact on cuts = punch + shake + a short colour fringe, never white.

## Reference
* Upload: `Screen_Recording_20261006_214440_YouTube.mp4` (1080x2340, 14.96 s, YouTube Shorts "use this template" page).
  - rec 0.0–1.0: previous Short — @OpN…Music, sound chip "ELA PEIDA FUNK🔥", a still of a red 992 GT3 RS in a Porsche
    showroom (the song's page; no editing style to copy).
  - rec 1.0–14.3: **the template** — @Zs3riyx, caption "Thank you for my 400 hundred subscribe 🎉❤️",
    sound chip "ELA PEIDA FUNK (SLOWED)". Loops at rec 14.30.
* Song: **ELA PEIDA FUNK (Slowed)** — Dj v2be, DJ SMG, XSKAY11 & DJ llz (EP "ELA PEIDA FUNK", Echo8, 2026, baile funk).
* `$WORK/song5.wav` = rec audio [1.221 : 14.1646] (the template's whole audio). **Video time T = song5 time** (beats.py
  on song5: the first 808 hit = drop at 4.336, period 0.51821 s = 115.8 BPM; all 17 kicks within ±16 ms of the grid).
  `ffmpeg -ss 1.221 -to 14.1646 -i rec.mp4 -vn -ac 2 -ar 48000 -c:a pcm_s16le song5.wav`
* Reference intro flashes (template time, from the picture brightness): 0.02, 0.15–0.25, 0.72–0.87, 1.02, 1.22, 1.39,
  1.65, 1.95, 2.17–2.27, 2.40, 2.65–2.72, 3.05, 3.34–3.44, 3.80–3.89, 4.00, 4.17, drop 4.35.

## Mechanism (kept)
1. Calm intro 4.34 s: car 1 (blue GT3 RS) in snow, 3 shots (cuts on the half beats 1.486 / 3.040), white exposure
   flashes on the vocal accents, purple line at the edge of the dark top band. (Our snow = only the cold grade.)
2. Just before the drop the next cars (2 orange P1 cutouts) slide in from the right and park in the snow shot.
3. Drop: heavy zoom blur + flash into real footage; one cut per beat, every shot blurs in (reference: orange embers
   everywhere — off for us, user didn't like the dots).
4. 4 beats per car; on the last beat the NEXT car pops in as a sticker.
5. Beat 8 (8.48): white flash on the silver car. (Reference: the creator's spiky chrome name slams in here, holds 4
   beats, turns black chrome on its last beat (10.30) while a silver sticker pops in — built, but OFF: user wants no
   ID in the middle.) The silver sticker pop on 10.30 stays.
6. End: last kick (12.627) -> our chrome MEHRAB.7w7 end card on dark smoke (the reference faded to black),
   song tail tape-stopped, white flash -> loop (the video starts on a soft flash too).
* Look: dark band over the top ~20 % (`BAND_Y`), cold milky snow grade in the intro (blue paint kept saturated),
  warm contrasty grade after the drop.

## Build (render5.py + shots5.py + logo5.py)
* `logo5.py`: letters = blades along Catmull-Rom centre lines (full width in the stroke, tapering into curled thorn
  tips over the extensions) + barbs, light blur/threshold for liquid joins; chrome = bevel height from the distance
  transform -> normals -> gradient map with sharp dark horizon bands + specular; `dark` -> black chrome; `sweep` = light
  band. Two lines "MEHRAB" / ".7w7" (cap 196 px, slant 0.10) on a 1080x760 canvas, placed at scale 0.93.
* Logo in the frame: dark 9 px stroke + offset drop shadow (readable on bright sky), 12 % scene reflection via normals,
  slam 1.55 -> 1.0 in 0.11 s with zoom blur, punch on every kick, reflections drift, two light sweeps.
* Stickers: GrabCut cutouts in `$WORK/cut/` (`make_cuts.py`; black + silver refined with polygon hints
  `cut_poly.py`), dealer plates on the P1s filled (`PLATES`), contact shadow, slide (intro) or pop with a white
  rim flash.
* Snow: 420 flakes + 26 bokeh flakes (closed-form motion), frost edges. Embers: 120 streaks + 14 bokeh, glow at 1/4 res.
  Both particle layers are OFF in the final (user feedback); the frost edges are part of the grade and stay.
* S02 is slow-mo (0.56x): extracted with `minterpolate` to 120 fps (`INTERP`).
* Clean frames at extraction: `remove_red_sign` (STOP sign on S12 -> wall texture copied from above + pole inpaint,
  `CLEAN`), `blank_plate` (FIRST MOTORS dealer plates on S03/S04 and the P1 licence plate on S05 -> plate-shaped bright
  blob, its letters replaced by the plate's own shading from a normalised blur, `PLATES`).
* Transitions: `zoom_fx` (scale about a point + radial blur), `spin_fx` (rotation + spin blur, zoomed so no corners),
  `apply_trans` reads `TRANS[k] = (kind, out s, in s, centre)` for the cut into shot k; out = ease-in to the cut,
  in = ease-out after it, so the motion peaks exactly on the beat.
* Fast fixes: `splice.py <src> <dst> 182-323 505-640` re-renders frame ranges into an existing render.
* **Fourth feedback: the dark blurred band at the top (reference look, `BAND_Y`) looked like a fault** -> `shots5.BAND = False`.

## The user's CapCut re-edit (the published version)
The user re-edited our 1080p v5 in CapCut (exported 1080p 30 fps, same timing, same audio): intro colour filter (vivid
deep blue), glass-shatter effect on the drop (4.33–5.05), teal light beams on the Turbo S (6.45–7.0), a white flash +
echo/stretch on the Turbo S rear (7.05–7.3), an orange beam with heat-wave warp on the highway shot (7.45–7.9), a prism +
echo on the GT3 reveal (8.4–9.0; it mirrors / duplicates the baked-in ID) and a darker ending with moving shade
(10.2–12.6). No CapCut watermark or ending clip. They asked to remove the top band from *their* video:
`capcut/fix_band.py cc.mp4 v5_1080p.mp4 n5_noaudio_v6.mp4 out.mp4` keeps their frames everywhere and only rebuilds the
band rows (y < 405): intro -> 3D LUT of their filter (`capcut/lut3d.py`, fitted on rows below the band, pooled over the
intro, `lut_intro.npy`) applied to (no-band - band); ending -> local gain field; effects / untouched -> plain delta.
Phase check: their frame k == our 60 fps frame 2k. (v1 re-stamped the ID line white in the dark ending.)
**Then: "the black effect that opens stays too long — put it where the ID comes"** -> `capcut/move_dark.py`: their dark
effect (frames 307–381 = 10.23–12.70 s: ~0.18 black that snaps open into a static diagonal light split, edge through
(840,0)-(0,1500), lit side upper-left) is removed from the GT3 shots (our band-free frames there) and rebuilt
parametrically on the end card: black 0.07 s -> snap open to their diagonal (0.08 s) -> hold half-lit -> full open by
+0.62 s -> loop zoom.

## Clips ($WORK/clips) — user's uploads (6 Oct, Pinterest recordings, pin box (20,96,1060,1936))
| name | content | used |
|---|---|---|
| p02 | 0–15 s SUPERVELOCE blue GT3 RS Miami (notification banner 2.2–5.7 s!); 17–27 Forza clip with buffering spinner (unused); 28–47 Auramind light-blue GT3 RS CGI studio (spinner until 30.4, FIRST MOTORS plate on some shots); **57–73 Tousif Tahsin "Porsche 992" — has a logo at the bottom: EXCLUDED (user)** | S01 9.70, S02 41.93, S03 43.95 |
| p06 | VLCK orange P1 studio (front plate "FIRST MOTORS") | S04 3.20, S06 7.58 (zoom crops the plate), stickers p1a 11.70 / p1b 18.90 |
| q1 | RZVI orange P1, night garage (pause icon until 1.5 s) | S05 6.05, S07 13.05 |
| p07 | MEN'S STYLE black 992 Turbo S on the Miami highway (side mirror in frame -> crop) | S09 16.15, S10 2.35 |
| p08 | Wheels Boutique black Turbo S donuts (people from 5.2 s, a meme clip at 11.4 s) | S08 1.95, S11 1.30 |
| q3 | mrscl black Turbo S still (loop icon bottom right) | sticker blk |
| p10 | XMotors silver 992 GT3 (pause icon until ~0.8 s) | S12–S19, sticker slv 4.90 |
| q4 | luxe_drive matte black GT3 RS — **"LD" logo bottom right: EXCLUDED** (user: no videos with logos) | — |
| p01, p03, p04, p05, p09, q2, q5 | other blue GT3 RS / P1 GTR / Senna / white GT3 RS / Artura / grey GT3 RS clips | unused |
No clip of the blue GT3 RS in snow was found, so the snow is made in the grade (`grade_cold` + `draw_snow`).

## Re-run
```
export WORK=/home/claude/work_edit            # clips/, cut/, logo/, seg5/, song5.wav
python3 logo5.py $WORK/logo/bg.png            # logo5.npz + preview
python3 render5.py extract [S01 ...]          # per-shot frames (60 fps, S02 120 fps interpolated)
python3 render5.py frames 0.5 4.4 8.6 12.9    # stills -> $WORK/check5
python3 render5.py video $WORK/n5_noaudio.mp4 # ~7 min on 2 cores
python3 -c "…pad song5.wav with 1 s silence -> song5_pad.wav"
python3 ../../kit/audio_finish.py $WORK/song5_pad.wav $WORK/n5_audio.wav --start 0 --end 13.664 --tapestop 12.627
bash ../../kit/finish4k.sh $WORK/n5_noaudio.mp4 $WORK/n5_audio.wav $WORK/out_4k.mp4 $WORK/out_1080p.mp4
python3 cover5.py $WORK/cover5.jpg          # P1 right after the drop (T 4.70)
```
