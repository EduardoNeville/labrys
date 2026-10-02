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

2. **Commodity enrichment (corrected, Bonferroni-surviving) — AUDITED 2026-10-01, holds and strengthens:**
   - AB 30 → LIVESTOCK (slot p=0.000116, 2.64×) → **document-level p=2.7e-11**, 2.87×
   - AB 28 → WINE (slot p=0.000073, 8.64×) → **document-level p=2.6e-05**, 5.71×

   `data/analysis/commodity_decoding/enrichment_audit.py` re-tests both against the null their
   unit requires, plus a site-stratified permutation (2,000 reps) that holds each sign's number
   of documents *per site* fixed — the control that dissolved the toponym claim (p 0.00086 →
   0.38). **Not one permutation reached the observed counts (empirical p = 0.0005, the floor of
   2,000).** These are the only positively-signed statistical results in this repository that
   have survived a matched null, and they are now its best-audited claims.

   Two corrections to the numbers as recorded:
   - **The Bonferroni family is 122 tests, not the 61 rows in `sign_commodity_enrichment.csv`**
     (`bonferroni_alpha` counts every tested pair, including the non-significant ones), so the
     family-wise alpha is 0.05/122 = **0.00041**, not 0.00082. Both claims clear it either way.
   - **The document level is more sensitive than the slot level and surfaces six more pairs**
     (AB 31, AB 76, AB 41, AB 02, AB 81 → LIVESTOCK; AB 27 → WINE, all p < 0.00041 at document
     level; none at slot level). Eight survivors against 0.05 expected by chance. Treat them as
     **candidates of the same kind, not findings** — they have not had the site-stratified
     permutation, and the two that have, have it.

   What the association does *not* say: it does not give AB 30 or AB 28 a meaning or a value. It
   says a syllabogram's *entry context* is enriched with a logogram's *semantic class* — which
   makes these the first **semantic-anchor candidates** in the project (closure paper §7 class 1)
   rather than distributional ones, and the only evidence class here that has ever returned a
   controlled positive.

3. **A 301 functional profile (corrected 2026-10-01):** logogram, 86.9% inscription-initial
   *pooled* — but that pooled figure is a statistic about one room. Per archive: **229 of 231
   (99.1%) initial at Haghia Triada Portico 11 and Room 13**, and **9 of 43 (20.9%) everywhere
   else** (Khania 3/7, Iouktas 1/6, Syme 0/5, Zakros 1/3, Palaikastro 0/2). "Heading/entry-opening
   marker" is that archive's tablet format, not a general property of the script. The AB 85
   retraction is unaffected — it rests on the attribution of 508 occurrences, not on the profile.
   Stratification must reach ROOM level: two rooms of the same site disagree (Portico 229/231,
   Villa Magazine 0/3). Tool: `data/analysis/ventris/archive_stratification.py`.

## The honest meta-verdict

**Every positive finding built on the corrupted corpus is invalidated** —
diachronic prior, misvalued signs, AB 85 word divider, V-link cohesion,
AB 82↔LIVESTOCK. They were all artifacts of the transcription bias.

**What survives:** the negatives (oracle, cryptanalysis), i-da, and the
corpus itself (now correct).

**What's newly enabled:** the real libation formula and two new commodity
associations (AB 30↔LIVESTOCK, AB 28↔WINE) — all on corrected data. This is
the genuine path forward.

**2026-10-01 update:** both commodity associations were audited against a document-level null, a
site-stratified permutation and a cross-site replication. Result: **the association is real within
Haghia Triada and does not generalize.** The slot-level null was wrong (windows overlap, so the
effective sample is documents), the document-level numbers are stronger (p=2.7e-11 / 2.6e-05), and
a site-stratified permutation clears them at the floor of 20,000 reps — but selecting on Haghia
Triada and testing on Khania replicates **2 of 67 pairs, both logogram↔own-class tautologies**,
while every syllabogram association fails. These are HT's entry conventions, not semantic anchors
for Linear A. Details in `data/analysis/ventris/verification_audit.md` Phase 14/14.1.
