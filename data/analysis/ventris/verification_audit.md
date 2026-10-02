# Phase 11 Verification — Claims Audit

> **2026-09-15 addendum:** see the *Phase 12 Addendum* at the end of this file. It
> supersedes Claim 1 (oracle numbers), Claim 2 (which is now **fully void**, not merely
> downgraded), and Claim 4 (numbers), and records five defects in the oracle machinery
> plus four drifted analysis products. Do not cite the tables above without reading it.
>
> **2026-10-01 addendum:** see the *Phase 13 Addendum*. A seventh instrument defect moved
> the Linear B oracle from 0/160 to 1/160 (lift 0.00× → **0.23×**, verdict unchanged:
> NO SIGNAL), and the Dream-RSI method search over the same sandbox is recorded there:
> π₀ is optimal on both splits at every β, K3 decided, Phase 5 not built.

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

*(Phase 13 below: the Linear B instrument repairs and the Dream-RSI method search. Phase 14,
further down: the commodity associations, audited — the one positive that survives.)*

---

## Phase 13 Addendum — the Linear B instrument, and the Dream-RSI method search (2026-10-01)

At stake: `METHOD_CLOSURE_PAPER.md` §6, "the result survives the repair of six defects". A
**seventh** defect was found 2026-09-30 and repaired 2026-10-01. It is the first repair that moves a
number, and it moves it the way that paper would predict: toward chance, not past it.

### D1 — the Kober triples file was a per-process permutation (repaired)

`pipeline/kober/triple_detection.py` enumerated triples by iterating two `set`s of sign ids, so
`triple_id` — and the positional s1/s2/s3 roles — were freshly permuted on every run in a new process.
`lb_oracle.py` step 2 rewrites that file, so every oracle run left a 120,184-line diff on a tracked
data artifact, and because `complete.py:_load_kober` reads the C/V distinction *from the roles*
(s1↔s2, s1↔s3 → C; s2↔s3, s1↔s3 → V), the constraint graph was not reproducible in principle.

Repaired: sort the enumeration, canonicalise the file order. Verified unchanged: same 60,155 triples,
same 2,667 C-pairs, same 2,564 V-pairs. Verified fixed: byte-identical across two independent runs.
**Guard 13** pins it. The roles happened to match, so this repair changed no measurement — it removed
the capacity to change one silently.

### D2 — the oracle's "8 trials" were 2 distinct draws (repaired)

`complete.py:447` called `random.seed(0)` on the **global** RNG from inside `score_completion`, in the
middle of `oracle_test`'s trial loop. Trial 1's greedy restore left that stream in a fixed state, so
trials 2–8 drew the same hidden set.

| trial | chance | hidden set |
| 1 | 0.0374 | A |
| 2–8 | 0.0185 | B (identical in all seven) |
| mean | **0.0208** | = the committed `chance_rate`, exactly |

Repaired with a private `random.Random(0)`. Behaviour-neutral for scoring: all **3,311**
(sign, candidate) component tuples are bit-identical before and after. **Guard 12** fails on a
reintroduction.

### The measured impact

| | before (committed) | after |
| recovery | 0.0000 (0/160) | **0.0063 (1/160)** |
| chance | 0.0208 | **0.0273** |
| lift | 0.00× | **0.23×** |
| distinct hidden sets | 2 | **8** |
| verdict | NO SIGNAL | **NO SIGNAL** |

**Attributed, not asserted.** The hit is `AB 01`, hidden in 1 of 8 trials and recovered there, by a
**tie resolved by candidate-list order**: the unique-argmax rate over these draws is 0.0%, and
evaluated tie-strictly the shipped config still returns 0 recovered. AB 01 is the most frequent sign
in the corpus (640 occurrences) and one of the two signs the original anchor-word leak produced
(1.28×, repaired among the six). So: still below chance, unchanged verdict, and the single positive is
a list-order artifact of the kind this project has now caught four times.

