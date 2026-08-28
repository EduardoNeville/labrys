# {{name}} — Phase 5 template

Scaffolded via `tools/new_language.py --id {{id}}`.

- `config.yaml` — 15 lines, only per-language diff
- `mapping.csv` — replace EXAMPLE rows with real sign inventory (header: bennettId,unicode,character,transliteration,signType)
- `data/raw/corpus.json` — SigLA-style list-of-pairs `["ID", {"site":..., "context":..., "support":..., "words":["..."], "parsedInscription":...}]` (see `languages/linear-a/data/raw/sigla/inscriptions.json` for shape)
- `data/database/corpus.db` — ignored, built via `ingest --language {{id}}`

Validate:
```bash
uv run python -m pipeline.cli unicode validate --language {{id}}
uv run python -m pipeline.ingest --language {{id}}
uv run python -m pipeline.cli db stats languages/{{id}}/data/database/corpus.db
```

Replace `mapping.csv` rows, drop real `corpus.json`, re-run. No pipeline code change needed — `List[SignInstance]` reuse.
