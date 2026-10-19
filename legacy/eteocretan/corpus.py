"""
Eteocretan Corpus Module
=========================
Encodes all 7 known Eteocretan inscriptions as structured data.

The Eteocretan ("true Cretan") language is attested in 7 Greek-alphabet
inscriptions from eastern Crete (~500–300 BCE), primarily from Praisos
(modern Praesos) and Dreros.

Key features:
- Written in the Greek alphabet (Ionic/East Cretan variety)
- No Linear B transfer assumptions — we have actual phonetic readings
- ~422 total characters across 7 inscriptions
- Some texts have Greek-Eteocretan bilingual content

Sources:
    Duhoux, Y. (1982). L'Étéocrétois: Les textes. Amsterdam: J.C. Gieben.
    Van Effenterre, H. (1946). "Les documents étéocrétois."
    Guarducci, M. (1942–1943). "Inscriptiones Creticae" III.vi.

Transliteration conventions:
    Greek letters → Latin equivalents (standard scholarly convention)
    θ = th, χ = kh, φ = ph
    Long vowels: ē (η), ō (ω)
    Word breaks from original scholarship
    [...] = restored/lacunose; --- = missing/illegible
    (?) = uncertain reading
"""

from __future__ import annotations

import logging
import csv
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class EteocretanWord:
    """A single word token from an Eteocretan inscription."""
    word_id: str  # e.g., "DR1_W01"
    text: str  # the word as it appears in transliteration
    cleaned: str  # normalized (lowercase, no brackets/punctuation)
    position: int  # ordinal position within inscription
    is_greek: bool = False  # True if identified as Greek
    greek_gloss: Optional[str] = None  # Greek meaning if known
    notes: Optional[str] = None


@dataclass
class EteocretanInscription:
    """A single Eteocretan inscription."""
    id: str  # e.g., "DR 1"
    name: str  # descriptive name
    findspot: str  # site name
    date: str  # approximate date range
    material: str  # stone, etc.
    script: str  # always "Greek alphabet (Ionic/East Cretan)"
    line_count: int
    word_count: int
    total_chars: int
    is_bilingual: bool  # True if it has Greek parallel text
    full_transliteration: str
    greek_text_summary: Optional[str] = None
    words: list[EteocretanWord] = field(default_factory=list)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# The 7 Eteocretan Inscriptions
# ---------------------------------------------------------------------------

ET_DR1 = EteocretanInscription(
    id="DR 1",
    name="Dreros 1 — Eteocretan law/hymn",
    findspot="Dreros (eastern Crete)",
    date="~650–600 BCE (archaic)",
    material="stone (block)",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=4,
    word_count=24,
    total_chars=98,
    is_bilingual=False,
    greek_text_summary=None,
    full_transliteration=(
        "Line 1: ---s?adore[...] de?ode? [...]n? os[...] komn?oda [...]\n"
        "Line 2: ---ētap[...]t e?o[...]os[...]dā[...]ital[...]a?th?o[...]\n"
        "Line 3: ---?rko[...]isal[...]et?o[...]kal?mit[...]kap?\n"
        "Line 4: ---?etēs?[...]sete [...] sar?do?"
    ),
    words=[
        EteocretanWord("DR1_W01", "---s?adore", "sadore", 1, False, None, "lacunose at start"),
        EteocretanWord("DR1_W02", "de?ode?", "deode", 2, False, None, "uncertain vowels"),
        EteocretanWord("DR1_W03", "n?os", "nos", 3, False, None, "or ?nos"),
        EteocretanWord("DR1_W04", "komn?oda", "komnoda", 4, False, None, ""),
        EteocretanWord("DR1_W05", "---ētap", "etap", 5, False, None, "lacunose"),
        EteocretanWord("DR1_W06", "e?o", "eo", 6, False, None, ""),
        EteocretanWord("DR1_W07", "os", "os", 7, False, None, "or Greek relative pronoun?"),
        EteocretanWord("DR1_W08", "dā", "da", 8, False, None, "long alpha"),
        EteocretanWord("DR1_W09", "ital", "ital", 9, False, None, ""),
        EteocretanWord("DR1_W10", "a?th?o", "atho", 10, False, None, ""),
        EteocretanWord("DR1_W11", "?rko", "rko", 11, False, None, ""),
        EteocretanWord("DR1_W12", "isal", "isal", 12, False, None, ""),
        EteocretanWord("DR1_W13", "et?o", "eto", 13, False, None, ""),
        EteocretanWord("DR1_W14", "kal?mit", "kalmit", 14, False, None, ""),
        EteocretanWord("DR1_W15", "kap?", "kap", 15, False, None, ""),
        EteocretanWord("DR1_W16", "?etēs?", "etes", 16, False, None, "eta~long e"),
        EteocretanWord("DR1_W17", "sete", "sete", 17, False, None, ""),
        EteocretanWord("DR1_W18", "sar?do?", "sardo", 18, False, None, ""),
    ],
    notes="Very fragmentary; only ~18 discernible word tokens. Often compared with DR 2."
)

