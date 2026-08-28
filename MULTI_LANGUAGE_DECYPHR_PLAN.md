# Multi-Language Decyphr Plan — One Pipeline, N Undeciphered Scripts

**Date:** 2026-08-20  
**Context:** `labrys/` — Linear A decipherment pipeline (11 phases, 1,719 inscriptions, 11,018 signs, ~69 real phonetic values). Oracle `0.6× chance` proves corpus-alone has no gradient. Unlock is external — a deciphered sister script.  
**Goal:** Generate N repositories (one per undeciphered language), reuse the same pipeline to attack each, and let a break in any one unlock the others.

---

## 1. Core Insight

`labrys/pipeline/` is 80% language-agnostic.

- **Generic (21/26 modules):** `models.py`, `database.py`, `positional_analysis.py`, `word_segmentation.py`, `ngram_analysis.py`, `network_analysis.py`, `morphology_scan.py`, `swadesh_search.py`, `wals_analysis.py`, `cooccurrence.py`, etc. — all operate on `List[SignInstance]`.
- **Linear-A-specific (3 modules):** `unicode_utils.py` (`BENNETT_TO_UNICODE` 225 entries), `linear_b_mapping.py`, `cypro_minoan_bridge.py`.

Copying `labrys` N times = N copies of the 144-mapping bug just fixed (`U+10655 A301` was `AB 85`). Fix once, reuse N times.

**Decision: monorepo with N configs first, split to N repos only when a language warrants a paper/visibility.**

```
language-decyphr/                  # current root
├── labrys/                        # becomes languages/linear-a (alias; no move yet)
│   ├── pipeline/                  # shared after extraction
│   └── data/
│       ├── raw/sigla/inscriptions.json  # 1,719 entries — canonical
│       ├── raw/sigla/supplement.json    # 1,713 tabulated
│       └── database/lineara_full.db
├── languages/                     # NEW — one config per language
│   ├── linear-a/config.yaml       # extracted from labrys
│   ├── cypro-minoan/config.yaml   # PRIORITY 1
│   ├── cretan-hieroglyphs/config.yaml  # PRIORITY 2
│   ├── eteocretan/config.yaml     # PRIORITY 3
│   └── eteocypriot/config.yaml
└── pipeline/                      # extracted shared (or keep in labrys/pipeline + symlink)
```

`ponytail: single monorepo with config-driven mapping; split to N standalone repos via template only when a language hits oracle >1.5× chance or merits publication — avoids 5× maintenance until signal exists.`

---

## 2. Languages to Attack — Ranked by Leverage on Linear A

Only Aegean-chain scripts transfer phonetic values to Linear A. Indus/Proto-Elamite/Linear Elamite are unrelated — solving them does not help Crete.

| Pri | Language | Script | Corpus | Unicode | Why it unlocks Linear A | Status 2024-25 | Repo ID |
|-----|----------|--------|--------|---------|------------------------|----------------|---------|
| **0** | **Minoan** | **Linear A** | **1,719 texts / 11,018 signs** | **U+10600–U+1077F** | baseline | **Undeciphered** — `labrys` 11 phases exhausted | `linear-a` |
| **1** | **Cypro-Minoan** | CM 0/1/2 syllabary | ~250 objects / <4k signs | U+12F90 (Unicode 16, 2024) | Direct daughter of LA. `labrys` already has `la_cm_shared_phonetic_grid.csv` with HIGH-confidence chain `LA→CM→Cypriot Syllabary→Greek` for ~30 signs (`AB 08 a`, `AB 28 i`, etc.). Decipher CM = 30 LA values free. | **Undeciphered** — *Computational Linguistics* 2024 review: too small, unknown language | `cypro-minoan` |
| **2** | **Cretan Hieroglyphs** | CHIC seals/tablets | ~350 texts / ~100 sign types | PUA (not encoded) | Immediate predecessor on Crete 2100–1700 BCE, ~10–15 signs shared with LA, likely same language. Proves continuity and gives pre-LA phonology. | **Undeciphered** — Ferrara 2023 *OJoA*, `cris.unibo.it` 2024: inventory vs non-writing still debated | `cretan-hieroglyphs` |
| **3** | **Eteocretan** | Greek alphabet | **7 texts / 55 tokens** | — | Only *alphabetic* Rosetta. If proven descendant of Minoan (Praisos/Dreros 700–300 BCE), Greek letters give phonetics directly (`onadesimet` 3×, `eteocretan_report.md`). | **Undeciphered language** — Oxford Classical Dict: "often hypothesized, not established" | `eteocretan` |
| **4** | **Eteocypriot** | Cypriot syllabary + Greek alphabet | ~20 texts (Amathus) | U+10800 | If Eteocypriot == language of Cypro-Minoan, then `Eteocypriot → CM → LA` chain. | **Undeciphered** — Cambridge *syllabotactic analysis of Eteocypriot and LA against CM* no consensus | `eteocypriot` |
| — | Phaistos Disk, Arkalochori Axe | unique | 1 each | — | Singletons — not pipeline-scale, but method test | Undeciphered | — (in `linear-a` extras) |

