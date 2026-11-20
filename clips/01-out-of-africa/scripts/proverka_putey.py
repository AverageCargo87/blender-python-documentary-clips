# Pre-render path check: the same smoothing as scena.py -> elevation (rel_ef_8192.npy) and water (okean_8192.png) sampled along each line.
#   python proverka_putey.py <root> <paths.json>          (paths.json: clips/01-out-of-africa/data/puti.json)
# The maths lives in lib/paths.py (unit-tested without Blender); this wrapper only loads the rasters and prints the report.
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from lib.paths import check_path, format_report
Image.MAX_IMAGE_PIXELS = None
ROOT = sys.argv[1]
E = np.load(f'{ROOT}/dannye/rel_ef_8192.npy')
OK = np.asarray(Image.open(f'{ROOT}/tex/okean_8192.png')) > 127
if __name__ == '__main__':
    P = json.load(open(sys.argv[2], encoding='utf-8'))
    for name, pts in P.items(): print(format_report(check_path(name, pts, E, OK)))
