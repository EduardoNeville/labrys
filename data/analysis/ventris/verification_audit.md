# Phase 11 Verification — Claims Audit

> **2026-09-15 addendum:** see the *Phase 12 Addendum* at the end of this file. It
> supersedes Claim 1 (oracle numbers), Claim 2 (which is now **fully void**, not merely
> downgraded), and Claim 4 (numbers), and records five defects in the oracle machinery
> plus four drifted analysis products. Do not cite the tables above without reading it.

**Purpose:** Verify every finding before synthesis. This audit caught TWO
compromised claims (Avenue 1 AB 85, Avenue 2 AB 82) — both were circular
artifacts of corpus encoding, not independent discoveries.

---

## Claim 1 — Oracle: "scorer has no signal" ✅ CONFIRMED

- **Re-verified:** With the strengthened 4-term scorer (Kober, cross-entropy,
  anchors), hidden confirmed signs still rank the true value 45th/70, excluded,
  and 37th/70 — argmax never right.
- **Robust:** Held across 4 scorer versions, 8-trials × 20-hidden oracle,
  and per-sign isolation. The leakage fix and A+B+C strengthening changed
  nothing (0.11× → 0.59×, still below chance).
- **Note:** the two signs "recovered" (AB 28, AB 01) have 1 candidate each —
  trivial.

## Claim 2 — Avenue 1: "AB 85 is the word divider" ❌ COMPROMISED

- **What I claimed:** AB 85 flagged as #1 positional anomaly (med=0.06, 508 occ)
  → independently confirms word-divider hypothesis.
- **What verification found:**
  - AB 85's transliteration is `*301` (258 occ) / `*306` (2 occ) — **logogram
    numbers**, not syllabogram values.
  - The `word_dividers` table is **empty** — no word-divider records exist.
  - AB 85's grid status is `CONFIRM` with value `?` and confidence 25/100 —
    the "confirmation" is low-confidence, possibly a bootstrapping artifact.
  - The positional anomaly (never medial) is real but its interpretation as
    "word divider" is NOT independently established — it could equally be a
    frequently-standalone logogram/ligature.
- **Verdict:** The positional *fact* (never medial) stands. The *interpretation*
  (word divider) is unsupported — circular or ambiguous. Must be downgraded.

## Claim 3 — Avenue 2: "AB 82 ↔ LIVESTOCK (Bonferroni, 70×)" ❌ COMPROMISED

- **What I claimed:** AB 82 significantly enriched in LIVESTOCK contexts
  (p=0.0002, 70× fold) — the project's strongest lead.
- **What verification found:**
  - Both LIVESTOCK co-occurrences come from the **same inscription (PH10)**,
    where AB 82 appears as `HIDE+[?]` — a **livestock ligature** (hide/skin).
  - AB 82's transliteration is `HIDE+[?]` in 3 of 11 occurrences — the
    commodity pipeline classified those rows as LIVESTOCK.
  - So AB 82's "enrichment" is **baked into the data encoding**: it IS a HIDE
    ligature inside livestock entries. The test rediscovered the encoding.
- **Verdict:** Circular — the association is real in the data but not an
  independent discovery. Must be retracted as a "discovery"; reframed as
  "AB 82 co-occurs with HIDE ligatures in livestock entries" (a data fact,
  not an insight).

## Claim 4 — Avenue 3: "all cryptanalysis signals are frequency artifacts" ✅ CONFIRMED

- **Re-verified:** Zipf alpha identical under token shuffle (1.502 both).
  Bigram reduction 26.7% real vs 18.1% shuffled — ~7pp real, weak.
  Kober V-link cohesion circular (V-links = shared context).
- **Robust:** Null controls (shuffle) are the correct methodology; the
  conclusions hold.

## Claim 5 — Avenue 4: "graph isomorphism untestable + no phonetic correlation" ✅ CONFIRMED

- **Re-verified:** No LB corpus sequences in repo. Community structure
  degenerate (337/345 in one component). Top-degree signs are numerals.
- **Robust:** The 55%-vs-59% correlation comparison was crude but the
  conclusion (centrality ≠ phonetic signal) holds — top-10 syllabogram
  values are phonetically incoherent.

---

## Summary

| Claim | Status |
|-------|--------|
| Oracle: scorer has no signal | ✅ Confirmed |
| Avenue 1: AB 85 word divider | ❌ **Compromised** (positional fact real, interpretation unsupported) |
| Avenue 2: AB 82↔LIVESTOCK | ❌ **Compromised** (circular — HIDE ligature encoding) |
| Avenue 3: signals are artifacts | ✅ Confirmed |
| Avenue 4: untestable + no signal | ✅ Confirmed |

