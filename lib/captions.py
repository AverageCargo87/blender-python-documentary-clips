"""Caption timing helpers shared by the edit scripts.

* easing and show/hide windows, as used by post.py (clip 1) and montazh*.py (clips 2 and 3);
* a reading-time rule for 10-11 year olds (podpisi_spisok.py);
* the slow-down retiming used to give captions more time WITHOUT re-rendering: frames of a finished scene are
  stretched with motion interpolation and the on-screen label points are remapped with the same function.
"""
import math


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smoothstep(u):
    u = clamp(u); return u * u * (3 - 2 * u)


def smootherstep(u):
    u = clamp(u); return u * u * u * (u * (6 * u - 15) + 10)


def window(t, a, b, fade=.6, ease=smoothstep):
    """Opacity of a caption shown from a to b with soft fades of length `fade` (0 outside, 1 in the middle)."""
    return ease((t - a) / fade) * ease((b - t) / fade)


CPS = 9.0          # characters per second a 10-11 year old reads comfortably from the screen (with margin)
FADE_LOSS = 1.0    # seconds lost to fade-in and fade-out


def reading_time(text, cps=CPS):
    """Seconds needed to read a caption: length / cps + 0.8 s to find it on screen."""
    return len(text.replace('\n', ' ')) / cps + .8


def visible_time(a, b):
    """Fully readable time of a caption shown from a to b (fades excluded)."""
    return max(0.0, b - a - FADE_LOSS)


def too_fast(text, a, b, cps=CPS):
    return visible_time(a, b) < reading_time(text, cps)


def retime_map(n0, a, b, k):
    """Source frame position for every output frame when frames a..b (1-based, inclusive) of an n0-frame
    scene are slowed down k times; frames outside the segment are kept as they are.

    Output length is (a - 1) + round((b - a + 1) * k) + (n0 - b). Positions inside the segment are fractional
    and are used to interpolate label points between the neighbouring source frames (zamedlit.py).
    """
    nseg = b - a + 1; nout = int(round(nseg * k))
    head = [float(f) for f in range(1, a)]
    mid = [a + q * (nseg - 1) / max(1, nout - 1) for q in range(nout)]
    tail = [float(f) for f in range(b + 1, n0 + 1)]
    return head + mid + tail


def interp_point(frames, pos):
    """Linear interpolation of a per-frame point list {1: [x, y, ...], 2: ...} at a fractional frame position."""
    n0 = len(frames)
    i0 = int(math.floor(pos)); i1 = min(n0, i0 + 1); u = pos - i0; i0 = max(1, min(n0, i0))
    r0, r1 = frames[i0], frames[i1]
    return [r0[c] * (1 - u) + r1[c] * u for c in range(len(r0))]


def retimed_duration(seconds, a, b, k, fps=30):
    """New scene length in seconds after slowing frames a..b down k times."""
    n0 = int(round(seconds * fps))
    return len(retime_map(n0, a, b, k)) / fps


def phrase_starts(starts, durations, gap=.35):
    """Place narration phrases at their planned starts, pushing a phrase later if it would overlap the previous one.

    Same rule as golos_raskladka.py (clip 3). Returns {id: (start, end)} in planned order.
    """
    out = {}; end = 0.0
    for pid, t0 in starts.items():
        t = max(t0, end + gap)
        end = t + durations[pid]; out[pid] = (round(t, 3), round(end, 3))
    return out
