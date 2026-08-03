# Phylogenetic Multi-Script Sign Evolution Report

## Phase 7 — Approach 3: Weighted Parsimony Model for 10 Persistent LB/CM Conflicts

### Descent Chain

```
Linear A (Minoan, ~1800-1450 BCE)
    │
    ▼
Linear B (Mycenaean Greek, ~1400-1200 BCE)
    │
    ▼
Cypro-Minoan (Cyprus, ~1500-1050 BCE)
    │
    ▼
Cypriot Syllabary (Classical Cypriot Greek, ~800-200 BCE)
```

### Methodology

For each of the 10 persistent conflicts, two competing hypotheses are
evaluated:

- **H_LB**: Linear A had the same value as Linear B (direct transfer)
- **H_CM**: Linear A had the value inferred from Cypro-Minoan (triangular inference)

Each hypothesis is scored across four weighted dimensions:

| Dimension            | Weight | Description |
|----------------------|--------|-------------|
| Phonetic plausibility| 0.35   | How natural is the sound change required in each direction, combining articulatory distance (place, manner, voicing for consonants; height, backness, rounding for vowels) with directional typological knowledge |
| Grid support         | 0.20   | Does the refined phonetic grid (Phase 5) support this value? |
| Direct attestation   | 0.25   | Quality of the source that directly supports this value (LB composite score or CM triangular confidence) |
| Indirect corroboration | 0.20 | Does the other source at least allow this value phonetically? |

The hypothesis with higher score wins. Confidence is the score margin scaled
and capped by source quality.

### Results Summary

| Sign  | LB Value | CM Value | CM Conf | Winner | Confidence | Margin |
|-------|----------|----------|---------|--------|------------|--------|
| AB 01 | /da/     | /ta/     | HIGH    | LB /da/ | 0.566 | 8% |
| AB 07 | /di/     | /ti/     | HIGH    | LB /di/ | 0.554 | 6% |
| AB 16 | /qa/     | /ka/     | MEDIUM  | LB /qa/ | 0.577 | 9% |
| AB 23 | /mu/     | /ma/     | HIGH    | LB /mu/ | 0.525 | 3% |
| AB 36 | /jo/     | /za/     | HIGH    | LB /jo/ | 0.544 | 5% |
| AB 38 | /e/      | /pa/     | HIGH    | LB /e/  | 0.550 | 6% |
| AB 60 | /ra/     | /ma/     | HIGH    | LB /ra/ | 0.531 | 3% |
| AB 65 | /ju/     | /jo/     | LOW     | LB /ju/ | 0.510 | 1% |
| AB 68 | /ro₂/    | /ro/     | LOW     | CM /ro/ | 0.400 | 1% |
| AB 80 | /ma/     | /pa/     | LOW     | LB /ma/ | 0.536 | 4% |

**Overall: 9/10 favour LB, 1/10 favours CM (AB 68: /ro/).**

### Detailed Analysis

#### AB 01 (da vs ta) — resolves to /da/ (confidence: 0.57)

Both values are phonetically similar (differing only in voicing). The LB
composite score (82.8/100) strongly supports /da/, and ta→da is a plausible
voicing change. CM inference gives HIGH confidence for /ta/ but the longer
inference chain (LA→CM→CG) introduces ambiguity. The model favours the
direct LB evidence.

**Recommendation**: Retain /da/; CM /ta/ is a plausible dialectal variant.

#### AB 07 (di vs ti) — resolves to /di/ (confidence: 0.55)

Same pattern as AB 01: voicing opposition. LB composite (76.2) supports
/di/. The place-name DIKTE = di-ka-ta confirms /di/ in a LA context.

**Recommendation**: Retain /di/.

#### AB 16 (qa vs ka) — resolves to /qa/ (confidence: 0.58)

The labiovelar → velar change (qa→ka) is highly natural typologically
(loss of labialisation), which means both values are phonetically plausible
in either direction. LB attestation for /qa/ is moderate (composite 68.0)
and CM /ka/ has MEDIUM confidence. The direct LB evidence gives a modest
edge, but the narrow margin means this should be revisited.

**Recommendation**: Retain /qa/; if /ka/, then reassign the labiovelar series.

#### AB 23 (mu vs ma) — resolves to /mu/ (confidence: 0.53)