**Bottom line for synthesis:** The only claims that survive verification are
the NEGATIVE ones (oracle, Avenue 3, Avenue 4). The two POSITIVE findings
(Avenue 1 word divider, Avenue 2 livestock) were both artifacts of corpus
encoding. The honest synthesis must present the project's outcome as: **all
computational avenues exhausted; no phonetic or semantic discovery survives
verification; the corpus is below the noise floor; new data is the only path.**

---

## Audit of Prior Phases (2–9) Claims

Beyond my own findings, the synthesis will cite Phase 2–9 results. These were
audited against their source CSVs:

### P1. "77 CONFIRMED anchors" — ⚠️ PARTIALLY OVERSTATED
- 19 of 77 CONFIRMED signs have value `?` (confirmed as category, no value).
- 20/77 low-confidence (<50); only 17/77 ≥70.
- The Phase 5 refined grid confirms only 44 as CONFIRM — the two grids disagree
  by 33 signs. My oracle's "58 anchors" are the intersection of 77-minus-`?`
  minus 19, but ~20 of those are low-confidence.
- **Synthesis must say "~58 values, ~17 high-confidence" not "78 anchors".**

### P2. "17 high-confidence anchors" — ⚠️ 3 ARE DISPUTED
- AB 01 (da), AB 38 (e), AB 50 (pu) are high-confidence in bootstrap grid but
  downgraded to UNCERTAIN in the refined grid — the SAME LB/CM conflicts the
  MASTER_SYNTHESIS flags as unresolved (AB 01 da/ta, AB 38 e/pa).
- **Synthesis must not present these as settled.**

### P3. Toponyms (pa-i-to, i-da) — ⚠️ **pa-i-to FAILS its control; i-da PASSES** (Phase 12)
- **Original claim:** PHAISTOS 95 matches at edit-distance 1 across ~75 inscriptions, 8+ sites;
  IDA 20 matches; "the strongest lexical claims and they hold."
- **Phase 12 re-measurement** (`pipeline/substratum_anchor_test.py`):
  - The tool matches against `signs.transliteration` — **the editor's conventional reading**, which
    *is* the Linear B transfer hypothesis. A hit therefore says "this text contains the sign
    sequence whose conventional reading is PA-I-TO", i.e. it restates the convention. It does not
    independently establish the sign values.
  - Exact recount in sign-ID space: **PA-I-TO 1** (HT120), **I-DA 13**, **DI-KA-TA 0**,
    **SU-KI-RI-TA 1** (PHWa32) — not 95 / 20. The larger figures come from distance-1 fuzzy
    matching with variant normalisation (da/ta conflation, damaged signs).
- **What survives:** the *geographic* correlation (sequence ↔ findspot) is real evidence of the
  same-word-in-two-scripts kind, provided the pattern holds against a shuffled-findspot control —
  which has not been run.
- **Status:** tested in Phase 12 with a findspot control — see the next section. The flagship
  `pa-i-to` claim fails; `i-da` passes and is the project's only surviving positive result.

### P4. "Tyrsenian is the best structural fit" — ❌ OVERSTATED
- AGENTS.md: "Tyrsenian ranks highest structurally (5/8 WALS, 62.5%)".
- Actual candidate_ranking.csv: Anatolian IE #1 (8), Hurro-Urartian #2 (8),
  Tyrsenian #3 (7) — ALL "INCONCLUSIVE (tentative)".
- WALS: no family clearly wins; Anatolian has 8 features at comparable
  confidence to Tyrsenian's 8.
- **Synthesis must say "no family distinguished; several weakly compatible;
  all inconclusive" — not "Tyrsenian best".**

### P5. "Agglutinative morphology" — ✅ SUPPORTED (weakly)
- 24 alternation paradigms exist, but with small attestations. The claim is
  reasonable but rests on limited data.

### P6. Misvalued signs (AB 16, AB 60, AB 80) — ✅ SUPPORTED
- Positional anomaly is real and reproducible (Avenue 1 table). The
  interpretation "misvalued" follows from the anomaly + LB/CM conflict.

---

## Consolidated Verdict for Synthesis

| Claim | Source | Status |
|-------|--------|--------|
| Oracle: no scorer signal | Phase 10c | ✅ Confirmed |
| Avenues 3/4 negative | Phase 11 | ✅ Confirmed |
| Avenue 1 AB 85 word divider | Phase 11 | ❌ Retracted |
| Avenue 2 AB 82↔LIVESTOCK | Phase 11 | ❌ Retracted |
| 77 CONFIRMED anchors | Phase 8 | ⚠️ Overstated (58 values, 17 high-conf) |
| Toponyms pa-i-to/i-da | Phase 3 | ⚠️ **Conditional** (matches the transliteration convention against itself; exact recount 1 / 13, not 95 / 20 — see Phase 12) |
| Tyrsenian best fit | Phase 3 | ❌ Overstated (no family distinguished) |
| Agglutinative morphology | Phase 3 | ✅ Supported (weak) |
| Misvalued signs | Phase 2/5 | ✅ Supported |

