"""resolve_conflicts.py — Resolve the 10 persistent LB/CM conflicts using
a weighted phylogenetic parsimony model.

For each conflict sign, two competing hypotheses are evaluated:
  H_LB:  Linear A had the Linear B-attested value
  H_CM:  Linear A had the Cypro-Minoan-inferred value

Each hypothesis is scored across four dimensions:
  1. Phonetic plausibility (0.35)  — how natural is the required change?
  2. Grid support          (0.20)  — does the refined grid back this value?
  3. Direct attestation    (0.25)  — quality of the source that directly
                                      supports this value
  4. Indirect corroboration(0.20)  — does the other source at least allow
                                      this value?

The hypothesis with higher score wins.  Confidence is proportional to the
score margin and scaled by source quality.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ConflictResolution:
    bennett_id: str
    lb_value: str
    cm_value: str
    cm_confidence: str          # HIGH / MEDIUM / LOW

    # Scores for each hypothesis
    lb_hypothesis_score: float
    cm_hypothesis_score: float

    # Component breakdown for winning hypothesis
    phonetic_score: float       # phonetic plausibility
    grid_score: float           # grid support
    attestation_score: float    # direct attestation
    corroboration_score: float  # indirect corroboration

    winning_value: str
    winning_source: str         # "LB" or "CM"
    confidence: float           # [0, 1] overall confidence in resolution
    resolution_note: str        # human-readable justification


# ---------------------------------------------------------------------------
# Phonetic distance helpers  (reused from alignment module via local copy)
# ---------------------------------------------------------------------------


_CONSONANT_FEATURES: Dict[str, Dict[str, float]] = {
    "p": {"place": 0, "manner": 0, "voice": -1},
    "b": {"place": 0, "manner": 0, "voice": +1},
    "t": {"place": 1, "manner": 0, "voice": -1},
    "d": {"place": 1, "manner": 0, "voice": +1},
    "k": {"place": 2, "manner": 0, "voice": -1},
    "g": {"place": 2, "manner": 0, "voice": +1},
    "q": {"place": 3, "manner": 0, "voice": -1},
    "m": {"place": 0, "manner": 1, "voice": +1},
    "n": {"place": 1, "manner": 1, "voice": +1},
    "r": {"place": 1, "manner": 2, "voice": +1},
    "l": {"place": 1, "manner": 3, "voice": +1},
    "s": {"place": 1, "manner": 4, "voice": -1},
    "z": {"place": 1, "manner": 4, "voice": +1},
    "j": {"place": 1.5, "manner": 5, "voice": +1},
    "w": {"place": 0.5, "manner": 5, "voice": +1},
    "h": {"place": 4, "manner": 4, "voice": -1},
}

_VOWEL_FEATURES: Dict[str, Dict[str, float]] = {
    "a": {"height": 0, "backness": 0, "round": 0},
    "e": {"height": 0.5, "backness": -1, "round": 0},
    "i": {"height": 1, "backness": -1, "round": 0},
    "o": {"height": 0.5, "backness": 1, "round": +1},
    "u": {"height": 1, "backness": 1, "round": +1},
}

# Directional sound-change plausibility bonuses.
# Key: (from_val, to_val) → bonus in [0, 1]; 0.5 = neutral.
# Encodes known tendencies:
#   - Voicing is common word-medially (many Mediterranean languages)
#   - Palatal → affricate is a well-known path
#   - Vowel shifts are common
#   - CV → V or V → CV requires syllable restructuring (rare)
_DIRECTIONAL_BIAS: Dict[Tuple[str, str], float] = {}

def _init_directional_bias():
    """Seed directional bias with linguistic knowledge."""
    pairs = [
        # Devoicing ← more common than voicing (but both possible)
        ("da", "ta"), ("di", "ti"), ("do", "to"), ("du", "tu"),
        ("ba", "pa"), ("bi", "pi"),
        ("ga", "ka"), ("gi", "ki"),
        # Palatal → affricate (jo→za, ju→zo)
        ("jo", "za"), ("jo", "zo"), ("ju", "za"), ("ju", "zo"),
        # Nasal vowel shifts
        ("mu", "ma"), ("ma", "mu"),
        ("nu", "na"), ("na", "nu"),
        # Liquid shifts
        ("ra", "ma"), ("ma", "ra"),  # r↔m is uncommon but attested
        ("ro", "lo"),
        # Labiovelar → velar (qa→ka common, ka→qa rare)
        ("qa", "ka"),
        ("qe", "ke"),
        # Vowel→CV restructuring (very rare)
        ("e", "pa"), ("a", "pa"), ("i", "pi"), ("o", "po"), ("u", "pu"),
        ("pa", "e"), ("pa", "a"),
    ]
    for a, b in pairs:
        _DIRECTIONAL_BIAS[(a, b)] = 0.5  # neutral default

    # Directional overrides (higher = more natural in this direction)
    overrides = {
        ("qa", "ka"): 0.85,   # labiovelar→velar is common (loss of labialization)
        ("ka", "qa"): 0.30,   # velar→labiovelar is rare
        ("jo", "za"): 0.75,   # palatal→affricate is a standard path
        ("za", "jo"): 0.40,   # affricate→palatal is less common
        ("e", "pa"): 0.15,    # vowel→CV is very marked
        ("pa", "e"): 0.10,    # CV→vowel is very marked
        ("ra", "ma"): 0.45,   # r→m is unusual
        ("ma", "ra"): 0.35,   # m→r similarly unusual
        ("mu", "ma"): 0.70,   # vowel shift is natural
        ("ma", "mu"): 0.65,
        ("da", "ta"): 0.65,   # devoicing somewhat more common than voicing
        ("ta", "da"): 0.55,
        ("di", "ti"): 0.65,
        ("ti", "di"): 0.55,
        ("ro", "ro"): 1.00,   # identity
        ("ju", "jo"): 0.70,   # vowel shift
        ("jo", "ju"): 0.65,
        ("ma", "pa"): 0.50,   # nasal→plosive
        ("pa", "ma"): 0.45,   # plosive→nasal less common
    }
    _DIRECTIONAL_BIAS.update(overrides)


_init_directional_bias()


def _parse_cv(value: str) -> tuple:
    value = value.strip().rstrip("?₂").lower()
    if not value or value == "?":
        return ("?", "?")
    if len(value) == 1 and value in "aeiou":
        return ("", value)
    if len(value) >= 2:
        return (value[0], value[1] if len(value) > 1 and value[1] in "aeiou" else value[1:2])
    return (value, "?")


def phonetic_distance(v1: str, v2: str) -> float:
    """Compute phonetic distance between two syllabic values (0=identical)."""
    v1 = v1.strip().rstrip("?₂").lower()
    v2 = v2.strip().rstrip("?₂").lower()
    if v1 == v2:
        return 0.0
    if v1 == "?" or v2 == "?" or not v1 or not v2:
        return 0.5

    c1, w1 = _parse_cv(v1)
    c2, w2 = _parse_cv(v2)

    c_dist = 0.0
    if c1 and c2:
        f1 = _CONSONANT_FEATURES.get(c1)
        f2 = _CONSONANT_FEATURES.get(c2)
        if f1 and f2:
            place_d = abs(f1["place"] - f2["place"]) / 4.0
            manner_d = abs(f1["manner"] - f2["manner"]) / 5.0
            voice_d = abs(f1["voice"] - f2["voice"]) / 2.0
            c_dist = place_d * 0.5 + manner_d * 0.3 + voice_d * 0.2
        else:
            c_dist = 0.5
    elif c1 or c2:
        c_dist = 0.4

    w_dist = 0.0
    fw1 = _VOWEL_FEATURES.get(w1)
    fw2 = _VOWEL_FEATURES.get(w2)
    if fw1 and fw2:
        height_d = abs(fw1["height"] - fw2["height"])
        backness_d = abs(fw1["backness"] - fw2["backness"]) / 2.0
        round_d = abs(fw1["round"] - fw2["round"])
        w_dist = height_d * 0.5 + backness_d * 0.3 + round_d * 0.2
    elif w1 != w2:
        w_dist = 0.5

    return c_dist * 0.6 + w_dist * 0.4


def phonetic_plausibility(from_val: str, to_val: str) -> float:
    """Score how plausible a sound change is in the given direction.

    Combines articulatory distance with known typological tendencies.
    Returns value in [0, 1]; 1 = very plausible.
    """
    from_v = from_val.strip().rstrip("?₂").lower()
    to_v = to_val.strip().rstrip("?₂").lower()

    if from_v == "?" or to_v == "?":
        return 0.5

    # Base: articulatory distance inverted (1 = identical)
    dist = phonetic_distance(from_v, to_v)
    base_plausibility = max(0.0, 1.0 - dist)

    # Directional bias - blend with base
    bias = _DIRECTIONAL_BIAS.get((from_v, to_v), 0.5)

    # Blend: 70% articulatory, 30% directional knowledge
    return base_plausibility * 0.70 + bias * 0.30


# ---------------------------------------------------------------------------
# Grid support
# ---------------------------------------------------------------------------


def _grid_support_for_value(
    refined_entry: dict,
    candidate_value: str,
) -> float:
    """How much does the refined phonetic grid support this candidate value?"""
    refined_val = refined_entry.get("refined_value", "?").strip().rstrip("?₂").lower()
    candidate = candidate_value.strip().rstrip("?₂").lower()

    if refined_val == candidate:
        # Direct match — full grid support
        confidence = float(refined_entry.get("confidence_score", 50))
        return min(1.0, confidence / 100.0)
    else:
        # Grid doesn't match — penalize
        # But give some credit if grid is uncertain enough
        confidence = float(refined_entry.get("confidence_score", 30))
        if confidence < 40:
            return 0.4  # grid is too uncertain to penalize heavily
        return 0.3


# ---------------------------------------------------------------------------
# Conflict resolver
# ---------------------------------------------------------------------------

CONFLICT_SIGNS = {
    "AB 01", "AB 07", "AB 16", "AB 23", "AB 36",
    "AB 38", "AB 60", "AB 65", "AB 68", "AB 80",
}

CM_CONFIDENCE_NUMERIC = {"HIGH": 1.0, "MEDIUM": 0.55, "LOW": 0.25}


def resolve_conflicts(
    cm_path: Optional[Path] = None,
    refined_path: Optional[Path] = None,
    lb_path: Optional[Path] = None,
) -> List[ConflictResolution]:
    """Resolve the 10 persistent LB/CM conflicts.

    Parameters
    ----------
    cm_path : Path, optional
        Path to la_cm_shared_phonetic_grid.csv
    refined_path : Path, optional
        Path to refined_phonetic_grid.csv
    lb_path : Path, optional
        Path to la_lb_mapping.csv

    Returns
    -------
    list of ConflictResolution
    """
    from pipeline.phylogenetic.alignment import (
        _load_cm_shared,
        _load_la_lb,
        _load_refined_grid,
    )
    DATA_DIR = Path("data/analysis/comparative")
    cm_map = _load_cm_shared(cm_path or DATA_DIR / "la_cm_shared_phonetic_grid.csv")
    lb_map = _load_la_lb(lb_path or DATA_DIR / "la_lb_mapping.csv")
    refined = _load_refined_grid(refined_path or DATA_DIR / "refined_phonetic_grid.csv")

    resolutions: List[ConflictResolution] = []

    for bid in sorted(CONFLICT_SIGNS, key=lambda x: int(x.split()[-1])):
        lb_ent = lb_map.get(bid)
        cm_ent = cm_map.get(bid)
        ref_ent = refined.get(bid, {})

        if not lb_ent or not cm_ent:
            continue

        lb_value = lb_ent.la_lb_value.strip().rstrip("?₂").lower()
        cm_value = cm_ent.inferred_la_phonetic.strip().rstrip("?₂").lower()
        if not lb_value or lb_value == "?":
            continue
        if not cm_value or cm_value == "?":
            continue

        cm_conf_str = cm_ent.triangular_confidence or "LOW"
        cm_conf_num = CM_CONFIDENCE_NUMERIC.get(cm_conf_str, 0.25)

        lb_composite = getattr(lb_ent, 'composite_score', 60.0)
        grid_conf = float(ref_ent.get("confidence_score", 50))

        # ----- Hypothesis H_LB: LA had LB value -----
        # Phonetic plausibility: how natural is LB_val → LB_val + LB_val → CM_val?
        phon_lb_lb = phonetic_plausibility(lb_value, lb_value)  # = 1.0
        phon_lb_cm = phonetic_plausibility(lb_value, cm_value)
        phon_score_lb = (phon_lb_lb * 0.5 + phon_lb_cm * 0.5)

        # Grid support for LB value
        grid_score_lb = _grid_support_for_value(ref_ent, lb_value)

        # Direct attestation: LB composite is the direct source for H_LB
        attest_lb = min(1.0, lb_composite / 100.0)

        # Indirect corroboration: CM must allow LB value
        corrob_lb = cm_conf_num * phon_lb_cm

        score_lb = (
            0.35 * phon_score_lb
            + 0.20 * grid_score_lb
            + 0.25 * attest_lb
            + 0.20 * corrob_lb
        )

        # ----- Hypothesis H_CM: LA had CM value -----
        # Phonetic plausibility: CM_val → LB_val + CM_val → CM_val
        phon_cm_lb = phonetic_plausibility(cm_value, lb_value)
        phon_cm_cm = phonetic_plausibility(cm_value, cm_value)  # = 1.0
        phon_score_cm = (phon_cm_lb * 0.5 + phon_cm_cm * 0.5)

        # Grid support for CM value
        grid_score_cm = _grid_support_for_value(ref_ent, cm_value)

        # Direct attestation: CM confidence is the direct source for H_CM
        attest_cm = cm_conf_num

        # Indirect corroboration: LB must allow CM value
        corrob_cm = min(1.0, lb_composite / 100.0) * phon_cm_lb

        score_cm = (
            0.35 * phon_score_cm
            + 0.20 * grid_score_cm
            + 0.25 * attest_cm
            + 0.20 * corrob_cm
        )

        # Determine winner
        margin = abs(score_lb - score_cm)

        if score_lb >= score_cm:
            winning_value = lb_value
            winning_source = "LB"
            phon_final = phon_score_lb
            grid_final = grid_score_lb
            attest_final = attest_lb
            corrob_final = corrob_lb
        else:
            winning_value = cm_value
            winning_source = "CM"
            phon_final = phon_score_cm
            grid_final = grid_score_cm
            attest_final = attest_cm
            corrob_final = corrob_cm

        # Confidence: margin-scaled, capped by source quality
        raw_conf = 0.5 + margin * 0.8  # margin in [0, ~0.6] → conf in [0.5, ~1.0]
        if winning_source == "LB":
            quality_cap = min(1.0, lb_composite / 100.0)  # capped by LB attestation
        else:
            quality_cap = cm_conf_num  # capped by CM confidence
        confidence = min(raw_conf, quality_cap + 0.15)  # small boost above cap
        confidence = max(0.3, min(0.95, confidence))  # clamp to [0.3, 0.95]

        # Generate resolution note
        note = _make_note(
            bid, lb_value, cm_value, cm_conf_str,
            winning_source, winning_value, score_lb, score_cm, margin,
        )

        resolutions.append(ConflictResolution(
            bennett_id=bid,
            lb_value=lb_value.upper() if lb_value else lb_value,
            cm_value=cm_value,
            cm_confidence=cm_conf_str,
            lb_hypothesis_score=round(score_lb, 4),
            cm_hypothesis_score=round(score_cm, 4),
            phonetic_score=round(phon_final, 3),
            grid_score=round(grid_final, 3),
            attestation_score=round(attest_final, 3),
            corroboration_score=round(corrob_final, 3),
            winning_value=winning_value,
            winning_source=winning_source,
            confidence=round(confidence, 3),
            resolution_note=note,
        ))

    logger.info("Resolved %d conflicts", len(resolutions))
    return resolutions


def _make_note(
    bid: str, lb_val: str, cm_val: str, cm_conf: str,
    winner: str, winning: str, score_lb: float, score_cm: float,
    margin: float,
) -> str:
    """Generate a human-readable resolution note."""
    margin_pct = int(margin * 100)
    if winner == "LB":
        if margin_pct >= 20:
            tmpl = (
                "Strongly favour LB /{lb}/ over CM /{cm}/ ({conf}): "
                "LB attestation is direct with high composite score; "
                "CM inference chain is longer and less reliable. "
                "Score margin: {m}%."
            )
        else:
            tmpl = (
                "Moderately favour LB /{lb}/ over CM /{cm}/ ({conf}): "
                "LB evidence is direct though narrow margin suggests "
                "CM value is phonetically plausible. Score margin: {m}%."
            )
    else:
        if margin_pct >= 20:
            tmpl = (
                "Strongly favour CM /{cm}/ over LB /{lb}/ ({conf}): "
                "CM value fits grid better and requires less phonetic "
                "restructuring. Score margin: {m}%."
            )
        else:
            tmpl = (
                "Moderately favour CM /{cm}/ over LB /{lb}/ ({conf}): "
                "Narrow advantage for CM value; both are plausible. "
                "Score margin: {m}%."
            )
    return tmpl.format(
        lb=lb_val, cm=cm_val, conf=cm_conf, m=margin_pct,
    )


def save_conflict_resolutions(
    resolutions: List[ConflictResolution],
    output_path: Path,
) -> None:
    """Write conflict_resolutions.csv."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "bennett_id", "lb_value", "cm_value", "cm_confidence",
        "winning_value", "winning_source", "confidence",
        "lb_hypothesis_score", "cm_hypothesis_score",
        "phonetic_score", "grid_score",
        "attestation_score", "corroboration_score",
        "resolution_note",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in resolutions:
            writer.writerow({
                "bennett_id": r.bennett_id,
                "lb_value": r.lb_value,
                "cm_value": r.cm_value,
                "cm_confidence": r.cm_confidence,
                "winning_value": r.winning_value,
                "winning_source": r.winning_source,
                "confidence": f"{r.confidence:.3f}",
                "lb_hypothesis_score": f"{r.lb_hypothesis_score:.4f}",
                "cm_hypothesis_score": f"{r.cm_hypothesis_score:.4f}",
                "phonetic_score": f"{r.phonetic_score:.3f}",
                "grid_score": f"{r.grid_score:.3f}",
                "attestation_score": f"{r.attestation_score:.3f}",
                "corroboration_score": f"{r.corroboration_score:.3f}",
                "resolution_note": r.resolution_note,
            })
    logger.info("Conflict resolutions saved to %s (%d rows)",
                output_path, len(resolutions))
