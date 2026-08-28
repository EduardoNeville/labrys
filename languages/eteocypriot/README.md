# Eteocypriot — Phase 4 (Amathus, ~20 texts)

**Status:** scaffold + synthetic placeholder (Egetmeyer 2010 hand CSV pending). Cypriot syllabary + Greek alphabet, undeciphered language.

- **Config:** `config.yaml` — 20 lines, `sign_system: syllabary`, `mapping: null` (Cypriot syllabary U+10800 deciphered as Greek phonetics; values known, language unknown)
- **Mapping:** none — `U+10800` already in `la_cm_shared_phonetic_grid.csv`; no new rows (plan §4)
- **Corpus:** `data/raw/eteocypriot.json` — **20 inscriptions / 649 letters / 39 unique (latin + 𐠀-U+10800)** — 6 real (EC1/ICS 196 bilingual 11w + EC2/ICS 195 13w Onasagoras/Purwos + EC3 14w + EC4 18w + EC5 12w + EC14 coin `pu-ru-wo-so`) from Masson 1983 ICS + cyprominoica.wordpress.com (EC1-5,14) + 14 synthetic placeholders (ICS 183,190-194,196a-e,295,388 etc. awaiting Egetmeyer Tome II full hand transcription).
- **DB:** `data/database/eteocypriot.db` — `20 / 660 / 40 / 20 sites`

## Real data now included (partial, cyprominoica EC1-5,14)

- **EC1/ICS 196 bilingual** (`a-na ma-to-ri u-mi-e-sa-i…` 11w) — Sittig 1914, real
- **EC2/ICS 195** (`mi-ta-ra-wa-no o-na-sa-ko-ra-no-ti…` 13w Onasagoras/Purwos) — Masson 1983 ICS 195, real
- **EC3** 14w `tu a-li-ra-ni…` — Masson, real
- **EC4** 18w `a-na ta-si su-sa…` — real
- **EC5** 12w `wi-ti-le-ra-nu…` — real
- **EC14/ICS 198** coin `pu-ru-wo-so` (Purwos, 390 BC) — real

Remaining 14 (ICS 183,190-194,196a-e,295,388 etc. per bottom list, Steele <20) are still synthetic placeholders — replace with Egetmeyer Tome II Répertoire hand CSV when available.

## Source to replace (remaining)

Egetmeyer 2010 Tome II *Répertoire* + Cambridge appendix: PDF table → CSV hand-transcribe `object_id, site, period, support, inscription as U+10800 or Greek, word breaks` into `data/raw/eteocypriot.json` SigLA-style list-of-pairs and re-run:

```bash
uv run python -m pipeline.ingest --language eteocypriot
uv run python pipeline/positional_analysis.py --language eteocypriot
uv run python pipeline/comparative_bridge.py --source cypro-minoan --target eteocypriot --via cypriot-syllabary
```

## What unlocks

If `Eteocypriot == language of Cypro-Minoan` (hypothesis Cambridge *syllabotactic analysis*), then `Eteocypriot (U+10800 phonetics) → CM (U+12F90) → LA`. 30 HIGH `LA→CM→CG` values become 30 LA values free.

## Honest ceiling

20 texts, bilingual `Amathus 1-2` only partially Greek — oracle `0.0×` expected, same wall.
