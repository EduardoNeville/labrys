# Phase 4 Synthesis — ML Predictions for UNCERTAIN Linear A Signs

## Overview

This report presents the results of applying the Phase 4 ML phonetic classifier
to the 94 Linear A syllabograms marked UNCERTAIN in the Phase 5 refined phonetic
grid. The classifier was trained on the 44 CONFIRMED signs (4 coarse phonological
categories: vowel, labial, dental/coronal, velar/palatal) using a small
transformer with masked context windows. Token embeddings from the trained
model were used to perform nearest-neighbour lookup against CONFIRMED signs,
blended with existing evidence from Linear B transfer (Phase 2), Cypro-Minoan
triangular inference (Phase 5), and grid confidence scoring (Phase 3).

**Total UNCERTAIN signs evaluated:** 94

**This is a 70-year unsolved problem.** The following results must be
interpreted with extreme caution. No prediction should be treated as confirmed
without independent verification from multiple evidential sources.

## Methodology

### Model Architecture

- **Model:** `PhoneticClassifier` (transformer encoder, d_model=128, 4 heads, 2 layers)
- **Training objective:** Predict coarse phonological category (vowel/labial/dental/velar)
  from a masked context window of ±5 signs
- **Training data:** ~11,000 sign occurrences from the Linear A corpus
- **Supervised labels:** 44 CONFIRMED signs from the refined phonetic grid
- **Output:** L2-normalised token embeddings (128-dim) for all 127 in-vocabulary Bennett IDs
- **Training epochs:** 20 (best checkpoint used for embeddings)

### Prediction Pipeline

1. Load token embeddings and the refined phonetic grid
2. For each UNCERTAIN sign with an embedding, compute cosine similarity to all CONFIRMED
   signs and return top-3 nearest neighbours
3. Blend NN similarity with existing evidence sources (LB composite, CM triangular,
   grid confidence) into a single confidence score
4. For 9 UNCERTAIN signs outside the classifier vocabulary (AB 21F, 97, 99, 100,
   101, 118, 125, 128, 129), fall back to existing grid evidence only

### Confidence Score Formula

| Evidence Source | Weight (with NN) | Weight (no NN) |
|----------------|-----------------|----------------|
| Nearest-neighbour similarity | 40% | 0% |
| Grid confidence (Phase 3) | 25% | 45% |
| LB composite (Phase 5) | 20% | 30% |
| CM triangular (Phase 5) | 15% | 25% |

Scores are clamped to [0, 1] and are explicitly acknowledged as approximate
heuristics — not calibrated probabilities.

## Results

### Confidence Distribution

| Tier | Range | Count | Percentage |
|------|-------|-------|------------|
| High | > 0.7 | 0 | 0.0% |
| Medium | 0.4–0.7 | 6 | 6.4% |
| Low | < 0.4 | 88 | 93.6% |

**Average confidence across all 94 signs:** 0.153

**No predictions reach HIGH confidence.** This is expected: UNCERTAIN signs
are, by definition, those where existing evidence is insufficient. The ML model
provides a weak supplementary signal but cannot overcome the fundamental data
scarcity.

### Medium-Confidence Predictions (0.4–0.7)

| Sign | Conventional | Predicted | Confidence | Key Evidence |
|------|-------------|-----------|------------|--------------|
| AB 01 | /da/ | /da/ | 0.546 | LB=/da/ (83), CM HIGH=/ta/, GC=65 |
| AB 07 | /di/ | /di/ | 0.477 | LB=/di/ (76), CM HIGH=/ti/, GC=55 |
| AB 14 | /do/ | /do/ | 0.424 | LB=/do/ (74), CM MED=/to/, GC=52 |
| AB 23 | /mu/ | /mu/ | 0.404 | LB=/mu/ (69), CM HIGH=/ma/, GC=28 |
| AB 36 | /jo/ | /jo/ | 0.415 | LB=/jo/ (67), CM HIGH=/za/, GC=35 |
| AB 38 | /e/ | /e/ | 0.487 | LB=/e/ (81), CM HIGH=/pa/, GC=52 |

