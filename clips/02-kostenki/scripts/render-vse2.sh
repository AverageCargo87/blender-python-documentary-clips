#!/usr/bin/env bash
# Clip 2, v4: render all scenes with the final durations, one after another.   bash render-vse2.sh <root> [scenes...]
R="$1"; shift; SC="${@:-A B E C D1 D2 S H}"; BL="${BLENDER:-blender}"; PY="${PYTHON:-python}"; HERE="$(cd "$(dirname "$0")" && pwd)"
P="${PROBA:-}"   # PROBA=--proba renders half-size previews into <root>/proba/
for S in $SC; do
  case $S in
    A) "$BL" -b --factory-startup --python "$HERE/globus.py" -- "$R" vse $P > "$R/render-A.log" 2>&1 ;;
    B) "$BL" -b --factory-startup --python "$HERE/dolina.py" -- "$R" led vse $P > "$R/render-B.log" 2>&1 ;;
    E) "$BL" -b --factory-startup --python "$HERE/dolina.py" -- "$R" leto vse $P > "$R/render-E.log" 2>&1 ;;
    C|D1|D2) "$PY" "$HERE/sloi.py" "$R" $S > /dev/null; "$BL" -b --factory-startup --python "$HERE/proekciya2.py" -- "$R" $S vse $P > "$R/render-$S.log" 2>&1 ;;
    S) "$BL" -b --factory-startup --python "$HERE/razrez.py" -- "$R" vse $P > "$R/render-S.log" 2>&1 ;;
    H) "$BL" -b --factory-startup --python "$HERE/zhilishche.py" -- "$R" vse $P > "$R/render-H.log" 2>&1 ;;
  esac
  echo "$S $(ls "$R/kadry/$S" 2>/dev/null | wc -l) frames, errors: $(grep -ci traceback "$R/render-$S.log")"
done
