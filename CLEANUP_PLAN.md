# Cleanup plan — moving what is no longer helpful into `legacy/`

**Date:** 2026-10-19 · **Executed:** yes, in full (this is the plan and the record of it) ·
**Companion:** `CODE_AUDIT.md` (module-level status), `archive/README.md` (retracted code),
`legacy/__init__.py` (the rules for that directory).

**Effect:** `pipeline/` went from **97 → 62 modules** (50,000 → 34,113 LOC). 36 modules
(~16.6k LOC) moved to `legacy/`; 3 subagent reports were re-filed into `archive/agent_scratch/`;
1 root-level module was moved *into* `pipeline/` where it belongs. Guards went 15 → **17/17**.

---

## 1. The problem this solves

The repo had accumulated three kinds of "not useful", and they need different treatment:

| kind | example | right answer |
| **Retracted** — the premise was falsified | `diachronic.py` (p 0.0003 → 0.1748) | `archive/` — with the falsifying number attached |
| **Concluded** — the negative is the result, but nobody will run it again | `eteocretan/`, `ml/` | `legacy/` — importable, out of the live tree |
| **Misplaced** — live code, wrong location | `ingest_lineara.py` at the repo root | move it into `pipeline/` |

Before this pass, `pipeline/` mixed all three with the load-bearing instruments, so "what is
live?" could only be answered by reading 50k LOC. It is now answerable from the directory
listing: **`pipeline/` is the live tree, `legacy/` is the archive of concluded work, `archive/`
is where falsified work lives.**

## 2. The decision rule (and why not "unused")

"Nothing imports it" is *not* sufficient — 20 of the modules nothing imports are the tools that
generate the committed data. Three tests were applied, and a module moves only if it fails all
three:

| # | test | how it was measured |
| 1 | **Live import** — reachable from an entry point (CLI, guards, bootstrap, `rsi_loop`, the audit scripts in `data/analysis/`) | full AST import graph over `pipeline/`, `data/analysis/`, `tools/`, `demo.py` |
| 2 | **Documented tool** — a document tells a reader to run it | grep for `python <path>` / `uv run python <path>` across all `*.md` |
| 3 | **Generator of a live artifact** — it writes a file some live code or citable claim depends on | write-site scan (`open(..., "w")`, `DictWriter`, `.write(`) cross-checked against committed paths |

Modules that pass any test stay. That is what kept `kober/triple_detection.py` (generates
`kober/triple_patterns.csv`, which the live scorer and a guard read), `commodity_decoding/`
(`context_extract.py` generates `logogram_contexts.csv`, read by the Phase 14 audits) and
`bootstrapping/grid_expand.py` (the first link in the grid chain for open item 1).

## 3. What moved (old path → new path, and the reason)

| old | new | why it moves |
| `pipeline/anatolian_search/` (3) | `legacy/anatolian_search/` | Phase 7 Approach 5; concluded, no importers, not in any run-list |
| `pipeline/eteocretan/` (3) | `legacy/eteocretan/` | Phase 7 Approach 1; concluded |
| `pipeline/phylogenetic/` (3) | `legacy/phylogenetic/` | Phase 7 Approach 3; concluded |
| `pipeline/formulaic/` (2) | `legacy/formulaic/` | Phase 9; concluded, and reads the deprecated grid |
| `pipeline/frequency_constraints/` (3) | `legacy/frequency_constraints/` | Phase 7; concluded, and reads the deprecated grid |
| `pipeline/egyptian_bridge/` (3) | `legacy/egyptian_bridge/` | Phase 10a; concluded negative (matches ≈ chance) |
| `pipeline/ml/` (10) | `legacy/ml/` | Phase 4: built, unvalidated, and its labels come from a grid that moved. Restart begins with the grid re-derivation, not with a training run |
| `pipeline/verification/` (7 incl. 3 scratch `.md`) | `legacy/verification/` | Phase 6; consumes the stale Phase 4 outputs |
| `pipeline/ventris/cryptanalysis.py` | `legacy/cryptanalysis.py` | Phase 11 Avenue 3; concluded negative |
| `pipeline/ventris/positional_oracle.py` | `legacy/positional_oracle.py` | Phase 11 Avenue 1; concluded negative, reads the deprecated grid |
| `pipeline/ventris/libation_formula.py` | `legacy/libation_formula.py` | superseded: the live verifier is `rsi_loop.py:x_libation` (`verify:libation-counts`) |
| `pipeline/deep_loanword_mining.py` | `legacy/deep_loanword_mining.py` | Phase 3 add-on, no importers, no run-list |
| `pipeline/commodity_decoding/semantic_cluster.py` | `legacy/semantic_cluster.py` | Phase 7 clustering; superseded by the Phase 14 audit path |

