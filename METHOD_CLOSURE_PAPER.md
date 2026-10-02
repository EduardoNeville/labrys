# No phonetic values are recoverable by frame or paradigm analysis: a controlled test of the Kober–Ventris method on a deciphered sister script

**Draft for review — not submitted.** 2026-09-15.
Labrys Project (computational approaches to Linear A).
Evidence base: `data/analysis/ventris/`; runnable checks: `pipeline/guards.py`.

---

## Abstract

The Kober–Ventris method — group signs by shared frames to obtain a consonant series,
separate them by vowel context to obtain a vowel, aggregate the result with corpus-level
plausibility scoring — is the only systematic technique ever to have produced a decipherment
of an Aegean syllabary (Linear B, 1952). Its modern computational restatements inherit the
same premise. We test that premise under conditions that are maximally favourable to it and
fully controlled: **Linear B itself**, with its phonetic values withheld, using its own
deciphered values as the answer key, 73 correct anchors, 40,038 sign tokens (4× the Linear A
corpus), real Greek phonotactics, and editor-supplied word division.

Four independent operationalizations are measured — five as of 2026-10-01 (§4.5) — each against
both a uniform-chance and a majority-class baseline, with permutation controls for partner-set
relations:

| operationalization | result |
|---|---|
| Shipped-style scorer, hide-N-recover oracle | **0.00×** chance (0/160 recovered) ᵈ |
| Weight simplex, swept exhaustively *(2026-10-01)* | **0 of 1,771** vectors recover one value, and 0 again with the answer guaranteed present |
| From-scratch per-sign instrument (no shared code) | exact value **0.00×**; series 1.03× majority; vowel 1.00× majority |
| Frame sharing (Kober's recorded relation, ~72k pairs) | 0.85–0.98× chance on all four relations |
| Paradigm-slot alternation (identical slot; strict minimal pairs) | partners share series 13.9–14.3% vs 27.4% majority; vowel elimination **matched or beaten by its own permutation control** |
| Context profiles *(2026-10-01)* | series 1.21× majority, (series,vowel) class 4.00× — the first controlled positive; **not convertible** (§4.5) |

ᵈ The pre-repair measurement. A seventh instrument defect made "8 trials" two distinct hidden
sets; repaired, the oracle reports **1/160 and 0.23×** — still below chance, verdict unchanged. §6.1.

No operationalization recovers phonetic values, and none exceeds majority-class prediction for
either the consonant series or the vowel, on the easiest instance available. The negative
survives the repair of eight implementation defects found during this work, including one leak
that had inflated an earlier positive result by 1.28×. Seven repairs left the result where it was;
the eighth moved it from 0.00× to 0.23× — toward chance, not past it (§6.1).

We conclude that corpus-internal distributional structure plus Linear B transfer does not
suffice for value attribution in this script family, and we state precisely which evidence
classes remain untested — now measured rather than listed (§7).

**Plain-language version.** We built a practice version of the puzzle whose answers we already
know, gave the computer every advantage — perfect word divisions, correct readings for
two-thirds of the signs, four times more text than Linear A has — and every method tested
recovered nothing. The methods are not mis-implemented: we found and fixed eight bugs during the
work, and the answer stayed zero (the eighth moved it to 0.23× — still below chance). We then
stopped trying aggregators and swept *every* weighting of the four evidence channels: not one of
1,771 recovers a value, even when the right answer is known to be in the candidate list. The
missing ingredient is not computation; it is information that this corpus does not contain.

---

## 1. Scope: what is and is not tested

**Tested.** Whether phonetic *values* can be attributed to signs in an Aegean syllabary corpus
by (i) distributional relations between signs, and (ii) cross-script transfer from a deciphered
sister script — the two evidence classes available for Linear A today, given that no bilingual
of adequate length exists.

**Not tested, and not claimed.** That Linear A is undecipherable; that its corpus contains no
information at all; that Kober's insight is false in principle. What is falsified is a specific
operationalization family — see §7 for the evidence classes that would give the underlying idea
a fair hearing.

---

## 2. Why Linear B is the best case

| property | Linear A (target) | Linear B (test bed) |
|---|---|---|
| status | undeciphered | deciphered (Ventris 1952) |
| relation | ancestor | descendant |
| script | Aegean syllabary | Aegean syllabary |
| sign inventory | ~69 real | 74 named + 14 unencoded |
| corpus size (sign tokens) | 11,018 | **40,038** |
| word division | inferred | **editor-supplied** |
| values known | ~44 of 138, all hypotheses | **all** (answer key available) |
| genre | administrative | administrative |

Withholding Linear B's values makes the task structurally identical to Linear A while
supplying three things Linear A does not have: an answer key, ground-truth word division, and
four times the data. A method that cannot recover values here cannot recover them there.

**The asymmetry runs in our favour.** Linear B is Greek — an inflected Indo-European language
whose morphology is well described — and its scribal corpus is formulaic. If anything, the test
bed is *more* tractable than Minoan is expected to be.

---

## 3. Apparatus

**Corpus.** `languages/linear-b/` — 7,370 source rows from the InsiderPhD Linear B dataset
(`tablet-sets/tablets.csv`), containing 796 duplicated identifiers (edition repeats) reduced to
**4,794 unique inscriptions**, **40,038 sign tokens**, **12,932 words**. Parser gate: token
coverage **100%** (threshold 0.95) and **88** distinct signs, against a 74-sign Unicode named
inventory.

**Verification of the ingest.** Round-trip reconstruction of the source transliteration from the
sign-ID database plus answer key: **4,794/4,794 inscriptions identical**; **39,719/39,744
(99.94%)** named-sign tokens map back to their own source spelling (the 25 exceptions are
`*65`-style tokens whose named value is `ju`). Sign frequencies reproduce the published Linear B
distribution (ro, jo, a, ko, to, ke, e, wo, pa, ra).

**Answer-key separation.** Values exist in exactly one file (`answer_key.csv`). The database
stores only sign IDs; `transliteration` is NULL for every syllabogram, enforced by
`assert_no_leak()` on every ingest and by a permanent guard. The scorer's SQL reads only
`bennett_id` (`complete.py:253`).

**Pre-registration.** The pass threshold (`lift > 1.5×`), trial count, and interpretation rule
were written into the result file before the first run and were never adjusted. The one
threshold that changed (the parser's unique-sign bound, from a guessed 80–90 to a
reference-relative 90% of the Unicode inventory) was corrected *before* any oracle run, and the
correction is documented where it is enforced.

**Controls.** Every measurement carries a null control: uniform chance *and* majority-class
prediction (§5 explains why uniform chance alone is insufficient), plus permutation controls for
partner-set relations. All controls are computed in the same run, over the same draws and the
same candidate space, as the measurement they bound.

---

## 4. Results

### 4.1 Operationalization 1 — the scorer + hide-N-recover oracle

73 anchors (CONFIRM) and 15 signs with no accepted reading; 8 trials × 20 hidden signs = 160
scored.

| corpus | recovery | chance | lift |
|---|---|---|---|
| Linear B (best case) | **0.0000** | 0.0208 | **0.00×** |
| Linear A (honest purged grid, 45 anchors) | **0.0000** | 0.0945 | **0.00×** |

Search was not the limiting factor: multi-pass coordinate ascent from several initializations on
the same objective also recovered **0/60**; and no aggregator tried — shipped weights, equal
weights, rank-normalised (Borda), two-stage — produced a *unique* argmax for any hidden sign
(top-1 rate **0.0%** across all).

**The whole weight space, swept (2026-10-01).** Eight hand-picked aggregators are not a search, so
the entire 4-channel weight simplex was swept — 1,771 vectors on a 0.05 grid, split by trial into
dev and holdout, the winner reported once on holdout
(`data/analysis/rsi/weight_space_search.py`): **zero vectors recover even one value**, on dev or
holdout. Restricted to draws where the true value *is* in the candidate list (117 dev, 154
holdout) — which isolates the aggregation question from the candidate-generation defect in §6.1 D4
— it is still zero of 1,771. The **identical search** with the truth replaced by a random other
candidate finds 2.8% of dev draws (max 3.8%), and 2.7% on the identifiable subset (max 6.0%): the
true value is *less* likely to be the unique argmax than a random candidate is. This turns §8's
claim from eight counterexamples into an exhaustive result over the convex simplex, and it kills
the tie-break rescue outright — the simplex's vertices are single-channel aggregators, and
lexicographic chains collapse to their first channel when ties are rare, as continuous channels
make them.

**Two readings of the same numbers, distinguished (2026-10-01).** The "components rank the true
value top-1 at 67% / 47% / 59% / 100%" figures (`aggregator_bakeoff.py`; the same quantity appears
in `oracle_diagnose.py` part C) are *not* unique identification. They are `in_argmax`, ties allowed,
which is argmax-set size: for the morph channel the argmax set covers two thirds of the candidate
list. Measured conditional on the truth being a candidate, `in_argmax` equals its own mechanical tie
rate (morph 66.1% vs 66.8%; entropy 50.2 vs 50.9; prefix 52.8 vs 53.9) while unique argmax is
**0.0%** for all nine aggregators tested. Three of the four quoted figures do reproduce as
`in_argmax`; the kober channel's 100% does not (8.9%).

