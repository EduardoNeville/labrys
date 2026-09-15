# Analysis retrace: why the Linear A/B oracles recover nothing

**Date:** 2026-09-15 · Supersedes the "objective contains no information" framing in
`languages/linear-b/data/analysis/ventris/lb_sandbox_result.md`.

Triggered by a correct challenge: 0/160 recovery on a *deciphered* script with perfect
anchors is implausible enough that bugs are more likely than a finding. Retraced layer by
layer. **Three real bugs found (one mine, two in the pipeline) plus one structural
explanation.** The corrected conclusion is *not* "the objective has no information".

---

## Layer-by-layer retrace

| Layer | Check | Result |
|---|---|---|
| Source corpus | 7,370 rows, 796 duplicated identifiers | deduped to 4,794 (duplicates were edition repeats) |
| Tokenizer | 299 distinct tokens, all shapes covered | 100% token coverage, gate passed |
| translit→ID map | injectivity, `*NN` collisions | 75 entries → 75 distinct IDs, no collisions |
| Sign inventory | 88 observed vs 74 named in Unicode | 14 numbered-but-unnamed signs, correctly UNCERTAIN |
| **DB round-trip** | reconstruct source transliteration from DB + key | **4,794/4,794 inscriptions identical; 39,719/39,744 (99.94%) tokens round-trip** (the 25 misses are `*65` tokens whose named value is `ju`) |
| Value leak | `SELECT DISTINCT transliteration` | all NULL |
| Frequencies | top signs | ro, jo, a, ko, to, ke, e, wo, pa, ra — matches known Linear B distribution |
| Scorer inputs | `complete.py:253` | reads `bennett_id` only |

**The corpus layer is correct.** Nothing below it is an ingest artefact.

---

## Bug 1 — my sandbox strangled the Kober channel (fixed)

`pipeline/lb_oracle.py:build_kober` passed the 15 *unnamed* signs as the detector's
`uncertain` set. `triple_detection.py:375` keeps only triples with **≥2 UNCERTAIN members**:

```python
self.triples = [t for t in self.triples if t["uncertain_count"] >= 2]
```

That filter is Linear A bookkeeping — LA is 94 UNCERTAIN / 44 CONFIRM (68% unknown), so it
barely bites. The sandbox was 15/88 (17%), so it collapsed the graph:

| uncertain set | triples | signs with a *named* partner |
|---|---|---|
| unnamed-only (as first run) | 101 | **3** ← constraint channel dead |
| all signs (filter inert) | 60,155 | 76 |

With 101 triples the hubs were `AB 34/56/79` — all valueless — so every hidden sign's
partners were valueless and **zero anchor votes fired**. Fixed: pass all observed signs.

## Bug 2 — the oracle's chance baseline was inflated (fixed)

`pipeline/ventris/complete.py:oracle_test` derived the random baseline from
`self.get_candidates(b)` with the **full** `self.confirmed`. A hidden sign's own value
therefore tightened its own candidate list, inflating the per-sign chance rate. Fixed to use
each trial's effective (non-hidden) anchor set:

| | before | after |
|---|---|---|
| Linear B chance | 0.0683 | **0.0193** |
| Linear A chance | 0.0841 | **0.0373** |

This is a leak in the *opposite* direction to the anchor-word leak found earlier: it made the
method look worse (lower lift) than the machinery warranted.

## Bug 3 — `_load_kober` discarded the Kober semantics (fixed)

`complete.py:_load_kober` added **every** pair of a triple to **both** graphs:

```python
for a, b in [(s1, s2), (s1, s3), (s2, s3)]:
    self.kober_clinks[a].add(b); self.kober_vlinks[a].add(b)   # identical graphs
```

That deletes the consonant/vowel distinction — Kober's entire method. The triple file carries
the real semantics (`sign_1↔sign_2` share a *following* sign → consonant-candidate;
`sign_2↔sign_3` share a *preceding* sign → vowel-candidate; `sign_1↔sign_3` both). Fixed to
consume it. Measured effect at current density: **none** (graphs are near-complete either
way, see below) — but the bug is real and would matter on a sparser graph.

---

## Structural finding — the answer to "why exactly zero"

