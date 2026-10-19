# Provenance of `data/analysis/` — generated, do not hand-edit

**Generated** by `pipeline/analysis_provenance.py`. `pipeline/guards.py` re-renders this file
and fails on drift, so an artifact added or moved without updating the map is visible.

**Status key**

| status | meaning |
|---|---|
| **LIVE** | a `pipeline/` module names it, and the inputs are current |
| **INPUT** | consumed by an instrument; it is not a result |
| **MIXED** | the directory has live and retired owners; the file needs a human look |
| **REPORT** | hand-written synthesis, not a generated artifact |
| **RETIRED** | only a `legacy/` module names it (or owns its directory) — superseded, kept for the record |
| **ORPHAN** | nothing generates it and nothing (live) cites it |

Totals: INPUT 16, LIVE 95, MIXED 23, ORPHAN 1, REPORT 6, RETIRED 9.

| artifact | status | provenance | last commit | cited |
|---|---|---|---|---|
| `data/analysis/bootstrapping/bootstrapping_report.md` | LIVE | `pipeline/bootstrapping/grid_expand.py` | 2026-10-19 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/bootstrapping/cycle_summary.json` | LIVE | `pipeline/bootstrapping/grid_expand.py` | 2026-10-19 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/bootstrapping/expanded_grid_purged.csv` | LIVE | `pipeline/audit_grid_inputs.py` (+7) | 2026-10-19 | 18 — `AGENTS.md` |
| `data/analysis/commodity_decoding/commodity_signatures.csv` | LIVE | `pipeline/bootstrapping/grid_expand.py` (+1) | 2026-08-13 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/commodity_alignment_report.md` | LIVE | `pipeline/commodity_alignment.py` | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/cypro_minoan_report.md` | LIVE | `pipeline/cypro_minoan_bridge.py` | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/grid_changes_from_ab.csv` | LIVE | `pipeline/phonetic_grid_refinement.py` | 2026-10-19 | 5 — `CODE_AUDIT.md` |
| `data/analysis/comparative/la_cm_comparison.csv` | LIVE | `pipeline/cypro_minoan_bridge.py` | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/la_cm_eteocypriot_grid.csv` | LIVE | `pipeline/comparative_bridge.py` | 2026-08-28 | 3 — `MULTI_LANGUAGE_DECYPHR_PLAN.md` |
| `data/analysis/comparative/la_lb_mapping_audit.csv` | LIVE | `pipeline/audit_grid_inputs.py` (+1) | 2026-09-15 | 4 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/la_lb_mapping_value_fixes.csv` | LIVE | `pipeline/fix_mapping_values.py` | 2026-09-15 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/la_lb_transfer_report.md` | LIVE | `pipeline/linear_b_mapping.py` | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/misvalued_signs_resolution.csv` | LIVE | `pipeline/phonetic_grid_refinement.py` | 2026-10-19 | 7 — `AGENTS.md` |
| `data/analysis/comparative/phase5_synthesis.md` | LIVE | `pipeline/phonetic_grid_refinement.py` | 2026-10-19 | 5 — `AGENTS.md` |
| `data/analysis/kober/cluster_members.csv` | LIVE | `pipeline/kober/positional_grid.py` | 2026-10-19 | 4 — `data/analysis/PROVENANCE.md` |
| `data/analysis/kober/frame_links.csv` | LIVE | `pipeline/kober/triple_detection.py` | 2026-10-19 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/kober/grid_series.csv` | LIVE | `pipeline/kober/positional_grid.py` | 2026-10-19 | 6 — `CLEANUP_PLAN.md` |
| `data/analysis/kober/kober_report.md` | LIVE | directory owner `pipeline/kober/{triple_detection,positional_grid}.py` | 2026-08-03 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/kober/positional_clusters.csv` | LIVE | `pipeline/kober/positional_grid.py` | 2026-10-19 | 4 — `data/analysis/PROVENANCE.md` |
| `data/analysis/kober/triple_patterns.csv` | LIVE | `data/analysis/ventris/stratify_oracle_by_findspot.py` (+6) | 2026-10-19 | 9 — `CLEANUP_PLAN.md` |
| `data/analysis/linguistic/ab02_analysis.csv` | LIVE | `pipeline/toponym_alignment.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/candidate_ranking.csv` | LIVE | `pipeline/falsification_report.py` | 2026-07-30 | 5 — `AGENTS.md` |
| `data/analysis/linguistic/falsification_matrix.csv` | LIVE | `pipeline/falsification_report.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/loanword_matches.csv` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/loanword_summary.md` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/morphology_paradigms.csv` | LIVE | `pipeline/commodity_alignment.py` (+2) | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/morphology_summary.md` | LIVE | `pipeline/morphology_scan.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/phase3_synthesis.md` | LIVE | `pipeline/falsification_report.py` | 2026-07-30 | 3 — `AGENTS.md` |
| `data/analysis/linguistic/reduplication_patterns.csv` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/swadesh_match_details.csv` | LIVE | `pipeline/swadesh_search.py` | 2026-10-19 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/swadesh_results.csv` | LIVE | `pipeline/falsification_report.py` (+2) | 2026-10-19 | 4 — `AGENTS.md` |
| `data/analysis/linguistic/swadesh_summary.md` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/toponym_report.md` | LIVE | `pipeline/toponym_alignment.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/wals_comparison.csv` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-10-19 | 4 — `AGENTS.md` |
| `data/analysis/linguistic/wals_summary.md` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/word_length_distribution.csv` | LIVE | `pipeline/falsification_report.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/logograms/commodity_ontology.csv` | LIVE | `pipeline/logogram_analysis.py` (+1) | 2026-07-30 | 3 — `AGENTS.md` |
| `data/analysis/logograms/commodity_period_matrix.csv` | LIVE | `pipeline/logogram_analysis.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/logograms/commodity_site_matrix.csv` | LIVE | `pipeline/logogram_analysis.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/logograms/fraction_cooccurrence.csv` | LIVE | `pipeline/logogram_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/logograms/fraction_occurrences.csv` | LIVE | `pipeline/logogram_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/logograms/fraction_values_audit.csv` | LIVE | `pipeline/audit_grid_inputs.py` | 2026-09-15 | 3 — `AGENTS.md` |
| `data/analysis/logograms/fraction_values_proposed.csv` | LIVE | `pipeline/audit_grid_inputs.py` (+3) | 2026-07-30 | 8 — `AGENTS.md` |
| `data/analysis/network/global/communities.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/global/community_sign_types.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/global/component_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/global/network_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/global/top_bridges.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/hagia_triada/communities.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/hagia_triada/community_sign_types.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/hagia_triada/component_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/hagia_triada/network_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/hagia_triada/top_bridges.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/khania/communities.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/khania/community_sign_types.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/khania/component_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/khania/network_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/khania/top_bridges.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/knossos/communities.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/knossos/community_sign_types.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/knossos/component_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/knossos/network_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/knossos/top_bridges.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/zakros/communities.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/zakros/community_sign_types.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/zakros/component_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/zakros/network_summary.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/network/zakros/top_bridges.csv` | LIVE | directory owner `pipeline/network_analysis.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/analysis_summary.csv` | LIVE | `pipeline/ngram_analysis.py` (+2) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/conditional_entropy.csv` | LIVE | `pipeline/ngram_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/mutual_information.csv` | LIVE | `pipeline/ngram_analysis.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/ngram_freqs.csv` | LIVE | `pipeline/linear_b_mapping.py` (+2) | 2026-07-30 | 3 — `AGENTS.md` |
| `data/analysis/ngram/phonotactic_summary.csv` | LIVE | `pipeline/ngram_analysis.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/sign_entropy.csv` | LIVE | `pipeline/ngram_analysis.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/typology_statistics.csv` | LIVE | `pipeline/ngram_analysis.py` (+1) | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/phylogenetic/conflict_resolutions.csv` | LIVE | `pipeline/bootstrapping/grid_expand.py` | 2026-08-03 | 6 — `data/analysis/PROVENANCE.md` |
| `data/analysis/positional/analysis_summary.csv` | LIVE | `pipeline/ngram_analysis.py` (+2) | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/positional/candidate_prefixes.csv` | LIVE | `pipeline/positional_analysis.py` (+1) | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/positional/candidate_suffixes.csv` | LIVE | `pipeline/positional_analysis.py` (+1) | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/positional/sign_clusters.csv` | LIVE | `pipeline/positional_analysis.py` (+1) | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/rsi/loop_state.json` | LIVE | `pipeline/rsi_loop.py` | 2026-10-04 | 2 — `RSI_LOOP.md` |
| `data/analysis/rsi/phase0.md` | LIVE | directory owner `pipeline/rsi_*.py + data/analysis/rsi/*.py` | 2026-10-01 | 4 — `METHOD_CLOSURE_PAPER.md` |
| `data/analysis/rsi/split.json` | LIVE | `pipeline/guards.py` (+1) | 2026-10-01 | 4 — `METHOD_CLOSURE_PAPER.md` |
| `data/analysis/rsi/tree.json` | LIVE | `pipeline/rsi_tree.py` | 2026-10-01 | 4 — `METHOD_CLOSURE_PAPER.md` |
| `data/analysis/segmentation/segmentation_confidence.csv` | LIVE | `pipeline/word_segmentation.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/segmentation/segmented_texts_consensus.csv` | LIVE | `pipeline/morphology_scan.py` (+3) | 2026-07-30 | 4 — `AGENTS.md` |
| `data/analysis/segmentation/strategy_comparison.csv` | LIVE | `pipeline/word_segmentation.py` | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/corpus_bias_finding.md` | LIVE | `pipeline/doc_claims_check.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/corrected_rerun_results.md` | LIVE | `pipeline/doc_claims_check.py` | 2026-10-19 | 7 — `AGENTS.md` |
| `data/analysis/ventris/libation_catalog.md` | LIVE | `pipeline/doc_claims_check.py` (+1) | 2026-10-19 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/libation_recovered.md` | LIVE | `pipeline/doc_claims_check.py` (+1) | 2026-10-19 | 10 — `AGENTS.md` |
| `data/analysis/ventris/sign_consensus.csv` | LIVE | `pipeline/ventris/complete.py` | 2026-08-13 | 3 — `MULTI_LANGUAGE_DECYPHR_PLAN.md` |
| `data/analysis/ventris/top_completions.csv` | LIVE | `pipeline/ventris/complete.py` | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/ventris_report.md` | LIVE | `pipeline/lb_oracle.py` (+1) | 2026-10-19 | 11 — `CODE_AUDIT.md` |
| `data/analysis/ventris/verification_audit.md` | LIVE | `pipeline/doc_claims_check.py` | 2026-10-19 | 28 — `AGENTS.md` |
| `data/analysis/bootstrapping/expanded_grid_legacy_138.csv` | INPUT | consumed by an instrument; not a result | 2026-10-19 | 6 — `AGENTS.md` |
| `data/analysis/commodity_decoding/logogram_contexts.csv` | INPUT | consumed by an instrument; not a result | 2026-08-13 | 3 — `CLEANUP_PLAN.md` |
| `data/analysis/commodity_decoding/sign_commodity_enrichment.csv` | INPUT | consumed by an instrument; not a result | 2026-08-13 | 4 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/commodity_contexts.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/fraction_alignment.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/la_cm_shared_phonetic_grid.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 8 — `AGENTS.md` |
| `data/analysis/comparative/la_lb_ideogram_map.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/la_lb_mapping.csv` | INPUT | consumed by an instrument; not a result | 2026-09-15 | 16 — `AGENTS.md` |
| `data/analysis/comparative/la_lb_misaligned.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/minoan_shadow_lexicon.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/comparative/refined_phonetic_grid.csv` | INPUT | consumed by an instrument; not a result | 2026-10-19 | 13 — `AGENTS.md` |
| `data/analysis/linguistic/phonetic_grid_confidence.csv` | INPUT | consumed by an instrument; not a result | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/linguistic/toponym_anchors.csv` | INPUT | consumed by an instrument; not a result | 2026-08-13 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ngram/misvalued_signs_ngram.csv` | INPUT | consumed by an instrument; not a result | 2026-07-30 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/positional/misvalued_signs_ranked.csv` | INPUT | consumed by an instrument; not a result | 2026-08-13 | 3 — `AGENTS.md` |
| `data/analysis/positional/positional_profiles.csv` | INPUT | consumed by an instrument; not a result | 2026-08-13 | 6 — `AGENTS.md` |
| `data/analysis/ventris/TODO_corrected_corpus.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/ab41_finding.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/b1_grid_audit.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/b1b2_phantom_finding.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 2 — `MULTI_LANGUAGE_DECYPHR_PLAN.md` |
| `data/analysis/ventris/b2_ab100_result.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/corpus_correction.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 4 — `AGENTS.md` |
| `data/analysis/ventris/diachronic_analysis.csv` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/diachronic_findings.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-10-19 | 4 — `CODE_AUDIT.md` |
| `data/analysis/ventris/diachronic_prior.csv` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/field_state_2025.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 3 — `MULTI_LANGUAGE_DECYPHR_PLAN.md` |
| `data/analysis/ventris/formula_phonetic_test.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/formula_word_findings.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/grid_purge_result.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/grid_validity_audit.csv` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/lb_sandbox_findings.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-09-15 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/libation_formula.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-10-19 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/method_closure.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-09-15 | 5 — `CODE_AUDIT.md` |
| `data/analysis/ventris/oracle_repair_report.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-09-15 | 6 — `EXPERIMENT_PROTOCOL.md` |
| `data/analysis/ventris/oracle_retrace_findings.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-09-15 | 6 — `LINEAR_B_SANDBOX_PLAN.md` |
| `data/analysis/ventris/phantom_removed.csv` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/phantom_signs.csv` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/wine_word_finding.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/ventris/word_morphology_finding.md` | MIXED | directory owner `pipeline/ventris/complete.py + reports` — check the file | 2026-08-13 | 1 — `data/analysis/PROVENANCE.md` |
| `data/analysis/synthesis/MASTER_SYNTHESIS.md` | REPORT | hand-written synthesis, not a generated artifact | 2026-10-19 | 6 — `CODE_AUDIT.md` |
| `data/analysis/synthesis/avenues_11.md` | REPORT | hand-written synthesis, not a generated artifact | 2026-08-13 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/synthesis/phase_summary_10_11.md` | REPORT | hand-written synthesis, not a generated artifact | 2026-10-19 | 3 — `data/analysis/PROVENANCE.md` |
| `data/analysis/synthesis/phase_summary_1_3.md` | REPORT | hand-written synthesis, not a generated artifact | 2026-08-03 | 3 — `MULTI_LANGUAGE_DECYPHR_PLAN.md` |
| `data/analysis/synthesis/phase_summary_4_6.md` | REPORT | hand-written synthesis, not a generated artifact | 2026-08-03 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/synthesis/phase_summary_7_9.md` | REPORT | hand-written synthesis, not a generated artifact | 2026-08-13 | 3 — `MULTI_LANGUAGE_DECYPHR_PLAN.md` |
| `data/analysis/network/global/sign_centrality.csv` | RETIRED | generator now `legacy/verification/internal_consistency.py` | 2026-08-13 | 3 — `AGENTS.md` |
| `data/analysis/network/hagia_triada/sign_centrality.csv` | RETIRED | generator now `legacy/verification/internal_consistency.py` | 2026-08-13 | 3 — `AGENTS.md` |
| `data/analysis/network/khania/sign_centrality.csv` | RETIRED | generator now `legacy/verification/internal_consistency.py` | 2026-08-13 | 3 — `AGENTS.md` |
| `data/analysis/network/knossos/sign_centrality.csv` | RETIRED | generator now `legacy/verification/internal_consistency.py` | 2026-08-13 | 3 — `AGENTS.md` |
| `data/analysis/network/zakros/sign_centrality.csv` | RETIRED | generator now `legacy/verification/internal_consistency.py` | 2026-08-13 | 3 — `AGENTS.md` |
| `data/analysis/phylogenetic/alignment_matrix.csv` | RETIRED | directory owner `legacy/phylogenetic/alignment.py` (now in legacy/) | 2026-08-03 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/phylogenetic/phylogenetic_report.md` | RETIRED | directory owner `legacy/phylogenetic/alignment.py` (now in legacy/) | 2026-08-03 | 4 — `data/analysis/PROVENANCE.md` |
| `data/analysis/positional/anomalous_signs.csv` | RETIRED | generator now `legacy/positional_oracle.py` | 2026-09-15 | 5 — `AGENTS.md` |
| `data/analysis/ventris/libation_formula_chunks.csv` | RETIRED | generator now `legacy/libation_formula.py` | 2026-08-13 | 2 — `data/analysis/PROVENANCE.md` |
| `data/analysis/alternative_approaches_synthesis.md` | ORPHAN | cited, but nothing generates it | 2026-08-03 | 3 — `data/analysis/PROVENANCE.md` |

---

**How to read it.** `RETIRED` does not mean wrong; it means *its measurement belongs to its
phase*, and the module that produced it no longer lives in `pipeline/`. `ORPHAN` means the
file has no owner left — it is either cited history or a deletion candidate.
