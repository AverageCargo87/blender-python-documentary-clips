# Clip 2 'Kostenki', edit v2: scenes + transitions + atmosphere (as in the first edit) and the NEW graphics:
#  * cards on 'frosted glass' (the blurred frame underneath), a shadow, a gold stripe, text rendered at double resolution;
#  * a leader line draws itself from the card to the spot, where a crisp marker pulses softly;
#  * small 'pill' labels next to objects and places (the Don, chalk, hearth, needle...), a direction arrow (Voronezh);
#  * everything is placed with sub-pixel precision, so nothing jitters.
#   python montazh2.py <root> [frames: 1-1473 | 10,200]
import sys, os, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = sys.argv[1]; ARG = sys.argv[2] if len(sys.argv) > 2 else 'vse'
FPS, W, H = 30, 1920, 1080
# scenes in order (duration, s); each next one starts 0.6 s before the previous ends (cross-dissolve)
_DL = [('A', 11.6), ('B', 11.0), ('S', 23.0), ('C', 11.0), ('H', 20.0), ('D1', 12.0), ('D2', 16.8), ('E', 15.0)]   # H, D2 and S are smoothly slowed down (zamedlit.py)
SCENY = []; _t = 0.0
for _s, _d in _DL: SCENY.append((_s, _t, _d)); _t += _d - .6
T0 = {s_: t_ for s_, t_, d_ in SCENY}
DLIT = SCENY[-1][1] + SCENY[-1][2]; NF = int(round(DLIT * FPS))
M = {s: json.load(open(f'{ROOT}/metki-{s}.json')) for s, _, _ in SCENY if os.path.exists(f'{ROOT}/metki-{s}.json')}
OUT = os.environ.get('POST', f'{ROOT}/post'); os.makedirs(OUT, exist_ok=True)
SH = f'{ROOT}/shrifty'; SS = 2                                     # text and icons are drawn at 2x and scaled down
def osw(sz, wt=600):
    f = ImageFont.truetype(f'{SH}/Oswald.ttf', int(sz * SS)); f.set_variation_by_axes([wt]); return f
def cor(sz, wt=600):
    f = ImageFont.truetype(f'{SH}/CormorantGaramond-Italic.ttf', int(sz * SS)); f.set_variation_by_axes([wt]); return f
F = dict(kt=osw(44, 600), ks=osw(31, 400), pill=osw(27, 500), eyb=osw(34, 500), tit=cor(96), bdg=osw(26, 500), ill=cor(34, 600), kop=osw(19, 400))
KREM, ZOL, TERR = (244, 234, 214), (233, 183, 101), (255, 128, 80)
STEKLO = np.array([.035, .06, .075], np.float32)
cl = lambda x, a=0., b=1.: max(a, min(b, x))
sgl = lambda u: u * u * (3 - 2 * u)
evo = lambda u: 1 - (1 - cl(u)) ** 3                                # soft ease-out
smt = lambda u: (lambda x: x * x * x * (x * (6 * x - 15) + 10))(cl(u))   # very smooth ease-in-out (smootherstep)
def okno(t, a, b, f=.9): return smt((t - a) / f) * smt((b - t) / f)
def shirina(s, font, ls=0): return sum(font.getlength(c) for c in s) + ls * SS * (len(s) - 1)
def razryad(d, xy, s, font, fill, ls=0):
    x, y = xy
    for c in s: d.text((x, y), c, font=font, fill=fill, anchor='ls'); x += font.getlength(c) + ls * SS

# -- scene frames
_kesh = {}
def kadr_sceny(s, t_rel):
    mx = len(M[s]['kadry']); n = max(1, min(mx, 1 + int(round(t_rel * FPS)))); f = f'{ROOT}/kadry/{s}/{n:04d}.png'
    if not os.path.exists(f) and os.path.exists(f'{ROOT}/proba/{s}/{n:04d}.png'): f = f'{ROOT}/proba/{s}/{n:04d}.png'   # --proba renders
    if f not in _kesh:
        if len(_kesh) > 6: _kesh.clear()
        im = Image.open(f).convert('RGB')
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)   # half-size preview frames
        _kesh[f] = np.asarray(im).astype(np.float32) / 255
    return _kesh[f], n
