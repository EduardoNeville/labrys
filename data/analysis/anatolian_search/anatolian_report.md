# Anatolian Cognate Search Report

**Generated:** 2026-08-03 03:48
**Module:** `pipeline/anatolian_search/comparison.py`
**Languages:** Cuneiform Luwian, Hieroglyphic Luwian, Lycian

---

## Executive Summary

We searched a curated Luwian/Lycian vocabulary of 134 words against N Linear A inscriptions, using both conventional Linear-B-transfer values and ML-refined phonetic values. The goal was to determine whether Anatolian (Luwian/Lycian) shows stronger lexical evidence than the Tyrsenian hypothesis, which found 0 exact Swadesh matches.

- **Total candidate matches:** 2345
- **Exact substring matches:** 121
- **Fuzzy matches (edit ≤ 1):** 2224
- **Unique word types matched exactly:** 25
- **Matches on ≥3 sites:** 0
- **Matches in BOTH seq types:** 181
- **Expected random 2-sign matches per term:** ~2.3
- **Expected random 3-sign matches per term:** ~0.0
- **Assessment:** NOT SIGNIFICANT: 2-3 sign AB forms match trivially by chance in a limited syllabary (~60 values). Short CV sequences strip all consonant cluster information, making unrelated languages appear similar. These are false positives driven by syllabary structure.

### Bottom Line

**No linguistically meaningful cognate matches were found.** While 25 unique Anatolian word forms appeared as exact substrings in Linear A texts, these are almost entirely 2-sign (4-character) CV sequences that match trivially by chance in a limited syllabary. The CV-only representation strips all consonant-cluster and morphological information, making unrelated languages appear superficially similar.

The observed matches (KUPA, SASA, ASASA, NANA, PATA, etc.) are the result of **syllabary-induced false positives** — any language expressed in a 60-value CV syllabary will produce similar-looking 2-3 sign sequences. These do not constitute lexical evidence for an Anatolian language.

---

## Methodology

### Data Sources

- **Luwian vocabulary:** Melchert (1993) *Cuneiform Luwian Lexicon*, Payne (2010) *Hieroglyphic Luwian* — nouns, verbs, numbers, suffixes
- **Lycian vocabulary:** Melchert (2004) *Dictionary of the Lycian Language*, Neumann (2007) *Glossar des Lykischen* — nouns, verbs, numbers, suffixes
- **Anatolian toponyms:** Hittite archives, Arzawa/Arzawan geography
- **Linear A corpus:** 1,719 inscriptions, ~11,018 sign occurrences from `data/database/lineara_full.db`
- **Refined phonetic grid:** Phase 5 synthesis (44 CONFIRM, 94 UNCERTAIN signs)
- **ML predictions:** 94 predicted values for UNCERTAIN signs (≥0.20 confidence threshold)

### Search Strategy

1. **Phoneme-to-AB conversion:** Each Anatolian word was converted to a Linear A AB sequence using an Anatolian-specific phoneme mapping (handling laryngeals, labiovelars, sibilants)
2. **Exact substring search:** AB forms searched as contiguous substrings in each inscription's syllabogram sequence
3. **Fuzzy matching (Levenshtein ≤ 1):** Sliding-window comparison allowing 1-sign differences or insertions/deletions
4. **Two-pass search:** Searched against BOTH conventional Linear-B-transfer values AND ML-refined phonetic values
5. **Deduplication:** One best match per (word, inscription, meaning) triplet

### Limitations

- **Syllabary distortion:** Consonant clusters, laryngeals, and coda consonants are distorted or lost in CV-syllabic representation. A Luwian word like *ḫašta-* 'bone' becomes ASATA in AB — only 60% phonetically similar.
- **Small corpus:** ~1,719 texts, mostly 2-10 signs each. Long texts (>20 signs) are rare. Statistical power for substring matching is limited.
- **Uncertain transliteration:** 68% of AB signs are UNCERTAIN. ML predictions have low confidence. Many matches would be spurious.
- **CV-syllabic approximation bias:** Two unrelated languages can produce similar-looking CV sequences purely by chance, especially with a limited syllabary (~60 signs).

---

## Cognate Candidate Results

### Exact Matches (edit distance = 0)

