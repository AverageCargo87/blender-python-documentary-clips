# Clip 1 pre-delivery check: on-screen speed of every labelled marker and path head, globe disc radius and its rate of change,
# read from metki.json written by scena.py. Used to keep labelled markers below ~40-60 px/s.
#   python analiz.py <root>
import json, math, sys, os
M = json.load(open(os.path.join(sys.argv[1] if len(sys.argv) > 1 else '.', 'metki.json')))['kadry']; NF = len(M)
fr = lambda t: str(min(NF, 1 + round(t * 30)))
def sp(key, t):
    a = M[fr(t)][key]; b = M[fr(t + 1/30)][key]; return math.hypot(b[0] - a[0], b[1] - a[1]) * 30
OK = {'avstralopitek': (12.2, 16.0), 'olduvay': (19.2, 24.8), 'yava': (32.4, 35.6), 'kitay': (35.0, 38.2), 'neandertal': (43.6, 46.2), 'kromanon': (53.7, 56.3)}
for n, (a, b) in OK.items():
    v = [sp(n, a + .3 + i / 30) for i in range(int((b - a - .6) * 30))]
    print(f'{n:14s} while captioned (edges excluded) max {max(v):4.0f} px/s')
print('--- per second: max speed of visible markers/path heads, disc radius and its speed, disc bottom')
keys = list(OK) + ['g:er-yava', 'g:er-kitay', 'g:sap-evropa', 'g:sap-aziya', 'g:sap-amerika']
for t10 in range(0, int((NF / 30 - .1) * 2)):
    t = t10 / 2
    best = 0
    for k in keys:
        x, y, vid, *_ = M[fr(t)][k]
        if vid > .3 and 0 < x < 1920 and 0 < y < 1080: best = max(best, sp(k, t))
    r0 = M[fr(t)]['disk'][2]; r1 = M[fr(t + 1/30)]['disk'][2]
    print(f'{t:5.1f}  points {best:4.0f}  R {r0:5.0f}  dR {abs(r1 - r0) * 30:4.0f}  bottom {M[fr(t)]["niz"]:5.0f}')