### 4.2 Operationalization 2 — an independent per-sign instrument

Scoring each hidden sign on its own (context-profile cosine against each candidate-bearing anchor
sign, plus weighted series and vowel votes), sharing no code with the shipped scorer:

| metric | instrument | majority baseline | uniform chance | ratio |
|---|---|---|---|---|
| Linear B — exact value | **0.0%** | — | 1.9% | **0.00×** |
| Linear B — consonant series | 23.1% | 22.5% | — | **1.03×** |
| Linear B — vowel | 16.9% | 16.9% | — | **1.00×** |
| Linear A — exact value | 0.6% | — | 4.2% | **0.15×** |
| Linear A — consonant series | 25.0% | 24.4% | — | 1.03× |
| Linear A — vowel | 15.0% | 15.0% | — | 1.00× |

The rebuilt instrument lands exactly on the majority-class baseline: it is not that the shipped
code was uniquely bad. Nothing in the corpus's distributional structure identifies a value.

### 4.3 Operationalization 3 — frame sharing (Kober's recorded relation)

Two signs sharing a following sign are candidates for a shared consonant; two sharing a
preceding sign are candidates for a shared vowel. Measured over all sign pairs in the corpus:

| relation | agreement | chance | ratio | pairs |
|---|---|---|---|---|
| share FOLLOWING sign → same consonant | 0.136 | 0.159 | 0.85× | 71,804 |
| share FOLLOWING sign → same vowel | 0.202 | 0.207 | 0.98× | 71,804 |
| share PRECEDING sign → same consonant | 0.141 | 0.159 | 0.88× | 71,593 |
| share PRECEDING sign → same vowel | 0.197 | 0.207 | 0.95× | 71,593 |

