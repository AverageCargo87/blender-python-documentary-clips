# Clip 3 'Fire', scene D: how fire was made. Three close-ups (macro), EEVEE, 24 fps:
#   D1a 'friction': a hand drill, the stick spins in a socket, smoke, wood dust, an ember;
#   D1b 'ember in dry grass': the ember in a nest of grass grows into a flame;
#   D2 'sparks from stone': flint strikes pyrite, sparks fall on tinder, the tinder smoulders, the grass catches.
#   blender -b --factory-startup --python scena_d.py -- <root> <D1a|D1b|D2> <vse|frames|metki> [--proba] [--polnyy]
#   --proba: half size, frames to kadry/<shot>-proba; --proba --polnyy: full size and quality but still into the preview folder (frame timing)
import sys, os, json, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, PLAN, REZHIM = A[0], A[1], A[2]; PROBA = '--proba' in A; MALO = PROBA and '--polnyy' not in A
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
from kamni import *
from mathutils import noise, Quaternion
from iskry import Iskry
from bpy_extras.object_utils import world_to_camera_view

# --------- timings and main knobs (seconds of the shot)
FPS = 24
KADROV = {'D1a': 154, 'D1b': 82, 'D2': 182}; DLITELNOST = {'D1a': 6.4, 'D1b': 3.4, 'D2': 7.6}
NF = KADROV[PLAN]; DLIT = DLITELNOST[PLAN]
# D1a: friction
HOD = .35                      # one pass of the palms: the stick turns one way
PAUZY = (1.75, 3.75); PAUZA = .25      # two stops (the palms move back up) and their length
OBOROTOV = 1.35                # stick turns per pass
T_DYM = 1.2                    # smoke starts rising from the socket
T_TRUHA = .7                   # wood dust starts falling
T_STOP = 5.0                   # spinning stops, the stick lifts away
T_UGOL = 5.3                   # an ember appears in the dust
KESH_DYM0 = 40                 # frame of the dymok cache from which the wisp is visible (almost empty before)
KESH_OGON0 = 48                # frame of the trut cache with the first flame tongue
RAZMYTIE = True                # motion blur (the stick, the flint strike)
# D1b: ember in grass
T_PLAMYA_B = 1.3               # the flame bursts out of the nest
# D2: sparks
T_UDARY = (.9, 1.9, 2.8, 3.7); T_VNIZ = .08      # strikes and the duration of the downward motion
ISKR = (5, 6, 5, 7)            # sparks per strike
ISKRY_SILA = 22.; ISKRY_R = .001; ISKRY_SLED = 1 / 170      # spark brightness, radius (m) and trail length (s)
ISKOROK = 14                   # small sparks above the flame (D1b, D2)
T_TLEET = 3.78; T_TLEET_MAX = 5.2                # a smouldering spot on the tinder: 2 mm -> 8 mm
T_TRAVA = 5.4                  # the grass nest catches
# light and smoke
SVET_KLYUCH = {'D1a': 15., 'D1b': 14., 'D2': 22.}      # warm side light ('a nearby fire'), W
SVET_KONTR = {'D1a': 30., 'D1b': 22., 'D2': 26.}       # rim light (the smoke shows against it)
SVET_HOLOD = {'D1a': 5., 'D1b': 5., 'D2': 7.}          # cold fill
DYM_PLOTN = {'D1a': 22., 'D1b': 38., 'D2': 20.}        # smoke density = density grid x this number
UGOL_SILA = 3.2                # glow of the smouldering spot (ember, tinder)
OGON_SILA = {'D1b': 120., 'D2': 120.}                  # flame brightness (mat_ognya sila); the flame is thin, hence the large number
OGON_STEPEN = 2.1              # brightness exponent on the flame grid (1.4 in mat_ognya): higher = crisper flame, no haze
OGON_SZHAT = .6                # how much the flame colour ramp is compressed (lower = more yellow and brighter)
OGON_YAZYKI = ((0, 0, .62, 0), (.015, .006, .48, -9))      # flame tongues: x, y offset (m), scale, cache frame offset
OGON_VYS = .7                 # flame height relative to width (the cache gives a narrow tall plume, so it is squashed)
SVET_PLAMENI = {'D1b': .28, 'D2': .28}                   # light from the flame onto the surroundings, W

ochistit()
sc = dvizhok('EEVEE', proc=50 if MALO else 100, samples=32 if MALO else 64, nf=NF)
e_ = sc.eevee
for k_, v_ in dict(use_volume_custom_range=True, volumetric_start=.12, volumetric_end=1.8, light_threshold=.002, shadow_ray_count=2, shadow_step_count=8,
                   volumetric_samples=int(os.environ.get('OG_VSAMP', 128)), fast_gi_distance=.4).items():      # macro: volumes only close up (0.12-1.8 m), more slices for thin smoke
    try: setattr(e_, k_, v_)
    except Exception as ex: print('eevee: missing', k_, ex)
if RAZMYTIE and PLAN in ('D1a', 'D2'):
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5
    try: e_.motion_blur_steps = 1; e_.motion_blur_max = 48
    except Exception as ex: print('motion blur:', ex)
mir = bpy.data.worlds.new('mir'); sc.world = mir; mir.use_nodes = True
bg_ = mir.node_tree.nodes['Background']; bg_.inputs[0].default_value = (.010, .014, .026, 1); bg_.inputs[1].default_value = .3

# --------- small helpers
def sm(u): u = max(0., min(1., u)); return u * u * (3 - 2 * u)
def tk(n): return (n - 1) / FPS                                  # frame time
def kl(sock, val, n): sock.default_value = val; sock.keyframe_insert('default_value', frame=n)
def c4(h, k=1.0): return (*[c * k for c in L(h)], 1)
def V3(*a): return Vector(a[0]) if len(a) == 1 else Vector(a)
def novyy(imya):
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; return m, nt, nt.nodes['Principled BSDF']
def uz(nt, tip, vh=None, **attr):
    n = nt.nodes.new(tip)
    for k_, v_ in attr.items(): setattr(n, k_, v_)
    for k_, v_ in (vh or {}).items(): n.inputs[k_].default_value = v_
    return n
def vv(nt, sock, v):                                             # feed an input either a link or a number/colour
    if isinstance(v, bpy.types.NodeSocket): nt.links.new(v, sock)
    else: sock.default_value = v
def mt(nt, op, *args, zazhim=False, imya=None):
    m = nt.nodes.new('ShaderNodeMath'); m.operation = op; m.use_clamp = zazhim
    for i, v in enumerate(args): vv(nt, m.inputs[i], v)
    if imya: m.name = imya
    return m.outputs[0]
def smes(nt, fac, a, b, rezhim='MIX'):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = rezhim
    vv(nt, m.inputs[0], fac); vv(nt, m.inputs[6], a); vv(nt, m.inputs[7], b); return m.outputs[2]
def znach(nt, imya, v):
    n = nt.nodes.new('ShaderNodeValue'); n.name = imya; n.outputs[0].default_value = v; return n.outputs[0]
def rampa(nt, fac, tochki):
    r = nt.nodes.new('ShaderNodeValToRGB'); cr = r.color_ramp
    cr.elements[0].position, cr.elements[0].color = tochki[0]; cr.elements[1].position, cr.elements[1].color = tochki[-1]
    for pos, col in tochki[1:-1]: cr.elements.new(pos).color = col
    nt.links.new(fac, r.inputs['Fac']); return r.outputs['Color']
def shum(nt, vec, mash, detal=4., sher=.5, rastyag=None):
    n = uz(nt, 'ShaderNodeTexNoise', {'Scale': mash, 'Detail': detal, 'Roughness': sher})
    if rastyag is not None:
        mp = uz(nt, 'ShaderNodeMapping', {'Scale': rastyag}); nt.links.new(vec, mp.inputs['Vector']); vec = mp.outputs[0]
    nt.links.new(vec, n.inputs['Vector']); return n
def bugry(nt, b, vysota, sila=.5, dist=.001, pred=None):
    bm = uz(nt, 'ShaderNodeBump', {'Strength': sila, 'Distance': dist}); nt.links.new(vysota, bm.inputs['Height'])
    if pred is not None: nt.links.new(pred, bm.inputs['Normal'])
    nt.links.new(bm.outputs[0], b.inputs['Normal']); return bm.outputs[0]
def obj_koord(nt): return uz(nt, 'ShaderNodeTexCoord').outputs['Object']
def mir_koord(nt): return uz(nt, 'ShaderNodeNewGeometry').outputs['Position']

def zhar(nt, b, P, pref='ug', mash=700., ryab=1.3):
    """A smouldering patch around point P (world coordinates): patchy glow by distance. Radius and strength are nodes '<pref>-r', '<pref>-sila' (keyed).
    Returns a charring mask (wider than the patch) for darkening the colour."""
    pos = mir_koord(nt); ds = uz(nt, 'ShaderNodeVectorMath', operation='DISTANCE'); ds.inputs[1].default_value = tuple(P); ds.name = pref + '-mesto'; nt.links.new(pos, ds.inputs[0])
    r = znach(nt, pref + '-r', .0005); s = znach(nt, pref + '-sila', 0.)
    otn = mt(nt, 'DIVIDE', ds.outputs['Value'], r); x = mt(nt, 'SUBTRACT', 1.0, otn)
    ns = shum(nt, pos, mash, 3.)
    m = mt(nt, 'MULTIPLY', x, mt(nt, 'MULTIPLY_ADD', ns.outputs['Fac'], ryab, 1.15 - ryab * .5), zazhim=True)
    col = rampa(nt, m, [(0, (0, 0, 0, 1)), (.2, (.5, .04, 0, 1)), (.5, (1., .3, .03, 1)), (.8, (1., .55, .12, 1)), (1, (1., .8, .4, 1))])
    nt.links.new(col, b.inputs['Emission Color']); nt.links.new(s, b.inputs['Emission Strength'])
    return mt(nt, 'MULTIPLY', mt(nt, 'SUBTRACT', 1.7, otn), 1.6, zazhim=True)

