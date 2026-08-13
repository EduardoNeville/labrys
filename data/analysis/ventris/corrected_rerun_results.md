# Corrected-Corpus Re-verification — FINAL Results

**Date:** 2026-08-13
**Status:** ALL Priority 1–3 done. See TODO for 4.3 (network stats).

## The correction (committed)

- Fixed 144 Unicode→Bennett mapping errors (rebuilt from unicode.org names list)
- Re-ingested 1,720 inscriptions; DB now: 10,389 syllabograms + 629 logograms
- IOZa2 now reads AB 08 AB 59 AB 28 AB 54 AB 57 (= A-TA-I-*301-WA-JA, GORILA)

## Final before/after verdict

| Finding | Before | After | Verdict |
|---------|--------|-------|---------|
| Diachronic prior | p=0.0003, 2× | p=0.1748, 1.1× | ❌ INVALIDATED |
| Toponym i-da | 20 | 19 exact | ✅ SURVIVES |
| Toponym pa-i-to | 95 fuzzy | 90 fuzzy (PA-TO d1) + 2 exact | ⚠️ WEAKENED |
| Misvalued AB 16/60/80 | anomalous | not anomalous | ❌ INVALIDATED |
| AB 85 word divider | 274 occ #1 | 8 occ | ❌ INVALIDATED |
| A 301 | 1 occ | 274 occ, 85% initial | ✅ NEW (logogram/heading) |
| V-link cohesion | 2.2× | 1.18× | ❌ INVALIDATED |
| Bigram reduction | 26.7% | 26.9% | ✅ unchanged |
| Oracle scorer | 0.6× chance | still fails | ✅ unchanged |
| AB 82↔LIVESTOCK | p=0.0002 | gone | ❌ INVALIDATED |

## New findings on corrected data

1. **Real libation formula now accessible:**
   - ja-sa-sa-ra-me: 9 insns (IOZa2/6/9/12/16, PKZa27, PLZf1, PSZa2)
   - u-na-ka-na-si: 6 insns (IOZa2/9, KOZa1, PKZa27/8, SYZa2)
   - si-ru-te: 7 insns (IOZa14/15, IOZa2, KOZa1, SYZa3, TLZa1, VRYZa1)
   - Opening: AB 08 AB 59 AB 28 AB 54 AB 57 (matches GORILA)

2. **Commodity enrichment (corrected, Bonferroni-surviving):**
   - AB 30 → LIVESTOCK (p=0.0001, 2.6×)
   - AB 28 → WINE (p=0.0001, 8.6×)

3. **A 301 functional profile:** logogram, 85% inscription-initial, 229/274 at
   Haghia Triada — a heading/entry-opening marker, not a syllabogram.

## The honest meta-verdict

**Every positive finding built on the corrupted corpus is invalidated** —
diachronic prior, misvalued signs, AB 85 word divider, V-link cohesion,
AB 82↔LIVESTOCK. They were all artifacts of the transcription bias.

**What survives:** the negatives (oracle, cryptanalysis), i-da, and the
corpus itself (now correct).

**What's newly enabled:** the real libation formula and two new commodity
associations (AB 30↔LIVESTOCK, AB 28↔WINE) — all on corrected data. This is
the genuine path forward.