def masshtab(a, s, cx, cy):
    Mx = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
    return cv2.warpAffine(a, Mx, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
rng = np.random.default_rng(7)
SNEG = [dict(x=rng.uniform(0, W, 140 * k), y=rng.uniform(0, H, 140 * k), r=rng.uniform(.8, 1.6, 140 * k) * (4 - k),
             v=rng.uniform(40, 70, 140 * k) * (4 - k) * .45, dr=rng.uniform(8, 26, 140 * k), ph=rng.uniform(0, 6.3, 140 * k)) for k in (1, 2, 3)]
def sneg(a, t, sila):
    if sila <= .01: return a
    m = np.zeros((H, W), np.uint8)
    for L_ in SNEG:
        y = (L_['y'] + L_['v'] * t) % (H + 40) - 20; x = (L_['x'] + L_['dr'] * np.sin(t * .6 + L_['ph'])) % W
        for xi, yi, ri in zip(x, y, L_['r']): cv2.circle(m, (int(xi * 16), int(yi * 16)), max(16, int(ri * 16)), 255, -1, cv2.LINE_AA, 4)
    m = cv2.GaussianBlur(m, (0, 0), .8).astype(np.float32)[..., None] / 255 * .75 * sila
    return a * (1 - m) + np.array([.95, .97, 1.0], np.float32) * m
def svet_pyatno(a, x, y, r, sila, col):
    yy, xx = np.ogrid[0:H, 0:W]; g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)).astype(np.float32)[..., None]
    return a + g * sila * np.array(col, np.float32)
