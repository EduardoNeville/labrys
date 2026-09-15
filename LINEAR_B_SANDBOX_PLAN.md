# Linear B Sandbox — Blind Decipherment Harness

**Date:** 2026-09-15
**Status:** Step 0 complete (corpus on disk). Steps 1–6 in progress.
**Related:** `MULTI_LANGUAGE_DECYPHR_PLAN.md` (monorepo + per-language configs), `data/analysis/ventris/verification_audit.md` (retraction culture), `pipeline/ventris/complete.py:oracle_test()`

---

## 1. Why this exists

The reason an LLM produced a credible Navier–Stokes proof is not that the LLM was smart. It is
that the output was **machine-checkable** — Lean, plus the PDE itself. Search is cheap; the
verifier is the scarce resource. Every "AI did mathematics" result has the same shape:
AlphaEvolve (numeric evaluators), Erdős problems (Lean), the proof claim itself (disputed, but
arguable *only because* a formal artifact exists).

Linear A has no verifier, and this repo has already proved it empirically:

```
pipeline/ventris/complete.py:oracle_test()
  recovery 0.6x chance   (4 runs, independent seeds)
```

That number is not "our model is too small." It says the objective function contains no
information about the answer. Scaling the search — bigger transformer, beam search, Optuna,
an LLM — scales a multiplier of zero.

**So the transferable move is not "use an LLM on Linear A." It is: manufacture a verifier.**

For a decipherment problem, manufacturing a verifier means building a sandbox where the answer
is already known. Linear B is that sandbox:

| Property | Linear A | Linear B |
|---|---|---|
| Relation | ancestor | descendant |
| Script family | Aegean syllabary | Aegean syllabary |
| Inventory | ~69 real signs | ~87 signs |
| Genre | administrative tablets | administrative tablets |
| Condition | fragmentary, damaged | fragmentary, damaged |
| **Phonetic values** | **~44 of 138, all hypotheses** | **known, from Ventris 1952** |

Withhold the values and Linear B is structurally the same puzzle — except it has an answer key.

### What a pass and a fail each buy

- **Pass** → a validated decipherment method, plus the first calibrated error rate anyone has
  had in this field. Every subsequent Linear A claim can be measured against it.
- **Fail** → publishable negative. "A Ventris-style pipeline holding 58 known anchors recovers a
  *deciphered* script at chance" closes a genre of unfalsifiable Linear A papers.

### What a pass does NOT buy

Linear B is the **best case**: real Greek, and its 58 anchors are facts rather than hypotheses.
A pass measures the *method's ceiling with perfect anchors*. It is an upper bound on what the
method could ever do for Linear A. Frame it that way in the writeup, or it becomes overclaim
number seven.

---

## 2. Pre-registration (committed before the run)

Written down first, in this file, so the result cannot be reinterpreted after the fact. This
repo has retracted four findings; the way to avoid a fifth is to fix the threshold now.

| Quantity | Value | Source |
|---|---|---|
| Pass threshold | `lift_over_chance > 1.5` | `MULTI_LANGUAGE_DECYPHR_PLAN.md` §3.4, `languages/linear-a/config.yaml` `oracle.threshold` |
| Trials | `8` | `ORACLE_TRIALS` |
| Hidden per trial | `20` of the CONFIRMED set | `ORACLE_HIDDEN` |
| Random baseline | mean `1/len(candidates)` per hidden sign | `oracle_test()` |
| Parser coverage gate | token coverage `> 0.95` | this file, §4 Step 1 |
| Parser inventory gate | `80 <=` unique syllabograms `<= 90` | this file, §4 Step 1 |

**Interpretation rule, fixed now:**
- `lift > 1.5` → method has signal → proceed to Cypro-Minoan (already staged).
- `0.5 < lift <= 1.5` → weak/degenerate; report as inconclusive, do not build on it.
- `lift <= 0.5` → no signal. Publish the negative, stop investing in LA-specific search.

---

## 3. Architecture — why the diff is small

Already in place, no work required:

