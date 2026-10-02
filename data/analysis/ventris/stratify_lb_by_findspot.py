"""Stratify the closure paper's §4 results by findspot.

The paper's negatives were computed on the whole Linear B sandbox, and that sandbox has the same
shape as the Linear A corpus this project just learned to distrust:

    KN (Knossos)  3326 of 4794 inscriptions  (69.4%)
    PY (Pylos)    1105                      (23.0%)
    TH, MY, TI, KH  the rest

Pooling cannot manufacture a signal, but it *can* dilute a stratum-specific one away — which is the
one way the paper's central negative could be wrong. So the two cheap §4 operationalizations are
re-run per findspot, using the canonical implementations rather than copies:

  §4.3 frame sharing      pipeline/frame_link_test.py     (build_links, pairwise_relations)
  §4.4 paradigm slots     pipeline/paradigm_slot_probe.py (contexts, partners_of,
                                                           minimal_pair_partners, evaluate)

Pre-registered reading, before the numbers: expected uniform — the pooled result is at or below
chance (§4.3) and anti-predictive (§4.4), and a stratum's own majority baseline moves with it. What
would falsify the paper's framing is any stratum where a relation clears ~1.2x its own chance.
PY matters most: it is a different archive, a different scribal tradition, and it contributes more
words than KN (6412 vs 5482) despite having a third of the inscriptions.

    uv run python data/analysis/ventris/stratify_lb_by_findspot.py
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

import random  # noqa: E402

from pipeline.frame_link_test import build_links, pairwise_relations  # noqa: E402
from pipeline.paradigm_slot_probe import (  # noqa: E402
    contexts, evaluate, minimal_pair_partners, partners_of)
from pipeline.phonetics import series_of  # noqa: E402

LB_DB = REPO / "languages/linear-b/data/database/linear-b.db"
KEY = REPO / "languages/linear-b/answer_key.csv"
MIN_WORDS = 200


def main() -> None:
    conn = sqlite3.connect(str(LB_DB))
    words_by_site: dict = defaultdict(list)
    for site, seq in conn.execute(
            "SELECT COALESCE(f.site,'?'), w.sign_sequences FROM words w "
            "JOIN inscriptions i ON i.id = w.inscription_id "
            "LEFT JOIN findspots f ON f.id = i.findspot_id "
            "WHERE w.sign_sequences IS NOT NULL AND w.sign_sequences != ''"):
        words_by_site[site].append(tuple(seq.split("-")))
    conn.close()

    known = {r["bennett_id"]: r["refined_value"].strip()
             for r in csv.DictReader(open(KEY, encoding="utf-8"))
             if r.get("decision") == "CONFIRM"}
    by_series: dict = defaultdict(list)
    for bid, val in known.items():
        by_series[series_of(val)].append(bid)

    total = sum(len(w) for w in words_by_site.values())
    print(f"words by findspot (total {total}); strata with >= {MIN_WORDS} words are tested")
    order = sorted(words_by_site, key=lambda s: -len(words_by_site[s]))

    for site in order:
        words = words_by_site[site]
        if len(words) < MIN_WORDS:
            print(f"\n### {site}: {len(words)} words — skipped (too small to test)")
            continue
        print(f"\n{'=' * 78}\n### {site}: {len(words)} words "
              f"({len(words)/total:.1%} of the corpus)\n{'=' * 78}")
        follow, precede, _, _ = build_links(words)
        pairwise_relations(follow, precede, known)
        ctxs = {w: contexts([w]) for w in set(words)}
        ctxs_of = defaultdict(set)
        for w, c in ctxs.items():
            for sign, ctx in c.items():
                ctxs_of[sign] |= ctx
        rng = random.Random(0)
        evaluate(f"A. shared slot — {site}", partners_of(ctxs_of), known, rng, by_series)
        evaluate(f"B. strict minimal pair — {site}", minimal_pair_partners(words), known,
                 rng, by_series)

    print("\nread the per-stratum numbers against the POOLED ones in METHOD_CLOSURE_PAPER §4.3/§4.4")
    print("(frame sharing 0.85-0.98x chance; paradigm A 13.9% series / control 19.4% unique;")
    print(" B 14.3% / control 18.5%). A stratum clearing ~1.2x its own chance falsifies the framing.")


if __name__ == "__main__":
    main()
