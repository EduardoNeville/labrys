"""alignment.py — Build sign-by-sign 4-script alignment across the
Linear A → Linear B → Cypro-Minoan → Cypriot syllabary descent chain.

Loads la_lb_mapping.csv, la_cm_shared_phonetic_grid.csv, and
refined_phonetic_grid.csv.  For each UNCERTAIN sign with conflicting
LB/CM evidence, enumerates possible values and scores them by:

  * visual continuity
  * phonetic naturalness
  * grid position confidence
  * attestation evidence
"""

from __future__ import annotations

import csv
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class LASignAlign:
    bennett_id: str
    la_char: str          # Unicode character
    la_lb_value: str       # value transferred from LB convention
    visual_sim_to_lb: float
    attestation: str       # "both", "la_only", etc.
    composite_score: float
    notes: str = ""


@dataclass
class CMSignAlign:
    bennett_id: str  # "AB 01" etc.
    la_char: str
    cm_sign: str     # "CM 001" etc.
    cm_desc: str
    cg_value: str    # Cypriot Greek value
    cg_char: str
    cg_unicode: str
    inferred_la_phonetic: str
    triangular_confidence: str  # HIGH / MEDIUM / LOW
    notes: str = ""


@dataclass
class FourScriptRow:
    """A single row of the 4-script alignment matrix."""

    bennett_id: str
    la_char: str
    lb_value: str            # from la_lb_mapping
    lb_visual_sim: float     # LA→LB visual similarity
    cm_value: str            # inferred LA phonetic from CM chain
    cm_confidence: str       # HIGH/MEDIUM/LOW
    cg_value: str            # terminal Cypriot value
    refined_value: str       # from refined_phonetic_grid
    decision: str            # CONFIRM / UNCERTAIN
    confidence_score: float  # from refined grid
    in_conflict: bool        # is this one of the 10 persistent conflicts?
    evidence_summary: str


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

DATA_DIR = Path("data/analysis/comparative")


def _load_la_lb(path: Path) -> Dict[str, LASignAlign]:
    """Load LA→LB mapping CSV, keyed by bennett_id."""
    mapping: Dict[str, LASignAlign] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"].strip()
            mapping[bid] = LASignAlign(
                bennett_id=bid,
                la_char=row.get("la_char", ""),
                la_lb_value=row.get("lb_value", "?"),
                visual_sim_to_lb=float(row.get("visual_sim", "0")),
                attestation=row.get("attestation", ""),
                composite_score=float(row.get("composite_score", "0")),
                notes=row.get("notes", ""),
            )
    return mapping


def _load_cm_shared(path: Path) -> Dict[str, CMSignAlign]:
    """Load Cypro-Minoan shared grid CSV, keyed by 'AB XX'."""
    mapping: Dict[str, CMSignAlign] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["la_ab"].strip()
            mapping[bid] = CMSignAlign(
                bennett_id=bid,
                la_char=row.get("la_char", ""),
                cm_sign=row.get("cm_sign", ""),
                cm_desc=row.get("cm_desc", ""),
                cg_value=row.get("cg_value", ""),
                cg_char=row.get("cg_char", ""),
                cg_unicode=row.get("cg_unicode", ""),
                inferred_la_phonetic=row.get("inferred_la_phonetic", ""),
                triangular_confidence=row.get("triangular_confidence", "LOW"),
                notes=row.get("notes", ""),
            )
    return mapping


def _load_refined_grid(path: Path) -> Dict[str, dict]:
    """Load refined phonetic grid CSV -> dict keyed by bennett_id."""
    grid: Dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"].strip()
            score_str = row.get("confidence_score", "0")
            try:
                score = float(score_str)
            except (ValueError, TypeError):
                score = 0.0
            grid[bid] = {
                "conventional_value": row.get("conventional_value", "?"),
                "lb_proposed_value": row.get("lb_proposed_value", ""),
                "cm_suggested_value": row.get("cm_suggested_value", ""),
                "refined_value": row.get("refined_value", "?"),
                "decision": row.get("decision", "UNCERTAIN"),
                "confidence_score": score,
                "conflict_note": row.get("conflict_note", ""),
                "evidence_summary": row.get("evidence_summary", ""),
            }
    return grid


# ---------------------------------------------------------------------------
# Phonetic naturalness
# ---------------------------------------------------------------------------

