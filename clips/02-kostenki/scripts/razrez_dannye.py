# Section data for Kostenki 14 (Markina Gora, east slope), SCHEMATIC, after Sinitsyn, Hoffecker, Bessudnov 2004;
# Haesaerts et al. 2004; Hoffecker et al. 2008; Pyle et al. 2006; Giaccio et al. 2008 (research brief by a reviewer agent).
# Depths are rounded (+-0.5-1 m, they vary a lot along the promontory). The ash is 1-2 cm in nature, thickened to ~5 cm in the model (labelled).
#   python razrez_dannye.py <root>  -> dannye/razrez.json
import sys, json
R = sys.argv[1]
SL = [
    # key, thickness m, colour, texture, recess, wave, second colour and blotch share, label
    dict(kl='pochva', tol=1.0, cvet='#2c2520', faktura='kroshka', utop=.004, volna=.05),
    dict(kl='pochva2', tol=.6, cvet='#4a3a2c', faktura='kroshka', utop=.004, volna=.06),
    dict(kl='less', tol=2.0, cvet='#cdb98a', faktura='suglinok', utop=.012, volna=.06, polosy='#a88a62'),
    dict(kl='sloy1', tol=.2, cvet='#7d7466', faktura='kroshka', utop=.006, volna=.05, cvet2='#8f9a9c', pyatna=.5),
    dict(kl='mel1', tol=.5, cvet='#b9b2a4', faktura='shcheben', utop=-.006, volna=.07, cvet2='#ece8de', pyatna=.7),
    dict(kl='gumus_v', tol=.45, cvet='#4f4236', faktura='kroshka', utop=.004, volna=.06),
    dict(kl='sloy2', tol=.15, cvet='#1f1b18', faktura='kroshka', utop=.004, volna=.05),
    dict(kl='gumus_v2', tol=.4, cvet='#5a4a3c', faktura='kroshka', utop=.004, volna=.06),
    dict(kl='belesy', tol=.4, cvet='#e3dcc8', faktura='suglinok', utop=.0, volna=.05),
    dict(kl='rzhavy', tol=.12, cvet='#7a5e4a', faktura='kroshka', utop=.004, volna=.04),
    dict(kl='pepel', tol=.05, cvet='#d6cdb0', faktura='pepel', utop=-.006, volna=.08, cvet2='#7a5e4a', pyatna=.35),
    dict(kl='sloy4a_b', tol=.15, cvet='#d9d2c0', faktura='suglinok', utop=.0, volna=.05),
    dict(kl='sloy4a', tol=.35, cvet='#6e6152', faktura='kroshka', utop=.004, volna=.05),
    dict(kl='lashamp', tol=.2, cvet='#bdb6a8', faktura='suglinok', utop=.006, volna=.05, polosy='#7a5c44'),
    dict(kl='mamont', tol=.4, cvet='#9c7c60', faktura='suglinok', utop=.008, volna=.06, cvet2='#e8e4da', pyatna=.22),
    dict(kl='sloy4b', tol=.4, cvet='#3a2f26', faktura='kroshka', utop=.004, volna=.05, cvet2='#8a4a36', pyatna=.18),
    dict(kl='osnova', tol=.6, cvet='#8b8d86', faktura='shcheben', utop=-.004, volna=.05, cvet2='#c9b98f', pyatna=.5),
]
# finds: (layer index, x, depth in layer 0..1, kind, size, rotation deg): flint, bones (femur/scapula), charcoal, hearth
N = {k: i for i, k in enumerate(s['kl'] for s in SL)}
NAH = [
    [N['sloy1'], -1.6, .5, 'kost', .55, [0, 90, 6]], [N['sloy1'], .9, .5, 'kremen', .045, [10, 20, 0]],
    [N['sloy2'], -.8, .5, 'kost', .42, [0, 90, -10]], [N['sloy2'], .2, .5, 'kremen', .04, [0, 30, 0]], [N['sloy2'], 1.5, .45, 'ugol', .05, [0, 0, 0]],
    [N['sloy4a'], -1.9, .45, 'kost', .5, [0, 90, 12]], [N['sloy4a'], -1.1, .55, 'kost', .38, [0, 90, -25]], [N['sloy4a'], -.2, .5, 'kost', .45, [0, 90, 4]],
    [N['sloy4a'], .7, .5, 'ugol', .05, [0, 0, 0]], [N['sloy4a'], 1.6, .45, 'kost', .4, [0, 90, 18]],
    [N['mamont'], -.4, .5, 'kost', .9, [0, 90, 3]], [N['mamont'], .9, .55, 'kost', .7, [0, 90, -8]],
    [N['sloy4b'], -1.3, .5, 'ochag', .55, [0, 0, 0]], [N['sloy4b'], -1.0, .4, 'ugol', .05, [0, 0, 0]], [N['sloy4b'], -1.6, .45, 'ugol', .04, [0, 0, 20]],
    [N['sloy4b'], .1, .5, 'kremen', .05, [0, 20, 0]], [N['sloy4b'], .6, .55, 'kremen', .04, [10, 50, 0]], [N['sloy4b'], 1.4, .5, 'kost', .35, [0, 90, -15]],
]
H = sum(s['tol'] for s in SL)
# camera: from above onto the grass -> down along the face to the oldest layer (sec, position, look-at)
KAM = [[0, [3.6, -6.4, 1.6], [.3, .8, -.8]], [3.5, [2.6, -4.9, -2.2], [.1, 0, -2.6]], [9.0, [2.2, -4.3, -5.3], [0, 0, -5.6]], [15.0, [1.7, -3.7, -6.9], [-.2, 0, -7.1]]]   # slowed to 23 s in the clip by frame interpolation (zamedlit_S.sh)
json.dump({'sloi': SL, 'nahodki': NAH, 'kamera': KAM, 'shirina': 5.0, 'dlit': 15.0}, open(f'{R}/dannye/razrez.json', 'w'), ensure_ascii=False, indent=1)
print('layers', len(SL), 'depth', round(H, 2))