```
pipeline/ventris/complete.py:136   VentrisGridCompleter(db_path=, expanded_grid_path=, kober_triples_path=)
pipeline/ventris/complete.py:577   oracle_test(hidden=, trials=)   # hide-N-recover, with baseline
pipeline/ventris/complete.py:947   --language / --db CLI overrides
pipeline/config.py                 languages/<id>/config.yaml loader
languages/{cypro-minoan,cretan-hieroglyphs,eteocretan,eteocypriot}/   already staged
```

Verified: the scorer is **value-blind by construction**.

```sql
-- pipeline/ventris/complete.py:253
SELECT i.id, s.sequence, s.bennett_id
FROM signs s JOIN inscriptions i ON s.inscription_id = i.id
```

No transliteration, no phonetic value. The experiment is sound before a line is written.

What is missing is the layer that turns LB *text* into sign *IDs*, because the source corpus
stores `ka-*56-(so)` — the phonetic value is baked into the token. You cannot withhold a value
you have no ID for.

---

## 4. Steps

### Step 0 — corpus on disk ✅

| | |
|---|---|
| Source | `github.com/InsiderPhD/Linear-B-Dataset` → `tablet-sets/tablets.csv` |
| Destination | `languages/linear-b/data/raw/tablets.csv` |
| Size | 7,370 tablets, 1.0 MB |
| Format | `;`-delimited, cols `identifier;location;series;inscription;original` |
| `inscription` | word-level transliteration, comma-separated words, `-`-separated signs |
| `original` | line-level transcription with logograms (`VIR MUL ROTA vest`), numbers, brackets |

**Not used:** DĀMOS (`damos.hf.uio.no`). Its own howto documents browse/word-search only —
no bulk export — so it is a reconciliation source, not the primary. LiBER (`liber.cnr.it`) as
second opinion if a coverage dispute arises.

**Check:** `wc -l` → 7,371 (7,370 rows + header). Sign inventory ~87 expected.

---

### Step 1 — transliteration → sign ID

**Files**
| Path | Role |
|---|---|
| `languages/linear-b/translit_to_signid.csv` | the table: `translit,sign_id,source,confidence` |
| `pipeline/lb_ingest.py` | parser + coverage gate + DB builder |

**Seed source:** reverse-index `data/analysis/comparative/la_lb_mapping.csv` (`lb_value` →
`bennett_id`). That file is authoritative *for this repo* and is what the Linear A comparison
already uses — no second opinion is being invented.

**Observed input shapes, and the rules they force** (derived from all 299 distinct tokens, not
guessed):

| Shape | Example | Rule |
|---|---|---|
| plain syllable | `ka-*56-(so)` | lookup seed |
| damaged reading | `[`, `]`, `ro[]`, `[[pa` | strip brackets, flag word `damaged=1` |
| uncertain reading | `(ro)`, `(wo)` | strip parens, flag sign `uncertain=1`, keep the sign |
| numbered sign | `*56`, `*82`, `*22` | `*NN` → `AB NN` (LA and LB share the numbering) |
| **subscript = distinct sign** | `ra2`, `ro2`, `a2`, `pu2`, `nwa`, `pte` | **never strip.** `ra2` ≠ `ra` |
| ligature | `(ME)+(RI)`, `(*209VAS)+(A)` | split on `+`, flag components |
| word boundary | `ro|(pa)` | split on `|` and `,` |
| line markers | `.1`, `.a` | dropped (only in `original`; defensive) |
| case variation | `KE`, `RO2`, `DA` | lowercase-normalise (verified: not ideograms) |

**Seed coverage, measured:** 104 raw `lb_value` entries, but the column is polluted with
numbers (`1`, `10`, `100`), fractions (`j (1/2?)`, `aa (4/5?)`), commodity guesses
(`[barley?]`, `[wine?]`) and placeholders (`—`, `?`). Only clean entries become syllables.

Signs marked `?` in the mapping (`ra2?`→AB 76, `ro2?`→AB 68, `nwa?`→AB 48, `pte?`→AB 62,
`pa2?`→AB 34, `du?`→AB 51, `swi?`→AB 64, `ju?`→AB 65) are accepted at lower confidence.

LB-only values with no LA cognate — the sandbox needs a *stable ID*, not a correct value, since
the value lives in the answer key:

