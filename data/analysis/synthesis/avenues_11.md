# Phase 11 — Unexplored Avenues (Research Roadmap)

**Status:** Open — Phase 10 (Ventris endgame) concluded negative. The oracle
ablation test proved the grammatical scorer has no signal (recovery 0.6× chance
across 4 runs, even after strengthening with Kober-consistency, held-out
cross-entropy, and known-word anchors).

**Core diagnosis:** every corpus-derived phonetic signal is circular — it
derives from Linear B transfer, the same evidence the scorer would need to
independently rediscover. The oracle cannot distinguish right from wrong
because "right" is defined by the only evidence available.

**The one non-circular signal:** positional profiles (Phase 2) measure sign
*identity* distributions (which signs appear where) with **no phonetic
assumption**. This is the leverage point for new avenues.

---

## Avenue 1 — Positional Profiles as Phonetic-Independent Constraints

**Status:** ✅ Concluded — vowel recovery fails, but anomaly detection works

**Vowel-recovery oracle (failed):** Hidden confirmed signs, predicted vowel
column from positional profiles. Recovery 0.13 vs chance 0.20 (0.66×) — below
chance. Mean positional profiles per vowel are nearly identical
(init≈0.15, med≈0.68, final≈0.15 for all vowels) — Minoan words don't have
vowel-marked word positions, so positional profiles cannot encode vowel class.

**Anomaly detection (works):** Signs with medial_fraction < 0.15 are NOT normal
medial CV syllables — they appear almost only in initial/final position. This
correctly flags the known misvalued signs AND the word divider:

| Sign | Status | init | med | final | n | Interpretation |
|------|--------|------|-----|-------|---|----------------|
| AB 85 | UNCERTAIN | 0.47 | 0.06 | 0.47 | 508 | **Word divider (confirmed independently)** |
| AB 60 | UNCERTAIN | 0.49 | 0.00 | 0.51 | 93 | /ra/-vs-/ma/ keystone — not a normal CV sign |
| AB 80 | UNCERTAIN | 0.50 | 0.04 | 0.46 | 28 | Misvalued (Phase 2) |
| AB 82 | UNCERTAIN | 0.44 | 0.00 | 0.56 | 16 | Anomalous — investigate |
| AB 22 | CONFIRMED | 0.22 | 0.11 | 0.67 | 9 | pi — final-dominant |
| AB 110 | UNCERTAIN | 0.43 | 0.14 | 0.43 | 7 | Anomalous — investigate |
| AB 16 | UNCERTAIN | 0.60 | 0.00 | 0.40 | 5 | qa/ka — misvalued |

**Key finding:** AB 85 (the suspected word divider) is the #1 anomalous sign
at 508 occurrences — positional data independently confirms it is not a
syllabogram. The anomaly signal also flags AB 82 and AB 110 as new
investigation targets.

**Deliverable:** `data/analysis/positional/anomalous_signs.csv`

**Honest limit:** positional profiles flag *which* signs are non-syllabographic
but cannot assign phonetic values. Useful for prioritization, not solving.

---

## Avenue 2 — "Reverse Rosetta": Commodity Logograms as Semantic Anchors

**Status:** ✅ Concluded — one Bonferroni-significant association found

**Method:** Hypergeometric enrichment test (exact, no scipy). For each
(commodity, sign) pair, computes P(co-occurrence ≥ observed by chance) across
all 526 adjacent syllabogram slots in 635 logogram contexts. Multiple-testing
corrected (Bonferroni over ~94 tests → family-wise alpha = 0.00053).

**Results (uncorrected p < 0.05):**

| Sign | Commodity | k/n | p | fold | Bonferroni |
|------|-----------|-----|---|------|-----------|
| **AB 82** | LIVESTOCK | 2/5 | 0.0002 | 70× | ✅ **survives** |
| AB 77 | OLIVE_OIL | 2/5 | 0.0155 | 9.6× | — |
| AB 21f | OLIVE_OIL | 1/5 | 0.0376 | 26× | — |
| AB 14 | MANPOWER | 1/6 | 0.045 | 22× | — |
| AB 29 | VESSELS | 31/406 | 0.0093 | 1.2× | — |
| AB 62 | VESSELS | 18/406 | 0.0455 | 1.2× | — |

