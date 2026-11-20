"""Caption timing: easing windows, reading time, slow-down retiming, and consistency of the real clip timelines."""
import ast
import json
import os
import re

import pytest

from conftest import REPO
from lib import captions as C


def const(path, name):
    """Literal value of a top-level assignment in a script, without running it (scripts need Blender or data)."""
    tree = ast.parse(open(os.path.join(REPO, path), encoding='utf-8').read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    v = node.value
                    if isinstance(v, ast.Call) and getattr(v.func, 'id', '') == 'dict':      # START = dict(S1a=1.6, ...)
                        return {k.arg: ast.literal_eval(k.value) for k in v.keywords}
                    return ast.literal_eval(v)
                if isinstance(t, ast.Tuple) and name in [e.id for e in t.elts if isinstance(e, ast.Name)]:
                    vals = ast.literal_eval(node.value)
                    return vals[[e.id for e in t.elts].index(name)]
    raise KeyError(name)


def test_window_shape():
    assert C.window(5.0, 2.0, 8.0) == 1.0
    assert C.window(1.0, 2.0, 8.0) == 0.0 and C.window(9.0, 2.0, 8.0) == 0.0
    assert 0 < C.window(2.3, 2.0, 8.0) < 1
    assert C.window(2.3, 2.0, 8.0) == pytest.approx(C.window(7.7, 2.0, 8.0))
    assert C.smootherstep(.5) == pytest.approx(.5) and C.smoothstep(.5) == pytest.approx(.5)


def test_reading_time_rule():
    assert C.reading_time('x' * 90) == pytest.approx(10.8)
    assert C.visible_time(2.0, 8.0) == 5.0 and C.visible_time(2.0, 2.5) == 0.0
    assert not C.too_fast('очаг', 10.6, 19.4) and C.too_fast('x' * 90, 0, 5)


def test_retime_map_shape():
    m = C.retime_map(480, 331, 480, 1.8)
    assert len(m) == 330 + 270
    assert m[:330] == [float(f) for f in range(1, 331)]
    assert m[330] == 331 and m[-1] == pytest.approx(480)
    assert all(b >= a for a, b in zip(m, m[1:]))


def test_interp_point():
    fr = {1: [0.0, 0.0], 2: [10.0, 20.0]}
    assert C.interp_point(fr, 1.5) == [5.0, 10.0] and C.interp_point(fr, 2.0) == [10.0, 20.0]


def test_kostenki_slowdowns_match_the_edit():
    """Scenes S, H and D2 were slowed down instead of re-rendered; the edit's scene lengths must equal the retimed lengths."""
    DL = dict(const('clips/02-kostenki/scripts/montazh2.py', '_DL'))
    assert C.retimed_duration(15.0, 1, 450, 46 / 30) == pytest.approx(DL['S'])      # 15 s -> 23 s
    assert C.retimed_duration(16.0, 331, 480, 1.8) == pytest.approx(DL['H'])        # 16 s -> 20 s
    assert C.retimed_duration(14.0, 1, 420, 1.2) == pytest.approx(DL['D2'])         # 14 s -> 16.8 s
    s = open(os.path.join(REPO, 'clips/02-kostenki/scripts/zamedlit_S.sh'), encoding='utf-8').read()
    assert 'minterpolate=fps=46' in s


def test_clip_frame_counts():
    FPS, DLIT = const('clips/01-out-of-africa/scripts/scena.py', 'FPS'), const('clips/01-out-of-africa/scripts/scena.py', 'DLIT')
    assert int(FPS * DLIT) == 2070                                          # clip 1: 69 s at 30 fps
    d = [x for _, x in const('clips/02-kostenki/scripts/montazh2.py', '_DL')]
    assert int(round((sum(d) - .6 * (len(d) - 1)) * 30)) == 3486             # clip 2: 1:56 at 30 fps, 0.6 s dissolves
    plany = const('clips/03-fire/scripts/montazh.py', 'PLANY')
    total = sum(x for _, x in plany) - .6 * (len(plany) - 1)
    assert len(plany) == 9 and total == pytest.approx(70.8) and int(round(total * 24)) == 1699
    assert round(sum(x for _, x in plany) * 24) == 1814                       # frames rendered before the dissolves


def narration(clip):
    j = json.load(open(os.path.join(REPO, 'clips', clip, 'data', 'narration.json'), encoding='utf-8'))
    ph = j['phrases'] if j['mode'] == 'phrases' else [p for g in j['groups'] for p in g['phrases']]
    return j, ph


@pytest.mark.parametrize('clip', ['01-out-of-africa', '02-kostenki', '03-fire'])
def test_narration_timeline_has_no_overlaps(clip):
    j, ph = narration(clip)
    ids = [p['id'] for p in ph]
    assert len(ids) == len(set(ids))
    placed = C.phrase_starts({p['id']: p['start'] for p in ph}, {p['id']: p['duration'] for p in ph}, gap=0.0)
    ends = 0.0
    for p in ph:
        s, e = placed[p['id']]
        assert s == pytest.approx(p['start']), f'{p["id"]} would have to move: it overlaps the previous phrase'
        assert s >= ends; ends = e
    assert ends <= j['clip_duration'], 'narration runs past the end of the clip'


@pytest.mark.parametrize('clip,script', [('01-out-of-africa', 'clips/01-out-of-africa/scripts/dorozhka.py'),
                                         ('02-kostenki', 'clips/02-kostenki/scripts/dorozhka.py'),
                                         ('03-fire', 'clips/03-fire/scripts/golos_raskladka.py')])
def test_narration_json_matches_the_mixing_script(clip, script):
    _, ph = narration(clip)
    start = const(script, 'START')
    assert {p['id']: p['start'] for p in ph} == start


@pytest.mark.parametrize('clip', ['01-out-of-africa', '02-kostenki', '03-fire'])
def test_narration_text_is_clean(clip):
    raw = open(os.path.join(REPO, 'clips', clip, 'data', 'narration.json'), encoding='utf-8').read()
    assert '\u2014' not in raw and '\u2013' not in raw            # dashes are stored as JSON escapes
    _, ph = narration(clip)
    for p in ph:
        assert re.search('[Ѐ-ӿ]', p['text']) and p['text'].strip()[-1] in '.?!', p['id']


def test_species_cards_follow_the_narrator():
    """Clip 1: each species card appears within 1 s of the moment the narrator says the key word.

    Word timings (data/word_timings.json) are the per-word timestamps returned by the TTS API for the recorded take.
    """
    KART = const('clips/01-out-of-africa/scripts/post.py', 'KART')
    _, ph = narration('01-out-of-africa')
    start = {p['id']: p['start'] for p in ph}
    W = json.load(open(os.path.join(REPO, 'clips/01-out-of-africa/data/word_timings.json'), encoding='utf-8'))
    key = {'avstralopitek': ('S2', 'австрал'), 'olduvay': ('S3', 'умел'),
           'yava': ('S4', 'Ява'), 'kitay': ('S4', 'синан'),
           'neandertal': ('S5', 'неанд'), 'kromanon': ('S6', 'Европ')}
    for name, (_, _, a, b, _) in KART.items():
        sid, stem = key[name]
        t_word = start[sid] + next(s for w, s, e in W[sid]['words'] if w.startswith(stem))
        assert abs(a - t_word) < 1.0, (name, a, t_word)
        assert b - a > 2.39, name                     # every card stays up long enough to read the title
    for sid, w in W.items():                          # the measured takes are the durations stored in narration.json
        assert w['duration'] == pytest.approx({p['id']: p['duration'] for p in ph}[sid])