Vowel shift u↔a. Both plausible, very narrow margin. LB value /mu/ has
moderate composite score (69.0). CM /ma/ has HIGH confidence — this is
one of the stronger CM claims.

**Recommendation**: Retain /mu/ but flag as HIGH PRIORITY for re-evaluation.

#### AB 36 (jo vs za) — resolves to /jo/ (confidence: 0.54)

Palatal /jo/ → affricate /za/ is a well-attested sound change path.
LB attestation is moderate (67.2). CM HIGH confidence for /za/. The
narrow margin reflects phonetic plausibility of both.

**Recommendation**: Retain /jo/.

#### AB 38 (e vs pa) — resolves to /e/ (confidence: 0.55)

This is the most striking conflict: a vowel vs. a CV syllable. LB gives
/e/ with high composite score (81.0). CM gives /pa/ with HIGH confidence.
A change in either direction requires syllable-structure restructuring,
which is highly marked. The model strongly penalises this restructuring
(~0.65 phonetic plausibility for e↔pa in either direction).

**Recommendation**: Retain /e/. The CM inference for this sign may be
wrong, or AB 38 may be a different sign than the one mapped to CM 010.

#### AB 60 (ra vs ma) — resolves to /ra/ (confidence: 0.53)

Very close. LB composite (72.5) for /ra/, CM HIGH for /ma/. The r→m change
is uncommon but attested. This is the most-studied conflict in the
literature and both sides have merit.

**Recommendation**: Retain /ra/ but flag as HIGHEST PRIORITY for toponym
search resolution.

#### AB 65 (ju vs jo) — resolves to /ju/ (confidence: 0.51)

Vowel-only difference (u↔o). CM has LOW confidence, making this the weakest
CM claim. Narrowest margin of any conflict (1%).

**Recommendation**: Retain /ju/; essentially unresolvable with current data.

#### AB 68 (ro₂ vs ro) — resolves to /ro/ (confidence: 0.40)

The only conflict where CM wins. ro₂ is a variant of ro in LB, and the
simpler value /ro/ is favoured. Both CM and LB show LOW confidence for
this sign, so the overall confidence is low.

**Recommendation**: Use /ro/; the ro₂ variant may reflect a spelling convention.

#### AB 80 (ma vs pa) — resolves to /ma/ (confidence: 0.54)

CM has LOW confidence for /pa/ (CM 051 → Cypriot /pa/), which weakens
the CM claim substantially. LB attestation for /ma/ is high (76.0).
The m→p or p→m change is moderately marked in either direction.

**Recommendation**: Retain /ma/; CM evidence too weak to revalue.

### Limitations

1. **All margins are narrow.** The confidences range from 0.40 to 0.58,
   meaning no resolution achieves "high confidence." This is intellectually
   honest: these ARE genuine conflicts.

2. **Model weights are heuristic.** The 35/20/25/20 weighting reflects
   qualitative judgment about the relative reliability of each evidence
   type. Sensitivity testing would be valuable.

3. **Directional bias is sparse.** Only a handful of sound changes have
   known directional tendencies. Most pairs default to neutral 0.5.

4. **The descent chain has gaps.** The Cypro-Minoan script is itself
   poorly attested (~250 inscriptions), creating uncertainty in the CM→CG
   link.

5. **CM evidence quality varies widely.** Only 12 CM links are HIGH
   confidence; most are MEDIUM or LOW.

### Output Files

| File | Description |
|------|-------------|
| `data/analysis/phylogenetic/alignment_matrix.csv` | 138-row 4-script alignment |
| `data/analysis/phylogenetic/conflict_resolutions.csv` | 10 conflict resolutions with scores |
| `data/analysis/phylogenetic/phylogenetic_report.md` | This report |

### Next Steps (Not in Scope)

1. Sensitivity analysis: vary weights ±10% to assess robustness
2. Toponym search for AB 60 (/ra/ vs /ma/) in Minoan place names
3. Sign-form analysis: re-examine whether CM sign identifications are
   visually correct for conflict signs
4. Diphone frequency analysis: compare positional distributions of
   competing values in LA corpus

---
*Generated by pipeline/phylogenetic/ (Phase 7, Approach 3)*
