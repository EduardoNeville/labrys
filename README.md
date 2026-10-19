# Labrys — Linear A Decipherment Project

Systematic, multi-phase computational approach to Linear A, the undeciphered script of Minoan
Crete (ca. 1800–1450 BCE).

**Read this with [`CODE_AUDIT.md`](CODE_AUDIT.md) open.** That document states, file by file,
which code is live, which avenue is concluded, and which claims were retracted and why. Several
numbers that older project summaries carry (0.6× oracle, "78 anchors", "312 signs", "Tyrsenian
best fit", "AB 85 word divider") are superseded; the audit lists every one.

## Status

| Phase | Description | Status |
| 1 — Data | Corpus digitization, schema, Unicode, SQLite | ✅ Complete (1,719 inscriptions, 11,018 signs) |
| 2 — Analysis | Positional grid, segmentation, n-gram, network, logograms | ✅ Complete |
| 3 — Linguistic | Swadesh-100, WALS, loanwords, toponymy, morphology | ✅ Complete — **no family distinguished** |
| 4 — ML | Transformer / contrastive experiments | ⚠️ **Built, unvalidated, stale** — inputs moved after the corpus correction; outputs are not citable |
| 5 — Comparative | LA↔LB mapping, Cypro-Minoan bridge, grid refinement | ✅ Complete — 34 CONFIRM on 71 real signs |
| 6 — Verification | Cross-evidence triangulation, toponym testing | ⚠️ consumes Phase 4 outputs — stale with them |
| 7–9 — Alternatives | Eteocretan, commodity, phylogenetic, Kober, Anatolian, formulaic | ✅ Complete — **all negative after controls** |
| 10 — Ventris endgame | Grid completion by grammatical testing | ⬜ **Concluded negative** — 1/160 recovered, 0.056× chance |
| 11 — Correction + purge | 144 mapping errors + 29 phantoms fixed; libation formula recovered; grid purged | ✅ Complete — honest 69-sign grid |
| 12–15 — Audits | Oracle machinery, commodity enrichment, archive stratification | ✅ Complete — most positives failed replication |
| 16 — Cross-script chain | LA → Cypro-Minoan → Cypriot Syllabary | ✅ **PASS** — 44.65×, 45/54 (the project's only pre-registered pass) |

The method-search loop is closed: π₀ (stop) is optimal on both splits at every weight, so the
recorded tree is replayable evidence rather than a queue.

## Quick Start

```bash
git clone git@github.com:EduardoNeville/labrys.git && cd labrys
./tools/bootstrap.sh          # uv sync → Linear B sandbox → grid check → 17/17 guards
```

`bootstrap.sh` is the only supported entry point for a fresh clone: the Linear B sandbox database
is gitignored (9.7 MB, rebuilt from `languages/linear-b/data/raw/tablets.csv`), so two guards
would otherwise fail for a reason that is not a defect.

```bash
uv sync                       # corpus + analysis deps (no torch)
./tools/bootstrap.sh --extra-ml   # adds the Phase 4 ML stack (which now lives in legacy/ml/)

uv run python -m pipeline.cli db stats data/database/lineara_full.db
# → 1,719 inscriptions, 11,018 signs, 205 distinct Bennett IDs, 62 findspots
uv run python pipeline/guards.py   # 17/17 + the non-fatal defect reports
./tools/rsi_loop.sh                # nightly re-check of every recorded number
```

Python is pinned to 3.12 (`.python-version`, and `requires-python = ">=3.10,<3.14"`): `uv` once
picked 3.14 and deleted the venv trying to build a cu121 torch wheel that has no 3.14 build.

## What we actually know

Deliberately stated with instruments attached, because the counts disagree (see `CODE_AUDIT.md` §4):

- **Sign inventory:** ~205 attestation IDs in the DB. The honest phonetic grid is **71 real signs,
  53 CONFIRM** (`expanded_grid_purged.csv`, Phase 8 lineage), covering the same 71 signs as the
  Phase 5 refined grid (**34 CONFIRM** — a different instrument). **AB 41 (si)**, 240 occurrences,
  is the notable open target: the Phase 8 lineage confirms its *identity* with value `?`, which is
  not an argument for `si`. The grids are not reconciled on values.
- **Logograms:** 88 distinct IDs, 742 occurrences (not 124).
- **Fractions:** 29 IDs. **16 of 29 proposed values are circular** and 1 is corroborated by the
  Linear B fraction series — treat the file as unaudited (`verification_audit.md` Phase 12).
- **Place names:** `i-da` (13 exact matches) is the only toponym that survives a findspot control.
  `pa-i-to` fails its control (95 fuzzy hits collapse to 1 exact). `di-ka-ta`, `su-ki-ri-ta`: not
  independently established.
- **The one thing that replicates across sites:** the **libation formula** — opening
  `A-TA-I-*301-WA-JA` in 11 of 11 texts at position 0 (`AB 08 AB 59 AB 28 A 301 AB 54 AB 57`),
  `ja-sa-sa-ra-me` (9), `si-ru-te` (7), `u-na-ka-na-si` (6), `i-pi-na-ma` (6), across 5 sites,
  9/9 slot order in multi-formula texts (`libation_recovered.md`, now checked against the corpus
  by a guard).
- **Morphology:** agglutinative, suffixal, no gender — weakly supported.
- **Language family:** none. Anatolian IE and Hurro-Urartian tie at rank 1, Tyrsenian 3 — all
  "INCONCLUSIVE (tentative)". Zero exact Swadesh matches for any family.

### What is closed, with the number

| route | closed by |
| Ventris scorer / any optimizer (beam, annealing, GPU MCMC, weight sweep) | **0.056×, 1/160**; **0 of 1,771** weight vectors recover a value |
| Frame links, paradigm-slot alternation, series/vowel voting | at or below chance in 4 operationalizations (best 1.03×) |
| Diachronic (MM→LM) prior | p=0.0003 → **0.1748** after correction |
| `AB 85` word divider, `AB 82`↔LIVESTOCK | artifact of a sign mis-attribution and of the encoding |
| Commodity semantic anchors | real at Haghia Triada, **does not replicate** (2/67 pairs, both tautologies) |
| `pa-i-to`, `A 301` heading profile | fail their controls (exact recount 1; 229/231 vs 9/43 across archives) |
| Egyptian loans, Eteocretan, Anatolian cognates, phylogenetic parsimony | no signal above null |

**The Linear A oracle, re-derived:** 1/160 recovered at **0.056× chance** — below chance, not merely
short of the 1.5× gate (`verification_audit.md` Phase 18; the Phase 12 figure of 0/160 / 0.00× was
measured on a Kober graph that predated the corpus correction).

**The bottleneck, stated once:** the corpus is ~11k sign tokens, every phonetic signal derives
circularly from Linear B transfer, and no independent phonetic evidence exists. That is why the
one route that passed (cross-script shape → Cypro-Minoan → Cypriot Syllabary) is also the route
that **validates but cannot extend** — every row where it would propose a new value is a
LOW-confidence correspondence. New data is the unlock: a real CM corpus with established values,
a bilingual, or new inscriptions.

## Project structure

```
labrys/
├── CODE_AUDIT.md               # what is live / concluded / retracted — read first
├── CLEANUP_PLAN.md             # what moved to legacy/ and why (old→new path map)
├── EXPERIMENT_PROTOCOL.md      # binding rules for any measurement
├── archive/                    # retracted + wrong turns, with the falsifying number
├── legacy/                     # concluded avenues — importable, never imported by pipeline/
├── pipeline/                   # the live tree: 62 files, 34k LOC
│   ├── models.py database.py unicode_utils.py phonetics.py   # core
│   ├── ingest.py ingest_lineara.py parsers                    # corpus build
│   ├── guards.py purge_grid.py                                # gates
│   ├── lb_ingest.py lb_oracle.py ventris/complete.py           # oracle
│   ├── cm_acceptance_test.py comparative_bridge.py             # cross-script PASS
│   ├── rsi_*.py                                               # method-search replay pool
│   └── <phase modules>                                        # frozen generators/records
├── data/
│   ├── database/lineara_full.db
│   └── analysis/            # outputs + the audit scripts that check them
├── languages/               # per-script configs; linear-b is the blind sandbox
├── tools/                   # bootstrap.sh, rsi_loop.sh, rsi_overseer.sh, new_language.py
└── docs/                    # TEI ODD, JSON-LD, schema
```

## For agents

See [`AGENTS.md`](AGENTS.md) for conventions and data access, and
[`EXPERIMENT_PROTOCOL.md`](EXPERIMENT_PROTOCOL.md) §8 for the code-lifecycle rules this audit
produced. `CODE_AUDIT.md` §8 lists the open items in priority order.
