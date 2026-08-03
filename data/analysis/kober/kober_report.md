# Kober-Style CV Grid Reconstruction — Report

## Phase 7, Approach 4 of 5: Purely Positional Evidence

**Date:** 2025-08-03  
**Analyst:** Marshal (kober-clustering)  
**Key Question:** Do Kober tripling patterns independently confirm or contradict Phase 4 ML predictions for the 94 UNCERTAIN syllabograms?

---

## 1. Methodology

Alice Kober (1945–1948) discovered that Linear B syllabograms form a CV grid where signs sharing a consonant occur before the same following sign, and signs sharing a vowel occur after the same preceding sign. This "tripling" method operates without any phonetic assumptions — it is pure distributional analysis. We applied this to Linear A.

### 1.1 Positional Grid (positional_grid.py)

- Load positional profiles for all signs from `positional_profiles.csv`
- Filter to 54 UNCERTAIN signs with ≥5 occurrences
- Cluster by [initial, medial, final] fraction vectors using K-means (k=5)
- Within each cluster, signs share positional behaviour → candidates for sharing articulatory features
- Compare cluster assignments with Phase 4 ML-predicted transliterations

### 1.2 Triple Detection (triple_detection.py)

- Extract all adjacent sign pairs (bigram frames) from `lineara_full.db` → 777 distinct bigrams (≥2 occurrences each)
- Build C-links: signs X and Z that share the same following sign Y → consonant candidates
- Build V-links: signs Y and W that share the same preceding sign X → vowel candidates
- Find complete triangles: S1↔S2 (C-linked), S2↔S3 (V-linked), S1↔S3 (both C- and V-linked)
- Filter: require ≥2 common frame partners per link, ≥2 UNCERTAIN members per triple
- Annotate with ML predictions and check CV pattern consistency

---

## 2. Results

### 2.1 Positional Grid Reconstruction

5 positional clusters identified among 54 UNCERTAIN signs:

| Cluster | Label | Role | n | init | med | fin |
|---------|-------|------|---|------|-----|-----|
| 0 | neutral | neutral-series | 5 | .069 | .622 | .309 |
| 1 | medial-dominant | medial-series | 23 | .108 | .765 | .127 |
| 2 | neutral | neutral-series | 10 | .231 | .544 | .226 |
| 3 | boundary-flexible | consonant-initial-series | 12 | .419 | .143 | .438 |
| 4 | medial-dominant | medial-series | 4 | .003 | .970 | .026 |

**Key observations:**

- **Cluster 3** (boundary-flexible) is the most interpretable: signs here are split between initial and final positions with almost no medial use. This is consistent with both consonant-initial prefixes and vowel-final suffixes. Members include AB 02 (ro), AB 60 (ra), AB 62 (pte/ta), AB 66 (ta), AB 80 (ma), AB 85 (au/?).
- **Cluster 1** (medial-dominant, 73-83% medial) contains the largest group — signs that predominantly appear inside texts. This is the default position for most syllabograms and doesn't strongly constrain phonetic value.
- **Cluster 4** (97% medial) contains 4 signs almost never at boundaries: AB 45 (de?), AB 58 (su?), AB 93, AB 96 — these may be infixes, connectors, or logograms.
- **40 UNCERTAIN signs lack positional profiles** — they occur fewer than 5 times in the corpus.

**ML-to-cluster comparison:** All 54 UNCERTAIN signs show no positional-phonetic contradiction. However, this is a weak test — it only checks whether initial-dominant signs have CV values (they all do, because most predictions are CV).

### 2.2 Triple Patterns

- **3,503 frame links** (1,873 C-links, 1,630 V-links)
- **7,305 complete triangles** detected (≥2 UNCERTAIN members, ≥2 common frame partners)
- Of these, **2,080** have all three members UNCERTAIN

**Top triples by sign frequency:**

| Triple | Signs | ML Predictions | UNCERTAIN count |
|--------|-------|----------------|-----------------|
| 11845 | AB 62—AB 85—AB 66 | ta/au/ta | 3/3 |
| 9610 | AB 36—AB 62—AB 66 | jo/ta/ta | 3/3 |
| 11843 | AB 62—AB 85—AB 36 | ta/au/jo | 3/3 |
| 1016 | AB 02—AB 62—AB 66 | ro/ta/ta | 3/3 |
| 237 | AB 01—AB 62—AB 66 | da/ta/ta | 3/3 |

