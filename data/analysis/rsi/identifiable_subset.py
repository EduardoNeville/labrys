"""Does the objective have resolution, on the draws where identification is possible?

Two things make the all-draws numbers hard to read, and both are denominators rather than
signals:

1. **The true value is not even a candidate on ~58-64% of draws.** `oracle_diagnose` part B:
   29/80 = 36.2%; `rsi_evaluate`'s membership metric: 44.4% over 160 draws. On those draws no
   aggregator can ever be right, and averaging them in dilutes every rate by ~2.5x.

2. **`phase0_null_control.py`'s permutation null had 100% membership**, because it replaced the
   truth with a candidate *drawn from the candidate list*. The real truth is in that list only
   ~40% of the time. So the null was solving an easier problem than the measurement, and it
   beating every channel (0.25-0.52x) was that asymmetry as much as it was flatness.

This script fixes the denominator: metrics are computed **conditional on the truth being in the
candidate list**, and the null is a uniformly random *other* candidate from the same list —
same subset, same membership, same candidate space. What the channels carry on identifiable
draws is then a measurement rather than an average over impossible ones.

    uv run python data/analysis/rsi/identifiable_subset.py --trials 25
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.aggregator_bakeoff import AGGS, _ranks, collect           # noqa: E402
from pipeline.oracle_diagnose import build                              # noqa: E402
from pipeline.rsi_tree import verdict_for                               # noqa: E402


def argmax_set(rows, vals):
    best = max(vals)
    return [r["cand"] for r, v in zip(rows, vals) if v == best]


def measure(draws, name, fn, rng) -> dict:
    """top1 / in_argmax / mean rank on the identifiable subset, plus a within-subset null."""
    top1 = in_arg = null_in_arg = 0
    ranks, null_ranks, arg_sizes = [], [], []
    n = 0
    for d in draws:
        rows = d["rows"]
        cands = [r["cand"] for r in rows]
        if d["truth"] not in cands:
            continue                      # not identifiable: excluded from BOTH sides
        n += 1
        vals = fn(rows)
        arg = argmax_set(rows, vals)
        arg_sizes.append(len(arg))
        if d["truth"] in arg:
            in_arg += 1
            if len(arg) == 1:
                top1 += 1
        rr = _ranks(vals)
        tix = [i for i, r in enumerate(rows) if r["cand"] == d["truth"]]
        ranks.append(rr[tix[0]])
        # within-subset null: a random OTHER candidate, drawn from the same list
        others = [i for i, c in enumerate(cands) if c != d["truth"]]
        if others:
            j = rng.choice(others)
            null_ranks.append(rr[j])
            null_in_arg += int(cands[j] in arg)
    return {
        "name": name, "n": n,
        "top1": top1 / max(n, 1), "in_argmax": in_arg / max(n, 1),
        "null_in_argmax": null_in_arg / max(n, 1),
        "rank": sum(ranks) / max(len(ranks), 1),
        "null_rank": sum(null_ranks) / max(len(null_ranks), 1),
        "mean_argmax": sum(arg_sizes) / max(len(arg_sizes), 1),
    }


def two_stage(rows):
    kb = max(r["k"] for r in rows)
    vals = [r["e"] if r["k"] >= kb - 1e-12 else float("-inf") for r in rows]
    return vals


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=25)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = build("linear-b")
    draws = collect(c, args.trials, args.hidden)
    c.close()
    n_all = len(draws)
    ident = [d for d in draws if d["truth"] in [r["cand"] for r in d["rows"]]]
    p_ident = len(ident) / n_all
    chance_all = sum(1.0 / max(len(d["rows"]), 1) for d in draws) / n_all
    print(f"draws {n_all};  truth in the candidate list on {len(ident)} "
          f"({p_ident:.1%});  uniform chance over all draws {chance_all:.4f}")

    rng = random.Random(7)
    # Every channel is row-wise except two-stage, which needs the whole draw.
    funcs = {name: (lambda rows, _agg=agg: [_agg(r) for r in rows])
             for name, agg in AGGS.items()}
    funcs["TWO-STAGE kober filter -> entropy argmax"] = two_stage
    print(f"\n{'channel':44s} {'top1':>6s} {'in_arg':>7s} {'null':>6s} {'rank':>6s} "
          f"{'nullrank':>8s}")
    best = None
    for name, fn in funcs.items():
        r = measure(ident, name, fn, rng)
        print(f"{name:44s} {r['top1']:6.1%} {r['in_argmax']:7.1%} "
              f"{r['null_in_argmax']:6.1%} {r['rank']:6.3f} {r['null_rank']:8.3f}")
        if best is None or r["top1"] > best["top1"]:
            best = r

    print(f"\nbest conditional top-1: {best['name']} at {best['top1']:.1%} "
          f"(n={best['n']} identifiable draws)")
    end_to_end = p_ident * best["top1"]
    lift = end_to_end / chance_all
    print(f"end-to-end recovery if the oracle used it: {p_ident:.3f} x {best['top1']:.3f} "
          f"= {end_to_end:.1%}  vs uniform chance {chance_all:.1%}  = {lift:.2f}x "
          f"-> {verdict_for(lift)}")
    print("\n  This is an ORACLE-CONTEXT upper bound, not achievable: collect() scores each "
          "candidate\n  with every other hidden sign set to its true value. oracle_diagnose "
          "part D - the same\n  objective under greedy/coordinate search from unknown values "
          "- recovers 1/80.")


if __name__ == "__main__":
    main()
