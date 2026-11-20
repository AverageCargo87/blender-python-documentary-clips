# Narration track for clip 2 'Kostenki': narrator phrases (golos/S1..S13.wav) placed on the timeline + a quiet piano bed.   python dorozhka.py <root>
# Voice -> golos-dorozhka.wav (48 kHz, mono); mix and loudness via ffmpeg: voice at -16 LUFS, music bed 3 dB quieter than before.
import sys, json, subprocess, numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
ROOT = sys.argv[1]
DLIT = 116.2
# phrase start times (s), by scene in v6: A 0, B 11.0, S 21.4, C 43.8, H 54.2, D1 73.6, D2 85.0, E 101.2; each plays while its labels are visible
START = {'S1': 1.0, 'S2': 6.8, 'S3': 12.6, 'S4': 22.6, 'S5': 33.4, 'S6': 45.2, 'S7': 56.0, 'S8': 66.6, 'S9': 74.8, 'S10': 86.4,
         'S11': 96.6, 'S12': 102.6, 'S13': 109.8}
SR = 48000
v = np.zeros(int(SR * DLIT), np.float32)
for k, t0 in START.items():
    sr, x = wavfile.read(f'{ROOT}/golos/{k}.wav'); x = x.astype(np.float32) / 32768
    x = resample_poly(x, SR, sr).astype(np.float32)
    i = int(t0 * SR); v[i:i + len(x)] += x[:len(v) - i]
wavfile.write(f'{ROOT}/golos-dorozhka.wav', SR, v)
S = json.load(open(f'{ROOT}/golos/slova.json', encoding='utf-8'))
for k, t0 in START.items():
    print(k, f'{t0:.1f}\u2013{t0 + S[k]["dlit"]:.2f}', ' '.join(f"{w['w']}@{t0 + w['s']:.1f}" for w in S[k]['slova']))
# music bed: light piano (muzyka.py B, chosen in review); the earlier drone zvuk.wav is no longer used
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{ROOT}/golos-dorozhka.wav', '-i', f'{ROOT}/muz-B4.wav', '-filter_complex',
                '[0]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,pan=stereo|c0=c0|c1=c0[v];[1]loudnorm=I=-29:TP=-8:LRA=7,aresample=48000[m];'
                '[v][m]amix=inputs=2:normalize=0:duration=longest,volume=-3dB[a]', '-map', '[a]', '-ar', '48000', f'{ROOT}/zvuk-itog.wav'], check=True)
print('ok')