**At or below chance in all four directions.** The frame relation carries no pairwise
information about phonetic identity on the best-case corpus. (Chance here is the marginal
agreement rate between independently drawn values, measured in the same run; pair instances that
share several frame signs are counted once per shared frame, which is what makes the count exceed
the number of distinct pairs.)

### 4.4 Operationalization 4 — paradigm-slot alternation

This is the operationalization Ventris actually used: two signs competing for the same slot of
the same word are paradigm cells, so they should share a consonant and differ in vowel — and if
a sign alternates with da/de/di/do at one slot it is *du*, the missing cell of its own row. Two
definitions were tested, the second the strictest available.

| definition | partners share series | vowel complement unique | correct when unique | permutation control |
|---|---|---|---|---|
| A. shared slot (identical left *and* right neighbour, ≥2 slots) | **13.9%** (vs 27.4% majority) | 12.5% | 9/9 | unique **19.4%**, correct **73.8%** |
| B. strict minimal pair (word types differing in exactly one position) | **14.3%** | 19.4% | 11/14 (78.6%) | unique **18.5%**, correct **80.0%** |

Two conclusions, both negative:

1. Slot-alternating partners do **not** share a consonant series — the rate is roughly *half* the
   majority-class baseline, i.e. the relation is anti-predictive.
2. The eliminative vowel step fires *less* often than its own random control (12.5% vs 19.4%),
   and when it fires its 9/9 success in condition A is a small-sample artifact matched by the
   control (73.8%), which reaches correctness by accident because same-series partner vowels
   cluster. Under the strict definition (B) signal and control converge (78.6% vs 80.0%).