### Dependency Graph (what unlocks what)

```
Cretan Hieroglyphs (2100 BCE)
        ↓  (same language hypothesized)
     Linear A  (1800–1450 BCE)  ←←← YOU ARE HERE (labrys)
        ↓  (script adapted)
   Cypro-Minoan (1550–1050 BCE)
        ↓                 ↓
  Cypriot Syllabary   Eteocypriot (600 BCE)
  (deciphered, Greek)   (undeciphered, ~20 texts)
        ↑                 ↓ (if same language)
        └──── Eteocretan (alphabetic, 7 texts)
              (if descendant of Minoan → phonetics)
```

**Any single decipherment propagates:** `CHIC → LA`, `CM → LA`, `Eteocretan → LA`, `Eteocypriot → CM → LA`.

### What `labrys` already tested and ruled out as *origin* families

`data/analysis/linguistic/candidate_ranking.csv` — 6 deciphered families tested via Swadesh-100, WALS, loanwords, toponyms. **All `p > 0.33`, all `INCONCLUSIVE`:**

- Anatolian IE (Luwian/Hittite) — score 8, `p=0.948`
- Hurro-Urartian — score 8, `p=0.335`
- Tyrsenian (Etruscan) — score 7, 62.5% WALS best but `0/18` Swadesh `p=1.0`
- Pre-Greek Substrate — 6, `p=1.0`
- Semitic / Afroasiatic — 5, WEAK/rejected

`phase_summary_7_9.md`: Eteocretan `0 LA matches`, Anatolian `0 ≥3-site hits`, commodity `i-ri=barley? freq=1`. **Minoan = isolate until Aegean sister breaks.**

---

## 3. Reuse Plan — What to Generalize

### 3.1 Three files become config-driven

| File | Current | Generalized |
|------|---------|-------------|
| `pipeline/unicode_utils.py` | `BENNETT_TO_UNICODE: list[tuple]` hardcoded 225 | `load_mapping(languages/<lang>/mapping.csv) -> dict` — CSV is source of truth, Python is loader + `validate_mapping()` |
| `ingest_lineara.py` | `PERIOD_MAP`, `SUPPORT_MAP`, JSON list-of-[id,data] specific to `lineara.xyz` | `pipeline/ingest.py --language <id>` — maps via `config.yaml` (`period_map`, `support_map`, `json_format`, `id_field`) |
| `pipeline/cypro_minoan_bridge.py` | hardcoded LA↔CM↔CG | `pipeline/comparative_bridge.py --source <a> --target <b> --via <c>` — same triangular logic, any chain |

All other modules stay untouched — they already take `List[Inscription]` / `List[SignInstance]`.

### 3.2 Per-language config (20 lines)

`languages/cypro-minoan/config.yaml` — the *only* per-language diff:

