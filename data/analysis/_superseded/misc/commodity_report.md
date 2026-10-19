# Commodity-Semantic Decoding Report

## Overview

This report analyzes syllabogram sequences adjacent to Linear A commodity logograms (WINE, GRAIN, OLIVE OIL, VESSELS, etc.) to identify candidate commodity-name phonemes. The approach is constrained semantic decoding — we know what many logograms *mean* and we look at what syllabograms consistently surround them.

## Data Summary

| Commodity Class | Occurrences | Distinct Logograms | Adjacent Sylls |
|---|---|---|---|
| VESSELS | 321 | 82 | 546 |
| UNKNOWN_COMMODITY | 70 | 50 | 106 |
| GRAIN | 14 | 17 | 18 |
| OLIVE_OIL | 7 | 10 | 5 |
| MANPOWER | 7 | 6 | 9 |
| LIVESTOCK | 5 | 6 | 4 |
| OLIVES | 3 | 6 | 8 |
| PERSONNEL | 1 | 4 | 5 |
| HIDES | 1 | 0 | 0 |
| WINE | 1 | 2 | 1 |

## Distinctive Syllabogram Sequences per Commodity

For each commodity class, the most distinctive adjacent bigrams/trigrams are ranked by *distinctiveness ratio*: how much more common they are near this commodity vs. all others.

### VESSELS

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | I-GRA+PA | 3 | 0 | ∞ |
| 2 | ?-ro | 3 | 0 | ∞ |
| 3 | JA-SE | 3 | 0 | ∞ |
| 4 | PA-¹⁄₂ | 2 | 0 | ∞ |
| 5 | ¹⁄₂-PA | 2 | 0 | ∞ |
| 6 | RE-1 | 2 | 0 | ∞ |
| 7 | *325-ZA | 2 | 0 | ∞ |
| 8 | DA-SI | 2 | 0 | ∞ |
| 9 | PO-ZE | 2 | 0 | ∞ |
| 10 | 𐄁-KO | 2 | 0 | ∞ |
| 11 | SI-jo | 2 | 0 | ∞ |
| 12 | NI-5 | 2 | 0 | ∞ |
| 13 | NI-14 | 2 | 0 | ∞ |
| 14 | KA-I | 2 | 0 | ∞ |
| 15 | SE-PA | 2 | 0 | ∞ |

### UNKNOWN_COMMODITY

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | 24-10 | 1 | 0 | ∞ |
| 2 | NE-TU | 1 | 0 | ∞ |
| 3 | TU-E | 1 | 0 | ∞ |
| 4 | E-*118 | 1 | 0 | ∞ |
| 5 | QA-SI+ME | 1 | 0 | ∞ |
| 6 | ?-ru | 1 | 0 | ∞ |
| 7 | ru-mu | 1 | 0 | ∞ |
| 8 | 1-*118 | 1 | 0 | ∞ |
| 9 | *118-*118 | 1 | 0 | ∞ |
| 10 | 4-NI | 1 | 0 | ∞ |
| 11 | NI-2 | 1 | 0 | ∞ |
| 12 | PA₃-10 | 1 | 0 | ∞ |
| 13 | *815-NA | 1 | 0 | ∞ |
| 14 | NA-RA | 1 | 0 | ∞ |
| 15 | *815-RA | 1 | 0 | ∞ |

### GRAIN

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | 𐄁-𐄁 | 1 | 0 | ∞ |
| 2 | I-RI | 1 | 0 | ∞ |
| 3 | RI-TA | 1 | 0 | ∞ |
| 4 | TA-MA | 1 | 0 | ∞ |
| 5 | TE-DU | 1 | 0 | ∞ |
| 6 | *28B-TI | 1 | 0 | ∞ |
| 7 | TI-JU | 1 | 0 | ∞ |
| 8 | TA₂-*312 | 1 | 0 | ∞ |
| 9 | PI-*310 | 1 | 0 | ∞ |
| 10 | RI-*301 | 1 | 0 | ∞ |
| 11 | *301-OLIV | 1 | 0 | ∞ |
| 12 | I-RI-TA | 1 | 0 | ∞ |
| 13 | RI-TA-MA | 1 | 0 | ∞ |
| 14 | *28B-TI-JU | 1 | 0 | ∞ |
| 15 | KU-PI-*310 | 1 | 0 | ∞ |

### OLIVE_OIL

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | RE-𐄁 | 1 | 0 | ∞ |
| 2 | CYP-TA | 1 | 0 | ∞ |
| 3 | OLE-QA2+[?]+PU | 1 | 1 | 139.40 |
| 4 | SE-A | 1 | 1 | 139.40 |
| 5 | 2-≈ | 1 | 1 | 139.40 |

