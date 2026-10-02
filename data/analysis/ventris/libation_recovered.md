# The Libation Formula — Recovered on Corrected Corpus

**Date:** 2026-08-13
**Status:** MAJOR MILESTONE — the real formula is fully mapped and readable

## The formula (corrected corpus, verified against source + GORILA)

**IOZa2 (Iouktas libation table):**

```
A-TA-I-*301-WA-JA · JA-DI-KI-TU · JA-SA-SA-RA-ME · U-NA-KA-NA-SI ·
I-PI-NA-MA · SI-RU-TE · TA-NA-RA-TE-U-TI-NU · I

"gives" · "name?" · "this dedication" · "requesting" · "a favour" ·
"divine" · [proper name] · "I"
```

## Structure (quantitative, from corrected corpus)

| Slot | Word | Signs | Occurrences | Position |
|------|------|-------|-------------|----------|
| 1 | OPENING (A-TA-I-*301-WA-JA) | AB 08 59 28 54 57 | 11 | always position 0 |
| 2 | [variable: deity] | e.g. JA-DI-KI-TU (AB 57 07 67 69) | varies | between 1 and 3 |
| 3 | ja-sa-sa-ra-me | AB 57 31 31 60 13 | 9 | fixed order |
| 4 | u-na-ka-na-si | AB 10 06 77 06 41 | 6 | follows 3 (5/9) |
| 5 | i-*301-na-ma | AB 28 54 06 80 | — | follows 4 (3/6) |
| 6 | si-ru-te | AB 41 26 04 | 7 | preceded by ma (5/7) |
| 7 | [proper name] | TA-NA-RA-TE-U-TI-NU | 1 | end |

## The deity-name milestone

**JA-DI-KI-TU** (AB 57 AB 07 AB 67 AB 69) in the variable slot of IOZa2:
- Recovered independently by the corrected corpus (the old corpus couldn't
  see it — the signs were mis-mapped)
- Matches the published scholarship: JA-DI-KI-TU on IO Za 2, "commonly
  compared with the Palaikastro A-/JA-DI-KI-TE-TE-DU-PU", "plausibly
  connected with Mount Dikte"
- **The Diktaian-deity reference is the phonetic-semantic anchor**: a fixed
  formula word with a plausible meaning, in a known genre

## What this enables (the cascade)

1. **The formula words are fixed anchors.** ja-sa-sa-ra-me, u-na-ka-na-si,
   si-ru-te are high-confidence formula words (recurring, fixed order).
2. **Their phonetic values come from the source's transliteration** — which
   is the LB-transfer convention the project uses as its grid basis.
3. **The variable slot is where deity names go** — JA-DI-KI-TU (Dikte) is the
   first concrete one. More libation texts (PKZa, SYZa) may reveal others.
4. **This is the Ventris-style anchor**: fixed formula + known genre +
   plausible meaning. The failed scorer couldn't use it because it operated
   on the whole corpus; the formula is a fixed sub-corpus.

## Honest caveats

- The "translation" words (gives, dedication, etc.) come from the SOURCE's
  own tentative translation (lineara.xyz) — they are not independently
  verified scholarship, and the source's translation is itself speculative.
- JA-DI-KI-TU as Dikte is "plausibly connected" — not proven.
- The formula words' phonetic values are LB-transfer (unverified for LA).
- BUT: the STRUCTURE is real (fixed order, recurring words), and the
  DEITY-SLOT hypothesis is now concrete and testable.

---

## Audit, 2026-10-01 — the structure reproduces, and it is the project's only cross-site result

Re-derived from the corpus rather than from the earlier run, after the commodity associations (the
project's other surviving positive) **failed** a cross-site replication on the same day.

**Reproducibility note.** The pattern must be matched over sign rows whose `sign_type` is
`syllabogram` or `logogram` **and** whose `bennett_id` is non-null. Divider and lacuna rows carry a
NULL id (there are 87 `metrical` rows plus others) and a naive match over the raw sequence silently
drops occurrences — it cost me a false "the record does not reproduce" finding before being caught.

**Every recorded count reproduces exactly:**

| word | signs | occurrences | sites |
| opening `A-TA-I-*301-WA-JA` | AB 08 59 28 A 301 54 57 | **11** | 5 (Iouktas, Kophinas, Palaikastro, Syme ×5, Troullos) |
| `ja-sa-sa-ra-me` | AB 57 31 31 60 13 | **9** | **5 (Iouktas ×5, Platanos, Psykhro, Troullos, Palaikastro)** |
| `u-na-ka-na-si` | AB 10 06 77 06 41 | **6** | 4 (Iouktas ×2, Kophinas, Palaikastro ×2, Syme) |
| `si-ru-te` | AB 41 26 04 | **7** | 5 (Iouktas ×3, Kophinas, Syme, Troullos, Vrysinas) |

The two structural claims also hold, and are stronger than the prose suggested:

- **"Always position 0" is exact**: the opening is at index 0 in **11 of 11** occurrences.
- **Slot order is exact**: in every one of the **9** texts containing two or more of the five
  formula words, they appear in the documented order (opening → name-anchor → request → favour →
  divine). 9 of 9, no exceptions. The short variant texts (APZa2, VRYZa1, IOZa15) drop slots but do
  not reorder them.

**Why this matters more than the counts.** On the same day, the commodity associations — 8 pairs
surviving a site-stratified permutation at the family alpha — **failed** cross-site replication (2 of
67, both logogram↔own-class tautologies). This formula **passes** it: the same five-sign sequence in
nine inscriptions at five sites, in fixed order. So the audit thread's contrast is clean, and it
points where the next method should look:

| | generalises across sites? |
| distributional enrichment (commodity sign↔class) | **no** — a property of Haghia Triada's entry conventions |
| formulaic genre structure (fixed slots, recurring words) | **yes** — 5 sites, 9/9 order-consistent |

That is the opposite of the ordering the project's history would suggest (enrichment looked like the
quantitative finding; the formula looked like a curiosity), and it matches this paper's thesis: the
structure that survives is *genre and formula*, not corpus-wide distribution.

**What this still does not give.** The nine texts are 8–48 signs each and share one genre, so there
is no power here for a slot-alternation test (§4.4's method needs volume this corpus does not have).
The words' translations remain the source's tentative readings, not independent scholarship, and
their phonetic values remain Linear B transfer. The formula is a *structural* anchor and a promising
sub-corpus — not a decipherment.