| Word (Phonemic) | AB Form | Meaning | Language | Inscription | Site | Seq Type |
|-----------------|---------|---------|----------|-------------|------|----------|
| nāna- | NANA | brother (?) | luwian | HT1 | Haghia Triada - Portico 11 and Room 13 | conventional |
| kup- | KUPA | to plan, devise | luwian | HT1 | Haghia Triada - Portico 11 and Room 13 | conventional |
| xupa- | KUPA | tomb | lycian | HT1 | Haghia Triada - Portico 11 and Room 13 | conventional |
| tbi- | TAPI | one (numeral '1') | lycian | HT4 | Haghia Triada - Portico 11 and Room 13 | conventional |
| tār- | TARA | tree/wood | luwian | HT6a | Haghia Triada - Villa Magazine | conventional |
| pddẽ- | PATE | place | lycian | HT8a | Haghia Triada - Villa Magazine | conventional |
| aruna- | ARUNA | sea | luwian | HT10b | Haghia Triada - Villa Magazine | conventional |
| tarri- | TARI | three | luwian | HT10b | Haghia Triada - Villa Magazine | conventional |
| -tari | TARI | middle voice 3sg [Mediopassive marker] | luwian | HT10b | Haghia Triada - Villa Magazine | conventional |
| arina- | ARINA | spring, water source | lycian | HT10b | Haghia Triada - Villa Magazine | conventional |
| arina- | ARINA | spring, source | lycian | HT10b | Haghia Triada - Villa Magazine | conventional |
| tri- | TARI | three | lycian | HT10b | Haghia Triada - Villa Magazine | conventional |
| Arinna | ARINA | toponym: Arinna | anatolian | HT10b | Haghia Triada - Villa Magazine | conventional |
| tede- | TETE | father | lycian | HT13 | Haghia Triada - Villa Magazine | conventional |
| kup- | KUPA | to plan, devise | luwian | HT16 | Haghia Triada - Villa Magazine | conventional |
| xupa- | KUPA | tomb | lycian | HT16 | Haghia Triada - Villa Magazine | conventional |
| kup- | KUPA | to plan, devise | luwian | HT24a | Haghia Triada - Corridor 9 and Vestibule 26 | conventional |
| xupa- | KUPA | tomb | lycian | HT24a | Haghia Triada - Corridor 9 and Vestibule 26 | conventional |
| Apasa | APASA | toponym: Apasa | anatolian | HT24a | Haghia Triada - Corridor 9 and Vestibule 26 | conventional |
| tede- | TETE | father | lycian | HT26a | Haghia Triada - Villa Magazine | conventional |
| kuen- | KUNA | to kill, strike | luwian | HT47a | Haghia Triada - Villa Magazine | conventional |
| nāna- | NANA | brother (?) | luwian | HT64 | Haghia Triada - Villa Magazine | conventional |
| pddẽ- | PATE | place | lycian | HT85b | Haghia Triada - Casa Room 7 | conventional |
| kup- | KUPA | to plan, devise | luwian | HT88 | Haghia Triada - Casa Room 7 | conventional |
| kubaba- | KUPAPA | goddess Kubaba | luwian | HT88 | Haghia Triada - Casa Room 7 | conventional |
| xupa- | KUPA | tomb | lycian | HT88 | Haghia Triada - Casa Room 7 | conventional |
| pata- | PATA | foot | luwian | HT94b | Haghia Triada - Casa Room 7 | conventional |
| tār- | TARA | tree/wood | luwian | HT96a | Haghia Triada - Casa Room 7 | conventional |
| Apasa | APASA | toponym: Apasa | anatolian | HT102 | Haghia Triada - Casa Room 7 | conventional |
| Apasa | APASA | toponym: Apasa | anatolian | HT105 | Haghia Triada - Casa Room 7 | conventional |

### Best Candidate Matches (exact + fuzzy, d≤1)

