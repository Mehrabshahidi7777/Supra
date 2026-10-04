# Night 3 — Smash or Pass? 5 Dream Cars (engine + shot list)

Final: `Night3_SmashOrPass_DreamCars/Night3_SmashOrPass_DreamCars_1080p.mp4` (1080x1920, 30 fps, 18.07 s, -14 LUFS, tape-stop ending).

## Reference
YouTube Short by FXNGVXK (song chip: "BREGA DO SCUBA", caption "MONTAGEM G…"), square video inside the Shorts UI.
Analysis: vocal-only intro 0.4–5.6 s, drop at 5.568 s, tempo 163 BPM (beat 0.3682 s), every cut on even beats
(2 beats = 0.736 s), intro cuts every 4 beats on the same grid. Car colour story green → pink → black/yellow → red → red,
3–4 shots per car (front, detail, rear, side/moving). Car-to-car transition = cutout of the next car with a glowing
outline in its colour growing out of the current shot. Whip/zoom blur between shots of the same car. Punchy grade,
lens edge blur, RGB fringe. Outro: white flash → channel name in white glow, font changes every 2 frames → warped fade.
Recording A/V offset ≈ +0.1 s (visual cuts late) — always cut on the audio grid.

## Our build
* Song from the reference recording, trimmed 1.12 → 19.1914 s (vocal entry on grid beat 1.150; end = 3 beats after the
  outro start, so the loop seam stays in time). Outro starts 18.0868 s (tape-stop from there).
* Hook: red 3D "SMASH OR PASS?" (kit/lib.py plate) over the strongest shot from frame 0 until the 3rd cut.
* Feedback (v3): the user noticed car #1 was never shown properly from the front and asked for its first shot to be
  head-on — fixed (G1 now the GT R head-on; old rear-wing opener moved to G4, V8 badge shot dropped).
  Lesson: give every car a clear front shot, ideally its first one.
* Numbers 1–5 + model name top-left in each car's colour → comments ("which number do you smash?").
* Pops: GrabCut cutouts (kit/cutout.py) of pink x1@9.85, BMW x3@4.6, orange p06@15.3, red p09@32.3.

## Clip files ($WORK/clips) → user's uploads
| name | upload (recording time) | content | used |
|---|---|---|---|
| p01 | …_002013_Pinterest | AMG GT Black Series at dealership (Yavuz Cevik) | G3 (front 3/4 approach, 18.90) |
| p02 | …_002149_Pinterest | AMG GT R green, forest (Luxlife; Carola Daimler Cars) | G1 (head-on front, 32.70) G2 G4 G5 |
| p03 | …_002456_Pinterest | BMW M4 CSL fog lot + drift (XMotors) | B2 B3 B4 |
| p04 | …_002618_Pinterest | BMW convoy at dusk, dark garage | – |
| p05 | …_002805_Pinterest | McLaren 720S orange | – |
| p06 | …_002920_Pinterest | McLaren P1 dark studio (Classy Motivation) | O1 O4 |
| p07 | …_002954_Pinterest | McLaren 765LT (notification banner 10–11.6 s!) | – |
| p08 | …_003025_Pinterest | McLaren 750S Spider bamboo road (SUPERVELOCE) | O2 O3 |
| p09 | …_003207_Pinterest | Lamborghini SVJ / Revuelto / Temerario (EBull) | R1–R4 |
| x1 | 6a60fce4 | pink Ferrari 488, white garage (Artseur) | P1–P3 |
| x2 | ced591d3 | magenta Ferrari SF90 studio, 4:5 pin (Jordan Centano) | P4 |
| x3 | 1e3fc9c3 | BMW M4 CSL forest, golden hour (SUPERVELOCE) | B1 |

Shot in-points, zoom and crop centre are in `shots.py` (refined with `kit/clips.py cuts` so no shot crosses a source cut).

## Re-run
```
export WORK=/home/claude/work_edit      # clips/, seg/, cut/, check/
python3 ../../kit/clips.py extract .     # per-shot frames
WORK=$WORK python3 render3.py frames 1.12 6.15 18.4   # stills to $WORK/check
WORK=$WORK python3 render3.py video $WORK/n3_noaudio.mp4
python3 ../../kit/audio_finish.py $WORK/ref.wav $WORK/n3_audio.wav --start 1.12 --end 19.1914 --tapestop 18.0868
bash ../../kit/finish.sh $WORK/n3_noaudio.mp4 $WORK/n3_audio.wav $WORK/out.mp4
```
Render speed ≈ 0.5 s/frame with 2 workers (542 frames ≈ 4.5 min).