def vinyetka():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((x - W / 2) / (W * .62)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    return (1 - .35 * np.clip(r - .55, 0, 1) ** 1.4)[..., None].astype(np.float32)
VIN = vinyetka()

# -- scene points on screen: (x, y, visible)
def nomer(s, t):
    s0 = [x for x in SCENY if x[0] == s][0]; return max(1, min(len(M[s]['kadry']), 1 + int(round((t - s0[1]) * FPS))))
def tochka(s, imya, n):
    j = M[s]; k = str(n)
    if s in ('A', 'B', 'E'):
        if imya in (None, 'kostenki'):
            r = j['kadry'][k]; return r[0], r[1], 1 if (s == 'A' or r[2] > 0) else 0
        r = j['tochki'][k][imya]; return r[0], r[1], (r[2] if s == 'A' else (1 if r[2] > 0 else 0))
    r = j['kadry'][k][imya]; return r[0], r[1], 1

# -- sprites: drawn at 2x, scaled down -> (premultiplied rgba float at 1x, backing mask at 1x)
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
    d.rounded_rectangle([0, 0, 5 * SS, bh * SS - 1], radius=3 * SS, fill=(*ZOL, 235))           # gold stripe on the left
    for s, y in zip(T, ys): razryad(d, (36 * SS, y * SS), s, F['kt'], (*KREM, 255), 2)
    for s, y in zip(S, ys2): razryad(d, (36 * SS, y * SS), s, F['ks'], (*ZOL, 255), .5)
    mask = Image.new('L', (bw * SS, bh * SS), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=14 * SS, fill=255)
    m = cv2.resize(np.asarray(mask).astype(np.float32) / 255, (bw, bh), interpolation=cv2.INTER_AREA)
    _spr[k] = (umenshit(im), m); return _spr[k]
def tabletka(txt):
    k = ('t', txt)
    if k in _spr: return _spr[k]
    TT = txt.upper().split('\n'); tw = max(shirina(T, F['pill'], 1.5) for T in TT) / SS; bw, bh = int(tw + 32), 44 + 34 * (len(TT) - 1)
    im = Image.new('RGBA', (bw * SS, bh * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=10 * SS, outline=(*TERR, 150), width=SS)
    for i_, T in enumerate(TT): razryad(d, (16 * SS, (31 + 34 * i_) * SS), T, F['pill'] if i_ == 0 else F['ks'], ((*KREM, 255) if i_ == 0 else (*ZOL, 255)), 1.5 if i_ == 0 else .5)
    mask = Image.new('L', (bw * SS, bh * SS), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], radius=10 * SS, fill=255)
    m = cv2.resize(np.asarray(mask).astype(np.float32) / 255, (bw, bh), interpolation=cv2.INTER_AREA)
    _spr[k] = (umenshit(im), m); return _spr[k]
def sdvig(arr, x, y):                    # sub-pixel placement of a sprite/mask on the frame
    return cv2.warpAffine(arr, np.float32([[1, 0, x], [0, 1, y]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)

# -- drawing on the frame
class Holst:
    def __init__(s, kadr): s.o = kadr; s.razmyt = None
    def steklo(s, m, a):                 # frosted glass: blurred, darkened frame + a soft shadow
        if s.razmyt is None: s.razmyt = cv2.GaussianBlur(s.o, (0, 0), 16)
        ten = cv2.GaussianBlur(np.roll(m, 7, axis=0), (0, 0), 9)[..., None] * .38 * a
        s.o = s.o * (1 - ten * (1 - m[..., None]))
        g = s.razmyt * .42 + STEKLO * .58
        s.o = s.o * (1 - m[..., None] * a * .93) + g * m[..., None] * a * .93
    def spr(s, rgba, a):
        s.o = rgba[..., :3] * a + s.o * (1 - rgba[..., 3:4] * a)
    def liniya(s, p0, p1, a, tol=3):
        q = lambda p: (int(round(p[0] * 16)), int(round(p[1] * 16)))
        m1 = np.zeros((H, W), np.uint8); cv2.line(m1, q(p0), q(p1), 255, tol + 3, cv2.LINE_AA, 4)
        m2 = np.zeros((H, W), np.uint8); cv2.line(m2, q(p0), q(p1), 255, tol, cv2.LINE_AA, 4)
        a1 = (m1.astype(np.float32) / 255 * a * .45)[..., None]; s.o = s.o * (1 - a1)
        a2 = (m2.astype(np.float32) / 255 * a)[..., None]; s.o = s.o * (1 - a2) + np.array(TERR, np.float32) / 255 * a2
    def strelka(s, p0, p1, a):           # line with an arrowhead
        s.liniya(p0, p1, a, 4)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L_ = math.hypot(dx, dy) or 1; ux, uy = dx / L_, dy / L_
        tri = [p1, (p1[0] - ux * 22 - uy * 11, p1[1] - uy * 22 + ux * 11), (p1[0] - ux * 22 + uy * 11, p1[1] - uy * 22 - ux * 11)]
        m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array([[int(x * 16), int(y * 16)] for x, y in tri], np.int32)], 255, cv2.LINE_AA, 4)
        al = (m.astype(np.float32) / 255 * a)[..., None]; s.o = s.o * (1 - al) + np.array(TERR, np.float32) / 255 * al
    def marker(s, x, y, a, t, r=12, puls=True):  # ring + dot + glow + soft pulse
        if a <= .01: return
        q = lambda v: int(round(v * 16))
        gl = np.zeros((H, W), np.uint8); cv2.circle(gl, (q(x), q(y)), q(r * 1.5), 255, -1, cv2.LINE_AA, 4)
        g = cv2.GaussianBlur(gl, (0, 0), r * .9).astype(np.float32)[..., None] / 255 * .45 * a
        s.o = s.o + g * (np.array(TERR, np.float32) / 255 - s.o) * .9
        if puls:
            u = (t * .55) % 1.0; rr = r + 26 * evo(u)
            mp = np.zeros((H, W), np.uint8); cv2.circle(mp, (q(x), q(y)), q(rr), 255, 2, cv2.LINE_AA, 4)
            ap = (mp.astype(np.float32) / 255 * a * .7 * (1 - u))[..., None]; s.o = s.o * (1 - ap) + np.array(TERR, np.float32) / 255 * ap
        mo = np.zeros((H, W), np.uint8); cv2.circle(mo, (q(x), q(y)), q(r), 255, 6, cv2.LINE_AA, 4)
        s.o = s.o * (1 - (mo.astype(np.float32) / 255 * a * .4)[..., None])
        mr = np.zeros((H, W), np.uint8); cv2.circle(mr, (q(x), q(y)), q(r), 255, 3, cv2.LINE_AA, 4); cv2.circle(mr, (q(x), q(y)), q(r * .33), 255, -1, cv2.LINE_AA, 4)
        ar = (mr.astype(np.float32) / 255 * a)[..., None]; s.o = s.o * (1 - ar) + np.array((255, 236, 220), np.float32) / 255 * ar * .35 + np.array(TERR, np.float32) / 255 * ar * .65

def krai(bx, by, bw, bh, px, py):        # point on the rectangle edge nearest to the target
    if px > bx + bw: ax = bx + bw
    elif px < bx: ax = bx
    else: ax = bx + bw / 2
    if px > bx + bw or px < bx: ay = cl(py, by + 20, by + bh - 20)
    else: ay = by + bh if py > by + bh else by
    return ax, ay

# -- graphics on the clip timeline
# karta: a fixed card + a line to the point; metka: a 'pill' next to the point (moves with it) + a short line; strelka: a direction arrow
# times a, b are counted from the START OF THEIR OWN SCENE (seconds); every caption stays up for at least ~4 s
EL = [
    dict(tip='karta', sc='A', pt=None, tit='ВОРОНЕЖСКАЯ ОБЛАСТЬ', sub='берег Дона', a=6.4, b=11.3, mesto='auto'),
    dict(tip='metka', sc='A', pt='moskva', txt='Москва', a=7.2, b=11.2, off=(115, -40)),
    dict(tip='karta', sc='B', pt=None, tit='КОСТЁНКИ', sub='здесь люди жили много тысяч лет', a=2.0, b=8.0, mesto=(110, 150)),
    dict(tip='metka', sc='B', pt='don', txt='зимой Дон замерзал', a=4.0, b=10.6, off=(-200, -90)),
    dict(tip='metka', sc='B', pt='balka', txt='стоянки \u2014 у оврагов', a=5.4, b=10.6, off='auto'),
    dict(tip='karta', sc='S', pt=None, tit='КАК УЗНАЛИ ВОЗРАСТ НАХОДОК?', sub='чем глубже слой, тем он древнее', a=.6, b=7.6, mesto=(110, 120), bez_linii=True),
    dict(tip='metka', sc='S', pt='pochva', txt='сверху \u2014 наши дни', a=.8, b=4.4, off=(-330, 0)),
    dict(tip='metka', sc='S', pt='less', txt='пыль, принесённая ветром', a='avto', b='avto', off=(-330, 0)),
    dict(tip='metka', sc='S', pt='sloy1', txt='около 26 000 лет назад', a='avto', b='avto', off=(-330, 0)),
    dict(tip='metka', sc='S', pt='sloy2', txt='около 33 000 лет назад', a='avto', b='avto', off=(-330, 0)),
    dict(tip='metka', sc='S', pt='pepel', txt='пепел вулкана из Италии', a='avto', b='avto', off=(-330, 0)),
    dict(tip='karta', sc='S', pt=None, tit='ПЕПЛУ \u2014 ОКОЛО 40 000 ЛЕТ', sub='всё, что под ним, ещё древнее', a=12.4, b=18.6, mesto=(110, 120), bez_linii=True),
    dict(tip='metka', sc='S', pt='sloy4a', txt='кости лошадей', a='avto', b='avto', off=(-330, 0)),
    dict(tip='metka', sc='S', pt='sloy4b', txt='самые древние очаги \u2014 около 45 000 лет назад', a='avto', b='avto', off=(-330, 0)),
    dict(tip='karta', sc='C', pt='zhilishche', tit='ЖИЛИЩЕ ИЗ КОСТЕЙ МАМОНТА', sub='так оно могло выглядеть', a=.6, b=6.4, mesto=(110, 150)),
    dict(tip='metka', sc='C', pt='cherep', txt='черепа мамонтов', a=2.4, b=10.4, off=(-230, 70)),
    dict(tip='metka', sc='C', pt='bivni', txt='бивни мамонтов', a=3.4, b=10.4, off=(150, -40)),
    dict(tip='metka', sc='C', pt='don', txt='Дон', a=5.0, b=10.4, off=(-40, -90)),
    dict(tip='karta', sc='H', pt=None, tit='КАК УСТРОЕНО ЖИЛИЩЕ', sub='круг из костей шириной 9 метров', a=.6, b=7.0, mesto=(110, 150), bez_linii=True),
    dict(tip='metka', sc='H', pt='cherep', txt='черепа \u2014 основание стены', a=6.6, b=11.4, off='auto'),
    dict(tip='metka', sc='H', pt='stolb', txt='длинные кости \u2014 столбы', a=7.4, b=12.0, off='auto'),
    dict(tip='metka', sc='H', pt='chel6', txt='челюсти укрепляли стену', a=8.2, b=12.8, off='auto'),
    dict(tip='metka', sc='H', pt='ochag', txt='очаг', a=10.6, b=19.4, off=(-200, -30)),
    dict(tip='karta', sc='H', pt='krysha', tit='КРЫША ИЗ ШКУР', sub='её не нашли \u2014 так думают учёные', a=12.0, b=19.6, mesto=(1290, 150)),
    dict(tip='karta', sc='D1', pt=None, tit='ОРУДИЯ ИЗ БИВНЯ, КОСТИ И КРЕМНЯ', sub='', a=.5, b=7.0, mesto=(110, 900), bez_linii=True),
    dict(tip='metka', sc='D1', pt='orudiya', txt='наконечник копья', a=1.0, b=7.0, off=(-120, -110)),
    dict(tip='metka', sc='D1', pt='igla', txt='игла с ушком', a=1.6, b=7.0, off=(40, -150)),
    dict(tip='metka', sc='D1', pt='shilo', txt='шило', a=2.2, b=7.0, off=(120, -60)),
    dict(tip='metka', sc='D1', pt='kremen', txt='кремнёвый наконечник', a=2.8, b=7.0, off=(40, 120)),
    dict(tip='karta', sc='D1', pt=None, tit='УКРАШЕНИЯ ИЗ БИВНЯ И КОСТИ', sub='', a=7.2, b=11.6, mesto=(110, 900), bez_linii=True),
    dict(tip='metka', sc='D1', pt='busy', txt='бусы', a=7.8, b=11.6, off=(130, -120)),
    dict(tip='metka', sc='D1', pt='podveski', txt='подвески', a=8.4, b=11.6, off=(170, 60)),
    dict(tip='karta', sc='D2', pt=None, tit='ЖЕНСКАЯ ФИГУРКА\nИЗ БИВНЯ МАМОНТА', sub='вырезана больше\n21 000 лет назад', a=.7, b=7.0, mesto=(1290, 300), bez_linii=True),
    dict(tip='metka', sc='D2', pt='golova', txt='лицо не вырезано', a=6.8, b=10.8, off=(230, -10)),
    dict(tip='metka', sc='D2', pt='poyas', txt='плетёный пояс', a=7.6, b=10.8, off=(250, 20)),
    dict(tip='karta', sc='D2', pt=None, tit='ТАКИЕ ФИГУРКИ ХРАНЯТСЯ', sub='в музеях Петербурга', a=10.8, b=16.4, mesto=(1290, 300), bez_linii=True),
    dict(tip='karta', sc='E', pt=None, tit='МУЗЕЙ-ЗАПОВЕДНИК «КОСТЁНКИ»', sub='здесь раскопали больше 20 стоянок', a=1.5, b=7.6, mesto='auto'),
    dict(tip='metka', sc='E', pt='don', txt='Дон', a=2.5, b=14.3, off='auto'),
    dict(tip='metka', sc='E', pt='selo', txt='село Костёнки', a=3.3, b=14.3, off='auto'),
    dict(tip='strelka', sc='E', pt=None, k='sever', txt='до Воронежа 35 км', a=4.6, b=14.3),
    dict(tip='karta', sc='E', pt=None, tit='МУЗЕЙ ПОСТРОЕН НАД ЖИЛИЩЕМ', sub='внутри \u2014 те самые кости мамонтов', a=8.0, b=14.3, mesto='auto'),
]
NAKLEYKI = [('B', 'около 45 000 лет назад · ледниковый период', 1.0, 10.8), ('C', 'намного позже · около 24 000 лет назад', .5, 10.6),
            ('H', 'намного позже · около 24 000 лет назад', 0.0, 19.6), ('E', 'сегодня', .7, 14.6)]
def _avto_okno(sc_, pt_):                 # when a layer point is in frame (the camera descends), with a margin at the edges
    j = M[sc_]['kadry']; vis = [1 + int(k) for k in range(len(j)) if 120 < j[str(k + 1)][pt_][1] < 960]
    if not vis: return 99, 99
    a_, b_ = (vis[0] - 1) / FPS + .3, (vis[-1] - 1) / FPS - .3
    return a_, b_
for e in EL:   # convert to clip time
    if e['sc'] not in T0: continue
    if e['a'] == 'avto':
        if e['sc'] in M: e['a'], e['b'] = _avto_okno(e['sc'], e['pt'])
        else: e['a'], e['b'] = 99, 99
    e['a'] += T0[e['sc']]; e['b'] += T0[e['sc']]
NAKLEYKI = [(s_, txt, a + T0[s_], b + T0[s_]) for s_, txt, a, b in NAKLEYKI]
METKA_SC = {'C': 'иллюстрация', 'D1': 'иллюстрация', 'D2': 'иллюстрация', 'S': 'схема по данным раскопок', 'H': 'реконструкция по данным раскопок'}
ILL = ['C', 'D1', 'D2']
_avto = {}
def avto_off(e):                         # the 'pill' goes away from the frame centre; computed once, at mid-show
    key = id(e)
    if key in _avto: return _avto[key]
    tm = (e['a'] + e['b']) / 2; x, y, _ = tochka(e['sc'], e['pt'], nomer(e['sc'], tm))
    dx, dy = x - W / 2, y - H / 2 - 120; L_ = math.hypot(dx, dy) or 1
    _avto[key] = (dx / L_ * 120, dy / L_ * 90 - 30); return _avto[key]

def oformlenie(h, t, sloi):
    vidno = {x[0]: x[4] for x in sloi}
    for e in EL:
        a = okno(t, e['a'], e['b'], .9)
        if a <= .01 or e['sc'] not in vidno: continue
        ns = vidno[e['sc']]
        px, py, vis = (0, 0, 0) if e.get('bez_linii') else tochka(e['sc'], e.get('pt'), ns)
        p_lin = smt((t - e['a'] - .45) / .9)                          # the line draws itself smoothly
        if e['tip'] == 'karta':
            spr, m = plashka(e['tit'], e['sub']); bh, bw = m.shape
            if e['mesto'] == 'auto' and not e.get('bez_linii'):
                mx_, my_, _ = tochka(e['sc'], e.get('pt'), nomer(e['sc'], (e['a'] + e['b']) / 2))
                bx = mx_ - 170 - bw if mx_ > W / 2 else mx_ + 170; by = cl(my_ - 230, 120, H - bh - 170)
            else: bx, by = e['mesto']
            bx, by = cl(bx, 96, W - bw - 96), cl(by, 60, H - bh - 60)
            vyezd = (1 - smt((t - e['a']) / 1.1)) * 26               # the card slides in softly
            bx += -vyezd if px > bx + bw / 2 else vyezd
            h.steklo(sdvig(m, bx, by), a); h.spr(sdvig(spr, bx, by), a)
            if vis:
                ax, ay = krai(bx, by, bw, bh, px, py); dx, dy = px - ax, py - ay; dn = math.hypot(dx, dy) or 1
                ex, ey = px - dx / dn * 18, py - dy / dn * 18
                h.liniya((ax, ay), (ax + (ex - ax) * p_lin, ay + (ey - ay) * p_lin), a)
                if not (e['sc'] in ('A', 'B', 'E') and e.get('pt') is None):   # Kostenki has its own permanent marker
                    h.marker(px, py, a * smt((t - e['a'] - 1.1) / .6), t)
        elif e['tip'] == 'metka':
            if not vis: continue
            a *= smt((py + 20) / 140) * smt((H + 20 - py) / 140) * smt((px + 20) / 140) * smt((W + 20 - px) / 140)   # fades out smoothly near the frame edge
            if a <= .01: continue
            spr, m = tabletka(e['txt']); bh, bw = m.shape
            ox, oy = avto_off(e) if e['off'] == 'auto' else e['off']
            cx, cy = px + ox, py + oy; bx, by = cl(cx - bw / 2, 96, W - bw - 96), cl(cy - bh / 2, 54, H - bh - 54)
            h.marker(px, py, a * smt((t - e['a']) / .6), t, r=8, puls=False)
            ax, ay = krai(bx, by, bw, bh, px, py); dx, dy = px - ax, py - ay; dn = math.hypot(dx, dy) or 1
            if dn > 24: h.liniya((ax, ay), (ax + (px - dx / dn * 12 - ax) * p_lin, ay + (py - dy / dn * 12 - ay) * p_lin), a, 2)
            a_t = a * smt((t - e['a'] - .5) / .8)
            h.steklo(sdvig(m, bx, by), a_t); h.spr(sdvig(spr, bx, by), a_t)
        elif e['tip'] == 'strelka':
            qx, qy, qv = tochka(e['sc'], e['k'], ns)
            dx, dy = qx - px, qy - py; dn = math.hypot(dx, dy) or 1; ux, uy = dx / dn, dy / dn
            p0 = (px + ux * 40, py + uy * 40); L_ = 230 * smt((t - e['a']) / 1.1); p1 = (p0[0] + ux * L_, p0[1] + uy * L_)
            h.strelka(p0, p1, a)
            spr, m = tabletka(e['txt']); bh, bw = m.shape
            bx, by = cl(p1[0] + ux * 30 - bw / 2 + (bw / 2 + 10) * np.sign(ux), 30, W - bw - 30), cl(p1[1] + uy * 30 - bh / 2, 30, H - bh - 30)
            a_t = a * smt((t - e['a'] - .8) / .8); h.steklo(sdvig(m, bx, by), a_t); h.spr(sdvig(spr, bx, by), a_t)

def kadr(n):
    t = (n - 1) / FPS
    akt = [(s, t0, d) for s, t0, d in SCENY if t0 <= t < t0 + d + 1e-6] or [SCENY[-1]]
    sloi = []
    for s, t0, d in akt:
        a, ns = kadr_sceny(s, t - t0); sloi.append((s, t0, d, a, ns))
    out = sloi[0][3]; ves = [1.0]
    if len(sloi) > 1:
        (s1, t1, d1, a1, n1), (s2, t2, d2, a2, n2) = sloi[0], sloi[1]
        u = sgl(cl((t - t2) / (t1 + d1 - t2)))
        if s1 == 'A':
            kx, ky, _ = tochka('A', None, n1)
            a1 = masshtab(a1, 1 + 2.2 * u, kx, ky); a2 = masshtab(a2, .82 + .18 * u, W / 2, H / 2)
        out = a1 * (1 - u) + a2 * u; ves = [1 - u, u]
    else: out = out.copy()
    sn = 0.0
    for (s, t0, d, a, ns), v in zip(sloi, ves):
        tr = t - t0
        if s == 'B': sn += .45 * v
        if s == 'C':
            ox, oy, _ = tochka('C', 'ogon', ns); mig = .20 + .08 * math.sin(tr * 9.1) + .05 * math.sin(tr * 23.7 + 1.3)
            out = svet_pyatno(out, ox, oy, 70, mig * v, (1.0, .55, .2)); sn += .55 * v
        if s == 'D2': out = svet_pyatno(out, 760 + 420 * cl(tr / 16.8), 430, 260, .05 * v, (1.0, .85, .6))
    out = np.clip(sneg(out, t, sn) * VIN, 0, 1)
    h = Holst(out)
    # Kostenki marker on the globe and in the valleys: always on while the point is in frame (replaces the 3D ring)
    for s, t0, d, a, ns in sloi:
        if s in ('A', 'B', 'E'):
            x, y, vis = tochka(s, None, ns)
            ap = {'A': okno(t, 6.0, 999), 'B': okno(t, T0['B'] + 1.0, 999), 'E': okno(t, T0['E'] + .4, 999)}[s]
            if vis and ap > .01 and -40 < x < W + 40 and -40 < y < H + 40: h.marker(x, y, ap * (1 if s != 'A' or len(sloi) == 1 else ves[0]), t, r=13)
    oformlenie(h, t, sloi)
    o = np.clip(h.o, 0, 1)
    img = Image.fromarray((o * 255 + .5).astype(np.uint8)).convert('RGBA')
    sl = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(sl)
    at = okno(t, .7, 6.3, 1.0)
    if at > .01:
        razryad(d, (120 * SS, 400 * SS), 'ДРЕВНЕЙШИЕ ЛЮДИ', F['eyb'], (*ZOL, int(255 * at)), 6)
        for i, s_ in enumerate(('Костёнки:', 'охотники', 'на мамонтов')):
            d.text((112 * SS, (512 + 104 * i) * SS), s_, font=F['tit'], fill=(*KREM, int(255 * at)), anchor='ls')
    for s, txt, a0, a1_ in NAKLEYKI:
        a = okno(t, a0, a1_)
        if a > .01:
            T_ = txt.upper(); w = shirina(T_, F['bdg'], 3) / SS + 44
            d.rounded_rectangle([96 * SS, 70 * SS, (96 + w) * SS, 118 * SS], radius=8 * SS, fill=(10, 18, 22, int(200 * a)))
            d.rounded_rectangle([96 * SS, 70 * SS, (100) * SS, 118 * SS], radius=2 * SS, fill=(*ZOL, int(235 * a)))
            razryad(d, (118 * SS, 104 * SS), T_, F['bdg'], (*KREM, int(255 * a)), 3)
    for s_, t0_, d_ in SCENY:
        if s_ in METKA_SC:
            ai = okno(t, t0_ + .3, t0_ + d_ - .3)
            if ai > .01:
                tw_ = F['ill'].getlength(METKA_SC[s_]) / SS
                d.rounded_rectangle([(W - 96 - tw_ - 18) * SS, (H - 86) * SS, (W - 96 + 18) * SS, (H - 40) * SS], radius=10 * SS, fill=(10, 18, 22, int(150 * ai)))
                d.text(((W - 96) * SS, (H - 52) * SS), METKA_SC[s_], font=F['ill'], fill=(*KREM, int(225 * ai)), anchor='rs')
    ak = max([okno(t, x[1] + .3, x[1] + x[2] - .3) for x in SCENY if x[0] == 'E'] + [0])
    if ak > .01: d.text(((W - 60) * SS, (H - 44) * SS), 'Contains modified Copernicus Sentinel data 2025', font=F['kop'], fill=(*KREM, int(140 * ak)), anchor='rs')
    sl = sl.resize((W, H), Image.LANCZOS)
    img = Image.alpha_composite(img, sl).convert('RGB')
    fade = sgl(cl(t / .8)) * sgl(cl((DLIT - t) / .9))
    Image.fromarray((np.asarray(img).astype(np.float32) * fade).astype(np.uint8)).save(f'{OUT}/{n:04d}.jpg', quality=95)

if ARG == 'vse': spisok = range(1, NF + 1)
elif '-' in ARG and ',' not in ARG: a, b = map(int, ARG.split('-')); spisok = range(a, min(NF, b) + 1)
else: spisok = [int(x) for x in ARG.split(',')]
for n in spisok: kadr(n)
print('ok', len(list(spisok)), 'frames of', NF)