```yaml
id: cypro-minoan
name: Cypro-Minoan
family: undeciphered-aegean
sign_system: syllabary
period_range: "1550–1050 BCE"
mapping: mapping.csv              # cm_sign → unicode U+12F90, from Ferrara 2024
corpus:
  raw: data/raw/cm.json           # Ferrara/Perna 2021/2024 export
  format: sigla-json              # reuse ingest.py
  id_field: name
comparative:
  - source: linear-a
    via: cypriot-syllabary        # triangular chain
    grid: data/analysis/comparative/la_cm_shared_phonetic_grid.csv
ingest:
  period_map: { "LC I": "LC I", "LC II": "LC II" }
  support_map: { "Tablet": "tablet", "Cylinder": "cylinder" }
pipeline:
  db: data/database/cm.db
  phases: [positional, ngram, network, morphology, swadesh, comparative, ventris]
oracle:
  # must beat labrys baseline 0.6× chance
  threshold: 1.5
```

`languages/eteocretan/config.yaml` is even smaller — `sign_system: alphabet`, `mapping: null` (Greek letters are phonetic directly), `comparative: [linear-a]`.

### 3.3 Database — reuse `models.py` 7-tier schema

No schema change. `Inscription.gorilaId` → generic `id`, `findspot.site`, `signs[].bennettId` → `signs[].signId`. All 12 tables (`inscriptions`, `signs`, `sign_semantics`, `findspots`, etc.) reused. `LinearADatabase` → `CorpusDatabase` (alias).

### 3.4 Evaluation — same gate for every language

`pipeline/ventris/complete.py:oracle_test()` is the **only** gate that matters. For each language:

1. Hide 20 CONFIRMED signs, greedy restore via scorer (Kober + entropy + prefix + anchor words).
2. Recovery must be `>1.5× chance` (labrys was `0.6×` — scorer has no signal).
3. If flat, no optimizer (beam, annealing, Optuna) will help — objective has no gradient. Report negative honestly, as `ventris_report.md` does.

Also reuse: `validate_mapping()`, `db stats`, `demo.py` smoke test.

---

## 4. Data Acquisition — Per Language

| Language | Source corpus | How to fetch | New mapping entries | Est. ingest effort |
|----------|---------------|--------------|---------------------|-------------------|
| **linear-a** | `data/raw/sigla/inscriptions.json` (1,719) + `supplement.json` (1,713) | already in repo — update from `sigla.phis.me` live API or `lineara.xyz` snapshot | 0 (after 144-fix) | done |
| **+ scepter** | `KN Zg 57` (~119 signs) + `KN Zg 58` (handle, 6 fractions) — Kanta et al. *Ariadne* 2024 | Wait for `Kanta (ed.) forthcoming: Anetaki II` continuous transliteration. Currently stubs `KNZg57a/b` (17+11 placeholder signs) + empty `KNZg58`. See §6. | 2–3 (`*652`, `*653`, `*418+L2` ligatures → `BENNETT_TO_UNICODE` U+1076B etc.) | 1 PR when edition prints |
| **cypro-minoan** | Ferrara/Perna 2021 *Cypro-Minoan* + 2024 *Cris* corpus (`~250` objects) | Request `cris.unibo.it/handle/11585/962437` CSV/JSON; fallback: `Olivier 2007` + `Unicode U+12F90` code chart | ~80–90 (`CM 001`–`CM 090` → U+12F90 block) | 2 days |
| **cretan-hieroglyphs** | Olivier/Godart `CHIC` + Ferrara 2023 seal inventory (`~350` texts) | `CHIC` JSON via `cris.unibo.it`; seals via `CMS` / `Ferrara 2023 OJoA` | ~96 (CHIC 001–096, PUA until encoded) | 2 days |
| **eteocretan** | Duhoux 7 texts (Praisos, Dreros; already in `pipeline/eteocretan/corpus.csv`) | promote `pipeline/eteocretan/corpus.csv` → `languages/eteocretan/data/raw/` | 0 (Greek alphabet) | 1 hour |
| **eteocypriot** | Egetmeyer 2010 *Le dialecte grec ancien de Chypre* + Cambridge appendix (~20 texts) | `Egetmeyer` PDF table → CSV | 0 (Cypriot syllabary U+10800 already in `la_cm_shared_phonetic_grid.csv`) | 1 day |

