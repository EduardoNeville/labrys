# The Dream-RSI replay pool — Linear B, as built

**Date:** 2026-09-30 · **Plan:** `.pi/PLAN.md` · **Status:** Phases 0–4 complete, Phase 5 not entered.

A pre-registered, replayable record of every evidence class this project has tried on the
one Aegean syllabary where the answer is known. The point is not the numbers — it is that
the negative is *machine-checked* rather than asserted in prose, and that a policy's
frontier is a data structure instead of a list in a paper.

## What is in the pool

`tree.json` — 14 nodes, **11 replayable + 3 world-expanding**.

| branch | nodes | outcome |
| root | `op1-shipped-scorer` | 0.00×, 0 recovered, NO SIGNAL (reproduces; guard 8) |
| repair | `op1a-six-defect-repair` | still 0.00× after six repairs |
| repair | `op1b-seventh-defect-repair` | **the first repair that moves a number: 1/160, 0.23×, still NO SIGNAL** |
| independent instrument | `op2-per-sign-instrument` | exact 0.00×, series 1.03×, vowel 1.00× — lands on the majority baseline |
| stronger search | `op2a-coordinate-ascent-4inits` | 0/60 — search is not the limit |
| aggregators | `op2b-aggregator-bakeoff` | 8 aggregators, unique argmax 0.0% for all |
| control | `op2c-in-argmax-null-control` | every channel *below* its permutation null (0.25–0.52×) |
| Kober's own relation | `op3-frame-sharing` | 0.85× / 0.98× / 0.88× / 0.95×, n=71,804 |
| per-sign use of it | `op3a-link-vote-and-context-profile` | series 22.9% vs 22.5% majority = 1.02× |
| Ventris's method | `op4-slot-alternation-A`, `op4b-minimal-pair-B` | anti-predictive (0.51×), then signal/control converge (0.98×) |
| acquisitions | `x1-cm-corpus`, `x2-anetaki-ii`, `x3-bilingual-find` | no score, by construction (`is_world_expanding`) |

`retracted.json` is **not** written: the LA-side retractions (diachronic prior, Kober
triples, fraction values, AB 85) are already recorded in `verification_audit.md`, and
copying them here would create a second place for the same claim to drift. The rule PLAN
§8.2 exists to enforce — LA nodes must not be scored alongside LB nodes — is enforced by
their absence.

## Counting rule (PLAN §8.4 says "do not invent a flatter tree")

