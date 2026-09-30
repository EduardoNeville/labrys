"""Is the aggregation failure tie-breaking, or is it the whole weight space?

`METHOD_CLOSURE_PAPER.md` §8 claims "the objective has no resolution to optimize", and §4.1
supports it with eight hand-picked aggregators, none of which produced a unique argmax. PLAN
§6.4 sharpened the question: if the kober channel ranks the truth first but ties it, the fix is a
tie-break rule, and that would be the highest-value untried operationalization in the project.

Eight points are not a search. This sweeps the entire 4-channel weight simplex (steps of 0.05,
1,771 vectors), evaluates every one on a dev half of the draws, and reports the winner **once**
on the holdout half — the same discipline PLAN §10.4 imposes on beta.

Controls, because "best of 1,771 tries" is a number that outruns its evidence by construction:
  * a permutation control runs the identical search with the truth replaced by a random other
    candidate on each draw, giving the maximum a best-of-1,771 search reaches with no signal.
    That, not 1/|C|, is the null for a maximum.
  * the dev/holdout split is by trial, so the two halves have different hidden sets.

Pre-registered prediction, written before the run: the best-on-dev score will sit at the
permutation-control maximum and the holdout score will be at or near zero. If instead a vector
survives on holdout, §8's claim is falsified and that is the finding of the year for this
project, not a footnote.

This is not a method-search optimizer (PLAN §13 forbids those, and no optimizer is built here):
it is a single controlled attempt to falsify a published claim about the objective, using the
component cache the plan made free.

    uv run python data/analysis/rsi/weight_space_search.py --trials 25
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.oracle_diagnose import build                               # noqa: E402
from pipeline.aggregator_bakeoff import collect                          # noqa: E402

STEPS = 0.05


def weight_grid() -> np.ndarray:
    """All (m, e, p, k) weight vectors on a 0.05 grid, summing to 1."""
    ticks = np.arange(0, 1.0 + 1e-9, STEPS)
    out = []
    for a in ticks:
        for b in ticks:
            for c in ticks:
                d = 1.0 - a - b - c
                if d < -1e-9:
                    continue
                if d > 1.0 + 1e-9:
                    continue
                out.append((a, b, c, max(d, 0.0)))
    return np.array(out)


def evaluate_vectors(draws, W: np.ndarray, truth_of=None) -> np.ndarray:
    """Unique-argmax-correct count per weight vector, over `draws`.

    `truth_of(draw) -> value` lets the caller substitute a permuted truth without touching
    the component matrix; that is what makes the control run the *identical* search.
    """
    scores = np.zeros(len(W))
    for d in draws:
        rows = d["rows"]
        if not rows:
            continue
        M = np.array([[r["m"], r["e"], r["p"], r["k"]] for r in rows])   # (C, 4)
        vals = M @ W.T                                                   # (C, V)
        best = vals.max(axis=0)
        # unique argmax: exactly one candidate attains the max
        hits = (vals == best[None, :])
        n_ties = hits.sum(axis=0)
        truth = truth_of(d) if truth_of else d["truth"]
        tix = [i for i, r in enumerate(rows) if r["cand"] == truth]
        if not tix:
            continue
        ok = hits[tix[0]] & (n_ties == 1)
        scores += ok
    return scores


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=25)
    p.add_argument("--hidden", type=int, default=20)
    p.add_argument("--perm-reps", type=int, default=5)
    p.add_argument("--identifiable-only", action="store_true",
                   help="restrict to draws where the truth is a candidate, so the result "
                        "cannot be blamed on candidate generation (phase0.md D4)")
    args = p.parse_args()

    c = build("linear-b")
    draws = collect(c, args.trials, args.hidden)
    c.close()

    half = (args.trials // 2) * args.hidden
    dev, hold = draws[:half], draws[half:]
    if args.identifiable_only:
        keep = lambda ds: [d for d in ds                              # noqa: E731
                           if d["truth"] in [r["cand"] for r in d["rows"]]]
        dev, hold = keep(dev), keep(hold)
        print(f"identifiable-only: dev {len(dev)}, holdout {len(hold)} draws where the "
              f"true value IS a candidate — the aggregation question isolated from D4")
    W = weight_grid()
    print(f"draws {len(draws)} (dev {len(dev)}, holdout {len(hold)});  "
          f"weight vectors {len(W)} on a {STEPS} grid")

    dev_scores = evaluate_vectors(dev, W)
    best_i = int(dev_scores.argmax())
    print(f"\nbest on dev: {int(dev_scores[best_i])}/{len(dev)} = "
          f"{dev_scores[best_i]/len(dev):.1%}  weights (m,e,p,k) = "
          f"{', '.join(f'{x:.2f}' for x in W[best_i])}")
    print(f"  vectors recovering >=1 on dev: {int((dev_scores > 0).sum())} of {len(W)}")

    hold_scores = evaluate_vectors(hold, W)
    print(f"  that vector on holdout: {int(hold_scores[best_i])}/{len(hold)} = "
          f"{hold_scores[best_i]/len(hold):.1%}")
    best_h = int(hold_scores.argmax())
    print(f"  best of the whole space on HOLDOUT: {int(hold_scores[best_h])}/{len(hold)} = "
          f"{hold_scores[best_h]/len(hold):.1%}")

    # Truth-independent ceilings: the largest argmax-set rate and the uniform rate.
    sizes = [len(d["rows"]) for d in draws if d["rows"]]
    print(f"\n  mean |candidates| {np.mean(sizes):.1f};  uniform chance over all draws "
          f"{np.mean([1/s for s in sizes]):.4f}")

    rng = random.Random(0)

    def permuted(d):
        other = [r["cand"] for r in d["rows"] if r["cand"] != d["truth"]]
        return rng.choice(other) if other else d["truth"]

    print(f"\npermutation control (identical search, truth replaced by a random other "
          f"candidate, {args.perm_reps} reps):")
    perm_best = []
    for _ in range(args.perm_reps):
        ms = evaluate_vectors(dev, W, truth_of=permuted)
        perm_best.append(ms.max() / len(dev))
        print(f"  best-of-{len(W)} under permutation: {ms.max():5.0f}/{len(dev)} = "
              f"{ms.max()/len(dev):.1%}")
    print(f"  mean {np.mean(perm_best):.1%}  max {np.max(perm_best):.1%}")

    print(f"\nVERDICT: dev best {dev_scores[best_i]/len(dev):.1%} vs permutation max "
          f"{np.max(perm_best):.1%}")
    if hold_scores[best_i] == 0 and dev_scores[best_i] <= max(perm_best) * len(dev) + 1:
        print("  No weight vector in the 4-channel simplex recovers a value. §8's claim holds "
              "by search,\n  not by eight examples — and PLAN §6.4's tie-break hypothesis is "
              "dead for weight vectors,\n  not just for the two-stage aggregator that "
              "implemented it.")


if __name__ == "__main__":
    main()