# --------- materials
def mat_plity(imya='plita', cvet=('#35322e', '#6f695f'), mash=22.):
    m = mat_kamnya(imya, cvet=cvet, mash=mash, bugry=.55, treshch=.08, sloi=.2)
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeBump': n.inputs['Distance'].default_value = .006
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .88
    return m

def mat_zemli_d():
    """Dry ground: grey-brown, fine-grained."""
    m, nt, b = novyy('zemlya-suhaya'); o = obj_koord(nt)
    n1 = shum(nt, o, 9., 6., .6); n2 = shum(nt, o, 260., 5., .65); n3 = shum(nt, o, 1400., 3.)
    b.inputs['Roughness'].default_value = .95
    col = rampa(nt, n1.outputs['Fac'], [(.3, c4('#3d3226')), (.7, c4('#6a5843'))])
    nt.links.new(smes(nt, .5, col, n2.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    h = mt(nt, 'MULTIPLY_ADD', n3.outputs['Fac'], .3, n2.outputs['Fac']); bugry(nt, b, h, .8, .004)
    return m

def mat_skola():
    """Split face of a dry soft branch: long fibres along X; charring around the origin (socket centre) grows with node 'ugol' (0..1)."""
    m, nt, b = novyy('skol'); o = obj_koord(nt)
    n1 = shum(nt, o, 1., 5., .55, rastyag=(22, 1300, 1300)); n2 = shum(nt, o, 45., 3.); n3 = shum(nt, o, 420., 3.)
    f = mt(nt, 'MULTIPLY_ADD', n2.outputs['Fac'], .45, mt(nt, 'MULTIPLY', n1.outputs['Fac'], .7))
    col = rampa(nt, f, [(.34, c4('#5e4a31')), (.52, c4('#8d7654')), (.72, c4('#ad9872'))])
    n4 = shum(nt, o, 1., 2., .5, rastyag=(9, 260, 260))                                                  # rare dark drying cracks along the grain
    tr = mt(nt, 'SUBTRACT', 1.0, mt(nt, 'DIVIDE', mt(nt, 'ABSOLUTE', mt(nt, 'SUBTRACT', n4.outputs['Fac'], .5)), .012), zazhim=True)
    col = smes(nt, mt(nt, 'MULTIPLY', tr, .8), col, c4('#231a11'))
    ug = znach(nt, 'ugol', 0.)
    d = uz(nt, 'ShaderNodeVectorMath', operation='LENGTH'); nt.links.new(o, d.inputs[0])
    dd = mt(nt, 'MULTIPLY_ADD', mt(nt, 'SUBTRACT', n3.outputs['Fac'], .5), mt(nt, 'MULTIPLY_ADD', ug, .006, .0012), d.outputs['Value'])     # ragged boundary
    R = mt(nt, 'MULTIPLY_ADD', ug, .0062, .0076)
    maska = mt(nt, 'DIVIDE', mt(nt, 'SUBTRACT', R, dd), mt(nt, 'MULTIPLY_ADD', ug, .003, .0012), zazhim=True)
    ugc = smes(nt, mt(nt, 'MULTIPLY', ug, 1.6, zazhim=True), c4('#2c1b0f'), c4('#040303'))
    nt.links.new(smes(nt, maska, col, ugc), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .78
    bugry(nt, b, mt(nt, 'MULTIPLY_ADD', tr, -1.5, n1.outputs['Fac']), .5, .0007)
    return m

def mat_kory_d(imya='kora'):
    """Branch bark: dark, with lengthwise cracks."""
    m, nt, b = novyy(imya); o = obj_koord(nt)
    n0 = shum(nt, o, 1., 6., .62, rastyag=(14, 330, 330)); n1 = shum(nt, o, 120., 5., .6); n2 = shum(nt, o, 900., 3.)
    tr = mt(nt, 'DIVIDE', mt(nt, 'ABSOLUTE', mt(nt, 'SUBTRACT', n0.outputs['Fac'], .5)), .07, zazhim=True)     # 0 in a crack, 1 on a ridge
    col = rampa(nt, n1.outputs['Fac'], [(.3, c4('#251d17')), (.7, c4('#5a4a3c'))])
    nt.links.new(smes(nt, mt(nt, 'MULTIPLY_ADD', tr, .8, .2), (.002, .002, .002, 1), col), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .9
    bugry(nt, b, mt(nt, 'MULTIPLY_ADD', n2.outputs['Fac'], .3, tr), 1., .0014)
    return m

def mat_luba():
    """A piece of bark as an ember catcher: light fibrous bast on top, dark bark underneath and on the rim."""
    m, nt, b = novyy('lub'); o = obj_koord(nt)
    n1 = shum(nt, o, 1., 4., .55, rastyag=(40, 900, 900)); n2 = shum(nt, o, 70., 3.)
    f = mt(nt, 'MULTIPLY_ADD', n2.outputs['Fac'], .5, mt(nt, 'MULTIPLY', n1.outputs['Fac'], .6))
    verh = rampa(nt, f, [(.3, c4('#5b4836')), (.55, c4('#806b54')), (.8, c4('#9c8870'))])
    geo = uz(nt, 'ShaderNodeNewGeometry'); sx = uz(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sx.inputs[0])
    k = mt(nt, 'DIVIDE', mt(nt, 'ADD', sx.outputs['Z'], -.15), .4, zazhim=True)
    nt.links.new(smes(nt, k, c4('#2e231b'), verh), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .8; bugry(nt, b, n1.outputs['Fac'], .5, .0006)
    return m

def mat_palochki():
    """A dry shoot: lengthwise grooves, blotches (they show the rotation), dark node rings, a charred tip at z=0."""
    m, nt, b = novyy('palochka'); o = obj_koord(nt)
    n1 = shum(nt, o, 1., 4., .5, rastyag=(900, 900, 14)); n2 = shum(nt, o, 55., 3., .55, rastyag=(1, 1, .22)); n3 = shum(nt, o, 260., 3.)
    col = rampa(nt, mt(nt, 'MULTIPLY_ADD', n3.outputs['Fac'], .35, mt(nt, 'MULTIPLY', n1.outputs['Fac'], .65)),
                [(.3, c4('#6f5d44')), (.52, c4('#a8946f')), (.75, c4('#cbb892'))])
    pyatna = mt(nt, 'DIVIDE', mt(nt, 'SUBTRACT', n2.outputs['Fac'], .47), .1, zazhim=True)       # large dark streaks and blotches
    col = smes(nt, mt(nt, 'MULTIPLY', pyatna, .72), col, c4('#4a3a28'))
    mpg = uz(nt, 'ShaderNodeMapping', {'Scale': (1, 1, .4)}); nt.links.new(o, mpg.inputs['Vector'])                 # 'eyes': dark bud scars that make the rotation visible
    vg = uz(nt, 'ShaderNodeTexVoronoi', {'Scale': 70.}); nt.links.new(mpg.outputs[0], vg.inputs['Vector'])
    col = smes(nt, mt(nt, 'MULTIPLY', mt(nt, 'SUBTRACT', 1.0, mt(nt, 'DIVIDE', vg.outputs['Distance'], .22), zazhim=True), .85), col, c4('#2e2216'))
    sx = uz(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(o, sx.inputs[0]); z = sx.outputs['Z']
    kol = mt(nt, 'LESS_THAN', mt(nt, 'PINGPONG', mt(nt, 'DIVIDE', mt(nt, 'SUBTRACT', z, .05), .068), .5), .028)
    col = smes(nt, mt(nt, 'MULTIPLY', kol, .3), col, c4('#3d2f20'))
    konchik = mt(nt, 'DIVIDE', mt(nt, 'SUBTRACT', .02, z), .014, zazhim=True)
    col = smes(nt, konchik, col, c4('#070605'))
    nt.links.new(col, b.inputs['Base Color']); b.inputs['Roughness'].default_value = .62
    bugry(nt, b, n1.outputs['Fac'], .45, .0005)
    return m

def mat_truhi(P, ryab=1.3):
    """Wood dust: node 'chern' 0..1 goes from dark brown to black; the ember uses nodes 'ug-r', 'ug-sila'."""
    m, nt, b = novyy('truha'); pos = mir_koord(nt)
    ch = znach(nt, 'chern', 0.); n1 = shum(nt, pos, 2600., 3.); n2 = shum(nt, pos, 300., 3.)
    col = smes(nt, ch, c4('#2f1d10'), c4('#070605'))
    col = smes(nt, mt(nt, 'MULTIPLY', n2.outputs['Fac'], .7), col, (0, 0, 0, 1))
    ob = zhar(nt, b, P, 'ug', mash=1100., ryab=ryab)
    nt.links.new(smes(nt, mt(nt, 'MULTIPLY', ob, .85), col, (.004, .003, .003, 1)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 1.0; bugry(nt, b, n1.outputs['Fac'], 1.0, .0008)
    return m

def mat_solomy(i, P):
    """Dry grass: straw tones (one per bunch), charring and glow near point P (nodes 'tr-r', 'tr-sila')."""
    m, nt, b = novyy(f'soloma{i}'); pos = mir_koord(nt); rng = np.random.default_rng(100 + i)
    n1 = shum(nt, pos, 38., 3.); n2 = shum(nt, pos, 2200., 2., rastyag=(1, 1, .15))
    f = mt(nt, 'MULTIPLY_ADD', n1.outputs['Fac'], .8, float(rng.uniform(-.12, .28)))
    col = rampa(nt, f, [(.25, c4('#7d6a3f')), (.45, c4('#b39a5f')), (.62, c4('#d2bd84')), (.82, c4('#e5d6a4'))])
    ob = zhar(nt, b, P, 'tr', mash=500.)
    nt.links.new(smes(nt, ob, col, (.006, .005, .004, 1)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .48; bugry(nt, b, n2.outputs['Fac'], .3, .0002)
    return m

def mat_pirita():
    """Pyrite: brass-yellow metal with faceted crystals, a rusty brown crust in places."""
    m, nt, b = novyy('pirit'); o = obj_koord(nt)
    vr = uz(nt, 'ShaderNodeTexVoronoi', {'Scale': 210.}, distance='CHEBYCHEV', feature='F1'); nt.links.new(o, vr.inputs['Vector'])
    sr = uz(nt, 'ShaderNodeSeparateColor'); nt.links.new(vr.outputs['Color'], sr.inputs[0])
    n1 = shum(nt, o, 48., 5., .6); n2 = shum(nt, o, 1300., 3.)
    korka = mt(nt, 'DIVIDE', mt(nt, 'SUBTRACT', n1.outputs['Fac'], .56), .07, zazhim=True)
    met = rampa(nt, sr.outputs[0], [(0, c4('#8f7d42')), (.5, c4('#c2b274')), (1, c4('#e6dba8'))])
    rzh = rampa(nt, n2.outputs['Fac'], [(.3, c4('#3a2112')), (.7, c4('#6e4423'))])
    nt.links.new(smes(nt, korka, met, rzh), b.inputs['Base Color'])
    nt.links.new(mt(nt, 'SUBTRACT', 1.0, korka), b.inputs['Metallic'])
    nt.links.new(mt(nt, 'MULTIPLY_ADD', korka, .62, mt(nt, 'MULTIPLY_ADD', sr.outputs[1], .2, .17)), b.inputs['Roughness'])
    h = mt(nt, 'MULTIPLY_ADD', n2.outputs['Fac'], mt(nt, 'MULTIPLY_ADD', korka, .5, .06), vr.outputs['Distance'])
    bugry(nt, b, h, .55, .0016)
    return m

def mat_kremnya():
    """Flint: dark semi-matte conchoidal fracture; where there was no chip (attribute 'kora' = 1), a light chalky cortex."""
    m, nt, b = novyy('kremen'); o = obj_koord(nt)
    at = uz(nt, 'ShaderNodeAttribute', attribute_name='kora')
    n1 = shum(nt, o, 26., 4., .55); n2 = shum(nt, o, 520., 4., .6)
    wv = uz(nt, 'ShaderNodeTexWave', {'Scale': 55., 'Distortion': 3.5, 'Detail': 2.}, wave_type='RINGS'); nt.links.new(o, wv.inputs['Vector'])
    izlom = rampa(nt, n1.outputs['Fac'], [(.3, c4('#17181b')), (.55, c4('#30333a')), (.8, c4('#585b63'))])
    korka = rampa(nt, n2.outputs['Fac'], [(.3, c4('#7d7361')), (.7, c4('#b3a892'))])
    k = mt(nt, 'DIVIDE', mt(nt, 'SUBTRACT', at.outputs['Fac'], .35), .3, zazhim=True)
    nt.links.new(smes(nt, k, izlom, korka), b.inputs['Base Color'])
    nt.links.new(mt(nt, 'MULTIPLY_ADD', k, .6, .26), b.inputs['Roughness'])
    h = mt(nt, 'MULTIPLY_ADD', wv.outputs['Fac'], mt(nt, 'MULTIPLY_ADD', k, -.1, .1), mt(nt, 'MULTIPLY', n2.outputs['Fac'], k))
    bugry(nt, b, h, .5, .0008)
    return m

def mat_truta(P):
    """Tinder: fluffed-up tinder fungus, brown and suede-like (velvety sheen). The smouldering spot uses nodes 'ug-r', 'ug-sila'."""
    m, nt, b = novyy('trut'); o = obj_koord(nt)
    n1 = shum(nt, o, 55., 5., .6); n2 = shum(nt, o, 1500., 3., .6)
    col = rampa(nt, n1.outputs['Fac'], [(.3, c4('#2b1a0e')), (.55, c4('#4b321c')), (.8, c4('#66482a'))])
    ob = zhar(nt, b, P, 'ug', mash=900.)
    nt.links.new(smes(nt, mt(nt, 'MULTIPLY', ob, .9), col, (.004, .003, .003, 1)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 1.0; b.inputs['Sheen Weight'].default_value = .3; b.inputs['Sheen Roughness'].default_value = .5
    b.inputs['Sheen Tint'].default_value = (.8, .55, .33, 1)
    bugry(nt, b, mt(nt, 'MULTIPLY_ADD', n1.outputs['Fac'], 1.5, n2.outputs['Fac']), .7, .0008)
    return m

def mat_dyma(imya='dym', plotn=30., cvet=(.93, .93, .91), aniz=.5):
    """White smoke without emission: density = density grid x node 'plotn' (input 1 is keyed)."""
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = uz(nt, 'ShaderNodeOutputMaterial'); pv = uz(nt, 'ShaderNodeVolumePrincipled', {'Color': (*cvet, 1), 'Anisotropy': aniz, 'Density Attribute': ''})
    ad = uz(nt, 'ShaderNodeAttribute', attribute_name='density')
    nt.links.new(mt(nt, 'MULTIPLY', ad.outputs['Fac'], plotn, imya='plotn'), pv.inputs['Density']); nt.links.new(pv.outputs[0], out.inputs['Volume'])
    return m

# --------- meshes
def setka(imya, V, F, mat=None, gladko=True, rezko=None):
    me = bpy.data.meshes.new(imya); me.from_pydata([tuple(float(c) for c in v) for v in V], [], F); me.update()
    if gladko: me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    if rezko: me.set_sharp_from_angle(angle=math.radians(rezko))
    o = bpy.data.objects.new(imya, me); sc.collection.objects.link(o)
    for m in (mat if isinstance(mat, (list, tuple)) else [mat] if mat else []): me.materials.append(m)
    return o

def iz_bmesh(imya, bm, mat=None, rezko=None):
    me = bpy.data.meshes.new(imya); bm.to_mesh(me); bm.free(); me.update()
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    if rezko: me.set_sharp_from_angle(angle=math.radians(rezko))
    o = bpy.data.objects.new(imya, me); sc.collection.objects.link(o)
    if mat: me.materials.append(mat)
    return o

def pole(nx, ny, x0, x1, y0, y1, zf):
    """Height-field mesh: zf(x, y) -> z or None (no point). Normals up."""
    xs = np.linspace(x0, x1, nx); ys = np.linspace(y0, y1, ny); idx = {}; V = []
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            z = zf(float(x), float(y))
            if z is not None: idx[(i, j)] = len(V); V.append((x, y, z))
    F = [(idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]) for j in range(ny - 1) for i in range(nx - 1)
         if (i, j) in idx and (i + 1, j) in idx and (i + 1, j + 1) in idx and (i, j + 1) in idx]
    return V, F

def plita(imya, centr, razm, tolsh, seed=1, mat=None, n=200, relyef=.0008):
    """A flat stone: even top (z = centr.z) with fine relief, irregular outline, rounded edges going down by the thickness."""
    a, b = razm[0] / 2, razm[1] / 2
    def zf(x, y):
        ang = math.atan2(y / b, x / a)
        ro = (abs(x / a) ** 3.2 + abs(y / b) ** 3.2) ** (1 / 3.2) / (1 + .08 * noise.noise(Vector((math.cos(ang) * 1.6, math.sin(ang) * 1.6, seed))))
        kr = sm((ro - .84) / .2)
        z = relyef * (noise.fractal(Vector((x * 9, y * 9, seed)), 1, 2, 3) + .4 * noise.fractal(Vector((x * 80, y * 80, seed + 2.5)), 1, 2, 3))
        return z * (1 - kr) - kr ** 1.5 * (tolsh + .01)
    V, F = pole(n, max(8, int(n * b / a)), -a * 1.14, a * 1.14, -b * 1.14, b * 1.14, zf)
    o = setka(imya, V, F, mat); o.location = centr; return o

def zemlya_d(z, seed=3, mat=None):
    """Dry ground: fine relief near the action, a plane into the dark further away."""
    zf = lambda x, y: (.0035 * noise.fractal(Vector((x * 6, y * 6, seed)), 1, 2, 4) + .0012 * noise.fractal(Vector((x * 45, y * 45, seed + 1)), 1, 2, 3)) * sm((.8 - max(abs(x), abs(y))) / .15)
    V, F = pole(230, 230, -.8, .8, -.8, .8, zf); o = setka('zemlya', V, F, mat); o.location = (0, 0, z)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, z - .0015)); p = bpy.context.object; p.name = 'zemlya-dal'
    if mat: p.data.materials.append(mat)
    return o

def rossyp(imya, n, R, razm, seed, mat, z0, iskl=(), centr=(0, 0)):
    """Scattered pebbles and clods as one mesh. iskl: ellipses (x, y, a, b) to keep clear."""
    rng = np.random.default_rng(seed); bm = bmesh.new()
    for i in range(n):
        for _ in range(30):
            r = R * math.sqrt(rng.random()); a = rng.uniform(0, 6.283); x, y = centr[0] + r * math.cos(a), centr[1] + r * math.sin(a)
            if not any(((x - ex) / ea) ** 2 + ((y - ey) / eb) ** 2 < 1 for ex, ey, ea, eb in iskl): break
        s = razm[0] * (razm[1] / razm[0]) ** (rng.random() ** 2.4)
        c = Vector((x, y, z0 + s * .3))
        mtx = Matrix.Translation(c) @ Euler(tuple(rng.uniform(0, 6.28, 3))).to_matrix().to_4x4() @ Matrix.Diagonal((s, s * rng.uniform(.6, 1), s * rng.uniform(.45, .8), 1))
        for v in bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=mtx)['verts']:
            d = v.co - c; v.co = c + d * (1 + .28 * noise.noise(d / s * 1.4 + Vector((i * 1.7, 0, 0))))
    return iz_bmesh(imya, bm, mat)

def vychest(o, rez):
    md = o.modifiers.new('rez', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = rez; md.solver = 'EXACT'
    aktivnyy(o); bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(rez, do_unlink=True)

LUNKA_R, LUNKA_GL, KRAY, TOLSH_OSN = .0072, .0045, .0115, .02
def doshchechka(mats, x0=-.15, x1=.2, shir=.05, seed=2):
    """Drill hearth board: a branch split lengthwise, flat split face on top (z = 0), bark on the sides and bottom. Origin: socket centre on the split face;
    the near edge of the face is at y = -KRAY. The socket is a spherical cup with a V-notch cut through to the near edge."""
    NX, NT, NB = 220, 22, 30; M = NT + NB; V = []; F = []; MI = []
    js = np.concatenate([[0, .028], np.linspace(.07, .93, NT - 3), [.972, 1]])            # a narrow rim of bark along the split edges
    for i in range(NX + 1):
        x = x0 + (x1 - x0) * i / NX; uv = sm((abs(x) - .008) / .03)              # exact dimensions near the socket
        kb = -KRAY - uv * (.0035 * noise.noise(Vector((x * 16, seed, 0))) + .0012 * noise.noise(Vector((x * 70, seed, 2))) + .004 * sm((abs(x) - .05) / .1))   # near edge
        kd = -KRAY + shir * (1 + .1 * noise.noise(Vector((x * 9, seed, 5))) + .03 * noise.noise(Vector((x * 60, seed, 6))))                                    # far edge
        w = (kd - kb) / 2; yc = (kd + kb) / 2; h = TOLSH_OSN * (1 + .08 * uv * noise.noise(Vector((x * 6, seed, 4))))
        for j in range(NT + 1):
            y = kb + 2 * w * js[j]; q = (y - yc) / w
            z = uv * (.0006 * noise.noise(Vector((x * 7, y * 120, seed))) + .0003 * noise.noise(Vector((x * 20, y * 500, seed + 3)))) - .0009 * abs(q) ** 6
            V.append((x, y, z))
        for k in range(1, NB):
            a = math.pi * k / NB; rr = 1 + .035 * noise.fractal(Vector((x * 30, a * 4, seed + 7)), 1, 2, 3)
            V.append((x, yc + w * math.cos(a) * rr, -h * math.sin(a) ** .75 * rr - .0009))
        if i < NX:
            for j in range(M):
                a_, b_ = i * M + j, i * M + (j + 1) % M; F.append((a_, b_, b_ + M, a_ + M)); MI.append(0 if 0 < j < NT - 1 else 1)
    F.append(tuple(range(M - 1, -1, -1))); MI.append(0); F.append(tuple(range(NX * M, NX * M + M))); MI.append(0)
    o = setka('osnova', V, F, mats, gladko=False); o.data.polygons.foreach_set('material_index', MI)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    Rs = (LUNKA_R ** 2 + LUNKA_GL ** 2) / (2 * LUNKA_GL)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=Rs, location=(0, 0, Rs - LUNKA_GL)); vychest(o, bpy.context.object)
    ya, yb, k = -.0034, -KRAY - .02, .6; xb = k * (ya - yb)                      # wedge: apex in the socket, open towards the near edge
    kl_ = setka('klin', [(0, ya, -.04), (-xb, yb, -.04), (xb, yb, -.04), (0, ya, .01), (-xb, yb, .01), (xb, yb, .01)],
                [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], gladko=False)
    bm = bmesh.new(); bm.from_mesh(kl_.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(kl_.data); bm.free()
    vychest(o, kl_)
    o.data.polygons.foreach_set('use_smooth', np.ones(len(o.data.polygons), bool)); o.data.set_sharp_from_angle(angle=math.radians(50))
    return o

def palochka(mat, dl=.42, r=.006, seed=5):
    """Drill stick: a straight dry shoot; origin at the rounded lower tip, Z axis up."""
    NA = 28; zs = list(np.linspace(0, r * 1.25, 12)[1:]) + list(np.linspace(r * 1.25, dl, 170)[1:]); V = [(0, 0, 0)]; F = []
    for z in zs:
        rad = r * (1 - (1 - min(1., z / (r * 1.25))) ** 2) ** .5
        rad *= 1 + .02 * noise.noise(Vector((0, seed, z * 30))) + .045 * math.exp(-((((z - .05) / .068 + .5) % 1 - .5) * .068 / .0045) ** 2)
        cx = .0005 * noise.noise(Vector((z * 16, seed, 1))); cy = .0005 * noise.noise(Vector((z * 16, seed, 7)))
        for k in range(NA):
            a = 2 * math.pi * k / NA; rr = rad * (1 + .025 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, z * 22 + seed))))
            V.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
    for k in range(NA): F.append((0, 1 + (k + 1) % NA, 1 + k))
    for i in range(len(zs) - 1):
        for k in range(NA):
            a_, b_ = 1 + i * NA + k, 1 + i * NA + (k + 1) % NA; F.append((a_, b_, b_ + NA, a_ + NA))
    return setka('palochka', V, F, mat)

def kora_kusok(mat, razm=(.05, .038), tolsh=.0022, seed=3):
    """Bark ember catcher: irregular outline, slightly boat-shaped. Origin in the middle, upper side at z ~ tolsh."""
    a, b = razm[0] / 2, razm[1] / 2; nr, na = 16, 120; V = [(0, 0, tolsh)]; F = []
    for j in range(1, nr + 1):
        for i in range(na):
            an = 2 * math.pi * i / na; u = j / nr
            kr = 1 + .2 * noise.noise(Vector((math.cos(an) * 1.4, math.sin(an) * 1.4, seed))) + .05 * noise.noise(Vector((math.cos(an) * 6, math.sin(an) * 6, seed + 1)))
            x, y = a * u * kr * math.cos(an), b * u * kr * math.sin(an)
            V.append((x, y, tolsh + 1.4 * y * y + .4 * x * x + .0004 * noise.noise(Vector((x * 50, y * 50, seed))) + .0012 * u ** 5 * (1 + math.sin(an * 2 + 1))))
    for i in range(na): F.append((0, 1 + i, 1 + (i + 1) % na))
    for j in range(nr - 1):
        for i in range(na):
            a_, b_ = 1 + j * na + i, 1 + j * na + (i + 1) % na; F.append((a_, a_ + na, b_ + na, b_))
    o = setka('kora-kusok', V, F, mat)
    sd = o.modifiers.new('tol', 'SOLIDIFY'); sd.thickness = tolsh; sd.offset = -1
    return o

def kuchka(mat, R=.0125, H=.0068, seed=4, imya='kuchka'):
    """Dust pile: a cone with scree. Origin at the middle of the base; grows by scale."""
    nr, na = 36, 120; V = [(0, 0, H * .96)]; F = []
    for j in range(1, nr + 1):
        u = j / nr
        for i in range(na):
            a = 2 * math.pi * i / na; Rk = R * (1 + .2 * noise.noise(Vector((math.cos(a) * 1.3, math.sin(a) * 1.3, seed))))
            x, y = math.cos(a) * Rk * u, math.sin(a) * Rk * u
            z = H * (1 - u ** 1.1) * (1 + .16 * noise.noise(Vector((x * 300, y * 300, seed)))) + .0005 * noise.fractal(Vector((x * 1100, y * 1100, 2.)), 1, 2, 2) * (1 - u ** 3) - .0004 * u ** 6
            V.append((x, y, z))
    for i in range(na): F.append((0, 1 + i, 1 + (i + 1) % na))
    for j in range(nr - 1):
        for i in range(na):
            a_, b_ = 1 + j * na + i, 1 + j * na + (i + 1) % na; F.append((a_, a_ + na, b_ + na, b_))
    return setka(imya, V, F, mat)

def nasyp(mat):
    """Dust in the notch: a ramp from the socket down to the pile. Hearth-board local coordinates; origin at catcher level, grows by Z scale."""
    z_niz = -TOLSH_OSN + .003; y0, y1 = -KRAY - .008, -.0032
    def zf(x, y):
        u = (y - y0) / (y1 - y0); hw = .6 * (-.0034 - y) + .0012                  # notch half-width at this y
        if abs(x) > hw * 1.3: return None
        return max(0., .0055 + (TOLSH_OSN - .0105) * u ** .8 - .002 * (x / hw) ** 2 + .0003 * noise.noise(Vector((x * 700, y * 700, 3.))))
    V, F = pole(26, 40, -.0075, .0075, y0, y1, zf); o = setka('nasyp', V, F, mat); return o, z_niz

def koltso(mat):
    """A ring of dust around the socket (open on the notch side). Origin at the socket centre on the face; grows by Z scale."""
    nr, na = 8, 90; V = []; F = []
    for i in range(na):
        a = -math.pi / 2 + .62 + (2 * math.pi - 1.24) * i / (na - 1)
        for j in range(nr):
            u = j / (nr - 1); kon = sm(min(i, na - 1 - i) / 14)
            r = LUNKA_R - .0005 + .0034 * u * kon * (1 + .3 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 5.))) + .2 * noise.noise(Vector((math.cos(a) * 9, math.sin(a) * 9, 2.))))
            z = .0009 * math.sin(math.pi * u) ** .8 * (1 + .4 * noise.noise(Vector((math.cos(a) * 6, math.sin(a) * 6, 1.)))) * kon - .00012
            V.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(na - 1):
        for j in range(nr - 1):
            a_ = i * nr + j; F.append((a_, a_ + 1, a_ + nr + 1, a_ + nr))
    return setka('koltso', V, F, mat)

def krivye(imya, puti, rad, mat=None, razr=2, skos=1):
    """A bundle of thin stems: smooth round-section curves; rad: per-point radii, m."""
    cu = bpy.data.curves.new(imya, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = skos; cu.use_fill_caps = True; cu.resolution_u = razr
    for P, r in zip(puti, rad):
        n = len(P); sp = cu.splines.new('NURBS'); sp.points.add(n - 1)
        sp.points.foreach_set('co', np.concatenate([np.asarray(P, float), np.ones((n, 1))], 1).ravel()); sp.points.foreach_set('radius', np.asarray(r, float))
        sp.order_u = 4; sp.use_endpoint_u = True; sp.use_smooth = True
    o = bpy.data.objects.new(imya, cu); sc.collection.objects.link(o)
    if mat: cu.materials.append(mat)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))        # curves -> mesh: frames re-evaluate faster
    bpy.data.objects.remove(o, do_unlink=True); bpy.data.curves.remove(cu)
    o = bpy.data.objects.new(imya, me); sc.collection.objects.link(o)
    return o

def gnezdo(imya, centr, mats, R0=.026, R1=.058, vys=.034, n=460, seed=1, dl=(.06, .14), tolsh=(.0002, .0004), dno=.16, vylet=.03):
    """A dry-grass 'bird's nest': blades run in circles, wider higher up; bottom ones lie across; ends stick out."""
    rng = np.random.default_rng(seed); G = len(mats); puti = [[] for _ in range(G)]; rad = [[] for _ in range(G)]; npt = 15; s = np.linspace(0, 1, npt)
    for _ in range(n):
        L_ = rng.uniform(*dl); ph = rng.uniform(0, 6.28, 6)
        if rng.random() < dno:                                   # bottom stems: almost straight, across the middle
            a = rng.uniform(0, 2 * math.pi); d = np.array([math.cos(a), math.sin(a)]); nr = np.array([-d[1], d[0]])
            x = (s - .5) * L_; bok = rng.normal(0, .014) + rng.normal(0, .007) * (1 - (2 * s - 1) ** 2)
            P = np.stack([d[0] * x + nr[0] * bok, d[1] * x + nr[1] * bok, rng.uniform(.001, .008) + .012 * np.abs(2 * s - 1) ** 2.5 * rng.uniform(.2, 1.2)], 1)
        else:
            u = rng.beta(1.25, 1.1); r0 = max(.012, R0 + (R1 - R0) * u ** .8 + rng.normal(0, .004)); z0 = .003 + vys * u ** 1.45
            ang = rng.uniform(0, 2 * math.pi) + rng.choice([-1, 1]) * L_ / r0 * s
            kon = np.clip((np.abs(s - .5) * 2 - .62) / .38, 0, 1) ** 1.6                          # the ends leave the circle
            v_r = np.where(s < .5, rng.uniform(0, vylet), rng.uniform(0, vylet)) * kon; v_z = np.where(s < .5, rng.uniform(-.2, 1), rng.uniform(-.2, 1)) * vylet * .7 * kon
            rr = r0 * (1 + .1 * np.sin(2 * ang + ph[0])) + v_r
            x, y = rr * np.cos(ang) * (1 + rng.normal(0, .08)), rr * np.sin(ang)
            nak, an = rng.normal(0, .17), rng.uniform(0, 2 * math.pi)
            P = np.stack([x, y, z0 + nak * (x * math.cos(an) + y * math.sin(an)) + v_z], 1)
        P += .0028 * np.stack([np.sin(s * 9 + ph[1]) + .5 * np.sin(s * 23 + ph[2]), np.sin(s * 8 + ph[3]) + .5 * np.sin(s * 21 + ph[4]), .7 * np.sin(s * 10 + ph[5])], 1)
        P[:, 2] = np.maximum(P[:, 2], .0006 + rng.uniform(0, .001))
        g = rng.integers(0, G); puti[g].append(P); rad[g].append(rng.uniform(*tolsh) * (.4 + .6 * np.sin(math.pi * s) ** .5))
    obs = []
    for g in range(G):
        o = krivye(f'{imya}{g}', puti[g], rad[g], mats[g]); o.location = centr; obs.append(o)
    return obs

def komok_truta(centr, mat, m_vors, razm=(.03, .027, .017), seed=6):
    """A lump of tinder (fluffed tinder fungus): a soft lumpy ball + short fibres over the surface."""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0); off = Vector((seed * 3.1, 1.7, .3))
    for v in bm.verts:
        p = v.co.copy(); k = 1 + .2 * noise.fractal(p * 1.4 + off, 1, 2, 3) + .05 * noise.noise(p * 6 + off)
        v.co = Vector((p.x * razm[0] * k, p.y * razm[1] * k, p.z * razm[2] * k * (1. if p.z > 0 else .55)))
    P = np.array([v.co[:] for v in bm.verts]); o = iz_bmesh('trut', bm, mat); o.location = centr
    rng = np.random.default_rng(seed); puti, rad = [], []
    for i in rng.choice(len(P), 420, replace=False):
        p = P[i]
        if p[2] < -.002: continue
        d = p / np.array(razm) ** 2; d /= np.linalg.norm(d); d = d + rng.normal(0, .55, 3); d /= np.linalg.norm(d)
        l = rng.uniform(.002, .006); izg = rng.normal(0, .5, 3) * l
        puti.append(np.stack([p * .98 + d * l * u + izg * u * u for u in np.linspace(0, 1, 5)])); rad.append(np.linspace(.00012, .00004, 5))
    vo = krivye('trut-vors', puti, rad, m_vors, razr=1, skos=0); vo.location = centr
    return o, P + np.array(centr)

def pirit(centr, mat, razm=(.036, .031, .027), seed=4):
    """A pyrite nodule: a lumpy ball with embedded cubic crystals. Returns the object and its vertices in world coordinates."""
    rng = np.random.default_rng(seed); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0); off = Vector((seed * 2.3, .7, 1.1))
    def poverh(p):
        k = 1 + .15 * noise.fractal(p * 1.3 + off, 1, 2, 3) + .13 * abs(noise.noise(p * 3.1 + off)) - .04
        return Vector((p.x * razm[0] * k, p.y * razm[1] * k, max(p.z, -.82) * razm[2] * k))
    for v in bm.verts: v.co = poverh(v.co.copy())
    for i in range(16):
        d = Vector(rng.normal(0, 1, 3)); d.z = abs(d.z) * .8 + .1; d.normalize(); s = rng.uniform(.005, .011)
        mtx = Matrix.Translation(poverh(d) * .97) @ Euler(tuple(rng.uniform(0, 1.57, 3))).to_matrix().to_4x4()
        bmesh.ops.create_cube(bm, size=s, matrix=mtx)
    P = np.array([v.co[:] for v in bm.verts]); o = iz_bmesh('pirit', bm, mat, rezko=38); o.location = centr
    return o, P + np.array(centr)

