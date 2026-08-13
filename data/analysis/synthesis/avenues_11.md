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

**Status:** ⬜ Not started

**Idea:** Logograms (commodity signs) are phonetically unreadable but
semantically known (grain, oil, wine, metal). The corpus pairs syllabograms
with logograms on the same tablet. If the same syllabogram sequence recurs
adjacent to "wine" across many tablets, it's likely a word for wine or a
measure word. This is *semantic*, not phonetic — doesn't need the failed
scorer. Phase 5's commodity alignment touched this but didn't exploit
co-occurrence clustering.

**Data:** `data/analysis/logograms/`, `data/analysis/comparative/commodity_*`.

---

## Avenue 3 — Statistical Cryptanalysis (the "cipher" framing)

**Status:** ⬜ Not started

**Idea:** Linear A is a syllabary (each sign = one syllable), not a random
cipher. Frequency distributions encode language structure. Zipf's law,
mutual information, and character-level language models on *sign sequences*
(not phonetic values) can identify:
- Which signs are likely vowels (high frequency, high entropy neighbors)
- Which signs are likely the same morpheme (consistent co-occurrence)

Phonetic-independent, doesn't need the failed scorer.

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

*Phase 11 — research roadmap. Avenue 1 concluded (anomaly detection works, vowel recovery fails). Avenue 2 is next.*