The single apparent positive in this study is therefore not one, and it is reported here because
reporting it is the point: it has the right shape, and it is noise.

---

### 4.5 Operationalization 5 — context profiles: the first controlled positive, and why it is not convertible *(added 2026-10-01)*

Every result above is a negative. This one is not, and it is reported in full for that reason.

**The channel.** A hidden sign's context profile — which signs precede and follow it — is compared
by cosine similarity against the profile of each (series, vowel) class, a class profile being the
summed profiles of the anchors carrying it. No links, no partitioning, no global statistic.

| metric | channel | majority | permutation null | vs majority | vs null |
| (series, vowel) class, exact | **9.6%** | 2.4% | 2.4% | **4.00×** | 3.93× |
| consonant series | 30.8% | 25.4% | 15.4% | **1.21×** | 2.01× |
| exact value | 0.0% | — | 2.3% chance | **0.00×** | — |

500 independent draws (25 trials × 20 hidden signs). The permutation null shuffles values among all
confirmed signs and re-splits anchors from the permutation, on the same draws
(`EXPERIMENT_PROTOCOL.md` §2); it gets its own RNG stream, because a control that consumes the
measurement's randomness is measuring something else.

The class result is the strongest controlled number in this work. **It is claimed as a metric and
nothing more**, for one practical reason and one ceiling:

**1. A class is not a value.** A (series, vowel) class holds ~2.3 candidates. Identifying it does not
identify a value; end-to-end, 9.6% × (within-class accuracy) is the ceiling on what it could deliver.

**2. The scorer cannot pick within a class it is given.** Handing over the *true* class for free —
an oracle restriction, generous in the only direction that matters — the shipped scorer selects the
right member of a 2.32-candidate class **8.5%** of the time against a **47.4%** chance rate:
**0.18×, worse than random** (`data/analysis/rsi/class_restriction_ceiling.py`). Tie-lenient, the
truth is in the argmax set 35.2% of the time (0.74×). The objective actively prefers the less typical
member of a class, which is what a frequency/typicality objective does. No improvement to this
channel, not even a perfect one, can yield values with this scorer. The prediction was written into
the script before the run and held.

**3. And exact value here is 0.0% by construction, not by measurement.** In a syllabary one value
belongs to one sign. Hiding a sign removes its value from the anchor set, so the only candidate that
could be right has an **empty anchor support**: no hide-N-recover instrument can measure a
value-level per-sign channel. It can measure class information, and the class information stops at
attempting to pick a member.

---

## 5. Methodological note: why two baselines

An earlier version of this work reported that the Kober channel identified the correct consonant
series at **6.4–8.4× chance**. That was wrong: the "chance" baseline had been computed over a
label set polluted by an unmapped-value sentinel, so the majority class was a junk label
predicted at ~0% accuracy, and any real series prediction looked enormous. Recomputing against a
clean majority baseline reduced the same channel to **1.03×**.

Uniform chance is the wrong null for a channel that can only ever emit the common class. Every
ratio in §4 is therefore reported against both, and partner-set relations additionally against a
permutation control drawn from the same category. We make no claim that a measurement without a
majority baseline is meaningful — including our own earlier ones.

---

## 6. The result survives the repair of eight defects

*(Six at the time of first writing; the seventh and eighth are §6.1, found 2026-10-01.)*

A zero multiplied by anything is zero, but a zero *measured by broken machinery* is worth
nothing. This result was subjected to adversarial repair before being reported, and is stated
here in the order the defects were found:

| # | defect | effect | measured impact |
|---|---|---|---|
| 1 | sandbox passed a 15-sign "uncertain" set into a detector that keeps only triples with ≥2 uncertain members → graph collapsed to 101 triples with 3 valued partners | constraint channel dead | fixed: 60,155 triples, 76 linked signs; oracle unchanged at 0.00× |
| 2 | oracle chance baseline computed from the *full* anchor set, so a hidden sign's own value tightened its own candidate list | chance inflated 2.3× (Linear A: 0.0841 → 0.0373) | fixed; every historical lift figure in the project is now retired |
| 3 | Kober loader added every triple pair to *both* the consonant and vowel graphs, deleting the distinction that is the method | constraints became one clique | fixed; no numerical change at current density |
| 4 | `CONS_SERIES_MAP` missing 18 of 74 Linear B values, including `no`, `po`, `pe` (1,707 / 1,132 / 1,050 occurrences) | those signs could not earn a series vote | fixed; Linear B only — no Linear A grid value is affected (0 of 52 overlap) |
| 5 | `vowel_of` returned `"?"` for every subscripted value (`ra2`, `ro2`, `ta2`, `pu2`, `a2`, `a3`), in four divergent copies | those signs silently skipped | fixed; consolidated into one module with a self-check |
| 6 | *our own* majority baseline polluted by the unmapped sentinel (§5) | inflated ratios up to 8× | corrected |

