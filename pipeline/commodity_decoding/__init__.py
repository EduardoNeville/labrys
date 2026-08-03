"""
Commodity-Semantic Decoding Module
===================================
Phase 7 — Approach 2 of 5: Commodity-semantic decoding.

Extracts syllabogram context windows around known commodity logograms,
clusters adjacent sequences by commodity class, and identifies candidate
commodity-name phonemes.

Modules:
  - context_extract: Extract ±3 sign windows around commodity logograms
  - semantic_cluster: Cluster sequences, rank distinctiveness, hypothesize proto-words

Outputs:
  data/analysis/commodity_decoding/logogram_contexts.csv
  data/analysis/commodity_decoding/commodity_signatures.csv
  data/analysis/commodity_decoding/commodity_report.md
"""

from pipeline.commodity_decoding.context_extract import (
    classify_commodity,
    extract_contexts,
)

from pipeline.commodity_decoding.semantic_cluster import (
    extract_sequences,
    build_ngram_profiles,
    score_distinctiveness,
    analyze_uncertain_signs,
    reconstruct_proto_words,
    build_report,
)

__all__ = [
    "classify_commodity",
    "extract_contexts",
    "extract_sequences",
    "build_ngram_profiles",
    "score_distinctiveness",
    "analyze_uncertain_signs",
    "reconstruct_proto_words",
    "build_report",
]
