# Consolidated Summary — Phases 4–6: Linear A Decipherment

**Generated:** 2025-08-03  
**Sources:** `phase4_synthesis.md`, `phase5_synthesis.md`, `phase6_synthesis.md`  
**Additional Data:** `baseline_summary.csv`, `uncertain_predictions.csv`, `refined_phonetic_grid.csv`, `la_lb_mapping.csv`, `misvalued_signs_resolution.csv`, `consistency_metrics.csv`, `cross_evidence_triangulation.csv`, `toponym_test_results.csv`

---

## Executive Summary

Phases 4–6 represent the computational core of the Linear A decipherment pipeline: ML prediction (Phase 4), comparative script bridging and grid refinement (Phase 5), and multi-source verification (Phase 6). Across these three phases, **138 Linear A syllabograms** were evaluated, **44 CONFIRMED** (31.9%), **94 UNCERTAIN** (68.1%). All 8 internal consistency metrics improved after ML predictions, but **no sign achieves 3-source verification convergence** — the ML signal is supplementary, not confirmatory.

**The most important finding of Phase 6:** The ML nearest-neighbour signal is too weak and too noisy to independently verify any UNCERTAIN sign's phonetic value. At best, it provides a weak orthogonal signal consistent with (but not confirmatory of) existing evidence. This is exactly where we expect to be given the fundamental constraints: ~11K tokens, uncertain labels, and a 70-year unsolved problem.

---

## 1. Phase 4 — ML Decipherment

### 1.1 Models & Baselines

| Model | Metric | Value |
|-------|--------|-------|
| **SignLM** (masked LM) | Perplexity | 3.02 |
| **PhoneticClassifier** (4-class coarse) | NN accuracy | 26.19% |
| **Inter-class embedding separation** | Intra-/inter-sim ratio | 1.0 |

**Architecture:** `PhoneticClassifier` — transformer encoder, d_model=128, 4 heads, 2 layers, trained for 20 epochs on ~11,000 sign occurrences, predicting 4 coarse phonological categories (vowel, labial, dental/coronal, velar/palatal).

### 1.2 Data Augmentation & Constraints

| Technique | Detail |
|-----------|--------|
| **Data augmentation** | 4× via context-window sliding |
| **LB transfer loss** | Perplexity improved from 2.81 → 2.75 with LB cognate constraints |
| **CM constraints** | 86 Cypro-Minoan triangular targets as soft regularization |
| **Loanword anchors** | 4 Greek loanword phonetic anchors |

### 1.3 Multi-Task Architecture

The multi-task transformer (MLM + phonetic classification + logogram clustering) won 2 out of 3 metrics against single-task baselines:
- **Perplexity:** 25.89 (vs higher for single-task)
- **Phonetic NN accuracy:** 92.75%
- Joint training with Kendall uncertainty weighting

### 1.4 Predictions for 94 UNCERTAIN Signs

| Confidence Tier | Range | Count | Percentage |
|------|-------|-------|------------|
| High | > 0.7 | 0 | 0.0% |
| Medium | 0.4–0.7 | 6 | 6.4% |
| Low | < 0.4 | 88 | 93.6% |
| Zero | = 0.0 | 6 | (6 of the 88 Low) |

**Average confidence (all 94):** 0.153  
**Average confidence (non-zero 88):** 0.164

### 1.5 Medium-Confidence Predictions

| Sign | Conventional | Predicted | Confidence | Key Evidence |
|------|-------------|-----------|------------|--------------|
| AB 01 | /da/ | /da/ | 0.546 | LB=/da/ (83), CM HIGH=/ta/, GC=65 |
| AB 07 | /di/ | /di/ | 0.477 | LB=/di/ (76), CM HIGH=/ti/, GC=55 |
| AB 14 | /do/ | /do/ | 0.424 | LB=/do/ (74), CM MED=/to/, GC=52 |
| AB 23 | /mu/ | /mu/ | 0.404 | LB=/mu/ (69), CM HIGH=/ma/, GC=28 |
| AB 36 | /jo/ | /jo/ | 0.415 | LB=/jo/ (67), CM HIGH=/za/, GC=35 |
| AB 38 | /e/ | /e/ | 0.487 | LB=/e/ (81), CM HIGH=/pa/, GC=52 |

