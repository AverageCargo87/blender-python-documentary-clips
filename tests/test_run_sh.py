"""run.sh without ElevenLabs keys: the voice stage of clip 01 still writes a (music-only) track, so `edit` can mux a preview."""
import os
import shutil
import subprocess
import sys

import pytest
from scipy.io import wavfile

from conftest import REPO


@pytest.mark.skipif(shutil.which('bash') is None or shutil.which('ffmpeg') is None, reason='needs bash and ffmpeg')
@pytest.mark.skipif(os.path.exists(os.path.join(REPO, '.env')), reason='a local .env may hold real keys; this test must not call ElevenLabs')
def test_voice_stage_without_keys_writes_music_only_track(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith('ELEVENLABS')}
    env.update(WORK=tmp_path.as_posix(), PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE='1')
    r = subprocess.run(['bash', os.path.join(REPO, 'run.sh'), '01', 'voice'], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert 'music bed only' in r.stderr
    sr, x = wavfile.read(tmp_path / '01-out-of-africa' / 'zvuk-itog.wav')
    assert sr == 48000 and x.ndim == 2 and abs(len(x) / sr - 69.0) < 0.1
    assert not (tmp_path / '01-out-of-africa' / 'golos').exists()          # no narration was requested
