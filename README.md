# Labrys — Linear A Decipherment Project

Systematic, multi-phase computational approach to deciphering Linear A, the undeciphered script of Minoan Crete (ca. 1800–1450 BCE).

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| **1 — Data** | Corpus digitization, schema, Unicode, SQLite | ✅ Complete |
| **2 — Analysis** | Positional grid, word segmentation, n-gram, network, logogram/fraction analysis | ✅ Complete |
| **3 — Linguistic** | Swadesh-100 testing, WALS typology, loanword matching, toponym alignment, morphology scan | ✅ Complete |
| **4 — ML Decipherment** | Transformer models, contrastive learning, GAN decipherment | ⬜ Next |
| **5 — Comparative** | LA↔LB mapping, Cypro-Minoan bridge, phonetic grid refinement | ✅ Complete |
| **6 — Verification** | Blind hold-out, cross-expert review, predictive testing | ⬜ Pending |
| **7 — Collaboration** | Open-science infrastructure, community standards | ⬜ Pending |

**Key finding (Phase 3):** Tyrsenian (Etruscan-related) is the best structural fit among non-isolate candidates, but no family shows statistically significant lexical matches.

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) for package management

### Install

```bash
git clone git@github.com:EduardoNeville/labrys.git
cd labrys
uv sync
```

For GPU (Phase 4 ML):

```bash
uv sync --extra cu121   # on GPU server
```

### Verify

```bash
uv run python demo.py
uv run python -m pipeline.cli db stats data/database/lineara_full.db
# Expected: 1,719 inscriptions, 11,018 signs, 312 unique signs, 62 sites
```

## What We Know

- **44 syllabograms confirmed** (of 138) — ~32%
- **~10 place names** identified with varying confidence (Phaistos, Ida, Tylissos, Dikte, Setoia, Sybrita)
- **~5 accounting terms** known from tablet context (ku-ro "total", po-to-ku-ro "grand total", ki-ro "owed")
- **~2 religious formula** recognized (a-sa-sa-ra, ja-sa-sa-ra-me) from libation tables
- **124 logogram types** identified — ~40 have clear commodity meanings
- **29 fraction signs** with proposed mathematical values
- **Morphological profile:** agglutinative, suffixal, head-final, no grammatical gender

## Project Structure

```
labrys/
├── pipeline/              # 26 Python modules (Phases 1–5)
│   ├── models.py          # Data models (7-tier schema)
│   ├── database.py        # SQLite corpus (1,719 inscriptions)
│   ├── unicode_utils.py   # Bennett AB → Unicode Aegean mapping
│   ├── positional_analysis.py   # Kober-style grid analysis
│   ├── word_segmentation.py     # 5-strategy word segmenter
│   ├── ngram_analysis.py        # N-grams, entropy, misvalued scan
│   ├── network_analysis.py      # Graph co-occurrence + communities
│   ├── swadesh_search.py        # 6-family Swadesh-100 testing
│   ├── wals_analysis.py         # WALS typology comparison
│   ├── loanword_matching.py     # Pre-Greek substrate matching
│   ├── toponym_alignment.py     # Place name phonetic anchors
│   ├── morphology_scan.py       # Paradigm detection, agglutination
│   ├── falsification_report.py  # Synthesis + ranking
│   ├── linear_b_mapping.py      # LA↔LB confidence-rated mapping
│   ├── cypro_minoan_bridge.py   # LA→CM→Cypriot Greek bridge
│   ├── commodity_alignment.py   # LA↔LB logogram/fraction alignment
│   ├── phonetic_grid_refinement.py   # Final refined phonetic grid
│   ├── logogram_analysis.py     # Commodity ontology + fractions
│   └── cli.py             # Click CLI with 7 commands
│
├── data/
│   ├── database/          # lineara_full.db (SQLite, 3.6 MB)
│   ├── analysis/          # 90+ output CSVs across all phases
│   │   ├── positional/    # Sign positional profiles + clusters
│   │   ├── segmentation/  # Word-segmented corpus
│   │   ├── ngram/         # N-gram freqs, entropy, typology
│   │   ├── network/       # Graph centrality + communities (5 sites)
│   │   ├── logograms/     # Commodity ontology + fraction values
│   │   ├── linguistic/    # Phase 3: Swadesh, WALS, loanwords, falsification
│   │   └── comparative/   # Phase 5: refined phonetic grid, LA↔LB mapping
│   └── corpus/            # linear_a_inventory.csv (625 texts)
│
├── docs/                  # Schema docs (TEI ODD, JSON-LD, examples)
├── pyproject.toml         # Project config + dependencies (uv)
├── uv.lock                # Lockfile for reproducible installs
└── demo.py                # End-to-end pipeline demo
```

## What Remains (Phase 4 — ML Decipherment)

The project is now ready for ML-based decipherment. With the full corpus in a normalized database and all analysis outputs available, the next step is to train models leveraging:

- **70% AB sign overlap** between Linear A and deciphered Linear B as weak supervision
- **Cypro-Minoan triangular inference** (LA → CM → Cypriot Greek)
- **Pre-Greek substrate loanwords** as Rosetta-fragment anchors
- **Positional + n-gram anomaly signals** from Phase 2 to guide model attention

## For Agents

See [AGENTS.md](AGENTS.md) for conventions, data access patterns, and how to work on this project.
