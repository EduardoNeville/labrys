"""Aggregator bake-off: the shipped objective vs alternatives, same components.

The shipped total is `0.45*morph + 0.15*entropy + 0.10*prefix + 0.30*kober`.
Measured individually (oracle_diagnose.py), the components rank the true value
top-1 at 67% / 47% / 59% / 100% — but the sum manages only 13%. The components
are on incomparable scales, so the sum is dominated by whichever term happens to
have the largest spread.

This script scores each (hidden sign, candidate) ONCE, caches the four
components, and then evaluates many aggregators on the identical cache. No
re-scoring, so the comparison is exact.

Metrics per aggregator:
  top1      — truth is the unique argmax
  in_argmax — truth is in the argmax set (ties counted as success)
  rank      — mean rank percentile of the truth (0 = best)

Usage: uv run python pipeline/aggregator_bakeoff.py --language linear-b
"""

from __future__ import annotations

import argparse
import logging
import random
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.oracle_diagnose import CONFIGS, build

logger = logging.getLogger("bakeoff")
REPO = Path(__file__).resolve().parent.parent


def collect(completer, trials: int, hidden: int) -> list:
    """Cache (components per candidate) for each hidden sign draw."""
    confirmed = completer.confirmed
    bids = sorted(confirmed)
    rng = random.Random(0)
    draws = []
    for _ in range(trials):
        hs = rng.sample(bids, min(hidden, len(bids)))
        eff = {b: v for b, v in confirmed.items() if b not in hs}
        truth_all = {b: confirmed[b] for b in hs}
        for bid in hs:
            cands = completer.get_candidates(bid, confirmed=eff)
            vals = dict(truth_all)
            rows = []
            for cand in cands:
                vals[bid] = cand
                m, e, p, k = completer.score_completion(
                    vals, confirmed_override=eff, uncertain_override=hs,
                    sample_size=50)
                rows.append({"cand": cand, "m": m, "e": e, "p": p, "k": k})
            draws.append({"bid": bid, "truth": confirmed[bid], "rows": rows})
    return draws


def _ranks(values: list) -> list:
    """Percentile rank per element, ties share the average rank. 1.0 = best."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    out = [0.0] * len(values)
    i = 0
    n = len(values)
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2
        pct = 1.0 - (avg / max(n - 1, 1))
        for t in range(i, j + 1):
            out[order[t]] = pct
        i = j + 1
    return out


def evaluate(draws: list, name: str, score_fn) -> dict:
    top1 = in_arg = 0
    ranks = []
    for d in draws:
        rows = d["rows"]
        if not rows:
            continue
        vals = [score_fn(r) for r in rows]
        best = max(vals)
        arg = [r["cand"] for r, v in zip(rows, vals) if v == best]
        if d["truth"] in arg:
            in_arg += 1
            if len(arg) == 1:
                top1 += 1
        rr = _ranks(vals)
        tix = [i for i, r in enumerate(rows) if r["cand"] == d["truth"]]
        if tix:
            ranks.append(rr[tix[0]])
    n = len(draws)
    return {"name": name, "n": n, "top1": top1 / n, "in_argmax": in_arg / n,
            "rank": sum(ranks) / max(len(ranks), 1)}


# ── aggregators ──────────────────────────────────────────────────────────────
SHIPPED = lambda r: 0.45 * r["m"] + 0.15 * r["e"] + 0.10 * r["p"] + 0.30 * r["k"]
AGGS = {
    "shipped 0.45m+0.15e+0.10p+0.30k": SHIPPED,
    "kober only": lambda r: r["k"],
    "entropy(bigram) only": lambda r: r["e"],
    "morph only": lambda r: r["m"],
    "prefix only": lambda r: r["p"],
    "kober+entropy (equal)": lambda r: r["k"] + r["e"],
    "kober+entropy+prefix (equal)": lambda r: r["k"] + r["e"] + r["p"],
    "all four (equal)": lambda r: r["m"] + r["e"] + r["p"] + r["k"],
}


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--language", default="linear-b", choices=list(CONFIGS))
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = build(args.language)
    print(f"language={args.language}  anchors={len(c.confirmed)}  "
          f"inscriptions={len(c.inscriptions)}")
    draws = collect(c, args.trials, args.hidden)
    c.close()

    sizes = Counter(len(d["rows"]) for d in draws)
    print(f"hidden-sign draws: {len(draws)}  "
          f"mean candidate-list size {sum(s*n for s,n in sizes.items())/len(draws):.1f}")

    results = []
    for name, fn in AGGS.items():
        results.append(evaluate(draws, name, fn))

    # rank-normalised variants (Borda): needs the per-draw rank vectors
    def borda(keys, name):
        top1 = in_arg = 0
        ranks = []
        for d in draws:
            cols = [[r[k] for r in d["rows"]] for k in keys]
            pct = [_ranks(col) for col in cols]
            vals = [sum(col[i] for col in pct) for i in range(len(d["rows"]))]
            best = max(vals)
            arg = [r["cand"] for r, v in zip(d["rows"], vals) if v == best]
            if d["truth"] in arg:
                in_arg += 1
                if len(arg) == 1:
                    top1 += 1
            tix = [i for i, r in enumerate(d["rows"]) if r["cand"] == d["truth"]]
            rr = _ranks(vals)
            if tix:
                ranks.append(rr[tix[0]])
        n = len(draws)
        return {"name": name, "n": n, "top1": top1 / n, "in_argmax": in_arg / n,
                "rank": sum(ranks) / max(len(ranks), 1)}

    results.append(borda(["m", "e", "p", "k"], "BORDA all four (rank-normalised)"))
    results.append(borda(["k", "e"], "BORDA kober+entropy (rank-normalised)"))

    # two-stage: kober as a hard series filter, then entropy picks the vowel
    def two_stage(d):
        rows = d["rows"]
        kb = max(r["k"] for r in rows)
        kept = [r for r in rows if r["k"] >= kb - 1e-12]
        top = max(r["e"] for r in kept)
        arg = [r["cand"] for r in kept if r["e"] == top]
        return arg

    top1 = in_arg = 0
    ranks = []
    for d in draws:
        arg = two_stage(d)
        if d["truth"] in arg:
            in_arg += 1
            if len(arg) == 1:
                top1 += 1
        vals = [SHIPPED(r) for r in d["rows"]]
        rr = _ranks(vals)
        tix = [i for i, r in enumerate(d["rows"]) if r["cand"] == d["truth"]]
        if tix:
            ranks.append(rr[tix[0]])
    n = len(draws)
    results.append({"name": "TWO-STAGE kober filter -> entropy argmax",
                    "n": n, "top1": top1 / n, "in_argmax": in_arg / n, "rank": 0.0})

    print(f"\n{'aggregator':44s} {'top1':>7s} {'in_argmax':>10s}  mean rank")
    for r in results:
        print(f"{r['name']:44s} {r['top1']:7.1%} {r['in_argmax']:10.1%}  "
              f"{r['rank']:8.3f}")


if __name__ == "__main__":
    main()