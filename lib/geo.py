"""Geodata math shared by the globe (clip 1) and the Don valley (clip 2).

The functions mirror what the clip scripts do inline (rel_ef.py, tekstury.py, sputnik.py, proverka_putey.py)
so the maths can be tested without Blender or network access.
"""
import math

import numpy as np

EARTH_R_KM = 6371.0
MERC_R = 20037508.342789244          # half the Web Mercator extent, metres
MERC_MAX_LAT = 85.05                  # rows outside this latitude are filled, not sampled


def terrarium_decode(rgb):
    """Terrarium PNG pixels (..., 3) -> elevation in metres: R*256 + G + B/256 - 32768."""
    a = np.asarray(rgb, dtype=np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def terrarium_encode(m):
    """Inverse of terrarium_decode (used by tests and for writing synthetic tiles)."""
    v = np.asarray(m, dtype=np.float64) + 32768
    r = np.floor(v / 256); g = np.floor(v - r * 256); b = np.round((v - r * 256 - g) * 256)
    return np.stack([r, g, b], -1).clip(0, 255).astype(np.uint8)


def mosaic(tiles, nx, ny, tile=256):
    """Stack decoded tiles {(i, j): array(tile, tile)} into one (ny*tile, nx*tile) grid, i = column, j = row."""
    out = np.zeros((ny * tile, nx * tile), np.float32)
    for (i, j), t in tiles.items():
        out[j * tile:(j + 1) * tile, i * tile:(i + 1) * tile] = t
    return out


def lat_rows(height):
    """Latitude at the centre of each row of an equirectangular grid of the given height (north up)."""
    return 90 - (np.arange(height) + .5) / height * 180


def mercator_row(lat_deg, merc_height):
    """Fractional row in a whole-world Web Mercator image of merc_height pixels for a latitude."""
    lat = np.clip(lat_deg, -MERC_MAX_LAT, MERC_MAX_LAT)
    return (1 - np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)) / np.pi) / 2 * merc_height


def equirect_from_mercator(merc, width=8192, height=4096, south_fill=2600.0, north_fill=-3000.0):
    """Nearest-neighbour reprojection of a whole-world Web Mercator grid to an equirectangular grid.

    Same maths as clips/01-out-of-africa/scripts/rel_ef.py: rows beyond +-85.05 deg are filled
    (Antarctica as ice at south_fill metres, the Arctic as ocean at north_fill metres).
    """
    lat = lat_rows(height)
    yy = mercator_row(lat, merc.shape[0])
    xx = (np.arange(width) + .5) / width * merc.shape[1]
    yi = np.clip(yy.astype(int), 0, merc.shape[0] - 1)
    xi = np.clip(xx.astype(int), 0, merc.shape[1] - 1)
    eq = merc[yi[:, None], xi[None, :]].astype(np.float32)
    eq[lat < -MERC_MAX_LAT, :] = south_fill
    eq[lat > MERC_MAX_LAT, :] = north_fill
    return eq


def merc_x(x, z):
    """Left edge of tile column x at zoom z in EPSG:3857 metres."""
    return x / 2 ** z * 2 * MERC_R - MERC_R


def merc_y(y, z):
    """Top edge of tile row y at zoom z in EPSG:3857 metres."""
    return MERC_R - y / 2 ** z * 2 * MERC_R


def tile_block_bounds(z, x0, y0, n):
    """(left, top, right, bottom) in EPSG:3857 metres of an n x n block of tiles starting at (x0, y0)."""
    return merc_x(x0, z), merc_y(y0, z), merc_x(x0 + n, z), merc_y(y0 + n, z)


def merc_to_lonlat(x, y):
    """EPSG:3857 metres -> (lon, lat) degrees."""
    lon = x / MERC_R * 180
    lat = math.degrees(2 * math.atan(math.exp(y / MERC_R * math.pi)) - math.pi / 2)
    return lon, lat


def lonlat_to_tile(lon, lat, z):
    """(lon, lat) degrees -> fractional slippy-map tile coordinates (x, y) at zoom z."""
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def lonlat_to_equirect_px(lon, lat, width, height):
    """(lon, lat) -> pixel (x, y) in an equirectangular image, as used for lakes and path sampling."""
    return (lon + 180) / 360 * width, (90 - lat) / 180 * height


def ll(lat, lon):
    """Latitude/longitude in degrees -> unit vector (x towards lon 0, z towards the north pole)."""
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])


def latlon(v):
    """Unit vector -> (lat, lon) degrees."""
    return math.degrees(math.asin(max(-1, min(1, v[2])))), math.degrees(math.atan2(v[1], v[0]))


def normalize(v):
    return v / np.linalg.norm(v)


def slerp(a, b, t):
    """Spherical linear interpolation between unit vectors a and b."""
    om = math.acos(max(-1, min(1, float(a @ b))))
    if om < 1e-6:
        return a
    return (a * math.sin((1 - t) * om) + b * math.sin(t * om)) / math.sin(om)


def chaikin_sphere(points, iterations=4):
    """Chaikin corner cutting on the sphere; keeps the first and last point."""
    U = list(points)
    for _ in range(iterations):
        V = [U[0]]
        for p, q in zip(U[:-1], U[1:]):
            V += [normalize(p * .75 + q * .25), normalize(p * .25 + q * .75)]
        V.append(U[-1]); U = V
    return U


def densify(points, n_seg=24):
    """Dense great-circle sampling: n_seg slerp steps per segment, last point appended."""
    D = []
    for p, q in zip(points[:-1], points[1:]):
        for k in range(n_seg):
            D.append(slerp(p, q, k / n_seg))
    D.append(points[-1])
    return D


def smooth_path(waypoints_latlon, iterations=4, n_seg=24):
    """Waypoints [(lat, lon), ...] -> the dense smoothed polyline that the globe scene draws."""
    return densify(chaikin_sphere([ll(*p) for p in waypoints_latlon], iterations), n_seg)


def great_circle_km(a, b):
    """Great-circle distance between unit vectors in km."""
    return EARTH_R_KM * math.acos(max(-1, min(1, float(a @ b))))


def horizon_dot(r):
    """A point at radius r (globe radius 1) leaves the visible disc when dot(normal, view) < sqrt(1 - 1/r^2)."""
    return math.sqrt(max(0.0, 1 - 1 / (r * r)))
