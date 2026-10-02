# The Dream-RSI replay pool — Linear B, as built

**Date:** 2026-09-30 · **Plan:** `.pi/PLAN.md` · **Status:** Phases 0–4 complete, Phase 5 not entered.

A pre-registered, replayable record of every evidence class this project has tried on the
one Aegean syllabary where the answer is known. The point is not the numbers — it is that
the negative is *machine-checked* rather than asserted in prose, and that a policy's
frontier is a data structure instead of a list in a paper.

## What is in the pool

`tree.json` — 18 nodes, **15 replayable + 3 world-expanding**.

| branch | nodes | outcome |
| root | `op1-shipped-scorer` | 0.00×, 0 recovered, NO SIGNAL (reproduces; guard 8) |
| repair | `op1a-six-defect-repair` | still 0.00× after six repairs |
| repair | `op1b-seventh-defect-repair` | **the first repair that moves a number: 1/160, 0.23×, still NO SIGNAL** |
| independent instrument | `op2-per-sign-instrument` | exact 0.00×, series 1.03×, vowel 1.00× — lands on the majority baseline |
| the retrace's open item 1 | `op2d-context-profile-class` | series **1.21×** majority (2.01× permutation) — INCONCLUSIVE; exact value **void by construction** |
| ceiling for it | `op2e-class-restriction-ceiling` | given the true class **for free**, the scorer is **0.18× chance** within it — worse than random |
| corrected denominator | `op2f-identifiable-subset` | conditional on the truth being knowable: unique argmax **0.0%** for all nine channels, `in_argmax` = its mechanical tie rate exactly |
| stronger search | `op2a-coordinate-ascent-4inits` | 0/60 — search is not the limit |
| aggregators | `op2b-aggregator-bakeoff` | 8 aggregators, unique argmax 0.0% for all |
| control | `op2c-in-argmax-null-control` | every channel *below* its permutation null (0.25–0.52×) |
| the exhaustive version | `op2g-weight-space-search` | **0 of 1,771 weight vectors recover one value** — and 0 of 1,771 with the answer guaranteed present |
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

**K2 status.** K2 fires if the backfill yields "< 12 replayable nodes"; §8.6's gate is "tree.json
has ≥ 12 nodes". The pool now has **15 replayable** and **18 total**, so **K2 fires under neither
reading** — and the margin came from discovery continuing (`op2d`–`op2g`), not from
padding: each is one hypothesis with one primary metric and a recorded outcome, and the counting
rule is stated above so a reviewer can disagree and recount. Earlier in the build it stood at 10
replayable, when K2 fired on its strict wording; both counts were reported at the time rather than
reconciled in either direction.

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

`split.json` is pre-registered and subtree-aware: dev = the spine (7 nodes), holdout =
op3/op3a, op4/op4b, x1, x2, x3 (7 nodes). One amendment, dated and recorded in the file:
a node discovered after the split joins **dev** if its parent is in dev; the holdout never
grows, because a class the policy has not seen stays unseen.

| policy | dev V | holdout V |
| **π₀ (`return []`)** | **0.000** | **0.000** |
| control (closure paper §8, transcribed) | −6.290 | −3.694 |
| clairvoyant (post-hoc upper bound) | −6.290 | −3.694 |
| acquire | 0.000 | 0.000 |

**π₀ is optimal on both splits, at β₁ ∈ {0.5, 1.0, 2.0}** — the ranking does not flip, so
the negative is not an artifact of the cost calibration (§10.4). K3 is decided: nothing beats
the pre-registered reference, so there is nothing for a Phase 5 policy to win.

### The one live node, what it would cost to be worth reaching, and why it is not convertible