`SigLA` live sync gap (2026-06-26): `KH 101, KH 103–105, KN 54, THE 7–11` (~10 vas/sealings, <30 signs) missing from `lineara.xyz` snapshot — pull `sigla.phis.me` API on next ingest.

---

## 5. Repository Generation — How to Create N Repos

### Option A — Monorepo (recommended now)

```bash
# 1. Extract mapping (1 PR, no behavior change)
uv run python -c "from pipeline.unicode_utils import write_mapping_csv; write_mapping_csv('languages/linear-a/mapping.csv')"
# pipeline/unicode_utils.py now loads languages/linear-a/mapping.csv

# 2. Add second language as proof
mkdir -p languages/cypro-minoan/data/raw
# fetch Ferrara CM CSV → languages/cypro-minoan/mapping.csv + data/raw/cm.json
uv run python pipeline/ingest.py --language cypro-minoan
uv run python -m pipeline.cli db stats languages/cypro-minoan/data/database/cm.db
uv run python pipeline/positional_analysis.py --language cypro-minoan
uv run python pipeline/ventris/complete.py --language cypro-minoan oracle_test
```

### Option B — Template for standalone repos (when splitting)

```bash
# generate template once
cookiecutter gh:EduardoNeville/labrys-template --output-dir /tmp/test-lang
# or minimal:
cargo install cargo-generate  # or use copier
copier copy gh:EduardoNeville/labrys-template languages/cypro-minoan --trust
```

Template contains: `pipeline/` (shared), `languages/<lang>/config.yaml`, `mapping.csv` stub, `data/raw/.gitkeep`, `pyproject.toml` (same `uv` deps), `demo.py`, `AGENTS.md`. Each generated repo is pushable as `github.com/EduardoNeville/cypro-minoan` etc. — but only do this after monorepo proof beats `oracle >1.0×`.

**Do not generate 5 repos on day 1.** Cost: 5× CI, 5× `BENNETT_TO_UNICODE` drift, 5× `uv.lock` conflicts. Generate 1 extra (`cypro-minoan`) in monorepo, validate pipeline transfers, then template-clone the rest in <30 min each.

---

## 6. Knossos Anetaki Scepter — Inclusion Recipe

Published `Kanta/Nakassis/Palaima/Perna, Ariadne 2024` (17pp, `ejournals.lib.uoc.gr/Ariadne/article/download/1841/1751/3474`). Not yet continuously transliterated — authors defer to `Anetaki II`.

Current stubs in `labrys`:

```json
["KNZg57a", {"parsedInscription":"𐜪𐜪𐜫…","words":["𐜪",…,"𐝫"],"support":"ivory object"}] // 17 DB signs
["KNZg57b", {"parsedInscription":"𐜪𐜪𐜫…","words":["𐘚","𐙂",…]}] // 11 signs
["KNZg58",  {"parsedInscription":"","words":[""]}] // 0 — empty
```

When edition drops:

```python
# 1. Extend mapping if new signs appear (ponytail: 3 lines, add when codepoints known)
# languages/linear-a/mapping.csv: add *652 → U+1076B, *653 → U+1076C, etc.

# 2. Add to data/raw/sigla/inscriptions.json as single entry (ring) + handle:
["KNZg57", {
  "site":"Knossos","findspot":"Anetaki plot, Room 1 Ivory Repository",
  "context":"LM IB","support":"ivory object","material":"ivory",
  "parsedInscription":"<FaceA metopes | FaceB | FaceC | FaceD, '\\n' per face>",
  "transcription":"<same, Unicode Aegean>",
  "words":["<per metope>", "𐝫"], # 𐝫 = metope divider
  "images":["images/KNZg57-Inscription.jpg"]
}]

# 3. Re-ingest
python ingest_lineara.py
uv run python -m pipeline.cli db stats data/database/lineara_full.db
uv run python -m pipeline.cli unicode validate
uv run python demo.py
```

