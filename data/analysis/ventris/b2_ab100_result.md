# B2 — AB 100-137 Grid Entries (Result)

**Date:** 2026-08-13
**Status:** DONE

## The finding

All 48 grid entries in the AB 100-137 range have **0 corpus occurrences**.
They are pure placeholders — the Unicode codepoints they'd occupy (U+10664+)
are actually **A 300+ logograms** (A 301: 274, A 303: 57, A 304: 28, ...).

## The real signs at those codepoints

| Codepoint range | Grid claims | Actually is |
|-----------------|-------------|-------------|
| U+10664+ | AB 100-137 (UNCERTAIN) | A 313B+ logograms (commodity/measure signs) |

## Verdict

**The entire AB 100-137 grid range is phantom** — 48 entries with no real
sign. They were placeholder rows in the grid that never corresponded to
corpus signs. The actual A 300+ logograms are the real signs at those
codepoints.

## Implication for the grid

The grid's total sign count (138) is inflated by ~69 phantoms:
- 19 phantom CONFIRMED (B1)
- 50 phantom UNCERTAIN (AB 100-137 + rare AB)

The real grid working set is ~69 signs (58 confirmed + the real uncertain
ones like AB 41, AB 60, AB 16).

## Output

- `data/analysis/ventris/b2_ab100_result` (this summary)
- The AB 100-137 entries should be purged from the grid