**All 6 medium-confidence predictions retain their conventional LB values.**
The ML embeddings are modestly supportive but do not provide strong enough
evidence to overturn the Linear B transfer values. The predominant source
of confidence in these predictions is the strong LB composite score (mean 75.0),
not the embedding similarity (mean cosine 0.177).

### Predicted vs. Conventional Mismatches

Four UNCERTAIN signs received predictions that differ from their conventional
AB syllabary value:

| Sign | Conventional | Predicted | Confidence | NN Support | Phase 5 Assessment |
|------|-------------|-----------|------------|------------|-------------------|
| AB 45 | /ri/ | /de/ | 0.298 | AB 53=ri (0.245) | CM=/de/ LOW vs GC=/ri/ |
| AB 47 | /nu/ | /ja/ | 0.262 | AB 30=ni (0.274) | CM=/ja/ LOW vs GC=/pa/ |
| AB 65 | /ju/ | /jo/ | 0.281 | AB 30=ni (0.173) | CM=/jo/ LOW vs GC=/i/ |
| AB 68 | /ro₂/ | /ro/ | 0.261 | AB 53=ri (0.254) | CM=/ro/ LOW vs GC=/pa/ |

**These are all low-confidence predictions** (0.26–0.30). Notably, AB 45, 47,
65, and 68 received REVISE recommendations in Phase 5. The ML predictions
partially align with those Phase 5 revisions for AB 65 (/ju/→/jo/) and AB 68
(/ro₂/→/ro/), but the confidence is too low for any actionable recommendation.

### Evidence Source Coverage

| Evidence Type | Signs with Source | % of 94 |
|--------------|-------------------|---------|
| Nearest-neighbour (embedding) | 85 | 90.4% |
| Linear B composite | 12 | 12.8% |
| Cypro-Minoan triangular | 48 | 51.1% |
| Grid confidence (Phase 3) | 26 | 27.7% |

The classifier covers 90.4% of UNCERTAIN signs (85/94). The 9 signs lacking
embeddings are rare syllabograms (AB 21F, AB 97, AB 99, AB 100) and high-numbered
signs (AB 101, 118, 125, 128, 129) that were not in the training corpus vocabulary.

### Zero-Confidence Signs

6 signs have confidence = 0.0, meaning no evidence from any source:

| Sign | Conventional | Predicted |
|------|-------------|-----------|
| AB 21F | ? | ? |
| AB 101 | ? | ? |
| AB 118 | ? | ? |
| AB 125 | ? | ? |
| AB 128 | ? | ? |
| AB 129 | ? | ? |

All six are variant or high-numbered signs with zero attestations in the
available evidence. Their status as UNCERTAIN is irreversible without new
archaeological data.

## ML/CM/LB Conflicts

### Signs with Conflicting Evidence Sources

The most interesting UNCERTAIN signs are those where the ML nearest-neighbour
prediction disagrees with the CM or LB evidence. The following signs show a
genuine three-way or two-way conflict:

| Sign | Conv | ML-NN | LB | CM | GC | Decision |
|------|------|-------|----|----|----|----------|
| AB 01 | /da/ | /na/ | /da/ (83) | /ta/ (HIGH) | /da/ (65) | UNCERTAIN |
| AB 07 | /di/ | /to/ | /di/ (76) | /ti/ (HIGH) | /di/ (55) | UNCERTAIN |
| AB 14 | /do/ | /te/ | /do/ (74) | /to/ (MED) | /do/ (52) | UNCERTAIN |
| AB 36 | /jo/ | /i/ | /jo/ (67) | /za/ (HIGH) | /jo/ (35) | UNCERTAIN |
| AB 38 | /e/ | /to/ | /e/ (81) | /pa/ (HIGH) | /e/ (52) | UNCERTAIN |
| AB 60 | /ra/ | /to/ | /ra/ (72) | /ma/ (HIGH) | — | UNCERTAIN |

A recurring pattern is visible: the ML nearest-neighbour often pulls toward
dental/coronal consonants (/t/, /n/, /s/) regardless of the LB or CM value.
This likely reflects the dominance of dental/coronal signs (24/44 CONFIRMED)
in the training labels, creating a systematic bias rather than a genuine
phonetic signal.

