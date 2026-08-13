# Grid Purge — The Honest 69-Sign Grid

**Date:** 2026-08-13
**Status:** DONE — purged grid produced

## The action

Removed all 69 phantom entries (no valid codepoint OR 0 corpus occurrences)
from `expanded_grid.csv`, producing `expanded_grid_purged.csv`.

## Before → After

| | Original | Purged |
|---|----------|--------|
| Total signs | 138 | **69** |
| CONFIRMED | 77 (19 phantom) | **58** |
| UNCERTAIN | 61 (50 phantom) | **11** |

## The real grid (69 signs)

**58 CONFIRMED:** AB 01-11, 13, 17, 21-31, 34, 37-40, 44-51, 53-59, 61,
65-67, 69-70, 72-74, 76-77, 81, 83, 85, 87

**11 UNCERTAIN (the real open questions):**
- AB 16 (qa, 48.1) — the qa/ka conflict
- AB 41 (si, 25) — **240 occurrences, most frequent UNCERTAIN sign**
- AB 60 (ra, 57.9) — the ra/ma keystone
- AB 78 (qe, 47), AB 80 (ma, 34.1), AB 82 (o, 25), AB 79 (ze, 25),
  AB 86 (lo, 25), AB 20 (zo?), AB 75 (?), AB 84 (?)

## Notes

- AB 37 is CONFIRMED but value `?` (111 occurrences) — a minor inconsistency
  (confirmed as a sign exists, value unknown)
- AB 41 (si) stands out: 2nd most frequent sign, UNCERTAIN, and in the
  formula (si-ru-te, u-na-ka-na-si)
- The phantom AB 68 (ro) is gone — the "Phase 7 resolution" was void

## Outputs

- `data/analysis/bootstrapping/expanded_grid_purged.csv` — the honest grid
- `data/analysis/ventris/phantom_removed.csv` — what was removed