def kremen(mat, razm=(.03, .021, .056), seed=7, skolov=44):
    """Flint: an elongated nodule knapped with chips (concave conchoidal facets, sharp ridges), a sharp edge at the bottom.
    Origin at the lowest point of the striking edge, Z axis up along the stone. Attribute 'kora': 1 = cortex, 0 = fresh fracture."""
    rng = np.random.default_rng(seed); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
    P = np.array([v.co[:] for v in bm.verts]); u = (P[:, 2] + 1) / 2
    sh = np.array([noise.fractal(Vector(p) * 1.2 + Vector((seed, 0, 0)), 1, 2, 3) for p in P])
    P = P * np.array(razm) * (1 + .12 * sh)[:, None]; P[:, 1] *= .3 + .7 * u ** .7; P[:, 0] *= .55 + .45 * np.sin(math.pi * np.clip(u * .8 + .2, 0, 1)) ** .6
    kora = np.ones(len(P)); R0 = np.array(razm)
    sk = [(np.array([.0, 1., -.75]), .05, .006), (np.array([.0, -1., -.75]), .05, .006), (np.array([.9, .5, -.5]), .04, .005), (np.array([-.9, -.5, -.55]), .04, .005)]
    for d, R, gl in sk:
        d = d / np.linalg.norm(d); i0 = np.argmax(P @ d); c = P[i0] + d * (R - gl)        # a sphere cuts into the stone to depth gl
        r = np.linalg.norm(P - c, axis=1); m = r < R
        P[m] = c + (P[m] - c) / r[m, None] * R; kora[m] = 0
    sk = []; cen = P.mean(0)
    for _ in range(skolov):
        i0 = rng.integers(0, len(P))
        if u[i0] > .86 and rng.random() < .8: continue                             # keep the cortex near the top
        d = (P[i0] - cen) / R0 ** 2; d /= np.linalg.norm(d); d = d + rng.normal(0, .25, 3); sk.append((i0, d, rng.uniform(.03, .09), rng.uniform(.0012, .003)))
    for i0, d, R, gl in sk:
        d = d / np.linalg.norm(d); c = P[i0] + d * (R - gl)
        r = np.linalg.norm(P - c, axis=1); m = r < R
        P[m] = c + (P[m] - c) / r[m, None] * R; kora[m] = 0
    P -= P[np.argmin(P[:, 2])]
    bm.verts.index_update(); sosedi = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
    for _ in range(5): kora = np.array([.4 * kora[i] + .6 * kora[s_].mean() for i, s_ in enumerate(sosedi)])     # smooth cortex boundary, no 'staircase'
    for v, p in zip(bm.verts, P): v.co = p
    o = iz_bmesh('kremen', bm, mat, rezko=24)
    at = o.data.attributes.new('kora', 'FLOAT', 'POINT'); at.data.foreach_set('value', kora.astype(np.float32))
    return o

