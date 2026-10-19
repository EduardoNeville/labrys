# TODO.md — Egyptian Bridge Marshal

## Core Tasks
- [x] Read all input files (DB, grid CSVs, AGENTS.md)
- [x] Build `pipeline/egyptian_bridge/__init__.py`
- [x] Build `pipeline/egyptian_bridge/corpus.py` (~88 Egyptian trade words)
  - [x] Encode Middle Egyptian consonantal vocabulary
  - [x] Map Egyptian consonants → LA CV signs
  - [x] CSV output to data/analysis/egyptian_bridge/
- [x] Build `pipeline/egyptian_bridge/search.py` (consonant-class search)
  - [x] Fix initial CV-matching too strict (changed to consonant-class matching)
  - [x] Map Egyptian consonant → class (P/T/K/S/N/R/W/G/H)
  - [x] Map LA syllabogram → class (by onset consonant)
  - [x] Substring search in both conventional and expanded sequences
  - [x] Filter for >=3-sign matches
  - [x] Flag commodity-adjacent contexts (±3 signs)
  - [x] Score matches (length + context + category)
  - [x] Null-model estimation (per-inscription shuffling)
  - [x] CSV output + Markdown report
- [x] Run and verify all outputs
- [x] Write report and result

## Discovered Sub-Tasks
- [x] Fix: initial CV-skeleton mapping was too rigid — false negative heavy
  (only 1 match). Rewrote to consonant-class approach.
- [x] Fix: nasal separation (m/n as N-class, separate from P and T)
- [x] Fix: commodity context detection used wrong index mapping
- [x] Fix: null model should shuffle per-inscription, not global string
- [x] Verify top matches against actual DB sequences (sntr, Ssr, SDr confirmed)