**The synthesis's honest case:** the solid results are the toponyms (real,
robust), the misvalued-sign flags (real), and the negative results (oracle +
avenues). The "best family fit" and "78 anchors" claims must be downgraded.

---

# Phase 12 Addendum — Oracle machinery audit and re-derivation (2026-09-15)

Prompted by a challenge to the Linear B sandbox's 0-recovery result. Full narrative:
`oracle_repair_report.md`; sandbox design: `../../LINEAR_B_SANDBOX_PLAN.md`.

## Five defects found and fixed

| # | File | Defect | Linear A impact (measured) |
|---|---|---|---|
| 1 | `pipeline/lb_oracle.py` (sandbox only) | 15-sign uncertain set collapsed the Kober graph to 101 triples / 3 valued partners | none (Linear B only) |
| 2 | `ventris/complete.py:oracle_test` | chance baseline computed with the **full** anchor set, so hidden signs tightened their own candidate lists | **real**: LA chance 0.0841 → **0.0373** |
| 3 | `ventris/complete.py:_load_kober` and `ventris/cryptanalysis.py:load_kober_vlinks` | every triple pair added to **both** C- and V-graphs, deleting the consonant/vowel distinction that is the method | semantics fixed; no measured change to LA numbers |
| 4 | `ventris/complete.py:CONS_SERIES_MAP` | 18 of 74 values missing (`no`, `po`, `pe`, `qo`, `a2`, `a3`, `au`, `dwe`, `dwo`, `nwa`, `pu2`, `pte`, `ra2`, `ra3`, `ro2`, `ta2`, `twe`, `two`) | **none**: LA grid has 52 distinct values, **0 overlap** with the missing set; LA oracle identical with legacy and fixed map (0.0000 vs chance 0.0373 both ways) |
| 5 | `vowel_of` in `complete.py`, plus duplicate copies in `formulaic/analyze.py` and `ventris/positional_oracle.py`, and `parse_cv` in `frequency_constraints/constrain.py` | returned `"?"` for subscripted values, silently dropping those signs' vowel constraints | **none**: no LA grid value carries a subscript |

**Defects 4–5 affected Linear B, not Linear A** (in LB, `no`/`po`/`pe` are frequent real signs).
An earlier draft of the repair report overstated this; corrected there.

**Consolidation:** all phonetic-value logic now lives in one module, `pipeline/phonetics.py`
(one `CONS_SERIES_MAP`, one subscript-safe `vowel_of`), replacing four divergent copies.
Runnable check: `uv run python pipeline/phonetics.py`.

## Claim 1 amendment — oracle numbers corrected

- Old: "0.11× → 0.59×, still below chance".
- Corrected (fixed baseline): **LA recovery 0.0000 vs chance 0.0373 → 0.00×**;
  Linear B 0.0000 vs 0.0208 → 0.00×. The internal `0.11×/0.59×` comparisons are retired.
- Conclusion (no signal) unchanged; the baseline it was measured against was wrong by 2.3×.

## Claim 2 amendment — "AB 85 word divider" ❌ **FULLY VOID**

- Old: "the positional *fact* (never medial) stands; only the interpretation is unsupported."
- **The fact does not attach to AB 85.** The 508-occurrence row in the anomaly file was
  `A 301` — a **logogram** id, not the syllabogram. In the current profile file:
  - `A 301` is **absent** entirely;
  - `AB 85` (syllabogram, transliteration `?`) has **n=8, initial 0.125, medial 0.750,
    final 0.125** — medial-**dominant**, the opposite of a word-divider profile.
- Verdict: the word-divider premise is void on the current data, not merely unsupported.
  `AGENTS.md` still lists a "word divider candidate" for AB 85 in its misvalued-sign list;
  that entry should be removed.

## Claim 4 amendment — cryptanalysis artifacts ✅ stands, numbers updated

- `load_kober_vlinks` had the same all-pairs defect as `_load_kober`; fixed to the file's
  C/V semantics.
- V-link cohesion lift: 0.756× (legacy loader) → 0.787× (fixed) — **below chance either
  way**, so "V-link cohesion is not a signal" holds.

## Re-derived data products (drift, not the fixes)