**Re-filed into `archive/agent_scratch/`** (subagent working files that read like findings):
`pipeline/verification/{JOURNAL,REPORT,TODO}.md`, `pipeline/commodity_decoding/REPORT.md`,
and the root `phase2_corpus_ingestion.md` (a stale report with a literal `$(date +%Y-%m-%d)` in
it, duplicating `docs/archive/`).

**Relocated, not legacy:**
`ingest_lineara.py` (repo root) → `pipeline/ingest_lineara.py`. It is live — `pipeline/ingest.py`
imports it and it stays canonical for linear-a parsing — but a root-level module imported by the
package was the single worst structural smell in the tree. Its `sys.path` shim was pointing at
`pipeline/` (so it only worked because of the editable install); it now points at the repo root
and runs standalone.

## 4. What was deliberately NOT moved

| kept | why |
| `pipeline/kober/triple_detection.py` | generates `kober/triple_patterns.csv`, read by the live scorer; a guard checks its 60,155 triples are canonically ordered |
| `pipeline/kober/positional_grid.py` | generates `kober/grid_series.csv` + cluster files cited by the Phase 12 cascade |
| `pipeline/bootstrapping/grid_expand.py` | the Phase 8 grid generator; since Phase 18 it writes the canonical `expanded_grid_purged.csv` directly |
| `pipeline/phonetic_grid_refinement.py` | generates the Phase 5 grid — the artifact open item 1 re-derives |
| `pipeline/linear_b_mapping.py`, `cypro_minoan_bridge.py`, `commodity_alignment.py` | generators of `la_lb_mapping.csv`, `la_cm_shared_phonetic_grid.csv` (input to the Phase 16 PASS) and the ideogram/fraction alignments |
| `pipeline/commodity_decoding/` | generator of a Phase 14 audit input |
| every Phase 2–3 analysis module | generators of live CSVs, several named in `AGENTS.md` as runnable |
| the oracle/gate/RSI instruments | the load-bearing part; guards depend on them |

Everything that stayed is listed with its state in `CODE_AUDIT.md` §1.

## 5. What the planning pass found (fixed before moving anything)

1. **Two sign-ID slips in the project's only cross-site positive.** `libation_recovered.md`
   listed the opening as five signs (`AB 08 59 28 54 57`) where the corpus reads six
   (`AB 08 AB 59 AB 28 A 301 AB 54 AB 57` — **A 301 was omitted**), and slot 5 as
   `AB 28 54 06 80` ("i-*301-na-ma") where the corpus reads `AB 28 AB 39 AB 06 AB 80`
   (**i-pi-na-ma**, 6 occurrences). Both wrong forms have **zero** matches in the corpus. The
   live verifier had it right all along; nothing compared the prose to the data.
   → Doc corrected, with the correction recorded in place, and a **new guard** now checks the
   table against the corpus.
2. **`legacy/` must not creep back.** New guard: `pipeline/` may not import `legacy.*`. The
   moment live code needs a legacy module, that module is not legacy.
3. **The guard suite's own blind spot.** The first version of that guard grepped text and
   flagged its own title string — a false positive of exactly the kind that gets a suite
   ignored. It parses imports (AST) now.