### Voice/Aspiration Series Patterns

The d-/t- conflict (AB 01, 07, 14, 45) is the single most prominent pattern
in the UNCERTAIN set. Linear B consistently gives voiced values (/da/, /di/,
/do/), while Cypro-Minoan more often suggests voiceless (/ta/, /ti/, /to/).
The ML embeddings cannot resolve this because:

1. The coarse classifier merges voiced and voiceless into the same
   dental/coronal category
2. The nearest-neighbour lookup operates on an embedding space trained for
   broad phonological categories, not fine phonetic distinctions
3. The corpus (~11K tokens) is too small for the model to learn sub-phonemic
   distinctions from positional context alone

## Key Sign Assessments

### AB 01 (/da/ vs /ta/)

- **Evidence:** LB 83 (/da/), CM HIGH (/ta/), GC 65 (/da/)
- **ML-NN top match:** AB 06 (/na/, cos=0.244)
- **Prediction:** /da/ (confidence 0.546)
- **Assessment:** The strong LB signal (composite 82.8) dominates. The CM
  conflict (/ta/ vs /da/) persists. The ML embeddings weakly suggest a
  coronal consonant, which is consistent with both /da/ and /ta/. This
  remains genuinely UNCERTAIN until a toponym or loanword anchor resolves
  the voicing.

### AB 60 (/ra/ vs /ma/)

- **Evidence:** LB 72 (/ra/), CM HIGH (/ma/), positional anomaly rank #2
- **ML-NN top match:** AB 05 (/to/, cos=0.154)
- **Prediction:** /ra/ (confidence 0.321)
- **Assessment:** Embedding similarity to CONFIRMED signs is very low
  (max 0.154). The positional anomaly (50.5% final position) strongly
  suggests a suffix function. The ML model cannot distinguish /ra/ from
  /ma/ because both collapse to different coarse categories (dental vs
  labial) and the model assigns low probability to both. This sign needs
  dedicated investigation.

### AB 02 (/ro~i/ dual hypothesis)

- **Evidence:** LB 76 (/ro/), GC 45 (/i/), positional anomaly rank #6
- **ML-NN top match:** AB 77 (/ka/, cos=0.177)
- **Prediction:** /ro/ (confidence 0.336)
- **Assessment:** The Phase 5 dual-value hypothesis (/ro~i/) is not
  testable with current ML methods. A conditioning analysis of AB 02's
  positional environments would be needed to determine whether two
  distinct usage patterns exist.

### AB 85 (word divider candidate)

- **Evidence:** CM LOW (/au/), positional anomaly (47% initial/47% final)
- **ML-NN top match:** AB 03 (/pa/, cos=0.126)
- **Prediction:** /au/ (confidence 0.130)
- **Assessment:** The very low NN similarity and confidence reinforce
  Phase 5's assessment that AB 85 is likely non-phonetic. The positional
  distribution (initial+final dominance) is characteristic of boundary
  markers, not phonetic signs.

## Limitations

### Fundamental Constraints

1. **Corpus size:** ~11,000 tokens is extremely small for deep learning.
   The model uses d_model=128 (tiny by modern standards) and 4 attention
   heads with 2 layers — adequate for the data but limiting in capacity.

2. **Training objective mismatch:** The classifier predicts coarse
   phonological categories (4 classes), not fine phonetic values (36 classes).
   The nearest-neighbour approach extrapolates from coarse embeddings to
   fine values, adding an additional layer of approximation.

3. **Label imbalance:** 24/44 CONFIRMED signs are dental/coronal, biasing
   the embedding space toward that category. Predictions for labial,
   velar/palatal, and vowel UNCERTAIN signs may be systematically pulled
   toward the dental cluster.

4. **No contextual inference:** The predictions use static token embeddings,
   not the contextual encoder. The model's ability to predict a sign's
   phonetic class from its surrounding context window was not evaluated
   on UNCERTAIN signs because these signs lack ground-truth labels.

