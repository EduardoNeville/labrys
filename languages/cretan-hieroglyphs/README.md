# Cretan Hieroglyphs — Phase 3b (CHIC, PUA)

**Status:** scaffold + synthetic placeholder (pipeline validation). Real CHIC corpus pending.

- **Config:** `config.yaml` — 20 lines, `sign_system: hieroglyphic`, `period_range: 2100–1700 BCE`
- **Mapping:** `mapping.csv` — **96 rows** `CHIC 001`→`096` → `U+E000` PUA block (not Unicode-encoded; PUA-private until encoded, per plan §9). Validated via `unicode validate --language cretan-hieroglyphs` → 80 syll +16 logo.
- **Corpus:** `data/raw/chic.json` — **19 inscriptions / 186 signs / 49 unique** — synthetic placeholder generated from CHIC inventory (~100 types) with sites Knossos/Malia/Phaistos/Zakros/Petras, periods EM III→MM III, supports Seal/Tablet/Bar/Vessel/Nodule, plus CHIC 010+015 recurring formula. **Not Olivier/Godart CHIC** — honest pipeline-transfer proof.
- **DB:** `data/database/chic.db` — `19 / 186 / 49 / 8 sites / 4 periods`

## Source to replace

Olivier/Godart `CHIC` + Ferrara 2023 `OJoA` seal inventory (`~350 texts / ~100 types`):

- Request `https://cris.unibo.it` CHIC JSON; seals via `CMS` / `Ferrara 2023 OJoA`
- Drop `chic.json` (SigLA-style `list-of-[id,data]` with PUA characters ``=`U+E000`, `context: "MM II"`, `support: "Seal"`, `words: ["", "|", ""]`) into `data/raw/chic.json` and re-run:

```bash
uv run python -m pipeline.cli unicode validate --language cretan-hieroglyphs
uv run python -m pipeline.ingest --language cretan-hieroglyphs
uv run python pipeline/positional_analysis.py --language cretan-hieroglyphs # 45 signs, 13 profiles
uv run python pipeline/ngram_analysis.py --language cretan-hieroglyphs
uv run python pipeline/ventris/complete.py --language cretan-hieroglyphs oracle_test # 0.0×
```

Outputs: `data/analysis/cretan-hieroglyphs/{positional,ngram,ventris}`.

## What unlocks Linear A

Immediate predecessor on Crete 2100–1700 BCE, ~10–15 shared signs with LA, likely same language. Proves continuity; shared logograms (`*180` hide, `GRA` etc. on `KN Zg 57`) give semantic anchors; test `i-ri=barley` at higher N via `commodity_alignment.py`.

## Honest ceiling

PUA-private validation only; true corpus tiny, oracle flat (0.0×) — same wall as LA. See `MULTI_LANGUAGE_DECYPHR_PLAN.md §9`.
