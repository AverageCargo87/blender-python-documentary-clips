# Clip 1 post pass: glow, marker cards, captions over the Blender frames -> post/NNNN.jpg.   python post.py <root> [frames: 1-1800 | 61,346]
import sys, json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = sys.argv[1]; ARG = sys.argv[2] if len(sys.argv) > 2 else '1-2070'
DLIT = 69.0
FPS, W, H = 30, 1920, 1080
M = json.load(open(f'{ROOT}/metki.json'))['kadry']
POST = os.environ.get('POST', 'post'); os.makedirs(f'{ROOT}/{POST}', exist_ok=True)
SH = f'{ROOT}/shrifty'
def osw(sz, wt=600):
    f = ImageFont.truetype(f'{SH}/Oswald.ttf', sz); f.set_variation_by_axes([wt]); return f
def cor(sz, wt=600):
    f = ImageFont.truetype(f'{SH}/CormorantGaramond-Italic.ttf', sz); f.set_variation_by_axes([wt]); return f
F = dict(kt=osw(32, 600), ks=osw(24, 400), mt=osw(27, 600), ms=osw(21, 400), rt=osw(18, 500), tit=cor(112), eyb=osw(28, 500), lt=osw(40, 600), ls=osw(32, 400), afr=cor(92), cap=cor(64), leg=osw(30, 500))
KREM, ZOL = (244, 234, 214), (233, 183, 101)
# colours picked with an eyedropper from finished frames (ring, H. erectus path, H. sapiens path)
TERR = (255, 122, 72)
C_ER, C_SAP = (192, 96, 42), (255, 226, 140)
C_ER_TUSK = (187, 135, 87)   # dimmed H. erectus path over land (measured on a frame)
cl = lambda x, a=0., b=1.: max(a, min(b, x))
sgl = lambda u: u * u * (3 - 2 * u)
def okno(t, a, b, f=.6): return sgl(cl((t - a) / f)) * sgl(cl((b - t) / f))
def shirina(s, font, ls=0): return sum(font.getlength(c) for c in s) + ls * (len(s) - 1)
def razryad(d, xy, s, font, fill, ls=0, anchor='ls'):
    # letter-spaced text (PIL cannot do tracking): draw letter by letter
    if not ls: d.text(xy, s, font=font, fill=fill, anchor=anchor); return font.getlength(s)
    x, y = xy; w = shirina(s, font, ls)
    if anchor[0] == 'm': x -= w / 2
    elif anchor[0] == 'r': x -= w
    for c in s: d.text((x, y), c, font=font, fill=fill, anchor='l' + anchor[1]); x += font.getlength(c) + ls
    return w
# Captions use the narrator's own words; country names follow the lesson's map exercise.
METKI = {  # name: (title, subtitle, show, hide, label side: None = automatic, 'ln' = down-left)
    'avstralopitek': ('АВСТРАЛОПИТЕК', '«южная обезьяна» · ЮАР', 12.2, 16.0, None),
    'olduvay': ('ЧЕЛОВЕК УМЕЛЫЙ', 'Олдувайское ущелье, Танзания', 19.2, 24.8, None),
    'yava': ('ЧЕЛОВЕК ПРЯМОХОДЯЩИЙ', 'остров Ява, Индонезия', 32.4, 35.6, None),
    'kitay': ('СИНАНТРОП', 'Китай · тоже человек прямоходящий', 35.0, 38.2, None),
    'neandertal': ('НЕАНДЕРТАЛЕЦ', 'Германия · 300\u201340 тыс. лет назад', 43.6, 46.2, None),
    'kromanon': ('ЧЕЛОВЕК СОВРЕМЕННОГО ВИДА', 'Франция, грот Кро-Маньон', 53.7, 56.3, 'ln'),
}


def svechenie(a):
    lum = a @ np.array([.2126, .7152, .0722], np.float32)
    br = a * np.clip((lum - .9) / .1, 0, 1)[..., None]   # only the H. sapiens paths glow, not the bright sand
    g = cv2.GaussianBlur(br, (0, 0), 9) * .55 + cv2.GaussianBlur(br, (0, 0), 26) * .45
    return np.clip(a + g * .9, 0, 1)
