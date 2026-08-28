# Cypro-Minoan — Phase 2 (in-monorepo proof)

**Status:** scaffold + synthetic placeholder corpus (pipeline validation). Real Ferrara/Perna corpus pending.

- **Config:** `config.yaml` — 20 lines, only per-language diff (plan §3.2)
- **Mapping:** `mapping.csv` — 89 rows `CM 001`→`CM 089` → `U+12F90` block (Unicode 16, 2024). Validated via `unicode validate --language cypro-minoan`.
- **Corpus:** `data/raw/cm.json` — **19 inscriptions / 252 signs / 53 unique** — synthetic placeholder generated from HIGH-confidence `LA→CM→CG` triangular signs (`CM 001, 002, 005, 008, 010, 012…`) + random fill to exercise positional/ngram code paths. **Not the Ferrara 2024 corpus** — honestly marks pipeline-transfer proof, not decipherment.
- **DB:** `data/database/cm.db` — via `pipeline/ingest.py --language cypro-minoan` (reuses `ingest_lineara` parser + `PERIOD_MAP`/`SUPPORT_MAP` from `config.yaml`).

## Source to replace with real data

Ferrara/Perna 2021 *Cypro-Minoan* + 2024 CRIS dump (`~250 objects / <4k signs`):

- Request `https://cris.unibo.it/handle/11585/962437` (CSV/JSON)
- Fallback: Olivier 2007 *Édition holistique* + Unicode 16 chart `U+12F90`
- When dump arrives: drop `cm.json` (SigLA-style `list-of-[id,data]` with `site`, `context: "LC I"` etc., `support: "Tablet"|"Cylinder"|"Ball"`, `words: ["𒾐𒾑", "|", "𒾒"]`, `parsedInscription`) into `data/raw/cm.json` and re-run:

```bash
uv run python -m pipeline.cli unicode validate --language cypro-minoan
uv run python -m pipeline.ingest --language cypro-minoan
uv run python -m pipeline.cli db stats languages/cypro-minoan/data/database/cm.db
uv run python pipeline/positional_analysis.py --language cypro-minoan
uv run python pipeline/ngram_analysis.py --language cypro-minoan
uv run python pipeline/ventris/complete.py --language cypro-minoan oracle_test
# expected oracle: 0.0× chance < 1.5× threshold (no signal on tiny corpus; linear-a baseline 0.6×)
```

Outputs go to `data/analysis/cypro-minoan/{positional,ngram,ventris}`.

## What unlocks Linear A

If CM breaks (bilingual / Eteocypriot chain), `data/analysis/comparative/la_cm_shared_phonetic_grid.csv` HIGH chain (30 signs: `AB 08→a`, `AB 28→i`…) gives 30 LA values free; re-run `phonetic_grid_refinement.py` → `expanded_grid_purged.csv 69→100`.

## Honest ceiling

`ventris_report.md` for CM is intentionally `0.0× lift` — no CONFIRMED grid, no gradient. Same as linear-a `0.6×` negative: small corpus cannot decipher itself. See `MULTI_LANGUAGE_DECYPHR_PLAN.md §9`.
