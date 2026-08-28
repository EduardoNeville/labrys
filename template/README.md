# labrys-template — Phase 5 (monorepo → N repos)

This `template/` is the source for `tools/new_language.py`.

- `template/language/` — per-language stub (config.yaml, mapping.csv, README.md, data/raw/.gitkeep)
- No `cookiecutter`/`copier` dependency — `tools/new_language.py` is a few stdlib lines (ponytail: one file > a framework).

When a language beats `oracle >1.5×` and warrants a standalone repo/paper, copy via:
```bash
uv run python tools/new_language.py --id cypro-minoan --name "Cypro-Minoan" --sign-system syllabary
git init languages/cypro-minoan && git push ...
```
Until then, stay monorepo — avoids `5× BENNETT_TO_UNICODE drift` (§5).