# --------- light, volumes, camera
def svet(imya, mesto, cel=None, sila=5., cvet=(1., .5, .2), radius=.03, konus=None, fn=None, drozh=0., seed=1, ten=True, obyom=1.0, kach=0.):
    """A light keyed on every frame: strength x fn(t) x lively flicker (drozh = depth), kach = source sway, m."""
    ld = bpy.data.lights.new(imya, 'SPOT' if konus else 'POINT'); ld.color = cvet; ld.shadow_soft_size = radius; ld.use_shadow = ten; ld.volume_factor = obyom
    if konus: ld.spot_size = math.radians(konus); ld.spot_blend = .75
    for k_, v_ in dict(use_shadow_jitter=True, shadow_jitter_overblur=10.0, shadow_filter_radius=1.0, shadow_maximum_resolution=.0002).items():
        try: setattr(ld, k_, v_)
        except Exception: pass
    o = bpy.data.objects.new(imya, ld); sc.collection.objects.link(o); o.location = mesto
    if cel is not None: smotret(o, cel)
    rng = np.random.default_rng(seed); n = NF + 3; t = np.arange(n) / FPS
    f = 1 + drozh * (.45 * np.sin(t * 9.1 + rng.uniform(0, 6)) + .3 * np.sin(t * 17.3 + rng.uniform(0, 6)) + .25 * np.sin(t * 31.7 + rng.uniform(0, 6)))
    f += drozh * .35 * np.convolve(rng.standard_normal(n), np.ones(3) / 3, 'same')
    for i in range(n):
        ld.energy = float(sila * max(.05, f[i]) * (fn(tk(i)) if fn else 1.)); ld.keyframe_insert('energy', frame=i)
        if kach:
            o.location = (mesto[0] + kach * math.sin(t[i] * 7.7 + 1.3), mesto[1], mesto[2] + kach * 1.3 * math.sin(t[i] * 11.1 + .4)); o.keyframe_insert('location', frame=i)
    return o