Also corrected: the report's old line "Signs recovered in ALL trials" was a false claim as worded — a
sign hidden once and recovered once does not carry the weight that phrase implies. It now prints the
appearance count (`AB 01 (1/8 trials)`), and `oracle_test` returns `per_sign_trials` so the rate is
interpretable.

### The Dream-RSI method search (`.pi/PLAN.md` phases 0–4)

Recorded here per PLAN §2. Full record in `data/analysis/rsi/`.

- **§6.4 = all-flat, branch 2 — with the denominator corrected.** No channel beats its null, and
  with metrics computed conditional on the truth being knowable (n=500 → 271 identifiable,
  within-subset null) **unique argmax is 0.0% for all nine channels**, `in_argmax` equals its
  mechanical tie rate (morph 66.1% vs 66.8%; entropy 50.2 vs 50.9; prefix 52.8 vs 53.9), and mean
  rank is at the null everywhere. The plan's tie-collapse hypothesis rested on a number about PMI,
  not about the kober channel, and `op5` — its only invented node — already existed as
  `aggregator_bakeoff.py`'s TWO-STAGE aggregator: 0.0% unique argmax, `in_argmax` 8.5% vs a 7.0%
  null.
- **§6.4's question is now answered by search, not by example.** `op2g`
  (`weight_space_search.py`) sweeps the whole 4-channel weight simplex — 1,771 vectors on a 0.05
  grid, dev/holdout split by trial, winner reported once — and **zero vectors recover even one
  hidden value**, on dev or holdout. Restricting to draws where the true value *is* a candidate
  (117 dev / 154 holdout) isolates the question from D4 and the answer is still zero. The identical
  search with a permuted truth finds 2.8% (max 3.8%), and 2.7% (max 6.0%) on the identifiable
  subset: **the true value is less likely to be the unique argmax than a random candidate is.** So
  `METHOD_CLOSURE_PAPER.md` §8's "the objective has no resolution to optimize" holds by search over
  the convex simplex, and PLAN §6.4's tie-break hypothesis is dead for weight vectors generally,
  not merely for the two-stage aggregator that implemented it.
  *Deviation, recorded:* PLAN §13 forbids optimizers. This is a bounded one-shot sweep used to
  falsify a published claim, with a holdout and a matched control for the best-of-N effect, and
  nothing is fed back into a loop — its result confirms §13's reasoning rather than contradicting
  it. It also places the two defects in order: aggregation first (0 of 1,771 vectors, even with the
  answer present), candidate generation second (~46% of draws void), so fixing D4 first would
  recover nothing.
- **Two corrections to earlier claims in this addendum's own series, both recorded rather than
  quietly fixed.** (i) `aggregator_bakeoff.py`'s "67/47/59/100%" figures are *not* stale: three of
  them reproduce as `in_argmax` (ties allowed), which is argmax-set size, not identification —
  morph 67≈66, entropy 47≈50, prefix 59≈53. Only kober's 100% does not (8.9%). `oracle_diagnose`
  part C prints the same ties-allowed quantity under the label "top-1", which is where the
  misreading starts. (ii) The permutation control in `phase0_null_control.py` had 100% membership
  — its "truth" was drawn from the candidate list, while the real truth is a candidate on only
  36.2–54.2% of draws — so it was solving an easier problem than the measurement. The corrected
  analysis (`identifiable_subset.py`, node `op2f`) reaches the same conclusion on a fair
  denominator, and orders the two real defects: **candidate generation voids ~46% of draws before
  any scoring**, and the shipped sum is *below* its own components (5.2% vs 66.1% `in_argmax`).
- **Reference number.** π₀ (`return []`) scores **V = 0.000 on dev and holdout** and is optimal at
  β₁ ∈ {0.5, 1.0, 2.0}; the transcribed control policy scores −4.500 / −3.694 and the post-hoc
  clairvoyant bound the same. Total quality across the whole tree is 0.02. No ranking flips, so the
  negative is not an artifact of the cost calibration.
