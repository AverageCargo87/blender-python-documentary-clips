#!/usr/bin/env bash
# Clip 3 'Fire': final render of all shots STRICTLY ONE AT A TIME (house rule: only one render in parallel),
# at lowered priority so the computer stays usable. Finished frames are skipped, so the queue can be restarted.
#   bash ochered.sh <root> [shots...]        default: E B2 B1 A1 A2 C D1a D1b D2
R="$1"; shift; PL="${@:-E B2 B1 A1 A2 C D1a D1b D2}"; BL="${BLENDER:-blender}"; HERE="$(cd "$(dirname "$0")" && pwd)"
P="${PROBA:-}"   # PROBA=--proba renders half-size previews into kadry/<shot>-proba
cd "$R"; mkdir -p proba
odin() {   # shot name, script, arguments...
  local imya=$1; shift
  "$BL" -b --factory-startup --python "$@" > "proba/render-$imya.log" 2>&1 &
  sleep 8
  command -v powershell > /dev/null && powershell -NoProfile -Command "Get-Process blender -ErrorAction SilentlyContinue | ForEach-Object { \$_.PriorityClass = 'BelowNormal' }" > /dev/null 2>&1
  wait
  echo "$(date +%H:%M) $imya: $(ls kadry/$imya 2>/dev/null | wc -l) frames, errors $(grep -ci traceback proba/render-$imya.log)"
}
for P in $PL; do
  case $P in
    E)   odin E "$HERE/scena_e.py" -- "$R" vse $P ;;
    B1|B2) OG_VSAMP=160 odin $P "$HERE/scena_b.py" -- "$R" $P vse $P ;;
    A1|A2) OG_VSAMP=128 OG_VEND=160 odin $P "$HERE/scena_a.py" -- "$R" $P vse $P ;;
    C)   odin C "$HERE/scena_c.py" -- "$R" vse $P ;;
    D1a|D1b|D2) odin $P "$HERE/scena_d.py" -- "$R" $P vse $P ;;
  esac
done
echo "queue finished $(date +%H:%M)"
