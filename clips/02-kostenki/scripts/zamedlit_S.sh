#!/usr/bin/env bash
# Section scene: rendered at 15 s (kadry/S15, 450 frames) -> 23 s in the clip (kadry/S, 690 frames) by smooth slow-down:
# in-between frames are synthesised from motion (ffmpeg minterpolate, motion-compensated).   bash zamedlit_S.sh <root>
R="$1"; mkdir -p "$R/kadry/S"
ffmpeg -y -loglevel error -framerate 30 -i "$R/kadry/S15/%04d.png" -vf "minterpolate=fps=46:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -start_number 1 "$R/kadry/S/%04d.png"
echo "S $(ls "$R/kadry/S" | wc -l) frames"
