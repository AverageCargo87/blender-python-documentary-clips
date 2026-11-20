#!/usr/bin/env bash
# Clip 3 'Fire': edit in 4 parallel workers -> MP4 (full and light).   bash sobrat.sh <root>
set -e
R="$1"; HERE="$(cd "$(dirname "$0")" && pwd)"; PY="${PYTHON:-python}"; cd "$R"; mkdir -p post; rm -f post/*.jpg
N=$(PYTHONIOENCODING=utf-8 "$PY" "$HERE/montazh.py" "$R" plan | tail -1 | sed 's/.* \([0-9]*\) frames.*/\1/'); q=$((N/4))
"$PY" "$HERE/montazh.py" "$R" 1-$q > /dev/null & "$PY" "$HERE/montazh.py" "$R" $((q+1))-$((2*q)) > /dev/null & "$PY" "$HERE/montazh.py" "$R" $((2*q+1))-$((3*q)) > /dev/null & "$PY" "$HERE/montazh.py" "$R" $((3*q+1))-$N > /dev/null & wait
echo "edited frames: $(ls post | wc -l) of $N"
PYTHONIOENCODING=utf-8 "$PY" "$HERE/dorozhka.py" "$R" | tail -2
ffmpeg -y -loglevel error -framerate 24 -i post/%04d.jpg -i zvuk-itog.wav -c:v libx264 -preset slow -crf 17 -maxrate 16M -bufsize 32M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart ogon.mp4
ffmpeg -y -loglevel error -framerate 24 -i post/%04d.jpg -i zvuk-itog.wav -c:v libx264 -preset slow -crf 21 -maxrate 5500k -bufsize 11M -pix_fmt yuv420p -c:a aac -b:a 128k -shortest -movflags +faststart ogon-legkiy.mp4
ls -la ogon.mp4 ogon-legkiy.mp4