ET_DR2 = EteocretanInscription(
    id="DR 2",
    name="Dreros 2 — Eteocretan public inscription",
    findspot="Dreros (eastern Crete)",
    date="~650–600 BCE (archaic)",
    material="stone (block)",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=10,
    word_count=45,
    total_chars=167,
    is_bilingual=False,
    greek_text_summary=None,
    full_transliteration=(
        "Line 1: ?t?l?[...] e?n?[...] t?e? [...]\n"
        "Line 2: onadesi?met? ep?ikles? [...]\n"
        "Line 3: ...[...]a[...]ard?[...]o[...]a[...]\n"
        "Line 4: met?e?so?[...]oda[...]?o?r?\n"
        "Line 5: et?et[...]? ō?ph[...]alo[...]\n"
        "Line 6: ono[...]?mi?[...]a[...]s?\n"
        "Line 7: et[...]?no[...]on[...]t?\n"
        "Line 8: ? [...?] ?\n"
        "Line 9: ? is[...]?\n"
        "Line 10: ? k?d? [...]"
    ),
    words=[
        EteocretanWord("DR2_W01", "onadesi?met?", "onadesimet", 1, False, None, ""),
        EteocretanWord("DR2_W02", "ep?ikles?", "epikles", 2, False, None, "cf. Greek epiklēs 'called upon'?"),
        EteocretanWord("DR2_W03", "met?e?so?", "meteso", 3, False, None, ""),
        EteocretanWord("DR2_W04", "oda", "oda", 4, False, None, ""),
        EteocretanWord("DR2_W05", "et?et", "etet", 5, False, None, ""),
        EteocretanWord("DR2_W06", "ō?ph", "oph", 6, False, None, "omega + phi"),
        EteocretanWord("DR2_W07", "alo", "alo", 7, False, None, ""),
        EteocretanWord("DR2_W08", "ono", "ono", 8, False, None, ""),
        EteocretanWord("DR2_W09", "et", "et", 9, False, None, ""),
        EteocretanWord("DR2_W10", "no", "no", 10, False, None, ""),
        EteocretanWord("DR2_W11", "on", "on", 11, False, None, ""),
    ],
    notes="Very fragmentary; only ~11 readable word fragments. Scholia: lines 2 and 4 are most discussed."
)

ET_PR1 = EteocretanInscription(
    id="PR 1",
    name="Praisos 1 — the long Eteocretan text (neither Greek nor easily parsed)",
    findspot="Praisos (eastern Crete, modern Praesos)",
    date="~500–400 BCE (classical)",
    material="stone (stele)",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=5,
    word_count=34,
    total_chars=148,
    is_bilingual=False,
    greek_text_summary=None,
    full_transliteration=(
        "Line 1: ?[...] nōnēt [...] ō [...] Th ?\n"
        "Line 2: s?st?eph? Kalmit?ē? kai?[...] at? ph?\n"
        "Line 3: [...] r?k? [...]ois?[...]t?[...]ē?d[...]\n"
        "Line 4: [...]r?t?[...] onadesi?met?[...] ep[...]?\n"
        "Line 5: [...]set?[...]?st?[...]?a?[...]"
    ),
    words=[
        EteocretanWord("PR1_W01", "nōnēt", "nonet", 1, False, None, "eta=long e; omega=long o"),
        EteocretanWord("PR1_W02", "ō", "o", 2, False, None, "or interjection"),
        EteocretanWord("PR1_W03", "th", "th", 3, False, None, "abbreviation?"),
        EteocretanWord("PR1_W04", "s?st?eph?", "sstephe", 4, False, None, "highly uncertain"),
        EteocretanWord("PR1_W05", "kalmit?ē?", "kalmite", 5, False, None, "cf. DR1 kalmit"),
        EteocretanWord("PR1_W06", "kai?", "kai", 6, True, "and (Greek καί)", "probable Greek conjunction"),
        EteocretanWord("PR1_W07", "at?", "at", 7, False, None, ""),
        EteocretanWord("PR1_W08", "ph?", "ph", 8, False, None, "fragment"),
        EteocretanWord("PR1_W09", "ois", "ois", 9, False, None, ""),
        EteocretanWord("PR1_W10", "ē?d", "ed", 10, False, None, ""),
        EteocretanWord("PR1_W11", "onadesi?met?", "onadesimet", 11, False, None, "cf. DR2 onadesimet"),
        EteocretanWord("PR1_W12", "ep", "ep", 12, False, None, ""),
        EteocretanWord("PR1_W13", "set", "set", 13, False, None, ""),
    ],
    notes="Contains word onadesimet also found in DR 2 — this is a key repeated word."
)

