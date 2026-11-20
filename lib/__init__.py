"""Shared, Blender-free helpers for the three clips.

Everything in this package is plain Python + numpy so it can be unit-tested without Blender:
geo (tile decoding, reprojection, sphere math), paths (pre-render checks of migration paths),
captions (easing windows, reading time, slow-down retiming) and textcheck (n-gram overlap check).
"""
