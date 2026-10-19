# PLAN.md — Step 3: the seven values asserted for unencoded signs

**Status:** ✅ complete (2026-10-19) · **Opened:** 2026-10-19 · **Previous:** `docs/plans/step-2-stale-consumers.md` (✅ complete)

**Convention.** `PLAN.md` holds the active step. Completed plans are preserved under `docs/plans/`;
what each actually changed is in `data/analysis/ventris/verification_audit.md`.

---

## 1. Goal (as written in the audit)

> The seven "value for an unencoded sign" defects (AB 18, 19, 22, 34, 35, 64, 79) — reported, not
> enforced.

`pipeline/guards.py` prints, on every run:

```
  known defects awaiting deliberate re-derivation (NOT enforced):
    asserts a value for an unencoded sign (7): AB 18, AB 19, AB 22, AB 34, AB 35, AB 64, AB 79
```

## 2. What the guard is actually reporting (measured)

The guard's own wording is ambiguous, and that ambiguity is the first thing to fix. Two different
defects are folded into one line:

| # | defect | what it means | count |
| 1 | **an unencoded sign carries a value** | the sign has no Unicode codepoint (or no sign at all), yet a grid row asserts a phonetic value for it | 7 |
| 2 | **a value is asserted where the standard says "unnamed"** | Linear B's standard has no name for that sign number, so any value is a project invention | see below |

Current state, measured from the grids (step 1 output):

| sign | rows in | claimed value | codepoint | corpus occurrences |
| AB 18 | refined, canonical | `zo` CONFIRM in the legacy grid; `?` today | none | 0 |
| AB 19 | refined, canonical | `?` / legacy `zo` | none | 0 |
| AB 22 | refined, canonical | `pi` | none (AB 22 is not an encoded LA sign) | 0 |
| AB 34 | canonical | `ti` (CONFIRM, confidence 55) | yes | 8 |
| AB 35 | refined, canonical | `ti` (legacy CONFIRM) | none | 0 |
| AB 64 | canonical | value asserted | none | 0 |
| AB 79 | canonical | `ze` (UNCERTAIN) | none | 0 |

So the seven split into **three kinds**, and they need different treatment:

- **A. Signs with no codepoint and no occurrences (AB 18, 19, 22, 35, 64, 79)** — these are exactly
  the phantom class step 1 removed from the *other* grids. If they are still in a grid, step 1's
  filter missed a path. **Expected outcome: they should already be gone.** Verify, and if so the
  guard is checking a retired artifact and must be re-pointed at the canonical grids.
- **B. AB 34** — a real sign (8 occurrences, has a codepoint) whose value is asserted with
  confidence 55 while `la_lb_mapping` says `pa2?` and the refined grid's `grid_confidence_score` is
  empty. This is the one *substantive* case the overseer flagged on 2026-10-02. It is a
  corroboration question, not a phantom.
- **C. The standard says "unnamed"** — the Phase 18 audit noted `AB 18/19/22/35/79` are standard
  "unnamed" sign numbers (`B018`, `B019`, …). A value there is an invention by construction.

## 3. Plan

### Task 3.1 — Make the report say what it means

Split the guard's single line into the three classes above, each with its own test and its own
wording. A defect report that conflates "phantom sign" with "unsupported value" cannot be acted on,
and this one has been copied from run to run since Phase 12.

### Task 3.2 — Verify the phantom class is gone

Check each of AB 18, 19, 22, 35, 64, 79 against the canonical grids after step 1. Expected: absent
(the filter is applied at the generators). If any survives, that path is a defect and step 1's
filter must be extended — this is the test that proves step 1 was complete.

### Task 3.3 — Decide AB 34, with evidence rather than by rule

AB 34 is the only case where a real sign carries a contested value. The evidence, measured:

| source | says |
| `la_lb_mapping.csv` | `lb_value = pa2?` — the standard's value with an uncertainty marker |
| `refined_phonetic_grid.csv` | `refined_value = ti`, `decision = CONFIRM`, confidence 55, `grid_confidence_score` **empty** |
| `expanded_grid_purged.csv` | follows the refined grid |
| the corpus | 8 occurrences |

`ti` is not `pa2?`. A CONFIRM at 55 with no grid-confidence term is a single-source promotion —
exactly what Phase 12's policy was written to stop. **Expected outcome: demote to UNCERTAIN and
record why**, unless a second independent source turns up in the evidence files. This changes a
grid value, so it re-runs the downstream chain (cheap now) and needs a Phase 20 entry.

### Task 3.4 — Enforce, or explain why not

Turn the three classes into guard behaviour:

| class | enforcement |
| phantom sign with a value | **enforced** — already covered by guard 20; the report should say "covered by guard 20" rather than duplicate it |
| standard "unnamed" sign carrying a value | **enforced** against the Unicode Linear B standard, unless the value is explicitly marked `?` |
| single-source CONFIRM (like AB 34) | **reported**, with the sign and its sources — a policy question, not an invariant |

### Task 3.5 — Record

Phase 20: the three classes, the AB 34 decision, the final counts, and the guard's new wording.
Update the guard report and `CODE_AUDIT.md` §5/§8 (item 3 closes).

## 4. Verification — results

| check | result |
| `guards.py` | **23/23** (+26 CONFIRM needs corroboration) |
| phantom class absent from the grids | ✅ AB 18/19/35/64 appear in no grid (step 1 covered them) |
| AB 34 | ✅ refined grid demoted to UNCERTAIN; canonical grid keeps it on CM + Kober acceptance (recorded as an instrument disagreement, not a bug) |
| report wording | ✅ split into literature-only (7) vs phantom-range (4); no longer reads as an accusation |
| oracle after the change | ✅ unchanged: 1/160, 0.056×, NO SIGNAL |
| final counts | refined **71 / 34 CONFIRM**; canonical **71 / 53 CONFIRM** |

### Original criteria

1. `guards.py` green, with the new/enforced checks.
2. No grid row asserts a value for a sign with no codepoint.
3. AB 34's status is recorded with its evidence, whichever way it goes.
4. The report distinguishes the classes: a reader can tell what to fix from the line alone.

## 5. Risks

| risk | mitigation |
| the AB 34 demotion changes the canonical grid and the oracle | re-run the chain and the oracle; record the movement in Phase 20 (the verdict has survived every change so far, and the gate is what the claim rests on) |
| the "unnamed" check fires on many signs | measure first; if it is broad, it is a report, not an invariant |
| scope creep into reconciling the two grids | not here: step 3 is about *unsupported values*, not about choosing between the lineages |

## 6. Out of scope

- Reconciling the 53 vs 35 CONFIRM (open item 2).
- The Phase 4 restart (open item 7).
