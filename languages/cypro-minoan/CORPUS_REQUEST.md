# Cypro-Minoan corpus — data request

**Purpose:** obtain the published Cypro-Minoan corpus in machine-readable form so the Linear A
project can run the one test that does not depend on distributional inference.

**Status:** draft, ready to send (check the bibliographic reference and the contact address before
sending). Scaffolding that will consume the data already exists in this directory: `config.yaml`
(corpus format + period/support maps), `mapping.csv` (89 CM signs → U+12F90 block), and an ingest
path that reuses the project's parser.

---

## Why this corpus, specifically

Linear A has no bilingual, no deciphered relative and no known language. Every corpus-internal
method has now been measured against controls on a deciphered sibling (Linear B, values withheld):
frame analysis, paradigm-slot alternation, distributional instruments — all at or below chance
(see `METHOD_CLOSURE_PAPER.md` at the repository root). What has *not* been tested is a chain with
a **deciphered endpoint**:

```
Linear A  →  Cypro-Minoan  →  Cypriot Syllabary  →  Greek
                                (deciphered, 1870s)
```

If Cypro-Minoan can be read — even partially — through the Cypriot Syllabary values, the question
"does this yield a known language?" becomes a **hypothesis test against a known language** rather
than an inference from internal statistics. Linear A↔CM sign correspondences then transfer values
directly. This is the project's stated priority-1 path
(`MULTI_LANGUAGE_DECYPHR_PLAN.md`, §2), and it is blocked only on the corpus.

## What we are asking for

The published corpus, in any machine-readable form. Concretely, per object:

| field | required? | why |
|---|---|---|
| object identifier (as published) | **yes** | join key and citation |
| findspot / site | **yes** | geographic controls |
| date or period (LC I–III, CG) | **yes** | chronological controls |
| object type (tablet, ball, nodule, cylinder, vessel, sealing, weight…) | **yes** | genre stratification (this decided a false positive in the Linear A work) |
| **sign-level sequential transliteration** — one value per sign, in reading order, using the published CM sign numbers | **yes** | without sign IDs the corpus cannot be aligned against the Cypriot syllabary, so the test is impossible |
| line / face boundaries | helpful | structure |
| sign-inventory concordance (CM number → Unicode U+12F90 codepoint) | helpful | we hold our own; a published one avoids mapping errors |
| reading uncertainty / damage marks (`[ ]`, `( )`) | helpful | our parser handles them |

**What we cannot use:** a running bound transliteration string without sign-level IDs. It cannot be
aligned, so it would not support the test.

**Formats:** CSV/TSV, JSON, SQLite, or any database export — we will write the adapter. If the
data exists only in the printed edition, a scan or a spreadsheet of the tables would be enough to
start.

## What we will do with it, and the acceptance test

1. Ingest into the project's schema (sign IDs only; no values assumed).
2. Apply the Cypriot Syllabary values through the published correspondence and ask whether the
   resulting strings behave like Greek (morphology, expected phonotactics, known lexemes).
3. Report **pass or fail with controls** — including a permutation null and a genre-stratified
   baseline. A negative will be reported as a negative; this project's last five published-feeling
   positives all dissolved under proper controls, and the audit trail is in the repository.

We will not redistribute the data, and we will cite the edition as instructed. If it is useful, we
are glad to share back: the corrected Linear A↔Linear B sign mapping, the Linear B test bed, and the
instrument harness (all in the repository).

## Draft message to send

> **Subject:** Request for machine-readable Cypro-Minoan corpus data
>
> Dear Professor / Dr …,
>
> I work on computational approaches to Linear A. We have just completed a controlled test of the
> standard method family on Linear B with its values withheld — frame analysis, paradigm-slot
> alternation and distributional scoring all measure at or below chance — and published the result
> as a negative (manuscript available on request). The remaining tractable path is the chain
> Linear A → Cypro-Minoan → Cypriot Syllabary → Greek, because the far end is deciphered and the
> question becomes testable against a known language rather than inferred.
>
> That path is blocked only on data. Could you share the corpus from your Cypro-Minoan editions in
> machine-readable form? Minimally, per object: the published identifier, findspot, date/period,
> object type, and a **sign-level sequential transliteration using the published CM sign numbers**.
> Any format is fine — CSV, JSON, a database dump, or a spreadsheet of the catalogue tables; we will
> write the adapter. A bound transliteration string without sign-level IDs cannot be aligned, so it
> would not support the test.
>
> We will not redistribute the data, will cite the edition as you direct, and will report the result
> with controls whether it comes out positive or negative. Happy to share our corrected sign mapping
> and test harness in return, and to describe the test in more detail.
>
> With thanks and best wishes,
> …

## Then

When data arrives: drop it into `data/raw/` (or hand it over as-is), and the pipeline needs one
adapter plus these steps, already scripted in `README.md`:

```bash
uv run python -m pipeline.cli unicode validate --language cypro-minoan
uv run python -m pipeline.ingest --language cypro-minoan
uv run python -m pipeline.cli db stats languages/cypro-minoan/data/database/cm.db
uv run python pipeline/positional_analysis.py --language cypro-minoan
```

The existing `data/raw/cm.json` is a **synthetic placeholder** (19 inscriptions, 252 signs) built to
prove the pipeline transfers; it is not evidence of anything and must be replaced.