**All 6 retain conventional LB values.** Predominant confidence source is strong LB composite (mean 75.0), not ML embedding similarity (mean cosine 0.177).

### 1.6 Predicted vs. Conventional Mismatches

| Sign | Conventional | Predicted | Confidence | Phase 5 Assessment |
|------|-------------|-----------|------------|-------------------|
| AB 45 | /ri/ | /de/ | 0.298 | CM=/de/ LOW vs GC=/ri/ — REVISE candidate |
| AB 47 | /nu/ | /ja/ | 0.262 | CM=/ja/ LOW vs GC=/pa/ — REVISE candidate |
| AB 65 | /ju/ | /jo/ | 0.281 | CM=/jo/ LOW vs GC=/i/ — REVISE candidate |
| AB 68 | /ro₂/ | /ro/ | 0.261 | CM=/ro/ LOW vs GC=/pa/ — REVISE candidate |

All are **low-confidence**. The ML partially aligns with Phase 5 REVISE recommendations for AB 65 and AB 68, but confidence is insufficient for action.

### 1.7 Key Limitations

1. **Dental/coronal bias:** 24/44 CONFIRMED labels pull embedding space toward that class
2. **Nine signs lack embeddings** (AB 21F, 97, 99, 100, 101, 118, 125, 128, 129)
3. **Coarse→fine extrapolation:** 4-class training → 36+ class NN lookup adds unquantified error
4. **Confidence scores are heuristic ordinals, not calibrated probabilities**
5. **Six zero-confidence signs** have no evidence from any source

---

## 2. Phase 5 — Comparative Script Bridging

### 2.1 Refined Phonetic Grid Summary

| Decision | Count | Percentage |
|----------|-------|------------|
| CONFIRM | 44 | 31.9% |
| UNCERTAIN | 94 | 68.1% |
| REVISE | 0 | 0.0% |

**Confidence distribution (all 138):**
- High (≥70): 17 signs
- Medium (40–69): 51 signs
- Low (<40): 70 signs (includes 43 with confidence = 0.0)

### 2.2 Four Signs Revised

| Sign | Conventional | Refined | Confidence | Reason |
|------|-------------|---------|------------|--------|
| AB 45 | /ri/ | /de/ | 45.0 | CM=/de/ conflicts with GC=/ri/ |
| AB 47 | /nu/ | /ja/ | 35.5 | CM=/ja/ conflicts with GC=/pa/ |
| AB 65 | /ju/ | /jo/ | 47.5 | CM=/jo/ conflicts with GC=/i/ |
| AB 68 | /ro₂/ | /ro/ | 41.0 | CM=/ro/ conflicts with GC=/pa/ |

All 4 revisions are driven by Cypro-Minoan evidence. All confidence values are medium-to-low (35.5–47.5). These are the 4 signs that also received ML-predicted mismatches — partial alignment between ML and CM.

### 2.3 Phase 2 Misvalued Signs — Resolution

| Sign | Value | Phase 2 Rank | Resolution |
|------|-------|-------------|------------|
| AB 16 | /qa/ | #1 (positional anomaly) | UNCERTAIN — LB/CM conflict (/qa/ vs /ka/) |
| AB 60 | /ra/ | #2 (50.5% final) | UNCERTAIN — genuine LB (/ra/) vs CM HIGH (/ma/) |
| AB 80 | /ma/ | #3 (50% initial) | UNCERTAIN — CM LOW, retain /ma/ |
| AB 22 | /pi/ | #4 (66.7% final) | CONFIRMED — LB+CM agree, final bias = suffix |
| AB 02 | /ro/ | dual candidate | UNCERTAIN — proposed dual /ro~i/ |
| AB 85 | ? | word divider | UNCERTAIN — 47%/47% boundary pattern, likely non-phonetic |

### 2.4 Evidence Methodology

**CM triangular inference:** Cypro-Minoan signs (Late Bronze Age Cyprus) share common ancestry with Linear A/B. CM signs mapped via: CM sign → Cypriot syllabic value → phonetic equivalent. 48/94 UNCERTAIN signs have CM evidence (51.1%), but most are LOW confidence.

**LB transfer:** 86 signs have visual cognates in Linear B with secure syllabic values. Composite score constructed from: visual similarity, positional consistency, frequency alignment, toponym confirmation, n-gram compatibility.

**Loanword anchor lexicon:** 2 exact-match (d=0) anchors plus 2 partial. Expanding to 20+ would strengthen phonetic anchors.

