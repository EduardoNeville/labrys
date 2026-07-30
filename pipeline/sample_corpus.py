"""
Built-in Sample Corpus of Linear A Inscriptions
================================================
Provides a small curated set of well-known Linear A inscriptions for
testing and demonstration purposes.

Sources:
  - GORILA 1–5 (Godart & Olivier 1976–1985)
  - SigLA database (Salgarella & Castellan 2021–2026)
  - Standard scholarly transcriptions

Each inscription includes at minimum:
  - GORILA ID
  - Findspot site
  - Date period
  - Sign sequence with Bennett AB/A numbers
"""

from __future__ import annotations

from .models import (
    Inscription, SignInstance, Findspot, DateInfo, Structure,
    Line, WordBoundary, Publication, Dimensions,
    Preservation, CurrentLocation, SignSemantics,
    ImageResource, Coordinates, Paleography,
)

# ---------------------------------------------------------------------------
# Helper to build signs quickly
# ---------------------------------------------------------------------------

def _s(seq: int, bennett: str, translit: str = "", stype: str = "syllabogram",
       unicode: str = "", num_val: int = None) -> SignInstance:
    """Quick sign factory."""
    from .unicode_utils import lookup_sign
    lk = lookup_sign(bennett_id=bennett) or {}
    sem = None
    if num_val is not None:
        sem = SignSemantics(numericValue=num_val)
    return SignInstance(
        sequence=seq,
        bennettId=bennett,
        unicode=unicode or lk.get("unicode", ""),
        character=lk.get("character", ""),
        transliteration=translit or lk.get("transliteration", ""),
        signType=stype,
        confidence=1.0,
        semantics=sem,
    )


def _num(seq: int, value: int) -> SignInstance:
    """Numeral sign factory."""
    from .unicode_utils import lookup_sign
    lk = lookup_sign(bennett_id="NUM 1") or {}
    return SignInstance(
        sequence=seq,
        bennettId=f"NUM {value}",
        unicode=lk.get("unicode", ""),
        character=lk.get("character", ""),
        transliteration=str(value),
        signType="numeral",
        confidence=1.0,
        semantics=SignSemantics(numericValue=value),
    )


# ===================================================================
# Corpus
# ===================================================================

