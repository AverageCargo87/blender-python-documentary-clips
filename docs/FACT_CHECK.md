# How facts and captions were checked

The clips are for 10-11 year olds, so every caption and narrated sentence went through a review loop before the render:

1. The narration and captions were written fresh from facts and from the lesson's own script (simple words, one idea
   per sentence; for clip 03 an agent in a methodologist role drafted them), not copied from a textbook.
2. Two reviewer agents read the script, the caption list (`podpisi_spisok.py` exports every caption with its on-screen
   time) and snapshot sheets of the rendered scenes: one in a historian role (is it true, is it current), one in an
   editor or methodologist role (is it clear, readable in time, not overloaded).
3. I accepted or rejected each note, then re-rendered or, if only timing changed, re-timed the finished frames.

Every Russian text in this repository was also checked against school textbook corpora kept outside the repository:
no run of 8 or more consecutive words is shared (`tools/overlap_check.py`; result on 2026-11-20: 0 shared runs).

## What the reviews changed

### 01 Out of Africa

- Migration paths walk over land, with water only at straits, the known sea crossings (Sunda, Wallacea, Bering) and a few short coastal cuts: through the Levant, Iran and India; to China through Vietnam, Guangzhou and Wuhan
  rather than across Tibet; modern humans leave from the Omo valley along the Nile. Branches start exactly on the parent
  arc. A script reports every stretch of every path over water or above 2500 m before rendering (`proverka_putey.py`).
- A path raised above the globe looked as if it ran over the sea under an oblique camera. The pre-render check samples
  the projection on the surface, so it could not catch this; the arcs were lowered and the frames inspected instead.
- Captions use the narrator's own words, for example "Cro-Magnon rock shelter" (grot), not "cave".
- Path colours were taken with an eyedropper from finished frames for the legend; labelled markers move no faster than
  ~40-60 px/s while their caption is visible (`analiz.py` measures it).
- At "only one species remained" the extinct species fade to grey and the H. erectus legend line leaves.

### 02 Kostenki

- The Ice Age landscape near Kostenki: thin wind-blown snow, dry grass, conifer clumps in gully floors, willow on the
  floodplain, chalk outcrops. Everything that did not exist then (fields, villages, roads, a reservoir, ponds) is removed
  from the 2025 satellite image before it becomes the Ice Age texture.
- "The Don froze in winter" instead of "the Don under ice"; "a roof of hides: not found, this is what scientists think";
  "Voronezh about 35 km"; "such figurines are kept in museums of Saint Petersburg" instead of a precise museum count that
  the reviewer marked as inaccurate.
- "The Venus: more than 21,000 years" is kept as formally correct (newer dates are about 25,000 years).
- Layer codes (IVa/IVb) and secondary words were removed from the section; label points were moved onto visible objects;
  the "illustration" and "reconstruction from excavation data" marks were enlarged.
- The section is schematic (17 layers after Sinitsyn, Hoffecker, Bessudnov 2004; Haesaerts et al. 2004; Hoffecker et al.
  2008; Pyle et al. 2006; Giaccio et al. 2008). The volcanic ash is 1-2 cm thick in nature and thickened to ~5 cm in the
  model, which the caption says.
- No hearth was found inside dwelling complex 1, only charcoal and burnt bones, so the narration says "a fire was kept
  burning inside" and the hearth on screen is simply labelled "hearth".

### 03 Fire

- "A layer with ash and charcoal, six metres", not "six metres of ash": the hearths in the section are separate lenses.
- Friction gives a smouldering ember, not a flame; the ember goes into dry grass and only then a flame appears.
- Working sparks come from flint struck on pyrite (flint on flint gives no usable spark).
- The animal is a hyena, which lived both in Africa and near the cave by Beijing; place captions read
  "Africa · a million years ago" and "China. A cave near Beijing · 400 thousand years ago".

## Rules kept for the next clips

- No close-up people or animals in motion (the uncanny valley): people are far away, silhouettes, painted cards, or a
  frozen moment.
- Rock art only from real photographs; no AI "cave paintings".
- Disputed textbook dates stay off screen.
- Facts and captions are checked by two reviewers, as above.