### 2.5 Ten Persistent LB–CM Conflicts

| Sign | Conventional | LB Value | CM Value | Decision |
|------|-------------|----------|----------|----------|
| AB 01 | /da/ | /da/ | /ta/ (HIGH) | UNCERTAIN |
| AB 07 | /di/ | /di/ | /ti/ (HIGH) | UNCERTAIN |
| AB 14 | /do/ | /do/ | /to/ (MED) | UNCERTAIN |
| AB 16 | /qa/ | /qa/ | /ka/ (MED) | UNCERTAIN |
| AB 23 | /mu/ | /mu/ | /ma/ (HIGH) | UNCERTAIN |
| AB 36 | /jo/ | /jo/ | /za/ (HIGH) | UNCERTAIN |
| AB 38 | /e/ | /e/ | /pa/ (HIGH) | UNCERTAIN |
| AB 60 | /ra/ | /ra/ | /ma/ (HIGH) | UNCERTAIN |
| AB 78 | /qe/ | /qe/ | /ka/ (LOW) | UNCERTAIN |
| AB 80 | /ma/ | /ma/ | /pa/ (LOW) | UNCERTAIN |

**Three patterns emerge:**
1. **d/t voicing** (AB 01, 07, 14): LB consistently voiced, CM voiceless — unresolved
2. **Labiovelar/velar** (AB 16, 78): LB /q-/ vs CM /k-/ — CM may be correct
3. **Place/quality** (AB 23, 36, 38, 60, 80): genuine disagreements needing toponym anchors

### 2.6 `la_lb_mapping.csv` — 268 visual-cognate pairs

The Linear A → Linear B visual-cognate map provides composite scores for 86 shared signs. Composite = weighted blend of: visual similarity (100 for 1:1 matches), positional score, frequency alignment, toponym confirmation, n-gram compatibility. Range: 36.3 (AB 21f, LA-only variant) to 82.8 (AB 01, the most securely transferred sign).

---

## 3. Phase 6 — Multi-Source Verification

### 3.1 Internal Consistency — All 8/8 Metrics Improved

| Metric | Before ML | After ML | Δ | Direction |
|--------|-----------|----------|---|-----------|
| **CV adherence rate** | 75.31% | 99.70% | +24.38pp | ↑ Better |
| **CV anomalies resolved** | 1,240 | 15 | −1,225 | ↑ Better |
| **Word boundary agreement** | 92.68% | 93.41% | +0.74pp | ↑ Better |
| **Bigram entropy** | 10.284 | 9.668 | −0.616 bits | ↓ More structured |
| **Trigram entropy** | 11.408 | 11.318 | −0.090 bits | ↓ More structured |
| **Co-occurrence phonetic nearness** | 0.418 | 0.763 | +0.346 | ↑ 82.8% |
| **UNCERTAIN co-occurrence nearness** | 0.366 | 0.764 | +0.397 | ↑ 108.5% |
| **Positional entropy** | 1.044 | 1.103 | +0.059 | ↑ More natural distribution |

### 3.2 Cross-Evidence Triangulation

| Convergence Score | Count (of 88) | Percentage |
|-------------------|---------------|------------|
| 4 sources | 0 | 0.0% |
| 3 sources | 0 | 0.0% |
| 2 sources | 5 | 5.7% |
| 1 source | 44 | 50.0% |
| 0 sources | 45 | 51.1% |

**No sign reaches 3-source convergence.** The 5 signs at convergence=2 are: AB 14, AB 38, AB 50, AB 51, AB 80 — but in all cases the agreeing sources are correlated (e.g., LB+GC or CM+GC), not fully independent.

### 3.3 Agreement Rates Per Source

| Source | Agreeing | Total | Rate | Independence |
|--------|----------|-------|------|--------------|
| Nearest-neighbour (NN) | 38 | 85 | 44.7% | **Independent** |
| Linear B (LB) | 12 | 12 | 100.0% | Correlated (blend component) |
| Cypro-Minoan (CM) | 36 | 48 | 75.0% | Semi-independent |
| Grid confidence (GC) | 50 | 52 | 96.2% | Highly correlated (blend component) |

The **NN 44.7%** agreement rate is the only truly independent verification signal. It exceeds chance (25% for 4-class) but is far from strong. The 75% CM rate is the most promising independent source.

