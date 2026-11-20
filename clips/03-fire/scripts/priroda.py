# Clip 3 'Fire': nature. The tree (umbrella acacia), grass in the wind, ground, lightning.
import bpy, math
import numpy as np
from obshchee import L, mat_prostoy

# --------- tree
def derevo(seed=3, osnova=(0, 0, 0), vys=6.4, stvol=2.7, imya='derevo', listya=True, plotn_listvy=1.0, m=1.0, r0=.26):
    """Umbrella acacia: leaning trunk, 4 main branches, flat crown. Returns dict(vetki=[(pts, rad, ur)], ob, list, konchiki)."""
    rng = np.random.default_rng(seed); V = []
    DL = [stvol, 3.4 * m, 2.5 * m, 1.6 * m, .95 * m]; DET = [1, 4, 3, 3, 3]; MAXU = 4
    def rost(p0, d, dl, r0, ur):
        n = max(5, int(dl / (.22 * m))); pts = [np.array(p0, float)]; d = np.array(d, float); d /= np.linalg.norm(d)
        for i in range(n):
            d = d + rng.normal(0, .10 if ur else .05, 3)
            if ur >= 1:
                d[2] = d[2] * (.90 if ur >= 2 else .95) + .015        # branches spread into an 'umbrella'
                if pts[-1][2] > osnova[2] + vys - .35 * m: d[2] = min(d[2], .02)
            d /= np.linalg.norm(d); pts.append(pts[-1] + d * dl / n)
        pts = np.array(pts); rad = r0 * (1 - .55 * np.linspace(0, 1, len(pts)) ** 1.2)
        V.append((pts, rad, ur))
        if ur < MAXU:
            k = DET[ur + 1] + (rng.integers(0, 2) if ur >= 1 else 0)
            for j in range(k):
                f = 1.0 if (ur == 0 or j == 0) else rng.uniform(.35, .95)
                i0 = min(len(pts) - 1, max(1, int(f * (len(pts) - 1))))
                base = pts[i0] - pts[i0 - 1]; base /= np.linalg.norm(base)
                if ur == 0:
                    az = j / k * 2 * math.pi + rng.uniform(-.35, .35); nak = math.radians(rng.uniform(42, 58))
                    nd = np.array([math.cos(az) * math.sin(nak), math.sin(az) * math.sin(nak), math.cos(nak)])
                else:
                    ax = rng.normal(0, 1, 3); ax -= ax.dot(base) * base; ax /= np.linalg.norm(ax)
                    ang = math.radians(rng.uniform(28, 55)); nd = base * math.cos(ang) + ax * math.sin(ang)
                    nd[2] = abs(nd[2]) * .5 + .08
                rost(pts[i0], nd, DL[ur + 1] * rng.uniform(.8, 1.15), rad[i0] * (.72 if ur == 0 else .62), ur + 1)
    nak0 = np.array([rng.uniform(-.12, .12), rng.uniform(-.12, .12), 1.0])
    rost(osnova, nak0, stvol, r0, 0)
    cu = bpy.data.curves.new(imya, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 3; cu.use_fill_caps = True
    for pts, rad, ur in V:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        sp.points.foreach_set('co', np.concatenate([pts, np.ones((len(pts), 1))], 1).ravel()); sp.points.foreach_set('radius', rad); sp.use_smooth = True
    ob = bpy.data.objects.new(imya, cu); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat_kory())
    konchiki = np.concatenate([p[len(p) // 3:] for p, r, u in V if u >= 3])
    out = dict(vetki=V, ob=ob, konchiki=konchiki, list=None)
    if listya:
        n_kl = int(len(konchiki) * 1.3 * plotn_listvy); ci = rng.integers(0, len(konchiki), n_kl)
        C = konchiki[ci] + rng.normal(0, 1, (n_kl, 3)) * np.array([.28, .28, .09]) * m
        NL = 70; n = n_kl * NL
        cen = np.repeat(C, NL, 0) + rng.normal(0, 1, (n, 3)) * np.array([.3, .3, .08]) * m
        a = rng.uniform(0, 2 * math.pi, n); nak = rng.normal(0, .45, n); dl = rng.uniform(.028, .05, n) * m ** .5; sh = dl * .45
        u = np.stack([np.cos(a) * np.cos(nak), np.sin(a) * np.cos(nak), np.sin(nak)], 1); w = np.stack([-np.sin(a), np.cos(a), rng.normal(0, .35, n)], 1)
        Vv = np.stack([cen - u * dl[:, None] - w * sh[:, None], cen + u * dl[:, None] - w * sh[:, None], cen + u * dl[:, None] + w * sh[:, None],
                       cen - u * dl[:, None] + w * sh[:, None]], 1).reshape(-1, 3).astype(np.float32)
        me = bpy.data.meshes.new(imya + '-list'); me.vertices.add(len(Vv)); me.vertices.foreach_set('co', Vv.ravel())
        me.loops.add(len(Vv)); me.loops.foreach_set('vertex_index', np.arange(len(Vv), dtype=np.int32))
        me.polygons.add(n); me.polygons.foreach_set('loop_start', np.arange(0, len(Vv), 4, dtype=np.int32)); me.polygons.foreach_set('loop_total', np.full(n, 4, np.int32))
        me.update(); lo = bpy.data.objects.new(imya + '-list', me); bpy.context.scene.collection.objects.link(lo)
        lo.data.materials.append(mat_listvy()); out['list'] = lo; out['list_centry'] = C
    return out

def mat_kory():
    m = bpy.data.materials.new('kora'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 9; ns.inputs['Detail'].default_value = 8
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, .12)
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (*L('#17110c'), 1); cr.color_ramp.elements[1].color = (*L('#4a3a2c'), 1)
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = .9; bm.inputs['Distance'].default_value = .03
    k = nt.links.new
    k(tc.outputs['Object'], mp.inputs['Vector']); k(mp.outputs[0], ns.inputs['Vector']); k(ns.outputs['Fac'], cr.inputs['Fac'])
    k(cr.outputs['Color'], b.inputs['Base Color']); k(ns.outputs['Fac'], bm.inputs['Height']); k(bm.outputs[0], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = .55                       # wet bark has a slight sheen
    return m

def mat_listvy():
    m = bpy.data.materials.new('listva'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*L('#2c3a18'), 1); b.inputs['Roughness'].default_value = .5
    try: b.inputs['Transmission Weight'].default_value = 0.0; b.inputs['Subsurface Weight'].default_value = 0.0
    except Exception: pass
    return m

# --------- grass
def trava(imya, centry, vys=(.45, .95), v_kochke=(18, 40), shir=.006, seed=5, r_kochki=.11, cvet=('#b9a36a', '#7a7040'), z_fn=None):
    """Grass tussocks: centry is (n,2) tussock positions. Each blade is a bent ribbon of 5 vertex rows.
    Attributes: k (0 at the root .. 1 at the tip) and faza, for the wind (see veter())."""
    rng = np.random.default_rng(seed); nk = len(centry)
    cnt = rng.integers(v_kochke[0], v_kochke[1] + 1, nk); n = int(cnt.sum())
    kc = np.repeat(np.asarray(centry, float), cnt, 0)
    root = kc + rng.normal(0, r_kochki, (n, 2))
    z0 = z_fn(root[:, 0], root[:, 1]) if z_fn is not None else np.zeros(n)
    h = rng.uniform(vys[0], vys[1], n) ** 1.0 * np.repeat(rng.uniform(.55, 1.2, nk), cnt)
    az = rng.uniform(0, 2 * math.pi, n); izg = rng.uniform(.1, .6, n) ** 1.3 * h           # tip deflection
    out_dir = root - kc; out_dir /= np.linalg.norm(out_dir, axis=1)[:, None] + 1e-6
    bend = .6 * out_dir + .4 * np.stack([np.cos(az), np.sin(az)], 1); bend /= np.linalg.norm(bend, axis=1)[:, None] + 1e-6
    side = np.stack([-bend[:, 1], bend[:, 0]], 1)
    R = 5; s = np.linspace(0, 1, R)
    P = np.zeros((n, R, 2, 3), np.float32); K = np.zeros((n, R, 2), np.float32)
    for i, si in enumerate(s):
        c2 = root + bend * (izg * si ** 2)[:, None]; zz = z0 + h * si * (1 - .12 * si)
        wd = shir * (1 - si) ** .7 * rng.uniform(.7, 1.3, n) + .0008
        for j, sg in enumerate((-1, 1)):
            P[:, i, j, :2] = c2 + side * (wd * sg)[:, None]; P[:, i, j, 2] = zz
        K[:, i, :] = si ** 1.6
    V = P.reshape(-1, 3)
    base = (np.arange(n) * R * 2)[:, None, None]
    q = np.array([[[2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2]] for i in range(R - 1)], np.int32).reshape(1, R - 1, 4)
    F = (base + q).reshape(-1)
    me = bpy.data.meshes.new(imya); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    nf = len(F) // 4; me.loops.add(len(F)); me.loops.foreach_set('vertex_index', F)
    me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, len(F), 4, dtype=np.int32)); me.polygons.foreach_set('loop_total', np.full(nf, 4, np.int32))
    me.polygons.foreach_set('use_smooth', np.ones(nf, bool))
    a = me.attributes.new('k', 'FLOAT', 'POINT'); a.data.foreach_set('value', K.ravel())
    fz = me.attributes.new('ton', 'FLOAT', 'POINT'); fz.data.foreach_set('value', np.repeat(rng.uniform(0, 1, n), R * 2).astype(np.float32))
    me.update(); ob = bpy.data.objects.new(imya, me); bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'ton'; ak = nt.nodes.new('ShaderNodeAttribute'); ak.attribute_name = 'k'
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*L(cvet[0]), 1); mx.inputs['B'].default_value = (*L(cvet[1]), 1)
    mk = nt.nodes.new('ShaderNodeMix'); mk.data_type = 'RGBA'; mk.inputs['A'].default_value = (*[c * .35 for c in L(cvet[1])], 1)   # darker at the root
    nt.links.new(at.outputs['Fac'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], mk.inputs['B']); nt.links.new(ak.outputs['Fac'], mk.inputs['Factor'])
    nt.links.new(mk.outputs['Result'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .45
    try: b.inputs['Subsurface Weight'].default_value = 0.0
    except Exception: pass
    me.materials.append(m)
    return ob

def veter(ob, sila=.12, poryv=(1.0, .25, 0), masshtab=.35, skorost=1.1, imya='veter'):
    """Geometry nodes: blade tips sway with a noise that travels over time (wind waves)."""
    ng = bpy.data.node_groups.new(imya, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; k = ng.links.new
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput'); sp = N.new('GeometryNodeSetPosition')
    at = N.new('GeometryNodeInputNamedAttribute'); at.data_type = 'FLOAT'; at.inputs['Name'].default_value = 'k'
    pos = N.new('GeometryNodeInputPosition'); tm = N.new('GeometryNodeInputSceneTime')
    ns = N.new('ShaderNodeTexNoise'); ns.noise_dimensions = '4D'; ns.inputs['Scale'].default_value = masshtab; ns.inputs['Detail'].default_value = 2
    mw = N.new('ShaderNodeMath'); mw.operation = 'MULTIPLY'; mw.inputs[1].default_value = skorost
    sub = N.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (.5, .5, .5)
    # gust: a common lean along the wind, strength from a second noise (large waves)
    ns2 = N.new('ShaderNodeTexNoise'); ns2.noise_dimensions = '4D'; ns2.inputs['Scale'].default_value = masshtab * .22; ns2.inputs['Detail'].default_value = 1
    mw2 = N.new('ShaderNodeMath'); mw2.operation = 'MULTIPLY'; mw2.inputs[1].default_value = skorost * .6
    sc2 = N.new('ShaderNodeVectorMath'); sc2.operation = 'SCALE'; sc2.inputs[0].default_value = poryv
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'
    mk = N.new('ShaderNodeMath'); mk.operation = 'MULTIPLY'; mk.inputs[1].default_value = sila; mk.name = 'sila'
    k(tm.outputs['Seconds'], mw.inputs[0]); k(pos.outputs[0], ns.inputs['Vector']); k(mw.outputs[0], ns.inputs['W'])
    k(ns.outputs['Color'], sub.inputs[0])
    k(tm.outputs['Seconds'], mw2.inputs[0]); k(pos.outputs[0], ns2.inputs['Vector']); k(mw2.outputs[0], ns2.inputs['W'])
    k(ns2.outputs['Fac'], sc2.inputs['Scale']); k(sub.outputs[0], add.inputs[0]); k(sc2.outputs[0], add.inputs[1])
    k(at.outputs['Attribute'], mk.inputs[0]); k(add.outputs[0], sc.inputs[0]); k(mk.outputs[0], sc.inputs['Scale'])
    k(gi.outputs[0], sp.inputs['Geometry']); k(sc.outputs[0], sp.inputs['Offset']); k(sp.outputs[0], go.inputs[0])
    md = ob.modifiers.new(imya, 'NODES'); md.node_group = ng
    return md

# --------- ground
def shum2(ny, nx, sig, seed):
    r = np.random.default_rng(seed).standard_normal((ny + 6 * int(sig) + 2, nx + 6 * int(sig) + 2)).astype(np.float32)
    kk = np.exp(-np.arange(-int(3 * sig), int(3 * sig) + 1) ** 2 / (2 * sig * sig)); kk /= kk.sum()
    r = np.apply_along_axis(lambda v: np.convolve(v, kk, 'valid'), 0, r); r = np.apply_along_axis(lambda v: np.convolve(v, kk, 'valid'), 1, r)
    r = r[:ny, :nx]; return r / (r.std() + 1e-6)

class Zemlya:
    """A square of ground with gentle relief; z(x, y): height (bilinear), ob: the mesh."""
    def __init__(self, razmer=300., n=300, ampl=1.2, seed=4, imya='zemlya', mat=None, ploshchadka=None):
        self.razmer, self.n = razmer, n
        hh = ampl * (.75 * shum2(n, n, n / 14, seed) + .25 * shum2(n, n, n / 50, seed + 1)) + .04 * shum2(n, n, 1.2, seed + 2)
        xs = np.linspace(-razmer / 2, razmer / 2, n); X, Y = np.meshgrid(xs, xs)
        if ploshchadka is not None:                                   # flatten a pad around a point (x, y, radius)
            px, py, pr = ploshchadka; w = np.exp(-((X - px) ** 2 + (Y - py) ** 2) / (2 * pr * pr))
            hc = hh[int((py / razmer + .5) * (n - 1)), int((px / razmer + .5) * (n - 1))]; hh = hh * (1 - w) + hc * w
        self.h, self.xs = hh, xs
        P = np.stack([X, Y, hh], -1).reshape(-1, 3).astype(np.float32)
        i = np.arange(n - 1); I, J = np.meshgrid(i, i); a = (J * n + I).ravel()
        F = np.stack([a, a + 1, a + n + 1, a + n], 1).astype(np.int32).ravel()
        me = bpy.data.meshes.new(imya); me.vertices.add(len(P)); me.vertices.foreach_set('co', P.ravel())
        nf = len(F) // 4; me.loops.add(len(F)); me.loops.foreach_set('vertex_index', F)
        me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, len(F), 4, dtype=np.int32)); me.polygons.foreach_set('loop_total', np.full(nf, 4, np.int32))
        me.polygons.foreach_set('use_smooth', np.ones(nf, bool)); me.update()
        self.ob = bpy.data.objects.new(imya, me); bpy.context.scene.collection.objects.link(self.ob)
        self.ob.data.materials.append(mat or mat_zemli())
    def z(self, x, y):
        n, R = self.n, self.razmer
        fx = np.clip((np.asarray(x, float) / R + .5) * (n - 1), 0, n - 1.001); fy = np.clip((np.asarray(y, float) / R + .5) * (n - 1), 0, n - 1.001)
        ix, iy = fx.astype(int), fy.astype(int); tx, ty = fx - ix, fy - iy; h = self.h
        return (h[iy, ix] * (1 - tx) + h[iy, ix + 1] * tx) * (1 - ty) + (h[iy + 1, ix] * (1 - tx) + h[iy + 1, ix + 1] * tx) * ty

def mat_zemli(mokro=.5, cvet=('#2b2218', '#4a3b2a')):
    """Dark wet ground: noise colour, small bumps, puddles shine (patches of low roughness)."""
    m = bpy.data.materials.new('zemlya'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; k = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 1.3; n1.inputs['Detail'].default_value = 9
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 22; n2.inputs['Detail'].default_value = 6
    n3 = nt.nodes.new('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = .35; n3.inputs['Detail'].default_value = 3
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (*L(cvet[0]), 1); cr.color_ramp.elements[1].color = (*L(cvet[1]), 1)
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = .45; rr.inputs['From Max'].default_value = .62
    rr.inputs['To Min'].default_value = .75 - .3 * mokro; rr.inputs['To Max'].default_value = .75 - .62 * mokro
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = .5; bm.inputs['Distance'].default_value = .05
    for n_ in (n1, n2, n3): k(tc.outputs['Object'], n_.inputs['Vector'])
    k(n1.outputs['Fac'], cr.inputs['Fac']); k(cr.outputs['Color'], b.inputs['Base Color'])
    k(n3.outputs['Fac'], rr.inputs['Value']); k(rr.outputs['Result'], b.inputs['Roughness'])
    k(n2.outputs['Fac'], bm.inputs['Height']); k(bm.outputs[0], b.inputs['Normal'])
    return m

# --------- lightning
def molniya(p0, p1, seed=1, r=.05, vetvey=7, imya='molniya', sila=400., vidno=70.):
    """Lightning channel from p0 (cloud) to p1 (target): large zigzags along the whole length and fine ones near the ground; branches grow from the lowest `vidno` metres
    (what is in frame) sideways and down. Returns (main channel, branches, channel points)."""
    rng = np.random.default_rng(seed)
    def lom(a, b, razmah, itr=7, k=1.85):
        pts = [np.array(a, float), np.array(b, float)]
        for it in range(itr):
            new = []
            for i in range(len(pts) - 1):
                m = (pts[i] + pts[i + 1]) / 2 + rng.normal(0, razmah / k ** it, 3) * np.array([1, 1, .3]); new += [pts[i], m]
            new.append(pts[-1]); pts = new
        return np.array(pts)
    p0, p1 = np.array(p0, float), np.array(p1, float); dist = np.linalg.norm(p1 - p0)
    verh = p1 + (p0 - p1) * (vidno / dist)                       # boundary of the 'visible' part
    gl = np.concatenate([lom(p0, verh, dist * .05, itr=6)[:-1], lom(verh, p1, vidno * .085, itr=8, k=1.7)])
    V = []
    niz = gl[np.linalg.norm(gl - p1, axis=1) < vidno * .95]
    def vetv(src, ur, r_, dl):
        i0 = rng.integers(2, max(3, int(len(src) * (.8 if ur == 0 else .6)))); t = src[min(len(src) - 1, i0 + 8)] - src[i0]; t /= np.linalg.norm(t) + 1e-9
        ax = rng.normal(0, 1, 3); ax -= ax.dot(t) * t; ax /= np.linalg.norm(ax); ang = math.radians(rng.uniform(22, 55))
        d = t * math.cos(ang) + ax * math.sin(ang); d[2] = min(d[2], -.12); d /= np.linalg.norm(d)
        b = lom(src[i0], src[i0] + d * dl, dl * .1, itr=6, k=1.7); V.append((b, r_))
        if ur < 2 and rng.uniform() < .7: vetv(b, ur + 1, r_ * .6, dl * rng.uniform(.3, .55))
    for _ in range(vetvey): vetv(niz, 0, r * .5, rng.uniform(.25, .6) * vidno)
    def krivaya(nm, spiski, s):
        cu = bpy.data.curves.new(nm, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 1
        for pts, rr in spiski:
            sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
            sp.points.foreach_set('co', np.concatenate([pts, np.ones((len(pts), 1))], 1).ravel())
            sp.points.foreach_set('radius', rr * (1 - .6 * np.linspace(0, 1, len(pts))) if nm.endswith('vetvi') else np.full(len(pts), rr))
        ob = bpy.data.objects.new(nm, cu); bpy.context.scene.collection.objects.link(ob)
        m = bpy.data.materials.new(nm); m.use_nodes = True; N = m.node_tree.nodes; N.clear()
        out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.72, .8, 1.0, 1)
        em.inputs['Strength'].default_value = s; m.node_tree.links.new(em.outputs[0], out.inputs['Surface']); cu.materials.append(m)
        ob.visible_shadow = False
        return ob
    return krivaya(imya, [(gl, r)], sila), krivaya(imya + '-vetvi', V, sila * .45), gl
