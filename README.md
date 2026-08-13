# Labrys — Linear A Decipherment Project

Systematic, multi-phase computational approach to deciphering Linear A, the undeciphered script of Minoan Crete (ca. 1800–1450 BCE).

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| **1 — Data** | Corpus digitization, schema, Unicode, SQLite | ✅ Complete |
| **2 — Analysis** | Positional grid, word segmentation, n-gram, network, logogram/fraction analysis | ✅ Complete |
| **3 — Linguistic** | Swadesh-100 testing, WALS typology, loanword matching, toponym alignment, morphology scan | ✅ Complete |
| **4 — ML Decipherment** | Transformer models, contrastive learning, GAN decipherment | ✅ Complete |
| **5 — Comparative** | LA↔LB mapping, Cypro-Minoan bridge, phonetic grid refinement | ✅ Complete |
| **6 — Verification** | Cross-evidence triangulation, toponym testing, internal consistency | ✅ Complete |
| **7 — Alternatives** | Five independent approaches (Eteocretan, commodity decoding, phylogenetic, Kober, Anatolian) | ✅ Complete |
| **8 — Kober Bootstrapping** | 78 CONFIRMED anchors from Kober triples + bootstrapped values | ✅ Complete |
| **9 — Formulaic Parallelism** | Substitution frames, prefix/suffix system identification | ✅ Complete |
| **10 — Ventris Endgame** | Grid completion via grammatical testing (10a Egyptian bridge, 10b grid completion, 10c oracle test) | ⬜ Concluded — negative |
| **11 — Avenues** | Four phonetic-independent approaches (positional, commodity, cryptanalysis, graph) + diachronic prior | ⬜ Concluded — one positive (diachronic) |

**Key finding (Phase 3):** No language family is distinguished — Anatolian IE, Hurro-Urartian, and Tyrsenian are all weakly compatible but inconclusive; none shows statistically significant lexical matches.

**Phase 10 outcome:** The oracle ablation test proved the grammatical scorer has no signal to recover known sign values (recovery 0.6× chance). Grid completion is closed pending new data — see `data/analysis/ventris/ventris_report.md`.

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

## What Remains

All 10 phases are complete, and Phase 11 (avenues after the oracle failure) is concluded. The outcome is honest and verified:

- **10a** — Egyptian bridge: no detectable Egyptian loanwords (matches ≈ chance, null-model ratios 1.6–6.4×)
- **10b** — Frequency-typology grid constraints: 28.2% of candidates eliminated, but random sampling of ~10¹⁴⁰ completions yields zero per-sign consensus
- **10c** — Oracle ablation test: a greedy restore of hidden CONFIRMED signs recovered them at **0.6× chance** — the grammatical scorer (morphology/entropy/prefix + Kober-consistency + anchor words) has no signal to distinguish true phonetic values. No optimizer (beam, annealing, Optuna) can help an objective with no gradient.
- **11** — Four phonetic-independent avenues (positional, commodity, cryptanalysis, graph): all negative or circular after proper controls. **One positive finding: the diachronic prior** — signs attested in both MM and LM periods are 2× more likely CONFIRMED (Fisher p=0.0003), independent of the phonetic evidence.

The bottleneck is corpus size (11K tokens) and the absence of independent phonetic evidence — every signal derives circularly from Linear B transfer. **Grid completion is closed pending new data** (new inscriptions, a bilingual find, or confirmed Cypro-Minoan values).

The oracle harness (`pipeline/ventris/complete.py`, `oracle_test`) remains the correct gate for any future scorer or new evidence. The diachronic prior (`pipeline/ventris/diachronic.py`) re-weights sign confidence by period attestation: `conf × (2.0 if MM else 0.5)`.

## For Agents

See [AGENTS.md](AGENTS.md) for conventions, data access patterns, and how to work on this project.
