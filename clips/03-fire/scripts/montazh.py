# Clip 3 'Fire', edit: shots + soft dissolves + glow on bright areas + sparse rain in the storm + title and captions.
# Caption design as in 'Kostenki' (frosted-glass cards, 'pills' next to objects), everything with sub-pixel precision.
#   python montazh.py <root> [frames: 1-400 | 10,200 | vse | plan]      (POST=<dir>: output folder, default <root>/post)
import sys, os, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = sys.argv[1]; ARG = sys.argv[2] if len(sys.argv) > 2 else 'vse'
FPS, W, H = 24, 1920, 1080
PER = .6                                                              # dissolve between shots, s
PLANY = [('A1', 7.6), ('A2', 7.0), ('B1', 5.2), ('B2', 6.4), ('C', 14.0), ('D1a', 6.4), ('D1b', 3.4), ('D2', 7.6), ('E', 18.0)]
ZATEMN = {'C': .9, 'D1a': .55, 'E': .45}                              # these shots are entered through a fade to black (change of place and time)
T0 = {}; _t = 0.0
for _s, _d in PLANY: T0[_s] = _t; _t += _d - PER
DL = dict(PLANY); DLIT = T0['E'] + DL['E']; NF = int(round(DLIT * FPS))
if ARG == 'plan':
    for s_, d_ in PLANY: print(f'{s_:4s} {T0[s_]:6.2f} \u2013 {T0[s_] + d_:6.2f}')
    print('total', DLIT, 's,', NF, 'frames'); sys.exit(0)
M = {s: json.load(open(f'{ROOT}/metki-{s}.json')) for s, _ in PLANY if os.path.exists(f'{ROOT}/metki-{s}.json')}
OUT = os.environ.get('POST', f'{ROOT}/post'); os.makedirs(OUT, exist_ok=True)
SH = f'{ROOT}/shrifty'; SS = 2
def osw(sz, wt=600):
    f = ImageFont.truetype(f'{SH}/Oswald.ttf', int(sz * SS)); f.set_variation_by_axes([wt]); return f
def cor(sz, wt=600):
    f = ImageFont.truetype(f'{SH}/CormorantGaramond-Italic.ttf', int(sz * SS)); f.set_variation_by_axes([wt]); return f
F = dict(kt=osw(44, 600), ks=osw(31, 400), pill=osw(30, 500), tit=cor(190, 600), lin=osw(24, 500), lin2=osw(40, 600))
KREM, ZOL, TERR = (244, 234, 214), (233, 183, 101), (255, 128, 80)
STEKLO = np.array([.035, .05, .06], np.float32)
cl = lambda x, a=0., b=1.: max(a, min(b, x))
smt = lambda u: (lambda x: x * x * x * (x * (6 * x - 15) + 10))(cl(u))
def okno(t, a, b, f=.8): return smt((t - a) / f) * smt((b - t) / f)
def shirina(s, font, ls=0): return sum(font.getlength(c) for c in s) + ls * SS * (len(s) - 1)
def razryad(d, xy, s, font, fill, ls=0):
    x, y = xy
    for c in s: d.text((x, y), c, font=font, fill=fill, anchor='ls'); x += font.getlength(c) + ls * SS

# -- shot frames
_kesh = {}
def _sst(x, a_, b_):
    t_ = np.clip((x - a_) / (b_ - a_), 0, 1); return t_ * t_ * (3 - 2 * t_)
