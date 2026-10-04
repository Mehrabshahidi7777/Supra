#!/usr/bin/env bash
# Mux the rendered (silent) video with the finished audio and encode for upload.
#   bash finish.sh video_noaudio.mp4 audio.wav out.mp4 [maxrate]
# Default maxrate 12M keeps an ~18 s Short under the 30 MiB chat-file limit.
# If the file is still > 30 MiB, re-run with 10M.
set -e
V="$1"; A="$2"; O="$3"; MR="${4:-12M}"
ffmpeg -v error -y -i "$V" -i "$A" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 19 -maxrate "$MR" -bufsize 24M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$O"
ls -la "$O"
ffprobe -v error -show_entries format=duration,bit_rate:stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$O"
ffmpeg -hide_banner -nostats -i "$O" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | head -2
