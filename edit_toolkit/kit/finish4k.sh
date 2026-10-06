#!/usr/bin/env bash
# Master delivery (house rule): vertical 4K 2160x3840 for YouTube / Instagram / Facebook / WhatsApp,
# plus a 1080p copy small enough to send in chat (< 30 MiB).
#   bash finish4k.sh video_noaudio.mp4 audio.wav out_4k.mp4 out_1080p.mp4
# The 1080x1920 render is upscaled with lanczos + light unsharp; keep the 4K file < ~95 MB (GitHub limit 100 MB):
# lower -maxrate if needed.
set -e
V="$1"; A="$2"; O4="$3"; O1="$4"
ffmpeg -v error -y -i "$V" -i "$A" -map 0:v -map 1:a \
  -vf "scale=2160:3840:flags=lanczos,unsharp=5:5:0.45:5:5:0" \
  -c:v libx264 -preset medium -crf 16 -maxrate 34M -bufsize 68M -profile:v high -level 5.2 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart "$O4"
ls -la "$O4"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height,r_frame_rate -of default=nw=1 "$O4"
bash "$(dirname "$0")/finish.sh" "$V" "$A" "$O1" 12M
