# Background for a portrait without regenerating it: cut the figure out (rembg) and place it on a blurred dark frame of the lesson.
#   python fon_portreta.py <portrait.png> <background-frame> <out.png> [shift_x 0..1]
import sys, numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from rembg import remove, new_session
src, fon, out = sys.argv[1], sys.argv[2], sys.argv[3]
sx = float(sys.argv[4]) if len(sys.argv) > 4 else .5
p = Image.open(src).convert('RGB'); S = p.size[0]
cut = remove(p, session=new_session('isnet-general-use'))           # RGBA
a = cut.split()[-1].filter(ImageFilter.GaussianBlur(1.2))           # soft edge for hair and fur
f = Image.open(fon).convert('RGB'); W, H = f.size
s = H; x0 = int((W - s) * sx); f = f.crop((x0, 0, x0 + s, s)).resize((S, S), Image.LANCZOS)
f = f.filter(ImageFilter.GaussianBlur(S / 90))                      # depth of field
f = ImageEnhance.Brightness(f).enhance(.55); f = ImageEnhance.Color(f).enhance(.8)
# vignette matching the other portraits
y, x = np.mgrid[0:S, 0:S].astype(np.float32) / S - .5; v = 1 - .55 * np.clip(np.sqrt(x * x + y * y) * 1.6 - .25, 0, 1)
f = Image.fromarray((np.asarray(f).astype(np.float32) * v[..., None]).astype(np.uint8))
f.paste(p, (0, 0), a); f.save(out); print('ok', out)