**One node = one method hypothesis, one primary metric, one measured outcome.**
Sub-measurements of one hypothesis are that node's `metrics`, not extra nodes: op3's four
frame directions are one node (the plan's own §8.3 example does this), op2b's eight
aggregators are one node. Counting them individually would clear K2 by construction, which
is precisely the game the recomputed-verdict rule exists to prevent.

**K2 status, stated both ways because the plan states it two ways.** K2 fires if the
backfill yields "< 12 replayable nodes"; §8.6's gate is "tree.json has ≥ 12 nodes". The
backfill yields **11 replayable** (`op1b`, appended after the repair, is the eleventh) and
**14 total**, so **K2 fires on its strict wording and §8.6's gate passes.** This was not
resolved by adding nodes. The reviewer who disagrees with the counting rule above can recount
from the table.

**`op1b` post-dates `split.json`.** It is a repair node on the dev spine, so it is not in the
pre-registered split and the replay does not traverse it. Adding it to dev would not have
touched the holdout, but it would be a post-hoc edit of a frozen pre-registration — and because
a repair node's `s_v` is 0 it would change no policy's `V` anyway. Recorded, not smuggled in.
The append itself (the tree is append-only; this is the one node not written by `backfill.py`):

```bash
uv run python -c "import sys; sys.path.insert(0,'.'); from pipeline.rsi_tree import append; \
  append({'id':'op1b-seventh-defect-repair','parent':'op1a-six-defect-repair', ...})"
```

## Definitions the plan left open, fixed here in one place

- **`s_v` (the quality term).** PLAN §10.1 reads `tree["values"][v]`; the field appears
  nowhere else. Defined as `max(0, primary_lift - 1)` — the node's excess over its *own*
  baseline (`rsi_tree.value_of`). Raw lift would let `op2c`, a node measured at 0.52× its
  own null, contribute +0.52 of value and outrank a real result, and it would make "flat"
  mean `lift <= 0`, which no node is. Excess-over-baseline makes every flat node
  contribute exactly 0, as §6.3's degeneracy analysis assumes.
- **"flat"** = `value_of == 0`. The gate's `verdict` is a threshold call on the same
  number, and the two agree whenever the gate says NO SIGNAL.
- **"untried"** = a frontier node with no observed child — the plan's "untried node in a
  live class" as against "deepening an exhausted one".
- **Acquisitions are ordinary tree nodes.** A policy selects a *parent* and the parent
  reveals its next child in file order (§10.1), so a node that is selectable while
  unobserved would break the replay.

## The reference number, and the two splits

`split.json` is pre-registered and subtree-aware: dev = the spine (6 nodes), holdout =
op3/op3a, op4/op4b, x1, x2, x3.

| policy | dev V | holdout V |
| **π₀ (`return []`)** | **0.000** | **0.000** |
| control (closure paper §8, transcribed) | −4.500 | −3.694 |
| clairvoyant (post-hoc upper bound) | −4.500 | −3.694 |
| acquire | 0.000 | 0.000 |

**π₀ is optimal on both splits, at β₁ ∈ {0.5, 1.0, 2.0}** — the ranking does not flip, so
the negative is not an artifact of the cost calibration (§10.4). The tree's quality term
reaches 0.02 in total (`op3a`'s excess over its majority baseline), which is §6.3's
degeneracy reached by machinery rather than by exhaustion. K3 is decided: no candidate
beats the pre-registered reference, so there is nothing for a Phase 5 policy to win.

**Phase 5 entry condition (§11): not met.** A different traversal does not reach the same
max `s_v` with fewer `N` — `clairvoyant` and `control` both reach 0.02 with N=4 on the
holdout, and both lose to stopping. Phase 5 is not built.

## Two structural limits found while building this

1. **Branch choice is not expressible in this replay.** A policy selects parents; each
   parent reveals its next child in file order. So "go to op3 rather than op1a" cannot be
   said. The policy's real decisions are pace (batch size), stopping, and — because
   `x1`/`x2`/`x3` are children of `op1` — whether to keep widening until an acquisition is
   reached. PLAN §9.3's test ("does the policy ever choose to stop searching and go get
   data?") is therefore weaker than intended: the acquisition is reached by continuing,
   not by preferring. Fixing it needs an action space over *children*, which is a change
   to §10.1's replay, not to the policy.
2. **The committed oracle scored 2 distinct hidden sets, not 8** — and the repair moved the
   result. `score_completion` reseeded the global RNG mid-loop; fixed with a private RNG. The
   scoring path is bit-identical (3,311 component tuples) but the oracle now reports **1/160,
   lift 0.23×, still NO SIGNAL**: the single hit is `AB 01`, hidden in 1 of 8 trials, via a tie
   resolved by candidate-list order. Full mechanism, numbers and the cache-key consequence in
   `phase0.md` (D1, D2, D3).

## Files

| file | what |
| `phase0.md` | the three numbers, the §6.4 determination (all-flat, branch 2), the two defects |
| `phase0_null_control.py` | the permutation control that retires PLAN §6.4's tie-collapse hypothesis |
| `backfill.py` | the nodes, written through `rsi_tree.append` so verdicts are gate-recomputed |
| `tree.json`, `split.json` | the pool and the pre-registered split |
| `cache/` | gitignored component cache, keyed on canonical content (not mtime) |