| product | committed | regenerated |
|---|---|---|
| `positional/anomalous_signs.csv` | 7 signs | **3 signs** (AB 74, AB 23m, AB 21) |
| `formulaic/substitutions.csv` | 9,588 rows | 8,653 rows |
| `formulaic/grid_constraints.csv` | 333 rows | 438 rows |
| `frequency_constraints/constrained_candidates.csv` | 3,200 rows | 3,200 rows, **519 `plausible` flags changed (16.2%)** |
| `frequency_constraints/frequency_report.md`, `formulaic/formulaic_report.md` | — | regenerated |

**Attribution:** none of these diffs come from defects 4–5. No grid value is subscripted and
none falls in the 18 missing map entries (verified: 0 overlaps). They are drift between
committed outputs and current inputs. Clearest case: `positional_profiles.csv` is *newer*
(2026-08-13 22:32) than the `anomalous_signs.csv` derived from it (2026-08-13 20:02), and
recomputing the stated rule (`medial < 0.15`, `n ≥ 5`) from the committed profile file
reproduces the regenerated 3-sign list exactly.

**Repo-hygiene consequence:** several committed analysis outputs are **not reproducible from
the committed inputs**. Any claim citing them must be re-derived from current inputs first
(frequency constraints feed `get_candidates`, so this affects candidate-space analyses too).

### Claims NOT affected by the defects
- Toponyms (pa-i-to, i-da): edit-distance matching on transliteration; no dependency.
- Misvalued-sign ranking (Phase 2) and ML predictions (Phase 4): no dependency on the
  touched constants.

## Phase 12 summary

| Claim | Status after this audit |
|---|---|
| Oracle: no signal | ✅ Confirmed; numbers corrected (0.00× vs chance 0.0373) |
| AB 85 word divider | ❌ **Fully void** (fact belongs to logogram A 301; AB 85 is medial-dominant) |
| AB 82 ↔ LIVESTOCK | ❌ Retracted (unchanged from Phase 11) |
| Cryptanalysis signals are artifacts | ✅ Confirmed; cohesion 0.79× |
| Graph isomorphism untestable | ✅ Confirmed (unchanged) |
| Toponyms, misvalued signs | ✅ Unaffected |
| Committed analysis outputs reproducible | ❌ **No** — 4 products drifted |

---

# Phase 12 — Tier 1: guards + data audit (2026-09-15, later)

Scope agreed with the maintainer: protect the negative result before writing it up.
Deliverables: `pipeline/guards.py`, `pipeline/audit_grid_inputs.py`, `EXPERIMENT_PROTOCOL.md`,
`pipeline/phonetics.py`.

## Guard suite — 7/7 passing

`uv run python pipeline/guards.py` — each guard is a regression test for a failure that
actually happened: value leak, phonetic constants (completeness + subscripts), single
definition of phonetic logic, grid values resolving, candidate override honoured, oracle
chance baseline from effective anchors, glyph columns from Unicode names.

Two new defects were found by the guards within minutes of first running them:

1. **`lo` values in the refined grid** — AB 86–96 all carry `lo`, a Linear A value absent from
the Linear B–derived series map. Fixed by adding `"lo": "LIQUID"` (if a sign is read `lo` it
is a liquid by definition).
2. **59 phantom rows in the legacy 138-sign grid** (`expanded_grid.csv`): AB 86–96 = `lo`,
AB 19/21F/37/39/42/46 …, i.e. the entries Phase 11 recorded as purged. The pipeline's
**default grid was still the legacy file** — `VentrisGridCompleter` and
`run_ventris_endgame` now default to `expanded_grid_purged.csv`, per `AGENTS.md`.

Linear A oracle re-measured on the honest grid: **45 anchors, 24 uncertain, recovery 0.0000
vs chance 0.0945 → 0.00×** (unchanged conclusion; the chance baseline differs because the
honest grid has fewer signs and a sparser link graph).

## `la_lb_mapping.csv` audit (267 rows)

| class | rows | meaning |
|---|---|---|
| glyph columns wrong | **85** | offset-assigned codepoints. **Presentational only** — `visual_sim` is a literal, so no score depends on the glyph |
| `lb_value` **conflict** vs Unicode standard | **7** | AB 11 (si vs po), 21 (mi vs qi), 29 (pu vs pu2), 33 (ra vs ra3), 42 (ke vs wo), 43 (ai vs a3), 66 (ta vs ta2) |
| `lb_value` **missing** (standard has one) | **15** | incl. frequent signs: AB 37 ti, 44 ke, 52 no, 58 su, 59 ta, 61 o, 73 mi |
| `lb_value` **unverifiable** (no Unicode sign for that number) | **7** | AB 18/19 (both claim `zo`), 22, 34, 35, 64, 79 |

**Fixed now:** the 85 glyph rows (in place, verified column-by-column: only the 4 glyph
columns changed), and the root cause — `linear_b_mapping.py` now derives glyphs from Unicode
names via `unicode_utils.correct_glyph_columns()` instead of the hardcoded offsets that caused it.

