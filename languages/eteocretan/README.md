# Eteocretan — Phase 3a (alphabet, 7 texts)

**Status:** scaffold + promoted Duhoux corpus (pipeline validation). Greek alphabet, mapping `null`.

- **Config:** `config.yaml` — 18 lines, `sign_system: alphabet`, `mapping: null`
- **Mapping:** none — Greek letters are phonetic directly (`onadesimet` affixes → LA suffixes)
- **Corpus:** `data/raw/eteocretan.json` — **7 inscriptions / 221 letters / 16 unique** — promoted from `pipeline/eteocretan/corpus.py` (Duhoux 1982). `DR 1` (24w), `DR 2` (11w), `PR 1` (13w), `PR 2 bilingual` (6w, +6w Greek `anethēkan to Di` dedication), `PR 3/4/5` fragments. Synthetic JSON is SigLA-style list-of-pairs for reuse of `ingest.py`; each Latin letter = a sign with `signType: syllabogram` so generic `List[SignInstance]` code reuses unchanged (ponytail: map alphabet to syllabogram).
- **DB:** `data/database/eteocretan.db` — `7 / 221 / 16 / 2 sites (Dreros, Praisos) / 2 periods (Archaic, Classical)`
- **Provenance:** Duhoux 1982, `pipeline/eteocretan/corpus.py::ALL_INSCRIPTIONS` (422 chars across 7 ins). For real data pull: `python -c "from pipeline.eteocretan.corpus import build_corpus; build_corpus()"` → `data/analysis/eteocretan/corpus.csv`.

## Run

```bash
uv run python -m pipeline.ingest --language eteocretan
uv run python -m pipeline.cli db stats languages/eteocretan/data/database/eteocretan.db
uv run python pipeline/positional_analysis.py --language eteocretan   # 16 signs, 14 profiles (min 5)
uv run python pipeline/ngram_analysis.py --language eteocretan        # 221 tokens, 27 MI rows
uv run python pipeline/ventris/complete.py --language eteocretan oracle_test # 0.0× <1.5× — no signal (55 tokens < gradient)
```

Outputs: `data/analysis/eteocretan/{positional,ngram,ventris}`.

## What unlocks Linear A

If Eteocretan == Minoan descendant proven (Praisos/Dreros 700–300 BCE), Greek alphabet gives phonetics directly: map `onadesimet` affixes (`-de-`, `-si-`, `-met` agglutinative) onto LA suffixes (`-RO`, `A-` prefix) per `field_state_2025.md`. Needs 1 more bilingual with shared content beyond `PR 2`.

## Honest ceiling

Tiny (55 tokens) → oracle flat by design, same as LA 0.6× negative. Not a decipherment, just pipeline-transfer proof for alphabet branch.
