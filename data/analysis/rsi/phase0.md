# Phase 0 — the three numbers

**Date:** 2026-09-30 · **Plan:** `.pi/PLAN.md` §6 (governed by `EXPERIMENT_PROTOCOL.md`)
**Status:** Phase 0 complete. K4 does **not** fire. §6.4 determination: **all-flat (branch 2)**.

## 0.1 — K4: does the committed result reproduce?

```
uv run python pipeline/lb_oracle.py --trials 8 --hidden 20
```

| quantity | committed (`ventris_report.md`) | this run |
| recovery | 0.0000 | **0.0000** |
| chance | 0.0208 | **0.0208** |
| lift | 0.00× | **0.00×** |
| verdict | NO SIGNAL | **NO SIGNAL** |
| hidden signs scored | 160 | **160** |

`git diff languages/linear-b/data/analysis/ventris/ventris_report.md` → **empty**. The script
rewrites the report; the regenerated file is byte-identical, so the reproduction is exact.
K4 does not fire.

**Wall-clock: 198 s** (8 trials × 20 hidden, greedy restore). K1 does not fire either — one
oracle pass is ~3 min, not hours.

## 0.2 — the cost of one `collect()` pass

```
uv run python pipeline/aggregator_bakeoff.py --language linear-b --trials N
```

| trials | hidden-sign draws | wall-clock |
| 1 | 20 | 4 s |
| 3 | 60 | 12 s |
| 25 | 500 | 109 s |

One scoring pass makes every aggregator, every weight vector and every argmax search free
(PLAN §4). Confirmed: 500 draws cost under two minutes, and `PASS`/`NO SIGNAL` gate calls on
that cache are arithmetic. **The expensive action is a new channel, nothing else.** β₁ = 1.0
hour per node (PLAN §10.4) is therefore calibrated to *authoring a channel*, not to computing
one, and that is the right calibration.

## 0.3 — the §6.4 determination (the number the plan turns on)

PLAN §6.4: "These reconcile only if the kober channel ranks truth first but ties it — real
information destroyed by tie-collapse, not zero information."

`in_argmax` cannot distinguish those, because a coarse score makes a large argmax set and a
large set swallows the truth at a rate proportional to its size. So each channel was measured
against a permutation control — same draws, truth replaced by a candidate drawn at random from
the same candidate list (`phase0_null_control.py`, N_PERM per draw):

```
uv run python data/analysis/rsi/phase0_null_control.py --trials 25
```

500 draws, mean 46.1 candidates/draw:

| channel | top1 | in_argmax | null | lift | mean \|argmax\| | mean rank |
| shipped 0.45m+0.15e+0.10p+0.30k | 0.0% | 2.8% | 8.0% | **0.35×** | 4.3 | 0.406 |
| kober only | 0.0% | 4.8% | 12.2% | **0.39×** | 6.1 | 0.463 |
| entropy(bigram) only | 0.0% | 27.2% | 58.7% | **0.46×** | 27.2 | 0.492 |
| morph only | 0.0% | 35.8% | 69.4% | **0.52×** | 32.2 | 0.450 |
| prefix only | 0.0% | 28.6% | 62.7% | **0.46×** | 28.7 | 0.487 |
| kober+entropy (equal) | 0.0% | 3.6% | 10.4% | **0.34×** | 5.3 | 0.460 |
| kober+entropy+prefix (equal) | 0.0% | 2.2% | 8.7% | **0.25×** | 4.5 | 0.448 |
| all four (equal) | 0.0% | 2.2% | 7.6% | **0.29×** | 4.3 | 0.405 |
| **TWO-STAGE kober filter → entropy argmax** (op5) | 0.0% | 4.6% | 10.5% | **0.44×** | 5.4 | 0.507 |

**Determination: branch 2 — the tree is all-flat.** Not "at chance": **below** it. No channel
puts the true value in its argmax set more often than a randomly chosen candidate does
(0.25–0.52×), so the 27–36% `in_argmax` figures of the m/e/p channels are an artifact of
argmax sets covering ~59% of the candidate list, not orientation. Mean rank 0.41–0.51 (1.0 =
best) says the same: the truth sits at the median of every channel's ordering.

### Two corrections this makes to the plan's premises

1. **The `kober` channel is not the tie-collapse case.** PLAN §6.4's hypothesis rests on
   `oracle_retrace_findings.md` §(c) — "PMI puts the truth in the argmax set 100% of the time
   but always tied". That sentence is about **PMI**, an abandoned per-sign estimator from part
   (c) of that document, not about kober. The same document's §(b) already recorded the answer:
   "Across every aggregator tried — shipped weights, equal weights, Borda rank-normalisation,
   **kober-then-entropy two-stage** — the unique-argmax rate is 0.0%."
