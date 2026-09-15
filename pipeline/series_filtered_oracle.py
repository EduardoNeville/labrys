"""Decisive test: with the consonant series known, can the shipped scorer pick
the vowel?

Findings so far:
  * ingest round-trips 100% (corpus is correct)
  * truth is in the candidate list 87.5% of the time; mean list size 70
  * Kober identifies the true consonant series in 100% of draws
  * but `get_candidates` only applies the series vote when >= 2 series appear
    and keeps every series above a half-max threshold — so a hidden sign
    typically still faces ~70 candidates (2-3 series x 5 vowels x consonants)
  * no aggregator ever made truth the unique argmax among those 70

So the question that decides everything: if the candidate space is reduced to
the Kober-agreed series (the constraint the method was designed to supply, but
applies too weakly), does the scorer recover vowels at better than chance?

Conditions, each measured against its own chance rate (1/|candidates|):
  DOMINANT-SERIES / others-true — candidates limited to the argmax Kober series,
      all other hidden signs held at their true values. Isolates the scorer's
      vowel discrimination.
  DOMINANT-SERIES / iterative  — same candidate reduction, full search with
      multi-pass coordinate ascent. End-to-end recovery.

Usage: uv run python pipeline/series_filtered_oracle.py --language linear-b
"""

from __future__ import annotations

import argparse
import logging
import random
from collections import Counter
from pathlib import Path

from pipeline.oracle_diagnose import CONFIGS, build
from pipeline.ventris.complete import CONS_SERIES_MAP, VOWEL_COLUMNS, vowel_of

logger = logging.getLogger("series_oracle")

# series -> consonants the candidate generator emits for that series
SERIES_CONS = {
    "LABIAL": "pm", "DENTAL": "tdn", "VELAR": "kq", "SIBILANT": "sz",
    "LIQUID": "rl", "PALATAL": "j", "SEMIVOWEL": "w",
}


def dominant_series(completer, bid: str, anchors: dict) -> set:
    """Kober series votes from links to anchors; return the argmax set."""
    votes = Counter()
    for partner in completer.kober_clinks.get(bid, set()):
        if partner in anchors:
            s = CONS_SERIES_MAP.get(anchors[partner], "")
            if s and s != "VOWEL":
                votes[s] += 1
    if not votes:
        return set()
    top = max(votes.values())
    return {s for s, n in votes.items() if n == top}


def series_candidates(completer, bid: str, allowed: set) -> list:
    """All CV values in the allowed series (plus bare vowels), intersected with
    the sign's full candidate list so we never invent a value the method would
    not consider."""
    base = set(completer.get_candidates(bid))
    out = []
    for s in allowed:
        for cons in SERIES_CONS.get(s, ""):
            for v in VOWEL_COLUMNS:
                val = f"{cons}{v}"
                if val in base:
                    out.append(val)
    for v in VOWEL_COLUMNS:
        if v in base:
            out.append(v)
    return sorted(set(out))


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--language", default="linear-b", choices=list(CONFIGS))
    p.add_argument("--trials", type=int, default=4)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = build(args.language)
    confirmed = c.confirmed
    bids = sorted(confirmed)
    rng = random.Random(0)

    print(f"language={args.language} anchors={len(bids)} inscriptions={len(c.inscriptions)}")

    st = Counter()
    st["size_sum"] = 0
    for _ in range(args.trials):
        hs = rng.sample(bids, min(args.hidden, len(bids)))
        eff = {b: v for b, v in confirmed.items() if b not in hs}
        truth_all = {b: confirmed[b] for b in hs}

        for bid in hs:
            truth = confirmed[bid]
            allowed = dominant_series(c, bid, eff)
            if not allowed:
                st["no_series_vote"] += 1
                continue
            cands = series_candidates(c, bid, allowed)
            if not cands:
                st["empty_cands"] += 1
                continue
            st["n"] += 1
            st["size_sum"] += len(cands)
            st["series_ok"] += int(CONS_SERIES_MAP.get(truth, "?") in allowed)

            # others-true condition
            vals = dict(truth_all)
            scored = []
            for cand in cands:
                vals[bid] = cand
                m, e, pr, k = c.score_completion(
                    vals, confirmed_override=eff, uncertain_override=hs, sample_size=50)
                scored.append((0.45 * m + 0.15 * e + 0.10 * pr + 0.30 * k, cand))
            best = max(s for s, _ in scored)
            arg = [cd for s, cd in scored if s == best]
            st["true_in_arg"] += int(truth in arg)
            st["top1"] += int(len(arg) == 1 and arg[0] == truth)

        # iterative end-to-end with the same candidate reduction
        red = {}
        for bid in hs:
            allowed = dominant_series(c, bid, eff)
            red[bid] = series_candidates(c, bid, allowed) if allowed else c.get_candidates(bid, confirmed=eff)
        vals = {b: (red[b][0] if red[b] else "a") for b in hs}
        for _ in range(4):
            changed = False
            for bid in sorted(hs, key=lambda b: len(red[b])):
                if not red[bid]:
                    continue
                best_s, best_v = -1.0, vals[bid]
                for cand in red[bid]:
                    vals[bid] = cand
                    m, e, pr, k = c.score_completion(
                        vals, confirmed_override=eff, uncertain_override=hs, sample_size=50)
                    s = 0.45 * m + 0.15 * e + 0.10 * pr + 0.30 * k
                    if s > best_s:
                        best_s, best_v = s, cand
                changed |= (best_v != vals[bid])
                vals[bid] = best_v
            if not changed:
                break
        for b in hs:
            st["iter_n"] += 1
            st["iter_ok"] += int(vals[b] == confirmed[b])

    n = max(st["n"], 1)
    print(f"\nseries votes available for {st['n']}/{st['n'] + st['no_series_vote']} draws; "
          f"true series allowed in {st['series_ok']}/{n} ({st['series_ok']/n:.1%})")
    print(f"mean candidate-list size after series filter: {st['size_sum']/n:.1f} "
          f"(was ~70)")
    print(f"\n{'condition':44s} {'recovery':>9s} {'chance':>8s} {'lift':>7s}")
    chance = 1.0 / max(st["size_sum"] / n, 1)
    print(f"{'dominant-series, others held true':44s} {st['top1']/n:9.1%} "
          f"{chance:8.1%} {(st['top1']/n)/chance:6.2f}x")
    print(f"{'dominant-series, in argmax (ties ok)':44s} {st['true_in_arg']/n:9.1%} "
          f"{chance:8.1%} {(st['true_in_arg']/n)/chance:6.2f}x")
    it = max(st["iter_n"], 1)
    print(f"{'dominant-series, iterative end-to-end':44s} {st['iter_ok']/it:9.1%} "
          f"{chance:8.1%} {(st['iter_ok']/it)/chance:6.2f}x")
    c.close()


if __name__ == "__main__":
    main()