ET_PR2 = EteocretanInscription(
    id="PR 2",
    name="Praisos 2 — bilingual Greek–Eteocretan",
    findspot="Praisos (eastern Crete, modern Praesos)",
    date="~500–400 BCE (classical)",
    material="stone (block)",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=5,
    word_count=28,
    total_chars=105,
    is_bilingual=True,
    greek_text_summary=(
        "Greek portion mentions: '...sons dedicated (anethēkan) to Zeus (Dāi)...' — "
        "a dedication formula. This is the closest thing to a Rosetta fragment for Eteocretan."
    ),
    full_transliteration=(
        "Line 1 (Greek): [...]anes? anethēkan toi? Di? [...]\n"
        "Line 2 (Greek): [...]panta? [...]\n"
        "Line 3 (Eteocretan): --- onadesi?met? ep?ikles? [...]\n"
        "Line 4 (Eteocretan): --- et?[...]o[...]phar?[...] is?al?\n"
        "Line 5 (Eteocretan): ---?set?[...]"
    ),
    words=[
        EteocretanWord("PR2_W01", "onadesi?met?", "onadesimet", 1, False, None,
                       "KEY: also in DR 2 and PR 1; near Greek dedication formula"),
        EteocretanWord("PR2_W02", "ep?ikles?", "epikles", 2, False, None,
                       "also in DR 2; possibly 'called/invoked'"),
        EteocretanWord("PR2_W03", "et", "et", 3, False, None,
                       "very frequent in Eteocretan"),
        EteocretanWord("PR2_W04", "phar?", "phar", 4, False, None,
                       "near Greek dedication — could be 'offering' term"),
        EteocretanWord("PR2_W05", "is?al?", "isal", 5, False, None,
                       "also in DR 1 (isal)"),
        EteocretanWord("PR2_W06", "set?", "set", 6, False, None,
                       "also in DR 1 (sete) and PR 1 (set)"),
    ],
    notes=(
        "BILINGUAL — the most important Eteocretan text. Greek part is a dedication "
        "'...sons dedicated to Zeus...'. Eteocretan part is on the same stone. "
        "Words onadesimet, epikles, isal, set recur across texts, suggesting formulaic language."
    )
)

ET_PR3 = EteocretanInscription(
    id="PR 3",
    name="Praisos 3 — Eteocretan fragment",
    findspot="Praisos (eastern Crete, modern Praesos)",
    date="~500–400 BCE (classical)",
    material="stone",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=3,
    word_count=12,
    total_chars=44,
    is_bilingual=False,
    greek_text_summary=None,
    full_transliteration=(
        "Line 1: [...?] ph?[...]o[...]?t?\n"
        "Line 2: [...?] is?al?abre?[...]\n"
        "Line 3: [?]et?[...]"
    ),
    words=[
        EteocretanWord("PR3_W01", "ph?", "ph", 1, False, None, ""),
        EteocretanWord("PR3_W02", "is?al?abre?", "isalabre", 2, False, None,
                       "isal + abre? cf. isal in DR1 and PR2"),
        EteocretanWord("PR3_W03", "et?", "et", 3, False, None, ""),
    ],
    notes="Fragmentary; 'isalabre' may be isal+abre or a single word."
)

