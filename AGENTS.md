# AGENTS.md — How to Work on the Labrys Project

## Project Context

We are systematically deciphering Linear A, the undeciphered script of Minoan Crete. The project has completed Phases 1–3 and 5 (infrastructure, analysis, linguistic testing, comparative script bridging). Phase 4 (ML) is next.

## Important: What We Actually Know

Be realistic about the state of the field. We have not "deciphered" Linear A. We know:
- ~44 of ~138 syllabograms with confidence
- ~15–20 words with high-confidence meanings (mostly accounting terms and place names)
- The morphological profile (agglutinative, suffixal, no gender)
- 124 logogram types with economic semantics
- No confirmed language family (Tyrsenian is best structural fit but lexically weak)

Do not overclaim. This is a 70-year-old unsolved problem for good reasons.

## Environment

```bash
# Use uv for everything
uv sync              # install all deps
uv run python ...    # run any script through uv's venv
uv run python -m pipeline.cli ...  # CLI access
```

## Code Conventions

### Python
- Target Python 3.10+
- Use only standard library + sqlite3 + csv + json where possible (for pipeline modules)
- ML modules may use torch, transformers, scikit-learn
- All scripts live in `pipeline/`
- Use `logging` module, not `print()` for output
- Dataclasses (from Phase 1 models.py) are the canonical data model

### Database Access

```python
import sqlite3
conn = sqlite3.connect('data/database/lineara_full.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
```

Key tables:
- `inscriptions` — gorila_id, findspot_id, material, object_type, minoan_period
- `signs` — inscription_id, sequence, bennett_id, character, sign_type, transliteration
- `findspots` — site name, coordinates
- `sign_semantics` — logogram meanings
- `words`, `word_dividers`, `lacunae` — from segmentation

### CLI

```bash
uv run python -m pipeline.cli --help
uv run python -m pipeline.cli db stats data/database/lineara_full.db
uv run python -m pipeline.cli db query data/database/lineara_full.db --site "Haghia Triada" --json
```

### Running Analysis Scripts

Most pipeline/*.py scripts can be run standalone:
```bash
uv run python pipeline/positional_analysis.py
uv run python pipeline/ngram_analysis.py
uv run python pipeline/swadesh_search.py
```

All output data to `data/analysis/<category>/`.

## Data Model (Quick Reference)

```
Inscription
├── gorilaId (e.g., "HT 1")
├── findspot { site, coordinates }
├── date { minoanPeriod, bceRange }
├── material, objectType, preservation
├── signs[]          # SignInstance in reading order
│   ├── bennettId    # AB 01, AB 02, ..., A 301, etc.
│   ├── unicode      # U+10600+
│   ├── transliteration  # "da", "ro", "pa"
│   ├── signType     # syllabogram|logogram|fraction|numeral|metrical
│   └── sequence     # ordinal position
├── structure { lines, words, sides }
├── images[]
└── relations { linearB, cyproMinoan }
```

## Sign System (Bennett AB)

- **AB 01–137**: Syllabograms (CV structure)
- **A 301–402**: Logograms / ideograms (commodities, measures)
- **A 701–730**: Fraction signs
- **A 501–594**: Metrical signs, vase shapes, adjuncts

Phonetic values are from Linear B transfer (NOT confirmed for Linear A). Phase 5 refined grid marks each as CONFIRM/REVISE/UNCERTAIN.

## Corpus Facts

- 1,719 inscriptions, 11,018 sign occurrences
- 312 unique Bennett IDs, 62 findspots, 12 periods
- 1,308 texts from LM IB (~1450 BCE destruction horizon)
- Largest archive: Hagia Triada (~863 inscriptions)
- Longest text: HT 117a (82 signs)
- Most texts are administrative (tablets, nodules, sealings)
- No narrative/literary texts exist

## Key Analysis Outputs (Where to Find Things)

| What | Where |
|------|-------|
| Positional sign profiles | `data/analysis/positional/positional_profiles.csv` |
| Misvalued AB signs (Phase 2) | `data/analysis/positional/misvalued_signs_ranked.csv` |
| Word-segmented corpus | `data/analysis/segmentation/segmented_texts_consensus.csv` |
| N-gram frequencies | `data/analysis/ngram/ngram_freqs.csv` |
| Sign co-occurrence graph | `data/analysis/network/global/sign_centrality.csv` |
| Fraction values | `data/analysis/logograms/fraction_values_proposed.csv` |
| Swadesh test results | `data/analysis/linguistic/swadesh_results.csv` |
| WALS typology matrix | `data/analysis/linguistic/wals_comparison.csv` |
| Falsification ranking | `data/analysis/linguistic/candidate_ranking.csv` |
| LA↔LB sign mapping | `data/analysis/comparative/la_lb_mapping.csv` |
| Cypro-Minoan values | `data/analysis/comparative/la_cm_shared_phonetic_grid.csv` |
| Refined phonetic grid | `data/analysis/comparative/refined_phonetic_grid.csv` |
| Phase 3 synthesis | `data/analysis/linguistic/phase3_synthesis.md` |
| Phase 5 synthesis | `data/analysis/comparative/phase5_synthesis.md` |

## Key Findings to Reuse

### Misvalued AB Signs (Phase 2 + Phase 5) 
AB 16 (qa), AB 60 (ra vs ma conflict), AB 80 (ma), AB 22 (pi), AB 02 (ro/i dual), AB 85 (word divider) — see `data/analysis/comparative/misvalued_signs_resolution.csv`

### Best Language Family Fit
Tyrsenian (Etruscan) ranks highest structurally (5/8 WALS features, 62.5%), but lexically weak (0 exact Swadesh matches, p=1.0). No family confirmed.

### Most Secure Place Names
pa-i-to (Phaistos), i-da (Mt. Ida) — HIGH confidence. di-ka-ta (Dikte), su-ki-ri-ta (Sybrita) had exact matches.

## Phase 4 ML Guidance

When building ML models:
- The corpus is tiny (~11K tokens) — data augmentation and transfer learning are essential
- ~70% of AB signs have Linear B cognates with known phonetic values (weak supervision signal)
- The refined phonetic grid marks which signs are CONFIRMED vs UNCERTAIN
- Positional anomalies (Phase 2) flag signs most likely misvalued
- Cypro-Minoan triangular evidence provides independent phonetic constraints
- Pre-Greek loanwords provide Rosetta-fragment anchors
- Train on the 40 longest texts (≥20 signs) first — they have the most context

## Commit Style

```
feat(pipeline): add module-name for new capability
fix(pipeline): fix specific issue
docs: update documentation
chore: maintenance tasks
build: dependency/package changes
```

## Run a Full Verification

```bash
uv run python demo.py                           # Pipeline demo
uv run python -m pipeline.cli unicode validate   # Mapping check
uv run python pipeline/positional_analysis.py    # Quick analysis
```