| translit | id | occurrences | note |
|---|---|---|---|
| `qo` | `AB 32` | 18 | LB number = LA number |
| `a2` | `AB 25` | 8 | |
| `au` | `AB 85` | 6 | interesting: AB 85 is the retracted "word divider" in LA |
| `a3` | `AB 43` | 5 | |
| `pu2` | `AB 29` | 5 | |
| `ra3` | `AB 33` | 2 | |
| `dwe`, `twe` | opaque `LB dwe`, `LB twe` | 3 | LB number not confirmed → opaque ID |

Each row carries its `source` (`la_mapping`, `lb_only`, `numbered`) so a specialist can correct
any single row without touching code.

**Gate, pre-registered:**
```
token coverage  > 0.95
80 <= unique syllabograms <= 90
```
Below 0.95 → the parser is wrong, fix before running (a run on a broken corpus produces a number
indistinguishable from a finding). Above ~110 unique → logograms leaking in as syllabograms.

**Check:** `uv run python pipeline/lb_ingest.py --report-only`

---

### Step 2 — build the DB

| | |
|---|---|
| Output | `languages/linear-b/data/database/linear-b.db` |
| Shape | `inscriptions` / `signs` / `findspots` / `words`, mirroring `data/database/lineara_full.db` |
| `bennett_id` | the sign ID from Step 1 |
| `sign_type` | `syllabogram` for every resolved sign |
| `transliteration` | **NULL for every syllabogram** |
| `words` | populated from the editor's comma division (Linear B has *real* word division; Linear A's is inferred — note this asymmetry in the writeup) |

**`transliteration = NULL` is not optional.** `complete.py` will not read it, but
`morphology_scan`, `swadesh_search` and `positional_analysis` will. One of them leaking turns
this into a beautiful fake result — which is exactly how the retracted findings happened.

**Check:** `uv run python -m pipeline.cli db stats languages/linear-b/data/database/linear-b.db`

---

### Step 3 — answer key + Kober patterns

| Path | Role |
|---|---|
| `languages/linear-b/answer_key.csv` | the values. In `expanded_grid_purged.csv` shape, all rows `decision=CONFIRM` |
| `languages/linear-b/data/analysis/kober/triple_patterns.csv` | re-run `pipeline/kober/triple_detection.py` on the LB DB |
| `languages/linear-b/data/analysis/kober/positional_grid.csv` | re-run `pipeline/kober/positional_grid.py` |

The key lives in exactly one file. Nothing else in the repo may contain an LB phonetic value.

**Check:** triple count and sign coverage vs Linear A's
(`data/analysis/kober/triple_patterns.csv`).

---

### Step 4 — wire up behind the config

`languages/linear-b/config.yaml`, modelled on `languages/linear-a/config.yaml`:

```yaml
id: linear-b
name: Linear B
family: hellenic            # deciphered — ground truth, not a hypothesis
sign_system: syllabary
period_range: "1450–1150 BCE"
mapping: translit_to_signid.csv
comparative:
  - source: linear-a
    via: null
    grid: data/analysis/comparative/la_lb_mapping.csv
pipeline:
  db: languages/linear-b/data/database/linear-b.db
oracle:
  threshold: 1.5
```

**The leak guard — this one assert is the entire defence of the experiment:**

```sql
SELECT DISTINCT transliteration FROM signs WHERE sign_type = 'syllabogram';
-- must be {NULL}
```

Implemented in `pipeline/lb_ingest.py:assert_no_leak()` and run on every ingest.

---

### Step 5 — run

```bash
uv run python pipeline/ventris/complete.py --language linear-b oracle_test --trials 8
```

Conditions, each a separate recorded run:

| ID | Condition | Question it answers |
|---|---|---|
| **(a)** | LB values hidden, LB corpus as-is | does the method have signal at all, under the best possible conditions? |
| **(b)** | as (a), with Linear A's morphological profile substituted (suffixal, agglutinative, no gender) | does the Minoan profile carry *any* information? If LB also fails under it, the profile all of Phases 3–5 rests on is decoration |
| (c) optional | as (a), word divisions stripped | how much of any signal came from the editor's word division? |

---

### Step 6 — fork