## 6. Verification (all after the moves)

| check | result |
| `python -m pipeline.guards` | **17/17 pass** (was 15/15; +2 new) |
| `python -m compileall pipeline legacy tools data/analysis` | clean |
| import smoke test, 12 representative `legacy.*` modules | all OK |
| `uv run python demo.py`, `pipeline.cli unicode validate`, `db stats` | unchanged (1,719 / 11,018 / 205 / 62) |
| live audit instruments re-run | `archive_stratification.py`, `enrichment_audit.py`, `identifiable_subset.py` all still run and report the recorded numbers |
| `pipeline.ingest` + standalone `pipeline/ingest_lineara.py` | both import; ingest paths unchanged |
| stale path references in live docs | fixed in `phonetics.py`, `MULTI_LANGUAGE_DECYPHR_PLAN.md`, `LINEAR_B_SANDBOX_PLAN.md`, `languages/eteocretan/README.md`, `CODE_AUDIT.md` |
| historical docs referencing old paths | left as-is (an audit trail that is edited stops being an audit trail) — the old→new map above is the redirect |

**Dependency note:** `legacy/ml/` needs `uv sync --extra ml` (torch is not a default install).
Every other legacy package imports with the base install.

## 7. How to reverse a move

```bash
git mv legacy/<name>.py pipeline/<name>.py          # single module
git mv legacy/<pkg> pipeline/<pkg>                  # package
# then rewrite its self-imports back:
grep -rl "legacy\." legacy/<pkg> | xargs sed -i 's/\blegacy\./pipeline./g'
python -m pipeline.guards                            # the legacy-import guard must stay green
```

If a module has to come back, it comes back **with a guard and a named generator** (§8.2 of
`EXPERIMENT_PROTOCOL.md`). Returning without them is how the last two rounds of drift happened.

## 8. Candidates for a future pass (not moved, and why)

| candidate | why it is still here |
| `pipeline/ngram_analysis.py`, `positional_analysis.py`, `network_analysis.py`, `word_segmentation.py`, `logogram_analysis.py`, `swadesh_search.py`, `wals_analysis.py`, `morphology_scan.py`, `loanword_matching.py`, `toponym_alignment.py`, `falsification_report.py` | these *generate* the CSVs that `AGENTS.md` lists as live outputs; they are Phase 2–3 RECORD but re-runnable instruments, and two of them (`positional_analysis`, `ngram_analysis`) are the documented quick checks |
| `pipeline/oracle_diagnose.py` | live (guards, RSI), but it still defaults the Linear A config to the deprecated grid — the last of the 6 consumers, and part of open item 1 |
| `data/analysis/**/*.py` (10 audit scripts) | intentionally outside `pipeline/`; their reports cite them by path and rewriting an audit trail to tidy a directory is the wrong trade |
| `docs/archive/*`, `data/analysis/synthesis/*` | historical documents; bannered where they carry superseded numbers (`CODE_AUDIT.md` §3) |
| `MULTI_LANGUAGE_DECYPHR_PLAN.md`, `LINEAR_B_SANDBOX_PLAN.md`, `RSI_LOOP.md`, `METHOD_CLOSURE_PAPER.md`, `POSITIVES_AUDIT.md` | forward-looking plans and papers, not results — they stay at the root until their phase closes |

## 9. Rules this pass adds (now in `EXPERIMENT_PROTOCOL.md` §8)

1. **`legacy/` is for concluded, not falsified.** Falsified goes to `archive/` with the number.
2. **Unused ≠ useless.** A module nothing imports may still be the only generator of a cited
   artifact. Run the three tests before moving anything.
3. **A move is a doc change.** Every live document naming the old path was updated; historical
   documents were left alone and are served by the path map in §3.
4. **The live tree must not import the legacy tree.** Enforced by guard 16.
5. **A prose table that states data gets checked against the data.** The libation table drifted
   from the corpus for two months while both were "verified" — because only one of them was.
   Enforced by guard 17.
