"""Build docs/media/smoke-vs-production.jpg: the `make smoke` frames next to the same frames of the released clip 01.

    python tools/smoke_compare.py [--smoke DIR] [--clip MP4] [--out JPG] [--date YYYY-MM-DD]

Top row: the label pass output of `make smoke` (work/01-out-of-africa/post/0200.jpg, 1000.jpg, 1800.jpg).
Bottom row: frames 200, 1000 and 1800 of release-assets/01-out-of-africa.mp4 (frame n is video frame n-1).
Each row gets a burned-in caption so the picture explains itself. Needs Pillow and ffmpeg; no metadata is written.
"""
import argparse
import datetime as dt
import io
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = (200, 1000, 1800)
TILE = (640, 360)
GAP = 4
BAND = 34
BG = (0, 0, 0)
FG = (236, 226, 204)
ACCENT = (226, 150, 82)


def production_frame(clip, n):
    """Frame n (1-based, as rendered) of the released clip, decoded with ffmpeg."""
    png = subprocess.run(['ffmpeg', '-v', 'error', '-i', clip, '-vf', f'select=eq(n\\,{n - 1})', '-frames:v', '1',
                          '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGB')


def row(images, caption, font):
    w = len(images) * TILE[0] + (len(images) - 1) * GAP
    out = Image.new('RGB', (w, BAND + TILE[1]), BG)
    d = ImageDraw.Draw(out)
    d.rectangle((14, 11, 17, BAND - 11), fill=ACCENT)
    d.text((26, BAND // 2), caption, font=font, fill=FG, anchor='lm')
    for i, im in enumerate(images):
        out.paste(im.resize(TILE, Image.LANCZOS), (i * (TILE[0] + GAP), BAND))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--smoke', default=os.path.join(REPO, 'work', '01-out-of-africa', 'post'))
    ap.add_argument('--clip', default=os.path.join(REPO, 'release-assets', '01-out-of-africa.mp4'))
    ap.add_argument('--out', default=os.path.join(REPO, 'docs', 'media', 'smoke-vs-production.jpg'))
    ap.add_argument('--date', help='date of the smoke run (default: modification date of its frames)')
    a = ap.parse_args()

    smoke_files = [os.path.join(a.smoke, f'{n:04d}.jpg') for n in FRAMES]
    date = a.date or dt.date.fromtimestamp(os.path.getmtime(smoke_files[0])).isoformat()
    font = ImageFont.truetype(os.path.join(REPO, 'assets', 'fonts', 'Oswald.ttf'), 17)
    frames = ', '.join(str(n) for n in FRAMES)
    top = row([Image.open(f).convert('RGB') for f in smoke_files], f'SMOKE RUN, THIS REPO, {date}  ·  make smoke, frames {frames}', font)
    bottom = row([production_frame(a.clip, n) for n in FRAMES], 'PRODUCTION RENDER  ·  released clip 01, same frames', font)
    sheet = Image.new('RGB', (top.width, top.height + GAP + bottom.height), BG)
    sheet.paste(top, (0, 0))
    sheet.paste(bottom, (0, top.height + GAP))
    sheet.save(a.out, quality=88, optimize=True)
    print('wrote', a.out, sheet.size)


if __name__ == '__main__':
    main()
