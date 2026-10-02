# Running the Dream-RSI loop continuously

**Date:** 2026-10-01 · **Companions:** `RSI_LOOP` implementation (`pipeline/rsi_loop.py`), the pool and
policy (`data/analysis/rsi/`), `.pi/PLAN.md` (the phases that built it),
`POSITIVES_AUDIT.md` (the rules a running loop must obey).

---

## 1. What is already built

| piece | where | state |
| recorded discovery tree (18 nodes, 15 replayable, verdicts gate-recomputed) | `data/analysis/rsi/tree.json` | built, guarded |
| replay simulator + policies + pre-registered split | `pipeline/rsi_replay.py`, `rsi_policy.py`, `split.json` | built; π₀ optimal on both splits at β₁ ∈ {0.5, 1, 2} |
| the scorer seam and the component cache | `pipeline/rsi_evaluate.py` | built; cache keyed on canonical content |
| 14 guards, each a regression test for a defect that happened | `pipeline/guards.py` | 14/14 |
| the inner work queue (this document's subject) | `pipeline/rsi_loop.py` | built, drained once |
| provenance-gated acquisition inbox | `rsi_loop.acquisition_inbox` + `PROVENANCE.json` files | built |

## 2. The honest problem with "running all the time"

The loop from `.pi/PLAN.md` §10 asks *which method next?* and its answer for this corpus is measured,
not asserted: π₀ (`return []`) is optimal on both splits at every β tried, nothing beats it, and the
whole 4-channel weight simplex is empty — **0 of 1,771 vectors recovers a single value**, and 0 again
when the answer is guaranteed to be in the candidate list. A system that optimizes method choice over
this corpus will emit a rigorously negative 0.00× forever.

That is precisely the failure mode PLAN §15 pre-registered as the thing to avoid:

> the failure mode is not a bad policy — it is a well-controlled, rigorously negative loop that
> produces 0.00× for a year because it was pointed at the one resource that was never scarce.

So "run it continuously" cannot mean "keep searching". It has to mean **keep the record true and the
acquisition path ready**, and hand anything that can raise the ceiling to the two tiers that can
actually do it.

## 3. Three tiers, and what each can do

```
inner   (deterministic, seconds–minutes, no model)   : verify recorded numbers, measure per archive
outer   (an agent that writes code, hours)           : new channels, new candidate generators, tests
world   (data acquisition, unbounded)                : a real CM corpus, the Anetaki edition, a bilingual
```

**Inner** — `pipeline/rsi_loop.py`. It executes two kinds of action:

- **`verify`** — re-derive a recorded number from the corpus and flag it if it moved. This is what
  found the D1 (per-process triple permutation) and D2 (a reseeded global RNG silently turned "8
  trials" into 2 distinct draws) defects — by hand, once each. It should happen on a schedule.
- **`diagnose`** — measure a question the tree records only in pooled form, per archive (the archive
  rule from `POSITIVES_AUDIT.md` §2 mode 3 now applies to everything).

First run, for the record:

```
[ok]      verify:guards             14/14 guards passed
[ok]      verify:shipped-node       lift 0.00x, 0 recovered, NO SIGNAL; matches the recorded node
[ok]      verify:libation-counts    counts [9, 6, 7, 11]; opening at index 0 in 11/11; slot order 7/7
[ok]      verify:commodity-pairs    document-level p reproduces; cross-site replication still 2 of 67
[ok]      diagnose:membership       KN 46.9% / PY 46.9% / TH 53.8% of draws keep the truth in the
                                    candidate list — D4 is an instrument property, not an archive one
```

**Outer** — the menu the inner loop emits (`--plan`), because these need code and cannot be faked:

| action | cost | why it is worth it |
| `code:cm-acceptance-test` | ~1 h | the only path with a ceiling. Pre-register the gate, null, stratification and falsification criterion *before* the corpus exists |
| `code:d4-candidate-generator` | ~2 h | the candidate generator voids ~47% of draws in every archive. Must be a **new method** behind the frozen evaluator (INVARIANT 1), never an edit to it |
| `code:new-channel` | ~3 h | any channel outside the four cached components. A proposal must say why it can be *converted* where the class channel (op2d, 4.00× its majority baseline) could not (op2e: 0.18× within a class handed over for free) |
| `diagnose:recall-by-archive` | ~7 min | registered as `code`, not as coverage: its executor was a stub returning `ok: True`, which the overseer caught in its first report — a stub that reports success is exactly the fake progress this document refuses |

The outer loop is an agent session, and its shape is Dream-RSI's: the improver is **fixed**
(INVARIANT 2 — same model, same prompt, same temperature), it may not touch the evaluator, and every
proposal must be pre-registered, nulled in the same run, and stratified before it can become a node.

### Tier 1 — the overseer (`tools/rsi_overseer.sh`)

A cheap model reviews what the deterministic tiers recorded and reports anomalies. Pinned by
invocation (`--model`, `--thinking`, `--no-session`), so its judgement cannot drift between days;
today's pin is `space-bunny-free` at `max` thinking, both overridable by env var.

Two properties make it safe to schedule:

- **It is treated as untrusted, and the guarantee is deterministic.** The frozen set is hashed before
  and after every run; any modification is reverted, recorded in the report as a violation, and the
  driver exits 2. Files touched outside the frozen set are diffed against the pre-run `git status`, so
  pre-existing untracked files are not blamed on the model. (pi offers no per-path read-only flag;
  isolation is via containerization, so the check is enforced here rather than requested in a prompt.)
- **It cannot write its own artifact.** The driver pipes a precomputed digest (loop status, guard
  output, tree table, log tail) plus a versioned prompt (`tools/rsi_overseer_prompt.md`) into
  `pi --print`, and writes the report itself. The agent never needs write access to produce anything.

**Its first two runs earned the tier.** Eight real defects, several of them in code written the same
day:

| # | found | disposition |
| 1 | `x_recall` was registered as executable while its executor returned `ok: True` for a measurement that never happened — a fake green tick, and the terminal line would have claimed a drained queue on its strength | action regraded to `code`; the stub now refuses |
| 2 | the libation verifier used 4 of the 5 formula patterns, so it reported slot order **7/7** while every document says **9/9**, and compared only against its own denominator | 5 patterns; now **9/9**, matching the docs |
| 3 | the matcher tested contiguity over a sequence with 45.9% of sign rows removed, so a match could span a lacuna and merge two fragments into a "word" | both counts now reported; **every match is contiguous** — the concern is permanently answered rather than assumed |
| 4 | `x_membership` hardcoded `changed: False`, so the figure the D4 cost estimate rests on could have halved and the loop would have logged healthy | compares against the last recorded values, flags >0.02 |
| 5 | the three archives' membership is measured on the **same hidden sets** (paired), and was reported as if independent | `values` recorded machine-readably; the pairing is stated in the record |
| 6 | `verify:header-counts` greped for claimed strings, so a doc claiming 1,719,000 would have passed and the disclaimed "312" kept reporting OK | parses the doc's numbers and compares numerically |
| 7 | AGENTS.md's "312 unique Bennett IDs" is unreproducible: the DB holds **205** non-empty (206 including the empty row), and the union across grid files is **269**. Nothing checked any header number | number corrected with the discrepancy recorded; action added |
| 8 | SQLite's WAL sidecars created by the driver's own digest queries were reported as agent violations | gitignored and exempted from the diff |

It also refused to declare the terminal state above, on the grounds that a three-way value concordance
over the grid is uncovered (its second report: `la_lb_mapping.lb_value` and
`refined_phonetic_grid.refined_value` disagree on AB 34 and AB 79 while the guard built to catch that
prints "conflicts (0)"). That refusal is the tier working: the stop rule has to hold from both sides.

**World** — the inbox. This is the only tier that can change the verdict, and it is currently empty:

```
x1-cm-corpus:     present but SYNTHETIC — circular for the test it would be used for
x2-anetaki-ii:    absent
```

## 4. The trust boundary that makes the inbox safe

The inbox's first version returned *"x1-cm-corpus is ready"* because `languages/cypro-minoan/data/raw/`
had files in it. Those files are a **synthetic placeholder generated from the very LA→CM signs a
transfer test would try to confirm**, plus random fill. A test on them would have been circular in the
most direct way possible — and it would have looked like progress, because the loop would have grown a
node.

So an input now counts as evidence only if a `PROVENANCE.json` declares `synthetic: false`. Undeclared
input is refused, and the refusal is printed. "An artifact exists" is not "the evidence exists" — the
distinction this project has had to make thirteen times, and the one a continuously-running loop is
most likely to get wrong *because it is the thing that keeps the loop busy*.

## 5. What counts as "a result"

"Run until we achieve some result" needs the result defined in advance, or the loop will define
success as its own activity. Four terminal states, in order of value:

- **S1 — a value.** A phonetic value for a Linear A sign accepted by the project's gates, with an
  independent control. Requires evidence from outside the corpus, or a channel that converts where
  op2d could not.
- **S2 — an anchor.** An association that replicates both on held-out data *and* across archives, with
  a positive control that passes. (The commodity associations reached a 20,000-rep stratified
  permutation at the floor and then failed cross-site — that is what S2 requires and why.)
- **S3 — a repair that moves a number.** D2 moved the Linear B oracle from 0.00× to 0.23× and stayed
  below chance; a repair is a result whether or not it helps, as long as it is attributed.
- **S4 — an acquisition completed.** A real corpus or text ingested, with its acceptance test run the
  day it lands.

The inner loop can produce S3; the outer loop can produce S3 and prepare S1/S2/S4; only the world can
produce S1/S2/S4. **The honest terminal state is "inner queue drained, outer menu enumerated, inbox
empty" — and the loop should say so rather than keep spinning.** That state has already been reached
once; it is printed by `--status`.

## 6. Running it

```bash
uv run python pipeline/rsi_loop.py --plan                       # what would run, and why
uv run python pipeline/rsi_loop.py --run 9                      # execute everything that is due
uv run python pipeline/rsi_loop.py --run 9 --force              # re-check (scheduled drift detection)
uv run python pipeline/rsi_loop.py --run 9 --force --include-expensive
uv run python pipeline/rsi_loop.py --status                     # coverage, inbox, terminal state
uv run python pipeline/rsi_loop.py --cron                       # print the crontab lines, paths resolved
```

`--cron` prints exactly what to paste, with `$HOME` and this checkout's path already resolved — so
the commands below are written down once, in the code that knows the paths, rather than in a snippet
that rots:

```cron
SHELL=/bin/sh
PATH=/home/<user>/.bun/bin:/home/<user>/.local/bin:/usr/local/bin:/usr/bin:/bin
0 3 * * *  <repo>/tools/rsi_loop.sh due      >> <repo>/data/analysis/rsi/loop_cron.log 2>&1
30 4 * * * <repo>/tools/rsi_overseer.sh      >> <repo>/data/analysis/rsi/loop_cron.log 2>&1
0 4 * * 0  <repo>/tools/rsi_loop.sh full     >> <repo>/data/analysis/rsi/loop_cron.log 2>&1
```

`--cron` prints this with the paths resolved for whatever machine it runs on. Three schedules: tier 0
nightly (re-derive every recorded number), tier 1 daily (the overseer's review), and the weekly run
that adds the expensive stratified checks. Exit 1 from tier 0 or exit 2 from tier 1 means investigate;
a silent log is a healthy one.

`tools/rsi_loop.sh` sets `PATH` (uv lives in `~/.local/bin`, pi in `~/.bun/bin` and runs under node),
cds to the checkout, timestamps each run, bounds the log to ~1 MB, and exits **1 when any verify
action flagged drift**. Run the pair once by hand before trusting the schedule:

```bash
tools/rsi_loop.sh due && tools/rsi_overseer.sh && tail -40 data/analysis/rsi/loop_cron.log
```

State is durable and committed: `data/analysis/rsi/loop_state.json` (last run per action, ok/changed)
and `loop_log.jsonl` (append-only history). `--run` skips actions that are not *due* — never run, last
run flagged, or `--force` — so an unscheduled invocation always moves on to unmeasured work instead of
re-checking the same things.

Two properties make this safe to leave running: the inner loop is **LLM-free** (no per-iteration cost,
and no chance of a model drift changing what "verified" means), and it **cannot write to the
evaluator** — it may only add nodes to an append-only tree whose verdicts are recomputed from the gate.

## 7. What the loop is *not* allowed to do

Codified as refusals, because each is a way a running system accumulates fake progress:

1. **Re-measure a covered space.** The weight simplex is exhausted (0 of 1,771); proposing another
   weighting is activity, not information. Dedup is by action-space coverage, not by node identity.
2. **Reward its own activity.** The tree's value function charges β₁ per node and exempts only
   world-expanding actions. Nothing in the loop optimizes the count of nodes.
3. **Treat an undeclared artifact as evidence.** §4.
4. **Edit the evaluator.** INVARIANT 1: the grid, `answer_key.csv`, the triples, the frequency
   constraints, `GATE_THRESHOLD`. A new method goes *behind* the frozen evaluator as a new node.
5. **Let the self-improving agent improve itself.** INVARIANT 2: fixed model, prompt and temperature
   across versions; improvement comes from the feedback signal, never from the improver changing.
6. **Publish a positive that has not been stratified *and* replicated.** Both, with a positive control
   that must pass (`POSITIVES_AUDIT.md` §4 rules 6–7).

## 8. The projection, stated plainly

The inner queue drains in about four minutes of CPU (measured: 6 s of verifies + 173 s of diagnostics;
the expensive recall check adds ~7 min per archive). After that the loop's continuing value is
**drift detection** — the D1/D2 class of defect recurs, and nothing else in this repository would
catch a recorded number quietly changing — plus **readiness**: the acceptance test and the ingestion
path for the day real data lands.

What it will not do is decipher Linear A. The measured reasons, in order: distributional methods are
closed by exhaustive search; the only channel that ever carried controlled signal is not convertible
by the scorer; the candidate generator voids half the draws before scoring begins; and the project's
positives dissolve on replication while its negatives survive it. **The loop's job is to keep that
statement true, to notice the moment it stops being true, and to have the machinery ready for what
does.** Pointing a self-improving loop at this corpus and waiting is the one experiment this project
has already run — and the answer was recorded before the loop was built.

---

## Appendix — the loop's own defect log

Written while building it, because a verifier that has never flagged anything is untested. Items 1–5
were found by running the inner loop; items 6+ by the overseer (tier 1), which is the point of having
one.

1. **The inbox said "ready" for a synthetic corpus** (§4). Found by reading the README of the corpus
   the inbox had just declared available. This is the loop's most important failure and the reason
   provenance is a gate.
2. **A false drift flag.** `verify:libation-counts` reported slot order 2/7 because the check compared
   against its own dict insertion order instead of the documented slot order (opening → name-anchor →
   request → favour → divine). The corpus was fine; the reference was wrong — the same class of error
   as comparing against a stale baseline, one level down.
3. **A check greping the wrong script.** `verify:commodity-pairs` looked for the cross-site replication
   line in `enrichment_audit.py`'s output; it lives in `cross_site_replication.py`'s.
4. **A diagnostic with `kober_triples_path=None`.** Membership is Kober-constrained, so it cannot be
   measured without the stratum's graph. It raised a TypeError — which is the *good* failure: a silent
   fallback to the pooled graph would have produced a plausible, wrong number.
5. **A loop that spun.** `--run 1` re-ran the guards instead of the never-measured diagnostic, because
   "due" had not been defined. Fixed: skip unless never run, flagged, or `--force`.

Five defects, five caught in about ten minutes of running. That ratio is the argument for the
`verify` action existing at all — and against trusting any of these numbers without re-deriving them.
