# Clip 3 'Fire', scene A: shared by the simulation (sim_derevo.py) and the scene (scena_a.py): ground, tree, strike point, timings.
import numpy as np
from priroda import Zemlya, derevo
FPS = 24
T_UDAR = 5.2                       # s from the scene start: the lightning strike
DL = {'A1': 7.6, 'A2': 7.0}        # shot durations
T0 = {'A1': 0.0, 'A2': 7.0}        # scene time at the start of each shot
T_VETKA = 12.6                     # s: a burning branch falls from the tree
NF_SIM = int((T0['A2'] + DL['A2'] - T_UDAR + .4) * FPS)     # simulation frames: from the strike to the end of the scene

def osnova():
    zem = Zemlya(razmer=700, n=350, ampl=2.2, seed=4, ploshchadka=(0, 0, 16))
    z0 = float(zem.z(0, 0))
    der = derevo(seed=3, osnova=(0, 0, z0 - .2), vys=9.2, stvol=3.7, m=1.45, r0=.42, plotn_listvy=.55)
    K = der['konchiki']
    verh = K[np.argmax(K[:, 2] - .12 * np.abs(K[:, 0] + 2.0) - .12 * np.abs(K[:, 1] + 1.0))]     # the treetop on the camera side: that is where the lightning strikes
    stvol = der['vetki'][0][0]; razvilka = stvol[-1]
    return zem, z0, der, np.array(verh), np.array(razvilka)

def goryashchie(der, verh, razvilka):
    """Which branches burn and with what delay (s after the strike): the split trunk at once, then along dry branches from the fork towards the strike point."""
    out = []
    os_ = verh - razvilka; os_[2] = 0; os_ /= np.linalg.norm(os_) + 1e-9
    for i, (pts, rad, ur) in enumerate(der['vetki']):
        c = pts.mean(0); d = c - razvilka
        if ur == 0: out.append((i, 0.0, 1.5)); continue
        if ur > 3: continue
        bok = float(d[:2].dot(os_[:2]))                 # how much the branch is on the 'struck' side of the crown
        if bok < -.8: continue
        dist = float(np.linalg.norm(c - verh))
        if dist > 6.5 and ur > 1: continue
        t_on = .25 + float(np.linalg.norm(d)) / 1.5
        out.append((i, t_on, 1.15 if ur <= 2 else .8))
    return out
