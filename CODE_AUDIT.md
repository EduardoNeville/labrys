# Code audit — what is live, what is concluded, and what was a wrong turn

**Date:** 2026-10-19 · **Scope:** everything under `pipeline/`, `data/analysis/`, `tools/`,
plus the root markdown. **Method:** import graph, generator tracing (which script writes which
committed artifact), a re-run of the reproducibility-critical scripts, and a claim-by-claim pass
over the root docs against `data/analysis/ventris/verification_audit.md`.

**Second pass (same day):** `CLEANUP_PLAN.md` moved 36 concluded modules (~16.6k LOC) into
`legacy/`, leaving `pipeline/` at 62 files / 34k LOC. This document is the status of what
remains; that one is the record of what moved and why.

**Why now.** The project is about to be shown to an external specialist (Ferrara / CM + CHIC).
A collaborator who clones this repo must be able to tell a live number from a retracted one,
and must not be able to build on the wrong turns. Before this audit, **five of the root
documents carried superseded numbers, ten modules defaulted to a grid with 69 signs that do
not exist, three retracted avenues were still importable, and the canonical grid had no
generator.**

Nothing here weakens a surviving result. It removes the ability to be misled by a dead one.

---

## 0. The five states a file can be in

| state | meaning | action |
| **CORE** | imported, exercised by guards, changes ripple | protect; never let a retraction land silently |
| **INSTRUMENT** | produces or checks a recorded number | keep; record its gate and its verdict |
| **RECORD** | a concluded avenue: the negative is the result | keep frozen; do not extend, do not re-tune |
| **STALE** | reproduces, but an input it reads has since moved | flag; re-derivation is a review task, not a build step |
| **ARCHIVED** | premise falsified, or a wrong turn | `archive/`, with the falsifying number in the header |

The failure mode this taxonomy exists to stop: **a module that reproduces perfectly and is
therefore trusted, while the claim it encodes has already been retracted.** `misvalued_signs_resolution.csv`
was exactly that — generated deterministically, one of its rows asserts `AB 85 = au CONFIRM`,
and `AB 85` is the sign whose 508-occurrence profile turned out to belong to the logogram
`A 301`.

---

## 1. Inventory

97 files in `pipeline/` counting `__init__` (~50k LOC) — **84 modules**, plus 10 audit scripts
under `data/analysis/` and 1 tool script. By state:

`pipeline/` after the cleanup: **62 files** (57 modules + 5 package inits), ~34k LOC — down from
97 files / 50k LOC. Of the 57 modules:

### CORE — 12 modules

`models.py`, `database.py`, `config.py`, `ingest.py`, `unicode_utils.py`, `phonetics.py`,
`exporters.py`, `cli.py`, `parser_sigla.py`, `parser_tei.py`, `sample_corpus.py`, `purge_grid.py` (new)

The canonical data model, the corpus, the Unicode mapping, the one phonetic-value implementation
(`phonetics.py` — four drifted copies were consolidated into it), and the CLI. `purge_grid.py` is
new in this audit: it is the missing generator for `expanded_grid_purged.csv` (see §5).

### INSTRUMENT — 23 modules, the part of the repo that is actually load-bearing

| group | modules | what it decides |
| oracle / gate | `lb_ingest.py`, `lb_oracle.py`, `ventris/complete.py`, `repaired_instrument.py`, `aggregator_bakeoff.py`, `oracle_diagnose.py` | whether any scorer has signal (answer: 0.00×, 0/160) |
| channel probes | `frame_link_test.py`, `paradigm_slot_probe.py`, `local_vowel_test.py`, `vowel_recovery_test.py`, `series_filtered_oracle.py`, `substratum_anchor_test.py` | whether an evidence channel beats its own null |
| controls | `toponym_findspot_control.py`, `audit_grid_inputs.py`, `fix_mapping_values.py`, `guards.py` | whether a claim survives its control |
| cross-script | `cm_acceptance_test.py`, `comparative_bridge.py` | the one pre-registered PASS (44.65×, 45/54) |
| method search | `rsi_tree.py`, `rsi_evaluate.py`, `rsi_replay.py`, `rsi_policy.py`, `rsi_loop.py` | replayable pool of 18 method hypotheses; π₀ optimal ⇒ stop |

### RECORD — 21 modules, concluded avenues (frozen)

Phases 2–3 (positional, segmentation, n-gram, network, co-occurrence, logograms, morphology,
Swadesh, WALS, loanword, toponym, falsification, deep loanword mining), the Phase 5 comparative
chain (LA↔LB mapping, CM bridge, commodity alignment, grid refinement), the parts of Phase 7–9
that are import targets or generators (`kober/*`, `bootstrapping/grid_expand`,
`commodity_decoding/context_extract`), and the Phase 11 negative `ventris/commodity_semantics.py`.

