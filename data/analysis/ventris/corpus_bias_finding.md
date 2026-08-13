# CRITICAL FINDING — Corpus Transcription Bias (Systematic Sign Mis-Identification)

**Date:** 2026-08-13
**Severity:** HIGH — may invalidate frequency-based findings across the project

## The discovery

While segmenting the libation formula (Avenue 7), the corpus's transcription of
the key libation texts was compared against the published GORILA reading. They
**do not match**.

| Text | Corpus transcription | Published (GORILA V) |
|------|---------------------|----------------------|
| IOZa2/3 opening | `AB 08 AB 51 AB 26 AB 85 AB 46 AB 49` | `AB 08 AB 59 AB 28 A 301 AB 54 AB 57` |
| IOZa9 opening | `AB 49 AB 30 AB 30...` | `AB 57 AB 31 AB 31...` (ja-sa-sa) |

The corpus consistently reads `AB 51` where GORILA has `AB 59`, `AB 26` for
`AB 28`, `AB 85` for `A 301`, `AB 46` for `AB 54`, `AB 49` for `AB 57`.

## The smoking gun — site-concentrated over-attribution

| Sign | Corpus occurrences | Correct form | Correct occurrences | Concentration |
|------|-------------------|-------------|--------------------|----------------|
| AB 85 | 274 | A 301 | **1** | **231/274 (84%) at Haghia Triada - Portico 11** |
| AB 26 | 193 | AB 28 | 14 | — |
| AB 51 | 165 | AB 59 | 96 | — |
| AB 49 | 169 | AB 57 | 73 | — |
| AB 46 | 48 | AB 54 | 36 | — |

**8.4% of all syllabogram occurrences (849/10,048) are in the 5 potentially
mis-identified signs.** AB 85's concentration at a single site (84% at one
Haghia Triada findspot) is statistically absurd for a real sign — it's a
systematic transcription error.

## What this invalidates

1. **Avenue 7 (libation formula)** — the recurring "formula" was an artifact
   of the corpus's consistent mis-transcription of IOZa2/3. The real formula
   words (ja-sa-sa-ra-me, u-na-ka-na-si) do NOT appear in the corpus because
   the corpus transcribes those texts differently. **Retracted.**
2. **Avenue 1 (AB 85 word divider)** — AB 85 is massively over-attributed
   (274 vs correct 1). The "positional anomaly" of AB 85 was largely an
   artifact of this. **Retracted.**
3. **Frequency-based findings** — the diachronic prior, toponyms, and
   misvalued-sign flags all use sign frequencies. If the mis-identification
   is widespread (not just libation texts), these are all contaminated.
   **Must be re-verified against corrected transcriptions.**

## The reframe

The project's core assumption — that the corpus's sign identification is
reliable — is **wrong**. The corpus has a systematic bias: it over-uses a
handful of frequent signs (AB 85, AB 26, AB 51, AB 49) at the expense of
visually-similar counterparts (A 301, AB 28, AB 59, AB 57). This explains why
so many statistical findings were circular or failed: **they were analyzing
the transcription bias, not the script.**

## Next steps

1. **Quantify the full scope.** Systematically compare the corpus's
   transcription of key texts (especially Haghia Triada, Iouktas, Palaikastro)
   against GORILA/published readings to measure the error rate.
2. **Re-verify the diachronic prior** on a cleaned subset (excluding the
   mis-identified signs) — does it still hold?
3. **Re-verify the toponyms** (pa-i-to, i-da) — do they survive on corrected
   transcriptions?
4. **Correct the corpus** — the highest-value action in the project. A
   corrected corpus would re-validate (or re-invalidate) every finding.