Separately, an **anchor-word leak** was found and fixed: hidden signs were re-constrained to
their own true values by hardcoded anchor words, producing a spurious **1.28×** on the first run.
The correct value is 0.00×.

Two further data defects were found while auditing the Linear A side and are *not* part of the
test bed: 85 of 267 glyph entries in the project's LA↔LB mapping were assigned by codepoint
offset (and the generator that produced them did so deliberately), and 16 of 29 rows in the
project's fraction-value file are derived by complement-fitting whose result is then cited as its
own evidence.

**Why this is a strength, not a caveat.** The negative is not the output of one script. It is the
output of five independent operationalizations, an independently written instrument, a permutation
control that beats its own signal, and a repair process that fixed everything fixable and — over
seven of the eight repairs — did not move the result at all. The eighth moved it by 0.23×, still
below chance, verdict unchanged. A result that survives adversarial self-repair is the only kind
worth publishing.

### 6.1 The seventh and eighth defects *(2026-10-01)* — one of them moved the number

Found while building a replay-based method search over this sandbox
(`data/analysis/rsi/`, `.pi/PLAN.md`). Both are in this paper's own instrument.

| # | defect | effect | measured impact |
| 7 | `score_completion` (`complete.py:447`) called `random.seed(0)` on the **global** RNG from inside the scorer, in the middle of `oracle_test`'s trial loop: trial 1 left the stream in a fixed state, so trials 2–8 drew the same hidden set | the pre-registered "8 trials × 20" design ran as **2 distinct draws**; "160 hidden signs scored" was 40. Baseline chance 0.0208 was a 1:7 average of 0.0374 and 0.0185 | repaired (private RNG, scoring bit-identical: all 3,311 component tuples unchanged); oracle **0.00× → 0.23×**, 1/160, **verdict unchanged** (NO SIGNAL). The single hit is `AB 01`, hidden in 1 of 8 trials, recovered via a **tie resolved by candidate-list order** — unique-argmax rate over those draws is 0.0% |
| 8 | `triple_detection.py` enumerated triples by iterating two `set`s of sign ids, so `triple_id` **and** the positional s1/s2/s3 roles that `_load_kober` reads the C/V distinction from were a per-process permutation | the Kober constraint graph was not reproducible in principle, and every oracle run rewrote a tracked data artifact with a 120k-line diff | repaired (sorted enumeration, canonical file order); verified unchanged: same 60,155 triples, same 2,667 C-pairs, same 2,564 V-pairs, and byte-identical across two runs |

Also corrected: the report line "Signs recovered in ALL trials: AB 01" was **false as worded** —
AB 01 was hidden in 1 of 8 trials. It now prints the appearance count. And a **fourth defect, not
repaired**: the candidate generator discards the true value before scoring on ~46% of draws
(36.2% at 80 draws; 54.2% at 500), so every recovery figure in this paper is diluted by ~2× and
no aggregator can be right on those draws (§6.1 D4). It is **not** the binding constraint, which
is why it was left alone: `weight_space_search.py` sweeps 1,771 weight vectors on the *identifiable*
subset — truth guaranteed present — and recovers **zero**.

**Why this strengthens rather than weakens the result.** Seven repairs left the number where it
was. The eighth moved it from 0.00× to 0.23× — toward chance, not past it, and with the verdict
unchanged, because a tie broken by list order is not identification. The repairs also place the two
real defects in order: **aggregation first** (no weighting of the four channels identifies a value,
even with the answer present), **candidate generation second** (~46% of draws void). Fixing the
second first would recover nothing.

---

## 7. What would falsify this — evidence classes left untested

