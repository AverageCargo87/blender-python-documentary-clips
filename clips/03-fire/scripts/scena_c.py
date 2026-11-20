# Clip 3 'Fire', scene C: the cave near Beijing. A large dark hall, the floor shown in section like a museum diorama.
# Deposits grow from 0.6 to 6 m; campfires light up and die out at different spots on the surface, and each one leaves
# a hearth lens in the section (red baked earth at the bottom, black charcoal above, grey-white ash on top). At the end a person stands at the foot for scale.
# EEVEE, 24 fps, 14 s = 336 frames. All motion comes from the function postavit(n) (only the flame strength has keys, set by koster_petlya),
# so frames can be rendered in any order.
#   blender -b --factory-startup --python scena_c.py -- <root> <vse|frames 1,60,100-110|metki> [--proba] [--kesh=name] [--proc=100]
#           [--shag=.007] [--red=1] [--sempl=48] [--osmotr=x,z,d] [--suho]
#   --proba: half size and a coarser mesh, frames to kadry/C-proba; --osmotr: close-up of the section (pattern check); --suho: no render
import sys, os, json, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, REZHIM = A[0], A[1]; PROBA = '--proba' in A
def _arg(imya, um=None):
    v = [a.split('=', 1)[1] for a in A if a.startswith(f'--{imya}=')]; return v[0] if v else um
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
from kamni import *
import kamni
from iskry import Iskry
from bpy_extras.object_utils import world_to_camera_view

# ========= tuning knobs
FPS = 24; DLIT = 14.0; NF = int(DLIT * FPS)
T_ROST = (2.2, 9.5)                      # deposits grow during this interval, s
T_CHEL = (10.2, 11.6)                    # the person fades in
W_, D_ = 7.0, 3.8                        # section width and block depth, m
H0, H1 = .6, 6.0                         # section height at the start and at the end, m
SHAG = float(_arg('shag', .007))         # mesh step of the front face, m (the section pattern is always computed at this step)
RED = int(_arg('red', 2 if PROBA else 1))                # mesh decimation in preview (the pattern stays the same, fewer vertices)
# hearth lenses: (centre x, top height, length, thickness). A fire burns above its lens when the surface reaches the lens top
LINZY = [(-.7, .60, 1.9, .20), (1.0, 1.02, 1.3, .16), (-2.3, 1.42, 1.5, .18), (.5, 1.88, 2.2, .25), (2.5, 2.30, 1.1, .15),
         (-1.4, 2.72, 1.7, .20), (1.3, 3.12, .9, .14), (-2.6, 3.50, 1.2, .17), (-.2, 3.92, 2.0, .22), (2.2, 4.32, 1.5, .18),
         (-1.9, 4.72, .8, .14), (1.0, 5.10, 1.8, .20), (-2.4, 5.50, 1.3, .16), (-.3, 6.00, 1.7, .18)]
I_METKA = 3                              # lens for the 'ash and charcoal' label (marker linza)
# earth layers from bottom to top: (thickness, colour)
SLOI = [(.50, '#8a693d'), (.42, '#774a31'), (.66, '#967846'), (.40, '#694a33'), (.62, '#87593a'), (.50, '#9a7f50'),
        (.72, '#784f34'), (.46, '#8b6d45'), (.58, '#6e4a31'), (.52, '#947446'), (.80, '#7f573a')]
CV_IZV = ('#9d9a90', '#b6b2a6', '#c8c4b8', '#aba79b', '#86837a')        # limestone blocks
CV_PROKAL, CV_UGOL, CV_ZOLA = '#9c3e27', '#131110', '#c2beb3'           # the three layers of a lens
# campfires
ZHIZN, NARAST, SPAD = .9, .6, .8        # lifetime of a fire in accelerated time, flare-up and die-down, s
RELE = [0, 3, 5, 8, 11, 13]             # v3 fix: fires above these lenses burn as a relay (the fire never disappears); no fire is shown above the other lenses
Y_OGNYA = 1.05                           # inset of the fires from the section edge, m
MASH_OGNYA = (1.35, 1.6)                 # scale of the fire volume (from, to); the first and last fires use MASH_GL
MASH_GL = 1.6
SHIR_OGNYA, VYS_OGNYA = 1.25, .9         # flame proportions: wider and lower than in the cache (a campfire, not a torch)
S_OGNYA, DYM = 34., .5                   # flame emission and smoke density (nodes sila and dym)
S_SVET, S_DAL, S_STEK = 260., 2000., 320.   # fire light: onto the block lid, onto the hall, a warm spill down the section, W
S_OREOL = .32                            # soft glow around the flame (a camera-facing card); 0 = off
S_ZHAR = 2.2                             # smouldering of the charcoal band in the section right below the surface; 0 = off
CV_OGNYA = (1.0, .55, .23)
Y_STEK, Z_STEK = 1.5, .45                # where the spill light hangs: in front of the section and above the edge, m
# general light on the section (cold, so the layers read)
S_KLYUCH, K_KLYUCH0, S_BOK = 9000., .3, 900.         # spotlight strength; its share at the scene start (while the hall is lit by a single fire)
CV_KLYUCH = (.80, .88, 1.0)
S_ZAL = .16                              # cold diffuse hall light from above (as if through a hole in the vault), W/m^2
FON = ((.010, .014, .024), .5)           # ambient colour and strength
# camera: two steady motions (start and end) with a smooth blend between them. kurs: turn left from 'straight at the section', deg;
# tangazh: pitch, deg; sx, sy: frame shift (a shift lens, so the section verticals stay vertical)
KAM_A = dict(p=(3.4, -15.0, 3.0), v=(-.05, .24, .02), kurs=13., tangazh=-2.5, sx=0., sy=0., lens=35.)
KAM_B = dict(p=(6.9, -17.2, 9.4), v=(-.067, .222, -.044), kurs=8., tangazh=0., sx=-.14, sy=-.325, lens=35.)   # p is the pose at T_ROST[1]
T_KAM = (1.9, 9.9)
X_CH, Y_CH, POV_CH = 2.25, -.6, .24      # the person: position and card rotation towards the camera
OSM = _arg('osmotr')                     # close inspection of the section: x,z,d puts the camera opposite point (x, z) at distance d, section fully open
PROC = int(_arg('proc', 50 if PROBA else 100))
SUHO = '--suho' in A                     # run through the frames without rendering (checks that postavit never fails on any frame)

def sm(u): u = max(0., min(1., u)); return u * u * (3 - 2 * u)
def sm5(u): u = max(0., min(1., u)); return u * u * u * (u * (6 * u - 15) + 10)
def gl(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)
def h_t(t): return H0 + (H1 - H0) * sm((t - T_ROST[0]) / (T_ROST[1] - T_ROST[0]))
_tt = np.linspace(T_ROST[0], T_ROST[1], 4000); _hh = np.array([h_t(t) for t in _tt])
def t_ot_h(z): return float(np.interp(z, _hh, _tt))

# -- campfire schedule
KESH = _arg('kesh') or 'koster'
KD = f'{ROOT}/sim/{KESH}'
_r = np.random.default_rng(5); OGNI = []
for i, (x, zt, dl, tol) in enumerate(LINZY):
    if i == 0: ta, tb = -9., 3.75
    elif i == len(LINZY) - 1: ta, tb = t_ot_h(zt - tol), DLIT + 9
    else: ta = t_ot_h(zt - tol * .8) - .05; tb = ta + ZHIZN
    OGNI.append(dict(x=x, y=Y_OGNYA + float(_r.uniform(-.2, .25)), ta=ta, tb=tb, povorot=(i % 4) * math.pi / 2,
                     mash=MASH_GL if i in (0, len(LINZY) - 1) else float(_r.uniform(*MASH_OGNYA))))