# Articulatory feature sets for consonants
_CONSONANT_FEATURES: Dict[str, Dict[str, float]] = {
    # place         labial dent/alv pal/alv velar  uvul  glott
    "p": {"place": 0, "manner": 0, "voice": -1},  # voiceless bilabial plosive
    "b": {"place": 0, "manner": 0, "voice": +1},  # voiced bilabial plosive
    "t": {"place": 1, "manner": 0, "voice": -1},  # voiceless alveolar plosive
    "d": {"place": 1, "manner": 0, "voice": +1},  # voiced alveolar plosive
    "k": {"place": 2, "manner": 0, "voice": -1},  # voiceless velar plosive
    "g": {"place": 2, "manner": 0, "voice": +1},  # voiced velar plosive
    "q": {"place": 3, "manner": 0, "voice": -1},  # voiceless uvular plosive
    "m": {"place": 0, "manner": 1, "voice": +1},  # bilabial nasal
    "n": {"place": 1, "manner": 1, "voice": +1},  # alveolar nasal
    "r": {"place": 1, "manner": 2, "voice": +1},  # alveolar trill/tap
    "l": {"place": 1, "manner": 3, "voice": +1},  # alveolar lateral
    "s": {"place": 1, "manner": 4, "voice": -1},  # voiceless alveolar fricative
    "z": {"place": 1, "manner": 4, "voice": +1},  # voiced alveolar fricative
    "j": {"place": 1.5, "manner": 5, "voice": +1},  # palatal approximant
    "w": {"place": 0.5, "manner": 5, "voice": +1},  # labiovelar approximant
    "h": {"place": 4, "manner": 4, "voice": -1},  # glottal fricative
}

# Vowel features
_VOWEL_FEATURES: Dict[str, Dict[str, float]] = {
    "a": {"height": 0, "backness": 0, "round": 0},     # low central
    "e": {"height": 0.5, "backness": -1, "round": 0},   # mid front
    "i": {"height": 1, "backness": -1, "round": 0},     # high front
    "o": {"height": 0.5, "backness": 1, "round": +1},   # mid back rounded
    "u": {"height": 1, "backness": 1, "round": +1},     # high back rounded
}


def _parse_cv(value: str) -> Tuple[str, str]:
    """Parse a syllabic value into (consonant, vowel)."""
    value = value.strip().rstrip("?₂").lower()
    if not value or value == "?":
        return ("?", "?")
    if len(value) == 1 and value in "aeiou":
        return ("", value)  # bare vowel
    if len(value) >= 2:
        return (value[0], value[1:])
    return (value, "?")


def _phonetic_distance_syllabic(v1: str, v2: str) -> float:
    """Compute phonetic distance between two syllabic values (0=identical, 1=max)."""
    v1 = v1.strip().rstrip("?₂").lower()
    v2 = v2.strip().rstrip("?₂").lower()
    if v1 == v2:
        return 0.0
    if v1 == "?" or v2 == "?":
        return 0.5  # unknown — moderate penalty

    c1, w1 = _parse_cv(v1)
    c2, w2 = _parse_cv(v2)

    c_dist = 0.0
    if c1 and c2:
        f1 = _CONSONANT_FEATURES.get(c1, {})
        f2 = _CONSONANT_FEATURES.get(c2, {})
        if f1 and f2:
            # Euclidean distance in feature space, normalised
            place_d = abs(f1.get("place", 0) - f2.get("place", 0)) / 4.0
            manner_d = abs(f1.get("manner", 0) - f2.get("manner", 0)) / 5.0
            voice_d = abs(f1.get("voice", 0) - f2.get("voice", 0)) / 2.0
            c_dist = (place_d * 0.5 + manner_d * 0.3 + voice_d * 0.2)
        else:
            c_dist = 0.5
    elif c1 or c2:
        c_dist = 0.4  # one has consonant, other doesn't

    w_dist = 0.0
    fw1 = _VOWEL_FEATURES.get(w1, {})
    fw2 = _VOWEL_FEATURES.get(w2, {})
    if fw1 and fw2:
        height_d = abs(fw1.get("height", 0) - fw2.get("height", 0))
        backness_d = abs(fw1.get("backness", 0) - fw2.get("backness", 0)) / 2.0
        round_d = abs(fw1.get("round", 0) - fw2.get("round", 0)) / 1.0
        w_dist = (height_d * 0.5 + backness_d * 0.3 + round_d * 0.2)
    elif w1 != w2:
        w_dist = 0.5

    return (c_dist * 0.6 + w_dist * 0.4)