Impact: `+119 signs` (+1% corpus), first cult non-accounting long text, only LA+Hieroglyphic hybrid, `KN Zg 58` 6-fraction sequence tests `data/analysis/logograms/fraction_values_proposed.csv` (Corazza et al. 2021). Adds morphology/positional on ritual genre; still no bilingual.

---

## 7. Roadmap — Phased, Smallest Diff First

| Phase | What | In `labrys/` | Done when |
|-------|------|-------------|-----------|
| **0 — Now** | No-code prep | This plan file | this commit |
| **1 — Extract (1 day)** | `unicode_utils.py` → CSV-driven, `ingest_lineara.py` → `ingest.py --language` | `languages/linear-a/mapping.csv`, `languages/linear-a/config.yaml`, alias `labrys = languages/linear-a` | `uv run python demo.py` + `unicode validate` green, DB `1,719` rows |
| **2 — CM proof (2–3 days)** | Add `cypro-minoan` in-monorepo, run full pipeline, oracle | `languages/cypro-minoan/data/database/cm.db`, `data/analysis/cypro-minoan/ventris_report.md` | `oracle_test` reports `X× chance`; if `0.6×` again → confirms small-corpus wall, honestly |
| **3 — CHIC + Eteocretan (1 week)** | Promote `eteocretan/corpus.csv`, ingest `CHIC` | `languages/cretan-hieroglyphs/`, `languages/eteocretan/` | each has `db stats` + `positional_profiles.csv` |
| **4 — Eteocypriot + bridges (1 week)** | `comparative_bridge.py` triangular `LA→CM→CG` + `CM→Eteocypriot` | `data/analysis/comparative/la_cm_eteocypriot_grid.csv` | updated `MASTER_SYNTHESIS.md §14` |
| **5 — Template (½ day)** | `labrys-template` cookiecutter from monorepo | `github.com/EduardoNeville/labrys-template` | `cookiecutter` generates new lang in <30 min |
| **6 — Split if warranted** | Standalone repos per language | `cypro-minoan`, `cretan-hieroglyphs`, etc. | only if a language beats oracle or gets dedicated funding/paper |

**Commands for phase 1 (copy-paste):**

```bash
# verify current state
uv sync; uv run python demo.py
uv run python -m pipeline.cli db stats data/database/lineara_full.db
# expected: 1719 inscriptions, 11018 signs, 312 unique, 62 sites

# after extraction, per-language (phase 2+)
uv run python pipeline/ingest.py --language cypro-minoan --sync
uv run python -m pipeline.cli db stats languages/cypro-minoan/data/database/cm.db
uv run python pipeline/positional_analysis.py --language cypro-minoan
uv run python pipeline/ngram_analysis.py --language cypro-minoan
uv run python pipeline/ventris/complete.py --language cypro-minoan oracle_test
```

---

## 8. What Deciphering One Unlocks — Concrete Mechanics