5. **Confidence scores are heuristic:** The blending formula uses ad-hoc
   weights. These are not calibrated probabilities and should not be
   interpreted as such. The scores are ordinal only — a sign with 0.50
   has more evidential support than one with 0.10, but neither is
   "50% likely to be correct."

### Evidence Quality

6. **9 signs lack embeddings** (9.6% of UNCERTAIN set), receiving
   predictions based solely on non-ML evidence.

7. **CM evidence dominates numerically** (48/94 signs) but the LOW
   confidence category contains mostly uncertain values with low
   triangular inference scores.

8. **Linear B transfer** provides the strongest evidence but applies to
   only 12/94 UNCERTAIN signs and is known to be problematic for the
   d/t and q/k series.

### Known Biases

9. **Dental pull:** The NN predictions for signs with weak evidence
   systematically select dental/coronal CONFIRMED neighbours because
   of class imbalance, not because of genuine phonetic similarity.

10. **Epoch limit:** The classifier used 20 training epochs on a
    dataset with extreme class imbalance. Longer training or
    class-balanced sampling might produce different embeddings.

## Comparison with Phase 5 Findings

### Agreement Patterns

The ML predictions agree with the Phase 5 refined grid values in most
cases, which is expected — both methods rely on the same underlying
evidence (LB composite, CM triangular, GC). The ML adds a weak orthogonal
signal from distributional similarity.

### Disagreements

The 4 predicted-vs-conventional mismatches (AB 45, 47, 65, 68) all involve
signs where Phase 5 itself recommended REVISE. The ML predictions partially
align with those revisions (AB 65: /ju/→/jo/, AB 68: /ro₂/→/ro/) but at
insufficient confidence for action.

### Confidence Calibration

Phase 5's confidence scoring (weighted average of LB ×2, CM ×1.5, GC ×1.5)
produces a different distribution from the ML blended scores. Phase 5
reports 17 HIGH, 51 MEDIUM, 70 LOW across all 138 signs. The ML predictions
on the UNCERTAIN subset are systematically lower (0 HIGH, 6 MEDIUM, 88 LOW)
because the UNCERTAIN subset already represents the hardest cases.

## Next Steps

### Immediate

1. **Re-train with fine-grained labels:** Train a 36-class phonetic classifier
   instead of the 4-class coarse model. This would allow direct prediction of
   phonetic values rather than nearest-neighbour extrapolation.

2. **Contextual inference:** Use the trained encoder's full forward pass on
   actual inscription contexts containing UNCERTAIN signs, with the anchor
   sign masked, to get context-dependent predictions rather than static token
   embeddings.

3. **Class-balanced sampling:** Address the dental/coronal over-representation
   to reduce systematic bias in the embedding space.

### Medium-Term

4. **Cross-validation on CONFIRMED signs:** Hold out a subset of CONFIRMED
   signs and evaluate prediction accuracy before applying to UNCERTAIN signs.
   This would provide a calibrated accuracy estimate.

5. **Ensemble with the masked language model:** The SignLM was also trained
   and its contextual representations could be probed for phonetic structure
   independently of the classifier.

6. **Multi-task architecture:** Joint training on phonetic classification,
   logogram classification, and masked language modelling could improve
   representation quality by sharing statistical strength across objectives.

### Long-Term

7. **Bayesian phylogenetic inference:** Combine ML embeddings with the
   comparative-historical framework from Phases 3 and 5 in a proper
   probabilistic model.

8. **New archaeological data:** Ultimately, the ~70% of signs that remain
   UNCERTAIN cannot be resolved by computational methods alone. New
   inscriptions, bilingual texts, or improved Cypro-Minoan decipherment are
   needed.

## Data Products

| File | Description | Rows |
|------|-------------|------|
| `uncertain_predictions.csv` | ML predictions for all 94 UNCERTAIN signs | 94 |
| `classifier_embeddings.pt` | Token embeddings for 127 syllabograms | 127 |
| `classifier_epoch_020.pt` | Final trained classifier checkpoint | — |

---

*Generated by Phase 4 ML pipeline — predict.py*
*Inputs: Phase 5 refined phonetic grid, classifier embeddings (20-epoch transformer)*
