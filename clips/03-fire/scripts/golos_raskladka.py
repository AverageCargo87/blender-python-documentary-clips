# Clip 3 'Fire': narrator voice on the timeline. Group recordings golos/G*.wav are cut into sentences (at the silence between them)
# and placed at START (seconds from the clip start) -> golos-dorozhka.wav (48 kHz, mono), golos/start.json.
#   python golos_raskladka.py <root>
import sys, json, numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
ROOT = sys.argv[1]; SR = 48000; DLIT = 70.8
# when each phrase should start: under the picture and caption of its shot
START = dict(S1a=1.6, S1b=7.6, S2a=14.4, S2b=19.6, S3a=24.9, S3b=30.4, S4=34.3, S5=37.9, S6=41.1, S7=46.9, S8a=53.7, S8b=57.5, S9=61.0, S10=64.0)
ZAZOR = .35                                             # never closer than this to the previous phrase
F = json.load(open(f'{ROOT}/golos/frazy.json', encoding='utf-8'))
out = np.zeros(int(SR * DLIT), np.float32); plan = {}; konec = 0.0
for gid, g in F.items():
    sr, x = wavfile.read(f'{ROOT}/golos/{gid}.wav'); x = x.astype(np.float32) / 32768
    k = int(.01 * sr); env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, 'same'))
    fr = g['frazy']; rez = [0]
    for a, b in zip(fr[:-1], fr[1:]):                    # cut at the quietest point between sentences
        i0, i1 = int(max(0, a['e'] - .12) * sr), int(min(len(x) / sr, b['s'] + .12) * sr)
        rez.append(i0 + int(np.argmin(env[i0:i1])))
    rez.append(len(x))
    for f_, i0, i1 in zip(fr, rez[:-1], rez[1:]):
        y = x[i0:i1].copy()
        e = np.sqrt(np.convolve(y ** 2, np.ones(k) / k, 'same')); gr = max(e.max() * .03, 1e-4); akt = np.where(e > gr)[0]    # trim silence at the ends
        y = y[max(0, akt[0] - int(.03 * sr)):min(len(y), akt[-1] + int(.12 * sr))]
        n1, n2 = int(.012 * sr), int(.07 * sr); y[:n1] *= np.linspace(0, 1, n1); y[-n2:] *= np.linspace(1, 0, n2)
        y = resample_poly(y, SR, sr).astype(np.float32)
        t = max(START[f_['id']], konec + ZAZOR); i = int(t * SR); n = min(len(y), len(out) - i)
        out[i:i + n] += y[:n]; konec = t + len(y) / SR
        plan[f_['id']] = dict(start=round(t, 2), konec=round(konec, 2), dlit=round(len(y) / SR, 2), sdvinuto=round(t - START[f_['id']], 2), txt=f_['txt'])
        print(f"{f_['id']:4s} {t:6.2f} \u2013 {konec:6.2f}  ({len(y) / SR:.2f} s){'  SHIFTED by %.2f' % (t - START[f_['id']]) if t - START[f_['id']] > .01 else ''}  {f_['txt']}")
wavfile.write(f'{ROOT}/golos-dorozhka.wav', SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
json.dump(plan, open(f'{ROOT}/golos/start.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('peak', round(float(np.abs(out).max()), 3))
