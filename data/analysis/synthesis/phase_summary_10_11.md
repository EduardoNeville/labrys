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
3. [Phase 11: The Diachronic Prior (INVALIDATED by correction)](#3-phase-11-the-diachronic-prior)
4. [The Corpus Correction (the key event)](#4-the-corpus-correction-the-key-event)
5. [The Libation Formula Recovery](#5-the-libation-formula-recovery)
6. [Verification Audit](#6-verification-audit)
7. [What Survives — The Solid Core](#7-what-survives--the-solid-core)
8. [What Was Retracted](#8-what-was-retracted)
9. [The Honest State of the Decipherment](#9-the-honest-state-of-the-decipherment)
10. [Path Forward](#10-path-forward)

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

## 3. Phase 11: The Diachronic Prior (INVALIDATED by the corpus correction)

This avenue used a **data dimension** (time) rather than a scoring hypothesis, and initially appeared to be the only positive finding. **It was invalidated by the corpus correction.**

### The original finding (now known to be an artifact)

Signs attested in BOTH MM (~1700 BCE) and LM (~1450 BCE) periods appeared 2× more likely CONFIRMED:

| Sign set | % CONFIRMED (old, corrupted corpus) | % CONFIRMED (corrected corpus) |
|----------|--------------------------------------|--------------------------------|
| Shared (MM→LM persistent) | **67%** (28/42) | 58% (22/38) |
| LM-only | **33%** (26/78) | 55% (22/40) |
| Fisher exact p | 0.0003 | **0.1748 (NOT significant)** |
| Oracle LOO | 1.21× lift | **0.91× (below baseline)** |

### Why it failed

The gap between shared and LM-only confirmed rates **collapsed** on corrected data (58% vs 55%). The apparent 2× enrichment was inflated by the corrupted sign frequencies (AB 85, AB 26, AB 51 etc. were massively over-attributed, distorting which signs appeared "persistent"). On the corrected corpus, persistence does NOT predict confirmation.

**Verdict: INVALIDATED — an artifact of the transcription bias, not a real signal.**

---

## 4. The Corpus Correction (the key event)

**144 Unicode→Bennett mapping errors** were found and fixed (verified against the Unicode standard names list and GORILA readings):

| Sign | Old (corrupted) | Corrected |
|------|-----------------|-----------|
| AB 85 | 274 occurrences | **8** (was a mis-mapped A 301) |
| A 301 | 1 | **274** (a logogram) |
| AB 26 | 193 | → AB 28: 193 |
| AB 51 | 165 | → AB 59: 165 |
| AB 46 | 48 | → AB 54 |
| AB 49 | 169 | → AB 57 |

- Re-ingested all 1,720 inscriptions; DB now has correct sign types (10,084 syllabograms, 742 logograms, 101 fractions, 87 metrical, 4 numerals).
- IOZa2 now reads AB 08 AB 59 AB 28 AB 54 AB 57 (= A-TA-I-*301-WA-JA, matching GORILA).

**Invalidated by the correction:** diachronic prior, misvalued-sign flags (AB 16/60/80), AB 85 word-divider, V-link cohesion (2.2×→1.18×), AB 82↔LIVESTOCK.

### The Grid Purge (second correction layer)

The grid itself contained **69 phantom entries** — signs with no valid codepoint:
- 19 phantom CONFIRMED: AB 32 (i, 67), AB 68 (ro, 41 — the old "Phase 7 resolution", VOID), AB 36 (jo, 59), AB 12/14/15/18/22F/33/35/43/52/62/63/64/92/96/112/113
- 50 phantom UNCERTAIN: all AB 100-137 (their codepoints are A 300+ logograms) + rare AB 19/21F/42/88-99

The honest grid is **69 real signs: 58 CONFIRMED + 11 UNCERTAIN** (`expanded_grid_purged.csv`).
**AB 41 (si)** is the most frequent UNCERTAIN sign (240 occurrences) and the key open target.

---

## 5. The Libation Formula Recovery

On the corrected corpus, the **real libation formula** became accessible:

```
A-TA-I-*301-WA-JA · JA-DI-KI-TU · JA-SA-SA-RA-ME · U-NA-KA-NA-SI ·
I-PI-NA-MA · SI-RU-TE · TA-NA-RA-TE-U-TI-NU · I
```

- ja-sa-sa-ra-me: 9 inscriptions; u-na-ka-na-si: 6; si-ru-te: 7
- IOZa9 = PKZa27 (identical 10-sign texts)
- **di-ki-te-te** at Palaikastro (PKZa8/11/12/15) matches published JA-DI-KI-TE-TE-DU-PU; **di-ki-tu-ja** at Iouktas
- **ja-** prefix 3.4× enriched in libations; **-me** suffix on ja-sa-sa-ra-me and i-da-ki-sa-ri-me (ZA21b)
- **Phonetic test: the formula is phonetically inert** — fixed sign strings, values already known (LB-transfer). Cannot cascade into new values.

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
| Misvalued signs AB 16/60/80 | ✅ Supported → ❌ INVALIDATED by correction (not anomalous on corrected data) |
| Agglutinative morphology | ✅ Supported (weakly) |
| Avenue 1: AB 85 word divider | ❌ Retracted (was mis-mapped A 301) |
| Avenue 2: AB 82↔LIVESTOCK | ❌ Retracted (circular) |
| "78 anchors" | ⚠️ Overstated → 77 CONFIRMED, 19 with value `?`, 17/77 ≥70, refined grid confirms 44 |
| "Tyrsenian best fit" | ⚠️ Overstated → Anatolian IE #1, Hurro-Urartian #2, Tyrsenian #3, ALL inconclusive |
| AB 01/38/50 high-confidence | ⚠️ Downgraded → UNCERTAIN in refined grid (LB/CM conflicts) |
| **Diachronic prior** | ✅ → ❌ **INVALIDATED by correction** (p 0.0003→0.1748) |

---

## 5. What Survives — The Solid Core

The verified, non-circular findings after the correction + purge:

1. **The honest 69-sign grid** — 58 CONFIRMED + 11 UNCERTAIN, all with valid
   codepoints and corpus presence (`expanded_grid_purged.csv`).
2. **i-da (Ida) toponym** — 19 exact matches on corrected corpus. The strongest lexical anchor.
3. **The libation formula structure** — fixed recurring words (ja-sa-sa-ra-me, u-na-ka-na-si, si-ru-te) in fixed order; di-ki-te-te at Palaikastro matches published readings.
4. **Commodity associations** — AB 30↔LIVESTOCK and AB 28↔WINE survive Bonferroni (p=0.0001).
5. **The oracle harness** — the correct gate for any future scorer or new evidence.
6. **The negatives** — oracle (no scorer signal), cryptanalysis (frequency artifacts).

---

## 6. What Was Retracted

1. "AB 85 is the word divider" — AB 85 was a mis-mapped A 301 (274→8 occurrences); the interpretation is void.
2. "AB 82 ↔ LIVESTOCK" — circular (HIDE ligature encoding in PH10).
3. "Tyrsenian is the best structural fit" — no family distinguished (Anatolian and Hurro-Urartian rank higher).
4. "78 anchors" — overstated; the reliable set is ~58 values, ~17 high-confidence.
5. "Beam search is next" (10b report) — superseded by the oracle: no search can help an objective with no signal.
6. "The diachronic prior" — INVALIDATED by the correction (was an artifact of corrupted frequencies).
7. "Misvalued signs AB 16/60/80" — INVALIDATED by the correction (not anomalous on corrected data).
8. "The libation formula 5-part structure" (first version) — was an artifact of the mis-transcription; the real formula is different and now recovered.

---

## 7. The Honest State of the Decipherment

The computational avenues are **exhausted**, and the correction revealed that even the apparent positives were artifacts. After the correction:

- **Every positive finding built on the corrupted corpus is invalidated** (diachronic prior, misvalued signs, AB 85, V-link cohesion, AB 82↔LIVESTOCK).
- **What survives**: i-da, the negatives, and the formula structure.
- **The libation formula is real but phonetically inert** — it confirms the corpus and gives fixed word anchors, but cannot cascade into new phonetic values.

**The fundamental bottleneck is unchanged:** 11K tokens of formulaic administrative text, no bilingual anchor, no independent phonetic evidence. Every statistical and grammatical method is capped by this ceiling.

---

## 8. Path Forward

1. **New data is the only known lever.** New inscriptions from ongoing Minoan excavations, better GORILA TEI coverage, or a bilingual find. The oracle harness is the correct gate for any new evidence.
2. **The libation formula is the best existing asset.** Its structure is mapped (fixed words, deity-root slots, site-specific forms). Any new inscription from Iouktas/Palaikastro/Syme could extend it.
3. **The corpus correction should be propagated.** Any future work must use the corrected mapping (verified against Unicode).
4. **The oracle is the gate.** Any new scorer, new evidence, or new method must pass the oracle before being trusted.

---

*Phase 10–11 — the Ventris endgame was attempted, tested honestly, and failed. The corpus correction (144 mapping errors) then invalidated most apparent positives but recovered the real libation formula. What survives is small but real: i-da, the negatives, and the formula structure. The corpus remains the ceiling.*

## Source Files

| File | Description |
|------|-------------|
| `pipeline/ventris/complete.py` | Grid completer + oracle ablation test |
| `pipeline/ventris/positional_oracle.py` | Avenue 1 (positional) |
| `pipeline/ventris/commodity_semantics.py` | Avenue 2 (commodity enrichment) |
| `pipeline/ventris/cryptanalysis.py` | Avenue 3 (cryptanalysis + nulls) |
| `pipeline/ventris/diachronic.py` | Avenue 6 (diachronic prior — invalidated) |
| `data/analysis/ventris/verification_audit.md` | Claims audit (retractions) |
| `data/analysis/ventris/corpus_correction.md` | The 144-mapping-error correction |
| `data/analysis/ventris/corrected_rerun_results.md` | Re-verification before/after |
| `data/analysis/ventris/libation_recovered.md` | The recovered libation formula |
| `data/analysis/ventris/formula_word_findings.md` | Formula word-level analysis |
| `data/analysis/ventris/formula_phonetic_test.md` | Formula phonetic test (negative) |
| `data/analysis/synthesis/avenues_11.md` | Phase 11 roadmap |
