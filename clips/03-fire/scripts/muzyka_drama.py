# Clip 3 'Fire': more dramatic music (review note: 'a bit more dramatic and not as loud').
# Piano in D minor following the scenes: a quiet pulse before the storm -> a chord hit on the lightning -> motion (fire is carried) ->
# mystery (the section near Beijing) -> a building ostinato (making fire) -> warmth (campfire) -> unease (the animal) -> D major at the end.
# The 'no drone' rule holds: nothing below ~150 Hz (high-pass), no sustained synth pads.
#   python muzyka_drama.py <out.wav> [duration=70.8]
import sys, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
OUT = sys.argv[1]; D = float(sys.argv[2]) if len(sys.argv) > 2 else 70.8
SR = 48000; N = int(SR * (D + 1)); rng = np.random.default_rng(7)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def nota(t0, m, v, ring=None, pan=None):
    """A piano note: two slightly detuned 'strings', partials with two-stage decay; louder is brighter."""
    i0 = int(t0 * SR)
    if i0 >= N or v <= 0: return
    f = hz(m); ring = ring or 4.0 * (262 / f) ** .5
    n = min(int((ring * 1.6 + .3) * SR), N - i0); t = np.arange(n) / SR; x = np.zeros(n)
    for k in range(1, 9):
        fk = k * f * np.sqrt(1 + .0003 * k * k)
        if fk > 7000: break
        a = v ** (.18 * (k - 1)) / k ** 1.25
        env = .55 * np.exp(-t / (.35 / k ** .5)) + .45 * np.exp(-t / (ring / k ** .6))
        ph = rng.uniform(0, 6.28)
        x += a * env * .5 * (np.sin(2 * np.pi * fk * t) + np.sin(2 * np.pi * fk * 1.0007 * t + ph))
    x *= np.clip(t / .004, 0, 1) * v
    if pan is None: pan = float(np.clip((m - 66) / 22, -.5, .5))
    L[i0:i0 + n] += (x * np.sqrt((1 - pan) / 2)).astype(np.float32); R[i0:i0 + n] += (x * np.sqrt((1 + pan) / 2)).astype(np.float32)

def akk(t0, ms, v, arp=.035, ring=None):
    for j, m in enumerate(sorted(ms)): nota(t0 + j * arp, m, v * (1 if j == 0 else .85), ring)

# chord voicing: bass (no lower than F3, 175 Hz) and four notes for the arpeggio
BAS = dict(Dm=62, Bb=58, F=53, C=60, Gm=55, A=57, D=62)
ARP = dict(Dm=[62, 65, 69, 74], Bb=[62, 65, 70, 74], F=[60, 65, 69, 72], C=[60, 64, 67, 72], Gm=[62, 67, 70, 74], A=[61, 64, 69, 73], D=[62, 66, 69, 74])
UZOR = [0, 1, 2, 3, 2, 1, 2, 1]

def perebor(t0, t1, ch, step, v0, v1, uzor=UZOR):
    t, i = t0, 0
    while t < t1 - 1e-6:
        u = (t - t0) / max(1e-6, t1 - t0); v = v0 + (v1 - v0) * u
        nota(t, ARP[ch][uzor[i % len(uzor)]], v * (1 if i % 4 == 0 else .8), ring=1.8)
        t += step; i += 1

def melodiya(t0, noty, okt=.4):
    for dt, m, v in noty:
        nota(t0 + dt, m, v, ring=3.2)
        if okt: nota(t0 + dt + .01, m + 12, v * okt, ring=2.4)

# -- 0.8-5.2: the storm gathers, a quiet pulse and two notes on top
for i, t in enumerate(np.arange(.9, 5.1, .91)): nota(t, 62, .09 + .025 * i, ring=2.2)
nota(1.8, 77, .15, ring=3.5); nota(3.6, 76, .17, ring=3.2)
# -- 5.2: lightning, a wide B-flat major chord
akk(5.18, [58, 62, 65, 70, 74, 77], .6, arp=.012, ring=5.5); nota(5.2, 82, .22, ring=4)
# -- 7.0-24.0: the tree burns, fire is carried into the cave and kept; arpeggio and melody, gradually louder
P1 = [(7.0, 'Dm'), (10.4, 'Bb'), (13.8, 'F'), (17.2, 'C'), (20.6, 'Dm')]; K1 = 24.0
M1 = [[(0, 74, .28), (1.7, 76, .22)], [(0, 77, .3), (1.7, 74, .22)], [(0, 72, .27), (1.7, 69, .2)],
      [(0, 67, .22), (1.13, 72, .23), (2.27, 76, .26)], [(0, 74, .28), (1.7, 69, .2)]]
for j, (t, ch) in enumerate(P1):
    t1 = P1[j + 1][0] if j + 1 < len(P1) else K1; u = j / len(P1)
    nota(t, BAS[ch], .3 + .05 * u, ring=4.5)
    perebor(t, t1, ch, .425, .1 + .04 * u, .12 + .04 * u)
    melodiya(t, M1[j])
