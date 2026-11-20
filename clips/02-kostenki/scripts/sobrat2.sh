#!/usr/bin/env bash
# Clip 2: edit v2 (montazh2.py) in 4 parallel workers -> MP4 (full, light, and the two-pass web version).   bash sobrat2.sh <root>
set -e
R="$1"; HERE="$(cd "$(dirname "$0")" && pwd)"; PY="${PYTHON:-python}"; cd "$R"; mkdir -p post; rm -f post/*.jpg
N=$("$PY" -c "d=[11.6,11,23,11,20,12,16.8,15]; print(int(round((sum(d)-.6*(len(d)-1))*30)))"); q=$((N/4))
"$PY" "$HERE/montazh2.py" "$R" 1-$q & "$PY" "$HERE/montazh2.py" "$R" $((q+1))-$((2*q)) & "$PY" "$HERE/montazh2.py" "$R" $((2*q+1))-$((3*q)) & "$PY" "$HERE/montazh2.py" "$R" $((3*q+1))-$N & wait
ls post | wc -l
A=zvuk-itog.wav; [ -f "$A" ] || A=zvuk.wav      # narrated mix if it exists, otherwise music only
ffmpeg -y -loglevel error -framerate 30 -i post/%04d.jpg -i "$A" -c:v libx264 -preset slow -crf 18 -maxrate 14M -bufsize 28M -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart kostenki.mp4
ffmpeg -y -loglevel error -framerate 30 -i post/%04d.jpg -i "$A" -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -c:a aac -b:a 128k -shortest -movflags +faststart kostenki-legkiy.mp4
# web version: two-pass x264 at 1850 kbit/s (~25-28 MB for 1:56)
ffmpeg -y -loglevel error -i kostenki.mp4 -c:v libx264 -preset slow -b:v 1850k -pass 1 -an -f mp4 -passlogfile x264pass /dev/null
ffmpeg -y -loglevel error -i kostenki.mp4 -c:v libx264 -preset slow -b:v 1850k -pass 2 -passlogfile x264pass -c:a aac -b:a 128k -movflags +faststart kostenki-sayt.mp4
ls -la kostenki.mp4 kostenki-legkiy.mp4 kostenki-sayt.mp4