**NOT fixed (needs deliberate re-derivation):** the 7 conflicts and 15 missing values. They are
substantive — this column feeds the LB-transfer term of `phonetic_grid_refinement.py`.

### Blast radius of the 7 conflicts (measured)

| grid | rows carrying a conflicted sign |
|---|---|
| `expanded_grid_purged.csv` | AB 11 `si` CONFIRM (73.7), AB 21 `mi` CONFIRM (60.4), AB 29 `pu` CONFIRM (63.2), AB 66 CONFIRM with no value (29.5) |
| `refined_phonetic_grid.csv` | AB 11 `si` CONFIRM, AB 21 `mi` CONFIRM, AB 33 `pa` CONFIRM, AB 43 `pa` CONFIRM, AB 29 `pu` UNCERTAIN, AB 42 `?` UNCERTAIN, AB 66 `ta` UNCERTAIN |

Note AB 33 and AB 43: the grids record `pa` for both, matching **neither** the mapping file
(`ra`, `ai`) nor the standard (`ra3`, `a3`) — a third, independent inconsistency. At least
these CONFIRM entries cannot all be right, and every one of them is currently presented as
settled in the project's phonetic grid.

## `fraction_values_proposed.csv` audit (29 rows)

The generator fits values as exclusive complements (`proposed = 1 − partner`) and the file's
notes then cite the pairing as evidence.

| finding | count |
|---|---|
| rows whose proposed value equals its own Linear B equivalent | **1** of 29 |
| rows with an exact 1-complement partner **that the note cites as evidence** | **16** (tautological) |
| rows neither LB-supported nor drawn from the LB fraction series | **23** |

Verdict: the file is largely circular. 16 of 29 values are determined by complementation and
presented with the complement as their justification. Only one value is corroborated by the
Linear B fraction series. **Any claim citing this file must be re-derived**, and the generator's
complement-fitting step must be removed or explicitly labelled before reuse.

## Tier 1 status

| item | status |
|---|---|
| 1.1 glyph columns + root cause | ✅ fixed, verified glyph-only diff |
| 1.1 `lb_value` conflicts/missing/unverifiable | 📋 audited, blast radius measured, **not** silently rewritten |
| 1.1 fraction file | 📋 audited — circular, 16/29 rows |
| 1.3 permanent guards | ✅ 7/7, caught 2 new defects |
| 1.4 `EXPERIMENT_PROTOCOL.md` | ✅ 7 rules + claim checklist |
| 1.2 reproducibility entry point | ⏸ deferred to after the write-up (drift documented) |

---

# Phase 12 — Linear A grid inputs: `lb_value` repaired (2026-09-15)

## What was applied

`pipeline/fix_mapping_values.py --apply` corrected `data/analysis/comparative/la_lb_mapping.csv`:

| class | rows | action |
|---|---|---|
| `lb_value` **conflict** with the Unicode LB standard | 7 | corrected (AB 11 si→po, 21 mi→qi, 29 pu→pu2, 33 ra→ra3, 42 ke→wo, 43 ai→a3, 66 ta→ta2) |
| `lb_value` **gap** for a cognate sign | 12 | filled from the standard (AB 32 qo, 37 ti, 44 ke, 52 no, 58 su, 59 ta, 61 o, 71 dwe, 72 pe, 73 mi, 75 we, 85 au) |
| `attestation = la_only` | 3 | **left as '—'** — the generator's own rule is that signs with no LB cognate carry no value (my earlier audit had over-flagged these) |
| no Unicode LB sign for the number | 7 | left untouched (literature readings: AB 18/19 zo, 22 pi, 34 pa2, 35 ti, 64 swi, 79 zo) |

Priors are preserved in a new `lb_value_prior` column plus `lb_value_source`; every edit is itemised in
`la_lb_mapping_value_fixes.csv`. Post-fix audit: **glyph wrong 0, conflicts 0, gaps 0**, guards 7/7.

**Evidence that these were errors, not scholarly divergence:** the generator documents `lb_value` as
"Phonetic value in Linear B (Ventris & Chadwick)" for the cognate sign; of the project's own grid
signs with a conventional value, **39 agree with the LB standard by number and 4 do not**; and 6 of
the 7 conflicts are *another sign's* standard value (AB 11 'si' = AB 41's, 21 'mi' = AB 73's,
29 'pu' = AB 50's, 33 'ra' = AB 60's, 42 'ke' = AB 44's, 66 'ta' = AB 59's), while the 7th ('ai') is
not a Linear B value at all. All 7 rows carried `la_hyp_value` identical to `lb_value`, so no
independent second opinion was discarded.

## The measured cascade — held for review, not adopted

