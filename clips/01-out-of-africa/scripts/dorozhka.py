# Narration track for clip 1: narrator phrases (golos/S1..S8.wav) placed on the timeline + a quiet piano bed (muz-B.wav).   python dorozhka.py <root>
# Voice -> golos-dorozhka.wav (48 kHz, mono); mix and loudness via ffmpeg: voice at -16 LUFS, music bed 3 dB quieter than before.
import sys, json, subprocess, numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
ROOT = sys.argv[1]
DLIT = 69.0
# phrase start times (s): S5 and S6 moved later than plan v4 so that 'Neanderthals' and 'came to Europe' land on their markers
START = {'S1': 5.8, 'S2': 8.4, 'S3': 15.6, 'S4': 25.1, 'S5': 39.0, 'S6': 46.0, 'S7': 57.6, 'S8': 61.0}
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
# music bed: light piano (muzyka.py B), chosen in review over the earlier drone (zvuk.wav is no longer used)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{ROOT}/golos-dorozhka.wav', '-i', f'{ROOT}/muz-B.wav', '-filter_complex',
                '[0]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,pan=stereo|c0=c0|c1=c0[v];[1]loudnorm=I=-29:TP=-8:LRA=7,aresample=48000[m];'
                '[v][m]amix=inputs=2:normalize=0:duration=longest,volume=-3dB[a]', '-map', '[a]', '-ar', '48000', f'{ROOT}/zvuk-itog.wav'], check=True)
print('ok')
