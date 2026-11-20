"""Overlap check between the clip texts and a reference corpus (for example school textbooks you own locally).

The rule used for this repository: after normalisation (lowercase, the Russian letter yo folded into ye,
stress marks and punctuation removed) a published text must share NO run of 8 or more consecutive words
with the corpus. Narration and captions are written fresh from facts, so this is a safety net, not a rewrite tool.
"""
import re
import unicodedata

N_DEFAULT = 8
_WORD = re.compile(r'[0-9a-zа-я]+')


def normalize(text):
    """Lowercase, yo -> ye, strip stress marks ('+' after a vowel or U+0301) and every non-letter/digit."""
    t = unicodedata.normalize('NFC', text).replace('+', '').replace('́', '')   # stress marks used for TTS
    t = t.lower().replace('ё', 'е')                                          # yo -> ye
    return ' '.join(_WORD.findall(t))


def words(text):
    return normalize(text).split()


def ngrams(ws, n=N_DEFAULT):
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def build_index(corpus_texts, n=N_DEFAULT):
    """Set of all n-word runs in the corpus."""
    idx = set()
    for t in corpus_texts:
        idx |= ngrams(words(t), n)
    return idx


def shared_runs(text, index, n=N_DEFAULT):
    """Every n-word run of `text` that also occurs in the corpus index, merged into maximal runs."""
    ws = words(text); hits = [i for i in range(len(ws) - n + 1) if tuple(ws[i:i + n]) in index]
    runs = []; start = prev = None
    for i in hits:
        if start is None: start = prev = i
        elif i == prev + 1: prev = i
        else: runs.append(' '.join(ws[start:prev + n])); start = prev = i
    if start is not None: runs.append(' '.join(ws[start:prev + n]))
    return runs
