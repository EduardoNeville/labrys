# `_superseded/` — outputs whose generator no longer lives in `pipeline/`

These are **not wrong results**. They are the committed outputs of concluded avenues whose
generator moved to `legacy/` during the 2026-10-19 cleanup. Each file's measurement belongs to its
phase; the code that produced it is preserved, importable, in `legacy/`.

They are here rather than left in place because a `.csv` with no live generator looks exactly like
a `.csv` with one. `PROVENANCE.md` (generated) is the map; this file is the redirect.

**Citation rule.** A live document must not cite a file under `_superseded/` (guard 25). Cite the
phase's report in `data/analysis/ventris/` or `data/analysis/synthesis/` instead, or say explicitly
that the number is a retired measurement.

| moved from | generator now at | why |
|---|---|---|
| `ml/` | `legacy/ml/` | Phase 4: built, never validated (0 high-confidence predictions), labels from a grid that has since moved. Restart is open item 7, and it begins with a re-run, not with these files. |
| `verification/` | `legacy/verification/` | Phase 6: consumes the Phase 4 predictions, so it inherits their staleness. |
| `eteocretan/` | `legacy/eteocretan/` | Phase 7 avenue 1; concluded. |
| `anatolian_search/` | `legacy/anatolian_search/` | Phase 7 avenue 5; concluded (no cognate signal above null). |
| `egyptian_bridge/` | `legacy/egyptian_bridge/` | Phase 10a; concluded (312 consonant-class matches ≈ chance, null ratios 1.6–6.4×). |
| `formulaic/` | `legacy/formulaic/` | Phase 9; concluded, and its generator reads the retired 138-row grid. |
| `frequency_constraints/` | `legacy/frequency_constraints/` | Phase 7; concluded. Its output was still being read as a *default* by the Linear A oracle until 2026-10-19 — the term has been disabled, and the oracle's numbers are unchanged without it (`verification_audit.md` Phase 19). |
| `commodity_decoding/commodity_report.md` | `legacy/semantic_cluster.py` | Phase 7 clustering report; the Phase 14 audit (`commodity_decoding/enrichment_audit.py`, still live) supersedes its claims. |
| `comparative/deep_loanword_*`, `comparative/nth_ss_analysis.csv` | `legacy/deep_loanword_mining.py` | Phase 3 add-on; concluded. |

## Deliberately **not** moved

| directory | why it stays |
|---|---|
| `phylogenetic/` | `pipeline/bootstrapping/grid_expand.py` reads `conflict_resolutions.csv` as an **input** to the canonical grid. Retired generator, live input — moving it would silently change the grid. |
| `commodity_decoding/` | `commodity_signatures.csv` is read by the same generator; `enrichment_audit.py` and `cross_site_replication.py` are live audit instruments (Phase 14/14.1). |

Those two are the residual state: **a live input with a retired generator**. If either is ever
re-derived, the generator must come back into `pipeline/` first.