`op2d` is the only node in the tree with a quality term worth much, `s_v = 0.21`. Reaching
it costs five reveals (its parent chain, and a node's children are revealed in file order),
so a policy that acted would score `0.21 − 5β₁ + 0.5` and beat π₀ only if
**β₁ < 0.142 h/node** — under ~8.5 minutes per method class. At the plan's β₁ = 1.0, the
tree's best available information is **7× too expensive** to be worth reaching. That is
PLAN §4's "the cost term is load-bearing" made quantitative: re-weighting existing channels
is free and would pay; computing a new channel does not.

And even at β₁ = 0 it would not pay, which `op2e` establishes as a **ceiling rather than a
sample-size question**. Handing that channel the true class *for free* — an oracle
restriction, generous in the only direction that matters — leaves the shipped scorer at
**8.5% within-class accuracy against a 47.4% chance rate (0.18×), i.e. worse than random**
among 2.32 class peers. Tie-lenient, the truth is in the argmax set 35.2% of the time (0.74×).
So no improvement to the class channel, not even a perfect one, can yield values with this
scorer: the binding constraint is the objective, not the channel and not the corpus.

### The measurement that produced it

`frame_link_test.py` now carries a same-draw permutation null for the context-profile channel
that the 35.7% figure never had (and its own RNG stream, so adding the control cannot perturb
the draw sequence it controls). At n=500 draws: series **30.8%** vs a 25.4% majority baseline
(**1.21×**, INCONCLUSIVE) and a 15.4% permutation null (**2.01×**); exact class pick 9.6% vs
2.4% majority (4.00×) and 2.4% null (3.93×); exact value 0.0% against a 2.3% chance rate. At
73 draws the series rate read 1.52× — above the gate — while the null held at 14.7%, which is
how that was caught. Two self-inflicted errors were also caught before committing the node:
the channel was first called per hidden sign instead of per trial, overstating n by 20× (with
rates unaffected), and the first null consumed the *shared* RNG, which would have silently
changed the draw sequence it was controlling.

**Phase 5 entry condition (§11): not met.** A different traversal does not reach the same
max `s_v` with fewer `N` — `clairvoyant` and `control` both reach 0.02 with N=4 on the
holdout, and both lose to stopping. Phase 5 is not built.

## The frontier's next requirement: semantic-anchor nodes cannot be scored yet

The audit of the commodity enrichment (Phase 14 of `verification_audit.md`) produced the project's
first **controlled positives**: eight sign↔commodity associations surviving a site-stratified
permutation at the 122-test family alpha, the two originals reaching document-level p = 2.7e-11 and
2.6e-05. They are candidate **semantic anchors** — closure paper §7 class 1, and `semantic-anchor`
in PLAN §8.1's taxonomy, marked replayable.

**They cannot enter this pool as it stands, and that is a finding about the apparatus.**
`rsi_tree.verdict_for` gates on `primary_lift` — recovery over a baseline — and the declared metrics
are `exact`, `series`, `vowel`, `frame`. A permutation p on a document-level co-occurrence rate is
not a lift, so a semantic-anchor node has no legal `primary_metric` here. Forcing one in (say,
calling `observed / null_mean = 2.4×` an `exact` lift) would be the number-outrunning-its-control
move the protocol exists to prevent.

What such a node would need first:

1. a declared metric meaning "association with a meaning class", with its own pre-registered
   threshold — a permutation p at a stated family size is the honest candidate, not a ratio; and
2. a statement of what it is worth: an association narrows a sign's *context*, not its value, so
   `values_recovered` is 0 by construction and the quality term has to be defined for it.

So the `semantic-anchor` class is populated in the world and empty in the tree, and the policy's
frontier is narrower than §8.1 of the plan says. Recorded here because it is the cheapest place for
the next person to find it.

## Four structural limits found while building this

1. **The aggregation has no resolution at all, verified by search.** `op2g` sweeps the whole
   4-channel weight simplex (1,771 vectors, 0.05 grid) on a dev half of the draws and reports the
   winner once on the holdout: **zero vectors recover even one value**, and zero as well when the
   question is isolated from candidate generation by keeping only draws where the answer *is* a
   candidate. The identical search on a permuted truth finds 2.7–2.8%, so the true value is *less*
   likely to be the unique argmax than a random candidate is. `METHOD_CLOSURE_PAPER.md` §8's claim
   now holds by search rather than by eight examples, and PLAN §6.4's tie-break hypothesis is dead
   for weight vectors generally — not just for the two-stage aggregator that implemented it.

2. **Branch choice is not expressible in this replay.** A policy selects parents; each
   parent reveals its next child in file order. So "go to op3 rather than op1a" cannot be
   said. The policy's real decisions are pace (batch size), stopping, and — because
   `x1`/`x2`/`x3` are children of `op1` — whether to keep widening until an acquisition is
   reached. PLAN §9.3's test ("does the policy ever choose to stop searching and go get
   data?") is therefore weaker than intended: the acquisition is reached by continuing,
   not by preferring. Fixing it needs an action space over *children*, which is a change
   to §10.1's replay, not to the policy.
3. **The committed oracle scored 2 distinct hidden sets, not 8** — and the repair moved the
   result. `score_completion` reseeded the global RNG mid-loop; fixed with a private RNG. The
   scoring path is bit-identical (3,311 component tuples) but the oracle now reports **1/160,
   lift 0.23×, still NO SIGNAL**: the single hit is `AB 01`, hidden in 1 of 8 trials, via a tie
   resolved by candidate-list order. Full mechanism, numbers and the cache-key consequence in
   `phase0.md` (D1, D2, D3).
4. **The candidate generator removes the answer before scoring starts.** The true value is a
   candidate on 36.2–54.2% of draws, so roughly half of every recovery figure in this project
   measures a question that was already unanswerable, and the two aggregation defects sit *behind*
   this one. Also: an earlier null control of **mine** had 100% membership (it drew its "truth"
   from the candidate list), which made the channels look worse than the corrected denominator
   shows. With the denominator fixed the negative still holds — unique argmax 0.0% for all nine
   channels on identifiable draws, `in_argmax` equal to its mechanical tie rate — see
   `phase0.md`'s dated correction and tree node `op2f`.

## Files

| file | what |
| `phase0.md` | the three numbers, the §6.4 determination (all-flat, branch 2), the two defects |
| `phase0_null_control.py` | the permutation control that retires PLAN §6.4's tie-collapse hypothesis |
| `backfill.py` | the nodes, written through `rsi_tree.append` so verdicts are gate-recomputed |
| `tree.json`, `split.json` | the pool (one dated dev amendment) and the pre-registered split |
| `cache/` | gitignored component cache, keyed on canonical content (not mtime) |
