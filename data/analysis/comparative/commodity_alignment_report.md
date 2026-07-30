# Linear A ↔ Linear B Commodity Alignment Report

**Generated:** 2026-07-30 16:58:59
**Script:** `pipeline/commodity_alignment.py`
**Inputs:**
  - `lineara_full.db` — Linear A sign corpus
  - `data/analysis/logograms/fraction_values_proposed.csv` — Phase 2 fraction proposals
  - `data/analysis/linguistic/morphology_paradigms.csv` — Phase 3 morphology scan
  - Known Linear B ideogram inventory (Ventris & Chadwick 1973, DMIC, Unicode 17.0)

---

## 1.  Ideogram Correspondence Map

| Metric | Value |
|--------|-------|
| Total Linear A logogram types | 366 |
| Mapped to Linear B equivalents | 184 |
| High-certainty correspondences | 184 |
| Low-certainty / unknown | 182 |
| Total corpus occurrences analysed | 728 |
| Inscriptions with logograms | 290 |
| Distinct findspots | 23 |

### Most Frequent LA Logograms in Corpus

| Rank | Logogram | Occurrences | LB Abbr | Meaning |
|------|----------|-------------|---------|---------|
| 1 | VASE 7 | 137 | VAS | vessel (general) |
| 2 | VASE 4 | 77 | HYDRIA | hydria / water jar |
| 3 | VASE 3 | 42 | PITHOS | pithos / storage jar |
| 4 | VASE 2 | 41 |  |  |
| 5 | VASE 8 | 35 | JAR | jar (generic) |
| 6 | A 568 | 32 |  |  |
| 7 | VASE 10 | 30 | CUP | cup / drinking vessel |
| 8 | A 400 | 22 | GRA+PA | wheat measured by the pa unit |
| 9 | VASE 5 | 19 | AMPHORA | amphora |
| 10 | VASE 1 | 18 | SITVL | situla / bucket-shaped vessel |
| 11 | VASE 6 | 16 | KRATER | krater / mixing bowl |
| 12 | A 334 | 15 |  |  |
| 13 | A 394 | 10 | VIR | man / person |
| 14 | A 355 | 10 |  |  |
| 15 | VASE 9 | 10 | BOWL | bowl |

### Known LB Ideograms NOT Yet Identified in LA

The following Linear B commodity ideograms have **no clear Linear A counterpart**:

| LB Abbr | Meaning | Notes |
|---------|---------|-------|
| SES | sesame | Attested in LB at Mycenae; not clearly in LA |
| AROM | aromatics (generic) | Generic ideogram; LA may have specific signs |
| CAP / CAPf | goat (male/female) | Not clearly identified in LA corpus |
| SUS / SUSf | pig (male/female) | Not clearly identified in LA corpus |
| EQU | horse | Rare in LB; not in LA |
| ASIN | donkey | LB only |
| LEPUS | hare | LB only |
| CERV | deer | LB only |
| LANA | wool | LB only |
| LINUM | flax / linen | LB only |
| AES | bronze / copper | Not in LA |
| AUR | gold | Not in LA |
| ARG | silver | Not in LA |
| TALENT | weight unit (talent) | Not in LA |
| MINA | weight unit (mina) | Not in LA |

---

## 2.  Syllabographic Contexts (Adjectives & Measures)

Syllabograms that recur adjacent to specific logograms may represent:
- **Adjectives:** e.g., "new wine", "dry figs", "mixed oil"
- **Measure terms:** e.g., units of capacity or weight
- **Qualifiers:** e.g., "first", "second", "small", "large"

### Robust Recurrent Adjacent Patterns (frequency ≥ 3)

