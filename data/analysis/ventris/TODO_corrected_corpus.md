# TODO — Re-run Analyses on the Corrected Corpus

**STATUS:** Priority 1 done, libation formula done. See `corrected_rerun_results.md`.

**Context:** The corpus DB was re-ingested with a corrected Unicode→Bennett
mapping (144 errors fixed: AB 85→8, A 301→274, AB 51→AB 59, AB 26→AB 28,
AB 46→AB 54, AB 49→AB 57, etc.). ALL frequency-based findings computed on the
old DB are suspect and must be re-verified.

**Guiding question for each:** did the finding survive the correction, or was
it an artifact of the transcription bias?

---

## Priority 1 — Core verified findings ✅ DONE

### 1.1 Diachronic prior (MM-attested → CONFIRMED) ✅ INVALIDATED
- [x] Re-run `pipeline/ventris/diachronic.py` on corrected DB
- [x] Result: Fisher p 0.0003 → **0.1748** (NOT significant), LOO 1.21× → **0.91×**
- [x] Shared 67% vs LM-only 55% — gap collapsed
- [x] **Verdict: artifact of corrupted frequencies — INVALIDATED**

### 1.2 Toponyms (pa-i-to = Phaistos, i-da = Ida) ✅ MIXED
- [x] Re-run toponym search on corrected DB
- [x] PHAISTOS: 95 → 90 fuzzy (PA-TO dist-1, mostly noise) + 2 exact sign-seq
- [x] IDA: 20 → **19 exact** (robust)
- [x] **Verdict: i-da SURVIVES, pa-i-to WEAKENED (was loose fuzzy match)**

### 1.3 Misvalued signs (AB 16, AB 60, AB 80) ✅ INVALIDATED
- [x] Re-run positional analysis (regenerated profiles from corrected DB)
- [x] Result: AB 16/60/80 NOT anomalous anymore; new anomalies are
      A 301 (508), AB 74, AB 164, AB 180, A 322
- [x] **Verdict: misvalued flags were artifacts — INVALIDATED**

### 1.4 Refined phonetic grid confidence ⬜ PARTIAL
- [x] AB 85 now 8 occ (was 274) — no longer meaningful as "word divider"
- [ ] A 301 functional analysis (see 4.1)

---

## Priority 2 — Libation formula ✅ DONE (the payoff)

### 2.1 Real formula words in corrected corpus ✅
- [x] ja-sa-sa-ra-me: **9 insns** (was 0) — IOZa2/6/9/12/16, PKZa27, PLZf1, PSZa2
- [x] u-na-ka-na-si: **6 insns** (was 0) — IOZa2/9, KOZa1, PKZa27/8, SYZa2
- [x] si-ru-te: **7 insns** (was 0) — IOZa14/15, IOZa2, KOZa1, SYZa3, TLZa1, VRYZa1

### 2.2 Formula structure on corrected data ✅
- [x] Re-extracted n-grams: opening now AB 08 AB 59 AB 28 AB 54 AB 57
      (= A-TA-I-*301-WA-JA, matches GORILA), ja-sa-sa = AB 57 AB 31 AB 31
- [x] The old "5-part formula" was an artifact; real structure now visible

---

## Priority 3 — Previously-tested avenues ⬜ PARTIAL

### 3.1 Positional anomaly detection ✅ DONE
- [x] New anomalies: A 301 (508), AB 74, AB 164, AB 180, A 322
- [x] Old anomalies (AB 16/60/80/82/110) gone — artifacts

### 3.2 Cryptanalysis ✅ DONE
- [x] Bigram: 26.7% → 26.9% (unchanged, frequency artifact)
- [x] V-link cohesion: 2.2× → **1.18×** (collapsed — was artifact)

### 3.3 Commodity enrichment ⬜ PENDING
- [ ] Regenerate logogram_contexts.csv from corrected DB first
- [ ] Then re-run commodity_semantics.py
- [ ] AB 82↔LIVESTOCK result is on STALE context data

### 3.4 Oracle test ✅ DONE
- [x] Still 0 consensus, scorer still fails (no signal) — unchanged

---

## Priority 4 — New analyses enabled by correction ⬜ PARTIAL

### 4.1 A 301 as a first-class sign ⬜
- [ ] 274 occ, #1 anomalous — functional analysis (logogram in formula)

### 4.2 AB 85's real role ✅
- [x] 8 occ, not anomalous — was a mis-mapped A 301; now properly rare

### 4.3 Corrected frequency spectrum ⬜
- [ ] positional_profiles.csv regenerated ✅
- [ ] sign_centrality / network stats need re-gen

---

## Definition of Done

For each re-run: output to `data/analysis/corrected/` (or overwrite with a
`corrected_` prefix), record BEFORE vs AFTER numbers, and a one-line verdict:
SURVIVES / CHANGED / INVALIDATED.

**Master question:** after correction, which of the project's verified
findings are still standing?

**ANSWER (so far):** Only the negatives (oracle, cryptanalysis) and i-da
survive. Every positive finding was an artifact. The real libation formula
is now accessible — the genuine path forward.
