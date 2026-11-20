"""Reprojection and sphere maths used by the globe and the valley."""
import math

import numpy as np

from lib import geo


def test_terrarium_roundtrip_and_known_values():
    assert geo.terrarium_decode([128, 0, 0]) == 0.0                 # sea level
    assert geo.terrarium_decode([0, 0, 0]) == -32768.0
    m = np.array([-10677.0, -95.0, 0.0, 236.0, 7188.0, 8848.5])
    assert np.allclose(geo.terrarium_decode(geo.terrarium_encode(m)), m, atol=1 / 256)


def test_mosaic_places_tiles_by_column_and_row():
    t = {(i, j): np.full((4, 4), 10 * j + i, np.float32) for i in range(3) for j in range(2)}
    m = geo.mosaic(t, 3, 2, tile=4)
    assert m.shape == (8, 12)
    assert m[0, 0] == 0 and m[0, 11] == 2 and m[7, 0] == 10 and m[7, 11] == 12


def test_mercator_row_equator_and_symmetry():
    assert math.isclose(float(geo.mercator_row(0.0, 1000)), 500.0)
    top, bot = geo.mercator_row(60.0, 1000), geo.mercator_row(-60.0, 1000)
    assert math.isclose(float(top + bot), 1000.0, abs_tol=1e-6)
    assert float(geo.mercator_row(85.05, 1000)) < 1.0                  # the Web Mercator edge is ~85.05 deg


def test_equirect_from_mercator_samples_the_right_rows():
    H_M = 512
    merc = np.repeat(np.arange(H_M, dtype=np.float32)[:, None], 256, axis=1)   # value = mercator row
    eq = geo.equirect_from_mercator(merc, width=64, height=32)
    lat = geo.lat_rows(32)
    inside = np.abs(lat) < geo.MERC_MAX_LAT
    expect = np.clip(geo.mercator_row(lat, H_M).astype(int), 0, H_M - 1)
    assert np.array_equal(eq[inside, 0], expect[inside].astype(np.float32))
    assert (eq[lat < -geo.MERC_MAX_LAT] == 2600.0).all() and (eq[lat > geo.MERC_MAX_LAT] == -3000.0).all()


def test_equirect_output_size_and_columns():
    merc = np.tile(np.arange(256, dtype=np.float32)[None, :], (256, 1))         # value = mercator column
    eq = geo.equirect_from_mercator(merc, width=8192, height=4096)
    assert eq.shape == (4096, 8192)
    assert eq[2048, 0] == 0 and eq[2048, -1] == 255 and eq[2048, 4096] == 128


def test_kostenki_lies_inside_the_valley_tile_block():
    x, y = geo.lonlat_to_tile(39.04, 51.39, 12)
    assert 2489 <= x < 2496 and 1361 <= y < 1368
    px, py = (x - 2489) * 256, (y - 1361) * 256       # the scene's site marker sits at relief pixel (824, 794)
    assert abs(px - 824) < 40 and abs(py - 794) < 40


def test_tile_block_bounds_roundtrip():
    l, t, r, b = geo.tile_block_bounds(12, 2489, 1361, 7)
    lon0, lat1 = geo.merc_to_lonlat(l, t); lon1, lat0 = geo.merc_to_lonlat(r, b)
    assert 38.7 < lon0 < 38.8 and 39.3 < lon1 < 39.4 and 51.1 < lat0 < lat1 < 51.7
    assert math.isclose(r - l, t - b)                                      # square block in metres


def test_sphere_helpers():
    for lat, lon in [(0, 0), (51.39, 39.04), (-33.9, 18.4), (66, -168)]:
        la, lo = geo.latlon(geo.ll(lat, lon))
        assert math.isclose(la, lat, abs_tol=1e-9) and math.isclose(lo, lon, abs_tol=1e-9)
    a, b = geo.ll(0, 0), geo.ll(0, 90)
    assert np.allclose(geo.slerp(a, b, 0), a) and np.allclose(geo.slerp(a, b, 1), b)
    assert np.isclose(np.linalg.norm(geo.slerp(a, b, .37)), 1.0)
    assert math.isclose(geo.great_circle_km(a, b), math.pi / 2 * geo.EARTH_R_KM)
    paris, london = geo.ll(48.857, 2.352), geo.ll(51.507, -0.128)
    assert 330 < geo.great_circle_km(paris, london) < 350


def test_chaikin_keeps_ends_and_densify_count():
    pts = [geo.ll(0, 0), geo.ll(10, 10), geo.ll(0, 20)]
    sm = geo.chaikin_sphere(pts, 4)
    assert np.allclose(sm[0], pts[0]) and np.allclose(sm[-1], pts[-1])
    assert len(sm) == len(pts) * 2 ** 4                 # each pass: first + 2 per segment + last = 2n points
    d = geo.densify(sm, 24)
    assert len(d) == (len(sm) - 1) * 24 + 1
    assert all(np.isclose(np.linalg.norm(v), 1.0) for v in d)


def test_horizon_threshold_for_raised_arcs():
    assert geo.horizon_dot(1.0) == 0.0
    assert math.isclose(geo.horizon_dot(1.0075), math.sqrt(1 - 1 / 1.0075 ** 2))
    assert 0.12 < geo.horizon_dot(1.0075) < 0.13      # arcs 0.75 % above the globe vanish ~7 deg before the limb
