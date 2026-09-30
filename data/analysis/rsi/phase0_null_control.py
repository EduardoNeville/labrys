"""Phase 0.3 — the §6.4 determination, with the null control §2 of the protocol requires.

PLAN.md §6.4 asks whether the kober channel "ranks truth first but ties it" (→ there is
live signal and the failure is tie-breaking, so op5 is worth building) or whether every
channel is at chance (→ the tree is all-flat, V ≤ 0, op5 is not created).

`in_argmax` alone cannot answer that: a coarse score makes a large argmax set, and a large
set swallows the truth at a rate proportional to its size. So each channel is measured
against a permutation control — the same draws, the truth replaced by a candidate drawn at
random from the same candidate list. A channel with signal must beat that control.

Reuses the existing cache machinery (`collect`) and the shipped aggregators (`AGGS`).

    uv run python data/analysis/rsi/phase0_null_control.py --trials 25
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.aggregator_bakeoff import AGGS, _ranks, collect  # noqa: E402
from pipeline.oracle_diagnose import build  # noqa: E402

N_PERM = 200


def by_score(agg):
    """An aggregator becomes an argmax oracle, plus the values its rank is computed from."""
    def f(rows):
        vals = [agg(r) for r in rows]
        best = max(vals)
        return vals, [r["cand"] for r, v in zip(rows, vals) if v == best]
    return f


def two_stage(rows):
    """The op5 hypothesis: kober decides the argmax set, entropy breaks the tie."""
    kb = max(r["k"] for r in rows)
    vals = [r["e"] if r["k"] >= kb - 1e-12 else float("-inf") for r in rows]
    top = max(vals)
    return vals, [r["cand"] for r, v in zip(rows, vals) if v == top]


def measure(draws, name, fn, rng) -> dict:
    n = len(draws)
    top1 = in_arg = 0
    amax = 0.0
    ranks: list[float] = []
    null = 0
    for d in draws:
        rows = d["rows"]
        vals, arg = fn(rows)
        amax += len(arg)
        if d["truth"] in arg:
            in_arg += 1
            if len(arg) == 1:
                top1 += 1
        rr = _ranks(vals)
        tix = [i for i, r in enumerate(rows) if r["cand"] == d["truth"]]
        if tix:
            ranks.append(rr[tix[0]])
        # permutation control: truth replaced by a random candidate from this draw
        for _ in range(N_PERM // 10):
            fake = rng.choice(rows)["cand"]
            if fake in arg:
                null += 1
    null_n = n * (N_PERM // 10)
    return {
        "name": name, "n": n,
        "top1": top1 / n, "in_argmax": in_arg / n,
        "null_in_argmax": null / max(null_n, 1),
        "mean_argmax": amax / n,
        "rank": sum(ranks) / max(len(ranks), 1),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=25)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = build("linear-b")
    print(f"anchors={len(c.confirmed)}  inscriptions={len(c.inscriptions)}")
    draws = collect(c, args.trials, args.hidden)
    c.close()
    sizes = [len(d["rows"]) for d in draws]
    print(f"draws={len(draws)}  mean candidates/draw={sum(sizes)/len(sizes):.1f}")

    rng = random.Random(0)
    results = [measure(draws, name, by_score(fn), rng) for name, fn in AGGS.items()]
    results.append(measure(draws, "TWO-STAGE kober filter -> entropy argmax", two_stage, rng))

    print(f"\n{'channel':44s} {'top1':>6s} {'in_arg':>7s} {'null':>6s} "
          f"{'lift':>5s} {'|argmax|':>8s} {'rank':>6s}")
    for r in results:
        lift = r["in_argmax"] / r["null_in_argmax"] if r["null_in_argmax"] else float("inf")
        print(f"{r['name']:44s} {r['top1']:6.1%} {r['in_argmax']:7.1%} "
              f"{r['null_in_argmax']:6.1%} {lift:5.2f} {r['mean_argmax']:8.1f} "
              f"{r['rank']:6.3f}")

    best = max(results, key=lambda r: r["in_argmax"])
    print(f"\nbest in_argmax: {best['name']} {best['in_argmax']:.1%} "
          f"vs null {best['null_in_argmax']:.1%} "
          f"({best['in_argmax'] / best['null_in_argmax']:.2f}x), "
          f"top1 {best['top1']:.1%}, mean rank {best['rank']:.3f}")
    # §6.4: branch 1 needs top1 == 0 with in_argmax high AND above the permutation control.
    if all(r["top1"] == 0.0 for r in results) and best["in_argmax"] <= 2 * best["null_in_argmax"]:
        print("VERDICT: all-flat (branch 2) — no channel beats its permutation control "
              "by more than noise; op5 is not created, per PLAN.md §8.4")
    else:
        print("VERDICT: tie-collapse (branch 1) possible — inspect before retiring the tree")


if __name__ == "__main__":
    main()