# v3 fix ('the fires kept disappearing'): a relay, the next fire flares up while the previous one burns and only then does that one die
for i, og in enumerate(OGNI): og['gorit'] = i in RELE
for k_, i in enumerate(RELE[1:], 1): OGNI[i]['ta'] = t_ot_h(LINZY[i][1] - LINZY[i][3]) - .35
for k_, i in enumerate(RELE[:-1]): OGNI[i]['tb'] = OGNI[RELE[k_ + 1]]['ta'] + NARAST + SPAD + .25
def sila_ognya(i, t):
    o = OGNI[i]
    if not o['gorit']: return 0.
    return sm((t - o['ta']) / NARAST) * (1 - sm((t - (o['tb'] - SPAD)) / SPAD))
def a_chel(t): return sm((t - T_CHEL[0]) / (T_CHEL[1] - T_CHEL[0]))
MAKUSHKA = (X_CH + .136 * math.cos(POV_CH), Y_CH + .136 * math.sin(POV_CH), 1.69)

# -- camera
def kam_t(t):
    if OSM:
        x, z, d = (float(v) for v in OSM.split(',')); return np.array([x, -d, z]), 0., 0., 0., 0., 35.
    w = sm5((t - T_KAM[0]) / (T_KAM[1] - T_KAM[0]))
    pa = np.array(KAM_A['p']) + np.array(KAM_A['v']) * t; pb = np.array(KAM_B['p']) + np.array(KAM_B['v']) * (t - T_ROST[1])
    f = lambda k: KAM_A[k] * (1 - w) + KAM_B[k] * w
    return pa * (1 - w) + pb * w, f('kurs'), f('tangazh'), f('sx'), f('sy'), f('lens')

ochistit()
sc = dvizhok('EEVEE', w=1920, h=1080, proc=PROC, samples=int(_arg('sempl', 16 if PROBA else 48)), nf=NF)
kam = kamera(lens=35)
try: sc.eevee.shadow_pool_size = '1024'
except Exception as e: print('eevee: shadow buffer', e)
def postavit_kameru(t):
    p, kurs, tang, sx, sy, lens = kam_t(t)
    kam.location = p; kam.rotation_euler = (math.radians(90 + tang), 0, math.radians(kurs))
    kam.data.shift_x = sx; kam.data.shift_y = sy; kam.data.lens = lens
def proj(v):
    c = world_to_camera_view(sc, kam, Vector(v)); return [round(c.x, 4), round(1 - c.y, 4), round(c.z, 3)]

# ========= label points for the edit (screen fractions: x from the left, y from the top; third value is distance from the camera, m)
def metki_kadra(n):
    t = (n - 1) / FPS; h = h_t(t); postavit_kameru(t); bpy.context.view_layer.update()
    xl, zl, dl, tol = LINZY[I_METKA]
    ves = [sila_ognya(i, t) for i in range(len(OGNI))]; ia = max(range(len(OGNI)), key=lambda i: (round(ves[i], 2), i))
    return dict(niz=proj((W_ / 2, 0, 0)), verh=proj((W_ / 2, 0, h)), h=round(h, 3), linza=proj((xl, 0, zl - tol * .5)), linza_vidna=bool(h >= zl),
                ogon=proj((OGNI[ia]['x'], OGNI[ia]['y'], h)), ogon_n=ia, chelovek=proj(MAKUSHKA), chelovek_a=round(a_chel(t), 3))
if REZHIM in ('vse', 'metki') and not OSM:
    M = dict(fps=FPS, dlit=DLIT, t=dict(rost=T_ROST, chelovek=T_CHEL), shirina=W_, vysota=(H0, H1),
             linzy=[dict(x=l[0], verh=l[1], dlina=l[2], tolshchina=l[3], t=round(OGNI[i]['ta'], 2)) for i, l in enumerate(LINZY)],
             kadry=[metki_kadra(n) for n in range(1, NF + 1)])
    json.dump(M, open(f'{ROOT}/metki-C.json', 'w'))
    for n in (1, 30, 53, 80, 110, 140, 170, 200, 229, 280, 336):      # framing check: bottom/top at the section edges and the flame top
        t = (n - 1) / FPS; h = h_t(t); d = M['kadry'][n - 1]; o = OGNI[d['ogon_n']]; postavit_kameru(t); bpy.context.view_layer.update()
        print(f"frame {n:3d} h={h:.2f} cam.z={kam_t(t)[0][2]:.2f} left.bottom={proj((-W_ / 2, 0, 0))[:2]} left.top={proj((-W_ / 2, 0, h))[:2]} "
              f"right.bottom={d['niz'][:2]} right.top={d['verh'][:2]} flame={proj((o['x'], o['y'], h + 1.25 * o['mash']))[:2]} person={d['chelovek'][:2]}")
    if REZHIM == 'metki': sys.exit(0)

# ========= noises independent of the mesh step (preview and final render get the same pattern)
def n1(seed, u, shag=1.0):
    r = np.random.default_rng(1000 + seed); T = r.standard_normal(256)
    a = np.asarray(u, float) / shag + 128.3; i = np.floor(a).astype(int); f = a - i; f = f * f * (3 - 2 * f)
    return T[i % 256] * (1 - f) + T[(i + 1) % 256] * f
def vshum(us, vs, yach, seed, okt=1, umen=.55):
    """Smooth noise on a us x vs grid (both regular 1D), blob size yach m. -> (len(vs), len(us)), std ~ 1."""
    out = 0.; amp = 1.; tot = 0.
    for o in range(okt):
        c = yach / 2.03 ** o; r = np.random.default_rng(seed * 131 + o)
        a = (us - us[0]) / c + r.uniform(0, 1); b = (vs - vs[0]) / c + r.uniform(0, 1)
        T = r.standard_normal((int((vs[-1] - vs[0]) / c) + 4, int((us[-1] - us[0]) / c) + 4)).astype(np.float32)
        ia = a.astype(int); fa = (a - ia).astype(np.float32); ib = b.astype(int); fb = (b - ib).astype(np.float32)
        fa = (fa * fa * (3 - 2 * fa))[None, :]; fb = (fb * fb * (3 - 2 * fb))[:, None]
        Tb0, Tb1 = T[ib], T[ib + 1]
        out = out + amp * ((Tb0[:, ia] * (1 - fa) + Tb0[:, ia + 1] * fa) * (1 - fb) + (Tb1[:, ia] * (1 - fa) + Tb1[:, ia + 1] * fa) * fb)
        tot += amp * amp; amp *= umen
    return (out / (tot ** .5 * .743)).astype(np.float32)

# ========= face pattern: per-vertex colour and real relief
def okno(us, vs, cu, cv, ru, rv):
    i0, i1 = np.searchsorted(us, [cu - ru, cu + ru]); j0, j1 = np.searchsorted(vs, [cv - rv, cv + rv]); return i0, i1, j0, j1

