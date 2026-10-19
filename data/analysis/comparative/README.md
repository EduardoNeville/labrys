# `data/analysis/comparative/` — artifact status

The directory that a collaborator will read first, so every file that is **not** live gets a
status here. Full reasoning: `../../../CODE_AUDIT.md`.

## Live — safe to cite

| file | what it is | generator |
| `la_lb_mapping.csv` | LA↔LB sign mapping, confidence-rated. Glyph columns and `lb_value` repaired in Phase 12. | `pipeline/linear_b_mapping.py`, repairs by `pipeline/fix_mapping_values.py` |
| `la_cm_shared_phonetic_grid.csv` | LA→CM→Cypriot shape correspondences. The input to the one pre-registered PASS (44.65×, 45/54, Phase 16). | `pipeline/cypro_minoan_bridge.py` |
| `la_cm_comparison.csv`, `la_cm_eteocypriot_grid.csv` | CM comparison tables | `pipeline/cypro_minoan_bridge.py` |
| `la_lb_ideogram_map.csv`, `fraction_alignment.csv` | logogram/fraction alignment | `pipeline/commodity_alignment.py` |
| `la_lb_mapping_audit.csv`, `la_lb_mapping_value_fixes.csv`, `la_lb_misaligned.csv` | the audit of the mapping | `pipeline/audit_grid_inputs.py`, `pipeline/fix_mapping_values.py` |

## ⚠️ Stale — reproduces, but its inputs moved

| file | problem |
| `refined_phonetic_grid.csv` | **live since 2026-10-19** — 71 rows, 35 CONFIRM; the 111 phantom IDs are filtered at the generator, and the case-sensitivity defect that hid AB 21f/22f is fixed (Phase 18). |
| `misvalued_signs_resolution.csv` | Regenerated 2026-10-19 from the purged grid: the phantom AB 36 `jo` row is gone. |
| `grid_changes_from_ab.csv`, `phase5_synthesis.md` | same lineage as the refined grid; report carries a supersession banner |

Re-derivation is `CODE_AUDIT.md` §8 item 1 — a review task, not a cleanup edit, because purging
the phantom rows changes every downstream count.

## ❌ Historical — do not cite

`commodity_alignment_report.md`, `cypro_minoan_report.md`, `deep_loanword_report.md`,
`la_lb_transfer_report.md`, `minoan_shadow_lexicon.csv`, `nth_ss_analysis.csv`,
`commodity_contexts.csv`, `deep_loanword_matches.csv`.

These are Phase 5–7 outputs written before the corpus correction and the grid purge. Their
headline numbers (including any "N confirmed signs") belong to superseded instruments. They are
kept as the record of what was measured with the data available at the time.

**The canonical reference for any value claim is `data/analysis/ventris/verification_audit.md`
plus the honest grid `data/analysis/bootstrapping/expanded_grid_purged.csv`** — and that grid's
generator is `pipeline/purge_grid.py --check`, which fails if the file is hand-edited.
