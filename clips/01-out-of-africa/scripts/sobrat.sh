#!/usr/bin/env bash
# Clip 1: labels and glow in 4 parallel workers -> MP4 with sound.   bash sobrat.sh <root>
set -e
R="$1"; HERE="$(cd "$(dirname "$0")" && pwd)"; PY="${PYTHON:-python}"; cd "$R"
"$PY" "$HERE/post.py" "$R" 1-518 &
"$PY" "$HERE/post.py" "$R" 519-1035 &
"$PY" "$HERE/post.py" "$R" 1036-1553 &
"$PY" "$HERE/post.py" "$R" 1554-2070 &
wait
ls post | wc -l
ffmpeg -y -loglevel error -framerate 30 -i post/%04d.jpg -i zvuk-itog.wav -c:v libx264 -preset slow -crf 20 -maxrate 12M -bufsize 24M \
  -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart iz-afriki-po-vsemu-miru.mp4
# light copy for the web lesson (crf 23, ~20 MB)
ffmpeg -y -loglevel error -i iz-afriki-po-vsemu-miru.mp4 -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -c:a copy -movflags +faststart \
  iz-afriki-po-vsemu-miru-legkiy.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 iz-afriki-po-vsemu-miru.mp4