### (a) The Kober channel is degenerate at both densities

| graph | behaviour |
|---|---|
| sparse (101 triples) | no votes → `kober_score` constant 0.5 → term inert; candidates ~70 |
| dense (60,155 triples / 76 signs) | every sign links to ~71 others → "series vote" = plurality over a near-complete set → noise; candidate lists 39.3; **truth excluded 51.7% of the time** |

Linear A is the same shape: 56 linked signs, **28.7 partners per anchor** — near-complete.
So the constraint stage that is supposed to reduce ~70 candidates to a handful either does
nothing or actively removes the truth. Measured discrimination of the Kober term on LB:
mean rank **0.531 — worse than chance**.

### (b) The score terms have orientation but no resolution

With everything else held at truth, each term ranks the true value inside its argmax set
(ties counted) as: morph 65.5%, entropy 58.6%, prefix 69.0%, kober 10.3%, and the shipped
sum **6.9%** — the combination is *worse than any single component, because the components
are on incomparable scales and the three noisy terms (weight 0.70) outvote the informative
one (0.30)*.

Across every aggregator tried — shipped weights, equal weights, Borda rank-normalisation,
kober-then-entropy two-stage — **the unique-argmax rate is 0.0%**. The components narrow the
field; nothing identifies a value.

### (c) Why a per-sign likelihood cannot work as written

In a syllabary each value belongs to exactly one sign. **Hiding a sign removes its value from
the anchor-only model entirely.** Measured directly:

| hidden sign | truth | `uni[truth]` in the anchor model | what the estimators do |
|---|---|---|---|
| AB 58 | su | **0** | LL picks `sa` (frequency bias) |
| AB 06 | na | **0** | PMI ties all zero-count values incl. `su`/`na` (absence bias) |
| AB 39 | pi | **0** | both fail |

So the shipped estimator is not measuring "does this value fit this sign" — it measures
distributional resemblance to other signs' values, and the two obvious estimators degenerate
into frequency bias (log-likelihood) or absence bias (PMI). PMI puts the truth in the argmax
set 100% of the time but always tied — no identification.

---

## Corrected numbers

| | recovery | chance | lift | verdict |
|---|---|---|---|---|
| Linear B, first run (leaky anchors, buggy chance) | 0.0875 | 0.0683 | 1.28× | invalid (leak) |
| Linear B, leak fixed, bugs 1–2 present | 0.0000 | 0.0683 | 0.00× | invalid (bug 1) |
| **Linear B, all fixes** | **0.0000** | **0.0193** | **0.00×** | valid measurement of a *broken instrument* |
| Linear A, historical | — | — | 0.6× | leak-contaminated |
| **Linear A, fixed code, default grid** | **0.0000** | **0.0373** | **0.00×** | same structural cause |

## What this does and does not establish

**Establishes:** the oracle test, as built, cannot recover values — for Linear B with perfect
anchors *or* Linear A. The cause is candidate-generation + aggregation design, not corpus size
and not "the corpus contains no information".

**Does NOT establish:** that Linear A is undecipherable, that the corpus lacks signal, or that
Kober's method is worthless. Those claims need an instrument with resolution, which this one
is not.

**Retracted from my earlier message:** "this closes a genre of papers" and "the objective
contains no usable gradient". The objective's *components* carry orientation (59–69%); what is
missing is a discriminating estimator and a working constraint stage.

## Open items (each is an instrument repair, not a corpus question)

1. **Give the estimator the hidden sign itself.** A per-sign likelihood must model "the value
   of sign X", e.g. via frame-based prediction: score candidate `v` by the observed
   *following signs* of X against the anchor signs that carry `v` — i.e. compare the sign's
   own context distribution to each candidate-bearing sign's distribution (nearest-neighbour
   over contexts), not a global corpus statistic.
2. **Repair the Kober stage.** With a near-complete link graph the threshold
   `max(2, max//2)` is meaningless. Use link weights (shared-frame counts) and require
   *mutual best* partners rather than a global threshold.
3. **Re-run all LA numbers with the fixed code** (any historical 0.6× / optimizer conclusions
   are invalid), and note this in `verification_audit.md`.
