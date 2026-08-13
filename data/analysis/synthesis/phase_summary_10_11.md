# Phase 10–11 Consolidated Summary: The Ventris Endgame, Its Failure, and the Verified Remains

**Date:** 2026-08-13
**Scope:** Phase 10 (Ventris endgame: 10a Egyptian bridge, 10b grid completion, 10c oracle test) and Phase 11 (four unexplored avenues + diachronic analysis)
**Status:** Honest synthesis — verified findings only, retractions documented

---

## Table of Contents

1. [Phase 10: The Ventris Endgame](#1-phase-10-the-ventris-endgame)
   - [10a Egyptian bridge & frequency constraints](#10a-egyptian-bridge--frequency-constraints)
   - [10b Grid completion](#10b-grid-completion)
   - [10c Oracle ablation test](#10c-oracle-ablation-test)
2. [Phase 11: Four Avenues](#2-phase-11-four-avenues)
   - [Avenue 1 — Positional profiles](#avenue-1--positional-profiles)
   - [Avenue 2 — Commodity semantics](#avenue-2--commodity-semantics)
   - [Avenue 3 — Statistical cryptanalysis](#avenue-3--statistical-cryptanalysis)
   - [Avenue 4 — Graph isomorphism](#avenue-4--graph-isomorphism)
3. [Phase 11: The Diachronic Prior (the one positive finding)](#3-phase-11-the-diachronic-prior)
4. [Verification Audit](#4-verification-audit)
5. [What Survives — The Solid Core](#5-what-survives--the-solid-core)
6. [What Was Retracted](#6-what-was-retracted)
7. [The Honest State of the Decipherment](#7-the-honest-state-of-the-decipherment)
8. [Path Forward](#8-path-forward)

---

## 1. Phase 10: The Ventris Endgame

**Goal:** Reproduce Ventris's method for Linear A — build the partial CV grid from confirmed anchors, enumerate completions, and test grammatical hypotheses against the corpus.

### 10a — Egyptian bridge & frequency constraints

- **Egyptian bridge** (`egyptian_bridge/`): 88 Middle Egyptian trade terms tested against the corpus. 312 matches, but null-model ratios 1.6–6.4× — **consistent with chance**. No detectable Egyptian loans.
- **Frequency-typology constraints** (`frequency_constraints/`): eliminated 28.2% of candidate phonemes for 80 UNCERTAIN signs (687 of 2,440). Boundary-flexible cluster: 62% eliminated. But this is a *filter*, not a resolution.

### 10b — Grid completion

- Built partial CV grid from 58 CONFIRMED anchors (34/40 cells filled).
- 100 random completions scored on morphology/entropy/prefix.
- **Result: zero per-sign consensus at 60% threshold.** Search space ~10¹⁴⁰ — random sampling cannot converge.
- The report concluded "beam search is next" — which 10c superseded.

### 10c — Oracle ablation test

The decisive experiment. **Before building any search (beam, annealing, Optuna), test whether the scorer can recover KNOWN answers.** Hide confirmed signs, treat them as uncertain, run greedy restore, measure recovery vs chance.

| Run | Recovery | Chance | Lift |
|-----|----------|--------|------|
| Original scorer | 0.006 | 0.055 | 0.11× |
| + leakage fix | 0.006 | 0.055 | 0.11× |
| + Kober/cross-entropy/anchors | 0.050 | 0.084 | 0.59× |
| + anchor-leak fix | 0.050 | 0.084 | 0.59× |

**Verdict: the scorer has no signal.** Even with every other hidden sign at its true value, the true value ranks 45th/70, excluded, or 37th/70 — the argmax is never right. No optimizer can recover answers an objective doesn't contain.

**Root cause (verified):** every corpus-derived phonetic signal is circular — derived from Linear B transfer, the same evidence the scorer would need to independently rediscover.

---

## 2. Phase 11: Four Avenues

Four phonetic-independent approaches tried after the oracle failure. All tested with proper controls (shuffle nulls, multiple-testing correction, circularity checks).

### Avenue 1 — Positional profiles

- **Vowel recovery: FAILED.** Nearest-prototype on positional profiles recovered 0.66× chance. Mean profiles per vowel are near-identical — Minoan has no vowel-marked word positions.
- **Anomaly detection: real facts, retracted interpretation.** Signs with medial_fraction < 0.15 are not normal medial CV syllables. Correctly flags AB 60, AB 80, AB 16 (known misvalued) and AB 82, AB 110.
- **RETRACTED:** "AB 85 = word divider." AB 85's transliteration is `*301`/`*306` (logogram numbers), the `word_dividers` table is empty, grid status CONFIRM-with-`?` at confidence 25/100. The positional fact is real; the interpretation is unsupported.

### Avenue 2 — Commodity semantics

- Hypergeometric enrichment test (exact, no scipy) over 526 adjacent syllabogram slots in 635 commodity contexts, Bonferroni-corrected over ~94 tests.
- **RETRACTED:** "AB 82 ↔ LIVESTOCK (p=0.0002, 70×)". Both co-occurrences come from a single inscription (PH10) where AB 82 appears as a `HIDE+[?]` ligature. The enrichment rediscovered the data encoding, not an independent association.

### Avenue 3 — Statistical cryptanalysis

All three classic tests, with shuffle nulls:

| Test | Real | Null | Verdict |
|------|------|------|---------|
| Zipf alpha | 1.502 | **1.502 identical** | Frequency artifact |
| Bigram reduction | 26.7% | 18.1% | ~7pp real, weak |
| Kober V-link cohesion | 2.2× | circular | V-links ARE shared-context links |

**Verdict: the raw sign stream has almost no sequential structure beyond frequency.** Independently confirms the oracle.

### Avenue 4 — Graph isomorphism

- No LB corpus sequences in repo — true LA↔LB graph comparison untestable.
- LA community structure degenerate (337/345 signs in one component).
- Centrality is a frequency artifact (top-degree = numerals; top syllabograms phonetically incoherent).
- **Verdict: negative.**

---

## 3. Phase 11: The Diachronic Prior (the one positive finding)

The one avenue that used a **data dimension** (time) rather than a scoring hypothesis — and the only positive finding that survived verification.

### Finding

Signs attested in BOTH MM (~1700 BCE) and LM (~1450 BCE) periods are 2× more likely CONFIRMED:

| Sign set | % CONFIRMED |
|----------|-------------|
| Shared (MM→LM persistent) | **67%** (28/42) |
| LM-only | **33%** (26/78) |
| Fisher exact p | **0.0003** |
| Oracle LOO | 67% vs 55% majority = **1.21× lift** |

### Why it survives (unlike Avenues 1–2)

1. **Not circular** — confirmation from phonetic evidence, persistence from period data (independent sources).
2. **Significant** — Fisher p=0.0003, single test.
3. **Not frequency-driven** — shared-confirmed median LM freq 2.5 vs 3.0.
4. **Independent of phonetic evidence** — MM-attested mean confidence 51.0 vs LM-only 28.4 (1.8×), holds even when LB/CM components are empty.

### Concrete consequences

- **AB 60 (ra/ma keystone) is LM-only** → the prior LOWERS its stakes. The project's most famous open question is less likely to resolve than assumed.
- **AB 16 (qa/ka) is MM-attested** → the prior RAISES it. The conflict worth resolving.
- **Highest-priority UNCERTAIN signs:** AB 16, AB 82, AB 89, AB 90 (the only MM-attested uncertain signs).
- **Bayesian form:** `conf_adjusted = conf_base × (2.0 if MM else 0.5)` — a re-weighting layer for any future evidence.

### Honest limits

A prior, not a value. Re-weights which signs to bet on, doesn't say what they mean. Positional behavior is NOT conserved across periods (persistence = existence, not function). The shared set is 43 signs; the MM subset is 172 signs.

---

## 4. Verification Audit

Before synthesis, every finding was audited against source data (`verification_audit.md`). Results:

| Claim | Status |
|-------|--------|
| Oracle: scorer has no signal | ✅ Confirmed |
| Avenue 3: signals are frequency artifacts | ✅ Confirmed |
| Avenue 4: untestable + no signal | ✅ Confirmed |
| Avenue 6: diachronic prior | ✅ Confirmed (positive) |
| Toponyms pa-i-to / i-da | ✅ Solid (95 Phaistos matches dist=1; 20 Ida matches, robust to da/ta) |
| Misvalued signs AB 16/60/80 | ✅ Supported |
| Agglutinative morphology | ✅ Supported (weakly) |
| Avenue 1: AB 85 word divider | ❌ Retracted (circular) |
| Avenue 2: AB 82↔LIVESTOCK | ❌ Retracted (circular) |
| "78 anchors" | ⚠️ Overstated → 77 CONFIRMED, 19 with value `?`, 17/77 ≥70, refined grid confirms 44 |
| "Tyrsenian best fit" | ⚠️ Overstated → Anatolian IE #1, Hurro-Urartian #2, Tyrsenian #3, ALL inconclusive |
| AB 01/38/50 high-confidence | ⚠️ Downgraded → UNCERTAIN in refined grid (LB/CM conflicts) |

---

## 5. What Survives — The Solid Core

The verified, non-circular findings the project can stand on:

1. **Toponyms pa-i-to (Phaistos) and i-da (Ida) are real** — 95 and 20 matches, robust to the da/ta conflict. The only solid lexical anchors.
2. **Misvalued signs AB 16, AB 60, AB 80 are positionally anomalous** — reproducible, phonetic-independent.
3. **The diachronic prior** — MM-attested signs are 2× more likely to carry secure values (p=0.0003), independent of the phonetic evidence.
4. **The oracle harness** — the correct gate for any future scorer or new evidence.

---

## 6. What Was Retracted

1. "AB 85 is the word divider" — positional fact real, interpretation unsupported (logogram transliterations, empty word_dividers table).
2. "AB 82 ↔ LIVESTOCK" — circular (HIDE ligature encoding in PH10).
3. "Tyrsenian is the best structural fit" — no family distinguished (Anatolian and Hurro-Urartian rank higher).
4. "78 anchors" — overstated; the reliable set is ~58 values, ~17 high-confidence.
5. "Beam search is next" (10b report) — superseded by the oracle: no search can help an objective with no signal.

---

## 7. The Honest State of the Decipherment

The computational avenues are **exhausted**. Every approach that produced a positive claim was either:
- **Circular** (derived from LB transfer or corpus encoding), or
- **Below the noise floor** (frequency artifacts, weak sequential signal)

The one surviving positive — the diachronic prior — is a *prior*, not a value. It re-prioritizes which signs to investigate but cannot assign phonetic values.

**The fundamental bottleneck is unchanged:** 11K tokens of formulaic administrative text, no bilingual anchor, no independent phonetic evidence. Every statistical and grammatical method is capped by this ceiling.

---

## 8. Path Forward

1. **New data is the only known lever.** New inscriptions from ongoing Minoan excavations, better GORILA TEI coverage, or a bilingual find. The oracle harness + diachronic prior are the correct tools to apply to any new data.
2. **The diachronic prior should be folded into any future evidence.** `conf_adjusted = conf_base × (2.0 if MM else 0.5)` — and re-oracle-tested.
3. **AB 16 (qa/ka) is the highest-priority open conflict** — MM-attested, raised prior. AB 60 (ra/ma) is downgraded (LM-only).
4. **The oracle is the gate.** Any new scorer, new evidence, or new method must pass the oracle before being trusted.

---

*Phase 10–11 — the Ventris endgame was attempted, tested honestly, and failed. The verification audit separated the circular from the solid. What survives is small but real: two toponyms, three misvalued-sign flags, and a diachronic prior. The corpus remains the ceiling.*

## Source Files

| File | Description |
|------|-------------|
| `pipeline/ventris/complete.py` | Grid completer + oracle ablation test |
| `pipeline/ventris/positional_oracle.py` | Avenue 1 (positional) |
| `pipeline/ventris/commodity_semantics.py` | Avenue 2 (commodity enrichment) |
| `pipeline/ventris/cryptanalysis.py` | Avenue 3 (cryptanalysis + nulls) |
| `pipeline/ventris/diachronic.py` | Avenue 6 (diachronic prior) |
| `pipeline/ventris/diachronic_prior.py` | Avenue 6b (prior applied) |
| `data/analysis/ventris/verification_audit.md` | Claims audit (retractions) |
| `data/analysis/ventris/diachronic_findings.md` | Avenue 6 detailed findings |
| `data/analysis/synthesis/avenues_11.md` | Phase 11 roadmap |
