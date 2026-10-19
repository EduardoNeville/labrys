# MEMORY.md — Egyptian Bridge Marshal

## 2025-08-03: Egyptian trade vocabulary bridge implementation

### Decisions
- Used consonant-class matching (P/T/K/S/N/R/W/V) instead of fixed CV mapping.
  Egyptian vowels aren't written, so matching at the consonant-feature level
  avoids false negatives from vowel mismatch while retaining specificity at
  the phonetic-class level. This is the appropriate level of abstraction for
  an undeciphered script.
- 8 consonant classes: P=labial stops, T=dental stops, K=velar stops,
  S=sibilants, N=nasals (m/n), R=liquids, W=glides (w/j), V=vowels.
  Nasals are separated because Egyptian distinguishes m/n from b/d/t in
  writing and LA has distinct nasal signs.
- 88 Egyptian words encoded with single-char consonant skeleton codes
  (T=ṯ, D=ḏ, S=š, H=ḥ, X=ḫ, Q=ḳ) for clean mapping.
- Commodity context detection: logograms (GRA, OLE, VIN, AROM, CYP, etc.)
  within ±3 sign positions of match.

### Gotchas
- Initial CV-skeleton approach (mapping each Egyptian consonant to a fixed
  LA CV sign like 't'→'TU') was too rigid. Only 1 match found in 4,232 tokens.
  The fixed vowel assignment (always /u/ for t- series) meant real borrowings
  with different vowels would never match.
- DB transliterations mix uppercase (AB values like 'DA', 'RO') and lowercase
  (positional variants like 'da', 'ro'). Only ~4,232 of 10,048 syllabograms
  have recognizable AB phonetic values — the rest are numerals, logogram codes,
  fractions, word dividers, or unassigned signs.
- Commodity logograms appear in the signs table with sign_type='syllabogram'
  (not 'logogram'), so letter-pattern filtering is needed.
- sign_semantics table is empty (0 rows) — commodity context must be detected
  from transliteration patterns only.
- The 'expanded' search sometimes finds more matches than 'conventional' because
  Phase 8 values for previously-unknown signs fill in the consonant-class gaps.

### Verified commands
- `uv run python pipeline/egyptian_bridge/corpus.py` — vocab generation
- `uv run python pipeline/egyptian_bridge/search.py` — full search pipeline
- `uv run python -c "from pipeline.egyptian_bridge.corpus import generate_all; print('OK')"` — import check
- `uv run python -c "from pipeline.egyptian_bridge.search import search, build_corpus; print('OK')"` — import check

### Results
- 312 consonant-class matches across 25 Egyptian words, 151 inscriptions
- 40 matches adjacent to commodity logograms (16 unique Egyptian words)
- Top matches: sntr (incense→HT96a with AROM+GRA), SDr (wine→ZA11a with VIN),
  Ssr (linen→HT27b with GRA+VIN)
- Null-model ratios: 1.6x–6.4x over shuffled control
- Key question: "Do 3-5 words appear in commodity-appropriate contexts?" → Yes,
  but the matches are consistent with both signal AND noise — no strong
  evidence for Egyptian loans in LA

### Key insight for future work
- With only 4,232 syllabogram tokens across 1,220 texts, 3-consonant-class
  matches are too common to distinguish borrowing from coincidence.
  A 4-sign threshold would reduce noise but most Egyptian trade terms
  have 2-3 consonant skeletons. This is an inherent limitation of the
  corpus size and Egyptian word length.