**Key finding — cross-avenue convergence on AB 82:**
- Avenue 1: AB 82 is positionally anomalous (medial_fraction = 0.00, appears
  only initial/final) — flagged as likely non-CV or functional sign
- Avenue 2: AB 82 is significantly enriched in LIVESTOCK contexts (p=0.0002)

Two independent signals converge: AB 82 behaves like a livestock-related
word or a functional sign (qualifier / divider) in livestock entries. This is
the "double constraint" the failed Ventris scorer couldn't find — a semantic/
functional identification, not a phonetic value.

**Honest caveat:** LIVESTOCK has only 5 adjacent slots (k=2/5). The 70× fold
rests on small counts. Suggestive, not conclusive — but the independent
convergence with Avenue 1 makes AB 82 the strongest lead in the project.

**Deliverable:** `data/analysis/commodity_decoding/sign_commodity_enrichment.csv`

---

## Avenue 3 — Statistical Cryptanalysis (the "cipher" framing)

**Status:** ✅ Concluded — negative (all signals are frequency artifacts)

**Method:** Three classic phonetic-independent cryptanalysis tests on raw sign
sequences (311 sequences ≥5 syllabograms, 120 signs):

| Test | Real | Null (shuffled) | Verdict |
|------|------|-----------------|---------|
| Zipf alpha | 1.502 (R²=0.757) | **1.502 (identical)** | Pure frequency artifact — zero sequential info |
| Bigram reduction | 26.7% | 18.1% (token-shuffle) | Mostly frequency artifact; ~7pp real, weak |
| Kober V-link cohesion | 2.2× | — | **Circular** — V-links ARE shared-context links |

**Key findings:**
1. Zipf's law is identical under token shuffle — it measures the frequency
   distribution (inventory usage), not sequential structure.
2. Bigram reduction survives shuffle at ~18% — the frequency distribution
   alone creates apparent structure (rare signs rarely follow rare signs).
   Real sequential signal above baseline: only ~7pp, too weak to exploit.
3. Kober V-links are *defined* as shared-following/preceding context
   (`connections: C,V,both`), so high cohesion is circular by construction —
   not vowel harmony, not phonological signal.

**Conclusion:** The raw sign stream has almost no sequential structure beyond
frequency. This independently confirms the oracle: no exploitable statistical
signal in 11K tokens of formulaic administrative text. The corpus is too small
and too repetitive for statistical or grammatical attack.

**Deliverable:** `pipeline/ventris/cryptanalysis.py` (reusable tests +
 shuffle null controls)

---

## Avenue 4 — Cross-Script Structural Comparison (Graph Isomorphism)

**Status:** ⬜ Not started

**Idea:** The sign co-occurrence graph (Phase 2 network) is structure
independent of phonetics. Compare it to the same graph for Linear B and
Cypro-Minoan. If the *topological structure* of the LA graph matches LB's
(same hubs, same communities), that's evidence the underlying language has
similar syllable structure — even without knowing the values. Graph-theoretic
test the oracle can validate.

**Data:** `data/analysis/network/global/sign_centrality.csv`.

---

## Avenue 5 — New Data (the honest long-shot)

**Status:** ⬜ Not started

**Idea:** The corpus is 11K tokens — ~1 page of modern text. The single
highest-value action is enlarging it: new inscriptions from ongoing Minoan
excavations, or better TEI coverage of GORILA. Every avenue above is capped
by the same ceiling.

---

## Skipped (proven dead)

- **More scorer terms** — oracle-proven dead (4 runs, all ≤ chance)
- **Optuna/beam/annealing** — no objective with gradient
- **More language-family testing** — Tyrsenian already tested, no signal

---

*Phase 11 — research roadmap. Avenues 1–3 concluded (1: anomaly works; 2: AB 82↔LIVESTOCK; 3: negative — all signals are frequency artifacts). Avenue 4 is next.*
