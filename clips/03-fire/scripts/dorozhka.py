# Clip 3 'Fire': sound track. Quiet effects (storm, fire, friction, stone strike, animal) placed on the timeline + light piano.
# The narrator voice (golos/S*.wav), if present, goes on top: voice at -16 LUFS, everything else quieter.
#   python dorozhka.py <root>      -> zvuk-itog.wav (48 kHz stereo)
import sys, os, json, subprocess, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly
ROOT = sys.argv[1]; SR = 48000
PLANY = [('A1', 7.6), ('A2', 7.0), ('B1', 5.2), ('B2', 6.4), ('C', 14.0), ('D1a', 6.4), ('D1b', 3.4), ('D2', 7.6), ('E', 18.0)]
T0 = {}; _t = 0.0
for _s, _d in PLANY: T0[_s] = _t; _t += _d - .6
DLIT = T0['E'] + 18.0; N = int(SR * DLIT)
def zagr(imya):
    w = f'{ROOT}/zvuk/{imya}.wav'
    if not os.path.exists(w): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{ROOT}/zvuk/{imya}.mp3', '-ar', str(SR), '-ac', '2', w], check=True)
    sr, x = wavfile.read(w); x = x.astype(np.float32) / (32768 if x.dtype == np.int16 else 1)
    return x if x.ndim == 2 else np.stack([x, x], 1)
def rms_db(x):
    e = np.sqrt((x ** 2).mean(1)); akt = e[e > e.max() * .05]
    return 20 * np.log10(np.sqrt((akt ** 2).mean()) + 1e-9)
def k_urovnyu(x, db): return x * 10 ** ((db - rms_db(x)) / 20)
def petlya(x, dlit, xf=.6):
    """Seamlessly loop a clip to dlit seconds: the end crossfades into the start."""
    n = int(dlit * SR); k = int(xf * SR); L = len(x) - k; out = np.zeros((n + len(x), 2), np.float32); i = 0
    w = np.linspace(0, 1, k, dtype=np.float32)[:, None]
    y = x.copy(); y[:k] *= w; y[-k:] *= 1 - w
    while i < n: out[i:i + len(y)] += y; i += L
    return out[:n]
def plavno(x, vh=.3, vyh=.5):
    n = len(x); a = np.ones(n, np.float32); k1, k2 = min(n, int(vh * SR)), min(n, int(vyh * SR))
    if k1: a[:k1] *= np.linspace(0, 1, k1) ** 2
    if k2: a[-k2:] *= np.linspace(1, 0, k2) ** 2
    return x * a[:, None]
def filtr(x, f, tip='low'):
    sos = butter(2, f / (SR / 2), tip, output='sos'); return np.stack([sosfilt(sos, x[:, 0]), sosfilt(sos, x[:, 1])], 1).astype(np.float32)
def vysota(x, k):                      # change pitch and length (k > 1: higher and shorter)
    return np.stack([resample_poly(x[:, c], 1000, int(1000 * k)) for c in (0, 1)], 1).astype(np.float32)
S = np.zeros((N + SR * 12, 2), np.float32)
def polozhit(x, t, pan=0.0):
    i = int(t * SR); x = x.copy(); x[:, 0] *= np.sqrt(1 - max(0, pan)); x[:, 1] *= np.sqrt(1 + min(0, pan)); S[i:i + len(x)] += x[:max(0, len(S) - i)]

Z = {k: zagr(k) for k in ('grom', 'veter', 'koster', 'trenie', 'udar', 'giena', 'vspyshka', 'derevo', 'golovnya', 'razgoranie')}
# -- storm and savanna (A1, A2, B1)
polozhit(plavno(k_urovnyu(petlya(Z['veter'], 19.5), -33), 1.5, 2.5), 0.0)
gr = Z['grom']
for tz, db in ((1.5, -40), (3.45, -37), (9.5, -42)):                                   # distant rumbles: muffled and quiet
    polozhit(plavno(k_urovnyu(filtr(vysota(gr, .8), 260), db), .4, 2.0), tz, pan=-.3 if tz < 2 else .3)
