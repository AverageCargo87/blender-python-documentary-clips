"""Every script compiles (Blender scripts too: compiling does not import bpy), shell and Node scripts parse."""
import glob
import os
import py_compile
import shutil
import subprocess

import pytest

from conftest import REPO

PY = sorted(glob.glob(os.path.join(REPO, '**', '*.py'), recursive=True))
PY = [p for p in PY if not any(s in p.replace('\\', '/') for s in ('/.venv/', '/work/', '/release-assets/'))]
SH = sorted(glob.glob(os.path.join(REPO, 'clips', '*', 'scripts', '*.sh'))) + sorted(glob.glob(os.path.join(REPO, 'tools', '*.sh'))) \
    + [os.path.join(REPO, 'run.sh')]
MJS = sorted(glob.glob(os.path.join(REPO, '**', '*.mjs'), recursive=True))


def test_found_scripts():
    assert len(PY) >= 60 and len(SH) >= 7 and len(MJS) >= 2


@pytest.mark.parametrize('path', PY, ids=lambda p: os.path.relpath(p, REPO))
def test_py_compiles(path, tmp_path):
    py_compile.compile(path, cfile=str(tmp_path / 'x.pyc'), doraise=True)


@pytest.mark.skipif(shutil.which('bash') is None, reason='bash not available')
@pytest.mark.parametrize('path', SH, ids=lambda p: os.path.relpath(p, REPO))
def test_shell_parses(path):
    subprocess.run(['bash', '-n', path], check=True)


@pytest.mark.skipif(shutil.which('node') is None, reason='node not available')
@pytest.mark.parametrize('path', MJS, ids=lambda p: os.path.relpath(p, REPO))
def test_node_parses(path):
    subprocess.run(['node', '--check', path], check=True)


def test_every_script_has_an_english_header():
    """First line of every clip script is an English comment (module header), not Cyrillic."""
    import re
    for p in PY + SH + MJS:
        if os.sep + 'tests' + os.sep in p or p.endswith('__init__.py') or p.endswith('conftest.py'):
            continue
        lines = [l for l in open(p, encoding='utf-8').read().split('\n') if l.strip() and not l.startswith('#!')]
        head = lines[0]
        assert head.lstrip().startswith(('#', '//', '"""')), p
        assert not re.search('[Ѐ-ӿ]', head), p