**These are not dead code.** Each records a measured negative or generates an artifact a claim
rests on. The rule is: **frozen**. A "small fix" to a concluded avenue is how a negative becomes
an unearned positive.

### LEGACY — 28 modules in `legacy/` (moved out of `pipeline/`)

The other 16 concluded modules plus all 12 STALE ones: `legacy/{ml,verification,eteocretan,
anatolian_search,phylogenetic,formulaic,frequency_constraints,egyptian_bridge}/` and five
standalone modules. Importable, never imported by `pipeline/` (guard 16). Old→new path map and
the per-module reason: `CLEANUP_PLAN.md` §3.

**Status: flagged, not regenerated — deliberately.** Regenerating the ML pipeline cannot change
a live conclusion (Phase 4 reported 0 high-confidence predictions), and re-running the rest is a
research task with review. Doing it inside a cleanup commit is how a repo acquires numbers
nobody checked.

### ARCHIVED — 6 modules + 3 root docs

See `archive/README.md`. Summary in §2.

---

## 2. What was wrong, with the number that killed it

Different from a bug: these were *plausible* lines of attack, each closed by a measurement.
The measured number is the only thing that should ever be cited as the reason.

| # | the turn | the number that closed it |
| 1 | **Optimizer family** — GPU MCMC, annealing, weight search over the Ventris scorer | oracle **0.00× / 0 recovered** (0/160); exhaustive sweep **0 of 1,771** weight vectors recover one value. `method_closure.md`: *no optimizer can help an objective with no gradient.* |
| 2 | **Frame/paradigm control (Ventris's actual method)** | 4 operationalizations all at or below chance; the apparent 9/9 vowel complement was **12.5% unique vs 19.4% control** — beaten by its own null |
| 3 | **Diachronic prior** (MM-attested ⇒ CONFIRMED) | p=0.0003 → **p=0.1748** after the corpus correction; corpus is 76% one destruction horizon, so the prior was never identifiable |
| 4 | **`AB 85` word divider** | the 508 occurrences belong to logogram **A 301**; real AB 85 is n=8, **medial-dominant 0.75** — the opposite profile |
| 5 | **`AB 82 ↔ LIVESTOCK`** | circular: AB 82's transliteration is literally `HIDE+[?]` in livestock entries. The test rediscovered the encoding |
| 6 | **Commodity semantic anchors** (AB 30↔LIVESTOCK, AB 28↔WINE) | real inside Haghia Triada (p=2.7e-11), **2 of 67 pairs replicate at Khania and both are logogram↔own-class tautologies**; every syllabogram association fails |
| 7 | **Toponym `pa-i-to`** | 95 "matches" were distance-1 fuzzy hits against the transliteration convention itself; exact recount **1**. `i-da` (13 exact) survives its findspot control |
| 8 | **`A 301` "entry-initial heading"** | 229/231 at HT Portico 11 + Room 13, **9/43 elsewhere** — that room's tablet format, not a property of the script. Two rooms of the same site disagree |
| 9 | **Fraction values** | 16 of 29 rows are determined by complement-fitting and then cite the complement as evidence; **1 of 29** is corroborated by the LB fraction series |
| 10 | **CFS "78 anchors"** | 19 were phantom signs; real count **58 CONFIRMED in 69 real signs** |
| 11 | **Phase 4 ML** | built, cached, and never validated; 0 high-confidence predictions, and its inputs have since moved. Not a wrong turn so much as an **unfinished** turn. Now in `legacy/ml/` |

**The pattern across all eleven.** Every one of them was *a real structure in the data* that did
not survive being asked "compared to what?". The recurring defect is not arithmetic, it is the
missing control: no null, or a null drawn from the wrong unit (slots instead of documents, one
archive instead of several). That is why `EXPERIMENT_PROTOCOL.md` rule 2 and the archive
stratification requirement exist.

---

## 3. Root docs: superseded numbers found (and their fix)

| file | claim | correct | fix |
| `README.md` | "0.6× chance" (×2) | **0.00×** — the 0.6 was leak-contaminated (chance baseline used the full anchor set) | rewritten |
| `README.md` | "312 unique signs" | **205** non-empty distinct Bennett IDs in the DB | rewritten |
| `README.md` | "78 CONFIRMED anchors" | **58** (Phase 8 lineage), 40→35 in the refined grid | rewritten |
| `README.md` | Phase 4 ML "✅ Complete" | built, unvalidated, stale | rewritten |
| `README.md` | "29 fraction signs with proposed values" | 16/29 circular, 1/29 corroborated | rewritten |
| `README.md` | launch line "124 logograms, 44 of 138 syllabograms" | 88 distinct logogram IDs; "of 138" is the phantom-inflated denominator | rewritten |
| `pipeline/ventris/complete.py` | docstring "78 CONFIRMED anchor signs" | 58 | fixed |
| `data/analysis/synthesis/MASTER_SYNTHESIS.md` | 0.6×, pa-i-to 95, "AB 85 word divider" | see §2 | banner added |
| `data/analysis/ventris/ventris_report.md` | "recovery = 0.6× chance" | 0.00× | banner added |
| `data/analysis/ventris/diachronic_findings.md` | 2× prior, p=0.0003 | retracted | banner + archived code |
| `MULTI_LANGUAGE_DECYPHR_PLAN.md` | "0.6× proves corpus-alone has no gradient" | 0.00× | corrected |
| `AGENTS.md` | "~44 of ~138 syllabograms" | see §4, and the two grids disagree | corrected |
| `AGENTS.md` | "Key tables: words, word_dividers, lacunae" | **all three are empty**; segmentation lives in CSVs | corrected |
| `AGENTS.md` | sign_semantics = logogram meanings | **0 rows** | corrected |

Historical documents are **bannered, not rewritten**: `verification_audit.md` is the audit trail,
and silently editing an old number destroys the evidence that the correction happened.

---

## 4. The counting problem (the single most confusing thing in this repo)

Four instruments report a "confirmed" count, and they do not agree:

| instrument | rows | CONFIRM | of which on signs that exist |
| `data/analysis/comparative/refined_phonetic_grid.csv` (Phase 5) | 138 | 40 | **35** (5 phantoms: AB 12, 15, 18, 35, 52) |
| `data/analysis/bootstrapping/expanded_grid.csv` (Phase 8, deprecated) | 138 | 77 | 58 |
| `data/analysis/bootstrapping/expanded_grid_purged.csv` (Phase 11, canonical) | 69 | 58 | **58** |
| `data/analysis/comparative/misvalued_signs_resolution.csv` (Phase 5 output) | 19 | — | includes 1 phantom row (AB 36) |

The two grids disagree by ~33 signs, and no document reconciles them. `AGENTS.md`'s "44 of 138"
is from a third snapshot. **Until that is resolved, any sentence of the form "N syllabograms are
confirmed" must state which grid it refers to.** The honest formulation is the one in the
README: the sign inventory is ~205 attestation IDs, the honest grid is 69 signs, and the
CONFIRMED count differs by instrument (58 Phase 8 lineage / 40‥35 Phase 5).

This is not pedantry. A collaborator who asks "how many values do you have?" will get four
answers from four files, and will conclude the project is confused — when in fact each file is
reproducible and the confusion is a naming/documentation failure.

---

## 5. Reproducibility: what regenerates what, and the three gaps

**Verified reproductions (this audit):**

| artifact | generator | result |
| `expanded_grid_purged.csv` | `pipeline/purge_grid.py --check` | **byte-identical**, 69/138 rows, 58 CONFIRM |
| `refined_phonetic_grid.csv`, `grid_changes_from_ab.csv`, `misvalued_signs_resolution.csv` | `pipeline/phonetic_grid_refinement.py` | **byte-identical** (run in a scratch tree) |
| Linear B sandbox DB | `pipeline/lb_ingest.py` | gate passes; 4,794 inscriptions / 40,038 signs |
| guard suite | `pipeline/guards.py` | **15/15** |

**The three gaps, and what was done:**

1. **The canonical grid had no generator.** `expanded_grid_purged.csv` was hand-produced once.
   → New: `pipeline/purge_grid.py`, wired into the guards as
   *"honest grid regenerates from its inputs"*. A silent hand-edit now fails the suite.
2. **Two guards failed on a fresh clone.** Not defects: the Linear B DB (9.7 MB) is gitignored
   and rebuildable, and the guards assumed it existed. A reproducibility gap that presents as a
   failure is worse than either. → New: `tools/bootstrap.sh` (sync → LB ingest → grid check →
   guards, all idempotent), and both guards now *skip with an instruction* instead of failing.
3. **The environment could delete itself.** `requires-python = ">=3.10"` let `uv` pick CPython
   3.14 and then destroy the venv trying to build a cu121 torch wheel with no 3.14 build. →
   Fixed: `>=3.10,<3.14`, `.python-version` pinned to 3.12, and torch moved to the optional
   `ml` extra (nothing outside `pipeline/ml/` imports it).

**Still open (flagged, with numbers, in the guard report):**

- `refined_phonetic_grid.csv` carries **69 phantom rows, 5 of them CONFIRM**. Purging it changes
  what 25+ modules read — a re-derivation with review, not a cleanup edit.
- **1 pipeline module still defaults to the deprecated grid** (`oracle_diagnose.py:47`) — down
  from 6 modules / 10 call sites after the `legacy/` move. It is live (guards, RSI) and part of
  open item 1. The guard prints it.
- `positional/anomalous_signs.csv` (3 rows) vs `misvalued_signs_ranked.csv` (age-stale) — the
  Phase 12 drift item.
- `data/analysis/comparative/misvalued_signs_resolution.csv` contains one phantom row (AB 36)
  and does not reflect the Phase 12 CONFIRM policy. It is regenerated only by re-running
  `phonetic_grid_refinement.py` after the grid is re-derived.

---

## 6. Schema vs reality

Seven of the sixteen tables in `lineara_full.db` are **empty**: `words`, `word_dividers`,
`lacunae`, `lines`, `sign_semantics`, `relations_linear_b`, `bibliography`.

`AGENTS.md` pointed at three of them as data sources. The real picture:

- segmentation lives in `data/analysis/segmentation/segmented_texts_consensus.csv`
- logogram semantics live in `data/analysis/logograms/commodity_ontology.csv`
- the DB itself holds `inscriptions` (1,719), `signs` (11,018), `findspots` (62), `images` (1,718)

An empty table is not a bug in a schema that is aspirational, but a doc that points at one is.
Fixed in `AGENTS.md`.

---

## 7. Rules, distilled — so this does not recur

These extend `EXPERIMENT_PROTOCOL.md`; §8 there is the binding version.

1. **A retraction is three actions, never one.** Move the code to `archive/` with a header
   naming the falsifying number, fix every doc that cites it, and record it in
   `verification_audit.md`. Deleting the file alone guarantees it comes back.
2. **Every canonical artifact gets a generator and a guard.** If a file cannot be re-derived,
   it is a hand-copied number wearing a `.csv` extension.
3. **Every guard must pass on a fresh clone.** "Skipped, run bootstrap" is acceptable;
   "FAILED because a gitignored file is absent" is not — it trains people to ignore the suite.
4. **Freeze concluded avenues.** A negative result is a result. The only allowed change is a
   broken import.
5. **Name the instrument in every claim.** "58 CONFIRMED" is meaningless without "which grid",
   because the repo contains three answers and two of them are on signs that do not exist.
6. **Purge phantoms at the source, not at the report.** The purge was applied to the Phase 8
   grid and never to the Phase 5 grid, so five CONFIRM decisions survived on non-existent
   signs. Check every derived file for the same leak.
7. **A dependency that only unvalidated code needs is not a default dependency.** torch is 2 GB
   of CUDA wheel behind code that has produced zero live conclusions.
8. **Hardware/environment scripts are not research artifacts.** They go in `archive/wrong_turns/`.
9. **A subagent's working files are not project documentation.** `JOURNAL.md`/`MEMORY.md` at the
   repo root read like findings; they were scratch, and their numbers were never controlled.
10. **When the audit and the README disagree, the README is wrong until proven otherwise.**
11. **`legacy/` is for concluded work, `archive/` is for falsified work, `pipeline/` is the live
    tree.** Unused ≠ useless: a module nothing imports may be the only generator of a cited
    artifact. Run the three tests in `CLEANUP_PLAN.md` §2 before moving anything.

---

## 8. Open items, ranked

| # | item | why it matters | cost |
| 1 | Re-derive `refined_phonetic_grid.csv` (purge 69 phantoms, apply Phase 12 policy) and migrate the last legacy-grid consumer (`oracle_diagnose.py`) | every downstream "confirmed" count, plus the ML/verification stack | 1–2 days + review |
| 2 | Reconcile the two grids (58 vs 35–40), or state permanently that they measure different things | a collaborator will ask this first | ½ day |
| 3 | Regenerate the 25+ stale consumers, or mark the affected outputs `SUPERSEDED` in place (the consumers themselves are now in `legacy/`) | prevents citing pre-correction numbers | 1–2 days |
| 4 | `AB 41 (si)` — 240 occurrences, UNCERTAIN, in the libation formula | the key open sign | research |
| 5 | Falsify-or-confirm the libation formula on the CM-syllabary chain (Phase 16 route) | the only surviving positive; its extension needs a real CM corpus | blocked on data |
| 6 | Second reviewer for the Phase 16 test | it is currently self-audited | external |
| 7 | Plan the Phase 4 restart: grid re-derivation first, then `git mv legacy/ml pipeline/ml` (or import from `legacy`) | the ML stack is stale and torch is now an optional extra | after item 1 |

---

## Appendix — how to re-run this audit

```bash
./tools/bootstrap.sh                 # deps, LB sandbox, grid check, 15/15 guards
uv run python pipeline/guards.py     # the suite + the non-fatal defect reports
uv run python pipeline/purge_grid.py --check
uv run python -m pipeline.cli db stats data/database/lineara_full.db

# a module that does not import anything and appears in no doc is a deletion candidate:
#   (import graph + doc-reference count, as used for this audit)
```

**The test for a future reader:** if you cannot tell, from the file alone, whether a number is
live, concluded, or retracted — that file is a defect, and it belongs in this document.