2. **op5 already exists and has already returned chance.** The plan's "only invented node" —
   kober decides the argmax, a second channel breaks the tie — is `aggregator_bakeoff.py`'s
   TWO-STAGE aggregator (and its two BORDA variants), implemented before the plan was written.
   Plumbed through this null control: **0.0% top1, 0.46% → 4.6% in_argmax, 0.44× its control.**

   The docstring of `aggregator_bakeoff.py` ("the components rank the true value top-1 at
   67% / 47% / 59% / 100%") does not reproduce on the repaired instrument: every channel is at
   0.0% top-1 here. Those figures predate the six-defect repair and the Phase-12 leak fix.

## What this decides, by the plan's own rules

| rule | consequence |
| PLAN §8.4 "If §6.4 came back 'all-flat', op5 is not created" | **op5 is not created** |
| PLAN §6.3, `max(s_v) = 0` → `V = 0 − β₁N + β₂N/max(1,k) < 0` for any acting policy | the optimum is **always stop**; `V = 0` only for the empty policy. "That is the correct answer, not a defect" |
| PLAN §13 "no information-gain bonus" | not added. The degeneracy is reported, not softened |
| PLAN §2 "explicitly NOT a kill criterion: the policy returns `[]`" | pre-registered as success, not failure |

A replay over an all-flat tree therefore has a known value function before any Phase 1–4 code
exists: no policy that acts can beat `return []`, and `K3` is decided by construction.

## What is *not* flat, and is not in the plan

The retrace's own open items name one untested evidence class that is **not** an aggregator of
the four existing channels, so Phase 0.3 does not touch it:

> **Give the estimator the hidden sign itself.** Score candidate `v` by the hidden sign's own
> observed context against the anchor signs that carry `v` — nearest-neighbour over contexts,
> not a global corpus statistic. — `oracle_retrace_findings.md`, open item 1

That is a **new channel** in PLAN §4's cost model (hours, not seconds), and it is the only
documented candidate for a node that is not flat. op5 was not it.

## Three defects found while running Phase 0 — all three repaired 2026-10-01

**D1 — `lb_oracle.py` is not idempotent, and it edits a data file (INVARIANT 1).** ~~Its step 2
regenerates `languages/linear-b/data/analysis/kober/triple_patterns.csv` non-canonically.~~
**REPAIRED.** Root cause was not the writer but the enumeration: `triple_detection.py` walked two
`set`s of sign ids, so `triple_id` *and* the positional s1/s2/s3 roles were a per-process
permutation — and `complete.py:_load_kober` reads the C/V distinction from those roles, so the
constraint graph was not reproducible in principle, only in practice. Fixed by sorting both set
iterations and canonicalising the file order.

Verified unchanged: same 60,155 triples, same 2,667 C-pairs, same 2,564 V-pairs. Verified fixed:
byte-identical across two independent runs. Guard 13 pins it. `ventris_report.md` regenerates
byte-identical as before.

**Consequence for the plan's cache key.** PLAN §7.1 step 1 keys the component cache on
`mtime(triples)` "so a future corpus correction invalidates stale caches automatically". With a
non-canonically-reserialized file, that mtime changed on **every** `lb_oracle.py` run — and
Phase 0.1 is a command the plan runs repeatedly. The cache would never hit. `rsi_evaluate.py`
keys on the *canonical content* instead (`sha1` over all 60,155 rows with the s1/s2/s3 roles
preserved). The stated intent is preserved by hashing content; the mtime does not do it. Note the
digest deliberately keeps row roles rather than sorting them: the roles are what the C/V split is
read from, so a role change must invalidate the cache, while a row reordering must not.

**D2 — the committed oracle ran 2 distinct hidden-sign sets, not 8.** ~~`score_completion`
(`pipeline/ventris/complete.py:447-448`) does `import random as _random; _random.seed(0);
_random.shuffle(...)` on the **global** RNG, in the middle of `oracle_test`'s trial loop.~~
**REPAIRED** with a private `random.Random(0)` instance: identical shuffle, no global side effect.
Reproduced before the repair:

| trial | chance | hidden set |
| 1 | 0.0374 | A |
| 2–8 | 0.0185 | B (identical in all seven) |
| mean | **0.0208** | = the committed `chance_rate`, exactly |

**The repair is behaviour-neutral for scoring.** All **3,311** (sign, candidate) component tuples
are bit-identical before and after (compared against the cache the pre-repair code produced), so
no recorded value in the tree changes for this reason. What changes is the draw sequence:

| | before | after |
| recovery | 0.0000 (0/160) | **0.0063 (1/160)** |
| chance | 0.0208 | **0.0273** |
| lift | 0.00× | **0.23×** |
| distinct hidden sets | 2 | **8** |
| verdict | NO SIGNAL | **NO SIGNAL** |

**Attributed**: the hit is `AB 01`, hidden in 1 of 8 trials and recovered there, by a **tie resolved
by candidate-list order** — the unique-argmax rate over these draws is 0.0%, and evaluated
tie-strictly the shipped config still returns 0 recovered (`rsi_evaluate`, guard 8). AB 01 is the
most frequent sign in the corpus and one of the two the original anchor-word leak produced. So the
seventh defect is the first repair that moves a number, and it moves it the way
`METHOD_CLOSURE_PAPER.md` §6 predicts: toward chance, not past it. Guard 12 fails on a
reintroduction.

**D3 — a report line overstated its own evidence.** "Signs recovered in ALL trials: AB 01" while
AB 01 was hidden in 1 of 8 trials. Repaired: `oracle_test` returns `per_sign_trials` and the report
prints `AB 01 (1/8 trials)`. The class of error is protocol §7's — a plausible number outrunning its
control.

Repairs recorded in `data/analysis/ventris/verification_audit.md` (Phase 13 Addendum) and as the
append-only tree node `op1b-seventh-defect-repair`.

## Artifacts

| file | content |
| `data/analysis/rsi/phase0_null_control.py` | §6.4 with the permutation control (this directory, not `pipeline/`: §12's file list has no Phase-0 script, and the control belongs with the record it justifies) |
| `data/analysis/rsi/phase0.md` | this file |

`pipeline/` untouched. No file under `languages/*/data/` left modified — the oracle report
regenerates byte-identical, and the Kober CSV was restored as noted above.