def obyom(kesh, imya, mat, tochka, mash=1.0, sdvig=0, pol_shir=.2, z_ist=.012, vys=1.0):
    """A baked volume placed so its source sits at tochka. No cache: skip it (the scene builds without it)."""
    kd = f'{ROOT}/sim/{kesh}'
    if not os.path.exists(kd + '/gotovo.txt'): print('!! no cache', kesh, '- no volume', imya); return None
    o = obyom_iz_kesha(kd, imya=imya, mat=mat, sdvig=sdvig, rezhim='CLIP'); o.scale = (mash, mash, mash * vys)
    o.data.frame_duration = 100000        # otherwise the volume vanishes after the cache frame count (in SCENE frames, before the offset); frames outside the cache simply do not exist and stay empty
    o.location = (tochka[0] - pol_shir * mash, tochka[1] - pol_shir * mash, tochka[2] - z_ist * mash * vys)
    return o

def iskry_d():
    """Sparks with an orange-red tint (pyrite and burning grass give dim sparks, not white ones)."""
    isk = Iskry('iskry', sila=ISKRY_SILA); nti = isk.mat.node_tree
    nti.links.new(smes(nti, 1.0, [n for n in nti.nodes if n.bl_idname == 'ShaderNodeAttribute'][0].outputs['Color'], (1., .5, .2, 1), 'MULTIPLY'),
                  [n for n in nti.nodes if n.bl_idname == 'ShaderNodeEmission'][0].inputs['Color'])
    return isk