def narisovat_bloki(us, vs, col, disp, zan, n, seed, f_ml, f_zr, krupnyh=6, vys=1.0, plosk=True, razm=.22):
    """Angular limestone blocks: convex polygons with chips, protruding from the face. zan: what is already occupied (lenses, other blocks)."""
    r = np.random.default_rng(seed); du = us[1] - us[0]; gotovo = popytok = 0
    cv_ = [np.array(L(c), np.float32) for c in CV_IZV]
    while gotovo < n and popytok < n * 40:
        popytok += 1
        R = r.uniform(.27, .5) if gotovo < krupnyh else .05 + razm * r.uniform() ** 2.2          # half size, m
        au = R * r.uniform(1.0, 1.45); av = R * (r.uniform(.5, .85) if plosk else r.uniform(.7, 1.0)); th = r.normal(0, .3) if plosk else r.uniform(0, 3.14)
        cu = r.uniform(us[0] + au * .7, us[-1] - au * .7); cv = r.uniform(vs[0] + av * .5, vs[-1] - av * .5)
        i0, i1, j0, j1 = okno(us, vs, cu, cv, au * 1.25 + .04, au * 1.25 + .04)
        if i1 - i0 < 3 or j1 - j0 < 3: continue
        U = us[i0:i1][None, :] - cu; V = vs[j0:j1][:, None] - cv; c, s = math.cos(th), math.sin(th)
        p = (U * c + V * s) / au; q = (-U * s + V * c) / av
        m = int(r.integers(4, 7)); fi = (np.arange(m) + r.uniform(-.3, .3, m)) * 2 * math.pi / m + r.uniform(0, 6.28); ro = r.uniform(.62, 1.0, m)
        d = np.full(p.shape, 9., np.float32)
        for k in range(m): d = np.minimum(d, ro[k] - (p * math.cos(fi[k]) + q * math.sin(fi[k])))
        d = d * min(au, av)                                                                     # ~ distance to the block edge, m
        w = (slice(j0, j1), slice(i0, i1))
        if (zan[w] & (d > -.03)).any(): continue
        zan[w] |= d > -.025
        gran = 1 + .12 * (p * r.normal() + q * r.normal()); vyst = 1.0
        if R > .1 and r.uniform() < .65:                                                        # a chip: the second facet is darker and lower
            ps = r.uniform(0, 6.28); skol = (p * math.cos(ps) + q * math.sin(ps)) > r.uniform(-.3, .3)
            gran = gran * np.where(skol, r.uniform(.8, .92), 1.0); vyst = np.where(skol, r.uniform(.45, .75), 1.0)
        tek = gran * (1 + .05 * f_zr[w] + .06 * f_ml[w]) * (1 - .16 * np.exp(-np.maximum(d, 0) / .025))
        c_ = cv_[int(r.integers(len(cv_)))] * r.uniform(.86, 1.08)
        mk = np.clip(d / (1.3 * du) + .5, 0, 1)
        kayma = np.exp(-(np.minimum(d, 0) / .014) ** 2) * (d < 0)                               # dark gap around the block
        cw = col[w] * (1 - .42 * kayma[..., None])
        col[w] = cw * (1 - mk[..., None]) + c_[None, None] * tek[..., None] * mk[..., None]
        faska = np.clip(d / (.22 * min(au, av) + .008), 0, 1) ** .6
        vysota = vys * (.012 + .10 * R) * faska * vyst * (1 + .3 * (p * r.normal() + q * r.normal()))
        disp[w] = disp[w] * (1 - mk) + vysota * mk
        gotovo += 1
    return gotovo

def narisovat_linzy(us, vs, col, disp, zan, ugol, f_sr, f_ml, f_zr, linzy):
    """Hearth lenses: brick-red baked earth at the bottom, a black charcoal band above, grey-white ash on top."""
    KR, CH, ZO = (np.array(L(c), np.float32) for c in (CV_PROKAL, CV_UGOL, CV_ZOLA)); dv = vs[1] - vs[0]
    for li, (xc, zt, dl, tol) in enumerate(linzy):
        a = dl / 2; i0, i1, _, _ = okno(us, vs, xc, 0, a + .15, 1); j0, j1 = np.searchsorted(vs, [zt - tol * 1.35 - .16, zt + .06])
        if i1 - i0 < 3 or j1 - j0 < 3: continue
        w = (slice(j0, j1), slice(i0, i1)); U = us[i0:i1]; V = vs[j0:j1][:, None]; u = (U - xc) / a
        r = np.random.default_rng(300 + li); naklon = r.normal(0, .012); kos = r.uniform(-.25, .25)          # slight tilt and unequal ends
        prof = np.clip(1 - np.abs(u) ** 4, 0, 1) ** .6 * (1 + kos * u)                         # even thickness, the ends taper off
        verh = zt - .006 - .06 * tol * u * u + naklon * (U - xc) + .009 * n1(100 + li, U, .22) + .005 * n1(300 + li, U, .07)
        niz = verh - tol * prof * (1 + .10 * n1(200 + li, U, .35)); tl = np.maximum(verh - niz, 0)
        drozh = .009 * f_sr[w] + .006 * f_ml[w]                                                 # band boundaries wobble by +-1 cm
        zb = (niz + .36 * tl)[None, :] + drozh * np.minimum(1, tl / .06)[None, :]; za = (niz + .66 * tl)[None, :] + drozh * np.minimum(1, tl / .06)[None, :]
        vn = ((np.abs(u) < 1) & (tl > 1.5 * dv))[None, :]; aa = 1.2 * dv
        m_zo = np.clip((V - za) / aa + .5, 0, 1) * np.clip((verh[None, :] - V) / aa + .5, 0, 1) * vn      # ash
        m_ch = np.clip((V - zb) / aa + .5, 0, 1) * np.clip((za - V) / aa + .5, 0, 1) * vn                 # charcoal
        glub = zb - V; shir = (.36 * tl + .16 * tol + .02)[None, :]                             # baked earth: under the charcoal, fading out downwards
        m_kr = gl(1 - glub / shir) * (glub > -aa) * np.clip(tl / (.45 * tol), 0, 1)[None, :] ** .7 * (np.abs(u) < 1)[None, :] * (1 - m_ch) * (1 - m_zo)
        kr = KR[None, None] * (1 + .15 * f_ml[w] + .10 * f_zr[w] - .45 * np.clip((-f_zr[w] - 1.5) * 3, 0, 1))[..., None]
        ch = CH[None, None] * (1 + .35 * np.clip(f_zr[w], 0, 2))[..., None]
        zo = ZO[None, None] * (1 + .08 * f_ml[w] + .06 * f_zr[w] + .06 * f_sr[w] - .6 * np.clip((-f_zr[w] - 1.6) * 3, 0, 1))[..., None]    # small charcoal bits in the ash
        cw = col[w] * (1 - .92 * m_kr[..., None]) + kr * .92 * m_kr[..., None]
        cw = cw * (1 - m_ch[..., None]) + ch * m_ch[..., None]; col[w] = cw * (1 - m_zo[..., None]) + zo * m_zo[..., None]
        disp[w] += -.012 * m_zo - .006 * m_ch + .004 * m_kr                                     # soft ash is recessed, hard baked earth protrudes
        s = (V - niz[None, :]) / np.maximum(tl, 1e-3)[None, :]; ugol[w] = np.maximum(ugol[w], m_ch)
        zan[w] |= (s > -.3) & (s < 1.3) & (np.abs(u) < 1.06)[None, :]

