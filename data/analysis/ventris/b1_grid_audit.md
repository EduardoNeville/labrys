# B1 — Grid Phantom-Sign Audit (Result)

**Date:** 2026-08-13
**Status:** DONE

## The finding

Of 138 grid signs:
- **69 have no valid codepoint** in the corrected mapping (50% of the grid)
- **19 CONFIRMED signs are VOID** (no codepoint, 0 corpus occurrences):
  AB 32 (i, 67), AB 12 (so, 65.3), AB 52 (62), AB 14 (do, 61.9),
  AB 18 (zo, 61.6), AB 15 (mo, 59.3), AB 36 (jo, 59), AB 22F/33/43/112 (pa, 57),
  AB 63 (ke, 55), AB 35 (ti, 54.7), AB 64/68/62/92/96/113
- **50 UNCERTAIN signs** are also codepoint-less (AB 100-137 range)

## The real confirmed set

**58 VALID confirmed signs** (codepoint + in corpus) — matches the earlier
"~58 reliable values" estimate, now confirmed with certainty.

## Key implication

The 19 VOID confirmations were **artifacts of the corrupted mapping** —
their values (i, ro, so, do, mo, zo, jo, pa, ke, ti) were assigned via the
phantom codepoint entries that doubled real signs' codepoints. The grid's
"77 confirmed" was overstated; the true working set is 58.

## Notable

- AB 41 (si, 240 freq) is UNCERTAIN but is one of the most frequent signs —
  a real gap in the grid (it's in the formula: si-ru-te, u-na-ka-na-si)
- AB 68 (ro) — the "Phase 7 resolution" — is VOID: the sign has no codepoint.
  Its resolution was based on a phantom.

## Outputs

- `data/analysis/ventris/phantom_signs.csv` — all 69 codepoint-less signs
- `data/analysis/ventris/grid_validity_audit.csv` — full validity matrix