| Word (Phonemic) | AB Form | Meaning | Language | Match Type | Dist | Inscription | Site | Seq Type | Both? |
|-----------------|---------|---------|----------|------------|------|-------------|------|----------|-------|
| nāna- | NANA | brother (?) | luwian | exact | 0 | HT1 | Haghia Triada - Portico 11 and Room 13 | conventional | ✓ |
| kup- | KUPA | to plan, devise | luwian | exact | 0 | HT1 | Haghia Triada - Portico 11 and Room 13 | conventional | ✓ |
| xupa- | KUPA | tomb | lycian | exact | 0 | HT1 | Haghia Triada - Portico 11 and Room 13 | conventional | ✓ |
| tbi- | TAPI | one (numeral '1') | lycian | exact | 0 | HT4 | Haghia Triada - Portico 11 and Room 13 | conventional |  |
| tār- | TARA | tree/wood | luwian | exact | 0 | HT6a | Haghia Triada - Villa Magazine | conventional |  |
| pddẽ- | PATE | place | lycian | exact | 0 | HT8a | Haghia Triada - Villa Magazine | conventional |  |
| aruna- | ARUNA | sea | luwian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| tarri- | TARI | three | luwian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| -tari | TARI | middle voice 3sg [Mediopassive marker] | luwian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| arina- | ARINA | spring, water source | lycian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| arina- | ARINA | spring, source | lycian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| tri- | TARI | three | lycian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| Arinna | ARINA | toponym: Arinna | anatolian | exact | 0 | HT10b | Haghia Triada - Villa Magazine | conventional |  |
| tede- | TETE | father | lycian | exact | 0 | HT13 | Haghia Triada - Villa Magazine | conventional |  |
| kup- | KUPA | to plan, devise | luwian | exact | 0 | HT16 | Haghia Triada - Villa Magazine | conventional |  |
| xupa- | KUPA | tomb | lycian | exact | 0 | HT16 | Haghia Triada - Villa Magazine | conventional |  |
| kup- | KUPA | to plan, devise | luwian | exact | 0 | HT24a | Haghia Triada - Corridor 9 and Vestibule 26 | conventional |  |
| xupa- | KUPA | tomb | lycian | exact | 0 | HT24a | Haghia Triada - Corridor 9 and Vestibule 26 | conventional |  |
| Apasa | APASA | toponym: Apasa | anatolian | exact | 0 | HT24a | Haghia Triada - Corridor 9 and Vestibule 26 | conventional |  |
| tede- | TETE | father | lycian | exact | 0 | HT26a | Haghia Triada - Villa Magazine | conventional |  |
| kuen- | KUNA | to kill, strike | luwian | exact | 0 | HT47a | Haghia Triada - Villa Magazine | conventional | ✓ |
| nāna- | NANA | brother (?) | luwian | exact | 0 | HT64 | Haghia Triada - Villa Magazine | conventional |  |
| pddẽ- | PATE | place | lycian | exact | 0 | HT85b | Haghia Triada - Casa Room 7 | conventional |  |
| kup- | KUPA | to plan, devise | luwian | exact | 0 | HT88 | Haghia Triada - Casa Room 7 | conventional |  |
| kubaba- | KUPAPA | goddess Kubaba | luwian | exact | 0 | HT88 | Haghia Triada - Casa Room 7 | conventional |  |
| xupa- | KUPA | tomb | lycian | exact | 0 | HT88 | Haghia Triada - Casa Room 7 | conventional |  |
| pata- | PATA | foot | luwian | exact | 0 | HT94b | Haghia Triada - Casa Room 7 | conventional |  |
| tār- | TARA | tree/wood | luwian | exact | 0 | HT96a | Haghia Triada - Casa Room 7 | conventional |  |
| Apasa | APASA | toponym: Apasa | anatolian | exact | 0 | HT102 | Haghia Triada - Casa Room 7 | conventional |  |
| Apasa | APASA | toponym: Apasa | anatolian | exact | 0 | HT105 | Haghia Triada - Casa Room 7 | conventional |  |

### Summary Statistics

- Total raw candidates (before dedup): 2345
- Exact matches: 121
- Fuzzy matches: 2224
- Unique word types (exact): 25
- Unique word types (fuzzy): 72
- Matches found in BOTH transliteration passes: 181
- Matches appearing on ≥3 different sites: 0

---

## Morphology Comparison Results

### Luwian Suffixes in Linear A

