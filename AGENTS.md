# AGENTS.md — How to Work on the Labrys Project

## Project Context

We are systematically deciphering Linear A, the undeciphered script of Minoan Crete. Phases 1–3, 5, 7–9 and 11–15 are complete; Phase 4 (ML) is **built but unvalidated and stale** with respect to the corrected grid (its outputs are not citable — see `CODE_AUDIT.md`); the Ventris method family (Phase 10) is **closed negative**, and Phase 16 (cross-script chain) is the project's only pre-registered pass.

## Important: What We Actually Know

Read [`CODE_AUDIT.md`](CODE_AUDIT.md) before citing anything. It records, file by file, which
code is live, which avenue is concluded, and which claims were retracted — with the number that
retracted them. Several numbers that circulate in older docs (0.6× oracle, "78 anchors",
"312 signs", "Tyrsenian best fit", "AB 85 word divider", "pa-i-to") are superseded there.

Be realistic about the state of the field. We have not "deciphered" Linear A. What we have,
with the instrument attached because the counts disagree (`CODE_AUDIT.md` §4):

- **Sign inventory:** ~205 attestation IDs in the DB. The honest phonetic grid is **69 real
  signs** (`expanded_grid_purged.csv`): 58 CONFIRMED + 11 UNCERTAIN. The Phase 5 refined grid
  reaches 40 CONFIRM, **35 of them on signs that exist**. The two grids are unreconciled — never
  write "N confirmed" without naming the grid.
- **Logograms:** **88** distinct IDs / 742 occurrences. "124" is unsupported.
- **Words:** ~15–20 with provisional meanings, mostly accounting terms and place names. Only
  **`i-da`** survives a findspot control; `pa-i-to` fails its own.
- **Morphology:** agglutinative, suffixal, no gender — weakly supported.
- **Language family:** **none confirmed.** Anatolian IE and Hurro-Urartian tie at rank 1,
  Tyrsenian 3, all "INCONCLUSIVE (tentative)". Do not describe Tyrsenian as the best fit.
- **The one cross-site replication:** the libation formula (11/11 opening at position 0, 5 sites).

Do not overclaim. This is a 70-year-old unsolved problem for good reasons.

## Environment

```bash
# Use uv for everything
./tools/bootstrap.sh   # fresh clone: deps + Linear B sandbox + grid check + guards (idempotent)
uv sync              # install deps (no torch; add --extra ml for Phase 4 ML)
uv run python ...    # run any script through uv's venv
uv run python -m pipeline.cli ...  # CLI access
uv run python pipeline/guards.py   # 15/15 before trusting any analysis output
```

`uv run` re-syncs from `pyproject.toml`, so it is the supported way to run anything. Python is
pinned to 3.12 — 3.14 removed the venv trying to build a cu121 torch wheel.

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

Key tables — **only four have rows** (`CODE_AUDIT.md` §6):
- `inscriptions` (1,719) — gorila_id, findspot_id, material, object_type, minoan_period
- `signs` (11,018) — inscription_id, sequence, bennett_id, character, sign_type, transliteration
- `findspots` (62) — site name, coordinates
- `images` (1,718)

**Empty and not a data source:** `words`, `word_dividers`, `lacunae`, `lines`, `sign_semantics`,
`relations_linear_b`, `bibliography`. Segmentation lives in
`data/analysis/segmentation/segmented_texts_consensus.csv`; logogram semantics in
`data/analysis/logograms/commodity_ontology.csv`.

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

> **Numbers verified against the DB 2026-10-02** (`verify:header-counts` in `pipeline/rsi_loop.py`):
> 1,719 inscriptions, 11,018 sign occurrences, 62 findspots — all confirmed. **The "312 unique
> Bennett IDs" figure is not reproducible**: `signs` holds **206** distinct Bennett IDs (205
> non-empty, 5,960 of 11,018 rows have one), and the union across the grid and mapping files is
> **269**. Neither is 312, and no artifact in the repo yields it. Treat the ID count as ~206 and
> re-derive before citing it.

- 1,719 inscriptions, 11,018 sign occurrences
- 312 unique Bennett IDs *(see the note above: the DB holds 206 distinct non-empty IDs; 312 is unverified)*, 62 findspots, 12 periods
- 1,308 texts from LM IB (~1450 BCE destruction horizon)
- Largest archive: Hagia Triada (~863 inscriptions)
- Longest text: HT 117a (82 signs)
- Most texts are administrative (tablets, nodules, sealings)
- No narrative/literary texts exist

## Key Analysis Outputs (Where to Find Things)