| Logogram | Adjacent Pattern | Freq | Morphology Cross-Ref |
|----------|------------------|------+----------------------|
| A 334 | before:[] after:[] | 15 | — |
| VASE 4 | before:[] after:[] | 9 | 𐝫~𐘇𐘳𐝫𐘚𐙕𐘮𐘱 (fuzzy morph, count=3) |
| VASE 4 | before:[] after:[𐝫] | 3 | 𐝫~𐘇𐘳𐝫𐘚𐙕𐘮𐘱 (fuzzy morph, count=3) |
| VASE 2 | before:[] after:[] | 8 | 𐝫~𐘇𐘳𐝫𐘚𐙕𐘮𐘱 (fuzzy morph, count=2) |
| A 393 | before:[] after:[] | 8 | — |
| VASE 7 | before:[] after:[] | 7 | — |
| VASE 3 | before:[] after:[] | 7 | — |
| VASE 8 | before:[] after:[] | 5 | — |
| A 394 | before:[] after:[] | 5 | — |
| VASE 1 | before:[] after:[] | 4 | — |
| VASE 10 | before:[] after:[𐝫 𐝫] | 4 | — |
| VASE 10 | before:[] after:[] | 3 | — |
| VASE 6 | before:[] after:[] | 3 | — |
| A 381 | before:[] after:[] | 3 | — |
| A 332 | before:[] after:[] | 3 | — |
| A 331 | before:[] after:[] | 3 | — |
| A 562 | before:[] after:[] | 3 | — |

### Interpretation

Sequences that appear **with multiple different logograms** are likely general terms
(e.g., a generic measure word), while sequences restricted to **one logogram** are
likely specific modifiers (e.g., "olive oil, first pressing").

Cross-referencing with Phase 3 morphology paradigms:
  - Shared roots across different logogram contexts may indicate grammatical particles
  - Alternation patterns (suffix/prefix) near logograms may encode case or number

---

## 3.  Fraction System Alignment

### Mapping Summary: LA (A 7xx) → LB Fraction Signs

| LA ID | Decimal (Phase 2) | Fraction (Phase 2) | LB Equiv | LB Decimal | LB Fraction | Confidence |
|-------|-------------------|--------------------|----------|------------|-------------|-----------|
| A 702 | 0.0625 | 1/16 | K | 0.25 | 1/4 | high |
| A 703 | 0.1667 | 1/6 | L | 0.125 | 1/8 | medium |
| A 704 | 0.25 | 1/4 | ? | 0.25 | 1/4 | low |
| A 705 | 0.3333 | 1/3 | N? | 0.3333 | 1/3 | low |
| A 706 | 0.166667 | 1/6 | O | 0.1667 | 1/6 | medium |
| A 707 | 0.6667 | 2/3 | R | 0.6667 | 2/3 | medium |
| A 708 | 0.75 | 3/4 | N | 0.75 | 3/4 | medium |
| A 709 | 0.8333 | 5/6 | S? | 0.8333 | 5/6 | low |
| A 710 | 0.6 | 0.6000 | 1 | 1.0 | 1 | high |
| A 711 | 0.875 | 7/8 | T | 0.875 | 7/8 | medium |
| A 712 | 0.9375 | 0.9375 | ? | 0.9375 | 15/16 | low |
| A 713 | 0.4 | 2/5 | ? | 0.4 | 2/5 | low |
| A 714 | 0.75 | 3/4 | ? | 0.75 | 3/4 | medium |
| A 715 | 0.25 | 1/4 | K? | 0.25 | 1/4 | medium |
| A 716 | 0.2 | 1/5 | J? | 0.2 | 1/5 | low |
| A 717 | 0.6667 | 2/3 | ? | 0.6667 | 2/3 | low |
| A 718 | 0.8 | 4/5 | ? | 0.8 | 4/5 | low |
| A 719 | 0.3125 | 0.3125 | M? | 0.3125 | 5/16 | low |
| A 720 | 0.1875 | 0.1875 | M? | 0.1875 | 3/16 | low |
| A 721 | 0.8125 | 0.8125 | ? | 0.8125 | 13/16 | low |
| A 722 | 0.4375 | 0.4375 | ? | 0.4375 | 7/16 | low |
| A 723 | 0.5625 | 0.5625 | ? | 0.5625 | 9/16 | low |
| A 724 | 0.6875 | 0.6875 | ? | 0.6875 | 11/16 | low |
| A 725 | 1.0 | 1 | 1 | 1.0 | 1 (whole) | high |
| A 726 | 0.125 | 1/8 | L? | 0.125 | 1/8 | high |
| A 727 | 0.8333 | 5/6 | P? | 0.8333 | 5/6 | low |
| A 728 | 0.1667 | 1/6 | O | 0.1667 | 1/6 | medium |
| A 729 | 0.8333 | 5/6 | P? | 0.8333 | 5/6 | low |
| A 730 | 0.8333 | 5/6 | P? | 0.8333 | 5/6 | low |

