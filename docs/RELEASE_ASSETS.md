# Release assets

The finished clips are larger than what belongs in git, so they live in `release-assets/` (ignored by git) and are meant
to be attached to a GitHub release. Short previews (720p, under 8 MB each), GIFs and contact sheets made from them are
tracked in `docs/media/`, and `tools/make_media.sh` rebuilds all of them from these files (the smoke comparison also needs
the output of `make smoke`).

| File | Clip | Length | Video | Size | SHA-256 |
|---|---|---|---|---|---|
| `01-out-of-africa.mp4` | Out of Africa (globe) | 69.0 s | 1920x1080, 30 fps, 2070 frames, H.264 + AAC | 19,985,274 B | `a3e9ea04efbdf50050cc90aeb074ea758c052a6c15522b4bafc93c2c0e508c2c` |
| `02-kostenki.mp4` | Kostenki: mammoth hunters | 116.2 s | 1920x1080, 30 fps, 3486 frames, H.264 + AAC | 28,118,068 B | `4692236fc943fcfdf1f8b156c26c3ca9b3a6f4178eda2b1791f373e291f5f74c` |
| `03-fire.mp4` | Fire | 70.8 s | 1920x1080, 24 fps, 1699 frames, H.264 + AAC | 26,023,188 B | `5b5bc51942df1ae32ad53766a51027b25b843e0b53adaa6e7e403290736974f9` |

Clips 01 and 02 are the exact files the lesson player streams; clip 03 is the web version prepared for its lesson (clip 01: x264 crf 23; clip 02: two-pass x264 at 1850 kbit/s;
clip 03: crf 23 at ~3 Mbit/s). They were remuxed without container metadata (`ffmpeg -map 0 -c copy -map_metadata -1`).
Durations, frame counts and sizes above were measured with ffprobe on 2026-11-20 in this repo.

Narration and captions are in Russian; the English translation of every narrated line is in `clips/*/data/narration.en.md`.

## Upload (when the repository is published)

```bash
gh release create v1.0 release-assets/01-out-of-africa.mp4 release-assets/02-kostenki.mp4 release-assets/03-fire.mp4 \
  --title "Rendered clips" --notes-file docs/RELEASE_ASSETS.md
```

## Credits that travel with the files

- Clip 02 contains modified Copernicus Sentinel data 2025 (the credit is also burned into the last scene).
- Clip 02 uses bones from the Smithsonian NMNH woolly mammoth scan (CC0).
- Elevation: Mapzen Terrain Tiles on AWS (Terrarium); lakes: Natural Earth (public domain).
- Voice: ElevenLabs. Clip 01 portraits, clip 02 layered pictures (camp, finds, figurine) and clip 03 sky, hyena and figure
  cards: AI-generated with Higgsfield.
- Fonts: Oswald and Cormorant Garamond (SIL OFL 1.1).