Regenerating `phonetic_grid_refinement.py` from the corrected mapping changes **27 of 138 grid rows**:

| change | detail |
|---|---|
| **CONFIRM count 44 → 54** | 10 promotions (AB 29, 42, 48, 49, 51, 52, 56, 58, 59 …), 2 to REVISE (AB 47, 65), 1 demotion (AB 22F CONFIRM→UNCERTAIN) |
| value corrections in the grid | AB 11 si→**po**, 21 mi→**qi**, 29 pu→**pu2**, 33 pa→**ra3**, 42 →**wo**, 43 pa→**a3**, 66 ta→**ta2**, 71 ke→**dwe**, 32 i→**qo**, 37 ?→**ti**, 62 ta→**?** |
| **anomaly needing review** | **AB 38 `e` → `pa`** — a *worse* value than the standard (B038 = *e*), and the opposite direction to the fix |

**Decision: the regenerated products were reverted** (`refined_phonetic_grid.csv`,
`grid_changes_from_ab.csv`, `misvalued_signs_resolution.csv`, `phase5_synthesis.md`); only the input
correction is retained. Reasoning, per `EXPERIMENT_PROTOCOL.md`:

1. The 10 promotions rest on a **single column** of LB-transfer conjecture. This project's own audit
   (P1/P2) already holds that CONFIRM should reflect corroborated evidence, not one source — and
   these 10 signs were UNCERTAIN precisely because that evidence was missing.
2. AB 38 moving `e`→`pa` shows the regeneration is not a pure improvement; adopting the whole diff
   would import a regression.
3. **Open policy question:** may single-source LB transfer grant CONFIRM at all? Until that is
   answered, adopting a +10 CONFIRM change would alter the project's headline claim
   ("~44 of 138") without new evidence.

**Pending work items created by this:**
- review the 7 value corrections (one line each in `la_lb_mapping_value_fixes.csv`);
- decide the CONFIRM policy for single-source LB transfer, then regenerate the grid and its
  consumers in dependency order (grid → kober `grid_series` → frequency constraints → ML labels →
  phylogenetics), diffing each step;
- **new grid-level inconsistency found:** AB 45's conventional value is `ri` while both the mapping
  and the standard say `de` (B045 = *de*) — not caused by the mapping fix, needs its own review;
- AB 18/19/22/34/35/64/79 remain literature-dependent (no machine-checkable check exists).

---

# Phase 12 — CONFIRM policy applied, cascade adopted (2026-09-15)

**Maintainer decision (supersedes the hold above):** correct the values, suppress single-source
promotions.

## Policy implemented in `phonetic_grid_refinement.py`

| situation | old rule | new rule |
|---|---|---|
| value agrees with a **known** conventional value | CONFIRM | CONFIRM (unchanged) |
| no conventional value, **≥2 sources** agree | CONFIRM | CONFIRM (unchanged) |
| no conventional value, **1 source** | **CONFIRM** | **UNCERTAIN** — awaiting corroboration |
| known conventional value, ≥2 sources propose another value | REVISE | REVISE (unchanged) |
| known conventional value, **1 source** proposes another value | CONFIRM if the source is LB, else REVISE | **REVISE** (symmetric — LB no longer privileged) |

A second defect was fixed at the same time: `la_hyp_value` duplicated the wrong `lb_value` on all 7
conflict rows, and the refinement reads `la_hyp_value` **in preference to** `lb_value`, so the first
pass of the mapping fix did not reach the grid at all. `fix_mapping_values.py` now corrects both
columns and is idempotent.

## Resulting grid

**CONFIRM 44 → 40.** 12 demotions, 8 promotions (all multi-source).

The 7 corrected signs no longer sit behind rubber-stamped confirmations — they now report what is
actually known:

| sign | was | now | note in the grid |
|---|---|---|---|
| AB 11 | `si` **CONFIRM** | `po` UNCERTAIN | HIGH CM=/si/ vs LB=/po/ — genuine conflict |
| AB 21 | `mi` **CONFIRM** | `qi` UNCERTAIN | Conflict: LB=/qi/; CM=/mi/ |
| AB 29 | `pu` UNCERTAIN | `pu2` **REVISE** | Single source LB suggests /pu2/ vs conventional /pu/ |
| AB 33 | `pa` **CONFIRM** | `ra3` UNCERTAIN | Single source LB proposes /ra3/; awaiting corroboration |
| AB 42 | `?` UNCERTAIN | `wo` UNCERTAIN | Single source LB proposes /wo/; awaiting corroboration |
| AB 43 | `pa` **CONFIRM** | `a3` UNCERTAIN | Single source LB proposes /a3/; awaiting corroboration |
| AB 66 | `ta` UNCERTAIN | `ta2` UNCERTAIN | Conflict: LB=/ta2/; CM=/ta/ |

