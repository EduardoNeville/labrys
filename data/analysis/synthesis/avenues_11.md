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

**Anomaly detection (facts, not interpretations):** Signs with medial_fraction
< 0.15 are NOT normal medial CV syllables — they appear almost only in
initial/final position. This correctly flags the known misvalued signs:

| Sign | Status | init | med | final | n | Positional fact |
|------|--------|------|-----|-------|---|----------------|
| AB 85 | UNCERTAIN | 0.47 | 0.06 | 0.47 | 508 | Never medial — but see retraction below |
| AB 60 | UNCERTAIN | 0.49 | 0.00 | 0.51 | 93 | /ra/-vs-/ma/ keystone — not a normal CV sign |
| AB 80 | UNCERTAIN | 0.50 | 0.04 | 0.46 | 28 | Misvalued (Phase 2) |
| AB 82 | UNCERTAIN | 0.44 | 0.00 | 0.56 | 16 | Never medial — see Avenue 2 retraction |
| AB 22 | CONFIRMED | 0.22 | 0.11 | 0.67 | 9 | pi — final-dominant |
| AB 110 | UNCERTAIN | 0.43 | 0.14 | 0.43 | 7 | Anomalous — investigate |
| AB 16 | UNCERTAIN | 0.60 | 0.00 | 0.40 | 5 | qa/ka — misvalued |

**Key finding (revised after verification audit):** AB 85 is positionally
anomalous (med=0.06, 508 occ) — the *fact* is real. But the interpretation
"word divider" is **not independently established**: AB 85's transliteration is
`*301`/`*306` (logogram numbers), the `word_dividers` table is empty, and its
grid status is CONFIRM-with-`?` (confidence 25/100). It may equally be a
frequently-standalone logogram/ligature. **Downgraded: positional fact real,
interpretation unsupported.**

**Deliverable:** `data/analysis/positional/anomalous_signs.csv`

**Honest limit:** positional profiles flag *which* signs are non-syllabographic
but cannot assign phonetic values. Useful for prioritization, not solving.

---

## Avenue 2 — "Reverse Rosetta": Commodity Logograms as Semantic Anchors

**Status:** ✅ Concluded — method works, but the one "significant" result is circular (retracted after audit)

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

**Key finding (revised after verification audit):** AB 82's association with
LIVESTOCK is **circular** — AB 82 appears as `HIDE+[?]` (a livestock ligature)
inside PH10, a livestock entry. The "enrichment" rediscovered the data encoding
(AB 82 tagged with a HIDE ligature → classified as LIVESTOCK), not an
independent association. Both co-occurrences come from the single inscription
PH10. **Retracted as a discovery; reframed as a data fact** (AB 82 co-occurs
with HIDE ligatures in livestock entries).

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

**Status:** ✅ Concluded — negative (not testable + no phonetic correlation)

**Original idea:** Compare LA co-occurrence graph topology to Linear B's — if
hubs/communities match, that's evidence of shared syllable structure.

**Why it fails (three independent reasons):**
1. **No LB corpus sequences in the repo.** The only LB data is the visual/
   value mapping (`la_lb_mapping.csv`) — no LB co-occurrence graph exists to
   compare against. True isomorphism is untestable with current data.
2. **Degenerate LA community structure.** The LA sign graph is one giant
   component (337 of 345 signs in community 0) — everything co-occurs with
   everything because administrative tablets list many items.
3. **Centrality is a frequency artifact.** Top-degree signs are numerals and
   fractions (𐄁, 𐄇, 𐄈...) which appear adjacent to everything. Among
   syllabograms, top-degree values are phonetically incoherent (du, pa, ni,
   jo, ro, a, ru, pu — no shared class), and the confirmed fraction among
   top-20 degree (55%) ≈ overall (59%) — no correlation with LB confidence.

**Variant tested:** graph-community ↔ phonetic-class correlation — fails.
Graph centrality carries no phonetic signal.

**Conclusion:** The LA co-occurrence graph has no structure that correlates
with phonetics. Same root cause as Avenues 1–3: frequency dominates, the
corpus is too small/formulaic. Cross-script isomorphism would require an LB
corpus, which we don't have.

---

## Avenue 6 — Diachronic Analysis (MM → LM script evolution)

**Status:** ✅ Concluded — POSITIVE, first non-circular finding

**Data:** 43 syllabograms appear in both MM (~1700 BCE) and LM (~1450 BCE)
periods; 78 are LM-only. The pre-LM subset is small (172 signs) but the
*persistence* signal is robust.

**Core finding:**

| Sign set | % CONFIRMED |
|----------|-------------|
| Shared (MM→LM persistent) | **67%** (28/42) |
| LM-only (later) | **33%** (26/78) |
| Fisher exact p | **0.0003** |
| Enrichment | 2.0× |

**Oracle LOO:** persistence predicts CONFIRMED status at 67% vs 55% majority
baseline — **1.21× lift**, out-of-sample.

**Why this survives verification (unlike Avenues 1–2):**
1. **Not circular** — confirmation from phonetic evidence (LB/CM), persistence
   from period data. Independent sources.
2. **Significant** — Fisher p=0.0003, single test (no multiple-testing issue).
3. **Not frequency-driven** — shared-confirmed median LM freq 2.5 vs
   shared-uncertain 3.0; the signal is independent of frequency.

**Interpretation:** script continuity is a real prior on phonetic confidence.
Signs that survived 250 years of script evolution are twice as likely to have
secure values. Historical sense: stable inherited signs are well-attested;
LM-only signs are likely later innovations or rare/uncertain.

**Honest limit:** a *prior*, not a value. Raises the prior on MM-attested
UNCERTAIN signs; flags LM-only signs as likelier late/rare. Cannot assign
phonetic values.

**Deliverable:** `data/analysis/ventris/diachronic_analysis.csv`,
`pipeline/ventris/diachronic.py`

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

*Phase 11 — research roadmap. Verified findings: oracle (no scorer signal),
Avenue 3/4 (negative), Avenue 6 (POSITIVE — diachronic persistence predicts
confirmation, p=0.0003, LOO 1.21× lift). Retracted: Avenues 1–2 (circular).
See `data/analysis/ventris/verification_audit.md`. Avenue 5 (new data) remains
open — it's corpus growth, not code.*