Written down so the closure can be attacked rather than believed. Every operationalization above
reduces to *distributional* evidence within one script plus transfer from a related one. Three
classes of evidence are not touched by this work:

1. **Semantic anchors.** A bilingual of adequate length, or an LA↔Cypro-Minoan correspondence
   with independently established values. Meaning-bearing anchors are a different evidence class,
   and the failure of distributional methods says nothing about them.
2. **A longer, non-administrative text.** All four tests use administrative lists, where word
   slots vary lexically rather than paradigmatically — which is a plausible reason why
   operationalization 4 failed. The `KN Zg 57/58` scepter (119 signs, ritual, the first genuinely
   new long Linear A text since the corpus correction) is the correct test case; condition B of
   §4.4 should be re-run on it the day its edition prints.
3. **Cross-script anchoring.** If Cypro-Minoan, Cretan Hieroglyphic, or Eteocretan yields values
   by any means, the transfer chains become testable, and this apparatus is the acceptance test.

In addition, the test bed is Greek and inflected, while Minoan is *hypothesized* to be
agglutinative. A method could in principle be better suited to the hypothesized target than to
the test bed. This is the one objection that would require a different best-case corpus to
answer, and we note it rather than dismiss it.

### 7.1 The frontier as an action space, and what a policy does with it *(added 2026-10-01)*

The three classes above were prose. They are now a **recorded decision problem**: a pool of 18
method nodes (`data/analysis/rsi/tree.json`, 15 of them replayable, every verdict recomputed from
its own primary metric rather than typed in), each carrying its evidence class, cost, and outcome.
A policy is a Python function over that pool, and it can be replayed against the recorded tree
without re-running the evaluator, because every outcome is already saved.

| class | status as of 2026-10-01 |
| distributional | **measured, closed.** Six branches, 0–1.21× against matched controls, and no weighting of the four channels recovers anything (§4.1) |
| cross-script | untested here, and untestable *as stated* until an independent side exists: the Linear A phonetic grid is itself Linear B transfer, so "LA→LB" is circular. Needs Cypro-Minoan or Cretan Hieroglyphic values |
| semantic anchors | **measured, and it does not replicate.** Eight sign↔commodity-context associations survive a site-stratified permutation at the 122-test family alpha (two at document-level p=2.7e-11 / 2.6e-05) — but selecting on one site and testing on another replicates **2 of 67 pairs, both logogram↔own-class tautologies**, while every *syllabogram* association fails (AB 30 p=0.044, AB 81 p=0.27, AB 31 p=0.42). They are a property of Haghia Triada's entry conventions, not semantic anchors — and a within-site permutation cannot see that, which is the methodology lesson. Separately, a permutation-p association has no legal `primary_metric` in the tree's gate (it scores *recovery* lifts), so the class stays empty there. See `verification_audit.md` Phases 14/14.1 |
| long text | untested. `KN Zg 57/58` is the case; needs the edition, not a method |

Against that pool, the control policy transcribed from §8's own reasoning — expand a live class,
switch after two flat ones, take an acquisition when everything is flat — **scores below doing
nothing**, on both a dev and a held-out split, at every cost calibration tried (β₁ ∈ {0.5, 1, 2}
hours per node): the empty policy scores V = 0, the exploring policy −5.29 (dev) and −3.69
(holdout). The tree's one node with real positive value (the class channel, §4.5) is seven times too
expensive to be worth reaching at β₁ = 1. So the loop's honest output is *stop searching and acquire
evidence*, and that is now a number rather than an argument.

The binding constraint is therefore exactly where §7's list points: outside the corpus. Note what
this implies for anyone tempted to build a self-improving loop on this project: the failure mode is
not a bad policy. It is a well-controlled, rigorously negative loop that returns 0.00× indefinitely
because it was pointed at the one resource that was never scarce — computation.

---

## 8. Implications

**For the method family.** The Ventris-endgame operationalization — frames → series, contexts →
vowels, corpus plausibility → ranking, greedy or coordinate search → values — is closed. It
should not be re-implemented with more parameters, larger models, or better optimizers: §4.1
shows the objective has no resolution to optimize — now **by search over the whole weight simplex
(0 of 1,771 vectors) rather than by eight examples** — and §4.2 shows the ceiling is majority
prediction, and §4.5 a class channel with real signal that the scorer cannot convert (0.18× within
a class it is handed for free).