- **Pass** → method validated. Cypro-Minoan is already staged
  (`languages/cypro-minoan/config.yaml` + `mapping.csv` exist). Run the same gate there — but
  with the LB error rate known, a CM failure becomes interpretable rather than ambiguous.
- **Fail** → write `data/analysis/lb_sandbox/lb_sandbox_result.md` as a negative result. The
  remaining levers are then only (i) new data — `KN Zg 57` when *Anetaki II* prints, and
  (ii) an external sister-script break. This is the same conclusion
  `MULTI_LANGUAGE_DECYPHR_PLAN.md` already reaches; the sandbox is what turns it from an
  inference into a measurement.

---

## 5. Abort conditions (decided now)

Stop and fix before running if any of these hold. A number from a broken corpus is
indistinguishable from a finding.

1. Token coverage `< 0.95`
2. Unique syllabograms `< 80` or `> 110`
3. The `transliteration` guard fires
4. The DB row count differs from the parsed row count by more than the documented blanks
5. Kober triples on LB are fewer than 10% of LA's (means sign IDs are wrong, not the corpus)

---

## 6. Not now

| Tempting | Why not |
|---|---|
| Bigger model / 36-class classifier in `pipeline/ml` | Phase 4 answered this: 0 HIGH, 6 MEDIUM of 94, mean cosine 0.177. ~2 orders of magnitude short on tokens. More capacity means more confidently wrong |
| Any optimizer (beam, annealing, Optuna) | `oracle_test` exists to say no, and already said no |
| Arithmetic/fraction verifier | `data/analysis/logograms/fraction_values_proposed.csv` is circular — `proposed_decimal_value` is derived from "pairs with A 708 to sum ~1", which is then cited as evidence for that pair. Also `A 710 = 0.6`, `A 713 = 0.4`, `A 712 = 0.9375`, `A 722 = 0.4375` are not in the Aegean fraction series → smells like a complement-generator emitting phantoms (cf. AB 100–137). Audit before it becomes evidence |
| Bayesian phylogenetics, evidence-weight blending | Blending three uninformative sources yields one uninformative source with a nicer confidence number |
| Template / split-repos | Gated on a language beating the oracle. See `MULTI_LANGUAGE_DECYPHR_PLAN.md` §5 |

---

## 7. Status

**Result (2026-09-15):** condition (a) ran → **lift 0.00×**. A challenge to that result
prompted a full retrace (`data/analysis/ventris/oracle_retrace_findings.md`), which found
**three bugs** — one in this sandbox's Kober generation (a 15-sign uncertain set collapsed the
triple graph to 101 triples / 3 anchors-with-partners), and two in the pipeline
(`oracle_test`'s chance baseline used the leaky full anchor set; `_load_kober` discarded the
C/V distinction). All three are fixed. The 0.00× survives the fixes, but its *meaning*
changes: the oracle test is a **broken instrument** (dead constraint stage, 39–70 candidates
per sign, no aggregator ever producing a unique argmax), not evidence that Linear A's corpus
lacks signal. Linear A re-measured with the fixed code is also 0.00× (chance 3.73%).
Condition (b) remains deferred, now for the stronger reason that the instrument needs repair
before ablation results mean anything.

| Step | Deliverable | Status |
|---|---|---|
| 0 | `languages/linear-b/data/raw/tablets.csv` (7,370 rows) | **done** |
| 1 | `translit_to_signid.csv`, `pipeline/lb_ingest.py` (100% coverage, 88 signs) | **done** |
| 2 | `linear-b.db` (4,794 ins / 40,038 signs, transliteration NULL) | **done** |
| 3 | `answer_key.csv` + LB Kober patterns | **done** (graph corrected in retrace) |
| 4 | `config.yaml` + leak guard | **done** |
| 5 | condition (a): 0.00× — **instrument broken, verdict withheld** | **retraced** |
| 6 | fork: repair the instrument (see retrace §Open items) before any LA conclusion | next |

**Gate amendment (documented in code):** the unique-sign bound became relative
to the Unicode inventory (74 named signs), corrected before the first oracle
run; the pass threshold (1.5×) is untouched and was never tuned.