def sgladit_ogon(f, sig=4.2):
    # EEVEE renders the flames on the tree with 'hatching' (an artefact of slice-based volume rendering). Average the brightness only between
    # 'fire' pixels: dark branches, leaf silhouettes and the sky are excluded and unchanged. f is RGB 0..1.
    r, b = f[..., 0], f[..., 2]
    w = _sst(r, .30, .48) * _sst(r - b, .06, .18)
    if w.max() < .05: return f
    gw = cv2.GaussianBlur(w, (0, 0), sig)
    sm = cv2.GaussianBlur(f * w[..., None], (0, 0), sig) / np.maximum(gw, 1e-4)[..., None]
    k = (w * _sst(gw, .25, .6))[..., None]                          # single sparks and rare leaves are left alone
    o = (f * (1 - k) + sm * k).astype(np.float32)
    m = np.clip(cv2.GaussianBlur(cv2.dilate(w, np.ones((7, 7), np.uint8)), (0, 0), 5) * 1.5, 0, 1)[..., None]
    x = cv2.bilateralFilter(o, 0, .15, 3.5)                         # flame edges stay soft, branch outlines stay intact
    o = (o * (1 - m) + x * m).astype(np.float32)
    # flame colour: in the render it is overexposed to a flat cream. The core stays light, the edges get yellow and orange.
    serd = _sst(cv2.GaussianBlur(w, (0, 0), 14), .55, .97)[..., None]
    gg = 1.25 + .75 * (1 - serd[..., 0]); gb = 1.9 + 2.3 * (1 - serd[..., 0])
    c = np.stack([o[..., 0], np.power(np.clip(o[..., 1], 0, 1), gg), np.power(np.clip(o[..., 2], 0, 1), gb)], -1)
    return (o * (1 - k) + c * k).astype(np.float32)
def kadr_plana(s, t_rel):
    nf = int(round(DL[s] * FPS)); n = max(1, min(nf, 1 + int(round(t_rel * FPS))))
    for pap in (f'{ROOT}/kadry/{s}', f'{ROOT}/kadry/{s}-proba'):
        f = f'{pap}/{n:04d}.png'
        if os.path.exists(f): break
    else: return np.zeros((H, W, 3), np.float32), n
    if f not in _kesh:
        if len(_kesh) > 4: _kesh.clear()
        im = Image.open(f).convert('RGB')
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        _kesh[f] = np.asarray(im).astype(np.float32) / 255
        if s in ('A1', 'A2'): _kesh[f] = sgladit_ogon(_kesh[f])
    return _kesh[f], n
def metka(s, n, k):
    try: return M[s]['kadry'][max(0, min(len(M[s]['kadry']) - 1, n - 1))].get(k)
    except Exception: return None

# -- rain: sparse slanted streaks in three layers, visible mostly in the flashes
rng = np.random.default_rng(7)
DOZHD = [dict(x=rng.uniform(-200, W, 120 * k), y=rng.uniform(0, H, 120 * k), dl=rng.uniform(30, 60, 120 * k) * (4 - k) / 2, v=rng.uniform(900, 1300, 120 * k) * (4 - k) / 2.2,
              a=rng.uniform(.35, 1.0, 120 * k)) for k in (1, 2, 3)]
def dozhd(a, t, sila, svet):
    if sila <= .01: return a
    m = np.zeros((H, W), np.uint8); q = lambda v: int(round(v * 16))
    for L_ in DOZHD:
        y = (L_['y'] + L_['v'] * t) % (H + 120) - 60; x = (L_['x'] + L_['v'] * .28 * t) % (W + 200) - 100
        for xi, yi, dl, ai in zip(x, y, L_['dl'], L_['a']):
            cv2.line(m, (q(xi), q(yi)), (q(xi + dl * .27), q(yi + dl)), int(255 * ai), 1, cv2.LINE_AA, 4)
    mm = cv2.GaussianBlur(m, (0, 0), .7).astype(np.float32)[..., None] / 255 * sila * (.10 + .9 * min(1, svet))
    return a + mm * np.array([.62, .7, .85], np.float32) * (1 - a)
