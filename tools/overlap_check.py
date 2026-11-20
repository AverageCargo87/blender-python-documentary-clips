"""Check every Russian text in this repository against local reference corpora (not part of the repo).

    python tools/overlap_check.py <corpus path> [<corpus path> ...] [--n 8] [--extra "text" ...]

A corpus path may be a .pdf (text via PyMuPDF), a .json (all string values; for files named text-kino*.json
only the "show" fields), a .txt/.md file, or a directory (searched recursively for those types).
Repository texts: string literals and comments of .py/.mjs files, .json string values and .md lines that
contain Cyrillic. Exit code 1 if any shared run of n words is found.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib.textcheck import build_index, shared_runs   # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CYR = re.compile('[Ѐ-ӿ]')
SKIP_DIRS = {'.git', '.venv', 'work', 'release-assets', 'node_modules', '__pycache__'}


def json_strings(o, only_key=None, key=None):
    if isinstance(o, dict):
        for k, v in o.items(): yield from json_strings(v, only_key, k)
    elif isinstance(o, list):
        for v in o: yield from json_strings(v, only_key, key)
    elif isinstance(o, str) and (only_key is None or key == only_key):
        yield o


def dehyphen(t):
    return re.sub(r'(\w)[-­]\s*\n\s*(\w)', r'\1\2', t)


def load_corpus(path):
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in sorted(files):
                if f.lower().endswith(('.pdf', '.json', '.txt', '.md')): yield from load_corpus(os.path.join(root, f))
        return
    low = path.lower()
    if low.endswith('.pdf'):
        import fitz                                     # PyMuPDF, only needed for PDF corpora
        with fitz.open(path) as doc:
            yield dehyphen('\n'.join(p.get_text() for p in doc))
    elif low.endswith('.json'):
        only = 'show' if os.path.basename(low).startswith('text-kino') else None
        yield '\n'.join(json_strings(json.loads(open(path, encoding='utf-8', errors='replace').read()), only))
    else:
        yield dehyphen(open(path, encoding='utf-8', errors='replace').read())


def repo_texts():
    """(label, text) for every repository file that contains Cyrillic: whole file text in reading order."""
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith(('.py', '.mjs', '.json', '.md', '.sh')): continue
            p = os.path.join(root, f); rel = os.path.relpath(p, REPO).replace('\\', '/')
            t = open(p, encoding='utf-8').read()
            if f.endswith('.json'):
                t = '\n'.join(s for s in json_strings(json.loads(t)) if CYR.search(s))
            else:
                t = '\n'.join(l for l in t.split('\n') if CYR.search(l)).encode('utf-8').decode('utf-8')
            if CYR.search(t): yield rel, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('corpus', nargs='+'); ap.add_argument('--n', type=int, default=8); ap.add_argument('--extra', action='append', default=[])
    a = ap.parse_args()
    corpus = []
    for c in a.corpus: corpus += list(load_corpus(c))
    idx = build_index(corpus, a.n)
    print(f'corpus: {len(a.corpus)} paths, {sum(len(t) for t in corpus):,} characters, {len(idx):,} distinct {a.n}-word runs')
    found = 0; checked = 0; nwords = 0
    items = list(repo_texts()) + [(f'--extra {i + 1}', t) for i, t in enumerate(a.extra)]
    for label, text in items:
        checked += 1; nwords += len(text.split())
        for run in shared_runs(text, idx, a.n):
            found += 1; print(f'SHARED in {label}: {run}')
    print(f'checked {checked} texts (~{nwords:,} words): {found} shared runs of {a.n}+ words')
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
