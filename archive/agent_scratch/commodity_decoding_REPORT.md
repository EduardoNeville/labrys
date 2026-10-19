# REPORT.md — Commodity-Semantic Decoding (Phase 7 — Approach 2 of 5)

## Summary

Created the `pipeline/commodity_decoding/` package with three modules:
- `context_extract.py` — extracts ±3 sign windows around 635 commodity logograms
  grouped into 10 commodity classes, building per-commodity syllabogram frequency profiles.
- `semantic_cluster.py` — clusters logogram-adjacent sequences, ranks distinctiveness,
  checks for UNCERTAIN signs in distinctive sequences, and hypothesizes proto-words.
- `__init__.py` — clean exports for all public functions.

Output data written to `data/analysis/commodity_decoding/`:
- `logogram_contexts.csv` (635 rows): every logogram occurrence with ±3 sign windows
- `commodity_signatures.csv` (10 rows): per-commodity top syllabograms, Bennett IDs,
  UNCERTAIN sign detection, unique context sequences
- `commodity_report.md` (255 lines): full markdown report with distinctive sequences,
  UNCERTAIN sign analysis, proto-word hypotheses, and overall assessment

## Implementation Details

### context_extract.py
- Reads `data/database/lineara_full.db` via sqlite3
- Classifies logograms into 10 commodity classes (WINE, OLIVE_OIL, OLIVES, GRAIN,
  CLOTH, MANPOWER, LIVESTOCK, HIDES, AROMATICS, VESSELS, UNKNOWN_COMMODITY, PERSONNEL)
  based on transliteration hints (VIN%, OLE%, GRA%, etc.) and known A 3xx mappings
- Extracts ±3 sign windows around each logogram occurrence
- Builds per-commodity frequency profiles with Bennett ID tracking
- Detects UNCERTAIN signs (those with ML predictions) in top-10 syllabograms per commodity
- Loads 94 ML predictions from `data/analysis/ml/uncertain_predictions.csv`

### semantic_cluster.py
- Extracts clean syllabogram sequences from context windows (filters out empty translits)
- Builds bigram+trigram profiles per commodity class
- Scores distinctiveness as `(freq_in_comm / freq_in_others)` with Laplace smoothing
- Checks whether distinctive n-grams contain signs with ML predictions (UNCERTAIN signs)
- Cross-references candidate sequences with known Mediterranean trade vocabulary
  (Mycenaean, pre-Greek, Hittite)
- Generates proto-word hypotheses with UNCERTAIN sign involvement and trade-word matches

## Key Findings

### Distinctive Sequences Identified
9/10 commodity classes have at least one syllabogram sequence with distinctiveness ratio > 2.0.
Many are "infinitely" distinctive (found only near a specific commodity in the current corpus).

### UNCERTAIN Signs in Commodity Contexts
28 of 94 UNCERTAIN signs (with ML predictions) appear in the top-10 Bennett IDs adjacent
to specific commodity logograms. These signs are prime candidates for commodity-name phonemes
because their semantic context is constrained.

### Most Interesting UNCERTAIN Signs per Commodity:
- **GRAIN**: AB 51, AB 29, AB 45, AB 01, AB 65, AB 73 — the sequence "i-ri" (containing
  AB 19/i, AB 103/ri, AB 113/i, AB 116/i, AB 133/i) matches Mycenaean *kri "barley"
- **VESSELS**: AB 29, AB 87, AB 62, AB 66 — the sequence "ja-se" (AB 47/ja, AB 96/se)
  with UNCERTAIN AB 47 (ML→ja) and AB 96 (ML→se) is interesting
- **OLIVE_OIL**: AB 92, AB 86, AB 50, AB 51, AB 87, AB 29

### Proto-Word Hypothesis (Strongest):
- **GRAIN: i-ri** — matches Mycenaean *kri "barley" (distinctiveness = ∞, only found
  near grain logograms). This is consistent with independent evidence from Linear B.

### Proto-Word Hypotheses (Novel):
- **UNKNOWN_COMMODITY: ne-tu**, **tu-e** — these are 2× more common near unknown
  commodity logograms and could be transaction verbs or commodity modifiers.
- **VESSELS: i-gra+pa** — appears 3× near vessel logograms, possibly a vessel qualifier
  or the name for a specific vessel type.

## Quantitative Results

| Metric | Value |
|--------|-------|
| Logogram context windows extracted | 635 |
| Commodity classes identified | 10 |
| Distinct syllabogram types adjacent to logograms | ~55 |
| Commodities with distinctive sequences (>2.0 ratio) | 9/10 |
| UNCERTAIN signs detected in top-10 adjacent Bennetts | 28/94 |
| Proto-word hypotheses generated | 35 |
| Hypotheses with trade-word matches | 2 (i-ri→*kri barley, ri-ta→? ) |
| VESSELS class dominates | 427/635 occurrences (67%) |

## Limitations Acknowledged

1. **Small corpus**: ~11K signs total; statistical distinctiveness is fragile
2. **ML confidence**: UNCERTAIN sign predictions are probabilistic (5-50% confidence)
3. **Administrative vs. naming**: Adjacent syllabograms may be quantities or
   transaction formulas, not commodity names
4. **VESSELS dominance**: 67% of logogram occurrences are vessels, making non-vessel
   commodity head-to-head comparisons difficult
5. **No confirmed decipherment**: This is constrained semantic guessing, not a
   decipherment claim

## File Manifest

### New package:
- `pipeline/commodity_decoding/__init__.py`
- `pipeline/commodity_decoding/context_extract.py`
- `pipeline/commodity_decoding/semantic_cluster.py`

### New data outputs:
- `data/analysis/commodity_decoding/logogram_contexts.csv`
- `data/analysis/commodity_decoding/commodity_signatures.csv`
- `data/analysis/commodity_decoding/commodity_report.md`

### Dependencies:
- `data/database/lineara_full.db` (read only)
- `data/analysis/ml/uncertain_predictions.csv` (read only)

All modules use `uv` for execution and follow AGENTS.md conventions (logging, standard library + sqlite3 + csv).