| Suffix | AB Form | Function | Occurrences | Final Pos | Texts With | Coverage | Sites |
|--------|---------|----------|-------------|-----------|-----------|----------|-------|
| -a | A | dative singular | 724 | 191 | 466 | 28.5% | 30 |
| -ḫa | A | conjunction 'and' | 724 | 191 | 466 | 28.5% | 30 |
| -mi- | MI | my (1sg possessive) | 78 | 10 | 67 | 4.1% | 19 |
| -ši- | SI | his/her (3sg possessive) | 46 | 0 | 39 | 2.4% | 16 |
| -ti | TI | 3sg present | 25 | 2 | 23 | 1.4% | 11 |
| -ti- | TI | your (2sg possessive) | 25 | 2 | 23 | 1.4% | 11 |
| -ati/-anti | ATI | 3pl present / ablative-instrumental | 6 | 0 | 6 | 0.4% | 4 |
| -an | ANA | accusative singular common | 3 | 0 | 3 | 0.2% | 3 |
| -aš | ASA | genitive singular | 2 | 0 | 2 | 0.1% | 1 |
| -una | UNA | infinitive | 2 | 0 | 2 | 0.1% | 2 |
| -izza- | IZA | causative | 1 | 0 | 1 | 0.1% | 1 |
| -nt- | NTA | participle | 0 | 0 | 0 | 0.0% | 0 |
| -ẽ | E | accusative | 275 | 20 | 172 | 10.5% | 28 |
| -mi | MI | 1sg present | 78 | 10 | 67 | 4.1% | 19 |
| -t- | TA | participle | 69 | 8 | 63 | 3.9% | 15 |
| -te | TE | 3pl verbal ending | 47 | 7 | 44 | 2.7% | 14 |
| -na- | NA | adjectivizer | 40 | 1 | 34 | 2.1% | 12 |
| -ti | TI | 3sg verbal ending | 25 | 2 | 23 | 1.4% | 11 |
| -asa- | ASA | genitival adjective | 2 | 0 | 2 | 0.1% | 1 |
| -ehi | EI | genitive adjective | 0 | 0 | 0 | 0.0% | 0 |
| -ije- | IJE | passive | 0 | 0 | 0 | 0.0% | 0 |
| -ãta- | ATA | gerundive | 0 | 0 | 0 | 0.0% | 0 |

---

## Toponym Suffix Pattern Matching

The -ss- and -nd- suffixes are diagnostic features shared between Anatolian (-ašša-, -anda-) and Aegean/Pre-Greek place names (-ssos, -nthos). Their presence in Linear A can indicate either Anatolian or Pre-Greek substrate influence.

- **Total -ss- pattern hits:** 15
- **Total -nd- pattern hits:** 70
- **Unique -ss- patterns:** 9
- **Unique -nd- patterns:** 27

**Most common -ss- patterns:**
  - `SE-SE`: 7 hits
  - `ZA-SO`: 1 hits
  - `SO-SA`: 1 hits
  - `SE-SA`: 1 hits
  - `SE-SO`: 1 hits
  - `ZA-SI`: 1 hits
  - `SO-SE`: 1 hits
  - `SE-SI`: 1 hits

**Most common -nd- patterns:**
  - `NE-DO`: 9 hits
  - `NE-DU`: 6 hits
  - `NO-TE`: 5 hits
  - `NA-TE`: 5 hits
  - `NE-DI`: 4 hits
  - `NI-DE`: 4 hits
  - `NE-TI`: 3 hits
  - `NO-DI`: 3 hits

**Note:** The -ss- and -nd- patterns are well-attested in Linear A toponymy and do NOT specifically favor Anatolian over Pre-Greek. Both language groups share these suffix patterns as an areal feature of the Bronze Age Aegean-Anatolian interaction sphere.

---

## Phonological Inventory Comparison

### Vowel Systems

| Feature | Luwian | Lycian | Linear A (AB) | Compatible? |
|---------|--------|--------|---------------|-------------|
| Vowel inventory | a, i, u, e (4) | a, i, u, e + nasalized (5+) | a, e, i, o, u (5) | Partial: Anatolian lacks /o/ |
| /o/ vowel | **Absent** | **Absent** | **Present** (O) | ❌ Mismatch |

**Critical finding:** Both Luwian and Lycian lack the /o/ vowel, while Linear A has a dedicated O-series. This is the same mismatch faced by the Tyrsenian hypothesis (Etruscan also has no /o/). The presence of /o/ in LA argues *against* both Anatolian and Tyrsenian.

### Voice Distinction

| Feature | Anatolian | Linear A (AB) | Compatible? |
|---------|-----------|---------------|-------------|
| Voiced stops (b, d, g) | Absent | Conventional AB has D-series and some voiced | Partial |
| Voice contrast | No phonemic voice | AB convention merges voice | ✅ Compatible |

The Linear B convention (which we use for AB values) does not distinguish voiced from voiceless stops. This *could* mask an Anatolian lack of voice distinction, but it could equally mask any other language's voice system.

### Labiovelars

Both Anatolian (kʷ) and Linear A QA-series suggest labiovelar presence. Compatible.