def iskorki(isk, P, T0):
    """Sparse small sparks rising above the flame from T0."""
    isk.vsplesk(T0 + .25, tuple(V3(P) + Vector((0, 0, .02))), napr=(0, 0, 1), n=ISKOROK, skorost=(.15, .5), konus=.45, zhizn=(.5, 1.2), g=0, drag=1.4, r=.00045, yark=.9,
                razbros_mesta=.01, turb=1.2, pod=.8, dlit=max(.3, DLIT - T0 - .6), ostyv=1.2)

def plamya(P, T0):
    """Flame from the trut cache at P from T0: two volumes (offset in space and time so the tongues are uneven). Colour: ramp compressed towards low grid values."""
    m = mat_ognya('ogon', sila=OGON_SILA[PLAN], dym=.03)
    for e in list([n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB'][0].color_ramp.elements)[1:-1]: e.position *= OGON_SZHAT
    for n in m.node_tree.nodes:                               # steeper exponent: the faint haze around the tongues dies out, the core is brighter, the flame is crisper
        if n.bl_idname == 'ShaderNodeMath' and n.operation == 'POWER': n.inputs[1].default_value = OGON_STEPEN
    for i, (dx, dy, ms, dk) in enumerate(OGON_YAZYKI):
        obyom('trut', f'ogon{i}', m, V3(P) + Vector((dx, dy, 0)), mash=ms, sdvig=KESH_OGON0 + dk - int(T0 * FPS + 1), pol_shir=.25, z_ist=.025, vys=OGON_VYS)

def kamera_d(lens, fstop, a, b, fokus):
    """Camera: slow push-in/orbit from a to b (dict: c target, d distance, az azimuth deg, el elevation deg); fokus(t): focus point."""
    kam = kamera(lens=lens, dof=.5, fstop=fstop); kam.data.clip_start = .03; kam.data.clip_end = 80
    for n in range(0, NF + 2):
        u = max(0., min(1., tk(n) / DLIT)); u = .5 * u + .5 * sm(u)
        c = V3(a['c']).lerp(V3(b['c']), u); d = a['d'] + (b['d'] - a['d']) * u
        az = math.radians(a['az'] + (b['az'] - a['az']) * u); el = math.radians(a['el'] + (b['el'] - a['el']) * u)
        p = c + d * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        kam.location = p; smotret(kam, c); kam.data.dof.focus_distance = (V3(fokus(tk(n))) - p).dot((c - p).normalized())
        kam.keyframe_insert('location', frame=n); kam.keyframe_insert('rotation_euler', frame=n); kam.data.dof.keyframe_insert('focus_distance', frame=n)
    return kam

def solominki(imya, n, R, z, mat, seed=8, centr=(0, 0), iskl=()):
    """Sparse dry grass blades lying on the stone/ground."""
    rng = np.random.default_rng(seed); puti, rad = [], []; s = np.linspace(0, 1, 8)
    for _ in range(n):
        for _k in range(30):
            r = R * math.sqrt(rng.random()); a = rng.uniform(0, 6.283); x, y = centr[0] + r * math.cos(a), centr[1] + r * math.sin(a)
            if not any(((x - ex) / ea) ** 2 + ((y - ey) / eb) ** 2 < 1 for ex, ey, ea, eb in iskl): break
        a = rng.uniform(0, 6.283); l = rng.uniform(.03, .11); izg = rng.normal(0, .012)
        P = np.stack([x + math.cos(a) * (s - .5) * l - math.sin(a) * izg * (1 - (2 * s - 1) ** 2), y + math.sin(a) * (s - .5) * l + math.cos(a) * izg * (1 - (2 * s - 1) ** 2),
                      z + .0005 + rng.uniform(0, .004) * s ** 2], 1)
        puti.append(P); rad.append(np.full(8, rng.uniform(.0003, .0006)))
    return krivye(imya, puti, rad, mat)

def osveshchenie(F, kontr_cel, sleva=True):
    """Shared shot lighting: a warm flickering side light 'from a nearby fire', a rim light from behind (shows the smoke), a faint cold fill."""
    F = V3(F); s = -1 if sleva else 1
    svet('klyuch', F + Vector((s * .40, -.22, .17)), F, sila=SVET_KLYUCH[PLAN], cvet=(1., .52, .2), radius=.05, konus=36, drozh=.13, seed=2, kach=.012)
    svet('kontr', F + Vector((-s * .16, .42, .2)), kontr_cel, sila=SVET_KONTR[PLAN], cvet=(1., .74, .48), radius=.04, konus=34, drozh=.06, seed=3, obyom=1.6)
    svet('holod', F + Vector((-s * .34, -.42, .4)), F, sila=SVET_HOLOD[PLAN], cvet=(.5, .66, 1.), radius=.12, konus=50, seed=4, obyom=.5)

# ========= shot D1a: friction
def hody():
    """Spin schedule: passes (t0, t1, direction); PAUZA stops between groups of passes, nothing after T_STOP."""
    out = []; t = 0.; napr = 1
    for g in list(PAUZY) + [T_STOP]:
        k = max(1, round((g - t) / HOD)); d = (g - t) / k
        for i in range(k): out.append((t + i * d, t + (i + 1) * d, napr)); napr = -napr
        t = g + PAUZA
    return out

def plan_D1a():
    m_plita = mat_plity(); m_zem = mat_zemli_d()
    plita('plita', (.03, .05, 0), (.66, .5), .035, seed=2, mat=m_plita, n=230); zemlya_d(-.035, mat=m_zem)
    rossyp('galka', 260, .7, (.002, .016), 5, mat_plity('galka', ('#3a352f', '#7a7266'), 60.), -.035, iskl=[(.03, .05, .37, .29)])
    ugl = math.radians(7.); M = Matrix.Translation((0, 0, TOLSH_OSN)) @ Matrix.Rotation(ugl, 4, 'Z')         # base: the socket at (0, 0, TOLSH_OSN)
    LUN = Vector((0, 0, TOLSH_OSN))
    m_skol = mat_skola(); osn = doshchechka([m_skol, mat_kory_d()]); osn.matrix_world = M
    kk = kora_kusok(mat_luba()); kk.matrix_world = Matrix.Translation(M @ Vector((.004, -KRAY - .011, -TOLSH_OSN))) @ Matrix.Rotation(ugl + .5, 4, 'Z')
    P_k = M @ Vector((.0005, -KRAY - .0035, -TOLSH_OSN + .0027))                                               # base of the dust pile
    P_ug = P_k + Vector((.0022, -.0042, .0042))                                                              # the ember sits on the pile slope facing the camera
    m_tr = mat_truhi(P_ug); ku = kuchka(m_tr); ku.location = P_k
    ns, z_niz = nasyp(m_tr); ns.matrix_world = M @ Matrix.Translation((0, 0, z_niz))
    ko = koltso(m_tr); ko.matrix_world = M
    kro = rossyp('kroshki', 22, .013, (.0003, .0008), 9, m_tr, .0003, centr=(0, -.003)); kro.location = P_k
    pal = palochka(mat_palochki()); pal.rotation_mode = 'ZXY'; z_dno = TOLSH_OSN - LUNKA_GL + .0002
    H_ = hody(); NT = m_tr.node_tree.nodes; ug_s = m_skol.node_tree.nodes['ugol'].outputs[0]
    def ugolyok(t):                                               # (radius, glow strength) of the ember
        v = sm((t - T_UGOL) / .7); d = t - T_UGOL
        return .0006 + .0022 * sm(d / 1.0), 0. if d < 0 else UGOL_SILA * v * (1 + .3 * math.sin(d * 10.5) + .12 * math.sin(d * 23. + 1.))
    for n in range(0, NF + 2):
        t = tk(n); spin = 0.; faza = 0.
        for t0, t1, napr in H_:
            u = max(0., min(1., (t - t0) / (t1 - t0))); pl = (1 - math.cos(math.pi * u)) / 2; spin += napr * OBOROTOV * 2 * math.pi * pl; faza += math.pi * pl
        uh = max(0., t - T_STOP - .08); pod = .13 * min(uh / .7, 2.5) ** 2                                   # after the stop the stick lifts away
        pal.location = (0, 0, z_dno + .00025 * math.sin(faza * 2) + pod)
        pal.rotation_euler = (math.radians(1.1) * math.sin(faza) + .03 * sm(uh / .6), math.radians(.8) * math.sin(faza * .5 + 1.) - .02 * sm(uh / .6), spin)
        pal.keyframe_insert('location', frame=n); pal.keyframe_insert('rotation_euler', frame=n)
        r = max(.02, max(0., min(1., (t - T_TRUHA) / (T_STOP - T_TRUHA))) ** .45)
        ku.scale = (r, r, r); ku.keyframe_insert('scale', frame=n)
        sn = sm((t - T_TRUHA) / 2.4); ns.scale = (1, 1, max(.01, sn)); ns.location = (0, 0, TOLSH_OSN + z_niz - .006 * (1 - sm(sn * 8))); ns.keyframe_insert('scale', frame=n); ns.keyframe_insert('location', frame=n)
        kro.scale = (max(.001, sm((t - T_TRUHA - .5) / 2.5)),) * 3; kro.keyframe_insert('scale', frame=n)
        sk = sm((t - T_TRUHA + .2) / 3.2); ko.scale = (1, 1, max(.01, sk)); ko.location = (0, 0, TOLSH_OSN - .0006 * (1 - sm(sk * 4))); ko.keyframe_insert('scale', frame=n); ko.keyframe_insert('location', frame=n)
        kl(NT['chern'].outputs[0], sm((t - 1.1) / 3.2), n); kl(ug_s, sm((t - .5) / 4.), n)
        ur, us = ugolyok(t); kl(NT['ug-r'].outputs[0], ur, n); kl(NT['ug-sila'].outputs[0], us, n)
    svet('ugolyok', P_ug + Vector((0, -.003, .004)), sila=.04, cvet=(1., .3, .06), radius=.003, fn=lambda t: ugolyok(t)[1] / UGOL_SILA * (ugolyok(t)[0] / .0028) ** 2, ten=False, obyom=0.)
    osveshchenie(LUN, LUN + Vector((0, 0, .06)))
    # smoke: from the socket (from T_DYM, weaker after the stop) and from the dust pile (smokes by itself towards the end)
    k1 = lambda t: DYM_PLOTN[PLAN] * sm((t - T_DYM) / .5) * (1 - .8 * sm((t - T_STOP - .15) / 1.0)); k2 = lambda t: DYM_PLOTN[PLAN] * 1.5 * sm((t - T_STOP + .5) / 1.3)
    d1 = obyom('dymok', 'dym-lunka', mat_dyma('dym1'), M @ Vector((.009, .004, -.003)), mash=.38, sdvig=KESH_DYM0 - int(T_DYM * FPS + 1))
    d2 = obyom('dymok', 'dym-kuchka', mat_dyma('dym2'), P_ug + Vector((0, .002, -.002)), mash=.42, sdvig=-12)
    for d_, fn in ((d1, k1), (d2, k2)):
        if d_ is None: continue
        s_ = d_.data.materials[0].node_tree.nodes['plotn'].inputs[1]
        for n in range(0, NF + 2): kl(s_, fn(tk(n)), n)
    F_l = LUN + Vector((0, -.006, -.001)); fokus = lambda t: F_l.lerp(P_ug, sm((t - T_STOP + .1) / .8))
    kam = kamera_d(85, 4.0, dict(c=(.014, -.008, .023), d=.47, az=9, el=30), dict(c=(.01, -.012, .017), d=.405, az=13, el=32), fokus)
    return dict(kam=kam, tochki=lambda n: dict(lunka=tuple(LUN), ugolyok=tuple(P_ug)), pered=lambda n: None,
                vremena=dict(dym=T_DYM, stop=T_STOP, ugolyok=T_UGOL, pauzy=PAUZY))

# ========= shot D1b: ember in dry grass
def plan_D1b():
    m_plita = mat_plity(); m_zem = mat_zemli_d()
    plita('plita', (.03, .05, 0), (.66, .5), .035, seed=2, mat=m_plita, n=230); zemlya_d(-.035, mat=m_zem)
    rossyp('galka', 260, .7, (.002, .016), 5, mat_plity('galka', ('#3a352f', '#7a7266'), 60.), -.035, iskl=[(.03, .05, .37, .29)])
    P_kora = Vector((0, -.004, .013)); P_k = P_kora + Vector((.002, -.001, .0026)); P_ug = P_k + Vector((.001, -.0035, .0045))
    ms = [mat_solomy(i, P_ug) for i in range(5)]
    gnezdo('gnezdo', (0, 0, 0), ms, R0=.027, R1=.056, vys=.03, n=470, seed=3)
    solominki('sor', 12, .22, 0., ms[0], seed=5, iskl=[(0, 0, .09, .09)])
    kk = kora_kusok(mat_luba(), razm=(.044, .034)); kk.location = P_kora; kk.rotation_euler = (.06, -.05, .7)
    m_tr = mat_truhi(P_ug, ryab=.4); m_tr.node_tree.nodes['chern'].outputs[0].default_value = 1.0; ku = kuchka(m_tr); ku.location = P_k
    rossyp('kroshki', 40, .016, (.0003, .0011), 9, m_tr, P_k.z + .0002, centr=(P_k.x, P_k.y - .002))
    plam = lambda t: sm((t - T_PLAMYA_B) / 1.9)                   # flame growth 0..1
    def ugolyok(t):
        return .002 + .002 * sm(t / T_PLAMYA_B) + .001 * plam(t), UGOL_SILA * (.6 + .25 * sm(t / 1.0)) * (1 + .28 * math.sin(t * 9.5) + .1 * math.sin(t * 21. + 1.))
    NT = m_tr.node_tree.nodes
    for n in range(0, NF + 2):
        t = tk(n); ur, us = ugolyok(t); kl(NT['ug-r'].outputs[0], ur, n); kl(NT['ug-sila'].outputs[0], us, n)
        for m in ms:                                              # grass around the ember chars and glows
            kl(m.node_tree.nodes['tr-r'].outputs[0], .004 + .006 * sm(t / T_PLAMYA_B) + .016 * plam(t), n)
            kl(m.node_tree.nodes['tr-sila'].outputs[0], .25 + .35 * sm(t / T_PLAMYA_B) + .4 * plam(t), n)
    svet('ugolyok', P_ug + Vector((0, -.004, .006)), sila=.03, cvet=(1., .32, .07), radius=.004, fn=lambda t: ugolyok(t)[1] / UGOL_SILA * (ugolyok(t)[0] / .004) ** 1.5 * (1 - .7 * plam(t)), ten=False, obyom=0.)
    svet('plamya', P_ug + Vector((0, -.025, .085)), sila=SVET_PLAMENI[PLAN], cvet=(1., .62, .3), radius=.03, fn=lambda t: plam(t) ** 1.3 * (1 + .6 * sm((t - 2.2) / 1.2)), drozh=.3, seed=7,
         kach=.006, obyom=.12)
    osveshchenie((0, 0, .03), P_ug + Vector((0, 0, .09)))
    d1 = obyom('dymok', 'dym', mat_dyma('dym1', cvet=(.95, .9, .74)), P_ug + Vector((0, .003, -.004)), mash=.5, sdvig=150)
    if d1 is not None:
        s_ = d1.data.materials[0].node_tree.nodes['plotn'].inputs[1]
        for n in range(0, NF + 2): kl(s_, DYM_PLOTN[PLAN] * (.75 + .25 * sm(tk(n) / 1.0)) * (1 - .97 * sm((tk(n) - T_PLAMYA_B + .1) / 1.0)), n)
    plamya(P_ug + Vector((-.004, .004, -.012)), T_PLAMYA_B); isk = iskry_d(); iskorki(isk, P_ug, T_PLAMYA_B)
    kam = kamera_d(85, 4.0, dict(c=(.016, 0, .05), d=.6, az=-7, el=22), dict(c=(.014, 0, .056), d=.54, az=-3, el=21), lambda t: P_ug)
    return dict(kam=kam, tochki=lambda n: dict(gnezdo=tuple(P_ug)), pered=lambda n: isk.obnovit(tk(n), vyderzhka=ISKRY_SLED), vremena=dict(plamya=T_PLAMYA_B))

# ========= shot D2: sparks from stone
def plan_D2():
    m_zem = mat_zemli_d(); zemlya_d(0., mat=m_zem)
    Z_K = .05; plita('kamen-plita', (-.13, .03, Z_K), (.31, .26), Z_K, seed=6, mat=mat_plity('plita', ('#3a3631', '#77706a'), 30.), n=170, relyef=.0012)
    rossyp('galka', 240, .7, (.002, .018), 5, mat_plity('galka', ('#3a352f', '#7a7266'), 60.), 0., iskl=[(-.13, .03, .18, .15), (.064, -.02, .075, .075)])
    C_P = Vector((-.024, -.002, Z_K + .0215)); pi, PV = pirit(C_P, mat_pirita())
    napr_u = Vector((.6, -.32, .73)).normalized(); S = Vector(PV[np.argmax((PV - np.array(C_P)) @ np.array(napr_u))])     # strike point: the right 'shoulder' of the pyrite
    nrm = (S - C_P).normalized(); kas = Vector((0, 0, -1)) - nrm * nrm.dot(Vector((0, 0, -1))); kas.normalize()          # tangent down the shoulder
    # tinder in a nest of dry grass: close by and lower
    C_G = Vector((.064, -.02, 0)); C_T = C_G + Vector((-.008, 0, .02))
    isk = iskry_d()
    P_t0 = C_T + Vector((-.008, -.011, .013)); napr_i = (kas * .3 + (P_t0 + Vector((.012, 0, .03)) - S).normalized() * .7).normalized()
    for T, n_i in zip(T_UDARY, ISKR):
        isk.vsplesk(T, tuple(S), napr=tuple(napr_i), n=n_i, skorost=(.8, 1.5), konus=.26, zhizn=(.18, .45), g=9.8, drag=1.0, pol=C_T.z + .0165, otskok=.1, r=ISKRY_R,
                    yark=1.2, razbros_mesta=.002)
    kon = isk.P[-1]['pos'][:, -1, :]; i_b = int(np.argmin(np.linalg.norm(kon[:, :2] - np.array(P_t0[:2]), axis=1)))       # where the spark of the last strike landed
    ms = [mat_solomy(i, (0, 0, 0)) for i in range(5)]
    m_trut = mat_truta((0, 0, 0)); tr, TV = komok_truta(C_T, m_trut, mat_prostoy('vors', L('#5a3f25'), 1.0))
    xy = np.array(kon[i_b][:2]); xy = np.array(C_T[:2]) + (xy - np.array(C_T[:2])) * min(1., .02 / (np.linalg.norm(xy - np.array(C_T[:2])) + 1e-9))
    bl = np.linalg.norm(TV[:, :2] - xy, axis=1) < .004; P_t = Vector((xy[0], xy[1], TV[bl, 2].max()))                    # the smouldering spot sits on the tinder surface
    m_trut.node_tree.nodes['ug-mesto'].inputs[1].default_value = tuple(P_t)
    for m in ms: m.node_tree.nodes['tr-mesto'].inputs[1].default_value = tuple(P_t + Vector((0, -.004, 0)))
    gnezdo('gnezdo', tuple(C_G), ms, R0=.031, R1=.06, vys=.03, n=470, seed=5)
    solominki('sor', 9, .1, .003, ms[1], seed=6, centr=(.04, -.15), iskl=[(-.13, .03, .17, .14), (.064, -.02, .08, .08)])
    kr = kremen(mat_kremnya()); kr.rotation_mode = 'QUATERNION'
    os_k = (-kas + nrm * .55 + Vector((-.1, .25, 0))).normalized(); q0 = os_k.to_track_quat('Z', 'Y')                   # the stone extends up and back from the striking edge
    P_pokoy = S - kas * .015 + nrm * .006 + Vector((0, 0, .003))
    def kremen_t(t):
        """Striking-edge position and tilt: wind-up, a fast glancing blow down, a short rebound, return. After the last strike it lifts away."""
        p = P_pokoy.copy(); nak = 0.
        for T in T_UDARY:
            d = t - T
            if -.42 < d <= -T_VNIZ: u = sm((d + .42) / (.42 - T_VNIZ)); p = P_pokoy + (-kas * .014 + nrm * .006) * u; nak = -.06 * u
            elif -T_VNIZ < d <= 0: u = (d + T_VNIZ) / T_VNIZ; u = u * u; p = (P_pokoy - kas * .014 + nrm * .006).lerp(S, u); nak = -.06 + .16 * u
            elif 0 < d <= .05: u = d / .05; p = S + kas * .014 * u + nrm * .003 * u; nak = .1 + .05 * u
            elif .05 < d <= .5: u = sm((d - .05) / .45); p = (S + kas * .014 + nrm * .003).lerp(P_pokoy, u) + nrm * .01 * math.sin(math.pi * u); nak = .15 * (1 - u)
        u = sm((t - T_UDARY[-1] - .45) / .9)
        return p + Vector((-.02, 0, .2)) * u * u, nak
    def tleet(t):                                                 # (radius, strength) of the smouldering spot on the tinder: 2 mm -> 8 mm by T_TLEET_MAX, then the glow grows with the flame
        d = t - T_TLEET
        if d < 0: return .0005, 0.
        r = .001 + .003 * sm(d / (T_TLEET_MAX - T_TLEET)) + .006 * sm((t - T_TRAVA) / 1.8)
        return r, UGOL_SILA * 1.2 * sm(d / .25) * (1 + .3 * math.sin(d * 9.) + .12 * math.sin(d * 22. + 1.)) * (1 + .6 * sm((t - T_TRAVA) / 1.5))
    plam = lambda t: sm((t - T_TRAVA) / 2.1)
    os_n = Vector((0, 1, 0)).cross(os_k).normalized(); NT = m_trut.node_tree.nodes
    for n in range(0, NF + 2):
        t = tk(n); p, nak = kremen_t(t); kr.location = p; kr.rotation_quaternion = Quaternion(os_n, nak) @ q0
        kr.keyframe_insert('location', frame=n); kr.keyframe_insert('rotation_quaternion', frame=n)
        dr = sum(math.exp(-(t - T) / .07) * math.sin((t - T) * 95.) for T in T_UDARY if t >= T)                           # the pyrite jolts on each strike
        pi.location = C_P + kas * .0012 * dr; pi.keyframe_insert('location', frame=n)
        ur, us = tleet(t); kl(NT['ug-r'].outputs[0], ur, n); kl(NT['ug-sila'].outputs[0], us, n)
        for m in ms:
            kl(m.node_tree.nodes['tr-r'].outputs[0], .0005 + .006 * sm((t - T_TRAVA + .5) / .6) + .016 * plam(t), n)
            kl(m.node_tree.nodes['tr-sila'].outputs[0], .4 * sm((t - T_TRAVA + .4) / .5) + .4 * plam(t), n)
    svet('vspyshka', S + nrm * .012 + kas * .01, sila=.25, cvet=(1., .55, .2), radius=.004, ten=False,
         fn=lambda t: sum(math.exp(-(t - T) / .035) for T in T_UDARY if t >= T - .001), obyom=0.)
    svet('tleet', P_t + Vector((0, -.003, .005)), sila=.05, cvet=(1., .3, .06), radius=.003, fn=lambda t: tleet(t)[1] / UGOL_SILA * (tleet(t)[0] / .004) ** 1.5, ten=False, obyom=0.)
    svet('plamya', P_t + Vector((.004, -.025, .085)), sila=SVET_PLAMENI[PLAN], cvet=(1., .62, .3), radius=.03, fn=lambda t: plam(t) ** 1.3, drozh=.3, seed=7, kach=.006, obyom=.12)
    F_ = (S + P_t) / 2; osveshchenie(F_, P_t + Vector((0, 0, .08)))
    d1 = obyom('dymok', 'dym', mat_dyma('dym1'), P_t + Vector((0, 0, -.003)), mash=.45, sdvig=KESH_DYM0 - 6 - int((T_TLEET + .1) * FPS + 1))
    if d1 is not None:
        s_ = d1.data.materials[0].node_tree.nodes['plotn'].inputs[1]
        for n in range(0, NF + 2): kl(s_, DYM_PLOTN[PLAN] * sm((tk(n) - T_TLEET) / .5) * (1 + .6 * sm((tk(n) - T_TLEET_MAX + .6) / .8)) * (1 - .95 * sm((tk(n) - T_TRAVA - .1) / 1.0)), n)
    plamya(P_t + Vector((.002, -.002, -.014)), T_TRAVA); iskorki(isk, P_t, T_TRAVA)
    fokus = lambda t: S.lerp(P_t, sm((t - T_UDARY[-1] - .1) / 1.0))
    kam = kamera_d(75, 4.0, dict(c=(S.x + .026, -.012, S.z - .024), d=.62, az=4, el=12), dict(c=(P_t.x - .008, -.016, P_t.z + .026), d=.5, az=9, el=14), fokus)
    return dict(kam=kam, tochki=lambda n: dict(udar=tuple(S), trut=tuple(P_t)), pered=lambda n: isk.obnovit(tk(n), vyderzhka=ISKRY_SLED),
                vremena=dict(udary=T_UDARY, tleet=T_TLEET, trava=T_TRAVA))

S_ = {'D1a': plan_D1a, 'D1b': plan_D1b, 'D2': plan_D2}[PLAN](); kam = S_['kam']

# --------- label points for the edit: screen fractions (x from the left, y from the top), t in seconds of the shot
def proj(v):
    c = world_to_camera_view(sc, kam, Vector(v)); return [round(c.x, 4), round(1 - c.y, 4), round(c.z, 3)]
if REZHIM in ('vse', 'metki'):
    M_ = dict(fps=FPS, dlit=DLIT, kadrov=NF, vremena=S_['vremena'], kadry=[])
    for n in range(1, NF + 1):
        sc.frame_set(n); d = {k: proj(v) for k, v in S_['tochki'](n).items()}; d['t'] = round(tk(n), 4); M_['kadry'].append(d)
    json.dump(M_, open(f'{ROOT}/metki-{PLAN}.json', 'w'))
    print('markers:', f'{ROOT}/metki-{PLAN}.json', M_['kadry'][0], M_['kadry'][-1])
    if REZHIM == 'metki': sys.exit(0)
out = f'{ROOT}/kadry/{PLAN}' + ('-proba' if PROBA else ''); os.makedirs(out, exist_ok=True)
for n in spisok_kadrov(REZHIM, NF):
    f = f'{out}/{n:04d}.png'
    if os.path.exists(f) and not PROBA: continue
    sc.frame_set(n); S_['pered'](n)
    sc.render.filepath = f; t = time.time(); bpy.ops.render.render(write_still=True); print(f'frame {n} {time.time() - t:.1f} s'); sys.stdout.flush()