def vinyetka():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((x - W / 2) / (W * .62)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    return (1 - .38 * np.clip(r - .55, 0, 1) ** 1.4)[..., None].astype(np.float32)
VIN = vinyetka()

def podpis(sloy, x, y, z, tit, sub, a, storona=None):
    d = ImageDraw.Draw(sloy); A = int(255 * a)
    tw = max(shirina(tit, F['lt'], 3), shirina(sub, F['ls'], 1)); bw, bh = tw + 50, 118
    if storona == 'ln': sprava, sverhu = False, False
    else: sprava, sverhu = x < W - bw - 170, y > 300
    ax, ay = x + (80 if sprava else -80), y + (-72 if sverhu else 72)
    bx = ax if sprava else ax - bw; by = ay - bh + 20 if sverhu else ay - 20
    bx = cl(bx, 96, W - bw - 96); by = cl(by, 40, H - bh - 40)
    # the leader line starts at the ring edge (on-screen ring radius depends on marker depth)
    rr = .0295 * 2667 / max(z, .3) * 1.1
    dx, dy = ax - x, ay - y; dn = math.hypot(dx, dy) or 1
    d.line([(x + dx / dn * rr, y + dy / dn * rr), (ax, ay)], fill=(*TERR, A), width=2)
    d.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill=(*TERR, A))
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8, fill=(10, 18, 22, int(205 * a)), outline=(*ZOL, int(70 * a)), width=1)
    razryad(d, (bx + 25, by + 52), tit, F['lt'], (*KREM, A), ls=3)
    razryad(d, (bx + 25, by + 96), sub, F['ls'], (*ZOL, A), ls=1)

# -- species cards: portrait + name + place. KART=A: the card stays fixed at the side and a thin line runs to the ring;
#    KART=B: a medallion next to the ring moves with the map (sub-pixel, no jitter). RYAD=1: at the end all species line up,
#    the extinct ones fade and ours remains.
REZ = os.environ.get('KART', 'A')  # A was chosen
RYAD = os.environ.get('RYAD', '1') == '1'
PDIR = os.environ.get('PORTRETY', f'{ROOT}/portrety/gotovye')
KART = {  # name: (title, subtitle, show, hide, top-left corner of the card in mode A); timing follows the narrator's words (golos/slova.json)
    'avstralopitek': ('АВСТРАЛОПИТЕК', '«южная обезьяна» · ЮАР', 11.2, 15.8, (1490, 300)),
    'olduvay': ('ЧЕЛОВЕК УМЕЛЫЙ', 'Олдувайское ущелье, Танзания', 18.9, 24.6, (1490, 230)),
    'yava': ('ЧЕЛОВЕК ПРЯМОХОДЯЩИЙ', 'остров Ява, Индонезия', 31.6, 34.0, (1490, 380)),
    'kitay': ('СИНАНТРОП', 'Китай · тоже человек прямоходящий', 33.6, 37.8, (1490, 120)),
    'neandertal': ('НЕАНДЕРТАЛЕЦ', 'Германия · 300\u201340 тыс. лет назад', 43.2, 46.4, (96, 200)),
    'kromanon': ('ЧЕЛОВЕК СОВРЕМЕННОГО ВИДА', 'Франция, грот Кро-Маньон', 53.2, 56.3, (96, 240)),
}
def portret(name, s):
    for f in (f'{PDIR}/{name}.png', f'{PDIR}/{name}.jpg', f'{ROOT}/portrety/zaglushki/{name}.jpg'):
        if os.path.exists(f):
            im = Image.open(f).convert('RGB'); w, h = im.size; m = min(w, h)
            return im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m)).resize((s, s), Image.LANCZOS)    # no portrait file (AI images are optional): a neutral placeholder tile keeps the pipeline running
    im = Image.new('RGB', (s, s), (22, 34, 40)); ImageDraw.Draw(im).ellipse([s * .3, s * .16, s * .7, s * .56], fill=(52, 68, 74)); return im
def perenos(s, font, ls, w):
    out, cur = [], ''
    for slovo in s.split(' '):
        tt = (cur + ' ' + slovo).strip()
        if cur and shirina(tt, font, ls) > w: out.append(cur); cur = slovo
        else: cur = tt
    return out + [cur]
