#!/usr/bin/env bash
# Rebuild everything in docs/media from the finished clips in release-assets/ (see docs/RELEASE_ASSETS.md).
#   bash tools/make_media.sh            (needs ffmpeg 6+; metadata is stripped from every output)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; A="$REPO/release-assets"; M="$REPO/docs/media"; mkdir -p "$M/previews"
C1="$A/01-out-of-africa.mp4"; C2="$A/02-kostenki.mp4"; C3="$A/03-fire.mp4"
gif() {   # gif <in> <start> <dur> <width> <fps> <out>
  ffmpeg -v error -y -ss "$2" -t "$3" -i "$1" -vf "fps=$5,scale=$4:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" \
    -map_metadata -1 -loop 0 "$6"
}
preview() {   # preview <in> <start> <dur> <out>: 720p H.264, soft audio fades, no metadata
  ffmpeg -v error -y -ss "$2" -t "$3" -i "$1" -vf "scale=1280:-2:flags=lanczos,fade=in:st=0:d=0.5,fade=out:st=$(awk "BEGIN{print $3 - .6}"):d=0.6" \
    -af "afade=in:st=0:d=0.5,afade=out:st=$(awk "BEGIN{print $3 - .8}"):d=0.8" -c:v libx264 -preset slow -crf 27 -pix_fmt yuv420p -c:a aac -b:a 96k \
    -map_metadata -1 -movflags +faststart "$4"
}
sheet() {     # sheet <in> <every s> <cols>x<rows> <out>
  ffmpeg -v error -y -i "$1" -vf "fps=1/$2,scale=480:-2,tile=$3:padding=4:color=black" -frames:v 1 -map_metadata -1 -fflags +bitexact -flags:v +bitexact -q:v 3 "$4"
}
gif "$C1" 25.5 11.5 600 10 "$M/hero-globe.gif"                # paths of Homo erectus to Java and China, species cards
gif "$C2" 56.5 7.0 480 10 "$M/dwelling-from-scan.gif"          # the bone ring assembles from the CC0 scan bones
preview "$C1" 44.0 25.0 "$M/previews/01-out-of-africa-preview.mp4"
preview "$C2" 11.0 30.0 "$M/previews/02-kostenki-preview.mp4"
preview "$C3" 3.0 25.0 "$M/previews/03-fire-preview.mp4"
sheet "$C1" 5.75 4x3 "$M/contact-01-out-of-africa.jpg"
sheet "$C2" 7.3 4x4 "$M/contact-02-kostenki.jpg"
sheet "$C3" 5.9 4x3 "$M/contact-03-fire.jpg"
# optional contrast: a few silent seconds of a separate toon-3D clip made with Higgsfield (pass its path as TOON=...)
if [ -n "${TOON:-}" ]; then gif "$TOON" 8.75 3.2 270 12 "$M/toon3d-higgsfield.gif"; fi
# smoke run vs. production, labelled rows; only after `make smoke` has written work/01-out-of-africa/post (needs Pillow)
if [ -f "$REPO/work/01-out-of-africa/post/0200.jpg" ]; then "${PYTHON:-python}" "$REPO/tools/smoke_compare.py"; fi
ls -la "$M" "$M/previews"
