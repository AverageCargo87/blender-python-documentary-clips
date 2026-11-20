# List every caption of the clip (from montazh2.py) with its on-screen time + scene snapshots for review.
#   python podpisi_spisok.py <root>  -> _proverka/podpisi.md, _proverka/scena-*.jpg
import sys, os, json, math
R = sys.argv[1]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'montazh2.py'), encoding='utf-8').read().split("if ARG == 'vse':")[0]
sys.argv = ['montazh2.py', R, '1']
g = {'__name__': 'm2'}; exec(compile(src, 'montazh2', 'exec'), g)
EL, NAK, SCENY = g['EL'], g['NAKLEYKI'], g['SCENY']
os.makedirs(f'{R}/_proverka', exist_ok=True)
CPS = 9.0       # characters per second, comfortable for 10-11 year olds reading from the screen (with margin)
rows = []
def tekst(e):
    if e['tip'] == 'karta': return (e['tit'] + (' / ' + e['sub'] if e['sub'] else '')).replace('\n', ' ')
    return e['txt'].replace('\n', ' / ')
rows.append(('A', 'title', 'ДРЕВНЕЙШИЕ ЛЮДИ / Костёнки: охотники на мамонтов', .7, 5.8))
for s_, txt, a, b in NAK: rows.append((s_, 'sticker', txt, a, b))
for e in EL:
    if e['a'] > 900: continue
    rows.append((e['sc'], {'karta': 'card', 'metka': 'marker', 'strelka': 'arrow'}[e['tip']], tekst(e), e['a'], e['b']))
rows.sort(key=lambda r: r[3])
with open(f'{R}/_proverka/podpisi.md', 'w', encoding='utf-8') as fo:
    fo.write('| # | scene | kind | text | from | to | visible, s (no fades) | needed to read, s |\n|---|---|---|---|---|---|---|---|\n')
    for i, (s_, vid, txt, a, b) in enumerate(rows, 1):
        vid_s = max(0, b - a - 1.0); nuzhno = len(txt) / CPS + .8
        fo.write(f'| {i} | {s_} | {vid} | {txt} | {a:.1f} | {b:.1f} | {vid_s:.1f} | {nuzhno:.1f}{" ⚠" if vid_s < nuzhno else ""} |\n')
print('captions', len(rows))
# snapshots: 4 moments per scene, when the most captions are visible
from PIL import Image
for s_, t0, d in SCENY:
    els = [r for r in rows if r[0] == s_]
    cand = [t0 + d * k / 40 for k in range(2, 39)]
    def vidno(t): return sum(1 for r in els if r[3] + .6 < t < r[4] - .6)
    best = sorted(cand, key=lambda t: -vidno(t))
    pick = []
    for t in best:
        if all(abs(t - p) > d / 6 for p in pick): pick.append(t)
        if len(pick) == 4: break
    pick.sort()
    sh = Image.new('RGB', (1920, 1080))
    for i, t in enumerate(pick):
        n = 1 + int(round(t * 30))
        sh.paste(Image.open(f'{R}/post/{n:04d}.jpg').resize((960, 540)), ((i % 2) * 960, (i // 2) * 540))
    sh.save(f'{R}/_proverka/scena-{s_}.jpg', quality=88)
print('ok')
