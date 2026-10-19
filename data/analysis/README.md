# `data/analysis/` — outputs, and the instruments that check them

This tree holds **results**, and (deliberately) a small number of **audit scripts** that live
next to the files they check. Two conventions worth knowing before you "clean up":

1. **`*.py` under `data/analysis/` is intentional, not misplaced.** These are the audit
   instruments written during the Phase 12–15 verifications — `archive_stratification.py`,
   `enrichment_audit.py`, `cross_site_replication.py`, `stratify_*_by_findspot.py`,
   `data/analysis/rsi/*`. They are kept at the path their reports cite, because historical audit
   documents (`verification_audit.md`) reference them by path and rewriting an audit trail to
   tidy a directory is the wrong trade. New analysis code belongs in `pipeline/`.

2. **A file here is not a finding.** Several directories contain artifacts produced before the
   corpus correction (2026-08-13) or before the grid purge, and they reproduce perfectly while
   being wrong. Status by directory:

| directory | status |
| `ventris/` | **canonical for results** — `verification_audit.md`, `corrected_rerun_results.md`, `libation_recovered.md`, `method_closure.md`. Bannered historical files: `ventris_report.md`, `libation_formula.md`, `diachronic_findings.md` |
| `comparative/` | mixed — see `comparative/README.md` for the file-level status |
| `synthesis/` | historical — `MASTER_SYNTHESIS.md` is bannered superseded (0.6×, pa-i-to 95, 78 anchors) |
| `bootstrapping/` | `expanded_grid_purged.csv` is the honest grid; `expanded_grid.csv` is deprecated |
| `commodity_decoding/` | mixed — `context_extract.py` stays (it generates `logogram_contexts.csv`, read by the live Phase 14 audits); `enrichment_audit.py` and `cross_site_replication.py` are the authority on the retracted-then-narrowed enrichment result; the Phase 7 clustering module is in `legacy/semantic_cluster.py` and `commodity_report.md` is historical |
| `rsi/` | the method-search replay pool — 18 nodes, π₀ optimal, concluded |
| `ml/`, `verification/`, `eteocretan/`, `anatolian_search/`, `egyptian_bridge/`, `formulaic/`, `frequency_constraints/` | **moved** to `_superseded/` on 2026-10-19: their generators live in `legacy/`. See `_superseded/README.md`. |
| `positional/`, `ngram/`, `logograms/`, `network/` | live and current: re-derived on the corrected corpus, byte-identical or count-level diffs only (`verification_audit.md` Phase 19) |
| `phylogenetic/`, `commodity_decoding/` | retired generators, **live inputs** — `grid_expand.py` reads their CSVs, so they stay |
| `linguistic/`, `ngram/`, `network/`, `logograms/`, `segmentation/` | live, except `fraction_values_proposed.csv` (16/29 rows circular — use `fraction_values_audit.csv`) |

**Before citing anything here:** check `CODE_AUDIT.md` §3–§5 and the banner on the file's own
report. If you cannot tell whether a number is live, concluded, or retracted, that is a defect —
report it and it gets an entry in `CODE_AUDIT.md`.