**For this project.** Four earlier internal conclusions are retired by this work: the 0.6×
oracle baseline (leak-contaminated), the claim that misvalued signs plus positional anomaly
identified a word divider (the anomaly belonged to a logogram, not the syllabogram), the
7,305-triple Kober graph as a source of constraints, and the fraction-value file as evidence.
The audit trail is in `data/analysis/ventris/verification_audit.md`.

**For the field.** The negative is the contribution. Seventy years of Linear A literature
contains many value proposals derived from frame patterns, alternation sets and positional
statistics, generally without controls. This study supplies the control: on the one Aegean
syllabary where the answer is known, those instruments return chance — and, in the one case where
they appear to return signal, they are beaten by their own permutation control.

---

## 9. Reproducibility

```bash
uv sync
uv run python pipeline/guards.py                    # 7/7 guards must pass
uv run python pipeline/lb_ingest.py                 # corpus → DB, gate, leak guard
uv run python pipeline/lb_oracle.py --trials 8      # §4.1 (writes the pre-registration first)
uv run python pipeline/repaired_instrument.py --language linear-b   # §4.2
uv run python pipeline/frame_link_test.py --language linear-b       # §4.3
uv run python pipeline/paradigm_slot_probe.py                       # §4.4
uv run python pipeline/audit_grid_inputs.py                         # §6 data defects
```

Every claim in §4 is produced by one command above; every number in §6 is produced by the
commands in `data/analysis/ventris/oracle_repair_report.md`.

| artifact | path |
|---|---|
| Linear B sandbox corpus + anonymized DB | `languages/linear-b/` |
| answer key (only file containing LB values) | `languages/linear-b/answer_key.csv` |
| pre-registered gate + verdict | `languages/linear-b/data/analysis/ventris/ventris_report.md` |
| corpus round-trip evidence | `pipeline/oracle_diagnose.py` (`check_roundtrip`) |
| defect log | `data/analysis/ventris/oracle_repair_report.md` |
| drift + claim audit | `data/analysis/ventris/verification_audit.md` |
| replay pool, policy, Phase 0–4 record | `data/analysis/rsi/` (`README.md`, `phase0.md`, `tree.json`, `split.json`) |
| the sweep over the weight simplex | `data/analysis/rsi/weight_space_search.py` |
| the class channel and its ceiling | `data/analysis/rsi/identifiable_subset.py`, `class_restriction_ceiling.py` |
| binding rules for new measurements | `EXPERIMENT_PROTOCOL.md` |

```bash
# added 2026-10-01: the method-search appendix (§4.5, §6.1, §7.1)
uv run python pipeline/frame_link_test.py --language linear-b --trials 25    # §4.5
uv run python data/analysis/rsi/class_restriction_ceiling.py                 # §4.5
uv run python data/analysis/rsi/weight_space_search.py --identifiable-only    # §4.1
uv run python data/analysis/rsi/identifiable_subset.py --trials 25           # §4.1, §6.1 D4
uv run python pipeline/rsi_replay.py --policy all --sensitivity              # §7.1
uv run python pipeline/guards.py                     # 13 guards now, not 7
```

---

## 10. Conclusion

On the deciphered sister script, with perfect anchors, four times the data and ground-truth word
division, no operationalization of the Kober–Ventris method recovers a single phonetic value, and
none beats majority-class prediction for the consonant series or the vowel. The result survived
the repair of **eight** defects, a leak that had inflated it, an independently written instrument,
a sweep of the entire weight simplex (0 of 1,771 vectors), and a class channel with genuine signal
that the scorer cannot convert into a value (0.18× within a class it is handed for free).

One number moved during those repairs — 0.00× to 0.23× — and it moved toward chance, not past it:
the single recovered sign was a tie broken by candidate-list order.

If Linear A is to be read, the evidence will have to come from outside its own distributional
structure: a bilingual, a longer non-administrative text, or a deciphered neighbour. The
contribution of this work is not a decipherment. It is a falsifiable statement about what cannot
work, made on the instance where the answer was already known — and the instruments left behind
to test the next candidate the day it arrives.