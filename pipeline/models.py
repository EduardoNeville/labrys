"""
Data Models for Linear A Inscriptions
======================================
Uses Pydantic (v2) for validation and serialization.
Mirrors the Unified Data Schema tiers (1–7) from the schema design.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Controlled vocabulary enums (mirroring the schema's SKOS concept schemes)
# ---------------------------------------------------------------------------

class MinoanPeriod(str, Enum):
    MM_II = "MM II"
    MM_III = "MM III"
    MM_III_LM_IA = "MM III/LM IA"
    LM_IA = "LM IA"
    LM_IB = "LM IB"
    LM_II = "LM II"
    LM_IIIA1 = "LM IIIA1"
    LM_IIIA2 = "LM IIIA2"
    LM_IIIB = "LM IIIB"
    MIXED = "Mixed"
    UNCERTAIN = "Uncertain"


class Material(str, Enum):
    CLAY = "clay"
    STONE = "stone"
    METAL = "metal"
    IVORY = "ivory"
    BONE = "bone"
    FRESCO = "fresco/plaster"
    POTTERY = "pottery/ceramic"
    GLASS = "glass"
    WOOD = "wood"


class ObjectType(str, Enum):
    TABLET_PAGE = "tablet (page-shaped)"
    TABLET_PALM = "tablet (palm-leaf)"
    TABLET_LONG = "tablet (long-and-thin)"
    ROUNDEL = "roundel"
    LIBATION_TABLE = "libation table"
    SEALING = "sealing"
    SEAL = "seal"
    POTTERY_VESSEL = "pottery vessel"
    FRESCO = "fresco"
    METAL_OBJECT = "metal object"
    BONE_LABEL = "bone label"
    IVORY_PLAQUE = "ivory plaque"
    STONE_VESSEL = "stone vessel"


class PreservationState(str, Enum):
    COMPLETE = "complete"
    NEARLY_COMPLETE = "nearly complete"
    INCOMPLETE = "incomplete"
    FRAGMENTARY = "fragmentary"
    SEVERELY_DAMAGED = "severely damaged"
    ERODED = "eroded"
    RECONSTRUCTED = "reconstructed"


class SignType(str, Enum):
    SYLLABOGRAM = "syllabogram"
    LOGOGRAM = "logogram"
    FRACTION = "fraction"
    NUMERAL = "numeral"
    ADJUNCT = "adjunct"
    LIGATURE = "ligature"
    WORD_DIVIDER = "word divider"
    PUNCTUATION = "punctuation"
    UNCERTAIN = "uncertain"


class WritingMethod(str, Enum):
    INCISED_PRE = "incised (pre-firing)"
    INCISED_POST = "incised (post-firing)"
    PAINTED = "painted (dipinto)"
    STAMPED = "stamped"
    CARVED = "carved"
    IMPRESSED = "impressed"


class ImageType(str, Enum):
    PHOTOGRAPH = "photograph"
    DRAWING = "drawing"
    MSI = "msi"
    INFRARED = "infrared"
    ULTRAVIOLET = "ultraviolet"
    RTI = "rti"
    MODEL_3D = "3d model"
    XRAY = "x-ray"
    CT_SCAN = "ct scan"


# ---------------------------------------------------------------------------
# Data models (dataclasses for simplicity; Pydantic can be swapped in)
# ---------------------------------------------------------------------------

@dataclass
class Coordinates:
    lat: float
    lon: float


@dataclass
class Findspot:
    site: str
    coordinates: Optional[Coordinates] = None
    context: Optional[str] = None


@dataclass
class DateInfo:
    minoanPeriod: str  # from MinoanPeriod enum values
    bceRange: Optional[dict] = None          # {"from": int, "to": int}
    notes: Optional[str] = None


@dataclass
class Dimensions:
    height: Optional[float] = None
    width: Optional[float] = None
    depth: Optional[float] = None
    diameter: Optional[float] = None
    unit: str = "mm"


@dataclass
class CurrentLocation:
    institution: Optional[str] = None
    collection: Optional[str] = None
    inventoryNumber: Optional[str] = None


@dataclass
class Preservation:
    state: str                      # from PreservationState enum values
    description: Optional[str] = None


@dataclass
class SignSemantics:
    logogramOf: Optional[str] = None
    commodity: Optional[str] = None
    fractionValue: Optional[str] = None
    numericValue: Optional[int] = None
    unit: Optional[str] = None
    metrologicalValue: Optional[str] = None


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float
    unit: str = "mm"


@dataclass
class SignCorrection:
    original: str
    correctedTo: str


@dataclass
class SignInstance:
    """A single sign occurrence on an inscription (Tier 2)."""
    sequence: int
    bennettId: str                         # e.g. "AB 02", "A 338"
    unicode: Optional[str] = None          # e.g. "U+10602"
    character: Optional[str] = None        # the literal Unicode char
    transliteration: Optional[str] = None  # phonetic reading
    confidence: Optional[float] = None     # 0.0 – 1.0
    signType: str = "syllabogram"          # from SignType enum values
    siglaVariantId: Optional[str] = None
    boundingBox: Optional[BoundingBox] = None
    shapeClass: Optional[str] = None
    isLigatureComponent: Optional[bool] = None
    ligatureOf: Optional[list[str]] = None
    erasure: Optional[bool] = None
    correction: Optional[SignCorrection] = None
    semantics: Optional[SignSemantics] = None


@dataclass
class Line:
    number: int | str
    signs: list[int] = field(default_factory=list)   # sign sequence numbers
    ruling: bool = False
    damaged: bool = False
    continuesFrom: Optional[str] = None


@dataclass
class WordBoundary:
    signSequences: list[int] = field(default_factory=list)


@dataclass
class Lacuna:
    signs: int
    position: int    # sign sequence index where gap occurs


@dataclass
class Structure:
    side: Optional[str] = None         # "recto" / "verso" / "edge"
    lines: list[Line] = field(default_factory=list)
    words: list[WordBoundary] = field(default_factory=list)
    wordDividers: list[int] = field(default_factory=list)  # sign seq indices
    lacunae: list[Lacuna] = field(default_factory=list)


@dataclass
class Paleography:
    scribalHandId: Optional[str] = None
    scribalHandCertainty: Optional[float] = None
    ductusNotes: Optional[str] = None
    writingMethod: Optional[str] = None


@dataclass
class LinearBRelation:
    dmicId: Optional[str] = None
    phoneticValue: Optional[str] = None


@dataclass
class Relations:
    linearB: list[LinearBRelation] = field(default_factory=list)
    cyproMinoan: list[dict] = field(default_factory=list)
    cretanHiero: list[dict] = field(default_factory=list)
    eteocretan: list[dict] = field(default_factory=list)
    scholarlyNotes: list[str] = field(default_factory=list)
    relatedInscriptions: list[str] = field(default_factory=list)


@dataclass
class ImageResource:
    iiifServiceUrl: Optional[str] = None
    iiifManifestUrl: Optional[str] = None
    credit: Optional[str] = None
    license: Optional[str] = None
    type: str = "photograph"     # from ImageType enum values
    msiBand: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class Publication:
    citation: str
    doi: Optional[str] = None


@dataclass
class BibliographyEntry:
    citation: str
    pages: Optional[str] = None


@dataclass
class Inscription:
    """
    Top-level inscription record covering all 7 tiers.

    This is the canonical in-memory representation.  It can be serialised
    to JSON-LD, TEI-XML, or plain text.
    """
    # Tier 1 — Text-Level Metadata
    gorilaId: str
    alternativeIds: list[str] = field(default_factory=list)
    findspot: Optional[Findspot] = None
    date: Optional[DateInfo] = None
    material: Optional[str] = None
    objectType: Optional[str] = None
    preservation: Optional[Preservation] = None
    dimensions: Optional[Dimensions] = None
    currentLocation: Optional[CurrentLocation] = None
    publication: Optional[Publication] = None
    bibliography: list[BibliographyEntry] = field(default_factory=list)

    # Tier 2 — Sign-Level Annotation
    signs: list[SignInstance] = field(default_factory=list)

    # Tier 3 — Paleographic Tier
    paleography: Optional[Paleography] = None

    # Tier 4 — Structural Tier
    structure: Optional[Structure] = None

    # Tier 5 — Semantic Tier (embedded in signs[].semantics)

    # Tier 6 — Relational Tier
    relations: Optional[Relations] = None

    # Tier 7 — Image Tier
    images: list[ImageResource] = field(default_factory=list)

    # Source tracking
    source: Optional[str] = None      # e.g. "sigla", "tei", "lineara.xyz"
    raw_data: Optional[dict] = None   # original source data for audit

    # ------------------------------------------------------------------
    def signs_by_type(self, sign_type: str) -> list[SignInstance]:
        """Filter signs by SignType value."""
        return [s for s in self.signs if s.signType == sign_type]

    def syllabograms(self) -> list[SignInstance]:
        return self.signs_by_type("syllabogram")

    def logograms(self) -> list[SignInstance]:
        return self.signs_by_type("logogram")

    def numeral_signs(self) -> list[SignInstance]:
        return self.signs_by_type("numeral")

    def transliteration_string(self, sep: str = " ") -> str:
        """Return a human-readable transliteration of all signs."""
        parts = []
        for s in self.signs:
            if s.transliteration:
                parts.append(s.transliteration)
            elif s.character:
                parts.append(s.character)
            elif s.bennettId:
                parts.append(s.bennettId)
            else:
                parts.append("[?]")
        return sep.join(parts)

    def to_dict(self) -> dict:
        """Recursive dataclass → dict conversion."""
        return _asdict_recursive(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Inscription":
        """Create an Inscription from a dictionary (e.g., parsed JSON)."""
        return _fromdict_recursive(cls, d)


# ---------------------------------------------------------------------------
# Recursive helpers for dataclass <-> dict conversion
# ---------------------------------------------------------------------------

def _asdict_recursive(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for fname in obj.__dataclass_fields__:
            val = getattr(obj, fname)
            if val is not None:
                # skip empty containers
                if isinstance(val, (list, dict)) and len(val) == 0:
                    continue
                result[fname] = _asdict_recursive(val)
        return result
    if isinstance(obj, list):
        return [_asdict_recursive(v) for v in obj if v is not None]
    if isinstance(obj, dict):
        return {k: _asdict_recursive(v) for k, v in obj.items() if v is not None}
    return obj


def _fromdict_recursive(cls: type, d: dict) -> Any:
    """Build a dataclass instance from a dict, recursively."""
    if not hasattr(cls, "__dataclass_fields__"):
        return d
    field_types = {}
    for fname, fld in cls.__dataclass_fields__.items():
        field_types[fname] = fld.type
    kwargs = {}
    for fname, ftype in field_types.items():
        if fname not in d:
            continue
        val = d[fname]
        # Resolve forward-ref strings
        origin = getattr(ftype, "__origin__", None)
        args = getattr(ftype, "__args__", [])
        if origin is list and args:
            inner = args[0]
            if hasattr(inner, "__dataclass_fields__"):
                kwargs[fname] = [_fromdict_recursive(inner, v) for v in val]
            else:
                kwargs[fname] = val
        elif origin is Optional and args:
            inner = args[0]
            if hasattr(inner, "__dataclass_fields__"):
                kwargs[fname] = _fromdict_recursive(inner, val) if val else None
            else:
                kwargs[fname] = val
        elif hasattr(ftype, "__dataclass_fields__"):
            kwargs[fname] = _fromdict_recursive(ftype, val)
        else:
            kwargs[fname] = val
    return cls(**kwargs)