AB 62 (pte/ta, 437 occurrences) and AB 66 (ta?, 461 occurrences) are the most frequent UNCERTAIN signs and appear together in many triples. This is expected — they're the most connected nodes in the bigram network.

### 2.3 ML Consistency Analysis

Of the 2,080 all-UNCERTAIN triples:

- **515 (24.8%)** show consonant or vowel sharing consistent with ML predictions
- **1,565 (75.2%)** do not

**Interpretation:** The Kober patterns define structural groups based purely on distribution. The ML predictions are derived from visual similarity (neural embeddings), Linear B cognates, Cypro-Minoan triangulation, and grid confidence. These two signal sources are largely independent.

When they agree (24.8% of triples), it's weak corroboration — both methods independently point to the same structural relationship. When they disagree (75.2%), several explanations are possible:

1. **The Kober grouping is structural but non-phonetic:** Signs may share distributional patterns for morphological or syntactic reasons, not phonological ones.
2. **The ML prediction is wrong:** One or more sign values may be misassigned.
3. **Linear A's phonology differs enough from Linear B** that the C-link/V-link inference doesn't carry over directly (e.g., if Linear A has CVC signs or complex clusters).
4. **Small corpus noise:** With 11K total sign occurrences, some bigram patterns may be artifacts of specific textual formulas.

---

## 3. Answering the Key Question

**Do Kober patterns independently confirm or contradict Phase 4 ML predictions?**

**Answer: Neither strongly, but the patterns provide a structural check that constrains ML uncertainty.**

The Kober method does not "confirm" ML predictions — 75% of triples are inconsistent. Nor does it "contradict" them directly — distributional behaviour and phonetic value are different things, and the corpus is small.

What the Kober method *does* provide:

1. **A structural prior:** Signs clustered together should have related phonetic structure. ML predictions for signs in the same Kober cluster that don't share a consonant or vowel deserve higher uncertainty flags.

2. **Specific hypotheses to test:** When a triple is CV-consistent (e.g., AB 62/ta + AB 66/ta — both start with t-), this predicts that they share a consonant. When a triple is CV-inconsistent (e.g., AB 49/we + AB 62/ta — no shared element), it flags one or both values as suspect.

3. **The consonant-initial series (Cluster 3):** AB 02, AB 60, AB 62, AB 66, AB 80, AB 85 are distributionally similar (boundary-flexible). Their ML predictions (ro, ra, ta, ta, ma, au) show partial consonantal coherence: ra/ro share r-, ta/ta share t-, but ma and au don't share with either. This suggests either:
   - Multiple consonant series are conflated in this cluster, OR
   - Some of these ML values are wrong

---

## 4. Limitations

1. **No word-level data:** The DB has no word segmentation. We used inscription-internal adjacency, which spans word boundaries. This dilutes the Kober method, which relies on *within-word* adjacency.

2. **Small corpus:** 11K sign occurrences and 1,719 inscriptions. Statistical power is limited, especially for rare signs (40 UNCERTAIN signs have <5 occurrences).

3. **No phonetic assumptions ≠ no phonetic information:** The method is structural, but interpreting it requires assuming the CV grid structure is present — which may not be fully true for Linear A.

4. **Multiple readings:** Some signs may have multiple phonetic values depending on context (polyvalent signs), which would break the simple C-link/V-link model.

---

## 5. Recommendations

1. **Re-run with word boundaries:** Implement word segmentation first, then apply Kober tripling within words only. This would dramatically reduce noise.

2. **Flag ML predictions contradicted by Kober structure:** The 1,565 inconsistent triples represent specific testable hypotheses. Signs that appear in many inconsistent triples with high-confidence ML values deserve re-examination.

3. **Cross-reference with positional clusters:** The 12 signs in Cluster 3 (boundary-flexible) are prime targets for targeted phonetic investigation — they have the most distinctive distributional behaviour.

4. **Use the Kober grid as a Bayesian prior:** When combining evidence sources for sign values, weight Kober-consistent predictions higher than Kober-inconsistent ones.

---

## 6. Output Files

| File | Description |
|------|-------------|
| `data/analysis/kober/positional_clusters.csv` | 5 K-means clusters with centroid descriptions |
| `data/analysis/kober/grid_series.csv` | 54 UNCERTAIN signs with cluster membership |
| `data/analysis/kober/cluster_members.csv` | Per-sign cluster assignment + ML comparison |
| `data/analysis/kober/frame_links.csv` | 3,503 C-links and V-links from bigram frames |
| `data/analysis/kober/triple_patterns.csv` | 7,305 complete triples with ML annotations |
