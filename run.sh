#!/usr/bin/env bash
# One entry point for the whole pipeline: data -> scene -> render -> post -> captions -> mux.
#
#   ./run.sh <clip> <stage> [--preview]
#
#   clip:   01 (Out of Africa) | 02 (Kostenki) | 03 (Fire)
#   stage:  see `./run.sh help`; `all` runs every stage of a clip in order
#   --preview  half-resolution Blender renders (--proba in the scene scripts), fewer samples, coarser meshes,
#              and for clip 01 a low-zoom elevation download; the edit/post steps upscale frames to 1080p.
#
# Environment: BLENDER (path to blender 5.2 executable, default `blender`), PYTHON (default `python`),
#              WORK (working root, default ./work), ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID for narration (see .env.example).
#              Without the key, clips 01 and 02 get a music-only track so `all` still ends with an MP4; clip 03 needs it.
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$REPO/.env" ]; then set -a; . "$REPO/.env"; set +a; fi   # optional local config (see .env.example)
CLIP="${1:-help}"; STAGE="${2:-help}"; PREVIEW=""; [[ " $* " == *" --preview "* ]] && PREVIEW="--proba"
BLENDER="${BLENDER:-blender}"; PY="${PYTHON:-python}"; WORK="${WORK:-$REPO/work}"
export BLENDER PYTHON="$PY" PROBA="$PREVIEW"
bl() { "$BLENDER" -b --factory-startup --python "$@"; }
have_voice() { [ -n "${ELEVENLABS_API_KEY:-${ELEVENLABS_TTS_API_KEY:-}}" ]; }
music_only() {   # music_only <bed.wav> <root>: without ElevenLabs keys the music bed becomes the final track, so `edit` can still mux
  echo "warning: ELEVENLABS_API_KEY is not set: no narration, $2/zvuk-itog.wav is the music bed only (see .env.example)" >&2
  ffmpeg -y -loglevel error -i "$1" -af "loudnorm=I=-20:TP=-1.5:LRA=11" -ar 48000 -ac 2 "$2/zvuk-itog.wav"
}

usage() {
  cat <<'EOF'
clip 01  Out of Africa (globe)
  fetch     elevation tiles (AWS Terrarium z5, or z3 with --preview) + Natural Earth lakes
  textures  colour/height/ocean textures 8192x4096 (tekstury.py)
  check     pre-render path check over land and altitude (proverka_putey.py)
  smoke     3 frames headless (+ marker positions) and the label pass on them -> work/01-out-of-africa/post/
  render    all 2070 frames (scena.py) ; analyse marker speeds (analiz.py)
  voice     music (lib/muzyka.py) ; narration via ElevenLabs + mix (dorozhka.py); without keys: music-only track
  edit      labels, cards, captions and mux to MP4 (sobrat.sh)
clip 02  Kostenki (valley, section, dwelling)
  fetch     Don relief (Terrarium z12), Sentinel-2 L2A true colour + scene classes (sputnik.py)
  textures  valley colour maps (tekstury2.py), detail patch + Ice Age trees (detal.py), section data, SDF bones
  scan      CC0 mammoth scan -> individual bones (needs SI_MAMMOTH_URL or a local zip, see fetch_mammoth_scan.py)
  render    scenes A B E S H (+ C D1 D2 if the layered pictures exist) (render-vse2.sh)
  slow      slow down finished frames of S, H, D2 (captions get more time, no re-render)
  voice     music ; narration + mix; without keys: music-only track
  edit      graphics, captions and mux (sobrat2.sh)
clip 03  Fire
  sim       bake the Mantaflow fires (campfire, tree, firebrand, tinder, smoke)
  render    all 9 shots, one at a time (ochered.sh)
  voice     narration (groups cut into sentences) + sound effects ; timeline (golos_raskladka.py); needs keys
  edit      edit + sound track + mux (sobrat.sh)
EOF
}