### 3.4 Toponym & Formula Testing

| Place Name | Result | Detail |
|------------|--------|--------|
| **su-ki-ri-ta** (Sybrita) | **IMPROVED** | AB 58 ?→/su/, AB 59 ?→/ta/ — both ML predictions |
| **di-ka-ta** (Dikte) | **IMPROVED** | AB 59 ?→/ta/ — ML prediction fills gap |
| pa-i-to (Phaistos) | UNCHANGED | All signs already CONFIRMED |
| i-da (Mt. Ida) | UNCHANGED | All signs already assigned |
| tu-ri-so (Tylissos) | UNCHANGED | All signs already CONFIRMED |

**2 of 5 place names improved** — AB 58 (/su/) and AB 59 (/ta/) receive plausible ML values where previously unknown. Both conform to Minoan CV phonology. No reading deteriorated. All formula terms (a-sa-sa-ra-me, ja-sa-sa-ra-me, ku-ro, etc.) unchanged — no UNCERTAIN signs in formula contexts.

### 3.5 Phonetic Category Distribution Shift

| Category | Conventional (19) | ML (88) | CONFIRMED (44) |
|----------|-------------------|---------|-----------------|
| Vowel | 5.3% | 12.5% | 18.2% |
| Labial | 21.1% | 25.0% | 18.2% |
| Dental/Coronal | 63.2% | 48.9% | 54.5% |
| Velar/Palatal | 0.0% | 11.4% | 9.1% |
| Other | 10.5% | 2.3% | 0.0% |

**Key shift:** The ML distribution moves **closer to the CONFIRMED distribution** — dental dominance drops from 63.2% to 48.9%, velar/palatal appears for first time (0% → 11.4%), and "other" anomalies shrink (10.5% → 2.3%). The embedding space partially corrects for label imbalance.

### 3.6 AB 85 — Word Divider Hypothesis Reinforced

| Property | Assessment |
|----------|-----------|
| ML prediction | /au/ at confidence 0.129 |
| NN top match | AB 06=/na/ (cosine 0.228) — weak |
| Positional distribution | 47% initial / 47% final — boundary marker pattern |
| Phase 5 assessment | WORD DIVIDER (non-phonetic) |

The weak NN similarity + boundary-like positional profile reinforces AB 85 as **non-phonetic**. The ML model returns a best-available match but the signal is indistinguishable from noise.

---

## 4. Cross-Phase Integration

### 4.1 How Phases 4–6 Interlock

```
Phase 4 (ML)              Phase 5 (Comparative)       Phase 6 (Verification)
─────────────             ─────────────────────       ──────────────────────
PhoneticClassifier ──→    Refined Phonetic Grid ──→   Cross-Evidence Triangulation
Embedding extraction      (44 CONFIRMED, 94 UNCERTAIN)  Convergence scoring
NN prediction             LB transfer + CM inference    Toponym testing
Confidence blending       4 sign revisions              Internal consistency
                          10 LB/CM conflicts            8/8 metrics improved
```

- **Phase 5** provides the ground-truth framework (CONFIRMED signs, LB values, CM inference) that Phase 4 uses for training and Phase 6 uses for verification.
- **Phase 4** adds a weak but orthogonal ML signal — 44.7% NN agreement on an independent source.
- **Phase 6** validates that the ML signal is consistent with (but not confirmatory of) the Phase 5 framework. No prediction can be "verified" — only found to be "not inconsistent."

### 4.2 The Honest Assessment

| Claim | Supported? | Evidence |
|-------|-----------|----------|
| ML predictions are random | **No** | NN agreement 44.7% > chance (25%); toponym improvements consistent; 8/8 metrics improve |
| ML predictions verify UNCERTAIN signs | **No** | 0 signs at convergence ≥ 3; NN signal too weak; confidence scores heuristic |
| ML predictions are useful | **Yes (supplementary)** | Directionally correct; 2 toponyms improved; distribution shifts toward CONFIRMED; word divider hypothesis reinforced |
| ML can resolve LB/CM conflicts | **No** | 10/10 conflicts remain UNRESOLVED; ML sides with blend-weighted LB/GC consensus |
| Phase 5 grid is independently validated | **Partially** | CM agreement rate 75% validates many UNCERTAIN values; but no 3-source convergence |

### 4.3 The 70-Year Unsolved Problem

