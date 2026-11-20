# Clip 3 'Fire': sparks and embers as particles with glowing trails. Trajectories are precomputed (numpy),
# the mesh is rebuilt every frame: each spark is a thin three-sided 'arrow' from tail to head.
#   isk = Iskry('iskry'); isk.vsplesk(t0=1.0, mesto=(0,0,1), napr=(0,0,1), n=200, ...); isk.obnovit(t)   # t in seconds
import bpy, math
import numpy as np

def _ramp(a):
    """Spark colour by 'age' 0..1: white-yellow -> orange -> dark red. Returns (n,3) linear RGB."""
    a = np.clip(a, 0, 1)[:, None]
    c0, c1, c2, c3 = np.array([1.0, .86, .55]), np.array([1.0, .5, .12]), np.array([.85, .16, .02]), np.array([.25, .02, .0])
    return np.where(a < .25, c0 + (c1 - c0) * a / .25, np.where(a < .65, c1 + (c2 - c1) * (a - .25) / .4, c2 + (c3 - c2) * (a - .65) / .35))

class Iskry:
    DT = 1 / 240

    def __init__(self, imya='iskry', sila=40.0):
        self.me = bpy.data.meshes.new(imya); self.ob = bpy.data.objects.new(imya, self.me)
        bpy.context.scene.collection.objects.link(self.ob)
        m = bpy.data.materials.new(imya); m.use_nodes = True; N = m.node_tree.nodes; N.clear()
        out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); at = N.new('ShaderNodeAttribute'); at.attribute_name = 'cv'
        em.inputs['Strength'].default_value = sila
        m.node_tree.links.new(at.outputs['Color'], em.inputs['Color']); m.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
        self.me.materials.append(m); self.mat = m
        self.ob.visible_shadow = False
        self.P = []          # list of bursts: dict(t0, pos (n, steps, 3), zhizn (n,), r (n,), yark (n,), ostyv (n,))
        self.rng = np.random.default_rng(11)

    def _sim(self, p0, v0, zhizn, g, drag, pol, otskok, veter, turb, pod):
        n = len(p0); steps = int(math.ceil(zhizn.max() / self.DT)) + 2
        P = np.zeros((n, steps, 3), np.float32); p = p0.astype(np.float64).copy(); v = v0.astype(np.float64).copy()
        ph = self.rng.uniform(0, 6.28, (n, 3)); fr = self.rng.uniform(2.0, 6.0, (n, 3))
        for i in range(steps):
            P[:, i] = p; t = i * self.DT
            a = np.zeros_like(v); a[:, 2] = -g + pod
            if turb > 0: a += turb * np.sin(fr * t + ph)
            v += (a - drag * (v - veter)) * self.DT; p += v * self.DT
            if pol is not None:
                m = p[:, 2] < pol
                if m.any():
                    p[m, 2] = pol; v[m, 2] = -v[m, 2] * otskok; v[m, :2] *= .55
        return P

    def vsplesk(self, t0, mesto, napr=(0, 0, 1), n=100, skorost=(2., 6.), konus=.5, zhizn=(.25, .9), g=9.8, drag=1.2, pol=None,
                otskok=.3, r=.004, yark=1.0, razbros_mesta=.01, veter=(0, 0, 0), turb=0., pod=0., dlit=0., ostyv=1.5):
        """A burst of sparks. dlit > 0: sparks are born over this time, not all at once. pod: lift force (for embers above a fire)."""
        rng = self.rng
        d = np.array(napr, float); d /= np.linalg.norm(d) + 1e-9
        e1 = np.cross(d, [0, 0, 1.0]);
        if np.linalg.norm(e1) < 1e-3: e1 = np.array([1.0, 0, 0])
        e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
        th = np.abs(rng.normal(0, konus, n)); ph = rng.uniform(0, 2 * math.pi, n)
        dirs = (np.cos(th)[:, None] * d + np.sin(th)[:, None] * (np.cos(ph)[:, None] * e1 + np.sin(ph)[:, None] * e2))
        sp = rng.uniform(skorost[0], skorost[1], n) * rng.uniform(.6, 1.0, n)
        p0 = np.array(mesto, float)[None] + rng.normal(0, razbros_mesta, (n, 3))
        zh = rng.uniform(zhizn[0], zhizn[1], n)
        P = self._sim(p0, dirs * sp[:, None], zh, g, drag, pol, otskok, np.array(veter, float), turb, pod)
        self.P.append(dict(t0=t0 + (rng.uniform(0, dlit, n) if dlit > 0 else np.zeros(n)), pos=P, zhizn=zh,
                           r=r * rng.uniform(.6, 1.4, n), yark=yark * rng.uniform(.5, 1.3, n), ostyv=ostyv))

    def obnovit(self, t, vyderzhka=1 / 45, min_dl=2.2):
        """Rebuild the mesh for time t (s). vyderzhka: trail length in time, min_dl: minimum length in radii."""
        V, C = [], []
        for G in self.P:
            age = t - G['t0']; m = (age > 0) & (age < G['zhizn'])
            if not m.any(): continue
            idx = np.nonzero(m)[0]; a = age[idx]
            i1 = np.clip(a / self.DT, 0, G['pos'].shape[1] - 1.001); i0 = np.clip((a - vyderzhka) / self.DT, 0, G['pos'].shape[1] - 1.001)
            def pos(ii):
                k = ii.astype(int); f = (ii - k)[:, None]
                return G['pos'][idx, k] * (1 - f) + G['pos'][idx, k + 1] * f
            h, tl = pos(i1), pos(i0)
            r = G['r'][idx]
            d = h - tl; ln = np.linalg.norm(d, axis=1); kor = ln < r * min_dl
            d = np.where(kor[:, None], np.array([0, 0, 1.0])[None], d / (ln[:, None] + 1e-9)); ln = np.maximum(ln, r * min_dl)
            tl = h - d * ln[:, None]
            e1 = np.cross(d, np.array([.3, .5, .81])[None]); e1 /= np.linalg.norm(e1, axis=1)[:, None] + 1e-9; e2 = np.cross(d, e1)
            fa = a / G['zhizn'][idx]
            col = _ramp(fa ** .8) * (G['yark'][idx] * np.clip(1 - fa, 0, 1) ** G['ostyv'])[:, None]
            ring = [(math.cos(k * 2.0944), math.sin(k * 2.0944)) for k in range(3)]
            vv = np.zeros((len(idx), 7, 3), np.float32)
            for k, (c, s) in enumerate(ring):
                off = (e1 * c + e2 * s) * r[:, None]
                vv[:, k] = h + off; vv[:, 3 + k] = tl + off * .35
            vv[:, 6] = h + d * r[:, None] * 1.2
            V.append(vv.reshape(-1, 3)); C.append(np.repeat(col, 7, 0))
        me = self.me; me.clear_geometry()
        if not V: me.update(); return 0
        V = np.concatenate(V); C = np.concatenate(C); n = len(V) // 7
        # faces: 3 side quads (2 triangles each) + 3 nose triangles
        base = (np.arange(n) * 7)[:, None]
        tri = np.array([[0, 1, 4], [0, 4, 3], [1, 2, 5], [1, 5, 4], [2, 0, 3], [2, 3, 5], [0, 6, 1], [1, 6, 2], [2, 6, 0], [3, 4, 5]], np.int32)
        F = (base[:, :, None] + tri[None]).reshape(-1)
        me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
        nt = len(F) // 3
        me.loops.add(len(F)); me.loops.foreach_set('vertex_index', F)
        me.polygons.add(nt); me.polygons.foreach_set('loop_start', np.arange(0, len(F), 3, dtype=np.int32)); me.polygons.foreach_set('loop_total', np.full(nt, 3, np.int32))
        ca = me.color_attributes.new('cv', 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', np.concatenate([C, np.ones((len(C), 1))], 1).astype(np.float32).ravel())
        me.update()
        return n
