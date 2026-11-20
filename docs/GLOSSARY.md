# Glossary of file and identifier names

The scripts were written for a Russian-language production, and file names and identifiers are transliterated Russian.
Comments, module headers and docs are in English; this table maps the names you will meet.

## Scripts

| Name | Meaning | What it does |
|---|---|---|
| `rel_ef` | relief | elevation download and reprojection |
| `tekstury`, `tekstury2` | textures | colour, height and mask maps |
| `scena`, `scena_a..e` | scene | Blender scene + render |
| `post` | post | label and glow pass over rendered frames |
| `proverka_putey` | path check | migration paths vs. elevation and ocean |
| `analiz` | analysis | marker speed on screen |
| `dorozhka` | track | narration placement and the audio mix |
| `muzyka`, `muzyka_drama` | music | synthesised piano bed |
| `sobrat`, `sobrat2` | assemble | parallel edit + ffmpeg mux |
| `fon_portreta` | portrait background | optional rembg cut-out on a blurred frame |
| `globus` | globe | clip 02 opening scene |
| `dolina` | valley | Don valley scene (`led` = Ice Age, `leto` = summer, today) |
| `detal` | detail | 8 m detail patch + trees |
| `sputnik` | satellite | Sentinel-2 download and reprojection |
| `sloi`, `proekciya2` | layers, projection | layered "3D photo" from a picture + depth |
| `razrez`, `razrez_dannye` | section, section data | excavation section diorama |
| `zhilishche` | dwelling | mammoth-bone dwelling |
| `kosti`, `pokaz_kostey` | bones, bone showcase | SDF-sculpted bones, preview render |
| `skan_razbor`, `skan_kuski`, `skan_kosti`, `skan_oblegchit` | scan: breakdown, pieces, bones, decimate | the CC0 scan -> individual bones |
| `montazh`, `montazh2` | edit | graphics, captions, dissolves |
| `podpisi_spisok` | caption list | review sheet with reading times |
| `zamedlit`, `zamedlit_S` | slow down | frame interpolation + label point retiming |
| `render-vse2` | render all | clip 02 render queue |
| `ochered` | queue | clip 03 render queue, one shot at a time |
| `obshchee`, `obshchee_a`, `obshchee_b` | common | shared Blender helpers / shared scene data |
| `kamni`, `iskry`, `priroda` | stones, sparks, nature | rocks and cave, spark particles, tree/grass/ground/lightning |
| `sim_koster`, `sim_derevo`, `sim_golovnya`, `sim_trut`, `sim_dymok` | campfire, tree, firebrand, tinder, smoke | Mantaflow bakes |
| `sglazhivanie` | smoothing | blur a baked flame grid |
| `golos_raskladka` | voice layout | cut narration groups into sentences and place them |
| `zvuki` | sounds | ElevenLabs sound effects |
| `proba_*` | test | quick Blender probes |

## Working folders under `work/<clip>/`

`dannye` data · `tex` textures · `kadry` frames · `post` edited frames · `golos` voice · `zvuk` sound effects ·
`shrifty` fonts · `portrety` portraits · `kartinki` pictures · `sloi` layers · `modeli` models · `skan` scan ·
`sim` simulation caches · `proba` previews · `metki*.json` label points per frame.

## Common identifiers

| Name | Meaning |
|---|---|
| `ROOT`, `R` | the clip's working folder |
| `REZHIM` | mode: `vse` all frames, `metki` label points only, or a frame list |
| `PROBA` | preview (half resolution) |
| `DLIT`, `FPS`, `NF` | duration, frame rate, frame count |
| `KAM`, `kluch` | camera keys, set a key |
| `PUTI`, `METKI`, `KART` | paths, markers, cards |
| `EL`, `karta`, `metka`, `strelka`, `NAKLEYKI` | graphics elements: card, pill label, arrow, stickers |
| `START` | narration start times on the clip timeline |
| `postavit(n)` | set the whole scene state for frame n |
| `L(hex)` | sRGB hex -> linear colour |
| `ll(lat, lon)` | latitude/longitude -> point on the unit sphere |
| `sgl`, `smt`, `okno` | smoothstep, smootherstep, show/hide window |