Four signs that the project presented as confirmed (AB 11 `si`, AB 21 `mi`, AB 33 `pa`, AB 43 `pa`)
are now flagged as unresolved, and three of them are **Linear B vs Cypro-Minoan conflicts** — the same
category as the AB 16/60/80 misvaluation flags. The 8 promotions (AB 51 du, 52 no, 56 pa, 58 su,
59 ta, 72 pe, 73 mi, 85 au) each rest on ≥2 sources (typically LB transfer plus CM triangular
inference, sometimes with grid confidence agreeing or dissenting — the dissents are recorded in the
note).

## Cascade regenerated (dependency order)

| product | result |
|---|---|
| `refined_phonetic_grid.csv` | CONFIRM 44 → 40; 12 value changes |
| `kober/grid_series.csv`, `positional_clusters.csv`, `cluster_members.csv` | regenerated |
| `frequency_constraints/constrained_candidates.csv` | eliminations **378 (11.8%) → 96 (3.0%)** — the constraint stage had been eliminating 3× more candidates on the old series assignments |
| `formulaic/*`, `positional/anomalous_signs.csv` | regenerated |

## Still pending (flagged, not silently regenerated)

**25+ modules read `refined_phonetic_grid.csv`**, including `pipeline/ml/*` (training labels),
`pipeline/phylogenetic/*`, `pipeline/verification/*`, `pipeline/ventris/diachronic_prior.py`,
`pipeline/eteocretan/*`, `pipeline/anatolian_search/*`. Their committed outputs are now stale with
respect to the corrected grid. Regenerating them is a research task with review, not a data fix;
the ML pipeline in particular would need a training run whose result cannot change any live
conclusion (Phase 4 already reported 0 high-confidence predictions).

Also open: AB 45's grid value `ri` vs standard `de`; the 7 literature-dependent values; the 59
legacy-grid phantoms; the fraction-file circularity (16/29 rows); the deferred reproducibility
entry point.

---

# Phase 12 — Substratum anchor test: the last evidence class, measured (2026-09-15)

**Question.** Every method that failed so far inferred values from distribution *within* Linear A.
The one untested class was lexical: Minoan words survive inside Linear B, written in a script whose
values are known, so an LA word aligned to an LB word would read off the unknown signs' values. Run
by `pipeline/substratum_anchor_test.py` (hole-filling against an 8,633-word LB value-lexicon, plus
a hold-out test hiding one known position per word, plus a permuted-transfer control).

## Measured result

| quantity | value |
|---|---|
| LA word units in the consensus segmentation | 2,136 (716 of them single-sign) |
| words dropped for characters absent from the mapping | 1,251 |
| **LA words with a complete transferred spelling** | **86** |
| hold-out: trials / unique fill / correct fill | 370 / 24 / **7 (1.9%)** |
| permuted control | **0 of 1,850 (0.0%)** |
| LA words with holes and a unique LB counterpart | 2 |
| new sign values proposed | 2 — **both on phantom-range signs (AB 102, AB 118)** |
| known anchors recovered exactly | su-ki-ri-ta ✅ (AB 58-67-53-59); pa-i-to ✗, i-da ✗, di-ka-ta ✗ |
| random 3-value sequence within distance-1 of an LA spelling (control) | 0.7% |

**Gate correction.** The script printed PASS on a ratio-to-zero (real 1.9% vs control 0.000). That is
a degenerate comparison, not a pass: with 86 usable words and a 1.9% recovery rate, the practical
yield is two values, both on signs AGENTS.md records as phantoms. The honest reading of the absolute
numbers is that **the lexical anchor is near-empty on the current corpus**.

## Why it is near-empty — three structural reasons

1. **LA words are tiny.** The corpus's word units are 716×1 sign, 68×2, 46×3, 29×4 … Only ~101 words
   reach three signs at all, so there is almost no aligning context to constrain a value.
2. **Most signs are outside the mapping.** 1,251 word units contain a character with no entry in
   `la_lb_mapping.csv` (including U+1076B alone, 2,170 occurrences) — so most of the corpus cannot be
   transliterated at all.
3. **Shared vocabulary with Linear B is thin.** The LB lexicon is Greek administrative vocabulary;
   the overlap with Minoan usage is names and places, which is exactly the material the toponym
   method already used.

## Consequence for the project

All four evidence classes available *within the existing data* are now measured:

| class | status |
|---|---|
| Distributional (frames, paradigms, contexts) | **closed** — 0.00×–1.03× with controls (`method_closure.md`) |
| Lexical / substratum | **near-empty** — 86 usable words, 2 yields, both phantoms (this section) |
| Toponyms | **conditional** — matches the convention against itself; exact recount 1 / 13, not 95 / 20 (P3 amendment) |
| Accounting / commodity semantics | weak and partly circular (fraction file 16/29 rows) |