g = k_urovnyu(gr, -21); pk = np.abs(g).max()
if pk > 10 ** (-7 / 20): g *= 10 ** (-7 / 20) / pk                                    # the strike without a 'boom': peak no higher than -7 dB
polozhit(plavno(g, .0, 1.5), 5.2 - .02)
polozhit(plavno(k_urovnyu(petlya(Z['derevo'], 9.0), -27), 1.6, 1.4), 5.5)            # the tree catches and burns
polozhit(plavno(k_urovnyu(Z['golovnya'], -29), .5, .9), T0['B1'] - .1)                 # the firebrand being carried
# -- campfire: in the cave (B2), far away in the hall (C), by the tinder nest (D), the main one (E)
ko = Z['koster']
polozhit(plavno(k_urovnyu(petlya(ko, 4.2), -35), 1.2, .8), T0['B2'] + 2.5)
polozhit(plavno(k_urovnyu(filtr(petlya(ko, 14.2), 2500), -37), 1.0, 1.0), T0['C'] - .2)
polozhit(plavno(k_urovnyu(petlya(ko, 19.0), -29), 1.2, 2.2), T0['E'] - .4)
# -- friction, ember, flame (D1a, D1b)
polozhit(plavno(k_urovnyu(Z['trenie'][:int(4.7 * SR)], -28), .25, .3), T0['D1a'] + .3)
polozhit(plavno(k_urovnyu(Z['razgoranie'], -27), .05, .8), T0['D1b'] + 1.2)
polozhit(plavno(k_urovnyu(petlya(ko, 2.6), -34), .6, .6), T0['D1b'] + 1.4)
# -- stone strikes, smouldering, flame (D2)
for i, tu in enumerate((.9, 1.9, 2.8, 3.7)):
    u = k_urovnyu(vysota(Z['udar'], (1.0, 1.06, .96, 1.03)[i]), -24); pk = np.abs(u).max()
    if pk > 10 ** (-9 / 20): u *= 10 ** (-9 / 20) / pk
    polozhit(plavno(u, 0, .2), T0['D2'] + tu - .03, pan=(-.1, .1, -.05, .05)[i])
polozhit(plavno(k_urovnyu(Z['razgoranie'], -27), .05, .8), T0['D2'] + 5.3)
polozhit(plavno(k_urovnyu(petlya(ko, 2.6), -33), .6, .9), T0['D2'] + 5.5)
# -- finale: the animal and the campfire flare
polozhit(plavno(k_urovnyu(Z['giena'], -27), .2, .8), T0['E'] + 10.5, pan=.25)
polozhit(plavno(k_urovnyu(Z['vspyshka'], -23), .0, .9), T0['E'] + 12.15)
S = S[:N]
kon = np.ones(N, np.float32); kon[-int(1.6 * SR):] = np.linspace(1, 0, int(1.6 * SR)) ** 1.5; S *= kon[:, None]
wavfile.write(f'{ROOT}/zvuk-shumy.wav', SR, np.clip(S, -1, 1))
# -- music: dramatic piano (D minor, no lows) for the full length; review note: 'more dramatic and not as loud'
muz = f'{ROOT}/muz-drama.wav'
if not os.path.exists(muz):
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'muzyka_drama.py'), muz, f'{DLIT:.1f}'], check=True)
def lufs(put):
    r_ = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', put, '-filter_complex', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True)
    return float([l for l in r_.stderr.splitlines() if l.strip().startswith('I:')][-1].split()[1])
gol = f'{ROOT}/golos-dorozhka.wav'; est_golos = os.path.exists(gol)
M_TSEL, M_PRISED = (-34.0, 4.0) if est_golos else (-31.0, 0.0)          # music loudness (LUFS) and how much it ducks under the voice (dB)
sr_m, mz = wavfile.read(muz); mz = mz.astype(np.float32)
if mz.ndim == 1: mz = np.stack([mz, mz], 1)
mz = np.concatenate([mz, np.zeros((max(0, N - len(mz)), 2), np.float32)])[:N]
mz *= 10 ** ((M_TSEL - lufs(muz)) / 20)
if est_golos and M_PRISED:
    sr_g, g = wavfile.read(gol); g = g.astype(np.float32) / (32768 if g.dtype == np.int16 else 1)
    if g.ndim == 2: g = g.mean(1)
    if sr_g != SR: g = resample_poly(g, SR, sr_g)
    g = np.concatenate([g, np.zeros(max(0, N - len(g)), np.float32)])[:N]
    h = SR // 100; e = np.sqrt((g[:len(g) // h * h].reshape(-1, h) ** 2).mean(1))       # voice envelope, 100 points per second
    akt = np.clip((e - .004) / .02, 0, 1); sgl = np.zeros_like(akt); v = 0.0
    for i, a in enumerate(akt):                                                        # ducks fast, recovers slowly
        v += (a - v) * (.12 if a > v else .025); sgl[i] = v
    k = np.interp(np.arange(N) / h, np.arange(len(sgl)), sgl)
    mz *= (10 ** (-M_PRISED * k / 20)).astype(np.float32)[:, None]
wavfile.write(f'{ROOT}/muz-gotov.wav', SR, np.clip(mz, -1, 1))
f_ = ['-i', f'{ROOT}/zvuk-shumy.wav', '-i', f'{ROOT}/muz-gotov.wav'] + (['-i', gol] if est_golos else [])
if est_golos:
    fc = ('[0]volume=-3dB[s];[2]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,pan=stereo|c0=c0|c1=c0[v];'
          '[s][1][v]amix=inputs=3:normalize=0:duration=first,volume=-3dB[a]')
else:
    fc = '[0][1]amix=inputs=2:normalize=0:duration=first,volume=3dB[a]'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *f_, '-filter_complex', fc, '-map', '[a]', '-ar', '48000', f'{ROOT}/zvuk-itog.wav'], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f'{ROOT}/zvuk-itog.wav', '-filter_complex', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
print([l.strip() for l in r.stderr.splitlines() if 'I:' in l or 'Peak:' in l or 'LRA:' in l][-3:])
print('length', DLIT, 'voice' if est_golos else 'no voice')