| What | Where | Status |
|------|-------|--------|
| Positional sign profiles | `data/analysis/positional/positional_profiles.csv` | live |
| Anomalous signs (Phase 2) | `data/analysis/positional/anomalous_signs.csv` | live (3 rows) |
| Misvalued AB signs | `.../positional/misvalued_signs_ranked.csv`, `.../comparative/misvalued_signs_resolution.csv` | ⚠️ contested/stale — see the section below |
| Word-segmented corpus | `data/analysis/segmentation/segmented_texts_consensus.csv` | live |
| N-gram frequencies | `data/analysis/ngram/ngram_freqs.csv` | live |
| Sign co-occurrence graph | `data/analysis/network/global/sign_centrality.csv` | live |
| Fraction values | `data/analysis/logograms/fraction_values_proposed.csv` | ⚠️ 16/29 circular — use `fraction_values_audit.csv` |
| Swadesh test results | `data/analysis/linguistic/swadesh_results.csv` | live (negative) |
| WALS typology matrix | `data/analysis/linguistic/wals_comparison.csv` | live |
| Falsification ranking | `data/analysis/linguistic/candidate_ranking.csv` | live (all inconclusive) |
| LA↔LB sign mapping | `data/analysis/comparative/la_lb_mapping.csv` | live (glyphs + `lb_value` repaired) |
| Cypro-Minoan values | `data/analysis/comparative/la_cm_shared_phonetic_grid.csv` | live — input to the Phase 16 PASS |
| Refined phonetic grid | `data/analysis/comparative/refined_phonetic_grid.csv` | ⚠️ **stale** — 69 phantom rows, 5 CONFIRM |
| Honest grid (use this) | `data/analysis/bootstrapping/expanded_grid_purged.csv` | live — regenerable (`purge_grid.py --check`) |
| Phase 3 synthesis | `data/analysis/linguistic/phase3_synthesis.md` | historical (carries superseded numbers) |
| Phase 5 synthesis | `data/analysis/comparative/phase5_synthesis.md` | historical |
| Audit trail | `data/analysis/ventris/verification_audit.md` | **canonical — read before citing anything** |
| Code status | `CODE_AUDIT.md` | **canonical — what is live / concluded / retracted** |

## Key Findings to Reuse