**Therefore no further analysis of the existing corpus will produce a decipherment.** The remaining
paths all require material that does not exist in the repository: a bilingual, a longer text with
recognisable content (`KN Zg 57/58`), or a deciphered neighbour reachable through Cypro-Minoan —
whose one lever is that the Cypriot Syllabary at the far end *is* deciphered, making that chain a
hypothesis test rather than an inference.

---

# Phase 12 — Findspot control on the toponym claim (2026-09-15)

The one validation the toponym claim never received: the *reading* comes from the transfer
convention, but the *findspot distribution* is independent data. Run by
`pipeline/toponym_findspot_control.py` (pre-registered pairs and gate in that file; 10,000 site-label
permutations preserving site sizes; exact binomial tails; Bonferroni over 7 pairs).
Corpus context: 1,719 inscriptions, 53 sites, **Haghia Triada = 64.5%**.

## Match quality first — the file counts rows, not inscriptions

| fact | value |
|---|---|
| rows in `toponym_anchors.csv` | 137 |
| **distinct (spelling, inscription) pairs** | **120** (e.g. `PHWa32` counted twice for su-ki-ri-ta) |
| matches at distance 0 (exact) | **21** |
| matches at distance 1 (fuzzy) | **116 (85%)** |
| `pa-i-to` patterns used | 79× `"PA TO"` — a **2-syllable truncation of a 3-syllable name**, dropping the *i* — plus 7× `"PA I TO"` |

Most of the corpus's "95 Phaistos matches" are therefore 2-glyph fuzzy hits, and the counts are
inflated by re-matching the same inscription with different patterns.

## Result under the naive null, then under the correct one

| spelling | expected | distinct matches | exact | at expected | by chance | p (naive) | **p (genre-matched)** |
|---|---|---|---|---|---|---|---|
| pa-i-to | Phaistos | 78 | 1 | 3 | 3.30 | 0.65 | 0.86 |
| di-ka-ta | Palaikastro | 8 | 0 | 0 | 0.13 | 1.00 | 1.00 |
| i-da | peak sanctuaries | 19 | **19** | **4** | 0.44 | **0.00086** | **0.38** ← retracted |
| su-ki-ri-ta | Phaistos | **2** | 1 | 1 | 0.08 | 0.004 | 0.0002 (n=2 — not evidence) |
| ko-no-so, ku-do-ni-ja, tu-ri-su | — | **0** | 0 | — | — | — | — |

**Why the naive null was wrong.** `i-da`'s four sanctuary matches are all `Za`-series texts
(IOZa11, KOZa1, NEZa1, SYZa1) — the libation-table genre, which is itself **33.7% at peak
sanctuaries** (30 of 89) against 2.3% for the corpus. Drawing each match's site from its own
genre instead of from all inscriptions moves the p-value from 0.00086 to **0.3798**: the apparent
geographic signal is genre, not geography. This is the third time in this project that a "positive"
dissolved on inspection of its null (after the 1.28× anchor leak and the 6.4× junk-label baseline).

**Standing result: no toponym survives as controlled evidence.**

- `pa-i-to` — the flagship claim — is a truncation artifact: 3 of 78 distinct matches at Phaistos
  against 3.3 expected, i.e. no signal at all.
- `di-ka-ta` — 8 fuzzy matches, none at Palaikastro. The three names with zero matches follow.
- `i-da` — retracted (genre).
- `su-ki-ri-ta` — **one** distinct exact 4-sign match, `PHWa32` at Phaistos, with a second row that
  is the same tablet re-matched. A single exact spelling at the right site is a data point, not a
  result; and all four of its signs already have standard-derived values, so it yields nothing new.

## Where this leaves every evidence class in the existing corpus

| class | status after this test |
|---|---|
| Distributional (frames, paradigms, contexts) | **closed** — 0.00×–1.03× against controls (`method_closure.md`) |
| Lexical / substratum | **near-empty** — 86 usable words, 2 yields, both phantoms |
| Toponyms | **no controlled signal** — flagship falsified, `i-da` retracted, one singleton exact match |
| Accounting / commodity semantics | weak, and the fraction file is 16/29 circular |

The instrument that came out of the exercise is worth keeping: a pre-registered geographic gate with
a **genre-stratified** permutation null now exists and can falsify or credit any future candidate
anchor (from a new text, from Cypro-Minoan, or from a newly proposed place name) in one command.

**Conclusion of the Phase 12 audit series: the existing corpus contains no anchor capable of
deciphering Linear A. Progress requires material the repository does not hold.**
