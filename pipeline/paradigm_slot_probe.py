"""Feasibility probe: paradigm-slot alternation (the untested operationalization).

Frame sharing (two signs sharing a neighbour anywhere in the corpus) is empty on
Linear B: 0.87-0.98x chance. But that is NOT what Ventris/Kober actually used.
The real relation is tighter:

    two signs alternate in the SAME SLOT of a word — identical left AND right
    neighbour, same word boundary — i.e. the paradigm cells of one stem.

That yields strong constraints, and they are eliminative rather than merely
correlational:

  * alternating partners share the CONSONANT (same series),
  * their VOWELS are complementary: if a sign alternates with da/de/di/do at one
    slot, it is du — the missing cell of its own series.

This probe measures, on Linear B (answer key available):
  1. P(same series | slot alternation) vs chance
  2. whether the vowel is the complement of the partners' vowels, and how often
     that complement is UNIQUE (= the value is identified, not just constrained)
  3. the same two numbers under a permutation control (random same-size partner
     sets drawn from the sign's own series)

If (2) is materially above the control, paradigm-slot alignment is worth
building. If not, the method family is closed on the best available evidence.

Usage: uv run python pipeline/paradigm_slot_probe.py
"""

from __future__ import annotations

import csv
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.phonetics import CONS_SERIES_MAP, VOWEL_COLUMNS, series_of, vowel_of

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "languages/linear-b/data/database/linear-b.db"
KEY = REPO / "languages/linear-b/answer_key.csv"

MIN_SHARED_CONTEXTS = 2  # a partner must co-occur in >= 2 distinct slots


def load():
    conn = sqlite3.connect(str(DB))
    words = [tuple(s.split("-")) for (s,) in
             conn.execute("SELECT sign_sequences FROM words") if s and s.strip()]
    conn.close()
    vals = {r["bennett_id"]: r["refined_value"].strip()
            for r in csv.DictReader(open(KEY, encoding="utf-8"))
            if r.get("decision") == "CONFIRM"}
    return words, vals


def contexts(words):
    """(left, right) slot per sign occurrence, word-boundary aware."""
    ctx_signs = defaultdict(set)
    for w in words:
        for i, s in enumerate(w):
            left = w[i - 1] if i > 0 else "<"
            right = w[i + 1] if i + 1 < len(w) else ">"
            ctx_signs[(left, right)].add(s)
    ctxs_of = defaultdict(set)
    for slot, signs in ctx_signs.items():
        for s in signs:
            ctxs_of[s].add(slot)
    return ctxs_of


def partners_of(ctxs_of, min_shared=MIN_SHARED_CONTEXTS):
    """sign -> Counter(partner -> number of shared slots)."""
    out = defaultdict(Counter)
    signs = list(ctxs_of)
    for i, a in enumerate(signs):
        for b in signs[i + 1:]:
            shared = len(ctxs_of[a] & ctxs_of[b])
            if shared >= min_shared:
                out[a][b] = shared
                out[b][a] = shared
    return out


def minimal_pair_partners(words):
    """Strictest variant: word types of equal length differing in EXACTLY one
    position (true paradigm cells of one frame). Buckets each word by its
    spelling with one position blanked, so grouping is exact, not quadratic.
    """
    buckets = defaultdict(set)
    for w in set(words):
        for i in range(len(w)):
            buckets[w[:i] + (None,) + w[i + 1:]].add(w[i])
    out = defaultdict(Counter)
    for variants in buckets.values():
        if len(variants) < 2:
            continue
        vs = sorted(variants)
        for i, a in enumerate(vs):
            for b in vs[i + 1:]:
                out[a][b] += 1
                out[b][a] += 1
    return out


def evaluate(label, partners, known, rng, by_series):
    st = Counter()
    for bid, truth in known.items():
        ts, tv = series_of(truth), vowel_of(truth)
        cand = [p for p in partners.get(bid, {}) if p in known]
        st["with_partners"] += int(bool(cand))
        if not cand:
            continue
        st["n"] += 1
        same = [p for p in cand if series_of(known[p]) == ts]
        st["series_agree"] += len(same)
        st["total"] += len(cand)
        partner_vowels = {vowel_of(known[p]) for p in same}
        remaining = [v for v in VOWEL_COLUMNS if v not in partner_vowels]
        if len(remaining) == 1:
            st["unique"] += 1
            st["correct"] += int(remaining[0] == tv)
        pool = [x for x in by_series[ts] if x != bid]
        if len(pool) >= len(same):
            for _ in range(3):
                ctrl = rng.sample(pool, len(same))
                cv = {vowel_of(known[p]) for p in ctrl}
                rem = [v for v in VOWEL_COLUMNS if v not in cv]
                st["ctrl_n"] += 1
                if len(rem) == 1:
                    st["ctrl_unique"] += 1
                    st["ctrl_correct"] += int(rem[0] == tv)
    n = max(st["n"], 1)
    cn = max(st["ctrl_n"], 1)
    print(f"\n--- {label} ---")
    print(f"  signs with partners              : {st['with_partners']}/{len(known)}")
    print(f"  partners share the series        : {st['series_agree']}/{max(st['total'],1)} "
          f"({st['series_agree']/max(st['total'],1):.1%})")
    print(f"  vowel complement unique          : {st['unique']}/{n} ({st['unique']/n:.1%})"
          f"   correct when unique: {st['correct']}/{max(st['unique'],1)}")
    print(f"  control: unique {st['ctrl_unique']/cn:.1%}, "
          f"correct {st['ctrl_correct']/max(st['ctrl_unique'],1):.1%}")
    return st


def main() -> None:
    words, vals = load()
    known = {b: v for b, v in vals.items()
             if series_of(v) != "?" and vowel_of(v) != "?"}
    print(f"words {len(words)}, tokens {sum(len(w) for w in words)}, "
          f"signs with a usable value {len(known)}")

    rng = random.Random(0)
    by_series = defaultdict(list)
    for b, v in known.items():
        by_series[series_of(v)].append(b)

    maj = Counter(series_of(v) for v in known.values()).most_common(1)
    print(f"majority-series baseline: {maj[0][1]/len(known):.1%}")

    partner_defs = [
        ("A. shared slot (same left AND right neighbour, >=2 slots)",
         partners_of(contexts(words))),
        ("B. strict minimal pair (word types differing in exactly 1 position)",
         minimal_pair_partners(words)),
    ]
    for label, partners in partner_defs:
        evaluate(label, partners, known, rng, by_series)


if __name__ == "__main__":
    main()