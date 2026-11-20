# Light background music without any drone (review note: 'the background hum feels alarming'): major key, nothing below ~150 Hz, sparse soft notes.
#   python muzyka.py <out.wav> <A|B> [duration]
#   A: 'kalimba/harp', pentatonic, light arpeggios;  B: 'warm piano', slow chords and a sparse melody.
import sys, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
OUT, VAR = sys.argv[1], sys.argv[2]; D = float(sys.argv[3]) if len(sys.argv) > 3 else 69.0
PETLYA = '--petlya' in sys.argv   # lesson background: loops seamlessly
D0 = D; D = D + (5.0 if PETLYA else 0)
SR = 48000; N = int(SR * D); rng = np.random.default_rng(11)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def nota(t0, midi, gr, pan=0.0, dlit=2.2, tip='A'):
    i0 = int(t0 * SR)
    if i0 >= N: return
    n = min(int(dlit * 1.6 * SR), N - i0); t = np.arange(n) / SR; f = hz(midi)
    if tip == 'A':   # kalimba/harp: fast attack, the metallic 4th partial decays faster
        x = (np.sin(2 * np.pi * f * t) * np.exp(-t / dlit) + .35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / (dlit * .5))
             + .08 * np.sin(2 * np.pi * 4.2 * f * t) * np.exp(-t / .25))
        att = np.clip(t / .006, 0, 1)
    else:            # piano: soft hammer, several partials with different decay times
        x = sum(a * np.sin(2 * np.pi * k * f * t * (1 + .0004 * k * k)) * np.exp(-t / (dlit / k ** .7)) for k, a in ((1, 1), (2, .45), (3, .22), (4, .12), (5, .06)))
        att = np.clip(t / .012, 0, 1)
    x = (x * att * gr).astype(np.float32)
    L[i0:i0 + n] += x * np.float32(np.sqrt((1 - pan) / 2)); R[i0:i0 + n] += x * np.float32(np.sqrt((1 + pan) / 2))
# harmony: C major, A minor, F major, G major (I-vi-IV-V), 4 beats each
AKK = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
PENT = [60, 62, 64, 67, 69, 72, 74, 76, 79]
if VAR == 'A':
    BPM = 68; dol = 60 / BPM; t = 0.0 if PETLYA else 1.0; k = 0
    while t < (D0 - .01 if PETLYA else D - 3):
        akk = AKK[(k // 8) % 4]
        # eighth-note arpeggios, but sparse: chord tones on strong beats, an occasional pentatonic note on weak beats
        if k % 2 == 0: nota(t, akk[(k // 2) % 3] + 12, .30, pan=rng.uniform(-.4, .4), dlit=2.0)
        elif rng.random() < .35: nota(t, rng.choice(PENT) + 12, .16, pan=rng.uniform(-.6, .6), dlit=1.4)
        if k % 8 == 0: nota(t, akk[0], .22, pan=0, dlit=3.0)      # chord root an octave lower, but never below 174 Hz
        t += dol / 2; k += 1
else:
    BPM = 60 if PETLYA else 56; dol = 60 / BPM; t = 0.0 if PETLYA else 1.0; k = 0
    while t < (D0 - .01 if PETLYA else D - 3):
        akk = AKK[k % 4]
        for j, m in enumerate(akk): nota(t + j * .06, m, .18, pan=(j - 1) * .3, dlit=3.2, tip='B')   # soft rolled chord
        for b in (1, 2, 3):                                        # sparse melody on top
            if rng.random() < .55: nota(t + b * dol, rng.choice([m + 12 for m in akk] + [74, 76]), .12, pan=rng.uniform(-.3, .3), dlit=2.2, tip='B')
        t += 4 * dol; k += 1
# no drone: high-pass at 150 Hz, soft top end
sos_hp = butter(2, 150, 'highpass', fs=SR, output='sos'); sos_lp = butter(2, 5000, 'lowpass', fs=SR, output='sos')
L, R = sosfilt(sos_lp, sosfilt(sos_hp, L)), sosfilt(sos_lp, sosfilt(sos_hp, R))
# light reverb (stereo noise impulse response, 2.2 s decay)
ir_t = np.arange(int(2.6 * SR)) / SR; env = np.exp(-ir_t / .55)
irL = rng.standard_normal(len(ir_t)) * env; irR = rng.standard_normal(len(ir_t)) * env
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
wL = fftconvolve(L, irL)[:N]; wR = fftconvolve(R, irR)[:N]
L, R = L * .75 + wL * .45, R * .75 + wR * .45
if PETLYA:
    n0 = int(D0 * SR); L[:N - n0] += L[n0:]; R[:N - n0] += R[n0:]; L, R = L[:n0], R[:n0]   # tail -> wrapped to the start
    x = np.stack([L, R], 1)
else:
    tt = np.arange(N) / SR; fade = np.clip(tt / 2.0, 0, 1) * np.clip((D - tt) / 3.5, 0, 1)
    x = np.stack([L * fade, R * fade], 1)
x = x / np.max(np.abs(x)) * .5
wavfile.write(OUT, SR, x.astype(np.float32)); print('ok', OUT)
