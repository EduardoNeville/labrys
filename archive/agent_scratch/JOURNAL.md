# JOURNAL.md — Egyptian Bridge Marshal

## 2025-08-03 14:50 — Task start
- Read all input files: AGENTS.md, expanded_grid.csv, refined_phonetic_grid.csv, lineara_full.db
- Understood DB schema: signs table with transliteration, sign_type, bennett_id
- DB has 11,018 total signs (10,048 syllabograms, 728 logograms)
- Loanword matching code in pipeline/loanword_matching.py served as pattern reference

## 2025-08-03 14:52 — corpus.py built
- 88 Egyptian trade/commerce terms encoded
- Categories: agriculture (12), beverages (3), commodities (17), materials (6), metals (7), trade (13), administrative (30)
- Used single-char consonant skeleton codes (T=ṯ, D=ḏ, S=š, H=ḥ, X=ḫ, Q=ḳ, etc.)
- Each consonant → one LA CV sign
- Average LA sequence length: 2.6 signs; 46 words have >=3 signs

## 2025-08-03 14:54 — search.py v1: CV-skeleton matching FAILED
- Direct CV mapping was too rigid: only 1 match found (TXnw → HT122a)
- Problem: each Egyptian consonant is mapped to a fixed CV sign (e.g., 't' always → 'TU')
  but Egyptian vowels aren't written — the actual borrowed form could use any vowel
- Corpus only has 4,232 valid syllabogram tokens; 3-sign exact CV matches are very rare
  because concatenated CV strings don't preserve word boundaries

## 2025-08-03 14:55 — search.py v2: consonant-class matching
- Rewrote to use consonant classes: P(labial), T(dental), K(velar), S(sibilant),
  N(nasal), R(liquid), W(glide), V(vowel)
- Egyptian consonants map to class (m,n→N; p,b,f→P; t,d,T,D→T; etc.)
- LA signs map by onset consonant (pa→P, na→N, a→V, etc.)
- Search for class-strings as substrings in corpus
- Result: 312 matches, 40 with commodity context, 25 unique Egyptian words

## 2025-08-03 14:56 — Bug fixes
- Fixed: nasals initially grouped with labial/dental stops (wrong)
- Fixed: commodity context used raw_signs indices instead of DB sequence numbers
- Added conventional_sequences tracking
- Added per-inscription null model (vs. global shuffling causing cross-text matches)

## 2025-08-03 14:57 — Final run and verification
- Verified top matches against actual DB sequences:
  - sntr (SNTR class) → HT96a: SI-MI-TA-RU adjacent to AROM+GRA logograms ✓
  - SDr (STR class) → ZA11a: SO-TA-RA with VIN nearby ✓
  - Ssr (SSR class) → HT27b: SA-SA-RE with GRA+VIN nearby ✓
- Null model: SSR (3.3x expected), NTT (3.1x), NNW (6.4x) — some above chance
- Honest assessment written: consonant-class matching is broad, false positives likely

## 2025-08-03 14:58 — Deliverables
- Wrote REPORT.md with comprehensive methodology, results, caveats
- Wrote result.md completion summary
- All 3 output files verified
