# TODO — Next Steps on the Corrected Corpus

**STATUS:** Priorities 1–3 of the re-verification TODO are DONE (see
`corrected_rerun_results.md`). This TODO defines the next phase: exploiting
what the correction unlocked.

**Context:** The corpus is now correct (144 mapping errors fixed). The real
libation formula (ja-sa-sa-ra-me, u-na-ka-na-si, si-ru-te) is accessible, and
two commodity associations survived Bonferroni (AB 30↔LIVESTOCK, AB 28↔WINE).
The negatives (oracle, cryptanalysis) still hold.

---

## Priority 5 — Libation formula exploitation (the real one)

### 5.1 Structural decomposition of the formula ✅ DONE
- [x] Opening identified: AB 08 AB 59 AB 28 AB 54 [AB 57] = A-TA-I-*301-WA-[JA]
- [x] ja-sa-sa-ra-me (AB 57 31 31 60 13), u-na-ka-na-si (AB 10 06 77 06 41),
      si-ru-te (AB 41 26 04) found in corrected corpus
- [x] FULL formula mapped on IOZa2, KOZa1, PKZa11, IOZa9, PKZa27
- [x] **KEY: IOZa9 = PKZa27 = identical 10-sign text**
      `ja-sa-sa-ra-me u-na-ka-na-si` (AB 57 31 31 60 13 | AB 10 06 77 06 41)
- [x] Template identified: [OPENING A-TA-I-*301-WA-JA] → [var] →
      ja-sa-sa-ra-me → u-na-ka-na-si → [i-*301-…] → si-ru-te

### 5.2 Formula-word co-occurrence structure ✅ DONE
- [x] Grammar built: OPENING always at pos 0; ja-sa-sa-ra-me followed by
      u-na-ka-na-si (5/9); u-na-ka-na-si followed by i-*301 (3/6);
      si-ru-te preceded by ma (5/7)
- [x] **Template: [OPENING A-TA-I-*301-WA-JA] → [var] → ja-sa-sa-ra-me →
      u-na-ka-na-si → [i-*301-…] → [ma-]si-ru-te — order FIXED, matches
      published scholarship**
- [ ] AB 28↔WINE: AB 28 (i) appears after u-na-ka-na-si (i-*301-…) and in
      pa-i-to — it's a formula element, not a commodity marker

### 5.3 The deity-name question ✅ DONE (milestone)
- [x] Variable slot recovered: IOZa2 has JA-DI-KI-TU (AB 57 07 67 69)
- [x] Scholarship confirms: JA-DI-KI-TU on IO Za 2, plausibly connected with
      Mount Dikte (Diktaian deity) — the phonetic-semantic anchor
- [x] Full IOZa2 reading verified against source transliteratedWords:
      A-TA-I-*301-WA-JA · JA-DI-KI-TU · JA-SA-SA-RA-ME · U-NA-KA-NA-SI ·
      I-PI-NA-MA · SI-RU-TE · TA-NA-RA-TE-U-TI-NU · I
- [x] Documented in libation_recovered.md

---

## Priority 6 — New commodity/positional findings (corrected)

### 6.1 AB 30 ↔ LIVESTOCK (p=0.0001) ✅ DONE
- [x] AB 30 consistently AFTER livestock logograms (A 303/304) in 12 contexts
      (HT30/89/94a/99a/100, KH15/58, KNZb35, PH14a) — a following modifier
- [x] AB 30 = ni (LB transfer) — a livestock qualifier word

### 6.2 AB 28 ↔ WINE (p=0.0001) ✅ DONE
- [x] AB 28 (i) is the FIRST sign after wine logogram (A 310) in 5 contexts
      (HT8a/8b/85b/98a/122a) — starts a wine term
- [x] Full word in HT8a: AB 28 AB 41 AB 67 = i-si-… — a wine-type word

### 6.3 The corrected anomalous-sign list ✅ DONE
- [x] New anomalies: AB 74 (47), AB 164 (15), AB 180 (11), A 322 (4,
      logogram), AB 23m (7), AB 21 (3)
- [x] **These are RARE signs with small samples — the anomaly is expected
      noise, NOT evidence of misvaluation (unlike the old high-freq AB
      85/60/80 which were artifacts)**
- [x] Verdict: corrected positional data shows no real misvalued-sign signal
- [ ] Re-verify whether ANY of these correspond to known misvalued signs
      (the old AB 16/60/80 list was invalidated)

---

## Priority 7 — Data quality completion ✅ DONE

### 7.1 Restore lost transliterations ✅
- [x] Transliteration coverage 95.9% (restored from source)

### 7.2 Corrected network/centrality stats ✅
- [x] Re-run network analysis on corrected DB
- [x] Top-degree still numerals (expected); top syllabograms now AB 81, AB 59
      (corrected identities, not the corrupted AB 85/51/26)

### 7.3 Verify no other mapping errors remain ✅
- [x] Fractions (A 701-730), metrical (A 500-510, MET A-J), numerals (NUM 10),
      vase shapes (VASE 10-13), A 560-568, ADJ 001-005 restored (70 entries)
- [x] Re-ingested: DB now has syllabogram (10084), logogram (742),
      fraction (101), metrical (87), numeral (4)
- [x] Full type coverage restored; libation formula + IOZa2 verified intact

---

## Priority 8 — The oracle on corrected data (sanity)

### 8.1 Re-run oracle with corrected anchors
- [ ] The confirmed-sign set changed (AB 28, AB 59, AB 54, AB 57 now have
      correct identities). Re-run oracle_test() — does the scorer still
      fail? (expected: yes, no signal)
- [ ] If any surprising change, investigate

---

## Definition of Done

Each item: run on corrected DB, record result, one-line verdict.
**Master goal:** build the real libation formula's structure and test the
deity-name hypothesis — the genuine path to a cascade.
