"""Pre-render checks for the migration paths of the globe (clip 1).

A path is a list of (lat, lon) waypoints. It is smoothed exactly like the scene does (Chaikin on the sphere +
great-circle densification), then elevation and the ocean mask are sampled along the line. The globe scene
uses this to make sure every path walks over land (water only at straits and known crossings) and never
climbs above 2500 m, before spending ~50 minutes on a render (2070 frames at ~1.5 s/frame).
"""
import math
from dataclasses import dataclass, field

import numpy as np

from .geo import great_circle_km, latlon, smooth_path

HIGH_M = 2500.0


@dataclass
class PathReport:
    name: str
    length_km: float
    water_km: float
    max_elev_m: float
    max_at: tuple
    high_points: int
    water_runs: list = field(default_factory=list)      # [(lat, lon, km)] stretches over water, in order
    mountain_runs: list = field(default_factory=list)   # [(lat, lon, max_m, points)] stretches above HIGH_M

    @property
    def water_share(self):
        return self.water_km / self.length_km if self.length_km else 0.0

    def ok(self, max_water_run_km=60.0, max_high_points=2, allowed_water=()):
        """True if no water stretch longer than max_water_run_km (except allowed (lat, lon) starts) and no long high run."""
        for la, lo, km in self.water_runs:
            if km > max_water_run_km and not any(abs(la - a) < 1.0 and abs(lo - b) < 1.0 for a, b in allowed_water):
                return False
        return all(r[3] <= max_high_points for r in self.mountain_runs)


def sample(grid, lat, lon):
    """Nearest sample of an equirectangular grid (north-up, lon -180..180) at (lat, lon)."""
    h, w = grid.shape[:2]
    x = int((lon + 180) / 360 * w) % w
    y = min(h - 1, max(0, int((90 - lat) / 180 * h)))
    return grid[y, x]


def check_path(name, waypoints, elevation, ocean, high_m=HIGH_M):
    """Walk the smoothed path and collect length, water stretches and high-mountain stretches."""
    D = smooth_path(waypoints)
    water = length = 0.0
    elev = []; runs = []; cur = None
    for a, b in zip(D[:-1], D[1:]):
        km = great_circle_km(a, b); length += km
        la, lo = latlon(a)
        e = float(sample(elevation, la, lo)); w = bool(sample(ocean, la, lo))
        elev.append((e, la, lo))
        if w:
            water += km
            if cur is None:
                cur = [la, lo, 0.0]
            cur[2] += km
        elif cur is not None:
            runs.append((round(cur[0], 1), round(cur[1], 1), round(cur[2]))); cur = None
    if cur:
        runs.append((round(cur[0], 1), round(cur[1], 1), round(cur[2])))
    mountains = []; cur = None
    for e, la, lo in elev:
        if e > high_m:
            if cur is None:
                cur = [la, lo, e, 0]
            cur[2] = max(cur[2], e); cur[3] += 1
        elif cur is not None:
            mountains.append(tuple(cur)); cur = None
    if cur:
        mountains.append(tuple(cur))
    mx = max(elev)
    return PathReport(name, length, water, mx[0], (mx[1], mx[2]), sum(1 for e, *_ in elev if e > high_m), runs, mountains)


def format_report(r):
    """The same one-line summary the original check script printed, plus long water and mountain stretches."""
    lines = [f'{r.name:12s} {r.length_km:6.0f} km, water {r.water_km:5.0f} km ({r.water_share * 100:.0f} %), '
             f'max {r.max_elev_m:.0f} m at ({r.max_at[0]:.1f}, {r.max_at[1]:.1f}), points >{HIGH_M:.0f} m: {r.high_points}']
    lines += [f'     water from {k[:2]} {k[2]} km' for k in r.water_runs if k[2] > 60]
    lines += [f'     mountains from ({g[0]:.1f}, {g[1]:.1f}), points {g[3]}, max {g[2]:.0f} m' for g in r.mountain_runs if g[3] > 2]
    return '\n'.join(lines)