# -- 24.0-37.6: the section near Beijing, slow and mysterious, sparse high notes ('thousands of years passed')
P2 = [(24.0, 'Dm'), (27.4, 'Gm'), (30.8, 'Bb'), (34.2, 'A')]
for t, ch in P2:
    nota(t, BAS[ch], .22, ring=5); akk(t + .05, ARP[ch][:3], .15, arp=.09, ring=4.5)
    for dt in (.85, 2.55): nota(t + dt, rng.choice(ARP[ch]) + 12, .08, ring=2.6)
melodiya(0, [(24.4, 69, .18), (27.8, 70, .19), (31.2, 74, .2), (32.9, 77, .24), (34.2, 76, .25), (35.9, 73, .2)], okt=.3)
# -- 37.6-51.2: making fire, an eighth-note ostinato building to the first flame (51.2)
P3 = [(37.6, 'Dm'), (41.0, 'Bb'), (44.4, 'Gm'), (47.8, 'A')]; K3 = 51.2
for j, (t, ch) in enumerate(P3):
    t1 = P3[j + 1][0] if j + 1 < len(P3) else K3; u0, u1 = (t - 37.6) / (K3 - 37.6), (t1 - 37.6) / (K3 - 37.6)
    nota(t, BAS[ch], .24 + .16 * u0, ring=4); nota(t + .01, BAS[ch] + 12, .1 + .14 * u0, ring=3.5)
    perebor(t, t1, ch, .283, .07 + .2 * u0, .07 + .2 * u1, uzor=[2, 3])
melodiya(0, [(41.0, 77, .2), (44.4, 79, .23), (47.8, 76, .26), (48.65, 77, .28), (49.5, 79, .31), (50.35, 81, .34)], okt=.35)
# -- 51.2-63.0: the campfire, warmth, F major, soft arpeggio
akk(51.2, [53, 60, 65, 69, 72, 77], .45, arp=.02, ring=6)
P4 = [(51.2, 'F'), (54.6, 'C'), (58.0, 'Dm'), (61.4, 'Bb')]; K4 = 63.0
M4 = [[(0, 81, .28), (1.7, 79, .2)], [(0, 76, .22), (1.7, 79, .2)], [(0, 77, .23), (1.7, 74, .2)], [(0, 74, .2)]]
for j, (t, ch) in enumerate(P4):
    t1 = P4[j + 1][0] if j + 1 < len(P4) else K4
    if j: nota(t, BAS[ch], .26, ring=4.5)
    perebor(t + (.425 if j == 0 else 0), t1, ch, .425, .1, .1)
    melodiya(t, M4[j], okt=.3)
# -- 63.0-68.7: the animal, an uneasy trill, the campfire flare (65.0) on an A major chord, the animal leaves
nota(63.0, BAS['Gm'], .2, ring=4); akk(63.02, [62, 67, 70], .12, arp=.06, ring=3)
for i, t in enumerate(np.arange(63.1, 65.0, .14)): nota(t, 81 + (i % 2), .045 + .03 * (t - 63.1) / 1.9, ring=.7)
akk(65.0, [57, 61, 64, 69, 73, 76], .48, arp=.015, ring=4.5)
nota(66.9, 62, .16, ring=4); akk(66.95, [65, 69, 74], .13, arp=.08, ring=3.5)
# -- 68.7: D major, a calm ending
akk(68.7, [62, 66, 69, 74, 78], .2, arp=.1, ring=5)

# cut the drone and harsh highs, a room with a soft tail
sos_hp = butter(3, 150, 'highpass', fs=SR, output='sos'); sos_lp = butter(2, 5200, 'lowpass', fs=SR, output='sos')
L, R = sosfilt(sos_lp, sosfilt(sos_hp, L)), sosfilt(sos_lp, sosfilt(sos_hp, R))
ir_t = np.arange(int(3.4 * SR)) / SR; env = np.exp(-ir_t / .65); pre = int(.025 * SR)
irL = np.concatenate([np.zeros(pre), rng.standard_normal(len(ir_t)) * env]); irR = np.concatenate([np.zeros(pre), rng.standard_normal(len(ir_t)) * env])
sos_rv = butter(1, 3200, 'lowpass', fs=SR, output='sos'); irL, irR = sosfilt(sos_rv, irL), sosfilt(sos_rv, irR)
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
wL = fftconvolve(L, irL)[:N]; wR = fftconvolve(R, irR)[:N]
L, R = L * .72 + wL * .5, R * .72 + wR * .5
n = int(D * SR); tt = np.arange(n) / SR; fade = np.clip(tt / .6, 0, 1) * np.clip((D - tt) / 1.6, 0, 1)
x = np.stack([L[:n] * fade, R[:n] * fade], 1); x = x / np.max(np.abs(x)) * .5
wavfile.write(OUT, SR, x.astype(np.float32))
spec = np.abs(np.fft.rfft(x[:, 0] + x[:, 1])) ** 2; fr = np.fft.rfftfreq(n, 1 / SR)
print('ok', OUT, f'{D} s; energy below 150 Hz: {100 * spec[fr < 150].sum() / spec.sum():.2f} %, 150-300 Hz: {100 * spec[(fr >= 150) & (fr < 300)].sum() / spec.sum():.1f} %')