def narisovat_melochi(us, vs, col, disp, zan, seed, linzy):
    """Small inclusions: burnt bones (black and grey-brown), white lumps, quartz flakes, charcoal bits. Denser near the hearths."""
    r = np.random.default_rng(seed); du = us[1] - us[0]
    def mesto():
        if linzy and r.uniform() < .72:
            xc, zt, dl, tol = linzy[int(r.integers(len(linzy)))]; return xc + r.normal(0, dl * .38), zt - tol * .5 + r.normal(0, .2)
        return r.uniform(us[0], us[-1]), r.uniform(vs[0], vs[-1])
    def kraska(cu, cv, rad, fn, cvet, vyst=.004):
        if not (us[0] + .08 < cu < us[-1] - .08 and vs[0] + .03 < cv < vs[-1] - .02): return
        i0, i1, j0, j1 = okno(us, vs, cu, cv, rad + .02, rad + .02)
        if i1 - i0 < 2 or j1 - j0 < 2 or zan[(j0 + j1) // 2, (i0 + i1) // 2]: return
        w = (slice(j0, j1), slice(i0, i1)); d = fn(us[i0:i1][None, :] - cu, vs[j0:j1][:, None] - cv)      # d > 0 inside, m
        mk = np.clip(d / du + .5, 0, 1)
        col[w] = col[w] * (1 - mk[..., None]) + np.array(L(cvet), np.float32)[None, None] * r.uniform(.85, 1.1) * mk[..., None]; disp[w] += vyst * mk
    for _ in range(90):                                              # bones: sticks with thickened ends
        cu, cv = mesto(); ln = r.uniform(.07, .2); tol = r.uniform(.011, .02); th = r.normal(0, .4); c, s = math.cos(th), math.sin(th)
        def kost(U, V, ln=ln, tol=tol, c=c, s=s):
            p = U * c + V * s; q = -U * s + V * c; pa = np.clip(p, -ln / 2, ln / 2)
            return tol * (1 + .6 * (np.abs(pa) / (ln / 2)) ** 6) - np.hypot(p - pa, q)
        kraska(cu, cv, ln / 2 + tol * 2, kost, ('#1b1816', '#1b1816', '#6a5c4d', '#6a5c4d', '#3a302a', '#a39478')[int(r.integers(6))])
    for _ in range(120):                                             # white lumps
        cu, cv = mesto(); rad = r.uniform(.012, .03); e = r.uniform(.6, 1.0); th = r.uniform(0, 3.14); c, s = math.cos(th), math.sin(th)
        kraska(cu, cv, rad, lambda U, V, rad=rad, e=e, c=c, s=s: rad - np.hypot(U * c + V * s, (-U * s + V * c) / e), '#e6e2d6')
    for _ in range(110):                                             # quartz flakes: small sharp triangles
        cu, cv = mesto(); rad = r.uniform(.016, .04); f0 = r.uniform(0, 6.28); ro = r.uniform(.35, .7, 3); fi = f0 + np.array([0, 2.1, 4.2]) + r.uniform(-.4, .4, 3)
        def otshchep(U, V, rad=rad, ro=ro, fi=fi):
            d = np.full(np.broadcast(U, V).shape, 9.)
            for k in range(3): d = np.minimum(d, ro[k] * rad - (U * math.cos(fi[k]) + V * math.sin(fi[k])))
            return d
        kraska(cu, cv, rad, otshchep, '#f2f0ea', .006)
    for _ in range(260):                                             # charcoal bits
        cu, cv = mesto(); rad = r.uniform(.006, .018)
        kraska(cu, cv, rad, lambda U, V, rad=rad: rad - np.hypot(U, V * 1.4), '#151312', -.002)

_zg = np.cumsum([s[0] for s in SLOI])[:-1]; _rg = np.random.default_rng(21)
_A = _rg.uniform(.04, .09, len(_zg)); _wv = _rg.uniform(.6, 1.3, len(_zg)); _fz = _rg.uniform(0, 6.28, len(_zg))
def gran_lico(xs):                                # layer boundaries along the front face: wavy lines z(x)
    return np.stack([_zg[k] + _A[k] * (.6 * np.sin(xs * _wv[k] + _fz[k]) + .5 * n1(k, xs, .8)) for k in range(len(_zg))])
def gran_bok(ys, x):                              # the same boundaries continue into the depth along the side face
    g0 = gran_lico(np.array([x]))[:, 0]
    return np.stack([g0[k] + _A[k] * .9 * (n1(40 + k, ys + x, .9) - n1(40 + k, np.array([x]), .9)[0]) for k in range(len(_zg))])

def pole_grani(us, vs, gran, seed, linzy=(), n_blokov=70, krupnyh=7, kray=.07, pusto=()):
    """Colour (nv, nu, 3), relief (nv, nu) and charcoal mask for a vertical face: earth layers, blocks, hearth lenses, small bits."""
    nu, nv = len(us), len(vs)
    f_kr = vshum(us, vs, 1.3, seed * 10 + 1, 2); f_sr = vshum(us, vs, .22, seed * 10 + 2, 2); f_ml = vshum(us, vs, .05, seed * 10 + 3, 2); f_zr = vshum(us, vs, .016, seed * 10 + 4)
    Vv = vs[:, None] + .030 * f_kr + .018 * f_sr + .008 * f_ml                    # uneven layer boundary
    CV = np.array([L(c) for _, c in SLOI], np.float32); col = np.broadcast_to(CV[0], (nv, nu, 3)).copy(); nomer = np.zeros((nv, nu), np.float32)
    for k in range(len(SLOI) - 1):
        t = gl((Vv - gran[k][None, :]) / .03 + .5); col = col * (1 - t[..., None]) + CV[k + 1] * t[..., None]; nomer += t
    col *= (1 + .13 * f_kr + .09 * f_sr + .07 * f_ml + .05 * f_zr)[..., None]
    ton = .08 * vshum(us, vs, .8, seed * 10 + 5, 2); col[..., 0] *= 1 + ton; col[..., 2] *= 1 - 1.2 * ton        # redder in places, more yellow in others
    col *= (1 + .035 * np.sin(vs[:, None] * 55 + 2.5 * f_sr + 1.5 * f_kr))[..., None]                           # fine bedding
    shch = np.clip((f_zr - 2.0) * 2.2, 0, 1) * (f_ml > .0)                                                       # rubble: light crumbs
    col = col * (1 - .6 * shch[..., None]) + np.array(L('#a9a496'), np.float32) * .6 * shch[..., None]
    col *= (1 - .5 * np.clip((-f_zr - 1.7) * 2.2, 0, 1))[..., None]
    tv = np.array([.0, .012, -.004, .010, .0, -.006, .012, .0, .010, -.004, .008])                               # dense layers protrude slightly
    disp = .010 * f_sr + .006 * f_ml + .004 * f_zr + .008 * shch + np.interp(nomer, np.arange(len(tv)), tv).astype(np.float32)
    zan = np.zeros((nv, nu), bool); ugol = np.zeros((nv, nu), np.float32)
    narisovat_linzy(us, vs, col, disp, zan, ugol, f_sr, f_ml, f_zr, linzy)
    for u0, u1, v0, v1 in pusto: zan[np.ix_((vs > v0) & (vs < v1), (us > u0) & (us < u1))] = True
    narisovat_bloki(us, vs, col, disp, zan, n_blokov, seed * 10 + 6, f_ml, f_zr, krupnyh=krupnyh)
    narisovat_melochi(us, vs, col, disp, zan, seed * 10 + 7, list(linzy))
    disp *= np.clip(np.minimum(us - us[0], us[-1] - us) / kray, 0, 1)[None, :]                                    # towards the block edges the relief fades out
    return np.clip(col, 0, 1), disp, ugol

def setka(imya, P, col=None, mat=None, obr=False, dop=None):
    """Mesh from a point lattice P (nv, nu, 3); per-vertex colour in attribute cvet; dop: extra numeric attributes."""
    nv, nu = P.shape[:2]; me = bpy.data.meshes.new(imya); me.vertices.add(nv * nu); me.vertices.foreach_set('co', P.reshape(-1).astype(np.float32))
    ids = np.arange(nv * nu).reshape(nv, nu); q = [ids[:-1, :-1], ids[:-1, 1:], ids[1:, 1:], ids[1:, :-1]]
    F = np.stack(q[::-1] if obr else q, -1).reshape(-1).astype(np.int32); nf = len(F) // 4
    me.loops.add(nf * 4); me.loops.foreach_set('vertex_index', F); me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, nf * 4, 4, dtype=np.int32))
    me.update(calc_edges=True)
    if col is not None:
        rgba = np.concatenate([col.reshape(-1, col.shape[-1]).astype(np.float32), np.ones((nv * nu, 1), np.float32)], 1)[:, :4] if col.shape[-1] == 3 else col.reshape(-1, 4).astype(np.float32)
        me.color_attributes.new('cvet', 'FLOAT_COLOR', 'POINT').data.foreach_set('color', rgba.ravel())
    for k, v in (dop or {}).items(): me.attributes.new(k, 'FLOAT', 'POINT').data.foreach_set('value', v.reshape(-1).astype(np.float32))
    me.polygons.foreach_set('use_smooth', np.ones(nf, bool))
    o = bpy.data.objects.new(imya, me); sc.collection.objects.link(o)
    if mat: me.materials.append(mat)
    return o