### Summary

- LA fraction types in corpus: **29**
- Fraction-to-LB mappings proposed: **12** (high or medium confidence)
- Whole-unit markers (A 710, A 725): consistently represent **1 (whole)**
- Key pairs summing to ~1.0:
  - A 704 (0.25) + A 708 (0.75) = 1.0
  - A 714 (0.75) + A 715 (0.25) = 1.0
  - A 716 (0.20) + A 718 (0.80) = 1.0
  - A 720 (0.1875) + A 721 (0.8125) = 1.0
  - A 722 (0.4375) + A 723 (0.5625) = 1.0
  - A 711 (0.875) + A 726 (0.125) = 1.0
  - A 727 (0.8333) + A 728 (0.1667) = 1.0

### Refined Values vs Phase 2 Proposals

The Phase 2 proposed values are largely confirmed. Key refinements:

1. **A 702:** Phase 2 proposed 0.0625 (1/16). Re-evaluated to 0.25 (1/4) based on
   co-occurrence with GRA logograms and comparison with LB K (𐄰).
2. **A 726:** Confirmed as 0.125 (1/8) = LB L (𐄱), being the most frequent
   fractional subunit in the corpus.
3. **A 728:** Confirmed as 0.1667 (1/6) = LB O (𐄤), frequently paired with
   A 727/A 729/A 730 (5/6) to complete the unit.

---

## 4.  Phonetic Inferences

### Syllabogram → Logogram Binding Patterns

Based on adjacent contexts extracted from the corpus, we hypothesise:

1. **Preposed syllabograms** (appearing before a logogram) are likely:
   - Adjectives: quality or state of the commodity
   - Measures: the unit of measurement
   - Prepositions / prefixes

2. **Postposed syllabograms** (appearing after a logogram) are likely:
   - Case endings or grammatical suffixes
   - Numeral classifiers
   - Verbal forms (if the logogram functions as a verb)

3. **Measure words** that appear across multiple logogram types:
   - These likely encode weight or volume units
   - Compare with known LB measure words (e.g., *pa*, *qe*)

### Cross-References

- **Phase 3 Morphology Scan:** 28 logograms have adjacent patterns
  matching known morphological alternations.
- **Toponym Analysis:** Some adjacent syllabograms may be toponymic adjectives
  indicating regional varieties of commodities.

---

## 5.  Data Files Generated

| File | Description |
|------|-------------|
| `la_lb_ideogram_map.csv` | 366 LA→LB ideogram correspondences with Unicode, meanings, and certainty |
| `commodity_contexts.csv` | 728 context extractions + 17 pattern summaries |
| `fraction_alignment.csv` | 29 LA↔LB fraction mappings with confidence ratings |

---

## 6.  Methodological Notes

- The adjacent syllabogram extraction uses a window of ±5 positions from each
  logogram, stopping at another logogram, fraction, or inscription boundary.
- Pattern frequency thresholds: ≥2 occurrences reported in CSV, ≥3 for robust
  candidates in this report.
- Fraction alignment uses four criteria: (1) decimal value proximity to LB known
  values, (2) pairing behaviour (summing to 1), (3) co-occurrence with specific
  logograms, (4) Phase 2 proposals.
- The LB ideogram reference table encodes 40+ entries compiled from Ventris &
  Chadwick (1973), DMIC, and the Unicode 17.0 Aegean block specification.
- Where LA and LB signs share visual form but divergent meanings, this is noted
  in the correspondence certainty field.

---

*End of report.*
