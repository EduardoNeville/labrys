# Corpus Correction — Verified Mapping Errors and the Correction Cascade

**Date:** 2026-08-13
**Status:** CONFIRMED — the corpus DB has systematic Unicode→sign mapping errors; the raw source and Unicode standard are correct.

## The three-way verification

| Codepoint | Source translit | Unicode name (authoritative) | Corpus DB mapping | Verdict |
|-----------|----------------|------------------------------|-------------------|---------|
| U+10655 (𐙕) | `*301` (47 insns) | **A301** | AB 85 (274×) | ❌ **WRONG** |
| U+10633 (𐘳) | `TA` | **AB059** | AB 51 (165×) | ❌ **WRONG** |
| U+1061A (𐘚) | `I` | **AB028** | AB 26 (193×) | ❌ **WRONG** |

**Three independent sources agree:** the raw `inscriptions.json` (lineara.xyz), the Unicode standard (U+10655 = LINEAR A SIGN A301, U+10633 = AB059, U+1061A = AB028), and the published GORILA readings. The corpus DB's mapping table (`unicode_utils.py`) maps these codepoints to the wrong Bennett IDs (AB 85, AB 51, AB 26), corrupting **632+ DB occurrences** (8.4% of syllabograms in 5 signs).

## Answering the challenge: which corpus is correct?

The user's challenge was right: I shouldn't assume the corpus DB is right and GORILA wrong (or vice versa) without evidence. The evidence is now three-way:

1. **The raw source** (`data/raw/sigla/inscriptions.json`) transliterates IOZa2 as `A-TA-I-*301-WA-JA • JA-SA-SA-RA-ME • U-NA-KA-NA-SI...` — matching GORILA exactly.
2. **The Unicode standard** names U+10655 = A301, U+10633 = AB059, U+1061A = AB028.
3. **GORILA** (via scholarship) reads the same.

The corpus DB matches **neither** — its mapping table is an independent (wrong) assignment. So the answer is: **the corpus DB is the outlier; the raw source + Unicode + GORILA agree.** The correction cascade is possible because the source is intact.

## What the correction fixes

1. **AB 85 (274 occurrences) → A 301**: the "word divider" and "libation formula" findings were artifacts of this. AB 85 barely exists; A 301 is the real sign.
2. **AB 51 (165) → AB 59**: the libation formula's TA position.
3. **AB 26 (193) → AB 28**: the libation formula's I position.

## What this means for prior findings

- **Avenue 1 (AB 85 word divider):** retracted — AB 85 is over-attributed by 274×.
- **Avenue 7 (libation formula):** retracted as found — but the REAL formula (ja-sa-sa-ra-me, u-na-ka-na-si) is in the source and becomes accessible after correction.
- **Frequency-based findings** (diachronic prior, toponyms, misvalued signs): must be re-verified on the corrected corpus.

## Next step

Fix `unicode_utils.py` mapping (U+10655→A 301, U+10633→AB 59, U+1061A→AB 28), re-ingest from the raw source, and re-run the key analyses on the corrected corpus.