KW, PAD = 360, 12
_kesh = {}
def karta(name):   # card sprite (A), RGBA
    if ('A', name) in _kesh: return _kesh[('A', name)]
    tit, sub = KART[name][:2]; PS = KW - 2 * PAD
    lt, ls_ = perenos(tit, F['kt'], 2, PS), perenos(sub, F['ks'], 1, PS)
    h = PAD + PS + 16 + 38 * len(lt) + 4 + 31 * len(ls_) + 14
    im = Image.new('RGBA', (KW, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, KW - 1, h - 1], radius=10, fill=(10, 18, 22, 228), outline=(*ZOL, 95), width=1)
    mk = Image.new('L', (PS, PS), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, PS - 1, PS - 1], radius=6, fill=255)
    im.paste(portret(name, PS), (PAD, PAD), mk)
    y = PAD + PS + 16 + 30
    for s in lt: razryad(d, (PAD + 4, y), s, F['kt'], (*KREM, 255), ls=2); y += 38
    y += 4 - 6
    for s in ls_: razryad(d, (PAD + 4, y), s, F['ks'], (*ZOL, 255), ls=1); y += 31
    _kesh[('A', name)] = im; return im
def medal(name, D=168, txt=True):   # medallion sprite (B and the final row): round portrait in a gold ring + caption below
    key = ('B', name, D, txt)
    if key in _kesh: return _kesh[key]
    tit, sub = KART[name][:2]
    bolshoy = D > 140
    ft, fs = (F['mt'], F['ms']) if bolshoy else (F['rt'], F['rt'])
    lt = perenos(tit, ft, 1, 300 if bolshoy else 200) if txt else []
    ls_ = perenos(sub, fs, 0, 300) if (txt and bolshoy) else []
    Wd = max(D + 8, 320 if bolshoy else 210)
    hh = D + 8 + ((14 + 30 * len(lt) + 26 * len(ls_)) if txt else 0) + 6
    im = Image.new('RGBA', (Wd, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = Wd // 2
    S = 4; E = D + 8
    big = Image.new('L', (E * S, E * S), 0); ImageDraw.Draw(big).ellipse([4 * S, 4 * S, (D + 4) * S, (D + 4) * S], fill=255)
    mk = big.resize((E, E), Image.LANCZOS)
    kb = Image.new('L', (E * S, E * S), 0); ImageDraw.Draw(kb).ellipse([1 * S, 1 * S, (D + 7) * S, (D + 7) * S], fill=255)
    kb = kb.resize((E, E), Image.LANCZOS)
    kr = Image.new('RGBA', (E, E), (0, 0, 0, 0)); kr.paste((*ZOL, 255), (0, 0), kb); im.alpha_composite(kr, (cx - E // 2, 0))
    pim = Image.new('RGBA', (E, E), (0, 0, 0, 0)); pim.paste(portret(name, E), (0, 0), mk)
    im.alpha_composite(pim, (cx - E // 2, 0))
    if txt:
        # dark plate under the text so it reads over the map
        ty0 = E + 6; d.rounded_rectangle([cx - Wd // 2 + 4, ty0, cx + Wd // 2 - 4, hh - 2], radius=8, fill=(10, 18, 22, 200))
        y = E + 14
        for s in lt: y += 24 if bolshoy else 18; razryad(d, (cx, y), s, ft, (*KREM, 255), ls=1, anchor='ms'); y += 6
        for s in ls_: y += 22; d.text((cx, y), s, font=fs, fill=(*ZOL, 255), anchor='ms'); y += 4
    _kesh[key] = im; return im
def na_kadr(acc, spr, x, y, a):
    # sprite with a fractional offset (bilinear), no whole-pixel stepping; acc is premultiplied RGBA float
    if a <= .01: return
    s = np.asarray(spr).astype(np.float32) / 255; s[..., :3] *= s[..., 3:4]
    Mx = np.float32([[1, 0, x], [0, 1, y]])
    w = cv2.warpAffine(s, Mx, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * a
    acc[...] = w + acc * (1 - w[..., 3:4])
def liniya(acc, p0, p1, a, tol=2, tochka=True):
    # anti-aliased line with sub-pixel precision (cv2, shift=4)
    if a <= .01: return
    m = np.zeros((H, W), np.uint8); q = lambda p: (int(round(p[0] * 16)), int(round(p[1] * 16)))
    cv2.line(m, q(p0), q(p1), 255, tol, cv2.LINE_AA, 4)
    if tochka: cv2.circle(m, q(p1), 4 * 16, 255, -1, cv2.LINE_AA, 4)
    al = (m.astype(np.float32) / 255 * a)[..., None]; col = np.array(TERR, np.float32) / 255
    acc[...] = np.concatenate([col * al, al], -1) + acc * (1 - al)
def gladko(name, n, r=3):   # smoothed marker position (+-r frames)
    xs = [M[str(min(max(1, n + i), len(M)))][name] for i in range(-r, r + 1)]
    return sum(p[0] for p in xs) / len(xs), sum(p[1] for p in xs) / len(xs), M[str(n)][name][2], M[str(n)][name][3]
def kartochki(acc, n, t):
    for name, (tit, sub, t0, t1, (kx, ky)) in KART.items():
        x, y, vid, z = gladko(name, n); av = okno(t, t0, t1) * cl((vid - .12) / .2)
        if av <= .01: continue
        rr = .0295 * 2667 / max(z, .3) * 1.1
        if REZ == 'A':
            spr = karta(name); kh = spr.size[1]
            ax = kx if kx > x else kx + KW; ay = cl(y, ky + 40, ky + kh - 40)
        else:
            spr = medal(name)
            # the medallion side is chosen once per window, at mid-show, so it does not jump
            xm, ym = M[str(1 + round((t0 + t1) / 2 * FPS))][name][:2]
            dx = 190 if xm < 1250 else -190; dy = -200 if ym > 380 else 200
            cxm, cym = x + dx, y + dy
            kx, ky = cxm - spr.size[0] / 2, cym - (168 + 8) / 2
            dn0 = math.hypot(dx, dy); ax, ay = cxm - dx / dn0 * 90, cym - dy / dn0 * 90
        dx_, dy_ = ax - x, ay - y; dn = math.hypot(dx_, dy_) or 1
        liniya(acc, (x + dx_ / dn * rr, y + dy_ / dn * rr), (ax, ay), av, tochka=(REZ == 'A'))
        na_kadr(acc, spr, kx, ky, av)
def ryad(acc, t):
    # finale: all species in a column on the right; on 'only one species remained' the extinct ones fade to grey, ours stays gold
    if not RYAD: return
    for i, name in enumerate(KART):
        a = sgl(cl((t - (61.0 + .14 * i)) / .7)) * (1 - sgl(cl((t - (DLIT - 1.4)) / .8)))
        if a <= .01: continue
        cx, cy = 1530 + 220 * (i % 2), 210 + 250 * (i // 2)
        spr = medal(name, 116)
        if i < 5:
            g = sgl(cl((t - 62.4) / 1.4))
            if g > 0:
                arr = np.asarray(spr).astype(np.float32); sero = arr[..., :3] @ np.array([.3, .59, .11], np.float32)
                arr[..., :3] = arr[..., :3] * (1 - g) + sero[..., None] * g
                spr = Image.fromarray(arr.astype(np.uint8), 'RGBA'); a *= 1 - .6 * g
        na_kadr(acc, spr, cx - spr.size[0] / 2, cy - 62, a)

def ten(sloy, r=10, a=.75):
    al = np.asarray(sloy.split()[-1]).astype(np.float32) / 255
    sh = cv2.GaussianBlur(al, (0, 0), r) * a
    t = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (np.clip(sh, 0, 1) * 255).astype(np.uint8)]), 'RGBA')
    return Image.alpha_composite(t, sloy)

# end captions timed to the voice (plan v4): S7 at ~57.6 s, S8 at ~61.0 s
TITRY = [('Останки людей современного вида \u2014 во всех частях света', 58.2, 61.2),
         ('В конце концов на Земле остался один вид людей \u2014 наш', 61.0, DLIT - .6)]
def kadr(n):
    t = (n - 1) / FPS
    im = Image.open(f'{ROOT}/kadry/{n:04d}.png').convert('RGB')
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)   # --proba renders are half size: upscale, labels stay crisp
    a = np.asarray(im).astype(np.float32) / 255
    a = svechenie(a) * VIN
    base = Image.fromarray((a * 255).astype(np.uint8)).convert('RGBA')
    # marker labels and the legend sit on plates
    sloy = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sloy)
    k = M[str(n)]
    # path legend at the top left; plate width follows what is drawn (letter-spaced capitals).
    # H. erectus dims together with its paths and leaves on 'only one species remained'; the H. sapiens row moves up into its place.
    a_er = sgl(cl((t - 28.0) / .8)) * (1 - sgl(cl((t - 60.6) / .8)))
    tusk = sgl(cl((t - 38.2) / 1.5))
    c_er = tuple(int(c0 + (c1 - c0) * tusk) for c0, c1 in zip(C_ER, C_ER_TUSK))
    a_sap = sgl(cl((t - 48.4) / .8))
    y_sap = 100 + 64 * (1 - sgl(cl((t - 61.0) / 1.0)))
    for txt, col, al, yy in (('человек прямоходящий', c_er, a_er, 100), ('люди современного вида', C_SAP, a_sap, y_sap)):
        al *= 1 - sgl(cl((t - (DLIT - 1.4)) / .8))
        if al > .01:
            T = txt.upper(); w = shirina(T, F['leg'], 2) + 74 + 24
            d.rounded_rectangle([96, yy - 38, 96 + w, yy + 14], radius=7, fill=(10, 18, 22, int(185 * al)))
            d.line([(114, yy - 12), (156, yy - 12)], fill=(*col, int(255 * al)), width=5)
            razryad(d, (170, yy), T, F['leg'], (*KREM, int(255 * al)), ls=2)
    sloy2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d2 = ImageDraw.Draw(sloy2)
    # clip title
    at = okno(t, .7, 4.8, .8)
    if at > .01:
        razryad(d2, (120, 452), 'ДРЕВНЕЙШИЕ ЛЮДИ', F['eyb'], (*ZOL, int(255 * at)), ls=6)
        d2.text((112, 570), 'Из Африки \u2014', font=F['tit'], fill=(*KREM, int(255 * at)), anchor='ls')
        d2.text((112, 690), 'по всему миру', font=F['tit'], fill=(*KREM, int(255 * at)), anchor='ls')
    aa = okno(t, 5.6, 7.8, .6)   # fades before the globe edge reaches the caption
    if aa > .01:
        razryad(d2, (120, 860), 'ПРАРОДИНА ЧЕЛОВЕКА', F['eyb'], (*ZOL, int(255 * aa)), ls=6)
        d2.text((112, 950), 'Африка', font=F['afr'], fill=(*KREM, int(255 * aa)), anchor='ls')
    # end captions: one replaces the other, at the bottom over a soft gradient
    afs = [okno(t, a0, a1, .9) for _, a0, a1 in TITRY]
    if max(afs) > .01:
        af = max(afs)
        g = np.zeros((H, W, 4), np.uint8); ys = np.arange(H)[:, None]
        g[..., 3] = (np.clip((ys - 860) / 200, 0, 1) * 110 * af).astype(np.uint8).repeat(W, 1)
        sloy2 = Image.alpha_composite(Image.fromarray(g, 'RGBA'), sloy2); d2 = ImageDraw.Draw(sloy2)
        for (txt, _, _), ai in zip(TITRY, afs):
            if ai > .01: d2.text((W / 2, 1010), txt, font=F['cap'], fill=(*KREM, int(255 * ai)), anchor='ms')
    acc = np.zeros((H, W, 4), np.float32); kartochki(acc, n, t); ryad(acc, t)
    b = np.asarray(base).astype(np.float32) / 255
    b[..., :3] = acc[..., :3] + b[..., :3] * (1 - acc[..., 3:4])
    base = Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8), 'RGBA')
    out = Image.alpha_composite(base, sloy)
    out = Image.alpha_composite(out, ten(sloy2, 12, .8))
    # fade in at the start and fade out at the end
    fade = sgl(cl(t / .8)) * sgl(cl((DLIT - t) / .8))
    o = (np.asarray(out.convert('RGB')).astype(np.float32) * fade).astype(np.uint8)
    Image.fromarray(o).save(f'{ROOT}/{POST}/{n:04d}.jpg', quality=93)

if '-' in ARG and ',' not in ARG:
    a, b = map(int, ARG.split('-')); spisok = range(a, b + 1)
else: spisok = [int(x) for x in ARG.split(',')]
for n in spisok:
    if os.path.exists(f'{ROOT}/kadry/{n:04d}.png'): kadr(n)
print('ok', len(list(spisok)))