### MANPOWER

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | VIN-VIN | 1 | 0 | ∞ |
| 2 | VIN-A | 1 | 0 | ∞ |
| 3 | DU-A | 1 | 0 | ∞ |
| 4 | A-RE | 1 | 0 | ∞ |
| 5 | RE-ZA | 1 | 0 | ∞ |
| 6 | A-PO | 1 | 0 | ∞ |
| 7 | VIN-VIN-A | 1 | 0 | ∞ |
| 8 | DU-A-RE | 1 | 0 | ∞ |
| 9 | A-RE-ZA | 1 | 0 | ∞ |

### LIVESTOCK

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | E-HIDE+[?] | 2 | 0 | ∞ |
| 2 | VIR+[?]-JA | 1 | 0 | ∞ |
| 3 | QE-*317 | 1 | 0 | ∞ |

### OLIVES

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | TU-DA | 1 | 0 | ∞ |
| 2 | DA-*308 | 1 | 0 | ∞ |
| 3 | *308-4 | 1 | 0 | ∞ |
| 4 | OLE+MI-¹⁄₆-≈ | 1 | 0 | ∞ |
| 5 | TU-DA-*308 | 1 | 0 | ∞ |
| 6 | DA-*308-4 | 1 | 0 | ∞ |
| 7 | OLE+MI-¹⁄₆ | 1 | 1 | 86.75 |
| 8 | ¹⁄₆-≈ | 1 | 1 | 86.75 |

### PERSONNEL

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | 1-*301 | 1 | 0 | ∞ |
| 2 | *301-*306 | 1 | 0 | ∞ |
| 3 | *306-SI | 1 | 0 | ∞ |
| 4 | 1-*301-*306 | 1 | 0 | ∞ |
| 5 | *301-*306-SI | 1 | 0 | ∞ |

### HIDES

No distinctive sequences found.

### WINE

| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |
|---|---|---|---|---|
| 1 | 𐝈𐝉-JU | 1 | 0 | ∞ |

## UNCERTAIN Signs in Distinctive Sequences

Distinctive sequences that contain UNCERTAIN signs (those with ML predictions from Phase 4) are prime candidates for commodity-name phonemes. If a sign's ML-predicted value produces a reading that matches known Mediterranean trade vocabulary, that strengthens both the ML prediction and the semantic decoding.

### VESSELS

No distinctive sequences with UNCERTAIN signs.

### UNKNOWN_COMMODITY

| Sequence | ML Reading | UNCERTAIN Signs | Score | Count |
|---|---|---|---|---|
| ru-mu | ru-mu | AB 23 | inf | 1 |

### GRAIN

No distinctive sequences with UNCERTAIN signs.

### OLIVE_OIL

No distinctive sequences with UNCERTAIN signs.

### MANPOWER

No distinctive sequences with UNCERTAIN signs.

### LIVESTOCK

No distinctive sequences with UNCERTAIN signs.

### OLIVES

No distinctive sequences with UNCERTAIN signs.

### PERSONNEL

No distinctive sequences with UNCERTAIN signs.

### HIDES

No distinctive sequences with UNCERTAIN signs.

### WINE

No distinctive sequences with UNCERTAIN signs.

## Proto-Word Hypotheses

Using ML-predicted values for UNCERTAIN signs plus conventional AB values for CONFIRM signs, we can assemble candidate readings for sequences that are distinctive to specific commodities. These are cross-referenced with known Mediterranean trade vocabulary (Mycenaean, pre-Greek, Hittite, etc.).

**⚠️ CAUTION**: These are HYPOTHESES, not decipherment claims. Linear A remains undeciphered after 70+ years of effort. These readings are constrained semantic guesses, not confirmed values.