def phonetic_naturalness_score(value_a: str, value_b: str) -> float:
    """Score phonetic naturalness of a value transition between two scripts.

    Returns a value in [0, 1] where 1 = very natural / identical, 0 = unnatural.
    """
    d = _phonetic_distance_syllabic(value_a, value_b)
    return max(0.0, 1.0 - d)


# ---------------------------------------------------------------------------
# Alignment builder
# ---------------------------------------------------------------------------


def build_alignment(
    la_lb_path: Optional[Path] = None,
    cm_path: Optional[Path] = None,
    refined_path: Optional[Path] = None,
) -> List[FourScriptRow]:
    """Build the 4-script alignment matrix.

    Parameters
    ----------
    la_lb_path : Path, optional
        Path to la_lb_mapping.csv
    cm_path : Path, optional
        Path to la_cm_shared_phonetic_grid.csv
    refined_path : Path, optional
        Path to refined_phonetic_grid.csv

    Returns
    -------
    list of FourScriptRow
    """
    la_lb_path = la_lb_path or DATA_DIR / "la_lb_mapping.csv"
    cm_path = cm_path or DATA_DIR / "la_cm_shared_phonetic_grid.csv"
    refined_path = refined_path or DATA_DIR / "refined_phonetic_grid.csv"

    la_lb = _load_la_lb(la_lb_path)
    cm = _load_cm_shared(cm_path)
    refined = _load_refined_grid(refined_path)

    # 10 persistent LB/CM conflicts from the task
    conflict_set = {
        "AB 01", "AB 07", "AB 16", "AB 23", "AB 36",
        "AB 38", "AB 60", "AB 65", "AB 68", "AB 80",
    }

    rows: List[FourScriptRow] = []

    # Iterate over all AB syllables (01-137) that appear in la_lb
    for bid in sorted(la_lb.keys(), key=_sort_key):
        if not bid.startswith("AB "):
            continue

        lb_ent = la_lb.get(bid)
        cm_ent = cm.get(bid)
        ref_ent = refined.get(bid, {})

        lb_value = lb_ent.la_lb_value if lb_ent else "?"
        cm_value = cm_ent.inferred_la_phonetic if cm_ent else ""
        cm_confidence = cm_ent.triangular_confidence if cm_ent else ""
        cg_value = cm_ent.cg_value if cm_ent else ""
        refined_value = ref_ent.get("refined_value", "?")
        decision = ref_ent.get("decision", "UNCERTAIN")
        conf_score = ref_ent.get("confidence_score", 0.0)
        evidence = ref_ent.get("evidence_summary", "")

        in_conflict = bid in conflict_set

        rows.append(FourScriptRow(
            bennett_id=bid,
            la_char=lb_ent.la_char if lb_ent else "",
            lb_value=lb_value,
            lb_visual_sim=lb_ent.visual_sim_to_lb if lb_ent else 0.0,
            cm_value=cm_value,
            cm_confidence=cm_confidence,
            cg_value=cg_value,
            refined_value=refined_value,
            decision=decision,
            confidence_score=conf_score,
            in_conflict=in_conflict,
            evidence_summary=evidence,
        ))

    logger.info("Built alignment: %d rows (%d in conflict set)",
                len(rows), sum(1 for r in rows if r.in_conflict))
    return rows


def _sort_key(bid: str) -> int:
    """Extract integer from 'AB 01' for sorting."""
    try:
        return int(bid.split()[-1])
    except (ValueError, IndexError):
        return 999


def save_alignment_matrix(
    rows: List[FourScriptRow],
    output_path: Path,
) -> None:
    """Write the alignment matrix CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "bennett_id", "la_char", "lb_value", "lb_visual_sim",
        "cm_value", "cm_confidence", "cg_value",
        "refined_value", "decision", "confidence_score",
        "in_conflict", "evidence_summary",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "bennett_id": row.bennett_id,
                "la_char": row.la_char,
                "lb_value": row.lb_value,
                "lb_visual_sim": f"{row.lb_visual_sim:.2f}",
                "cm_value": row.cm_value,
                "cm_confidence": row.cm_confidence,
                "cg_value": row.cg_value,
                "refined_value": row.refined_value,
                "decision": row.decision,
                "confidence_score": f"{row.confidence_score:.1f}",
                "in_conflict": str(row.in_conflict),
                "evidence_summary": row.evidence_summary,
            })
    logger.info("Alignment matrix saved to %s (%d rows)", output_path, len(rows))