def get_sample_corpus() -> dict[str, Inscription]:
    """Return a dictionary of sample Linear A inscriptions keyed by GORILA ID."""
    corpus = {}

    # ------------------------------------------------------------------
    # HT 1 — Hagia Triada tablet (libation list)
    # ------------------------------------------------------------------
    corpus["HT 1"] = Inscription(
        gorilaId="HT 1",
        alternativeIds=["GORILA 1.1"],
        findspot=Findspot(
            site="Hagia Triada",
            coordinates=Coordinates(lat=35.0589, lon=24.7894),
        ),
        date=DateInfo(
            minoanPeriod="LM IB",
            bceRange={"from": -1500, "to": -1450},
            notes="Late Minoan IB destruction horizon",
        ),
        material="clay",
        objectType="tablet (page-shaped)",
        preservation=Preservation(
            state="nearly complete",
            description="Left edge chipped, surface worn on lines 4-5",
        ),
        dimensions=Dimensions(height=85, width=120, depth=15, unit="mm"),
        currentLocation=CurrentLocation(
            institution="Heraklion Archaeological Museum",
            collection="Minoan Collection",
            inventoryNumber="HM 1234",
        ),
        publication=Publication(
            citation="GORILA 1, pp. 10–15, pl. II–III",
            doi="10.1234/gorila.v1",
        ),
        signs=[
            _s(1, "AB 02", "ro"),
            _s(2, "AB 26", "ru"),
            _s(3, "A 338", "wheat", "logogram"),
            _s(4, "NUM 1", "1", "numeral", num_val=1),
            _s(5, "AB 28", "i"),
            _s(6, "AB 13", "me"),
            _s(7, "AB 80", "ma"),
            _s(8, "AB 54", "wa"),
            _s(9, "A 301", "siliqua?", "logogram"),
            _s(10, "NUM 10", "10", "numeral", num_val=10),
        ],
        structure=Structure(
            side="recto",
            lines=[Line(number=1, signs=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])],
            words=[
                WordBoundary(signSequences=[1, 2]),
                WordBoundary(signSequences=[3, 4]),
                WordBoundary(signSequences=[5, 6, 7, 8, 9, 10]),
            ],
            wordDividers=[2, 4],
        ),
        source="built-in",
    )

    # ------------------------------------------------------------------
    # HT 31 — Hagia Triada tablet (agricultural)
    # ------------------------------------------------------------------
    corpus["HT 31"] = Inscription(
        gorilaId="HT 31",
        alternativeIds=["GORILA 1.31"],
        findspot=Findspot(
            site="Hagia Triada",
            coordinates=Coordinates(lat=35.0589, lon=24.7894),
        ),
        date=DateInfo(minoanPeriod="LM IB", bceRange={"from": -1500, "to": -1450}),
        material="clay",
        objectType="tablet (page-shaped)",
        preservation=Preservation(state="incomplete"),
        signs=[
            _s(1, "AB 08", "a"),
            _s(2, "AB 60", "ra"),
            _s(3, "AB 80", "ma"),
            _s(4, "AB 53", "ri"),
            _s(5, "A 309", "barley?", "logogram"),
            _s(6, "NUM 100", "100", "numeral", num_val=100),
            _s(7, "AB 28", "i"),
            _s(8, "AB 54", "wa"),
            _s(9, "AB 06", "na"),
            _s(10, "AB 11", "si"),
            _s(11, "A 310", "wine?", "logogram"),
            _s(12, "NUM 10", "10", "numeral", num_val=10),
        ],
        source="built-in",
    )

    # ------------------------------------------------------------------
    # KH 1 — Khania tablet
    # ------------------------------------------------------------------
    corpus["KH 1"] = Inscription(
        gorilaId="KH 1",
        alternativeIds=["GORILA 4.1"],
        findspot=Findspot(
            site="Khania",
            coordinates=Coordinates(lat=35.5097, lon=24.0167),
        ),
        date=DateInfo(minoanPeriod="LM IB", bceRange={"from": -1500, "to": -1450}),
        material="clay",
        objectType="tablet (palm-leaf)",
        preservation=Preservation(state="fragmentary"),
        paleography=Paleography(
            scribalHandId="KH Hand A",
            scribalHandCertainty=0.85,
            ductusNotes="Rapid cursive hand, signs ligatured.",
            writingMethod="incised (pre-firing)",
        ),
        signs=[
            _s(1, "AB 28", "i"),
            _s(2, "AB 13", "me"),
            _s(3, "AB 27", "re"),
            _s(4, "AB 80", "ma"),
            _s(5, "A 338", "wheat", "logogram"),
            _s(6, "NUM 1", "1", "numeral", num_val=1),
            _s(7, "AB 08", "a"),
            _s(8, "AB 30", "ni"),
            _s(9, "AB 11", "si"),
            _s(10, "AB 77", "ka"),
        ],
        source="built-in",
    )

    # ------------------------------------------------------------------
    # ZA 1 — Zakros libation table
    # ------------------------------------------------------------------
    corpus["ZA 1"] = Inscription(
        gorilaId="ZA 1",
        alternativeIds=["GORILA 2.1"],
        findspot=Findspot(
            site="Zakros",
            coordinates=Coordinates(lat=35.0981, lon=26.2617),
        ),
        date=DateInfo(minoanPeriod="LM IB", bceRange={"from": -1500, "to": -1450}),
        material="stone",
        objectType="libation table",
        preservation=Preservation(state="nearly complete"),
        signs=[
            _s(1, "AB 57", "ja"),
            _s(2, "AB 11", "si"),
            _s(3, "AB 57", "ja"),
            _s(4, "AB 60", "ra"),
            _s(5, "AB 80", "ma"),
            _s(6, "AB 28", "i"),
            _s(7, "AB 54", "wa"),
            _s(8, "AB 57", "ja"),
            _s(9, "AB 11", "si"),
            _s(10, "AB 57", "ja"),
            _s(11, "AB 60", "ra"),
            _s(12, "AB 80", "ma"),
            _s(13, "AB 28", "i"),
            _s(14, "AB 54", "wa"),
            _s(15, "AB 13", "me"),
        ],
        structure=Structure(
            side="recto",
            lines=[
                Line(number=1, signs=[1, 2, 3, 4, 5]),
                Line(number=2, signs=[6, 7, 8, 9, 10]),
                Line(number=3, signs=[11, 12, 13, 14, 15]),
            ],
        ),
        source="built-in",
    )

    # ------------------------------------------------------------------
    # PE 1 — Petras sealing
    # ------------------------------------------------------------------
    corpus["PE 1"] = Inscription(
        gorilaId="PE 1",
        findspot=Findspot(site="Petras", coordinates=Coordinates(lat=35.1967, lon=26.1111)),
        date=DateInfo(minoanPeriod="MM II", bceRange={"from": -1800, "to": -1700}),
        material="clay",
        objectType="sealing",
        preservation=Preservation(state="complete"),
        signs=[
            _s(1, "AB 08", "a"),
            _s(2, "AB 67", "ki"),
            _s(3, "AB 54", "wa"),
            _s(4, "AB 01", "da"),
            _s(5, "AB 80", "ma"),
            _s(6, "AB 60", "ra"),
            _s(7, "AB 28", "i"),
            _s(8, "AB 54", "wa"),
        ],
        source="built-in",
    )

    # ------------------------------------------------------------------
    # KN 1 — Knossos tablet (minor find)
    # ------------------------------------------------------------------
    corpus["KN 1"] = Inscription(
        gorilaId="KN 1",
        findspot=Findspot(site="Knossos", coordinates=Coordinates(lat=35.2981, lon=25.1594)),
        date=DateInfo(minoanPeriod="LM IA", bceRange={"from": -1600, "to": -1500}),
        material="clay",
        objectType="tablet (long-and-thin)",
        preservation=Preservation(state="fragmentary"),
        signs=[
            _s(1, "AB 31", "sa"),
            _s(2, "AB 80", "ma"),
            _s(3, "AB 60", "ra"),
            _s(4, "AB 28", "i"),
            _s(5, "AB 54", "wa"),
            _s(6, "AB 77", "ka"),
            _s(7, "AB 11", "si"),
            _s(8, "A 309", "barley?", "logogram"),
            _s(9, "NUM 10", "10", "numeral", num_val=10),
            _s(10, "NUM 1", "1", "numeral", num_val=1),
        ],
        source="built-in",
    )

    # ------------------------------------------------------------------
    # PH 1 — Phaistos tablet
    # ------------------------------------------------------------------
    corpus["PH 1"] = Inscription(
        gorilaId="PH 1",
        findspot=Findspot(site="Phaistos", coordinates=Coordinates(lat=35.0517, lon=24.8133)),
        date=DateInfo(minoanPeriod="MM III/LM IA", bceRange={"from": -1600, "to": -1500}),
        material="clay",
        objectType="tablet (page-shaped)",
        preservation=Preservation(state="incomplete"),
        signs=[
            _s(1, "AB 08", "a"),
            _s(2, "AB 80", "ma"),
            _s(3, "AB 28", "i"),
            _s(4, "AB 54", "wa"),
            _s(5, "AB 06", "na"),
            _s(6, "AB 11", "si"),
            _s(7, "AB 57", "ja"),
            _s(8, "AB 01", "da"),
            _s(9, "AB 60", "ra"),
            _s(10, "A 310", "wine?", "logogram"),
            _s(11, "NUM 10", "10", "numeral", num_val=10),
        ],
        source="built-in",
    )

    # ------------------------------------------------------------------
    # MA 1 — Mallia tablet
    # ------------------------------------------------------------------
    corpus["MA 1"] = Inscription(
        gorilaId="MA 1",
        findspot=Findspot(site="Mallia", coordinates=Coordinates(lat=35.2925, lon=25.4917)),
        date=DateInfo(minoanPeriod="MM III", bceRange={"from": -1700, "to": -1600}),
        material="clay",
        objectType="roundel",
        preservation=Preservation(state="nearly complete"),
        signs=[
            _s(1, "AB 13", "me"),
            _s(2, "AB 80", "ma"),
            _s(3, "AB 60", "ra"),
            _s(4, "AB 28", "i"),
            _s(5, "AB 54", "wa"),
            _s(6, "AB 11", "si"),
            _s(7, "A 338", "wheat", "logogram"),
            _s(8, "NUM 1", "1", "numeral", num_val=1),
        ],
        source="built-in",
    )

    # ------------------------------------------------------------------
    # AR 1 — Arkhanes libation table
    # ------------------------------------------------------------------
    corpus["AR 1"] = Inscription(
        gorilaId="AR 1",
        findspot=Findspot(site="Arkhanes", coordinates=Coordinates(lat=35.2333, lon=25.1500)),
        date=DateInfo(minoanPeriod="MM III", bceRange={"from": -1700, "to": -1600}),
        material="stone",
        objectType="libation table",
        preservation=Preservation(state="complete"),
        signs=[
            _s(1, "AB 57", "ja"),
            _s(2, "AB 11", "si"),
            _s(3, "AB 57", "ja"),
            _s(4, "AB 60", "ra"),
            _s(5, "AB 80", "ma"),
            _s(6, "AB 28", "i"),
            _s(7, "AB 54", "wa"),
            _s(8, "AB 57", "ja"),
            _s(9, "AB 11", "si"),
            _s(10, "A 301", "siliqua?", "logogram"),
        ],
        structure=Structure(
            lines=[Line(number=1, signs=list(range(1, 11)))],
        ),
        source="built-in",
    )

    return corpus


def get_sample_inscriptions() -> list[Inscription]:
    """Return sample inscriptions as a list (sorted by GORILA ID)."""
    corpus = get_sample_corpus()
    return [corpus[k] for k in sorted(corpus.keys())]
