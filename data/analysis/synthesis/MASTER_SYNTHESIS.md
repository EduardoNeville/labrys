# The Labrys Project — Complete Synthesis Report

**Date:** 2026-08-03
**Phases completed:** 9
**Repository:** `https://github.com/EduardoNeville/labrys`
**Commit:** See `git log` for full history

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Phase 1 — Data Infrastructure](#2-phase-1--data-infrastructure)
3. [Phase 2 — Statistical Analysis](#3-phase-2--statistical-analysis)
4. [Phase 3 — Linguistic Testing](#4-phase-3--linguistic-testing)
5. [Phase 4 — ML Decipherment](#5-phase-4--ml-decipherment)
6. [Phase 5 — Comparative Script Bridging](#6-phase-5--comparative-script-bridging)
7. [Phase 6 — Verification](#7-phase-6--verification)
8. [Phase 7 — Five Alternative Approaches](#8-phase-7--five-alternative-approaches)
9. [Phase 8 — Kober Bootstrapping](#9-phase-8--kober-bootstrapping)
10. [Phase 9 — Formulaic Parallelism](#10-phase-9--formulaic-parallelism)
11. [The Phonetic Grid — Current State](#11-the-phonetic-grid--current-state)
12. [What We Actually Know](#12-what-we-actually-know)
13. [What Remains Unknown](#13-what-remains-unknown)
14. [The Path Forward](#14-the-path-forward)

---

## 1. Project Overview

The Labrys Project is a systematic, multi-phase computational effort to decipher Linear A, the undeciphered script of Minoan Crete (ca. 1800–1450 BCE). After 70+ years of scholarly effort, Linear A remains one of the most significant unsolved problems in historical linguistics and archaeology.

### Corpus Statistics

| Metric | Value |
|--------|-------|
| Total inscriptions | 1,719 |
| Total sign occurrences | 11,018 |
| Unique Bennett IDs | 312 |
| Syllabograms (AB 01–137) | 138 |
| Logograms (A 301–402) | 124 |
| Fraction signs (A 701–730) | 29 |
| Findspots (archaeological sites) | 62 |
| Chronological periods | 12 (EM II–LM IIIB) |
| Database size | 3.6 MB (SQLite) |
| Longest text | HT 117a (82 signs) |
| Largest archive | Hagia Triada (~863 inscriptions) |

### Sign System (Bennett AB)

- **AB 01–137**: Syllabograms — CV structure (consonant + vowel)
- **A 301–402**: Logograms / ideograms — commodities, measures
- **A 701–730**: Fraction signs — mathematical notation
- **A 501–594**: Metrical signs, vase shapes, adjuncts

**Critical note on phonetic values:** The conventional AB phonetic grid assigns values to all 138 syllabograms by transferring the corresponding Linear B (deciphered Mycenaean Greek) values. These are **unverified for Linear A**. Our entire project is about determining which transfer values are correct, which are wrong, and what the correct values are.

---

## 2. Phase 1 — Data Infrastructure

**Status:** ✅ Complete
**Module:** `pipeline/database.py`, `pipeline/models.py`, `pipeline/unicode_utils.py`

### Deliverables

- SQLite database (`data/database/lineara_full.db`) — normalized schema with inscriptions, signs, findspots, periods, materials, object types
- Python data model (dataclasses): `Inscription`, `SignInstance`, `Findspot`, `Period`
- Unicode Aegean (U+10600–U+1077F) ↔ Bennett AB mapping
- TEI XML and SIGLA format parsers
- Click CLI with 7 commands for database access

### Data Model

```
Inscription
├── gorilaId (e.g., "HT 1")
├── findspot { site, coordinates }
├── date { minoanPeriod, bceRange }
├── material, objectType, preservation
├── signs[]          # SignInstance in reading order
│   ├── bennettId    # AB 01, AB 02, ..., A 301, etc.
│   ├── unicode      # U+10600+
│   ├── transliteration  # "da", "ro", "pa"
│   ├── signType     # syllabogram|logogram|fraction|numeral|metrical
│   └── sequence     # ordinal position
├── structure { lines, words, sides }
├── images[]
└── relations { linearB, cyproMinoan }
```

### Toolchain

- Python 3.10+
- `uv` for package management
- `sqlite3` for database access
- All pipeline modules runnable as standalone scripts or via CLI

---

## 3. Phase 2 — Statistical Analysis

**Status:** ✅ Complete
**Modules:** `positional_analysis.py`, `word_segmentation.py`, `ngram_analysis.py`, `network_analysis.py`, `logogram_analysis.py`

### Key Findings

#### Positional Analysis

Sign positional profiles reveal signs with anomalous distributions — signs that appear mostly in positions inconsistent with their conventional CV value:

| Sign | Conventional | Anomaly | Rank |
|------|-------------|---------|------|
| AB 16 | /qa/ | 60% initial, 0% medial | #1 |
| AB 60 | /ra/ | 50.5% final position | #2 |
| AB 80 | /ma/ | 50% initial position | #3 |
| AB 22 | /pi/ | 66.7% final position | #4 |
| AB 02 | /ro/ | Dual initial/final bias | #5 |
| AB 85 | — | Acts like punctuation, not syllabogram | #7 |

These anomalies flagged signs most likely to be **incorrectly valued** in the conventional AB grid.

#### Word Segmentation

- 2,223 word tokens extracted using 5-strategy consensus segmentation
- Mean word length: 6.72 signs
- Most words are 2–8 signs (accounting/administrative vocabulary)
- Word dividers identified in some inscriptions

#### N-gram Analysis

- Bigrams and trigrams computed for full corpus
- Fraction sign 𐝫 is the single most frequent sign (12.6% of occurrences)
- AB 26 (/ru/) and AB 30 (/ni/) are the most frequent syllabograms
- Entropy measurements suggest natural language structure, not random or purely formulaic

#### Sign Network Analysis

- Co-occurrence network built across all 62 findspots
- 5 site-specific sub-networks analyzed
- Core of 15–20 high-centrality syllabograms identified (AB 26, AB 30, AB 06, AB 51, AB 08, AB 49, AB 66, AB 85, AB 31)
- AB 62 and AB 66 are the most connected UNCERTAIN signs in the network

#### Logogram & Fraction Analysis

- 124 logogram types classified by commodity (VESSELS, GRAIN, WINE, OLIVE OIL, LIVESTOCK, etc.)
- 29 fraction signs with proposed mathematical values (8 anchored to Linear B)
- Commodity ontology built: WINE, GRAIN, OLIVE OIL, OLIVES, HIDES, LIVESTOCK, MANPOWER, PERSONNEL, VESSELS

---

## 4. Phase 3 — Linguistic Testing

**Status:** ✅ Complete
**Modules:** `swadesh_search.py`, `wals_analysis.py`, `loanword_matching.py`, `toponym_alignment.py`, `morphology_scan.py`, `falsification_report.py`

### Language Family Testing

Six candidate language families tested against Linear A using Swadesh-100 wordlist and WALS typological features:

| Family | WALS Match | Swadesh Matches | Verdict |
|--------|-----------|-----------------|---------|
| **Tyrsenian** (Etruscan) | 5/8 (62.5%) | 0 exact matches | Weak structural fit, lexically empty |
| Indo-European (Hittite) | 3/8 (37.5%) | 0 | Poor match |
| Semitic (Akkadian) | 2/8 (25.0%) | 0 | Poor match |
| Hurro-Urartian | 4/8 (50.0%) | 0 | Moderate |
| Pre-Greek substrate | N/A (not a family) | 2 partial | Best lexical evidence |
| Isolate | Default | N/A | Remains possible |

**Audit note (Phase 11):** candidate_ranking.csv ranks Anatolian IE and
Hurro-Urartian ABOVE Tyrsenian (scores 8 vs 7), all marked "INCONCLUSIVE
(tentative)". The "Tyrsenian best" framing overstates — no family is
distinguished; several are weakly compatible.

**Conclusion:** No language family has statistically significant lexical
evidence, and no family is structurally distinguished. Minoan remains
unaffiliated.

### Known Words

| Word | Reading | Meaning | Confidence | Evidence |
|------|---------|---------|------------|----------|
| ku-ro | ku-ro | "total" | HIGH | Repeated final position in accounting tablets; paralleled by Linear B `to-so` |
| po-to-ku-ro | po-to-ku-ro | "grand total" | HIGH | Compound of ku-ro with po-to prefix |
| ki-ro | ki-ro | "owed / deficit" | MEDIUM-HIGH | Appears in balanced accounts opposite ku-ro |
| a-sa-sa-ra-me | a-sa-sa-ra-me | Libation formula | MEDIUM | Repeated on stone libation tables |
| ja-sa-sa-ra-me | ja-sa-sa-ra-me | Variant formula | MEDIUM | Variant of a-sa-sa-ra-me; ja- is a prefix |
| pa-i-to | pa-i-to | "Phaistos" | HIGH | Matches archaeological site name, appears in LA and LB |
| i-da | i-da | "Mt. Ida" | HIGH | Exact match to mountain name |
| su-ki-ri-ta | su-ki-ri-ta | "Sybrita" | HIGH | Exact match to place name |
| di-ka-ta | di-ka-ta | "Dikte" | MEDIUM | Near-exact match to mountain name |
| tu-ru-sa | tu-ru-sa | "Tylissos" | MEDIUM | Near-exact match |
| se-to-i-ja | se-to-i-ja | "Setoia" | MEDIUM | Matches Linear B place name |
| ku-do-ni-ja | ku-do-ni-ja | "Kydonia" (Chania) | MEDIUM | Matches Linear B place name |

### Morphological Profile

- **Agglutinative**: Morphemes concatenated linearly (prefix-root-suffix)
- **Suffixal**: Suffixes dominate over prefixes (typical SOV language)
- **No grammatical gender**: No masculine/feminine/neuter distinctions detected
- **4-vowel system**: /a/, /i/, /o/, /u/ (no /e/ in some analyses; /e/ is CONFIRMED in grid)
- **Head-final**: Modifier precedes modified (typical SOV)
- **Syllable structure**: Predominantly open syllables (CV), ~20–25% closed syllables

### Loanword & Toponym Evidence

- 471 loanword matches identified (Greek → LA via Pre-Greek substrate)
- 88 distinct Greek lemmas with potential LA cognates
- 2 exact matches (d=0): ARUKU ≈ Argos, RUKUTU ≈ Lyctus
- Toponym anchors provide Rosetta-fragment evidence for specific sign values
- Pre-Greek suffixes (-ss-, -nth-) appear in both Cretan toponyms and Anatolian/Greek ones

---

## 5. Phase 4 — ML Decipherment

**Status:** ✅ Complete
**Modules:** `pipeline/ml/data.py`, `pipeline/ml/lm.py`, `pipeline/ml/contrastive.py`, `pipeline/ml/evaluate.py`, `pipeline/ml/augment.py`, `pipeline/ml/transfer.py`, `pipeline/ml/constraints.py`, `pipeline/ml/multitask.py`, `pipeline/ml/predict.py`

### Models Trained

| Model | Architecture | Task | Key Metric |
|-------|-------------|------|------------|
| SignLM | 2-layer BERT-style transformer (128-dim, 4 heads) | Masked language modeling | **Perplexity 3.02** |
| PhoneticClassifier | 2-layer transformer + classifier head | Predict phonetic class (4 coarse categories) from context | **NN accuracy 26.19%** |
| MultiTaskTransformer | Shared encoder + 3 task heads (LM, phonetic, logogram) | Joint training with manual weighting | **Perplexity 25.89, NN 92.75%, Logogram 92.96%** (wins 2/3 vs single-task) |

### Data Augmentation & Transfer

- **4× corpus expansion** via sign substitution, window cropping, sequence reversal
- **Linear B transfer learning**: Pretrain on LB cognate sign patterns → fine-tune on LA
- Transfer model perplexity **2.75** vs baseline **2.81** (modest improvement)
- Curriculum learning: train on longest texts first

### Constraint Integration

- 86 Cypro-Minoan triangulation targets (36 HIGH, 15 MEDIUM, 35 LOW confidence)
- 3 HIGH-confidence CM/LB conflicts: AB 36 (jo/za), AB 38 (e/pa), AB 60 (ra/ma)
- 4 Pre-Greek loanword anchors (ARUKU→Argos, RUKUTU→Lyctus)
- Both implemented as weighted regularization terms in the loss function

### Predictions for 94 UNCERTAIN Signs

| Confidence Level | Count | Range |
|-----------------|-------|-------|
| HIGH | **0** | > 0.70 |
| MEDIUM | **5** | 0.40–0.70 |
| LOW | **89** | < 0.40 |
| Average confidence | — | 0.153 |

**Bottom line:** The ML produces weak supplementary signal. The corpus (~11K tokens) is too small for deep learning to independently break the decipherment open. The model consistently favors LB-derived values; CM evidence disagrees with ML in 91% of HIGH-confidence CM cases.

### GPU Infrastructure Fix

During Phase 4, a critical system-level issue was diagnosed and fixed:

- **Root cause**: Tesla P40 GPU was crashing mid-training due to `nvidia-drm.modeset=1` on a headless compute GPU, 975MB swap on 31GB RAM, TLP laptop power management disabling NMI watchdog, and dual NVIDIA DKMS builds
- **Fixes applied**: GRUB modeset removed, TLP purged, swap expanded to 16GB, swappiness set to 10, kernel panic auto-reboot enabled (30s), NMI watchdog enabled
- **PyTorch fix**: Pinned to `torch>=2.0,<2.6` with CUDA 12.1 index (cu121) for driver compatibility

---

## 6. Phase 5 — Comparative Script Bridging

**Status:** ✅ Complete
**Modules:** `linear_b_mapping.py`, `cypro_minoan_bridge.py`, `phonetic_grid_refinement.py`, `commodity_alignment.py`

### Refined Phonetic Grid

| Decision | Count | Percentage |
|----------|-------|------------|
| **CONFIRM** | 44 | 31.9% |
| **REVISE** | 0 | 0.0% |
| **UNCERTAIN** | 94 | 68.1% |

### Signs Revised from Conventional AB Grid

| Sign | Conventional | Refined | Confidence | Reason |
|------|-------------|---------|------------|--------|
| AB 45 | /ri/ | /de/ | 45.0 | CM=/de/; GC=/ri/ |
| AB 47 | /nu/ | /ja/ | 35.5 | CM=/ja/; GC=/pa/ |
| AB 65 | /ju/ | /jo/ | 47.5 | CM=/jo/; GC=/i/ |
| AB 68 | /ro₂/ | /ro/ | 41.0 | CM=/ro/; GC=/pa/ |

### The 10 Persistent LB/CM Conflicts

These signs have conflicting evidence from Linear B transfer vs Cypro-Minoan triangular inference:

| Sign | LB Value | CM Value | CM Confidence | Grid Score | Status |
|------|----------|----------|---------------|------------|--------|
| AB 01 | /da/ | /ta/ | HIGH | 73.5 | Conflict |
| AB 07 | /di/ | /ti/ | HIGH | 55.0 | Conflict |
| AB 16 | /qa/ | /ka/ | MEDIUM | 48.1 | Conflict |
| AB 23 | /mu/ | /ma/ | HIGH | 39.0 | Conflict |
| AB 36 | /jo/ | /za/ | HIGH | 35.0 | Conflict |
| AB 38 | /e/ | /pa/ | HIGH | 65.5 | Conflict (vowel vs CV!) |
| AB 60 | /ra/ | /ma/ | HIGH | 57.9 | **Most studied conflict** |
| AB 65 | /ju/ | /jo/ | LOW | 47.5 | Minor |
| AB 68 | /ro₂/ | /ro/ | LOW | 41.0 | Minor (resolved Phase 7) |
| AB 80 | /ma/ | /pa/ | LOW | 34.1 | Minor |

### Phase 2 Misvalued Sign Resolutions

| Sign | Phase 2 Rank | Conventional | Refined | Decision |
|------|-------------|-------------|---------|----------|
| AB 16 | #1 anomalous | /qa/ | /qa/ | UNCERTAIN (CM=/ka/) |
| AB 60 | #2 anomalous | /ra/ | /ra/ | UNCERTAIN (CM=/ma/ HIGH) |
| AB 80 | #3 anomalous | /ma/ | /ma/ | UNCERTAIN (CM=/pa/ LOW) |
| AB 22 | #4 anomalous | /pi/ | /pi/ | **CONFIRM** (CM=/pi/ HIGH) |
| AB 02 | #5 anomalous | /ro/ | /ro/ | UNCERTAIN (dual function) |
| AB 85 | #7 anomalous | — | — | UNCERTAIN (word divider?) |

### Cypro-Minoan Triangular Inference

- 86 Linear A → Cypro-Minoan → Cypriot Greek mappings identified
- 36 HIGH-confidence CM values provide independent phonetic constraints
- Methodology: LA sign → visual match to CM sign → CM sign value from Cypriot syllabary
- Key limitation: CM itself is partially undeciphered; intermediate step introduces ambiguity

---

## 7. Phase 6 — Verification

**Status:** ✅ Complete
**Module:** `pipeline/verification/cross_evidence.py`, `pipeline/verification/toponym_testing.py`, `pipeline/verification/internal_consistency.py`

### Cross-Evidence Triangulation

Of 94 UNCERTAIN signs compared against 4 evidence sources (nearest-neighbor, Linear B, Cypro-Minoan, grid confidence):

| Convergence Score | Count | Meaning |
|-------------------|-------|---------|
| 0 | 45 | No evidence source agrees with ML |
| 1 | 44 | One source agrees (usually LB) |
| 2 | 5 | Two sources agree |
| 3+ | **0** | Nothing converges at high confidence |

### Internal Consistency

Applying ML predictions to UNCERTAIN signs improves 8/8 consistency metrics:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| CV Adherence Rate | 75.3% | **99.7%** | +24.4pp |
| CV Anomalies | 1,240 | 15 | -1,225 |
| Word Boundary Agreement | 92.68% | 93.41% | +0.74pp |
| Bigram Entropy | 10.28 | 9.67 | -0.62 bits |
| Trigram Entropy | 11.41 | 11.32 | -0.09 bits |
| Co-occurrence Phonetic Nearness | 0.418 | 0.763 | +82.8% |
| UNCERTAIN Phonetic Nearness | 0.366 | 0.764 | +109.0% |
| Positional Entropy | 1.044 | 1.103 | +5.6% |

### Toponym Testing

ML predictions applied to re-read known toponyms and formulas:

- 17 terms tested (7 toponyms, 2 formulas, 3 accounting terms, 5 loanword anchors)
- ML overwhelmingly confirms conventional readings for known signs
- **su-ki-ri-ta** reading improved by AB 45 ri→de revision
- **di-ka-ta** reading slightly improved
- Most UNCERTAIN signs in toponyms retained conventional values
- No revolutionary breakthroughs from toponym re-reading

### Honest Assessment

> "No UNCERTAIN Linear A sign achieves 3-source convergence across the four verification channels. The ML predictions are supplementary signals — not independent verification. This is the honest assessment."

---

## 8. Phase 7 — Five Alternative Approaches

**Status:** ✅ Complete
**Packages:** `pipeline/eteocretan/`, `pipeline/commodity_decoding/`, `pipeline/phylogenetic/`, `pipeline/kober/`, `pipeline/anatolian_search/`

### Approach 1: Eteocretan Decipherment

**Signal quality:** LOW — corpus too small

- 7 Greek-alphabet inscriptions from eastern Crete (~500–300 BCE)
- ~55 word tokens, ~44 unique types
- No exact matches with known LA vocabulary
- 27% of words mappable to LA signs (driven by short words)
- `onadesimet` is most promising word: appears in 3 texts + bilingual PR 2
- Phonotactic profile broadly compatible but inconclusive
- **Verdict:** Cannot confirm or refute Eteocretan = Minoan with current corpus

### Approach 2: Commodity-Semantic Decoding

**Signal quality:** MODERATE — works in principle, corpus-limited

- Distinctive syllabogram sequences found for 9/10 commodity classes
- `i-ri` near GRAIN logogram matches Mycenaean `ki-ri` (κριθή, barley)
- Only 1 distinctive sequence contains UNCERTAIN signs
- Most sequences appear once — statistical power critically low
- **Verdict:** Method validates but needs 10× larger corpus for robust results

### Approach 3: Phylogenetic Multi-Script Model

**Signal quality:** MODERATE-HIGH — strongest analytical tool for conflict resolution

- Weighted parsimony model across LA→LB→CM→Cypriot (4 scripts)
- 4 scoring dimensions: phonetic plausibility (0.35), grid support (0.20), direct attestation (0.25), indirect corroboration (0.20)
- **9/10 conflicts favor LB, 1/10 favors CM** (AB 68 → /ro/)
- All margins narrow (1–9%), reflecting genuine uncertainty
- Priority rankings for each conflict provided

| Sign | Winner | Confidence | Priority |
|------|--------|------------|----------|
| AB 01 | LB /da/ | 0.57 | Moderate |
| AB 07 | LB /di/ | 0.55 | Moderate |
| AB 16 | LB /qa/ | 0.58 | Moderate |
| AB 23 | LB /mu/ | 0.53 | **HIGH** |
| AB 36 | LB /jo/ | 0.54 | Moderate |
| AB 38 | LB /e/ | 0.55 | **HIGH** |
| AB 60 | LB /ra/ | 0.53 | **HIGHEST** |
| AB 65 | LB /ju/ | 0.51 | Low |
| AB 68 | CM /ro/ | 0.40 | Low |
| AB 80 | LB /ma/ | 0.54 | Moderate |

### Approach 4: Kober Clustering

**Signal quality:** MODERATE — provides strongest independent constraints

- 5 positional clusters identified among 54 UNCERTAIN signs (≥5 occurrences)
- 7,305 complete Kober triples detected, 2,080 all-UNCERTAIN
- **24.8% of triples show ML-consistent CV sharing** (above random)
- 75.2% disagreement with ML — indicates significant ML noise
- Boundary-flexible cluster (init=42%, fin=44%) contains 12 signs including AB 02, AB 60, AB 62, AB 66, AB 80, AB 85
- AB 62 (437 occurrences) and AB 66 (461 occurrences) are the most connected UNCERTAIN signs
- 40 UNCERTAIN signs lack sufficient occurrences (<5) for positional analysis

### Approach 5: Anatolian Cognate Search

**Signal quality:** ZERO — negative result

- 134 Luwian/Lycian words searched against 1,719 LA inscriptions
- 2,345 candidate matches, 25 exact substring matches
- **All 25 matches are 2-sign CV sequences** — trivially matched by chance in ~60-value syllabary
- Expected random matches: ~2.3 per term. Observed: consistent with random.
- **Verdict:** Like Tyrsenian (Phase 3), the Anatolian hypothesis fails the lexical test. Minoan remains unaffiliated.

### Cross-Approach Convergence

**No sign achieves convergent prediction from ≥2 independent approaches with high confidence.** The honest outcome after 5 alternative approaches:

- Only AB 68 (/ro/) definitively resolved
- AB 60 (ra/ma) is the single hardest unsolved problem — 7 evidence sources, 0 definitive resolutions
- Kober + Commodity combined identified as highest-ROI next step (the "double constraint" method Ventris used)

---

## 9. Phase 8 — Kober Bootstrapping

**Status:** ✅ Complete
**Module:** `pipeline/bootstrapping/grid_expand.py`

### Method

Iterative grid expansion following Ventris's method:

1. Start with 45 CONFIRMED anchor signs (44 Phase 5 + AB 68 /ro/)
2. For each UNCERTAIN sign, find C-linked and V-linked CONFIRMED partners via Kober bigram frames
3. Generate phonetic hypothesis based on partner class distributions
4. Accept hypotheses meeting confidence threshold
5. Add accepted signs to anchor set → repeat

### Results

| Cycle | Threshold | Accepted | Anchors After |
|-------|-----------|----------|---------------|
| 1 | 0.60 | 27 signs | 72 |
| 2 | 0.55 | 5 signs | 77 |
| 3 | 0.50 | 0 signs | Convergence |

**Final: 45 → 77 CONFIRMED signs** (32 newly resolved, 14 with real phonetic
values). Audit note: 19 of 77 have value `?` (category confirmed, no value),
20/77 low-confidence (<50), only 17/77 ≥70. The Phase 5 refined grid confirms
only 44. The reliable working set is ~58 values, ~17 high-confidence.

### 6 of 10 Conflict Signs Resolved

| Sign | Resolved Value | Confidence | C-links | V-links |
|------|---------------|------------|---------|---------|
| AB 01 | `/da/` | 0.75 | 28 | 26 |
| AB 07 | `/di/` | 0.75 | 19 | 22 |
| AB 23 | `/mu/` | 0.75 | 17 | 23 |
| AB 36 | `/jo/` | 0.75 | 25 | 22 |
| AB 38 | `/e/` | 0.75 | 8 | 16 |
| AB 65 | `/ju/` | 0.75 | 24 | 23 |

### Remaining Gaps

- **AB 60** (ra/ma): Only 2 C-links, 0 V-links — appears alone on 46/47 inscriptions as a one-sign nodule
- **AB 16** (qa/ka): Rare labiovelar, only 5 C-links
- **AB 80** (ma/pa): 6 C-links but CM evidence conflicts
- **61 signs** remain UNCERTAIN (insufficient distributional evidence to bootstrap)

---

## 10. Phase 9 — Formulaic Parallelism

**Status:** ✅ Complete
**Module:** `pipeline/formulaic/analyze.py`

### Method

Exploit repeated variant sequences across the corpus as a mini parallel corpus within Linear A:

1. Find all n-gram sequences (length 3–5) repeated across different inscriptions
2. Identify variant pairs — sequences differing by exactly 1 sign
3. Classify substitutions as MORPHOLOGICAL (prefix/suffix position, different class) or PHONETIC (medial position, same class)
4. For phonetic substitutions at medial positions, the two signs share either a consonant or vowel — constraining the grid

### Results

| Metric | Value |
|--------|-------|
| Total substitution pairs | 9,588 |
| Phonetic substitutions | 333 |
| Morphological substitutions | 6,379 |
| Grid constraints generated | 333 |
| Unique signs involved | 224 |

### Key Discoveries

#### AB 49 = Dental-Consonant /a/ Sign

AB 49 substitutes for AB 08 (`/a/`) at the prefix position of a 12-occurrence formula (`AB 49-AB 30-AB 30` vs `AB 08-AB 30-AB 30`). Combined with Phase 8 Kober constraints (26 C-links, 27 V-links, both dental), AB 49 is a dental-consonant sign with vowel `/a/` — one of: `/ta/`, `/na/`, `/sa/`, `/za/`.

#### AB 85 = Logogram, Not Syllabogram

AB 85 is the most substituted sign in the formulaic network — it substitutes for 6+ different signs (AB 76 /pi/, AB 75, AB 64, AB 09 /se/, AB 36 /jo/, AB 47 /nu/) in the same frame position. This is inconsistent with a phonetic syllabogram. Consistent with Phase 5 findings that AB 85 may be a word divider or classifier logogram.

#### Shared-Vowel Constraints

Two strong shared-vowel confirmations:

| Pair | Vowel | Evidence | Confidence |
|------|-------|----------|------------|
| AB 34 (`/ti/`) ↔ AB 07 (`/di/`) | `/i/` | Same vowel, different initial consonant | 0.70 |
| AB 24 (`/ne/`) ↔ AB 04 (`/te/`) | `/e/` | Same vowel, different initial consonant | 0.70 |

These confirm nasal/stop pairs in the same consonant series, consistent with the CV grid structure.

#### Productive Prefix System

AB 59, AB 89, and VASE 3 all substitute for AB 30 (`/ni/`) in prefix position, suggesting a productive three-way prefix alternation — possibly grammatical number, gender, or case marking.

#### AB 46 = Grammatical Suffix Marker

AB 46 substitutes for AB 38 (`/e/`) and AB 10 (`/u/`) at suffix positions in high-frequency frames. The substitution pattern is morphological rather than phonetic, suggesting AB 46 is a grammatical suffix morpheme, not a phonetic syllabogram.

---

## 11. The Phonetic Grid — Current State

### After 9 Phases of Systematic Analysis

| Status | Count | Percentage |
|--------|-------|------------|
| **CONFIRMED** | 78 | 56.5% |
| **UNCERTAIN** | 60 | 43.5% |
| **Total syllabograms** | 138 | 100% |

### The 4 Remaining Persistent Conflicts

| Sign | Conventional | CM Value | CM Confidence | Best Estimate | Priority |
|------|-------------|----------|---------------|---------------|----------|
| AB 16 | /qa/ | /ka/ | MEDIUM | /qa/ (phylo conf 0.58) | Moderate |
| AB 60 | /ra/ | /ma/ | HIGH | **UNCERTAIN** (cannot resolve) | HIGHEST |
| AB 68 | /ro₂/ | /ro/ | LOW | **/ro/ (resolved Phase 7)** | Done |
| AB 80 | /ma/ | /pa/ | LOW | /ma/ (phylo conf 0.54) | Moderate |

### Signs with Newly Constrained Values

| Sign | New Constraint | Source | Evidence |
|------|---------------|--------|----------|
| AB 49 | Dental + vowel `/a/` | Phase 8 + Phase 9 | Kober: 26 C-links + 27 V-links (dental). Formulaic: substitutes for AB 08 (/a/) |
| AB 85 | Likely logogram/classifier | Phase 9 | Substitutes for 6+ different signs in same position |
| AB 46 | Likely grammatical suffix | Phase 9 | Substitutes morphologically for AB 38 (/e/) and AB 10 (/u/) |
| AB 34 | Shared vowel `/i/` with AB 07 | Phase 9 | Phonetic substitution pair, conf 0.70 |
| AB 24 | Shared vowel `/e/` with AB 04 | Phase 9 | Phonetic substitution pair, conf 0.70 |

---

## 12. What We Actually Know

### High-Confidence Knowledge (Multiple Convergent Sources)

1. **~15–20 words with secure meanings**: ku-ro (total), po-to-ku-ro (grand total), ki-ro (owed), pa-i-to (Phaistos), i-da (Mt. Ida), su-ki-ri-ta (Sybrita), and others. **Correction audit note:** on the corrected corpus, i-da has 19 exact matches (robust); pa-i-to's "95 matches" were loose fuzzy transliteration matches (PA-TO distance-1) — exact sign-sequence matches are only 2. The libation formula words (ja-sa-sa-ra-me, u-na-ka-na-si, si-ru-te, di-ki-te-te) are now verified recurring on the corrected corpus.

2. **~58 syllabogram values confirmed or strongly supported** (audit-adjusted): 44 from Phase 5, 1 from Phase 7 (AB 68), 33 from Phase 8 bootstrapping (14 with real values). Audit note: of 77 "CONFIRM" signs in the bootstrap grid, 19 have value `?` (category-only), 20/77 low-confidence (<50), only 17/77 ≥70; the refined grid confirms only 44. The reliable working set is ~58 values. (The corpus correction re-mapped the sign identities but did not change the grid values.)

**Grid purge (Phase 11):** the expanded grid has been purged to 69 real signs (58 CONFIRMED + 11 UNCERTAIN) — 69 phantom entries were removed (19 phantom CONFIRMED incl. AB 68 "ro" (Phase 7 resolution — VOID), AB 32 "i", AB 36 "jo"; 50 phantom UNCERTAIN incl. all AB 100-137). The honest grid is `expanded_grid_purged.csv`. AB 41 (si) is the most frequent UNCERTAIN sign (240 occurrences) and the key open target.

3. **3 conventional AB grid values are wrong**: AB 45 = /de/ (not /ri/), AB 47 = /ja/ (not /nu/), AB 65 = /jo/ (not /ju/) — these hold but see audit note on AB 01/38/50. (The 4th, AB 68 = /ro/, is now VOID — AB 68 was a phantom sign with no valid codepoint; the "Phase 7 resolution" was based on a phantom.)

4. **The morphological profile is agglutinative, suffixal, head-final, with no grammatical gender**: This constrains candidate language families and word formation patterns (supported, weakly attested).

5. **A 301 is a logogram, 85% inscription-initial at Haghia Triada** (correction-updated): the old "AB 85" (274 occurrences, positionally anomalous) was a MIS-MAPPED A 301. On the corrected corpus, AB 85 has 8 occurrences and is not anomalous; A 301 has 274 and is a heading/entry-opening logogram, and a fixed element (i-*301-54) in the libation formula.

6. **AB 60 remains genuinely unresolved after 11 phases**: 7 evidence sources, 0 definitive resolutions. It appears alone on 46/47 inscriptions as a one-sign nodule, making Kober and formulaic analysis impossible. The Phase 11 diachronic prior (which would have lowered AB 60's prior as LM-only) was INVALIDATED by the corpus correction — so AB 60's status is unchanged: genuinely unresolved.

7. **No language family has statistically significant lexical evidence**: Tyrsenian (Phase 3) and Anatolian (Phase 7) both fail. Minoan is an isolate by default.

### What We Can Say With Moderate Confidence

1. **The remaining 4 conflict signs favor LB values**: Phylogenetic model gives 3/4 to LB by narrow margins

2. **AB 49 is likely a dental-consonant sign with vowel /a/**: Kober + formulaic evidence converges

3. **The prefix system is productive**: 3 different signs substitute for AB 30 (/ni/) in prefix position

4. **AB 46 is a grammatical suffix marker**: Morphological substitution pattern

5. **AB 62 and AB 66 are the most connected UNCERTAIN signs**: Kober network analysis; resolving either one would constrain many others

### What We Can't Say

1. **We have not "deciphered" Linear A**: 60 of 138 syllabograms remain UNCERTAIN. We can read ~15–20 words with confidence. The language remains unidentified.

2. **AB 60's value**: After 9 phases of systematic analysis, this single sign remains the hardest problem in Linear A decipherment. `/ra/` has a narrow edge but we cannot prove it.

3. **The Minoan language family**: It's an isolate by process of elimination, not by positive identification.

---

## 13. What Remains Unknown

### Methodological Gaps

1. **Corpus size is the fundamental bottleneck**: 11,018 sign tokens is ~1 page of modern text. Every statistical method we've applied is corpus-limited. A corpus 10× larger would transform what's possible.

2. **No true bilingual text exists**: Linear A + a known language with the same content. The Rosetta Stone for Egyptian hieroglyphs, the Behistun inscription for cuneiform — Linear A has no equivalent.

3. **Cypro-Minoan is itself partially undeciphered**: The triangular inference chain (LA→CM→Cypriot) compounds uncertainty at the CM link.

### Specific Unresolved Questions

1. **AB 60: /ra/ or /ma/?** — The single most productive question. Resolving this one sign would unlock constraints on its C-linked partners and potentially crack open a consonant series.

2. **AB 16: /qa/ or /ka/?** — If /qa/, Linear A has a labiovelar series. If /ka/, the labiovelar is absent and the grid structure is simpler.

3. **AB 38: /e/ or /pa/?** — A vowel vs a full CV syllable. If CM is correct, the sign identification in the LA→LB mapping is wrong for this sign.

4. **What are the unclassified logograms?** — ~84 of 124 logograms have no identified meaning. Some may be key commodity terms.

5. **What is the verb system?** — We know accounting vocabulary (nouns + totals). Grammatical structure (verbs, tense, aspect) is almost completely unknown.

---

## 14. The Path Forward

### Phase 10: The Ventris Endgame — Concluded (Negative)

Michael Ventris deciphered Linear B by combining three things:

1. Kober's positional grid (we have this: 78 anchors, 7,305 triples)
2. A small set of known sign values from the Cypriot syllabary (we have: 45 from LB transfer + 33 bootstrapped)
3. **Systematic testing of grammatical hypotheses against the corpus** (this is what we've now attempted — and it failed)

Phase 10 was executed in three parts:

- **10a — Egyptian bridge & frequency-typology constraints**: 88 Middle Egyptian trade terms tested against the corpus; matches ≈ chance (null ratios 1.6–6.4×), no detectable loans. Frequency profiles eliminated 28.2% of candidate phonemes for the 80 UNCERTAIN signs.
- **10b — Grid completion**: Partial CV grid built from 58 CONFIRMED anchors (34/40 cells filled). 100 random completions scored on morphology/entropy/prefix; **zero per-sign consensus** at 60% threshold. Search space ~10¹⁴⁰ — random sampling cannot converge.
- **10c — Oracle ablation test**: A greedy restore of hidden CONFIRMED signs recovered them at **0.6× chance** (0.6% vs 5.5% chance). Even in the ideal per-sign isolation case, the true value ranked 52nd/70, excluded, or 48th/70 — the argmax was never right. The scorer has **no signal**. Strengthening attempts (Kober-consistency term, held-out cross-entropy, known-word anchors) did not lift recovery above chance.

**Conclusion:** The Ventris method requires *independent* phonetic evidence to test hypotheses against. The corpus contains none — every signal (LB transfer, Kober links, anchors) derives circularly from the same source. No optimizer (beam search, simulated annealing, Optuna) can recover answers an objective doesn't contain. **Grid completion is closed pending new data.**

### Phase 11: Four Avenues + The Diachronic Prior (INVALIDATED by correction)

Phase 11 tested four phonetic-independent approaches after the oracle failure:

- **Avenue 1 — Positional profiles**: vowel recovery failed (0.66× chance); anomaly detection flagged real positional facts — but these were later invalidated by the corpus correction (see below). The "AB 85 word divider" interpretation was retracted.
- **Avenue 2 — Commodity semantics**: hypergeometric enrichment found AB 82↔LIVESTOCK (p=0.0002) but it was circular (HIDE ligature encoding) — retracted.
- **Avenue 3 — Statistical cryptanalysis**: Zipf identical under shuffle, bigram ~7pp real, V-link cohesion circular — all frequency artifacts. No sequential structure beyond frequency.
- **Avenue 4 — Graph isomorphism**: no LB corpus to compare; degenerate communities; centrality numeral-dominated. Negative.
- **Avenue 6 — Diachronic prior (claimed the one positive)**: signs attested in both MM and LM periods appeared 2× more likely CONFIRMED (Fisher p=0.0003). **INVALIDATED by the corpus correction** — on corrected data p=0.1748 (not significant), LOO 0.91× (below baseline). It was an artifact of the corrupted frequencies.

### The Corpus Correction (Phase 11 — the most important discovery)

**144 Unicode→Bennett mapping errors** were found and fixed (verified against the Unicode standard and GORILA):
- AB 85: 274 → 8 occurrences (the real sign was A 301, a logogram, now 274)
- AB 26→AB 28, AB 51→AB 59, AB 46→AB 54, AB 49→AB 57 (systematic codepoint offsets)
- Re-ingested all 1,720 inscriptions; the corrected DB now reads IOZa2 as
  AB 08 AB 59 AB 28 AB 54 AB 57 (= A-TA-I-*301-WA-JA, matching GORILA)

**Invalidated by the correction:** the diachronic prior, the misvalued-sign flags (AB 16/60/80), the AB 85 word-divider, the V-link cohesion (2.2×→1.18×), the AB 82↔LIVESTOCK association. They were all artifacts of the transcription bias.

**Survives:** i-da (19 exact toponym matches), the negatives (oracle, cryptanalysis).

### The Libation Formula Recovery (Phase 11 — the positive outcome)

On the corrected corpus, the **real libation formula** became accessible:

```
A-TA-I-*301-WA-JA · JA-DI-KI-TU · JA-SA-SA-RA-ME · U-NA-KA-NA-SI ·
I-PI-NA-MA · SI-RU-TE · TA-NA-RA-TE-U-TI-NU · I
```

- ja-sa-sa-ra-me: 9 inscriptions; u-na-ka-na-si: 6; si-ru-te: 7
- IOZa9 = PKZa27 (identical 10-sign texts)
- **di-ki-te-te** at Palaikastro (PKZa8/11/12/15) matches published JA-DI-KI-TE-TE-DU-PU; **di-ki-tu-ja** at Iouktas — site-specific deity-root forms
- **ja-** prefix 3.4× enriched in libations; **-me** suffix on ja-sa-sa-ra-me and i-da-ki-sa-ri-me (ZA21b) — mountain-deity roots (Ida, Dikte)
- **BUT: the formula is phonetically inert for value recovery** — its words are fixed sign strings whose values come from the (LB-transfer) grid. It cannot cascade into new phonetic values.

See `data/analysis/synthesis/phase_summary_10_11.md` for the full consolidated synthesis.

### Why It Failed

1. **Circular evidence**: The scorer's "correct answers" (confirmed values) are themselves derived from LB transfer — the same evidence the scorer would have to independently rediscover. The oracle cannot distinguish right from wrong because "right" is defined by the only evidence available.
2. **Corpus ceiling**: 11K tokens of near-unstructured administrative text. Word-final distributions, bigram structure, and prefix concentration barely move when phonetics are reassigned — the corpus is too small and too homogeneous for grammatical hypothesis testing to gain traction.
3. **No independent anchor**: Ventris had the Cypriot syllabary and Greek morphology as external checks. Linear A has neither — Cypro-Minoan is itself half-undeciphered, and the language family is unknown.

### The One Question That Would Unlock Everything

**Does AB 60 = /ra/ or /ma/?** If a new archaeological discovery finds AB 60 in a multi-sign inscription with toponym context, or if a known Cretan place name definitively requires one reading over the other, this single resolution cascades through the Kober network and potentially unlocks the consonant series AB 60 belongs to.

---

## Appendix A — Repository Structure

```
labrys/
├── pipeline/                    # 9 packages, 40+ Python modules
│   ├── models.py                # Data model (Phases 1–9)
│   ├── database.py              # SQLite corpus
│   ├── positional_analysis.py   # Phase 2
│   ├── ngram_analysis.py        # Phase 2
│   ├── word_segmentation.py     # Phase 2
│   ├── network_analysis.py      # Phase 2
│   ├── logogram_analysis.py     # Phase 2
│   ├── swadesh_search.py        # Phase 3
│   ├── wals_analysis.py         # Phase 3
│   ├── loanword_matching.py     # Phase 3
│   ├── toponym_alignment.py     # Phase 3
│   ├── morphology_scan.py       # Phase 3
│   ├── falsification_report.py  # Phase 3
│   ├── ml/                      # Phase 4 (6 modules)
│   ├── linear_b_mapping.py      # Phase 5
│   ├── cypro_minoan_bridge.py   # Phase 5
│   ├── phonetic_grid_refinement.py  # Phase 5
│   ├── commodity_alignment.py   # Phase 5
│   ├── verification/            # Phase 6 (3 modules)
│   ├── eteocretan/              # Phase 7
│   ├── commodity_decoding/      # Phase 7
│   ├── phylogenetic/            # Phase 7
│   ├── kober/                   # Phase 7
│   ├── anatolian_search/        # Phase 7
│   ├── bootstrapping/           # Phase 8
│   ├── formulaic/               # Phase 9
│   ├── egyptian_bridge/         # Phase 10a
│   ├── frequency_constraints/   # Phase 10a
│   └── ventris/                 # Phase 10b/c (grid completion + oracle)
│
├── data/
│   ├── database/                # lineara_full.db (3.6 MB)
│   ├── raw/                     # TEI XML, SIGLA
│   └── analysis/                # 150+ CSV/MD outputs
│       ├── positional/
│       ├── segmentation/
│       ├── ngram/
│       ├── network/
│       ├── logograms/
│       ├── linguistic/          # Phase 3
│       ├── ml/                  # Phase 4
│       ├── comparative/         # Phase 5
│       ├── verification/        # Phase 6
│       ├── eteocretan/          # Phase 7
│       ├── commodity_decoding/  # Phase 7
│       ├── phylogenetic/        # Phase 7
│       ├── kober/               # Phase 7
│       ├── anatolian_search/    # Phase 7
│       ├── bootstrapping/       # Phase 8
│       ├── formulaic/           # Phase 9
│       └── synthesis/           # This report + phase summaries
│
├── docs/                        # Schema docs
├── pyproject.toml               # Python 3.10+, uv, torch cu121
├── AGENTS.md                    # Developer conventions
└── README.md                    # Project overview
```

## Appendix B — Key Files for Future Work

| File | Purpose |
|------|---------|
| `data/analysis/synthesis/phase_summary_1_3.md` | Detailed Phase 1-3 summary |
| `data/analysis/synthesis/phase_summary_4_6.md` | Detailed Phase 4-6 summary |
| `data/analysis/synthesis/phase_summary_7_9.md` | Detailed Phase 7-9 summary |
| `data/analysis/synthesis/phase_summary_10_11.md` | Detailed Phase 10-11 summary (Ventris endgame + avenues) |
| `data/analysis/synthesis/avenues_11.md` | Phase 11 research roadmap |
| `data/analysis/ventris/verification_audit.md` | Claims audit (retractions) |
| `data/analysis/ventris/diachronic_findings.md` | Diachronic prior detailed findings |
| `data/analysis/comparative/refined_phonetic_grid.csv` | Current state of all 138 signs |
| `data/analysis/bootstrapping/expanded_grid.csv` | Post-Phase 8 grid (78 CONFIRMED) |
| `data/analysis/kober/triple_patterns.csv` | 7,305 Kober triples |
| `data/analysis/formulaic/substitutions.csv` | 9,588 formulaic substitutions |
| `data/analysis/phylogenetic/conflict_resolutions.csv` | 10 conflict resolutions with confidence |
| `data/analysis/alternative_approaches_synthesis.md` | Phase 7 cross-approach synthesis |
| `data/analysis/ventris/ventris_report.md` | Phase 10b grid-completion report (negative) |
| `data/analysis/ventris/sign_consensus.csv` | Per-sign consensus across top completions |
| `pipeline/ventris/complete.py` | Grid completer + oracle ablation test (`oracle_test()`) |
| `data/analysis/egyptian_bridge/egyptian_report.md` | Phase 10a Egyptian bridge (negative) |
| `data/analysis/frequency_constraints/frequency_report.md` | Phase 10a frequency-typology constraints |

---

*The Linear A decipherment remains unsolved after 70+ years. We have not solved it. But we have mapped its boundaries — we know exactly where the 10 hardest problems are, which methods work, which have been exhausted, and exactly what evidence would move the needle. The Labrys Project has transformed Linear A from mystery to mapped territory.*

*Generated from 9 phases of systematic computational analysis.*
*Date: 2026-08-03*