- **K2** fires on its strict wording (10 replayable nodes < 12) and passes §8.6's (13 nodes ≥ 12);
  both counts are stated in the pool's README rather than reconciled by adding nodes. **K3** is
  decided: no candidate beats the pre-registered reference, Phase 5's entry condition is not met (no
  traversal reaches the same quality with fewer nodes), so Phase 5 was not built.
- **One channel was not covered by any of this, and is now measured.** `frame_link_test.py`'s
  context-profile channel, extended with a same-draw permutation control
  (`op2d-context-profile-class`): **series 1.21× the majority baseline** (2.01× the permutation
  null, n=500 independent draws) → INCONCLUSIVE, below the 1.5× gate. At 73 draws the same
  channel read 1.52×, i.e. above the gate, while the permutation null held at 14.7% across
  both samples — which is how the small-sample read was caught before it was recorded.
- **The (series, vowel) class axis does survive**: 9.6% exact class pick against a 2.4%
  majority baseline (4.00×) and a 2.4% permutation null (3.93×) — the strongest controlled
  result this project has. Recorded as a metric and claimed as nothing more, because the 1.5×
  gate was pre-registered for exact-value lift over uniform chance, and a class is not a value.
- **Why no value-level per-sign channel can be measured here, by construction.** In a syllabary
  one value belongs to one sign. Hiding the sign removes its value from the anchor set, so for
  the only candidate that could be right the anchor support is *empty*: exact value is 0/500
  not because the channel failed but because the design deletes the answer. The hide-N-recover
  oracle can measure class information and cannot measure value identification — a structural
  reason for `METHOD_CLOSURE_PAPER.md` §4.1's result, not only an empirical one.
- **And it would not pay even if it were live.** `op2d` is the tree's only node with a
  substantial positive quality term (s_v = 0.21). Reaching it costs five reveals, so acting
  beats π₀ only if β₁ < 0.142 h/node — a cost model under which only free re-weighting pays,
  never a new channel.
- **And it is not convertible even at β₁ = 0.** `op2e` hands the class over *for free* (an
  oracle restriction) and the shipped scorer still picks the right member of a 2.32-candidate
  class 8.5% of the time against a 47.4% chance rate — **0.18×, worse than random**, the
  signature of an objective that rewards typicality and therefore avoids the truth among its
  class peers. Tie-lenient: 35.2% (0.74×). End-to-end estimate 0.096 × 0.085 = 0.81% absolute
  against a 2.5% uniform chance rate. So the class signal cannot be converted into values by
  this scorer: the binding constraint is the objective, not the channel and not the corpus.
  The within-class prediction was written into the script before the run and held.

---

## Phase 14 — the commodity associations, audited *(2026-10-01)*

The last positively-signed claim in `AGENTS.md`'s verified list: **AB 30 ↔ LIVESTOCK** and
**AB 28 ↔ WINE**, both recorded as surviving Bonferroni. Every sibling in that list has since been
retracted, corrected, or shown to be a class metric, so this one got the toponym treatment:
re-test it against a null matched to its unit of observation, then stratify.

**What was wrong with the null.** `pipeline/ventris/commodity_semantics.py` runs a hypergeometric
test over adjacent *slots* — syllabograms in a ±3-sign window around each commodity logogram.
Slots are not independent draws: windows overlap within a text, and a short tablet's window spans
most of the document. WINE is 10 contexts and 14 slots, so the effective sample is nearer 10 than
14.

**The re-test** (`data/analysis/commodity_decoding/enrichment_audit.py`):