### Laryngeals

Anatolian /ḫ/ has no clear representation in Linear A. It would likely be omitted or mapped to vowels, making many Anatolian words unrecognizable in AB transliteration.

---

## Anatolian Toponym Matches

| Toponym | AB Form | Location | Matched in LA? |
|---------|---------|----------|----------------|
| Millawanda | MILAWANATA | Miletus | — |
| Apasa | APASA | Ephesus | ✓ |
| Wilusa | WILUSA | Troy/Ilion | — |
| Tarḫuntašša | TARATASASA | S-Central Anatolia | — |
| Arinna | ARINA | Hittite heartland | ✓ |
| Ḫattuša | ATUSA | Boğazköy | ✓ |
| Karkiša | KARAKISA | Caria (?) | ✓ |
| Lukkā | LUKA | Lycia (?) | ✓ |
| Aḫḫiyawa | AIJAWA | Aegean/Mycenaean | ✓ |
| Parnassa | PARANASA | Parnassos? | — |
| Zippašla | SIPASALA | W Anatolia | — |
| Iyalanda | IJALANATA | Alinda (?) | — |

---

## Limitations and Caveats

1. **No semantic verification:** Substring matching can only identify phonetic similarities. Without understanding the underlying language, we cannot verify that matched sequences actually mean what the Anatolian word means.
2. **CV-syllabary distortion:** Anatolian languages (especially Luwian) have consonant clusters (e.g., *ḫarš-*, *tarḫunt-*) that are severely distorted in CV-only representation. A true Luwian text in AB would look very different from reconstructed forms.
3. **Areal features, not genetic signal:** -ss- and -nd- toponym patterns are shared across the Anatolian-Aegean interaction sphere. They do not uniquely identify Anatolian languages.
4. **Small, administrative corpus:** The Linear A corpus consists almost entirely of administrative/economic texts (tablets, sealings, nodules). Common nouns may simply not appear in these genres.
5. **Time gap:** Luwian is attested ~1600-1200 BCE (roughly contemporary with Linear A) but Lycian is ~500-300 BCE, 700+ years after Linear A. Using Lycian vocabulary to test Linear A assumes minimal lexical change over 7 centuries.

---

## Conclusion

**The Anatolian (Luwian/Lycian) hypothesis finds no convincing lexical support in the Linear A corpus.** While 25 unique Anatolian word forms appeared as exact substrings (121 total hits), these are overwhelmingly 2-sign (4-character) CV sequences that match trivially by chance in a limited syllabary (~60 sign values). The CV-only representation strips all consonant-cluster and morphological information, making unrelated languages appear superficially similar.

**Key finding: zero matches on 3+ sites.** No Anatolian word form appeared as an exact substring on 3 or more different archaeological sites — a basic threshold for a genuine lexical candidate. The most common matches (KUPA 'to plan/tomb', SASA '-iterative') appear across multiple texts at Hagia Triada, but within a single archive, and their short length (4 chars = 2 CV signs) makes them expected by chance.

The structural similarities between Anatolian and Linear A (suffixal morphology, SOV word order, agglutination) remain interesting but are not unique — Tyrsenian, Hurro-Urartian, and other language families share these features. The critical diagnostics (particular suffixes like -nt- participle, case endings, specific vocabulary) do not appear in Linear A with sufficient confidence to confirm an Anatolian affiliation.

### Comparison Across Hypotheses

| Hypothesis | Structural Fit | Exact Lexical Matches | Toponym Support | Verdict |
|------------|---------------|----------------------|-----------------|---------|
| Tyrsenian (Etruscan) | 5/8 WALS (62.5%) | 0 (p=1.0) | Limited | Best structural fit, no lexical |
| Anatolian (Luwian/Lycian) | 4/8 WALS (50.0%) | 25 2-sign matches (chance) | -ss-/-nd- shared | Structural fit, no lexical |
| Pre-Greek Substrate | 2/4 (50.0%) | N/A | Strong (-ss-, -nth-) | Best toponym fit |

**Final assessment:** The Anatolian hypothesis, like the Tyrsenian hypothesis, fails the lexical test. Despite the documented Bronze Age contact between Crete and Anatolia, and the use of Luwian in the Hittite empire that interacted with the Aegean, we find no convincing evidence that Minoan (the language of Linear A) was an Anatolian language. The apparent 2-sign matches are artifacts of the limited CV syllabary, not evidence of linguistic relationship.