> **Archive stratification is mandatory (2026-10-01).** Haghia Triada *Portico 11 and Room 13*
> alone is **863 of 1,719 inscriptions (50.2%)** and has its own tablet format, so any pooled
> positional/distributional/functional statistic is mostly a statistic about that room. **Two rooms
> of the same site disagree** (A 301 is initial in 229/231 occurrences at Portico and 0/3 at Villa
> Magazine). Compute per archive and report across archives; a pooled number answers a question
> about the largest room. Three survivors of every earlier audit were re-tested this way and two
> failed (commodity enrichment: fails cross-site; A 301's "heading" profile: Portico-specific) while
> one passed (libation formula: 5 sites, 9/9 slot order). Tool: `python data/analysis/ventris/archive_stratification.py --sign "A 301"`. See `verification_audit.md` Phases 14, 14.1, 15.

### Misvalued AB Signs (Phase 2 + Phase 5)

**Status: contested — do not cite without re-deriving.** `data/analysis/comparative/misvalued_signs_resolution.csv`
still carries a phantom row (AB 36 `jo`, a sign with no codepoint and 0 occurrences) and predates
the Phase 12 CONFIRM policy (`verification_audit.md`). The Phase 2 anomaly list stands as a
*flag*; the "misvalued" interpretation does not, and the corrected-corpus rerun records
AB 16/60/80 as no longer anomalous. Re-derive via `phonetic_grid_refinement.py` after the
grid itself is re-derived (`CODE_AUDIT.md` §8 items 1–2).

AB 85 was **removed** from this list in Phase 12: the 508-occurrence "never medial" profile that motivated it belongs to the logogram **A 301**, not to the syllabogram AB 85 (n=8, medial=0.75, i.e. medial-dominant). See `data/analysis/ventris/verification_audit.md` Phase 12 Addendum. **Caveat (2026-10-01):** A 301's replacement profile ("entry-initial") is itself archive-local — 229/231 initial at Haghia Triada Portico 11 and Room 13, 9/43 elsewhere. The retraction stands (it rests on the occurrence count, not the profile); do not cite the profile as a general property.

### Best Language Family Fit
No family is distinguished. Phase 3 candidate ranking: Anatolian IE and Hurro-Urartian tie at #1 (score 8), Tyrsenian #3 (score 7) — ALL marked "INCONCLUSIVE (tentative)". Tyrsenian shows the best *structural* WALS profile in some readings but is lexically weak (0 exact Swadesh matches, p=1.0). No family confirmed; several weakly compatible.

### Most Secure Place Names
pa-i-to (Phaistos), i-da (Mt. Ida) — HIGH confidence. di-ka-ta (Dikte), su-ki-ri-ta (Sybrita) had exact matches. Verified: 95 Phaistos matches (dist=1), 20 Ida matches robust to the da/ta conflict.

### Phase 10-11 Verified Findings
- **Oracle (10c)**: the grammatical scorer has NO signal — **recovery 0.00× chance (0/160)**. The earlier "0.6× chance" figure was leak-contaminated (anchor-word leak + a chance baseline computed from the full anchor set); both fixed in Phase 12. No optimizer can help. See `pipeline/ventris/complete.py` `oracle_test()` and `data/analysis/ventris/verification_audit.md` Phase 12.
- **Corpus correction (11)**: 144 Unicode→Bennett mapping errors + 29 phantom codepoints fixed. The corpus is now correct (IOZa2 reads A-TA-I-*301-WA-JA per GORILA). See `data/analysis/ventris/corpus_correction.md`.
- **Grid purge (11)**: the expanded grid has 69 real signs (58 CONFIRMED + 11 UNCERTAIN). 69 phantom entries removed — including AB 68 (the old "Phase 7 ro resolution", VOID) and all AB 100-137. Use `data/analysis/bootstrapping/expanded_grid_purged.csv`, NOT the old 138-sign grid.
- **Libation formula (11, audited 2026-10-01)**: recovered on the corrected corpus — ja-sa-sa-ra-me (**9** insns), u-na-ka-na-si (**6**), si-ru-te (**7**), opening A-TA-I-*301-WA-JA (**11**, at position 0 in **11 of 11**). Recent re-derivation from the corpus reproduces every count and both structural claims exactly: in all **9** texts carrying two or more formula words, they appear in the documented slot order (9/9). **Spanning 5 sites** (Iouktas, Platanos, Psykhro, Troullos, Palaikastro). Phonetically inert (LB-transfer values, cannot yield new ones), and the word translations are the source's tentative readings. **It is the project's only result that replicates across sites** — on the same day the commodity associations failed the same test — which says the structure that generalises is *genre and formula*, not corpus-wide enrichment. See `data/analysis/ventris/libation_recovered.md`.
- **Commodity (11, corrected; audited 2026-10-01; replication FAILED)**: AB 30↔LIVESTOCK and AB 28↔WINE. **The association is real within Haghia Triada and does not generalize.** Auditing it: the recorded null was wrong (adjacent *slots* from ±3 windows are not independent draws — the effective sample is documents); at the document level the two claims are p=2.69e-11 / 2.63e-05 and they clear a site-stratified permutation at the floor of 20,000 reps (z=7.1). But **selection on Haghia Triada → test on Khania replicates 2 of 67 pairs, and both are logogram↔own-class tautologies** (A 303↔LIVESTOCK, A 301↔PERSONNEL); every syllabogram association fails (AB 30 p=4.4e-02, AB 81 p=0.27, AB 31 p=0.42; the WINE pairs have no Khania population at all). So: a property of HT's entry conventions, **not** semantic anchors for Linear A. Bonferroni family is 122 tests (alpha=0.00041), not 61. See `data/analysis/commodity_decoding/enrichment_audit.py`, `cross_site_replication.py`, and `verification_audit.md` Phase 14/14.1.
- **AB 41 (si)** is the most frequent UNCERTAIN sign (240 occ) and the key open target.
- **Retracted**: "AB 85 word divider", "AB 82↔LIVESTOCK" (circular), "Tyrsenian best fit", "78 anchors", "diachronic prior" (all invalidated by correction). See `data/analysis/ventris/verification_audit.md` and `data/analysis/ventris/corrected_rerun_results.md`.

## Phase 4 ML Guidance

**Read `CODE_AUDIT.md` §2 item 11 and §8 item 1 first.** The Phase 4 code exists and runs, but its
training labels come from `refined_phonetic_grid.csv`, which still carries the 69 phantom rows
(5 of them CONFIRM) and predates the Phase 12 CONFIRM policy. Its committed outputs are therefore
not citable, and the module set is behind the optional `ml` extra (`uv sync --extra ml`).

The last honest Phase 4 result was **0 high-confidence predictions**. Any restart should begin
with the grid re-derivation, not with a training run.

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