| If this breaks | How it unlocks others | Pipeline action |
|----------------|-----------------------|-----------------|
| **Cypro-Minoan** deciphered (e.g., via Eteocypriot or new bilingual) | 30–40 LA phonetic values via `la_cm_shared_phonetic_grid.csv` HIGH chain; `refined_phonetic_grid.csv` 11 UNCERTAIN become CONFIRMED (`AB 41 si` already 240 occ candidate) | Re-run `phonetic_grid_refinement.py` with CM as CONFIRMED, regenerate `expanded_grid_purged.csv` (69→100 real), re-run `morphology_scan.py` with true phonetics |
| **Cretan Hieroglyphs** deciphered | Pre-LA language proven same as Minoan; shared logograms (`*180` hide, `GRA/FAR/OLIV` already on `KN Zg 57`) give semantic anchors | Ingest CHIC, run `commodity_alignment.py` LA↔CHIC, test `i-ri=barley` at higher N |
| **Eteocretan** proven Minoan descendant | Greek alphabet = phonetics: map `onadesimet` affixes (`-de-`, `-si-`, `-met` agglutinative) onto LA suffixes (`-RO`, `A-` prefix per `field_state_2025.md`) | Run `pipeline/eteocretan/` at scale on new bilingual find (1 bilingual `PR 2` today — need 1 more with shared content) |
| **Linear A** itself breaks (e.g., via scepter `KN Zg 58` fraction sequence or new `Hashimoto 2025` toponym) | Unlocks CM and CHIC backwards via same triangular grids | Update `languages/cypro-minoan/mapping.csv` from LA side, re-run `comparison_results.csv` |

---

## 9. Risks and Honest Ceilings

| Risk | Mitigation |
|------|------------|
| All corpora are tiny (`LA 11k`, `CM <4k`, `Eteocretan 55` tokens) → every oracle flat | Honest negative is a result. `ventris_report.md` spread `0.0046`, `0 signs ≥60%` consensus — publish as mapped boundaries, not failure. |
| `Anetaki II` / Ferrara CM corpus not yet public | Stub + wait; pipeline ready to ingest in 1 PR. No photo-guess transcription. |
| CHIC PUA signs not Unicode-standard | Store as `CHIC 001` IDs, keep `mapping.csv` PUA-private, validate via `validate_mapping()` not via Unicode block. |
| N repos drift apart | Keep `pipeline/` as git submodule or `uv` workspace; CI pins `uv.lock`. Template is generated, not hand-copied. |
| New mapping bugs (like 144 just fixed) | `unicode validate` in CI for every `mapping.csv`; three-way check `source → Unicode standard → corpus DB` per `corpus_correction.md`. |

---

## 10. References — Where to Find Things in This Repo

| What | File |
|------|------|
| Corpus canonical | `data/raw/sigla/inscriptions.json` (1,719), `supplement.json` (1,713) |
| DB | `data/database/lineara_full.db` (3.6 MB) |
| Honest grid (use this) | `data/analysis/bootstrapping/expanded_grid_purged.csv` (58 CONFIRMED + 11 UNCERTAIN = 69 real) — not `expanded_grid.csv` (138 with 69 phantoms) |
| CM bridge | `data/analysis/comparative/la_cm_shared_phonetic_grid.csv`, `pipeline/cypro_minoan_bridge.py` |
| LB mapping | `data/analysis/comparative/la_lb_mapping.csv`, `pipeline/linear_b_mapping.py` |
| Phases 1–3 synthesis | `data/analysis/synthesis/phase_summary_1_3.md` |
| Phases 7–9 | `data/analysis/synthesis/phase_summary_7_9.md` |
| Ventris oracle (gate) | `pipeline/ventris/complete.py:oracle_test()`, `data/analysis/ventris/ventris_report.md`, `sign_consensus.csv` |
| Corrections | `data/analysis/ventris/corpus_correction.md`, `b1b2_phantom_finding.md`, `corrected_rerun_results.md` |
| Field state | `data/analysis/ventris/field_state_2025.md` |
| Master honesty | `data/analysis/synthesis/MASTER_SYNTHESIS.md §14`, `verification_audit.md` |
| Scepter paper | `ejournals.lib.uoc.gr/Ariadne/article/download/1841/1751/3474` (17pp, ring ~119 signs, handle 6 fractions) |
| Dev conventions | `AGENTS.md`, `README.md`, `docs/unified-linear-a-schema.md` |

---

*One pipeline, N configs, honest oracle. The shortest path to a decipherment is not N pipelines — it is N corpora through the same honest gate, waiting for the one that finally has signal.*