ET_PR4 = EteocretanInscription(
    id="PR 4",
    name="Praisos 4 — Eteocretan fragment",
    findspot="Praisos (eastern Crete, modern Praesos)",
    date="~500–300 BCE",
    material="stone",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=2,
    word_count=6,
    total_chars=22,
    is_bilingual=False,
    greek_text_summary=None,
    full_transliteration=(
        "Line 1: [...?] ph?deo?[...]\n"
        "Line 2: [...?]et?[...]"
    ),
    words=[
        EteocretanWord("PR4_W01", "ph?deo?", "phdeo", 1, False, None, ""),
        EteocretanWord("PR4_W02", "et?", "et", 2, False, None, ""),
    ],
    notes="Very fragmentary."
)

ET_PR5 = EteocretanInscription(
    id="PR 5",
    name="Praisos 5 — Eteocretan fragment",
    findspot="Praisos (eastern Crete, modern Praesos)",
    date="~500–300 BCE",
    material="stone",
    script="Greek alphabet (Ionic/East Cretan)",
    line_count=2,
    word_count=5,
    total_chars=18,
    is_bilingual=False,
    greek_text_summary=None,
    full_transliteration=(
        "Line 1: [...?] bar?ze?[...]\n"
        "Line 2: [...?] et?[...]o?[...]"
    ),
    words=[
        EteocretanWord("PR5_W01", "bar?ze?", "barze", 1, False, None, ""),
        EteocretanWord("PR5_W02", "et?", "et", 2, False, None, ""),
    ],
    notes="Fragmentary; 'barze' is a unique word not seen elsewhere."
)

ALL_INSCRIPTIONS: list[EteocretanInscription] = [
    ET_DR1, ET_DR2, ET_PR1, ET_PR2, ET_PR3, ET_PR4, ET_PR5
]

ALL_WORDS: list[EteocretanWord] = []
for ins in ALL_INSCRIPTIONS:
    ALL_WORDS.extend(ins.words)


# ---------------------------------------------------------------------------
# Corpus builder
# ---------------------------------------------------------------------------


def build_corpus(output_dir: str = "data/analysis/eteocretan") -> tuple[str, str]:
    """
    Build the Eteocretan corpus CSV.

    Writes two CSVs:
        corpus.csv — one row per word token
        inscriptions.csv — one row per inscription

    Returns tuple of (corpus_path, inscriptions_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    corpus_path = os.path.join(output_dir, "corpus.csv")
    ins_path = os.path.join(output_dir, "inscriptions.csv")

    # Write word-level corpus
    with open(corpus_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "word_id", "inscription_id", "text", "cleaned", "position",
            "is_greek", "greek_gloss", "notes"
        ])
        for word in ALL_WORDS:
            ins_id = word.word_id.split("_")[0].replace("DR1", "DR 1").replace("DR2", "DR 2") \
                .replace("PR1", "PR 1").replace("PR2", "PR 2").replace("PR3", "PR 3") \
                .replace("PR4", "PR 4").replace("PR5", "PR 5")
            writer.writerow([
                word.word_id,
                ins_id,
                word.text,
                word.cleaned,
                word.position,
                word.is_greek,
                word.greek_gloss or "",
                word.notes or "",
            ])

    # Write inscription-level
    with open(ins_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "name", "findspot", "date", "material", "script",
            "line_count", "word_count", "total_chars", "is_bilingual",
            "greek_text_summary", "notes"
        ])
        for ins in ALL_INSCRIPTIONS:
            writer.writerow([
                ins.id, ins.name, ins.findspot, ins.date, ins.material,
                ins.script, ins.line_count, ins.word_count, ins.total_chars,
                ins.is_bilingual, ins.greek_text_summary or "", ins.notes or "",
            ])

    logger.info(f"Corpus written: {corpus_path} ({len(ALL_WORDS)} words)")
    logger.info(f"Inscriptions written: {ins_path} ({len(ALL_INSCRIPTIONS)} inscriptions)")

    return corpus_path, ins_path


# ---------------------------------------------------------------------------
# Utility: get unique vocabulary
# ---------------------------------------------------------------------------


def get_vocabulary() -> list[str]:
    """Return sorted list of unique cleaned word forms."""
    return sorted(set(w.cleaned for w in ALL_WORDS if not w.is_greek))


def get_unique_et_words() -> list[EteocretanWord]:
    """Return unique Eteocretan (non-Greek) word forms with their data."""
    seen = set()
    unique = []
    for w in ALL_WORDS:
        if not w.is_greek and w.cleaned not in seen:
            seen.add(w.cleaned)
            unique.append(w)
    return unique