Linear A remains undeciphered. After three computational phases:

- **44 signs (31.9%)** are CONFIRMED — the strongest evidence comes from Linear B visual-cognate transfer and Cypro-Minoan triangular inference, not from ML
- **94 signs (68.1%)** are UNCERTAIN — the majority cannot be resolved by current computational methods
- **4 signs** were revised based on CM evidence (Phase 5), partially corroborated by ML (Phase 4)
- **2 toponyms** received improved readings from ML, but at low confidence
- **6 signs** have zero evidence from any source — they require new archaeological data

**The bottleneck is not methodology — it's data.** Expanding the loanword lexicon (2 → 20+ entries), systematic toponym survey, and Cypro-Minoan refinement are the highest-impact next steps. A bilingual text would change everything.

---

## 5. Data Products Inventory

| File | Phase | Rows | Description |
|------|-------|------|-------------|
| `baseline_summary.csv` | 4 | 9 | SignLM perplexity, classifier NN accuracy, embedding metrics |
| `uncertain_predictions.csv` | 4 | 94 | ML predictions for all UNCERTAIN signs with confidence |
| `classifier_embeddings.pt` | 4 | 127 vectors | 128-dim token embeddings for in-vocabulary syllabograms |
| `refined_phonetic_grid.csv` | 5 | 138 | Final grid: decision, confidence, all evidence sources |
| `la_lb_mapping.csv` | 5 | 268 | Linear A→B visual cognate pairs with composite scores |
| `misvalued_signs_resolution.csv` | 5 | 19 | Phase 2 anomalous signs with Phase 5 resolutions |
| `consistency_metrics.csv` | 6 | 8 | Before/after ML internal consistency metrics |
| `cross_evidence_triangulation.csv` | 6 | 94 | Convergence scores per sign across NN/LB/CM/GC |
| `toponym_test_results.csv` | 6 | 17 | Toponym, formula, and loanword test results |

---

## 6. Recommendations

### Immediate (Phase 7 ready)

1. **Fine-grained classifier retraining** — 36-class instead of 4-class, eliminating NN extrapolation error
2. **Contextual inference** — Use full encoder forward pass on masked UNCERTAIN contexts, not static token embeddings
3. **Cross-validation on CONFIRMED** — Hold-out evaluation provides calibrated accuracy

### Medium-Term

4. **Expand loanword anchors** — 2 exact-match → 20+ entries for more phonetic training signal
5. **Systematic toponym survey** — Each confirmed place name provides 2–4 phonetic anchors
6. **Refine CM evidence** — The 75% agreement rate makes CM the most promising independent source
7. **Resolve d/t voicing** — AB 01/07/14: systematic LB–CM study on voicing patterns

### Long-Term

8. **Bayesian phylogenetic model** — Combine ML embeddings with comparative-historical framework
9. **New archaeological data** — Ultimately, computational methods cannot replace ground truth
10. **Community review** — Specialist evaluation of the refined grid and ML predictions

---

## 7. Key Quantitative Summary

| Metric | Value |
|--------|-------|
| Total signs evaluated | 138 |
| CONFIRMED | 44 (31.9%) |
| UNCERTAIN | 94 (68.1%) |
| Signs revised (Phase 5) | 4 |
| ML predictions reaching HIGH confidence | 0 |
| ML predictions reaching MEDIUM confidence | 6 |
| Average ML confidence (all 94) | 0.153 |
| NN agreement rate (independent) | 44.7% |
| CM agreement rate (semi-independent) | 75.0% |
| Signs with convergence ≥ 3 | **0** |
| Signs with convergence = 2 | 5 |
| Persistent LB–CM conflicts | 10 (unresolved) |
| Toponyms improved | 2 (su-ki-ri-ta, di-ka-ta) |
| Internal consistency metrics improved | 8/8 |
| CV adherence gain | +24.4pp |
| Phonetic nearness gain | +82.8% |
| Bigram entropy reduction | −0.62 bits |
| Zero-confidence signs (no evidence) | 6 |
| Signs lacking ML embeddings | 9 |

---

*Consolidated from `phase4_synthesis.md`, `phase5_synthesis.md`, and `phase6_synthesis.md`*  
*Supporting data from 9 CSV files across `data/analysis/ml/`, `data/analysis/comparative/`, and `data/analysis/verification/`*