def mat_sreza(imya, bugry=.3):
    """Colour from vertices (cvet), small bumps. The charcoal band (attribute ugol) smoulders while it is right below the surface (node h is its height)."""
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; k = nt.links.new; b = N['Principled BSDF']
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 'cvet'; k(at.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .93
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 70; nz.inputs['Detail'].default_value = 8
    bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = bugry; bu.inputs['Distance'].default_value = .004
    k(tc.outputs['Object'], nz.inputs['Vector']); k(nz.outputs['Fac'], bu.inputs['Height']); k(bu.outputs[0], b.inputs['Normal'])
    geo = N.new('ShaderNodeNewGeometry'); sp = N.new('ShaderNodeSeparateXYZ'); hv = N.new('ShaderNodeValue'); hv.name = 'h'; hv.outputs[0].default_value = 99.
    gb = N.new('ShaderNodeMath'); gb.operation = 'SUBTRACT'; mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .0; mr.inputs['From Max'].default_value = .55
    mr.inputs['To Min'].default_value = 1.; mr.inputs['To Max'].default_value = .0
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
    au = N.new('ShaderNodeAttribute'); au.attribute_name = 'ugol'; ml = N.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'
    ms = N.new('ShaderNodeMath'); ms.operation = 'MULTIPLY'; ms.inputs[1].default_value = S_ZHAR; ms.name = 'zhar'
    k(geo.outputs['Position'], sp.inputs[0]); k(hv.outputs[0], gb.inputs[0]); k(sp.outputs['Z'], gb.inputs[1]); k(gb.outputs[0], mr.inputs['Value'])
    k(mr.outputs['Result'], pw.inputs[0]); k(pw.outputs[0], ml.inputs[0]); k(au.outputs['Fac'], ml.inputs[1]); k(ml.outputs[0], ms.inputs[0])
    b.inputs['Emission Color'].default_value = (1.0, .24, .03, 1); k(ms.outputs[0], b.inputs['Emission Strength'])
    return m

def glyba(imya, mesto, razmer, seed, mat, podr=4, graney=11):
    """An angular limestone block: a sphere cut by random planes (chips), with fine roughness."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=podr, radius=1, location=(0, 0, 0)); o = bpy.context.object; o.name = imya; me = o.data
    r = np.random.default_rng(seed); co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3).astype(np.float64)
    for _ in range(graney):
        nn = r.normal(size=3); nn /= np.linalg.norm(nn); d = r.uniform(.45, .85); s_ = co @ nn - d; m_ = s_ > 0; co[m_] -= s_[m_, None] * nn[None]
    co *= np.array(razmer)[None] * 1.25; me.vertices.foreach_set('co', co.astype(np.float32).ravel()); me.update()
    kamni._shum(me, min(razmer) * .05, 2.2 / max(razmer), seed, okt=4, greben=.3)
    bm = bmesh.new(); bm.from_mesh(me)                                                 # chip edges are sharp, faces are smooth
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle() > .55: e.smooth = False
    bm.to_mesh(me); bm.free()
    o.location = mesto; o.rotation_euler = (r.uniform(-.2, .2), r.uniform(-.2, .2), r.uniform(0, 6.28)); bpy.ops.object.shade_smooth()
    if mat: me.materials.append(mat)
    return o

# ========= deposit block: front face, two side faces, a moving lid surface
t_sb = time.time()
m_srez = mat_sreza('srez')
xs = np.linspace(-W_ / 2, W_ / 2, int(round(W_ / SHAG)) + 1); zs = np.linspace(0, H1, int(round(H1 / SHAG)) + 1)
col, disp, ugol = pole_grani(xs, zs, gran_lico(xs), 3, LINZY, n_blokov=100, krupnyh=8, pusto=[(X_CH - .85, X_CH + .7, -1, 1.9)])
X, Z = np.meshgrid(xs, zs); lico = setka('srez', np.stack([X, -disp, Z], -1)[::RED, ::RED], col[::RED, ::RED], m_srez, dop=dict(ugol=ugol[::RED, ::RED]))
sb = SHAG * 1.6; ys = np.linspace(0, D_, int(round(D_ / sb)) + 1); zb = np.linspace(0, H1, int(round(H1 / sb)) + 1); boka = []
for zn, im in ((1, 'bok-pr'), (-1, 'bok-lev')):
    col, disp, _ = pole_grani(ys, zb, gran_bok(ys, zn * W_ / 2), 5 + zn, (), n_blokov=45, krupnyh=4)
    Y, Z = np.meshgrid(ys, zb); boka.append(setka(im, np.stack([zn * (W_ / 2 + disp), Y, Z], -1)[::RED, ::RED], col[::RED, ::RED], m_srez, obr=zn < 0))
print(f'section: {len(xs[::RED])}x{len(zs[::RED])} vertices, {time.time() - t_sb:.1f} s'); sys.stdout.flush()

# 'growth' = revealing by height: geometry nodes remove everything above h (postavit sets the h node value)
ng = bpy.data.node_groups.new('srez-po-vysote', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
_N = ng.nodes; _k = ng.links.new
_gi = _N.new('NodeGroupInput'); _go = _N.new('NodeGroupOutput'); _pos = _N.new('GeometryNodeInputPosition'); _sep = _N.new('ShaderNodeSeparateXYZ')
uz_h = _N.new('ShaderNodeValue'); uz_h.name = 'h'; _cmp = _N.new('FunctionNodeCompare'); _cmp.data_type = 'FLOAT'; _cmp.operation = 'GREATER_THAN'
_dl = _N.new('GeometryNodeDeleteGeometry'); _dl.domain = 'POINT'
_k(_pos.outputs[0], _sep.inputs[0]); _k(_sep.outputs['Z'], _cmp.inputs[0]); _k(uz_h.outputs[0], _cmp.inputs[1])
_k(_gi.outputs[0], _dl.inputs['Geometry']); _k(_cmp.outputs[0], _dl.inputs['Selection']); _k(_dl.outputs[0], _go.inputs[0])
for o in [lico] + boka: o.modifiers.new('srez', 'NODES').node_group = ng

# the lid is the current surface: earth, ash dust, stones fallen from the ceiling (clean near the edge, where the fires burn)
sk = .016
kx = np.linspace(-W_ / 2 - .05, W_ / 2 + .05, int(round((W_ + .1) / sk)) + 1); ky = np.linspace(-.10, D_ + .05, int(round((D_ + .15) / sk)) + 1)
f_kr = vshum(kx, ky, 1.2, 51, 2); f_sr = vshum(kx, ky, .25, 52, 2); f_ml = vshum(kx, ky, .05, 53, 2); f_zr = vshum(kx, ky, .02, 54)
dolya = (np.clip(.5 + .5 * vshum(kx, ky, .9, 55, 2), 0, 1) * .5)[..., None]
col = (np.array(L('#6a5237'), np.float32) * (1 - dolya) + np.array(L('#80766a'), np.float32) * dolya) * (1 + .14 * f_kr + .1 * f_sr + .08 * f_ml + .06 * f_zr)[..., None]
disp = .035 * f_kr + .012 * f_sr + .005 * f_ml; zan = np.zeros(f_kr.shape, bool); zan[ky < 1.95, :] = True
narisovat_bloki(kx, ky, col, disp, zan, 60, 61, f_ml, f_zr, krupnyh=6, vys=1.6, plosk=False, razm=.2)
disp *= np.clip(ky / .3, 0, 1)[:, None]
X, Y = np.meshgrid(kx, ky); kryshka = setka('kryshka', np.stack([X, Y, disp], -1)[::RED, ::RED], np.clip(col, 0, 1)[::RED, ::RED], mat_sreza('kryshka', .5))
m_izv = mat_kamnya('izvestnyak', cvet=('#6f6c64', '#b3afa4'), mash=3, bugry=.6, treshch=.0, sloi=.2)
rng = np.random.default_rng(3); na_kryshke = []
for i, (x, y, r_) in enumerate(((-2.8, 2.7, .30), (-1.2, 3.3, .20), (.9, 3.2, .36), (2.7, 2.9, .26), (-.4, 2.4, .14), (1.9, 2.3, .12), (-3.0, 3.5, .16))):
    o = glyba(f'oblomok{i}', (x, y, r_ * .3), (r_ * rng.uniform(.9, 1.3), r_ * rng.uniform(.7, 1.0), r_ * rng.uniform(.45, .7)), 70 + i, m_izv, podr=3)
    o.parent = kryshka; na_kryshke.append(o)

# ========= cave hall: a dome of grey limestone, floor, boulders
m_zal = mat_kamnya('zal', cvet=('#38383c', '#78787c'), mash=.55, bugry=1.0, treshch=.0, sloi=.4)
zal = peshchera('zal', a=20, b=30, h=19, vhod=(90, 0, 1), mat=m_zal, seed=6, nt=260 if PROBA else 420, nf=90 if PROBA else 140, ampl=1.9); zal.location = (1, -2, -.5)
npl = 150 if PROBA else 240; px = np.linspace(-24, 26, npl); py = np.linspace(-33, 29, npl)
dx_ = np.maximum(np.abs(px) - W_ / 2 - .3, 0)[None, :]; dy_ = np.maximum(np.maximum(-1.6 - py, py - D_ - .3), 0)[:, None]
pz = (.24 * vshum(px, py, 4.0, 41, 3) + .05 * vshum(px, py, .7, 42, 2)) * gl(np.hypot(dx_, dy_) / 3.5) - .01          # the floor is flat near the block
X, Y = np.meshgrid(px, py)
pol_ = setka('pol', np.stack([X, Y, pz], -1), None, mat_kamnya('pol', cvet=('#2b2925', '#5b564d'), mash=1.3, bugry=.6, treshch=.0, sloi=.1))
m_gl = mat_kamnya('glyba', cvet=('#34343a', '#74747a'), mash=.9, bugry=.9, treshch=.0, sloi=.3)
GLYBY = [((-9., 14., 1.3), (4.0, 3.2, 3.0)), ((2.5, 17., 1.6), (5.0, 3.6, 3.6)), ((11., 13., 1.2), (3.6, 3.0, 2.8)), ((-16., 8., 1.5), (3.6, 3.0, 3.6)),     # distant, large
         ((-3.5, 11., .8), (2.4, 2.0, 1.8)), ((15., 5., 1.0), (3.0, 2.4, 2.4)), ((-7.2, 3.0, .55), (1.6, 1.25, 1.2)), ((-9.5, -1.5, .5), (1.5, 1.1, 1.0)),
         ((7.6, 6.5, .6), (1.7, 1.4, 1.3)), ((-5.6, 6.6, .4), (1.1, .9, .8)), ((-5.0, -1.8, .2), (.6, .5, .4)), ((-6.9, -5.0, .15), (.5, .4, .3)),              # near, small
         ((-2.6, -4.6, .1), (.35, .3, .2)), ((-4.2, -3.2, .12), (.45, .35, .25)), ((5.6, 3.0, .25), (.7, .6, .5)),
         ((-2.8, 7.2, .5), (1.5, 1.2, 1.1)), ((4.0, 8.6, .7), (2.0, 1.6, 1.5)), ((-6.4, 9.5, .9), (2.6, 2.0, 2.0))]
glyby = [glyba(f'glyba{i}', m_, r_, 30 + i, m_gl, podr=4 if max(r_) > 1 else 3) for i, (m_, r_) in enumerate(GLYBY)]
mir = bpy.data.worlds.new('mir'); sc.world = mir; mir.use_nodes = True
mir.node_tree.nodes['Background'].inputs[0].default_value = (*FON[0], 1); mir.node_tree.nodes['Background'].inputs[1].default_value = FON[1]

# ========= campfires: fire volume from the cache, light (on the block, on the hall, spill down the section), hearth (charcoal, ash, wood)
def kollekciya(imya, obekty):
    c = bpy.data.collections.new(imya)
    for o in obekty: c.objects.link(o)
    return c
def tochka(imya, mesto, cvet, radius=.15, roditel=None, priyom=None, ten=True, zerno=.004):
    ld = bpy.data.lights.new(imya, 'POINT'); ld.color = cvet; ld.shadow_soft_size = radius; ld.use_shadow = ten; ld.energy = 0
    ld.shadow_maximum_resolution = zerno                                               # shadow map texel size, m: larger is coarser and cheaper
    o = bpy.data.objects.new(imya, ld); sc.collection.objects.link(o); o.location = mesto
    if roditel: o.parent = roditel
    if priyom: o.light_linking.receiver_collection = priyom
    return o
def mertsanie(seed, glubina=.3):
    r = np.random.default_rng(seed); n = NF + 3; t = np.arange(n) / FPS
    f = 1 + glubina * (.45 * np.sin(t * 9.1 + r.uniform(0, 6)) + .3 * np.sin(t * 17.3 + r.uniform(0, 6)) + .25 * np.sin(t * 31.7 + r.uniform(0, 6)))
    return np.maximum(.3, f + glubina * .35 * np.convolve(r.standard_normal(n), np.ones(3) / 3, 'same'))
def mat_kostrishcha():
    m = bpy.data.materials.new('kostrishche'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; k = nt.links.new; b = N['Principled BSDF']; out = N['Material Output']
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 'cvet'; az = N.new('ShaderNodeAttribute'); az.attribute_name = 'zhar'; oi = N.new('ShaderNodeObjectInfo')
    ml = N.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'; mz = N.new('ShaderNodeMath'); mz.operation = 'MULTIPLY'; mz2 = N.new('ShaderNodeMath'); mz2.operation = 'MULTIPLY'; mz2.inputs[1].default_value = 9.
    tr = N.new('ShaderNodeBsdfTransparent'); mix = N.new('ShaderNodeMixShader')
    k(at.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .95; b.inputs['Emission Color'].default_value = (1.0, .26, .03, 1)
    k(at.outputs['Alpha'], ml.inputs[0]); k(oi.outputs['Alpha'], ml.inputs[1]); k(az.outputs['Fac'], mz.inputs[0]); k(oi.outputs['Alpha'], mz.inputs[1])
    k(mz.outputs[0], mz2.inputs[0]); k(mz2.outputs[0], b.inputs['Emission Strength'])
    k(ml.outputs[0], mix.inputs['Fac']); k(tr.outputs[0], mix.inputs[1]); k(b.outputs[0], mix.inputs[2]); k(mix.outputs[0], out.inputs['Surface'])
    try: m.surface_render_method = 'DITHERED'; m.use_transparent_shadow = True
    except Exception: pass
    return m
def pyatno(imya, R, seed):
    """A hearth on the surface: a dark patch of charcoal and ash with glowing embers, soft edges."""
    nr, na = 12, 40; r = np.random.default_rng(seed); V = [(0, 0, 0)]; C = [(.02, .018, .016, 1.0)]; Zh = [1.0]; F = []
    for j in range(1, nr + 1):
        for i in range(na):
            a = i / na * 2 * math.pi; u = j / nr; kr = 1 + .16 * math.sin(a * 3 + seed) + .09 * math.sin(a * 7 + 2 * seed)
            V.append((math.cos(a) * R * u * kr, math.sin(a) * R * u * kr, 0))
            C.append(((.26, .25, .23) if r.uniform() < .15 + .3 * u else (.016, .014, .013)) + (max(0., 1 - u ** 2.4),)); Zh.append(float(r.uniform() < .5 * (1 - u) ** 1.5))
    for i in range(na): F.append((0, 1 + i, 1 + (i + 1) % na))
    for j in range(1, nr):
        for i in range(na):
            a0, a1 = 1 + (j - 1) * na + i, 1 + (j - 1) * na + (i + 1) % na; F.append((a0, a0 + na, a1 + na, a1))
    me = bpy.data.meshes.new(imya); me.from_pydata(V, [], F); me.update()
    me.color_attributes.new('cvet', 'FLOAT_COLOR', 'POINT').data.foreach_set('color', np.array(C, np.float32).ravel())
    me.attributes.new('zhar', 'FLOAT', 'POINT').data.foreach_set('value', np.array(Zh, np.float32))
    o = bpy.data.objects.new(imya, me); sc.collection.objects.link(o); me.materials.append(m_kostr); o.visible_shadow = False
    return o

def mat_oreola():
    m = bpy.data.materials.new('oreol'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear(); k = nt.links.new
    out = N.new('ShaderNodeOutputMaterial'); tc = N.new('ShaderNodeTexCoord'); ds = N.new('ShaderNodeVectorMath'); ds.operation = 'DISTANCE'; ds.inputs[1].default_value = (.5, .5, 0)
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = .5; mr.inputs['To Min'].default_value = 1; mr.inputs['To Max'].default_value = 0
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.6; oi = N.new('ShaderNodeObjectInfo'); ml = N.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'
    em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, .42, .12, 1); tr = N.new('ShaderNodeBsdfTransparent'); ad = N.new('ShaderNodeAddShader')
    k(tc.outputs['UV'], ds.inputs[0]); k(ds.outputs['Value'], mr.inputs['Value']); k(mr.outputs['Result'], pw.inputs[0]); k(pw.outputs[0], ml.inputs[0]); k(oi.outputs['Alpha'], ml.inputs[1])
    k(ml.outputs[0], em.inputs['Strength']); k(tr.outputs[0], ad.inputs[0]); k(em.outputs[0], ad.inputs[1]); k(ad.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'; m.use_backface_culling = False
    return m
def oreol(imya, razmer):
    me = bpy.data.meshes.new(imya); h_ = razmer / 2; me.from_pydata([(-h_, -h_, 0), (h_, -h_, 0), (h_, h_, 0), (-h_, h_, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i_, c_ in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[i_].uv = c_
    me.update(); o = bpy.data.objects.new(imya, me); sc.collection.objects.link(o); me.materials.append(m_oreol); o.visible_shadow = False
    cn = o.constraints.new('COPY_ROTATION'); cn.target = kam                                  # always faces the camera
    return o
m_oreol = mat_oreola(); m_kostr = mat_kostrishcha(); m_suk = mat_dereva('suk', ugol=.8, zhar=.9)
k_gran = kollekciya('priyom-gran', [lico] + boka)                                        # receivers of the fire spill light
k_zal = kollekciya('priyom-zal', [zal, pol_] + glyby)                                    # receivers of the 'far' fire light
k_blok = kollekciya('priyom-blok', [kryshka] + na_kryshke)                               # receivers of the near fire light (extended below)
k_klyuch = kollekciya('priyom-klyuch', [lico, kryshka, pol_] + boka + na_kryshke)        # receivers of the spotlight
# fire is a shared seamless loop koster_petlya (a pair of volumes). Fires that never burn at the same time share one pair:
# postavit moves it to the next fire, and the emission strength (flare-up and die-down) is driven by keys through mnozh
SLOTY = []
for i, og in enumerate(OGNI):
    if not og['gorit']: continue
    for sl in SLOTY:
        if OGNI[sl[-1]]['tb'] + .12 < og['ta']: sl.append(i); break
    else: SLOTY.append([i])
OBYOMY = []
for k, sl in enumerate(SLOTY):
    obs, _ = koster_petlya(KD, sila=S_OGNYA, dym=DYM, nf=NF, mnozh=lambda n, sl=sl: sum(sila_ognya(i, (n - 1) / FPS) for i in sl) ** 1.3, imya=f'ogon{k}')
    for v in obs: v.parent = kryshka
    for i in sl: OGNI[i]['obyomy'] = obs
    OBYOMY += obs
print('fire volume pairs:', SLOTY); sys.stdout.flush()
for i, og in enumerate(OGNI):
    x, y, s = og['x'], og['y'], og['mash']; r = np.random.default_rng(100 + i)
    og['svet'] = tochka(f'svet{i}', (x, y, .5 * s), CV_OGNYA, .12, kryshka, k_blok)
    og['dal'] = tochka(f'dal{i}', (x, y, .75 * s), CV_OGNYA, .3, kryshka, k_zal, zerno=.03)
    og['stek'] = tochka(f'stek{i}', (x, -Y_STEK, Z_STEK), CV_OGNYA, .3, kryshka, k_gran, zerno=.008)
    og['pyatno'] = pyatno(f'kostrishche{i}', .62 * s, i); og['pyatno'].parent = kryshka; og['pyatno'].location = (x, y, .035); k_blok.objects.link(og['pyatno'])
    dr = bpy.data.objects.new(f'drova{i}', None); sc.collection.objects.link(dr); dr.parent = kryshka; dr.location = (x, y, .03); og['drova'] = dr
    for j in range(6):
        a = j / 6 * 2 * math.pi + r.uniform(-.3, .3); rr = r.uniform(.24, .34) * s
        o = suk(f'suk{i}_{j}', (math.cos(a) * rr, math.sin(a) * rr, .02), (math.cos(a + 3.3) * .04, math.sin(a + 3.3) * .04, r.uniform(.22, .32) * s),
                r=r.uniform(.02, .03) * s * .8, seed=i * 10 + j, mat=m_suk); o.parent = dr; k_blok.objects.link(o)
    og['oreol'] = oreol(f'oreol{i}', 2.8 * s); og['oreol'].parent = kryshka; og['oreol'].location = (x, y, .5 * s)
    og['mert'] = mertsanie(i + 1); og['mert2'] = mertsanie(50 + i, .2)

# sparks at the first fire (wide shot of the hall) and at the last one (finale)
isk = Iskry('iskry', sila=60.)
o0, o1 = OGNI[0], OGNI[-1]
isk.vsplesk(-1.6, (o0['x'], o0['y'], H0 + .4), napr=(0, 0, 1), n=200, skorost=(.3, 1.6), konus=.5, zhizn=(.6, 1.7), g=0, drag=1.2, r=.004, yark=.9,
            razbros_mesta=.14, turb=2.2, pod=1.3, dlit=3.6, ostyv=1.2)
isk.vsplesk(o1['ta'] + .3, (o1['x'], o1['y'], H1 + .45), napr=(0, 0, 1), n=230, skorost=(.3, 1.5), konus=.45, zhizn=(.7, 2.0), g=0, drag=1.2, r=.0045, yark=.9,
            razbros_mesta=.16, turb=2.2, pod=1.3, dlit=DLIT - o1['ta'], ostyv=1.2)

# ========= general light: a cold spotlight on the section, faint fill on the side faces, cold diffuse hall light from above
def prozhektor(imya, mesto, cel, cvet, ugol, razmytie, radius, priyom=None, ten=True, zerno=.008):
    ld = bpy.data.lights.new(imya, 'SPOT'); ld.color = cvet; ld.spot_size = math.radians(ugol); ld.spot_blend = razmytie; ld.shadow_soft_size = radius; ld.use_shadow = ten
    ld.shadow_maximum_resolution = zerno
    o = bpy.data.objects.new(imya, ld); sc.collection.objects.link(o); o.location = mesto; smotret(o, cel)
    if priyom: o.light_linking.receiver_collection = priyom
    return o
klyuch = prozhektor('klyuch', (-5.0, -11.5, 9.5), (.3, 0, 2.5), CV_KLYUCH, 52, .8, 1.6, k_klyuch)
bok_svet = prozhektor('bok', (13., -7., 5.), (W_ / 2, D_ / 2, 2.8), CV_KLYUCH, 50, .8, 1.5, kollekciya('priyom-bok', boka)); bok_svet.data.energy = S_BOK
_ld = bpy.data.lights.new('svod', 'SUN'); _ld.energy = S_ZAL; _ld.color = (.55, .68, 1.0); _ld.angle = math.radians(40); _ld.shadow_maximum_resolution = .06
svod = bpy.data.objects.new('svod', _ld); sc.collection.objects.link(svod); svod.location = (-3, 6, 30); smotret(svod, (1.5, 2, 0))
svod.light_linking.receiver_collection = k_zal; svod.light_linking.blocker_collection = kollekciya('ten-svod', glyby + [lico, kryshka] + boka)   # the hall vault does not block this light

# ========= a person for scale at the foot, on the right
chel = kartochka('chelovek', f'{ROOT}/kartinki/chelovek-cvet.png', 1.7, (X_CH, Y_CH, -.012), povorot_z=POV_CH, svet=float(_arg('ch_svet', .1)), diffuz=1.0)   # v3: a painted figure, not a black silhouette
pr_chel = chel.data.materials[0].node_tree.nodes['prozr'].outputs[0]

# ========= scene state at frame n (all motion happens here)
def postavit(n):
    t = (n - 1) / FPS; h = H1 if OSM else h_t(t)
    uz_h.outputs[0].default_value = h + 1e-4; kryshka.location = (0, 0, h); postavit_kameru(t); m_srez.node_tree.nodes['h'].outputs[0].default_value = h
    pk = np.array(kam.location); vp = np.array([-math.sin(kam.rotation_euler[2]), math.cos(kam.rotation_euler[2]), 0]); dmin, dmax = 1e9, 0.
    for o in OBYOMY: o.hide_render = True
    for i, og in enumerate(OGNI):
        a = sila_ognya(i, t); vid = a > .003; s = og['mash']
        for o in [og[k] for k in ('svet', 'dal', 'stek', 'pyatno', 'oreol')]: o.hide_render = not vid
        og['drova'].scale = (max(.001, sm(a * 1.6)),) * 3
        if not vid: continue
        sx = s * SHIR_OGNYA * (.75 + .25 * a); sz = s * VYS_OGNYA * (.5 + .5 * a)                              # the flame flares up and settles
        th = og['povorot']; c_, s_ = math.cos(th), math.sin(th)                       # fires are rotated differently so the flame tongues are not identical
        for o in og['obyomy']:
            o.hide_render = False; o.rotation_euler = (0, 0, th); o.scale = (sx, sx, sz); o.location = (og['x'] - .65 * sx * (c_ - s_), og['y'] - .65 * sx * (s_ + c_), .0)
        og['svet'].data.energy = S_SVET * a * og['mert'][n]; og['dal'].data.energy = S_DAL * a * og['mert'][n]; og['stek'].data.energy = S_STEK * a * og['mert2'][n]
        og['pyatno'].color = (1, 1, 1, sm(a * 1.4)); og['oreol'].color = (1, 1, 1, S_OREOL * a * og['mert2'][n]); og['oreol'].hide_render = S_OREOL <= 0
        d = float((np.array([og['x'], og['y'], h]) - pk) @ vp); dmin, dmax = min(dmin, d), max(dmax, d)
    sc.eevee.volumetric_start = max(.1, dmin - 2.5); sc.eevee.volumetric_end = dmax + 3.5     # spend the whole volume depth on the fires
    klyuch.data.energy = S_KLYUCH * (K_KLYUCH0 + (1 - K_KLYUCH0) * sm((t - T_ROST[0]) / 3.5))
    ac = a_chel(t); pr_chel.default_value = ac; chel.hide_render = ac < .003
    isk.obnovit(t, vyderzhka=1 / 60)

out = f'{ROOT}/kadry/C' + ('-proba' if PROBA else ''); os.makedirs(out, exist_ok=True)
print(f'scene built in {time.time() - t_sb:.0f} s, fire cache {KESH}'); sys.stdout.flush()
for n in spisok_kadrov(REZHIM, NF):
    f = f'{out}/{n:04d}' + ('o' if OSM else '') + '.png'
    if os.path.exists(f) and not PROBA and not SUHO: continue
    sc.frame_set(n); postavit(n)
    if SUHO: continue
    sc.render.filepath = f; t = time.time(); bpy.ops.render.render(write_still=True); print(f'frame {n} {time.time() - t:.1f} s'); sys.stdout.flush()
if SUHO: print(f'dry-run frames passed: {len(spisok_kadrov(REZHIM, NF))}')