| Commodity | Sequence | Count | UNCERTAIN Signs | Trade Word Matches | Assessment |
|---|---|---|---|---|---|
| UNKNOWN_COMMODITY | ne-tu | 1 | AB 75 | none | Highly distinctive — possible commodity term |
| UNKNOWN_COMMODITY | tu-e | 1 | AB 38; AB 75 | none | Highly distinctive — possible commodity term |
| UNKNOWN_COMMODITY | e-*118 | 1 | AB 38 | none | Highly distinctive — possible commodity term |
| UNKNOWN_COMMODITY | qa-si+me | 1 | AB 16 | none | Highly distinctive — possible commodity term |
| UNKNOWN_COMMODITY | ru-mu | 1 | AB 121; AB 23 | none | Highly distinctive — possible commodity term |
| VESSELS | i-gra+pa | 3 | AB 113; AB 116; AB 133; AB 19 | none | Highly distinctive — possible commodity term |
| VESSELS | ja-se | 3 | AB 47; AB 96 | none | Highly distinctive — possible commodity term |
| VESSELS | re-1 | 2 | AB 130; AB 42; AB 94 | none | Highly distinctive — possible commodity term |
| VESSELS | *325-za | 2 | AB 110 | none | Highly distinctive — possible commodity term |
| VESSELS | da-si | 2 | AB 01; AB 41 | none | Highly distinctive — possible commodity term |
| OLIVE_OIL | re-𐄁 | 1 | AB 130; AB 42; AB 94 | none | Highly distinctive — possible commodity term |
| OLIVE_OIL | cyp-ta | 1 | AB 59; AB 62; AB 66 | none | Highly distinctive — possible commodity term |
| OLIVE_OIL | se-a | 1 | AB 115; AB 96 | none | Highly distinctive — possible commodity term |
| MANPOWER | vin-a | 1 | AB 115 | none | Highly distinctive — possible commodity term |
| MANPOWER | du-a | 1 | AB 115; AB 51 | none | Highly distinctive — possible commodity term |
| MANPOWER | a-re | 1 | AB 115; AB 130; AB 42; AB 94 | none | Highly distinctive — possible commodity term |
| MANPOWER | re-za | 1 | AB 110; AB 130; AB 42; AB 94 | none | Highly distinctive — possible commodity term |
| MANPOWER | a-po | 1 | AB 115 | none | Highly distinctive — possible commodity term |
| MANPOWER | vin-vin-a | 1 | AB 115 | none | Highly distinctive — possible commodity term |
| MANPOWER | du-a-re | 1 | AB 115; AB 130; AB 42; AB 51; AB 94 | none | Highly distinctive — possible commodity term |
| GRAIN | i-ri | 1 | AB 103; AB 113; AB 116; AB 133; AB 19 | ki-ri (Mycenaean *kri barley) | Plausible trade-word candidate |
| GRAIN | ri-ta | 1 | AB 103; AB 59; AB 62; AB 66 | none | Highly distinctive — possible commodity term |
| GRAIN | ta-ma | 1 | AB 59; AB 62; AB 66; AB 80; AB 99 | none | Highly distinctive — possible commodity term |
| GRAIN | te-du | 1 | AB 51; AB 95 | none | Highly distinctive — possible commodity term |
| GRAIN | *28b-ti | 1 | AB 104; AB 135 | none | Highly distinctive — possible commodity term |
| GRAIN | ti-ju | 1 | AB 104; AB 135 | none | Highly distinctive — possible commodity term |
| OLIVES | tu-da | 1 | AB 01; AB 75 | none | Highly distinctive — possible commodity term |
| OLIVES | da-*308 | 1 | AB 01 | none | Highly distinctive — possible commodity term |
| OLIVES | tu-da-*308 | 1 | AB 01; AB 75 | none | Highly distinctive — possible commodity term |
| OLIVES | da-*308-4 | 1 | AB 01 | none | Highly distinctive — possible commodity term |

## Overall Assessment

- **9/10** commodity classes have at least one syllabogram sequence with distinctiveness ratio > 2.0
- **1** candidate sequences contain UNCERTAIN signs that could be constrained by commodity semantics
- **2/35** proto-word hypotheses have plausible Mediterranean trade vocabulary matches

### Key Observations

- **UNKNOWN_COMMODITY**: Sequence `24-10` is *only* found near this commodity (distinctiveness = ∞)
- **VESSELS**: Sequence `I-GRA+PA` is *only* found near this commodity (distinctiveness = ∞)
- **OLIVE_OIL**: Sequence `RE-𐄁` is *only* found near this commodity (distinctiveness = ∞)
- **MANPOWER**: Sequence `VIN-VIN` is *only* found near this commodity (distinctiveness = ∞)
- **GRAIN**: Sequence `𐄁-𐄁` is *only* found near this commodity (distinctiveness = ∞)

### Key Limitations

- The Linear A corpus is small (~11K signs), so statistical distinctiveness is fragile — a single new tablet could change rankings.
- ML predictions for UNCERTAIN signs are probabilistic (confidence typically 5–50%), and our proto-word readings compound this uncertainty multiplicatively.
- Adjacent syllabograms may encode quantities, transaction verbs, or administrative formulas rather than commodity names — our current approach cannot distinguish these.
- The three most common syllabograms near most commodities are measurement formulas / transaction terms, not commodity names.
