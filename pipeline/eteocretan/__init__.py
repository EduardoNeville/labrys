"""
Eteocretan Decipherment Analysis (Phase 7)
===========================================
Systematic comparison of Eteocretan inscriptions (Greek alphabet, ~500–300 BCE)
against Linear A evidence to test the hypothesis: Eteocretan = descendant of Minoan.

Modules:
    corpus   — Structured encoding of all 7 known Eteocretan inscriptions
    compare  — Systematic comparison against Linear A ML predictions,
               refined phonetic grid, known LA words, loanwords, and toponyms

Reference data consumed:
    - data/analysis/ml/uncertain_predictions.csv (ML predictions for LA signs)
    - data/analysis/comparative/refined_phonetic_grid.csv (Phase 5 refined grid)
    - data/analysis/linguistic/loanword_matches.csv (Greek→LA loanword matches)
    - data/analysis/linguistic/toponym_anchors.csv (toponym anchor alignments)
    - data/analysis/comparative/phase5_synthesis.md (Phase 5 synthesis)

Output:
    - data/analysis/eteocretan/corpus.csv
    - data/analysis/eteocretan/comparison_results.csv
    - data/analysis/eteocretan/eteocretan_report.md
"""

from pipeline.eteocretan.corpus import (
    EteocretanInscription,
    EteocretanWord,
    ET_DR1,
    ET_DR2,
    ET_PR1,
    ET_PR2,
    ET_PR3,
    ET_PR4,
    ET_PR5,
    ALL_INSCRIPTIONS,
    ALL_WORDS,
    build_corpus,
)

from pipeline.eteocretan.compare import (
    ComparisonResult,
    run_all_comparisons,
    analyze_bilinguals,
    compare_phonotactics,
    map_words_to_la_signs,
)

__all__ = [
    "EteocretanInscription",
    "EteocretanWord",
    "ET_DR1", "ET_DR2", "ET_PR1", "ET_PR2",
    "ET_PR3", "ET_PR4", "ET_PR5",
    "ALL_INSCRIPTIONS", "ALL_WORDS",
    "build_corpus",
    "ComparisonResult",
    "run_all_comparisons",
    "analyze_bilinguals",
    "compare_phonotactics",
    "map_words_to_la_signs",
]