| test | AB 30 ↔ LIVESTOCK | AB 28 ↔ WINE |
| slot level, as committed | p=1.16e-04 | p=7.30e-05 |
| **document level** (the hypergeometric's assumption actually holds) | **p=2.69e-11** | **p=2.63e-05** |
| **site-stratified permutation**, 2,000 reps, each sign's documents-per-site held fixed | observed 31 vs null mean 13.0 / max 24 → **p=0.0005 (floor)** | observed 7 vs null mean 1.3 / max 5 → **p=0.0005 (floor)** |

Not one permutation reached the observed counts. Recall what this control is for: on the toponym
claim, stratifying by genre moved p from 0.00086 to **0.38**. Here it moves nothing, because the
sign footprints are spread across sites (AB 30 inside the population: 30 Haghia Triada, 11 Khania,
2 Zakros, 2 Phaistos) and the association is not a geography effect.

**Corrections the audit produced:**

1. **The Bonferroni family is 122 tests, not 61.** `sign_commodity_enrichment.csv` has 61 rows
   because it holds only the p<0.05 pairs; `bonferroni_alpha` counts every tested pair. So the
   family-wise alpha is 0.05/122 = **0.00041**. Both claims clear it; "survives Bonferroni" is
   right, for a reason slightly different from the one written down.
2. **The document level is more sensitive and surfaces six more pairs** (AB 31, AB 76, AB 41,
   AB 02, AB 81 → LIVESTOCK; AB 27 → WINE). Eight survivors against 0.05 expected by chance. They
   are **candidates of the same kind, not findings**: they have not had the stratified permutation,
   and the two that have, have it.
3. **What the association does not say.** It gives neither sign a meaning or a value. It says a
   syllabogram's *entry context* is enriched with a logogram's *semantic class*. That makes these
   the first **semantic-anchor candidates** in this project — closure paper §7's class 1 — as
   against the distributional class, which is closed. It is the only evidence class here that has
   ever returned a controlled positive.

**Standing result: the two commodity associations are the best-audited claims in this repository
and the only positives to survive a matched null. They remain associations with a meaning class,
not meanings.**

### Phase 14 addendum — the six candidates, tested, and one caveat about counting

The six pairs flagged above as candidates have now had the same stratified permutation, at
20,000 reps (resolution 5e-5, below the family alpha 0.00041):

| pair | documents | null mean ± sd | z | p_perm |
| AB 30 ↔ LIVESTOCK | 31 | 12.9 ± 2.54 | 7.1 | ≤5e-05 |
| AB 81 ↔ LIVESTOCK | 29 | 10.2 ± 2.44 | 7.7 | ≤5e-05 |
| AB 31 ↔ LIVESTOCK | 22 | 7.1 ± 2.14 | 6.9 | ≤5e-05 |
| AB 76 ↔ LIVESTOCK | 16 | 3.6 ± 1.69 | 7.3 | ≤5e-05 |
| AB 02 ↔ LIVESTOCK | 16 | 5.3 ± 1.98 | 5.4 | ≤5e-05 |
| **AB 41 ↔ LIVESTOCK** | 22 | 13.2 ± 2.36 | 3.7 | **4.0e-04** (marginal, at the threshold) |
| AB 28 ↔ WINE | 7 | 1.3 ± 1.00 | — | ≤5e-05 |
| AB 27 ↔ WINE | 8 | 1.3 ± 1.00 | 6.6 | ≤5e-05 |

All eight survive. **But they are not eight discoveries**, and the counting caveat is the whole
point of this addendum:

- **They were selected by the document-level test and then re-tested**, which inflates them. That
  is why the threshold used is the full 122-test family alpha and not something smaller.
- **Six of the eight are LIVESTOCK pairs, and they overlap.** 74 of 107 LIVESTOCK documents carry
  at most one of the six, which rules out a single entry template — but pairwise Jaccard reaches
  0.52 (AB 31/AB 76) and 0.45 (AB 02/AB 81), so they are not independent findings either. They are
  a partially-overlapping **set**, and should be cited as one result with that overlap matrix, not
  as six.
- **AB 41 is the marginal one** (p = 4.0e-04, eight permutations in 20,000). It is also the
  project's key open target — the most frequent UNCERTAIN sign (240 occurrences) — so the claim
  "AB 41 appears in livestock-entry contexts" is the kind of constraint that would matter *if* it
  replicates on a held-out site. It has not been.

**What replication would require:** a held-out site or period, or the same test pre-registered on
`KN Zg 57/58` when its edition prints. Until then these are controlled candidates — the strongest
kind of evidence this project has produced, and still not meanings.

### Phase 14.1 — the replication, and it fails *(same day, pre-registered before the run)*

The requirement above was written hours before it was met, and it is the most informative result in
this file. `cross_site_replication.py` selects pairs on **one site** and tests the fixed set on a
**different site never used in selection**, then swaps the sites.

**Pre-registered prediction:** the three strongest LIVESTOCK pairs (AB 30, AB 81, AB 31) replicate;
AB 41 does not; the WINE pairs are untestable at Khania. **The prediction was wrong, and in the
informative direction.**

Selection on Haghia Triada: 67 pairs clear 0.05/122. Replication on Khania, threshold 0.05/67:

| pair | Haghia Triada | Khania | verdict |
| A 303 ↔ LIVESTOCK | p=1.6e-11 (k=13/55) | p=7.9e-10 (k=29/34) | **replicates — a logogram and its own class** |
| A 301 ↔ PERSONNEL | p=7.2e-88 (k=237/237) | p=7.5e-09 (k=7/7) | **replicates — a logogram and its own class** |
| AB 30 ↔ LIVESTOCK | p=8.8e-10 (k=19/55) | p=4.4e-02 (k=10/34) | **fails** |
| AB 81 ↔ LIVESTOCK | p=1.8e-15 | p=2.7e-01 | **fails** |
| AB 31 ↔ LIVESTOCK | p=1.4e-10 | p=4.2e-01 | **fails** |
| AB 76, AB 02, AB 41 ↔ LIVESTOCK | p ≤ 4.6e-05 | p ≥ 8.3e-03 | **fail** |
| WINE pairs (AB 28, AB 27), MANPOWER, HIDES | p ≤ 4.9e-06 | no population | **untestable** |

**Two of 67 replicate, and both are tautologies** — a logogram co-occurring with the semantic class
that *defines* it. So the pipeline has a working positive control (it detects an association that is
real across sites) while every *syllabogram* association fails to generalise.

**The correction to Phase 14:** these associations are real **within Haghia Triada** and are a
property of that archive's entry conventions, not of the script's commodity notation. The
site-stratified permutation did not catch this because it is a within-site test that pools sites,
and HT supplies 336 of 604 contexts — it measured the HT association correctly and said nothing
about whether it travels. Phase 14's framing ("the first semantic-anchor candidates") was too
strong: what the audit establishes is that HT's livestock entries use a particular syllabogram set,
and that this does not hold at Khania.

**What still stands from Phase 14:** the slot-level null was wrong (windows overlap, the effective
sample is documents); the Bonferroni family is 122, not 61; the document level is more sensitive;
and AB 82↔LIVESTOCK's retraction remains correct. What does not stand is treating the surviving
pairs as candidate semantic anchors for Linear A.

---

## Phase 15 — archive stratification, and why three claims failed it *(2026-10-01)*

Three survivors of every earlier audit were re-tested on this date. Two failed, one passed, and the
reason is a corpus property nobody had written down:

| claim | verdict |
| commodity sign↔class enrichment | **fails cross-site replication** — 2 of 67 pairs, both logogram↔own-class tautologies |
| A 301 "heading/entry-opening marker" | **archive-specific** — see below |
| libation formula | **passes** — 9 occurrences, 5 sites, 9 of 9 texts in documented slot order |

**The corpus property:**

```
Haghia Triada - Portico 11 and Room 13     863 of 1719 inscriptions   (50.2%)
Khania                                     226                        (13.1%)
Haghia Triada - Villa Magazine              96                        ( 5.6%)
```

Half the corpus is one room, and it has its own tablet format. **A pooled positional or
distributional statistic is therefore mostly a statistic about Portico 11 and Room 13.**

**A 301, corrected.** The recorded profile is "logogram, 85% inscription-initial, 229/274 at Haghia
Triada — a heading/entry-opening marker". Pooled, it reproduces (238/274 = 86.9%). Per archive it
comes apart:

| archive | n | at index 0 |
| Haghia Triada - Portico 11 and Room 13 | 231 | **229 (99.1%)** |
| everywhere else | 43 | **9 (20.9%)** — Khania 3/7, Iouktas 1/6, Syme 0/5, Zakros 1/3, Palaikastro 0/2 |

The apparent coincidence in the record is the finding: *229* is both the index-0 count and (nearly)
the Portico count, because they are the same occurrences. A 301 heads tablets **at Portico**, and
does not elsewhere. Stratification has to reach room level, not site level — **two rooms of the same
site disagree**: Portico 229/231 initial, Villa Magazine 0/3, Casa Room 7 0/2, Casa Room 9 0/1.

The AB 85 retraction is **unaffected**: it rests on the attribution of 508 occurrences (a mapping
fact from Phase 11/12), not on this profile.

**The rule, and the tool.** Any positional, distributional or functional claim about Linear A signs
must be computed per archive and reported across archives; a pooled number answers a question about
the largest room. `data/analysis/ventris/archive_stratification.py` runs the check for any sign
(`--sign`), which is also how the rule generalises: A 306, the livestock logogram, is
Khania-weighted (11 of 22 occurrences) and therefore *not* a Portico artifact — the tool
distinguishes the two cases rather than banning pooled numbers outright.

**Why the libation formula passes where the others fail:** it is genre structure spanning five
sites, not a corpus-wide enrichment. The structure that survives this corpus is formula and genre;
the structure that does not is distribution. That is the same conclusion the closure paper reaches
for the Linear B test bed by an entirely different route.

**Applies to the Linear B sandbox too — and there it was tested.** That corpus is *more* skewed
than Linear A's: **KN is 3,326 of 4,794 inscriptions (69.4%)**, PY 1,105 (23.0%). Pooling cannot
manufacture a signal but it can dilute a stratum-specific one away, so both cheap §4
operationalizations were re-run per findspot (`stratify_lb_by_findspot.py`, driving the canonical
implementations rather than copies):

| stratum | words | frame sharing (4 relations) | paradigm A series / unique vs control |
| PY | 6,412 (49.6%) | 0.87 / **1.03** / 0.95 / 1.00× | 14.4% / 14.7% vs 19.1% |
| KN | 5,482 (42.4%) | 0.88 / 1.00 / 0.94 / 0.99× | 14.3% / 16.9% vs 19.7% |
| TH | 740 (5.7%) | 0.90 / **1.15** / 0.95 / 1.01× | 13.6% / 10.7% vs 8.3% |
| MY | 277 (2.1%) | 0.86 / **1.18** / 1.03 / 0.97× | **21.6%** / 2.3% vs 2.3% |
| pooled (§4.3, §4.4) | 12,932 | 0.85 / 0.98 / 0.88 / 0.95× | 13.9% / 12.5% vs 19.4% |

**The negatives survive stratification.** PY is the stratum that mattered — a different archive and
scribal tradition, and more words than KN — and it is flat. Every series-sharing rate sits at
12.1–21.6% against a ~27.4% majority baseline; the eliminative vowel step fires *less* than its own
control in PY (14.7% vs 19.1%) and KN (16.9% vs 19.7%).

Two deviations, both of the kind this file has documented before:

1. **The largest frame ratio is 1.18× (MY) and 1.15× (TH)** on the same relation. With 12 tests
   across strata, one or two at ~1.15× is what multiplicity predicts, and both are below the
   pre-registered 1.5× gate.
2. **TH's "correct when unique" is 5/6 (A) and 4/4 (B)**, against controls of 21.4% and 44.4% —
   the §4.4 small-sample artifact recurring at n=6, one stratum down. The paper already documents
   exactly this shape at n=9 with a control reaching 73.8%; here the *control's* rate is the
   artifact. A careless reader would cite it as "Thera: 83–100% correct".

**Not stratified, and the exposure is named:** §4.1 (the scorer + oracle) and §4.2 (the independent
instrument) need per-stratum scorers, so they remain pooled. For them the risk runs the other way
from the usual one: their pooled result is a *floor* (0.00×), so a stratum-specific signal is the
only thing stratification could reveal, and the weight-simplex sweep (0 of 1,771 vectors, on all
draws) argues the defect is in the objective rather than in anyone's corpus subset.

### §4.1 stratified — the exposure is now closed *(same day)*

`stratify_oracle_by_findspot.py` ran the §4.1 oracle per findspot, with a corpus filtered to the
stratum **and its Kober graph rebuilt from that corpus**: using the corpus-wide triples would inject
other sites' frame structure into the stratum's constraint channel and produce a number about the
pooled corpus wearing a stratum's name.

| stratum | inscriptions | sign tokens | recovery | chance | lift | verdict |
| KN | 3,326 | 16,114 | 0.0125 | 0.0275 | **0.46×** | NO SIGNAL |
| PY | 1,105 | 20,689 | 0.0125 | 0.0275 | **0.45×** | NO SIGNAL |
| TH | 291 | 2,270 | 0.0000 | 0.0507 | **0.00×** | NO SIGNAL |
| pooled (§4.1) | 4,794 | 40,038 | 0.0063 | 0.0273 | 0.23× | NO SIGNAL |

Every stratum is below chance, none approaches the pre-registered 0.5× band edge let alone 1.5×,
and the strata sit slightly *above* the pooled figure only because recovery is a floor effect (1–2
hits in 160 draws). Note PY carries **more sign tokens than KN** (20,689 vs 16,114) on a third of
the inscriptions, so the second archive is not the weaker sample.

**§4.2 on the same filtered corpora** (the instrument is path-parameterised, so only the grid — the
answer key, not corpus data — stays shared):

| stratum | exact value | series vs majority | vowel vs majority |
| KN | 0.0% (0.00×) | 23.1% vs 22.5% (**1.03×**) | 16.2% vs 16.9% (0.96×) |
| PY | 0.0% (0.00×) | 22.5% vs 22.5% (**1.00×**) | 17.5% vs 16.9% (1.04×) |
| TH | 0.0% (0.00×) | 17.5% vs 22.5% (**0.78×**) | 17.5% vs 16.9% (1.04×) |
| pooled (§4.2) | 0.0% | 23.1% vs 22.5% (1.03×) | 16.9% vs 16.9% (1.00×) |

Exact value is 0.0% in every stratum, and neither class metric clears its own majority baseline
anywhere — TH is the largest departure and it is *below* (−0.78×). **All four §4 operationalizations
are now stratified**, and none changes verdict:

| | pooled | per stratum |
| §4.1 oracle | 0.23× NO SIGNAL | 0.46× / 0.45× / 0.00× — NO SIGNAL |
| §4.2 instrument | exact 0.00×; series 1.03×; vowel 1.00× | exact 0.00×; series 0.78–1.03×; vowel 0.96–1.04× |
| §4.3 frames | 0.85–0.98× | 0.87–1.18× (max on one of four relations, small stratum) |
| §4.4 paradigm | A 13.9%, control 19.4% | 12.1–21.6% series; eliminative step below control in both large strata |

**A near-miss, recorded because it is instructive.** The first version of that script patched the
module's corpus path per stratum and then re-read it as the *source* for the next copy, so PY and TH
were scored against an empty corpus — and an empty corpus produced **recovery 0.0187 vs chance
0.0143 = 1.31×, INCONCLUSIVE**: the most interesting-looking number of the whole audit, and pure
plumbing error. It was caught only because the inscription count printed alongside it was 0. The
lesson is the project's oldest one — report the input size next to every number — and the script now
captures the pooled path before any patching, with a comment saying why.
