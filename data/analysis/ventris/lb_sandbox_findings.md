# FINDING: oracle anchor leak + corrupted la_lb_mapping.csv grid

> **See also `oracle_retrace_findings.md` (same day, later):** a full retrace after a
> challenge to the 0.00× result found **three** bugs, not two — including a dead Kober
> constraint channel in the sandbox and one bug in this list's own chance-baseline
> methodology. Read the retrace first; the "conclusion stands" framing below is too strong.

**Discovered** 2026-09-15 while running the Linear B sandbox (`pipeline/lb_oracle.py`).

## 1. Anchor-word leak in `pipeline/ventris/complete.py` (fixed)

`get_candidates()` restricted candidates using the *full* `self.confirmed` grid
during oracle runs. Hidden signs remain in `self.confirmed` (the override only
affects `score_completion`), so a hidden sign that appears in a hardcoded anchor
word (`pa-i-to`, `i-da`) was constrained to its own true value.

- Symptom: LB sandbox recovered exactly AB 01 (da, in `i-da`) and AB 28 (i, in
  `pa-i-to`) at 100% — everything else 0%.
- Fix: `get_candidates(bid, confirmed=None)` + `_greedy_restore` passes
  `confirmed_override` through. Behavior-neutral outside oracle mode.
- **Consequence:** the historical Linear A 0.6× baseline was leaked. Re-running
  the original configuration with the fix: **0.00×**. The 0.6× number is therefore
  invalid as a measurement; whether the corrected 0.00× means "no signal" or
  "broken instrument" is answered in `oracle_retrace_findings.md` (the latter).
- Old LA oracle numbers in prior reports (0.6×) should be read as
  leak-contaminated and re-measured with the fixed code.

## 2. `data/analysis/comparative/la_lb_mapping.csv` grid corruption

Three-way audit (repo grid vs Unicode Linear A and Linear B names):

| Fault | Rows | Detail |
|---|---|---|
| `lb_unicode`/`lb_char` names a different sign | 71/117 | systematic offset; AB 78's `lb_char` = U+1004E, an unassigned codepoint |
| `lb_value` ≠ standard value at that number | 11 | 6 hard conflicts: AB 11 (si→po), 21 (mi→qi), 29 (pu→pu2), 33 (ra→ra3), 42 (ke→wo), 66 (ta→ta2) |
| LA-side `la_unicode` names a different AB sign | subset (drift grows with number) | AB 21→AB22M, AB 42→AB49, AB 78→AB131B while AB 01/02 are correct |

Same position-vs-number class as the Phase 11 unicode_utils fix (144 mappings),
but in the *comparative* file, which Phase 2/5 LB-transfer values are derived
from. At least the 6 hard `lb_value` conflicts need a row-by-row audit before
any further LA claim cites this file. Full rows: `languages/linear-b/data/analysis/lb_grid_vs_unicode_mismatches.csv`.

The Linear B sandbox used the Unicode standard directly and is unaffected.

## Retraction-adjacent decisions

- Keep the corrected oracle numbers in LA reports (0.6× → 0.00×) with a note.
- Do NOT silently rewrite historical reports; amend `verification_audit.md`.
- Grid audit is a new `fix(grid)` work item, not folded into the sandbox.