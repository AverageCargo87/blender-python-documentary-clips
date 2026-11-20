# Slow down part of a scene without re-rendering: in-between frames are synthesised from motion (ffmpeg minterpolate);
# label points (metki-<scene>.json) are stretched the same way.  python zamedlit.py <root> <scene> <from_frame> <to_frame> <factor>
# Originals are kept: kadry/<scene>_ish, metki-<scene>_ish.json (a rerun starts from them, not from the stretched result).
import sys, os, json, shutil, subprocess, glob
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from lib.captions import retime_map      # the frame-time mapping, unit-tested in tests/test_captions.py
R, SC, A, B, K = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
ish, cel = f'{R}/kadry/{SC}_ish', f'{R}/kadry/{SC}'
if not os.path.exists(ish): shutil.move(cel, ish)
mi = f'{R}/metki-{SC}_ish.json'
if not os.path.exists(mi): shutil.copy(f'{R}/metki-{SC}.json', mi)
N0 = len(glob.glob(f'{ish}/*.png'))
shutil.rmtree(cel, ignore_errors=True); os.makedirs(cel)
tmp = f'{R}/kadry/_zam_{SC}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
nseg = B - A + 1; nout = int(round(nseg * K))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-start_number', str(A), '-i', f'{ish}/%04d.png', '-frames:v', str(nseg) if False else str(nout),
                '-vf', f'select=between(n\\,0\\,{nseg - 1}),minterpolate=fps={30 * K:.4f}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',
                '-start_number', '1', f'{tmp}/%04d.png'], check=True)
seg = sorted(glob.glob(f'{tmp}/*.png'))
while len(seg) < nout: shutil.copy(seg[-1], f'{tmp}/{len(seg) + 1:04d}.png'); seg = sorted(glob.glob(f'{tmp}/*.png'))
seg = seg[:nout]
n = 0
for f in range(1, A): n += 1; shutil.copy(f'{ish}/{f:04d}.png', f'{cel}/{n:04d}.png')
for p in seg: n += 1; shutil.copy(p, f'{cel}/{n:04d}.png')
for f in range(B + 1, N0 + 1): n += 1; shutil.copy(f'{ish}/{f:04d}.png', f'{cel}/{n:04d}.png')
shutil.rmtree(tmp)
# label points: the same time mapping
j = json.load(open(mi)); kad = j['kadry']
def tochka(t_ish):            # t_ish is a fractional source frame number
    i0 = int(np.floor(t_ish)); i1 = min(N0, i0 + 1); u = t_ish - i0; i0 = max(1, min(N0, i0))
    r0, r1 = kad[str(i0)], kad[str(i1)]
    if isinstance(r0, dict): return {k: [round(r0[k][c] * (1 - u) + r1[k][c] * u, 1) for c in range(len(r0[k]))] for k in r0}
    return [round(r0[c] * (1 - u) + r1[c] * u, 3) for c in range(len(r0))]
out = {}; m = 0
for f in range(1, A): m += 1; out[m] = kad[str(f)]
for s_ in retime_map(N0, A, B, K)[A - 1:A - 1 + nout]: m += 1; out[m] = tochka(s_)
for f in range(B + 1, N0 + 1): m += 1; out[m] = kad[str(f)]
j['kadry'] = out
json.dump(j, open(f'{R}/metki-{SC}.json', 'w'))
print(SC, N0, '->', n, 'frames; points', len(out))
