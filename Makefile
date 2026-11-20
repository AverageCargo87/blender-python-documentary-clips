# Thin wrapper around run.sh. PREVIEW=1 switches every render to the half-resolution preview path.
#   make test                  unit tests + py_compile, no Blender needed
#   make smoke                 clip 01: fetch open data, build textures, check paths, render 3 frames headless + label pass
#   make clip1 [PREVIEW=1]     full clip 01 (needs Blender 5.2 and, for narration, ElevenLabs keys)
#   make clip2 / make clip3    same for clips 02 and 03
SHELL := bash
PY ?= python
P := $(if $(PREVIEW),--preview,)

.PHONY: test venv smoke clip1 clip2 clip3 check clean

venv:
	$(PY) -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt || .venv/bin/python -m pip install -r requirements-dev.txt

test:
	$(PY) -m pytest -q

smoke:
	./run.sh 01 fetch $(P) && ./run.sh 01 textures && ./run.sh 01 check && ./run.sh 01 smoke

check:
	./run.sh 01 check

clip1:
	./run.sh 01 all $(P)

clip2:
	./run.sh 02 all $(P)

clip3:
	./run.sh 03 all $(P)

clean:
	rm -rf work