def vinyetka():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((x - W / 2) / (W * .62)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    return (1 - .42 * np.clip(r - .5, 0, 1) ** 1.4)[..., None].astype(np.float32)
VIN = vinyetka()
def svechenie(a, sila=.8):
    """Glow on bright areas (fire, sparks, lightning, eyes): two blurs of the overexposed part, combined with 'screen'. Computed at half size."""
    m = cv2.resize(a, (W // 2, H // 2), interpolation=cv2.INTER_AREA); lum = m.max(2, keepdims=True)
    yark = m * np.clip((lum - .62) / .38, 0, 1) ** 1.6
    g = cv2.GaussianBlur(yark, (0, 0), 7) * .6 + cv2.GaussianBlur(yark, (0, 0), 26) * .7
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR) * sila
    return 1 - (1 - a) * (1 - np.clip(g, 0, 1))
ZERNO = [np.random.default_rng(100 + i).normal(0, 1, (H // 2, W // 2)).astype(np.float32) for i in range(6)]
def zerno(a, n, sila=.012):
    z = cv2.resize(ZERNO[n % 6], (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return a + z * sila * (.35 + a.mean(2, keepdims=True))

# -- caption sprites
_spr = {}
def umenshit(im):
    a = np.asarray(im).astype(np.float32) / 255; a[..., :3] *= a[..., 3:4]
    return cv2.resize(a, (im.width // SS, im.height // SS), interpolation=cv2.INTER_AREA)
def plashka(tit, sub):
    k = ('p', tit, sub)
    if k in _spr: return _spr[k]
    T = tit.split('\n'); S = sub.split('\n') if sub else []
    tw = max([shirina(s, F['kt'], 2) for s in T] + [shirina(s, F['ks'], .5) for s in S]) / SS
    ys = [54 + 52 * i for i in range(len(T))]; ys2 = [ys[-1] + 44 + 39 * i for i in range(len(S))]
    bw, bh = int(tw + 30 + 30 + 6), (ys2 or ys)[-1] + 24
    im = Image.new('RGBA', (bw * SS, bh * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=14 * SS, outline=(*ZOL, 70), width=SS)
    d.rounded_rectangle([0, 0, 5 * SS, bh * SS - 1], radius=3 * SS, fill=(*ZOL, 235))
    for s, y in zip(T, ys): razryad(d, (36 * SS, y * SS), s, F['kt'], (*KREM, 255), 2)
    for s, y in zip(S, ys2): razryad(d, (36 * SS, y * SS), s, F['ks'], (*ZOL, 255), .5)
    mask = Image.new('L', (bw * SS, bh * SS), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=14 * SS, fill=255)
    m = cv2.resize(np.asarray(mask).astype(np.float32) / 255, (bw, bh), interpolation=cv2.INTER_AREA)
    _spr[k] = (umenshit(im), m); return _spr[k]
def tabletka(txt):
    k = ('t', txt)
    if k in _spr: return _spr[k]
    TT = txt.upper().split('\n'); tw = max(shirina(T, F['pill'], 1.5) for T in TT) / SS; bw, bh = int(tw + 36), 48 + 36 * (len(TT) - 1)
    im = Image.new('RGBA', (bw * SS, bh * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=11 * SS, outline=(*TERR, 150), width=SS)
    for i_, T in enumerate(TT): razryad(d, (18 * SS, (34 + 36 * i_) * SS), T, F['pill'], (*KREM, 255), 1.5)
    mask = Image.new('L', (bw * SS, bh * SS), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=11 * SS, fill=255)
    m = cv2.resize(np.asarray(mask).astype(np.float32) / 255, (bw, bh), interpolation=cv2.INTER_AREA)
    _spr[k] = (umenshit(im), m); return _spr[k]
def titul(txt):
    k = ('tit', txt)
    if k in _spr: return _spr[k]
    tw = shirina(txt, F['tit'], 3) / SS; bw, bh = int(tw + 80), 270
    im = Image.new('RGBA', (bw * SS, bh * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    razryad(d, (30 * SS, 190 * SS), txt, F['tit'], (*KREM, 255), 3)
    d.rounded_rectangle([34 * SS, 232 * SS, (34 + 150) * SS, 236 * SS], radius=2 * SS, fill=(*ZOL, 235))
    ten = Image.new('L', (bw * SS, bh * SS), 0); razryad(ImageDraw.Draw(ten), (30 * SS, 190 * SS), txt, F['tit'], 255, 3)
    t_ = cv2.GaussianBlur(cv2.resize(np.asarray(ten).astype(np.float32) / 255, (bw, bh), interpolation=cv2.INTER_AREA), (0, 0), 14)
    _spr[k] = (umenshit(im), t_); return _spr[k]
def tekst(txt, font_k, cvet=KREM):
    k = ('x', txt, font_k)
    if k in _spr: return _spr[k]
    f = F[font_k]; tw = shirina(txt, f, 1) / SS; bw, bh = int(tw + 16), int(f.size / SS * 1.5)
    im = Image.new('RGBA', (bw * SS, bh * SS), (0, 0, 0, 0)); razryad(ImageDraw.Draw(im), (8 * SS, int(bh * .78) * SS), txt, f, (*cvet, 255), 1)
    _spr[k] = umenshit(im); return _spr[k]
def sdvig(arr, x, y):
    return cv2.warpAffine(arr, np.float32([[1, 0, x], [0, 1, y]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)

class Holst:
    def __init__(s, kadr): s.o = kadr; s.razmyt = None
    def steklo(s, m, a):
        if s.razmyt is None: s.razmyt = cv2.GaussianBlur(s.o, (0, 0), 16)
        ten = cv2.GaussianBlur(np.roll(m, 7, axis=0), (0, 0), 9)[..., None] * .38 * a
        s.o = s.o * (1 - ten * (1 - m[..., None]))
        g = s.razmyt * .42 + STEKLO * .58
        s.o = s.o * (1 - m[..., None] * a * .93) + g * m[..., None] * a * .93
    def spr(s, rgba, a):
        s.o = rgba[..., :3] * a + s.o * (1 - rgba[..., 3:4] * a)
    def liniya(s, p0, p1, a, tol=3, cvet=TERR):
        q = lambda p: (int(round(p[0] * 16)), int(round(p[1] * 16)))
        m1 = np.zeros((H, W), np.uint8); cv2.line(m1, q(p0), q(p1), 255, tol + 3, cv2.LINE_AA, 4)
        m2 = np.zeros((H, W), np.uint8); cv2.line(m2, q(p0), q(p1), 255, tol, cv2.LINE_AA, 4)
        a1 = (m1.astype(np.float32) / 255 * a * .45)[..., None]; s.o = s.o * (1 - a1)
        a2 = (m2.astype(np.float32) / 255 * a)[..., None]; s.o = s.o * (1 - a2) + np.array(cvet, np.float32) / 255 * a2
    def tochka(s, x, y, a, r=7):
        if a <= .01: return
        q = lambda v: int(round(v * 16))
        mo = np.zeros((H, W), np.uint8); cv2.circle(mo, (q(x), q(y)), q(r + 3), 255, -1, cv2.LINE_AA, 4)
        s.o = s.o * (1 - (mo.astype(np.float32) / 255 * a * .4)[..., None])
        mr = np.zeros((H, W), np.uint8); cv2.circle(mr, (q(x), q(y)), q(r), 255, 3, cv2.LINE_AA, 4); cv2.circle(mr, (q(x), q(y)), q(r * .3), 255, -1, cv2.LINE_AA, 4)
        ar = (mr.astype(np.float32) / 255 * a)[..., None]; s.o = s.o * (1 - ar) + np.array(TERR, np.float32) / 255 * ar
def krai(bx, by, bw, bh, px, py):
    if px > bx + bw: ax = bx + bw
    elif px < bx: ax = bx
    else: ax = bx + bw / 2
    if px > bx + bw or px < bx: ay = cl(py, by + 14, by + bh - 14)
    else: ay = by + bh if py > by + bh else by
    return ax, ay

# -- graphics: times a, b from the start of THEIR OWN shot (s). karta: a fixed card; metka: a 'pill' at a shot point (moves with it)
EL = [
    dict(tip='titul', sc='A1', txt='Огонь', a=.7, b=3.8, mesto=(120, 640)),
    dict(tip='karta', sc='A1', tit='АФРИКА', sub='миллион лет назад', a=3.9, b=9.6, mesto=(110, 880)),
    dict(tip='metka', sc='A2', pt='derevo', txt='огонь от молнии', a=1.6, b=6.4, off=(250, -230)),
    dict(tip='metka', sc='B1', pt='ogon', txt='огонь несут в пещеру', a=.9, b=4.7, off=(-90, -190)),
    dict(tip='metka', sc='B2', pt='vhod', txt='огонь берегут\nдень и ночь', a=2.8, b=6.0, off=(330, -150)),
    dict(tip='karta', sc='C', tit='КИТАЙ. ПЕЩЕРА ПОД ПЕКИНОМ', sub='400 тысяч лет назад', a=.7, b=7.0, mesto=(110, 120)),
    dict(tip='metka', sc='C', pt='linza', txt='зола и угли', a=5.2, b=13.6, off=(-330, -30), usl='linza_vidna'),
    dict(tip='karta', sc='D1a', tit='ПОЗЖЕ', sub='люди научились добывать огонь сами', a=.6, b=5.0, mesto=(110, 120)),
    dict(tip='metka', sc='D1a', pt='lunka', txt='трением', a=2.0, b=6.2, off=(260, -200)),
    dict(tip='metka', sc='D2', pt='udar', txt='искрами из камня', a=.8, b=5.4, off=(280, -210)),
    dict(tip='metka', sc='E', pt='eda', txt='еда', a=.8, b=4.2, off=(190, -130)),
    dict(tip='metka', sc='E', pt='teplo', txt='тепло', a=4.8, b=7.6, off=(-60, -210)),
    dict(tip='metka', sc='E', pt='svet', txt='свет', a=8.2, b=10.6, off=(170, -120)),
    dict(tip='tabl', sc='E', txt='защита', a=10.9, b=15.3, mesto=(110, 860)),          # no arrow: the caption is about fire, not about the animal
]

def oformlenie(h, t):
    for e in EL:
        s = e['sc']; tl = t - T0[s]; a = okno(tl, e['a'], e['b'])
        if a <= .01: continue
        nf = int(round(DL[s] * FPS)); n = max(1, min(nf, 1 + int(round(tl * FPS))))
        if e['tip'] == 'titul':
            spr, ten = titul(e['txt']); x, y = e['mesto']; y -= 14 * (1 - smt((tl - e['a']) / 1.4))
            h.o = h.o * (1 - sdvig(ten, x, y)[..., None] * .55 * a); h.spr(sdvig(spr, x, y), a)
        elif e['tip'] == 'karta':
            spr, m = plashka(e['tit'], e.get('sub', '')); x, y = e['mesto']
            h.steklo(sdvig(m, x, y), a); h.spr(sdvig(spr, x, y), a)
        elif e['tip'] == 'tabl':
            spr, m = tabletka(e['txt']); x, y = e['mesto']; y += 10 * (1 - smt((tl - e['a']) / 1.0))
            h.steklo(sdvig(m, x, y), a); h.spr(sdvig(spr, x, y), a)
        elif e['tip'] == 'metka':
            p = metka(s, n, e['pt'])
            if p is None: continue
            if e.get('usl') and not metka(s, n, e['usl']): continue
            px, py = p[0] * W, p[1] * H
            if not (-200 < px < W + 200 and -200 < py < H + 200): continue
            spr, m = tabletka(e['txt']); bw, bh = m.shape[1], m.shape[0]
            bx = cl(px + e['off'][0] - bw / 2, 60, W - bw - 60); by = cl(py + e['off'][1] - bh / 2, 60, H - bh - 60)
            ax, ay = krai(bx, by, bw, bh, px, py)
            dx, dy = px - ax, py - ay; L_ = math.hypot(dx, dy) or 1
            k_ = smt((tl - e['a']) / 1.0)                                          # the line draws itself towards the point
            ex, ey = ax + dx * k_ * (1 - 16 / L_), ay + dy * k_ * (1 - 16 / L_)
            h.liniya((ax, ay), (ex, ey), a * .9, 3); h.tochka(px, py, a * k_)
            h.steklo(sdvig(m, bx, by), a); h.spr(sdvig(spr, bx, by), a)

def lineyka(h, t):
    """Measuring rod by the section in scene C: grows with the layers; a tick every metre; '6 metres' at the end."""
    s = 'C'
    if s not in M: return
    tl = t - T0[s]; a = okno(tl, 1.6, DL[s] - .2, .7)
    if a <= .01: return
    nf = int(round(DL[s] * FPS)); n = max(1, min(nf, 1 + int(round(tl * FPS))))
    niz, verh, hh = metka(s, n, 'niz'), metka(s, n, 'verh'), metka(s, n, 'h')
    if not niz or not verh or not hh: return
    x0, y0 = niz[0] * W + 46, niz[1] * H; x1, y1 = verh[0] * W + 46, verh[1] * H
    h.liniya((x0, y0), (x1, y1), a, 3, KREM)
    for m_ in range(0, int(hh + 1e-3) + 1):
        u = m_ / hh; xm, ym = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        h.liniya((xm - 12, ym), (xm + 12, ym), a, 3, KREM)
        if m_ and m_ < 6:
            sp = tekst(f'{m_} м', 'lin'); h.spr(sdvig(sp, xm + 22, ym - sp.shape[0] * .55), a * .85)
    h.liniya((x1 - 16, y1), (x1 + 16, y1), a, 4, ZOL)
    a6 = a * smt((hh - 5.75) / .25)
    if a6 > .01:
        spr, m = plashka('6 МЕТРОВ', 'слой с золой и углями'); bx, by = cl(x1 + 40, 60, W - m.shape[1] - 60), cl(y1 - 40, 60, H - m.shape[0] - 60)
        h.steklo(sdvig(m, bx, by), a6); h.spr(sdvig(spr, bx, by), a6)

def kadr(n):
    t = (n - 1) / FPS
    sloi = [(s, t - T0[s]) for s, d in PLANY if T0[s] - 1e-6 <= t < T0[s] + d + 1e-6]
    out = None
    for i, (s, tl) in enumerate(sloi):
        a, nk = kadr_plana(s, tl)
        if s in ('A1', 'A2'):
            v = metka(s, nk, 'vsp') or 0.0
            a = dozhd(a, t, .32 if s == 'A1' else .2, v)
        if out is None: out = a
        else:
            u = smt(tl / PER)
            out = out * (1 - u) + a * u
            z = ZATEMN.get(s, 0)
            if z: out = out * (1 - z * math.sin(math.pi * cl(tl / PER)) ** 1.2)
    out = svechenie(out)
    out = out * VIN
    out = zerno(out, n)
    h = Holst(out.astype(np.float32)); oformlenie(h, t); lineyka(h, t)
    o = h.o * smt(t / .9) * smt((DLIT - t) / 1.3)
    Image.fromarray((np.clip(o, 0, 1) * 255 + .5).astype(np.uint8)).save(f'{OUT}/{n:04d}.jpg', quality=95, subsampling=0)

if '-' in ARG and ',' not in ARG:
    a_, b_ = ARG.split('-'); KADRY = range(int(a_), int(b_) + 1)
elif ARG == 'vse': KADRY = range(1, NF + 1)
else: KADRY = [int(x) for x in ARG.split(',')]
for n in KADRY:
    if 1 <= n <= NF: kadr(n)
print('done', len(list(KADRY)))
