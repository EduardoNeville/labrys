# B1 + B2 — The Grid's Phantom Signs (Combined Finding)

**Date:** 2026-08-13
**Status:** DONE — the grid has 69 phantom signs

## The core discovery

The grid (`expanded_grid.csv`) contains **138 sign entries, of which 69 have
NO valid codepoint** in the corrected Unicode mapping. These are phantom
entries — they never corresponded to real signs in the corpus.

## Breakdown

| Category | Count | Details |
|----------|-------|---------|
| VALID confirmed | 58 | real signs with codepoint + corpus presence |
| VOID confirmed | 19 | AB 32(i,67), AB 68(ro,41), AB 36(jo,59), AB 12/14/15/18/22F/33/35/43/52/62/63/64/92/96/112/113 |
| UNCERTAIN w/o codepoint | 50 | AB 100-137 (48) + AB 19/21F/42/88-99 (rare) |

## The AB 100-137 range (B2)

All 48 AB 100-137 grid entries have **0 corpus occurrences**. Their Unicode
codepoints (U+10664+) are actually **A 300+ logograms** (A 301: 274,
A 303: 57, A 304: 28). The grid's AB 100-137 rows are placeholders for
signs that don't exist.

## Impact on prior findings

1. **AB 68 (ro) — the "Phase 7 resolution" — is VOID.** Its resolution was
   based on a phantom codepoint. The sign doesn't exist with a valid
   codepoint.
2. **AB 36 (jo), AB 32 (i), AB 12 (so), AB 14 (do), AB 15 (mo), AB 18 (zo)**
   — all CONFIRMED at high confidence — are VOID.
3. **The real confirmed set is 58, not 77.** The "78 anchors" was inflated
   by ~19 phantoms.
4. **AB 41 (si) is the notable real gap**: UNCERTAIN but 240 occurrences
   (2nd most frequent sign). It's in the formula (si-ru-te, u-na-ka-na-si).

## The honest state of the grid

After two correction rounds (144 mapping errors + 29 phantom codepoints)
and this audit, the grid's reliable core is **58 confirmed signs**. The
phantom entries (AB 100-137, AB 12/14/15/18/19/32/33/35/36/42/43/52/62/63/
64/68/71/88-99) should be **purged** from the grid — they represent nothing
real and their presence inflates the apparent progress.

## The defensible core (58 confirmed)

AB 01-11, 13, 16, 17, 21-31, 34, 37-41, 44-51, 53-61, 65-70, 72-87
(exact list in `grid_validity_audit.csv`)

## Next step (recommended)

**Purge the grid** — produce a corrected `expanded_grid.csv` with only the
69 real signs (58 confirmed + real uncertain), removing the 69 phantoms.
This gives the project an honest, defensible grid for any future work.