c1() {
  local R="$WORK/01-out-of-africa" S="$REPO/clips/01-out-of-africa/scripts"
  mkdir -p "$R/dannye" "$R/tex" "$R/shrifty" "$R/portrety/gotovye"
  cp -n "$REPO"/assets/fonts/*.ttf "$R/shrifty/" 2>/dev/null || true
  cp -n "$REPO"/clips/01-out-of-africa/data/portraits/*.jpg "$R/portrety/gotovye/" 2>/dev/null || true
  case "$1" in
    fetch)    TERRARIUM_ZOOM=$([ -n "$PREVIEW" ] && echo 3 || echo 5) "$PY" "$S/rel_ef.py" "$R/dannye"; "$PY" "$S/fetch_lakes.py" "$R" ;;
    textures) "$PY" "$S/tekstury.py" "$R" ;;
    check)    "$PY" "$S/proverka_putey.py" "$R" "$REPO/clips/01-out-of-africa/data/puti.json" ;;
    smoke)    bl "$S/scena.py" -- "$R" 200,1000,1800 --proba; "$PY" "$S/post.py" "$R" 200,1000,1800 ;;
    render)   bl "$S/scena.py" -- "$R" vse $PREVIEW; "$PY" "$S/analiz.py" "$R" | head -8 ;;
    voice)    "$PY" "$REPO/lib/muzyka.py" "$R/muz-B.wav" B 69.0
              if have_voice; then node "$REPO/lib/narration.mjs" "$REPO/clips/01-out-of-africa/data/narration.json" "$R"; "$PY" "$S/dorozhka.py" "$R"
              else music_only "$R/muz-B.wav" "$R"; fi ;;
    edit)     bash "$S/sobrat.sh" "$R" ;;
    all)      for s in fetch textures check render voice edit; do c1 $s; done ;;
    *)        usage; exit 2 ;;
  esac
}

c2() {
  local R="$WORK/02-kostenki" S="$REPO/clips/02-kostenki/scripts"
  mkdir -p "$R/dannye" "$R/tex" "$R/shrifty" "$R/modeli" "$R/kadry"
  cp -n "$REPO"/assets/fonts/*.ttf "$R/shrifty/" 2>/dev/null || true
  cp -n "$REPO"/clips/02-kostenki/data/tochki.json "$R/dannye/" 2>/dev/null || true
  export GLOBE_TEX="$WORK/01-out-of-africa/tex"       # scene A reuses the globe textures of clip 01
  case "$1" in
    fetch)    "$PY" "$S/fetch_don_relief.py" "$R"; "$PY" "$S/sputnik.py" "$R" 2025-08-30 4 visual; "$PY" "$S/sputnik.py" "$R" 2025-08-30 4 scl ;;
    textures) "$PY" "$S/tekstury2.py" "$R"; "$PY" "$S/detal.py" "$R" led; "$PY" "$S/detal.py" "$R" leto
              "$PY" "$S/razrez_dannye.py" "$R"; "$PY" "$S/kosti.py" "$R" ;;
    scan)     "$PY" "$S/fetch_mammoth_scan.py" "$R" "${SI_MAMMOTH_URL:-}"; "$PY" -I "$S/skan_razbor.py" "$R"; "$PY" -I "$S/skan_kosti.py" "$R"
              bl "$S/skan_oblegchit.py" -- "$R" "$R/_skan-kosti.png" ;;
    render)   local sc="A B E S H"; [ -d "$R/kartinki" ] && sc="$sc C D1 D2"
              bash "$S/render-vse2.sh" "$R" $sc ;;
    slow)     # finished frames are slowed instead of re-rendered (captions get more time)
              # S: rendered 15 s -> 23 s; H: frames 331-480 x1.8 (16 -> 20 s); D2: all 420 frames x1.2 (14 -> 16.8 s)
              # (zamedlit.py does what zamedlit_S.sh did for S, and also stretches the label points)
              "$PY" "$S/zamedlit.py" "$R" S 1 450 1.533333; "$PY" "$S/zamedlit.py" "$R" H 331 480 1.8; "$PY" "$S/zamedlit.py" "$R" D2 1 420 1.2 ;;
    voice)    "$PY" "$REPO/lib/muzyka.py" "$R/muz-B4.wav" B 116.2
              if have_voice; then node "$REPO/lib/narration.mjs" "$REPO/clips/02-kostenki/data/narration.json" "$R"; "$PY" "$S/dorozhka.py" "$R"
              else music_only "$R/muz-B4.wav" "$R"; fi ;;
    edit)     bash "$S/sobrat2.sh" "$R" ;;
    all)      for s in fetch textures scan render slow voice edit; do c2 $s; done ;;
    *)        usage; exit 2 ;;
  esac
}

c3() {
  local R="$WORK/03-fire" S="$REPO/clips/03-fire/scripts"
  mkdir -p "$R/shrifty" "$R/sim" "$R/kadry" "$R/proba"
  cp -n "$REPO"/assets/fonts/*.ttf "$R/shrifty/" 2>/dev/null || true
  local res=$([ -n "$PREVIEW" ] && echo 64 || echo 128)
  case "$1" in
    sim)      bl "$S/sim_koster.py" -- "$R" koster $res 168
              bl "$S/sim_derevo.py" -- "$R" derevo; bl "$S/sim_golovnya.py" -- "$R"; bl "$S/sim_trut.py" -- "$R"; bl "$S/sim_dymok.py" -- "$R" ;;
              # optional: sglazhivanie.py smooths the flame grid of the tree cache into a second cache
    render)   bash "$S/ochered.sh" "$R" ;;
    voice)    have_voice || { echo "clip 03 voice needs ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID: narration and the 10 sound effects come from ElevenLabs (see .env.example)" >&2; exit 1; }
              node "$REPO/lib/narration.mjs" "$REPO/clips/03-fire/data/narration.json" "$R"; node "$S/zvuki.mjs" "$R"
              "$PY" "$S/golos_raskladka.py" "$R" ;;
    edit)     bash "$S/sobrat.sh" "$R" ;;
    all)      for s in sim render voice edit; do c3 $s; done ;;
    *)        usage; exit 2 ;;
  esac
}

case "$CLIP" in
  01|1|01-out-of-africa) c1 "$STAGE" ;;
  02|2|02-kostenki)      c2 "$STAGE" ;;
  03|3|03-fire)          c3 "$STAGE" ;;
  *) usage ;;
esac
