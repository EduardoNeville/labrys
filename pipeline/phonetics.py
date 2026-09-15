"""Canonical phonetic-value helpers — single source of truth.

Before this module the same logic existed in four places and drifted:

  * `pipeline/ventris/complete.py`      — CONS_SERIES_MAP missing 18 of 74
    Linear B values (incl. `no`, `po`, `pe`), `vowel_of` returning "?" for
    every subscripted value
  * `pipeline/formulaic/analyze.py`     — duplicate `vowel_of`, same subscript bug
  * `pipeline/ventris/positional_oracle.py` — duplicate `vowel_of`, same bug
  * `pipeline/frequency_constraints/constrain.py` — `parse_cv` returned the
    vowel as "a2"/"u2" for subscripted values, which then failed the
    `in VOWELS` check, silently dropping the vowel constraint

Everything now imports from here. See `data/analysis/ventris/oracle_repair_report.md`
for how the drift was found, and `data/analysis/ventris/verification_audit.md` for
the affected data products.
"""

from __future__ import annotations

# 8 consonant series (rows) × 5 vowel columns
CONSONANT_SERIES = ["VOWEL", "LABIAL", "DENTAL", "VELAR", "SIBILANT", "LIQUID",
                    "PALATAL", "SEMIVOWEL"]
VOWEL_COLUMNS = ["a", "e", "i", "o", "u"]

# Consonant-to-series mapping for each phonetic value.
# Covers all 74 Linear B syllabogram values named in Unicode plus the Linear A
# grid's values. Values absent here silently cannot earn a series vote anywhere
# in the pipeline (this is defects 4 in the repair report).
CONS_SERIES_MAP = {
    # VOWEL only (no consonant onset)
    "a": "VOWEL", "e": "VOWEL", "i": "VOWEL", "o": "VOWEL", "u": "VOWEL",
    # LABIAL
    "pa": "LABIAL", "pi": "LABIAL", "pu": "LABIAL",
    "ma": "LABIAL", "me": "LABIAL", "mi": "LABIAL", "mo": "LABIAL", "mu": "LABIAL",
    "wa": "SEMIVOWEL", "wi": "SEMIVOWEL", "wo": "SEMIVOWEL", "we": "SEMIVOWEL",
    # DENTAL (stops + nasals)
    "ta": "DENTAL", "te": "DENTAL", "ti": "DENTAL", "to": "DENTAL", "tu": "DENTAL",
    "da": "DENTAL", "de": "DENTAL", "di": "DENTAL", "do": "DENTAL", "du": "DENTAL",
    "na": "DENTAL", "ne": "DENTAL", "ni": "DENTAL", "nu": "DENTAL", "no": "DENTAL",
    "ra": "LIQUID", "re": "LIQUID", "ri": "LIQUID", "ro": "LIQUID", "ru": "LIQUID",
    "la": "LIQUID",
    # SIBILANT
    "sa": "SIBILANT", "se": "SIBILANT", "si": "SIBILANT", "so": "SIBILANT",
    "su": "SIBILANT",
    "za": "SIBILANT", "ze": "SIBILANT", "zo": "SIBILANT",
    # VELAR
    "ka": "VELAR", "ke": "VELAR", "ki": "VELAR", "ko": "VELAR", "ku": "VELAR",
    "qa": "VELAR", "qe": "VELAR", "qi": "VELAR", "qo": "VELAR",
    # PALATAL
    "ja": "PALATAL", "je": "PALATAL", "jo": "PALATAL", "ju": "PALATAL",
    # complex / rare values
    "pe": "LABIAL", "po": "LABIAL",
    "a2": "VOWEL", "a3": "VOWEL", "au": "VOWEL",
    "dwe": "DENTAL", "dwo": "DENTAL", "twe": "DENTAL", "two": "DENTAL",
    "nwa": "DENTAL", "pte": "LABIAL",
    "pu2": "LABIAL", "ra2": "LIQUID", "ra3": "LIQUID", "ro2": "LIQUID",
    "ta2": "DENTAL",
    # Linear A value absent from the Linear B syllabary (no *lo in LB). If a sign
    # is read 'lo' it is a liquid by definition, so the series is unambiguous.
    "lo": "LIQUID",
}

# Unicode subscript digits → ASCII, so ₀-₉ subscripts are handled like 0-9.
_SUBDIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def strip_subscript(val: str) -> str:
    """Lower-case a value, dropping trailing subscript digits and uncertainty marks.

    Subscript digits mark a DISTINCT sign (ra2 ≠ ra) but are not part of the
    consonant or the vowel. A trailing '?' (e.g. 'zo?') marks the value as
    uncertain — it is the same value, not a different one.
    """
    v = (val or "").strip().lower().translate(_SUBDIGITS).rstrip("?").strip()
    while v and v[-1].isdigit():
        v = v[:-1]
    return v


def vowel_of(val: str) -> str:
    """Vowel column of a phonetic value, or '?' if it has none."""
    v = strip_subscript(val)
    if not v:
        return "?"
    if len(v) == 1:
        return v if v in "aeiou" else "?"
    if len(v) == 2:
        return v[1] if v[1] in "aeiou" else v[0]
    return v[-1] if v[-1] in "aeiou" else "?"


def series_of(val: str) -> str:
    """Consonant series of a phonetic value, or '?' if unmapped."""
    return CONS_SERIES_MAP.get(strip_subscript(val), "?")


def _selfcheck() -> None:
    # the 18 values that were missing must all resolve
    for v in ("no", "po", "pe", "qo", "a2", "a3", "au", "dwe", "dwo", "nwa",
              "pu2", "pte", "ra2", "ra3", "ro2", "ta2", "twe", "two"):
        assert series_of(v) != "?", f"{v} unmapped"
    # subscripted values must yield the right vowel, not '?'
    assert vowel_of("ra2") == "a" and vowel_of("ro2") == "o"
    assert vowel_of("ta2") == "a" and vowel_of("pu2") == "u"
    assert vowel_of("a2") == "a" and vowel_of("a3") == "a"
    assert vowel_of("nwa") == "a" and vowel_of("dwe") == "e"
    assert vowel_of("au") == "u"
    # unicode subscripts
    assert vowel_of("ra₂") == "a" and series_of("ro₂") == "LIQUID"
    # a '?' suffix marks uncertainty on the same value ('zo?' is 'zo')
    assert series_of("zo?") == "SIBILANT" and vowel_of("ra2?") == "a"
    # plain values unchanged
    assert vowel_of("da") == "a" and series_of("da") == "DENTAL"
    assert vowel_of("?") == "?" and series_of("?") == "?"
    assert len(CONS_SERIES_MAP) >= 74, len(CONS_SERIES_MAP)
    print(f"phonetics selfcheck OK — {len(CONS_SERIES_MAP)} values mapped")


if __name__ == "__main__":
    _selfcheck()
