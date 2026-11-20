"""Pre-render path checks on synthetic elevation and ocean rasters (no downloads needed)."""
import json
import os

import numpy as np
import pytest

from conftest import REPO
from lib import paths

W, H = 720, 360   # 0.5 deg per pixel, equirectangular
WORK = os.environ.get('WORK', os.path.join(REPO, 'work'))


def world(ocean_lon_band=None, mountain=None):
    elev = np.full((H, W), 300.0, np.float32); ocean = np.zeros((H, W), bool)
    if ocean_lon_band:
        lo0, lo1 = ocean_lon_band
        x0, x1 = int((lo0 + 180) / 360 * W), int((lo1 + 180) / 360 * W)
        ocean[:, x0:x1] = True; elev[:, x0:x1] = -3000
    if mountain:
        la0, la1, lo0, lo1, h = mountain
        y0, y1 = int((90 - la1) / 180 * H), int((90 - la0) / 180 * H)
        x0, x1 = int((lo0 + 180) / 360 * W), int((lo1 + 180) / 360 * W)
        elev[y0:y1, x0:x1] = h
    return elev, ocean


def test_land_path_is_clean():
    e, o = world()
    r = paths.check_path('land', [(0, 0), (5, 10), (10, 20)], e, o)
    assert r.water_km == 0 and r.high_points == 0 and r.ok()
    assert 2400 < r.length_km < 2700                       # ~22.4 deg of arc, slightly shortened by smoothing


def test_sea_crossing_is_measured_and_flagged():
    e, o = world(ocean_lon_band=(10, 14))
    r = paths.check_path('sea', [(0, 0), (0, 20)], e, o)
    assert 400 < r.water_km < 500                          # 4 deg of ocean at the equator ~ 445 km
    assert len(r.water_runs) == 1 and not r.ok()
    assert r.ok(allowed_water=[r.water_runs[0][:2]])       # a known strait can be whitelisted


def test_mountain_stretch_detected():
    e, o = world(mountain=(-2, 2, 8, 12, 4200.0))
    r = paths.check_path('pass', [(0, 0), (0, 20)], e, o)
    assert r.max_elev_m == 4200 and r.high_points > 2 and not r.ok()
    assert 'mountains from' in paths.format_report(r)


def test_sample_wraps_longitude():
    e = np.zeros((H, W)); e[:, 0] = 1
    assert paths.sample(e, 0, -180) == 1 and paths.sample(e, 0, 180) == 1


def test_real_waypoints_are_well_formed():
    P = json.load(open(os.path.join(REPO, 'clips', '01-out-of-africa', 'data', 'puti.json'), encoding='utf-8'))
    assert set(P) == {'er-yava', 'er-kitay', 'sap-evropa', 'sap-aziya', 'sap-amerika'}
    for name, pts in P.items():
        assert len(pts) >= 10, name
        assert all(-90 <= la <= 90 and -180 <= lo <= 180 for la, lo in pts), name
    assert P['er-yava'][0][1] > 30 and P['sap-amerika'][-1][1] < -50       # from East Africa ... to South America


@pytest.mark.skipif(not os.path.exists(os.path.join(WORK, '01-out-of-africa', 'tex', 'okean_8192.png')),
                    reason='needs ./run.sh 01 fetch && ./run.sh 01 textures')
def test_real_paths_against_real_relief():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    R = os.path.join(WORK, '01-out-of-africa')
    E = np.load(os.path.join(R, 'dannye', 'rel_ef_8192.npy'))
    O = np.asarray(Image.open(os.path.join(R, 'tex', 'okean_8192.png'))) > 127
    P = json.load(open(os.path.join(REPO, 'clips', '01-out-of-africa', 'data', 'puti.json'), encoding='utf-8'))
    for name, pts in P.items():
        r = paths.check_path(name, pts, E, O)
        assert r.water_share < .15, name                    # only straits, the Sunda shelf, Wallacea, Bering
        assert r.max_elev_m < 3000, name                    # no Himalaya or Tibet crossing
