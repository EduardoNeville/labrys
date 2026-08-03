#!/usr/bin/env python3
"""
Predictive Toponym & Formula Testing
=====================================
Applies Phase 4 ML predictions to re-read known Linear A toponyms,
formulaic sequences, and accounting terms.

For each known term, if any UNCERTAIN sign appears, substitute the ML
predicted value and check whether the resulting reading improves the
phonological match to the attested place name or known reading.

Dependencies: csv (stdlib), json (stdlib), os (stdlib).
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("toponym_testing")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))

DEFAULT_UNCERTAIN_PREDICTIONS = os.path.join(
    PROJECT_ROOT, "data", "analysis", "ml", "uncertain_predictions.csv"
)
DEFAULT_PHONETIC_GRID = os.path.join(
    PROJECT_ROOT, "data", "analysis", "comparative", "refined_phonetic_grid.csv"
)
DEFAULT_TOPONYM_ANCHORS = os.path.join(
    PROJECT_ROOT, "data", "analysis", "linguistic", "toponym_anchors.csv"
)
DEFAULT_LOANWORD_MATCHES = os.path.join(
    PROJECT_ROOT, "data", "analysis", "linguistic", "loanword_matches.csv"
)
DEFAULT_OUTPUT = os.path.join(
    PROJECT_ROOT, "data", "analysis", "verification", "toponym_test_results.csv"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TermResult:
    """Result for one tested term."""
    term_type: str          # toponym / formula / accounting / loanword
    canonical_form: str     # the conventional syllabic reading (e.g. pa-i-to)
    ml_substituted_form: str  # the ML-substituted reading
    phonological_improvement: str  # "1" or "0" (binary as string for CSV)
    ml_reading_plausible: str      # "1" or "0"
    substituted_signs: int  # count of signs substituted
    notes: str = ""


# ---------------------------------------------------------------------------
# Known Linear A syllabic forms → bennett_id mapping
# ---------------------------------------------------------------------------

# We define each term as a sequence of Bennett IDs (not syllables)
# so there is no ambiguity about which sign variant is meant.
#
# The canonical syllabic form is stored separately for human readability.
#
# Bennett ID assignments follow the refined phonetic grid (Phase 5) and
# consensus Linear A/B transliteration conventions.

KNOWN_TERMS: list[dict] = [
    # ---------- TOPONYMS ----------
    {
        "canonical_form": "pa-i-to",
        "bennett_ids": ["AB 03", "AB 28", "AB 05"],
        "attested_name": "Phaistos",
        "attested_phonetic": "pʰaistos",
        "term_type": "toponym",
    },
    {
        "canonical_form": "i-da",
        "bennett_ids": ["AB 28", "AB 01"],
        "attested_name": "Ida (Mt. Ida)",
        "attested_phonetic": "ida",
        "term_type": "toponym",
    },
    {
        "canonical_form": "di-ka-ta",
        "bennett_ids": ["AB 07", "AB 77", "AB 59"],
        "attested_name": "Dikte",
        "attested_phonetic": "dikte",
        "term_type": "toponym",
    },
    {
        "canonical_form": "su-ki-ri-ta",
        "bennett_ids": ["AB 58", "AB 67", "AB 53", "AB 59"],
        "attested_name": "Sybrita",
        "attested_phonetic": "sybrita",
        "term_type": "toponym",
    },
    {
        "canonical_form": "tu-ru-sa",
        "bennett_ids": ["AB 69", "AB 26", "AB 31"],
        "attested_name": "Tylissos",
        "attested_phonetic": "tylissos",
        "term_type": "toponym",
    },
    {
        "canonical_form": "se-to-i-ja",
        "bennett_ids": ["AB 09", "AB 05", "AB 28", "AB 57"],
        "attested_name": "Setoia",
        "attested_phonetic": "setoia",
        "term_type": "toponym",
    },
    {
        "canonical_form": "ku-do-ni-ja",
        "bennett_ids": ["AB 81", "AB 14", "AB 30", "AB 57"],
        "attested_name": "Kydonia",
        "attested_phonetic": "kydonia",
        "term_type": "toponym",
    },
    # ---------- FORMULAIC SEQUENCES ----------
    {
        "canonical_form": "a-sa-sa-ra-me",
        "bennett_ids": ["AB 08", "AB 31", "AB 31", "AB 60", "AB 13"],
        "attested_name": "a-sa-sa-ra-me (libation formula)",
        "attested_phonetic": "asasarame",
        "term_type": "formula",
    },
    {
        "canonical_form": "ja-sa-sa-ra-me",
        "bennett_ids": ["AB 57", "AB 31", "AB 31", "AB 60", "AB 13"],
        "attested_name": "ja-sa-sa-ra-me (libation variant)",
        "attested_phonetic": "jasasarame",
        "term_type": "formula",
    },
    # ---------- ACCOUNTING TERMS ----------
    {
        "canonical_form": "ku-ro",
        "bennett_ids": ["AB 81", "AB 02"],
        "attested_name": "ku-ro (total)",
        "attested_phonetic": "kuro",
        "term_type": "accounting",
    },
    {
        "canonical_form": "po-to-ku-ro",
        "bennett_ids": ["AB 29", "AB 05", "AB 81", "AB 02"],
        "attested_name": "po-to-ku-ro (grand total)",
        "attested_phonetic": "potokuro",
        "term_type": "accounting",
    },
    {
        "canonical_form": "ki-ro",
        "bennett_ids": ["AB 67", "AB 02"],
        "attested_name": "ki-ro (owed/deficit)",
        "attested_phonetic": "kiro",
        "term_type": "accounting",
    },
]


# ---------------------------------------------------------------------------
# Loading functions
# ---------------------------------------------------------------------------

def load_ml_predictions(path: str = DEFAULT_UNCERTAIN_PREDICTIONS) -> dict:
    """
    Load ML predictions from uncertain_predictions.csv.

    Returns
    -------
    dict mapping bennett_id → predicted_refined_value
        e.g. {"AB 01": "da", "AB 07": "di", ...}
    """
    predictions: dict[str, str] = {}
    if not os.path.exists(path):
        logger.warning("ML predictions file not found: %s", path)
        return predictions

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = (row.get("bennett_id") or "").strip()
            pred = (row.get("predicted_refined_value") or "").strip()
            if bid and pred and pred != "?":
                predictions[bid] = pred

    logger.info("Loaded %d ML predictions from %s", len(predictions), path)
    return predictions


def load_phonetic_grid(path: str = DEFAULT_PHONETIC_GRID) -> dict:
    """
    Load refined phonetic grid.

    Returns
    -------
    dict mapping bennett_id → {
        "conventional_value": str,
        "decision": str (CONFIRM/UNCERTAIN/REVISE),
        "refined_value": str,
        "confidence_score": float,
    }
    """
    grid: dict[str, dict] = {}
    if not os.path.exists(path):
        logger.warning("Phonetic grid not found: %s", path)
        return grid

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = (row.get("bennett_id") or "").strip()
            if not bid:
                continue
            grid[bid] = {
                "conventional_value": (row.get("conventional_value") or "").strip(),
                "decision": (row.get("decision") or "").strip(),
                "refined_value": (row.get("refined_value") or "").strip(),
                "confidence_score": _parse_float(row.get("confidence_score", "0")),
            }

    logger.info(
        "Loaded %d signs from phonetic grid (%d UNCERTAIN, %d CONFIRM)",
        len(grid),
        sum(1 for v in grid.values() if v["decision"] == "UNCERTAIN"),
        sum(1 for v in grid.values() if v["decision"] == "CONFIRM"),
    )
    return grid


def load_toponym_anchors(path: str = DEFAULT_TOPONYM_ANCHORS) -> list[dict]:
    """Load toponym anchors with exact (d=0) matches."""
    anchors: list[dict] = []
    if not os.path.exists(path):
        logger.warning("Toponym anchors not found: %s", path)
        return anchors

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dist_str = (row.get("distance") or "99").strip()
            try:
                dist = int(dist_str)
            except ValueError:
                dist = 99
            if dist == 0:
                anchors.append(dict(row))

    logger.info("Loaded %d exact (d=0) toponym anchors", len(anchors))
    return anchors


def load_loanword_matches(path: str = DEFAULT_LOANWORD_MATCHES) -> list[dict]:
    """Load loanword matches with exact (distance=0) matches."""
    matches: list[dict] = []
    if not os.path.exists(path):
        logger.warning("Loanword matches not found: %s", path)
        return matches

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dist_str = (row.get("distance") or "99").strip()
            try:
                dist = int(dist_str)
            except ValueError:
                dist = 99
            if dist == 0:
                matches.append(dict(row))

    logger.info("Loaded %d exact (d=0) loanword matches", len(matches))
    return matches


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_float(s: str) -> float:
    """Parse a float, returning 0.0 on failure."""
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_int(s: str) -> int:
    """Parse an int, returning 0 on failure."""
    try:
        return int(s)
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Syllabary mapping
# ---------------------------------------------------------------------------

def build_syllabary_map(grid: dict[str, dict]) -> dict[str, str]:
    """
    Build a bennett_id → conventional_value map from the grid.
    Falls back to refined_value if conventional is empty or '?'.
    """
    smap: dict[str, str] = {}
    for bid, info in grid.items():
        cv = info.get("conventional_value", "")
        rv = info.get("refined_value", "")
        val = cv if cv and cv != "?" else rv
        if val and val != "?":
            smap[bid] = val
    return smap


# ---------------------------------------------------------------------------
# Phonetic similarity
# ---------------------------------------------------------------------------

def _phonetic_edit_distance(a: str, b: str) -> int:
    """
    Compute a simple phonetic edit distance between two strings.
    Characters are compared case-insensitively.  Consonantal similarity
    (voicing pairs, r/l) reduces the substitution cost.
    """
    a = a.lower().replace("-", "")
    b = b.lower().replace("-", "")
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    # Similarity groups: substitutions within these groups cost 0.5 instead of 1
    sim_groups = [
        {"p", "b", "pʰ", "ph", "f", "v"},
        {"t", "d", "tʰ", "th"},
        {"k", "g", "kʰ", "kh", "c", "q"},
        {"r", "l"},
        {"s", "z", "ʃ"},
        {"m", "n", "ŋ"},
        {"i", "e", "y"},
        {"u", "o", "w"},
    ]
    sim_map: dict[str, set[str]] = {}
    for grp in sim_groups:
        for ch in grp:
            sim_map[ch] = grp

    def _cost(c1: str, c2: str) -> float:
        if c1 == c2:
            return 0.0
        if c1 in sim_map and c2 in sim_map[c1]:
            return 0.5
        return 1.0

    prev = [float(i) for i in range(m + 1)]
    curr = [0.0] * (m + 1)
    for i in range(1, n + 1):
        curr[0] = float(i)
        for j in range(1, m + 1):
            sub_cost = _cost(a[i - 1], b[j - 1])
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + sub_cost,
            )
        prev, curr = curr, prev

    return int(round(prev[m]))


def _compare_phonetic(la_form: str, attested: str) -> tuple[int, str]:
    """
    Compare a Linear A reading to the attested name.
    Returns (distance, assessment_string).
    """
    dist = _phonetic_edit_distance(la_form, attested)
    max_len = max(len(la_form.replace("-", "")), len(attested.replace("-", "")))
    normalized = dist / max(1, max_len)

    if normalized <= 0.3:
        assessment = "excellent"
    elif normalized <= 0.5:
        assessment = "good"
    elif normalized <= 0.7:
        assessment = "moderate"
    else:
        assessment = "poor"

    return dist, f"{assessment} (dist={dist}, norm={normalized:.2f})"


# ---------------------------------------------------------------------------
# Core testing logic
# ---------------------------------------------------------------------------

def test_term(
    term: dict,
    grid: dict[str, dict],
    predictions: dict[str, str],
) -> TermResult:
    """
    Test one known term against ML predictions.

    1. Build the canonical form from conventional grid values.
    2. For each bennett_id that is UNCERTAIN in the grid, substitute
       the ML predicted value.
    3. Compare both forms to the attested name.
    4. Determine if ML substitution improves the match.
    """
    bennett_ids: list[str] = term["bennett_ids"]
    attested_name: str = term["attested_name"]
    attested_phonetic: str = term["attested_phonetic"]
    term_type: str = term["term_type"]

    canonical_syllables: list[str] = []
    ml_syllables: list[str] = []
    substituted_count = 0
    substitution_details: list[str] = []

    for bid in bennett_ids:
        gi = grid.get(bid, {})
        decision = gi.get("decision", "UNKNOWN")
        conventional = gi.get("conventional_value", "?")
        refined = gi.get("refined_value", "")
        ml_pred = predictions.get(bid, "")

        # Determine the canonical syllable
        canon_syl = conventional if conventional and conventional != "?" else refined
        if not canon_syl or canon_syl == "?":
            canon_syl = "?"
        canonical_syllables.append(canon_syl)

        # Determine ML-substituted syllable
        # Only count as genuine substitution when the conventional value is
        # KNOWN (not '?') and the ML prediction differs from it.
        if decision == "UNCERTAIN" and ml_pred and ml_pred != canon_syl:
            ml_syllables.append(ml_pred)
            if canon_syl and canon_syl != "?":
                substituted_count += 1
                substitution_details.append(f"{bid}: {canon_syl}→{ml_pred}")
            else:
                substitution_details.append(f"{bid}: unknown→{ml_pred}")
        else:
            ml_syllables.append(canon_syl)

    canonical_form_joined = "-".join(canonical_syllables)
    ml_form_joined = "-".join(ml_syllables)

    # Canonical string for comparison (strip hyphens)
    canonical_str = canonical_form_joined.replace("-", "").replace("?", "")
    ml_str = ml_form_joined.replace("-", "").replace("?", "")

    # Compute phonetic distances
    canon_dist, canon_assess = _compare_phonetic(canonical_str, attested_phonetic)
    ml_dist, ml_assess = _compare_phonetic(ml_str, attested_phonetic)

    # Determine improvement
    improvement = ml_dist < canon_dist
    plausible = bool(ml_str) and ml_dist <= canon_dist

    # Build notes
    notes_parts = [
        f"canonical={canonical_form_joined} (dist={canon_dist})",
        f"ML={ml_form_joined} (dist={ml_dist})",
    ]
    if substitution_details:
        notes_parts.append(f"substitutions: {'; '.join(substitution_details)}")
    else:
        notes_parts.append("no substitutions needed")
    notes_parts.append(f"canonical_assessment={canon_assess}")
    notes_parts.append(f"ML_assessment={ml_assess}")

    if improvement:
        notes_parts.append("ML IMPROVES reading")
    elif ml_dist == canon_dist and substituted_count > 0:
        notes_parts.append("ML NEUTRAL (same distance)")
    elif substituted_count > 0:
        notes_parts.append("ML DOES NOT improve reading")
    else:
        pass

    return TermResult(
        term_type=term_type,
        canonical_form=canonical_form_joined,
        ml_substituted_form=ml_form_joined,
        phonological_improvement="1" if improvement else "0",
        ml_reading_plausible="1" if plausible else "0",
        substituted_signs=substituted_count,
        notes="; ".join(notes_parts),
    )


# ---------------------------------------------------------------------------
# Loanword anchor testing
# ---------------------------------------------------------------------------

def test_loanword_anchors(
    toponym_anchors: list[dict],
    loanword_matches: list[dict],
    grid: dict[str, dict],
    predictions: dict[str, str],
) -> list[TermResult]:
    """
    Test whether ML predictions strengthen any weak loanword matches.

    For each exact-match loanword anchor, check whether ML predictions
    for the participating signs improve or disrupt the match.

    We look at the context around the matched anchor to find signs that
    might be ML-substitutable.
    """
    results: list[TermResult] = []
    seen: set[str] = set()

    # Process toponym anchors
    for anchor in toponym_anchors[:20]:  # limit to avoid duplicates
        place = anchor.get("place_name", "")
        matched = anchor.get("matched_string", "")
        la_spelling = anchor.get("la_spelling", "")
        ins_id = anchor.get("inscription_id", "")

        key = f"{place}|{matched}"
        if key in seen:
            continue
        seen.add(key)

        # The matched_string is a sequence of AB codes, e.g., "PAIT"
        # We need to break this into individual signs and check the grid.
        # Since matched_string is concatenated AB codes (2 chars each),
        # we tokenize into 2-char chunks when possible.
        matched_clean = matched.strip().upper()
        chunks = []
        i = 0
        while i < len(matched_clean):
            if i + 1 < len(matched_clean):
                chunks.append(matched_clean[i:i + 2])
                i += 2
            else:
                chunks.append(matched_clean[i])
                i += 1

        # Try to map chunks to bennett_ids via the grid
        canonical_parts: list[str] = []
        ml_parts: list[str] = []
        sub_count = 0
        sub_details: list[str] = []

        for chk in chunks:
            # Find the bennett_id whose conventional_value or refined_value matches
            found_bid = None
            for bid, info in grid.items():
                cv = (info.get("conventional_value") or "").upper()
                rv = (info.get("refined_value") or "").upper()
                effective = cv if cv and cv != "?" else rv
                if chk == cv or chk == rv or chk == effective:
                    found_bid = bid
                    break

            if found_bid:
                gi = grid[found_bid]
                decision = gi.get("decision", "")
                cv = gi.get("conventional_value", "?")
                rv = gi.get("refined_value", "")
                # Use refined value when conventional is unknown
                effective_cv = cv if cv and cv != "?" else rv
                ml_pred = predictions.get(found_bid, "")

                canonical_parts.append(effective_cv.lower() if effective_cv != "?" else chk.lower())
                if decision == "UNCERTAIN" and ml_pred and ml_pred != effective_cv:
                    ml_parts.append(ml_pred)
                    if effective_cv and effective_cv != "?":
                        sub_count += 1
                        sub_details.append(f"{found_bid}: {effective_cv}→{ml_pred}")
                    else:
                        sub_details.append(f"{found_bid}: unknown→{ml_pred}")
                else:
                    ml_parts.append(effective_cv.lower() if effective_cv != "?" else chk.lower())
            else:
                canonical_parts.append(chk.lower())
                ml_parts.append(chk.lower())

        if sub_count > 0 or True:  # Include all for completeness
            canon_str = "-".join(canonical_parts)
            ml_str = "-".join(ml_parts)

            # Compare to the Greek name if available
            notes_parts = [
                f"anchor={place}",
                f"matched_string={matched}",
                f"inscription={ins_id}",
            ]
            if sub_details:
                notes_parts.append(f"substitutions: {'; '.join(sub_details)}")
            else:
                notes_parts.append("no uncertain signs in match")

            if sub_count > 0:
                # Check phonetic distance to the Minoan form
                canon_flat = canon_str.replace("-", "")
                ml_flat = ml_str.replace("-", "")
                attested_flat = la_spelling.replace("-", "")
                canon_dist, _ = _compare_phonetic(canon_flat, attested_flat)
                ml_dist, _ = _compare_phonetic(ml_flat, attested_flat)
                if ml_dist < canon_dist:
                    improved = True
                    notes_parts.append("ML IMPROVES match")
                elif ml_dist == canon_dist:
                    improved = True
                    notes_parts.append("ML NEUTRAL (same distance)")
                else:
                    improved = False
                    notes_parts.append("ML DISRUPTS match")
            else:
                improved = True
                notes_parts.append("ML prediction did not disrupt exact match")

            results.append(TermResult(
                term_type="loanword",
                canonical_form=f"{place}:{canon_str}",
                ml_substituted_form=ml_str,
                phonological_improvement="1" if improved else "0",
                ml_reading_plausible="1" if improved else "0",
                substituted_signs=sub_count,
                notes="; ".join(notes_parts),
            ))

    # Also process loanword_matches for high-confidence exact matches
    for match in loanword_matches[:20]:
        greek = match.get("greek", "")
        minoan = match.get("minoan_form", "")
        matched = match.get("matched", "")
        confidence = _parse_float(match.get("confidence_score", "0"))

        key = f"{greek}|{matched}"
        if key in seen:
            continue
        seen.add(key)

        # For loanword matches, check if the matched Minoan form contains
        # any uncertain signs
        matched_clean = matched.strip().upper()
        chunks = []
        i = 0
        while i < len(matched_clean):
            if i + 1 < len(matched_clean):
                chunks.append(matched_clean[i:i + 2])
                i += 2
            else:
                chunks.append(matched_clean[i])
                i += 1

        canonical_parts: list[str] = []
        ml_parts: list[str] = []
        sub_count = 0
        sub_details: list[str] = []

        for chk in chunks:
            found_bid = None
            for bid, info in grid.items():
                cv = (info.get("conventional_value") or "").upper()
                rv = (info.get("refined_value") or "").upper()
                effective = cv if cv and cv != "?" else rv
                if chk == cv or chk == rv or chk == effective:
                    found_bid = bid
                    break

            if found_bid:
                gi = grid[found_bid]
                decision = gi.get("decision", "")
                cv = gi.get("conventional_value", "?")
                rv = gi.get("refined_value", "")
                effective_cv = cv if cv and cv != "?" else rv
                ml_pred = predictions.get(found_bid, "")

                canonical_parts.append(effective_cv.lower() if effective_cv != "?" else chk.lower())
                if decision == "UNCERTAIN" and ml_pred and ml_pred != effective_cv:
                    ml_parts.append(ml_pred)
                    if effective_cv and effective_cv != "?":
                        sub_count += 1
                        sub_details.append(f"{found_bid}: {effective_cv}→{ml_pred}")
                    else:
                        sub_details.append(f"{found_bid}: unknown→{ml_pred}")
                else:
                    ml_parts.append(effective_cv.lower() if effective_cv != "?" else chk.lower())
            else:
                canonical_parts.append(chk.lower())
                ml_parts.append(chk.lower())

        canon_str = "-".join(canonical_parts)
        ml_str = "-".join(ml_parts)

        # Compare ML reading to the Greek word
        notes_parts = [
            f"loanword={greek}→{minoan}",
            f"matched={matched}",
            f"confidence={confidence}",
        ]
        if sub_details:
            notes_parts.append(f"substitutions: {'; '.join(sub_details)}")
        else:
            notes_parts.append("no uncertain signs in match")

        # Determine if ML improves or disrupts: compare phonetic distances
        canon_flat = canon_str.replace("-", "")
        ml_flat = ml_str.replace("-", "")
        greek_flat = greek.lower()

        if sub_count > 0:
            # Check if ML-substituted form is phonetically closer to the Greek
            canon_dist, _ = _compare_phonetic(canon_flat, minoan.lower())
            ml_dist, _ = _compare_phonetic(ml_flat, minoan.lower())
            if ml_dist < canon_dist:
                improved = True
                notes_parts.append("ML IMPROVES match to Minoan form")
            elif ml_dist == canon_dist:
                improved = True
                notes_parts.append("ML NEUTRAL (same phonetic distance)")
            else:
                improved = False
                notes_parts.append("ML DISRUPTS match")
        else:
            improved = True
            notes_parts.append("ML prediction did not disrupt exact match")

        results.append(TermResult(
            term_type="loanword",
            canonical_form=f"{greek}:{canon_str}",
            ml_substituted_form=ml_str,
            phonological_improvement="1" if improved else "0",
            ml_reading_plausible="1" if improved else "0",
            substituted_signs=sub_count,
            notes="; ".join(notes_parts),
        ))

    return results


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_toponym_testing(
    predictions_path: str = DEFAULT_UNCERTAIN_PREDICTIONS,
    grid_path: str = DEFAULT_PHONETIC_GRID,
    toponym_path: str = DEFAULT_TOPONYM_ANCHORS,
    loanword_path: str = DEFAULT_LOANWORD_MATCHES,
    output_path: str = DEFAULT_OUTPUT,
) -> list[TermResult]:
    """Run the full toponym testing pipeline and write results."""
    logger.info("=" * 60)
    logger.info("Toponym & Formula ML Prediction Testing")
    logger.info("=" * 60)

    # Load data
    predictions = load_ml_predictions(predictions_path)
    grid = load_phonetic_grid(grid_path)
    toponym_anchors = load_toponym_anchors(toponym_path)
    loanword_matches = load_loanword_matches(loanword_path)

    # Summarize: which known terms have uncertain signs?
    n_terms_with_uncertain = 0
    for term in KNOWN_TERMS:
        uncertain_bids = [
            bid for bid in term["bennett_ids"]
            if grid.get(bid, {}).get("decision") == "UNCERTAIN"
        ]
        if uncertain_bids:
            n_terms_with_uncertain += 1
            logger.info(
                "  %s has %d UNCERTAIN signs: %s",
                term["canonical_form"],
                len(uncertain_bids),
                ", ".join(uncertain_bids),
            )
    logger.info(
        "%d/%d known terms have UNCERTAIN signs eligible for ML substitution",
        n_terms_with_uncertain,
        len(KNOWN_TERMS),
    )

    # Test each known term
    results: list[TermResult] = []
    for term in KNOWN_TERMS:
        result = test_term(term, grid, predictions)
        results.append(result)
        logger.info(
            "  %s: canonical=%s ML=%s improved=%s plausible=%s subs=%d",
            term["canonical_form"],
            result.canonical_form,
            result.ml_substituted_form,
            result.phonological_improvement,
            result.ml_reading_plausible,
            result.substituted_signs,
        )

    # Test loanword anchors
    loanword_results = test_loanword_anchors(
        toponym_anchors, loanword_matches, grid, predictions
    )
    results.extend(loanword_results)
    logger.info(
        "Added %d loanword anchor results",
        len(loanword_results),
    )

    # Write results
    write_results(results, output_path)

    # Summary
    summary = summarise_results(results)
    logger.info("=" * 60)
    logger.info("Summary: %s", summary)
    logger.info("=" * 60)

    return results


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_results(results: list[TermResult], output_path: str):
    """Write results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "term_type",
        "canonical_form",
        "ml_substituted_form",
        "phonological_improvement",
        "ml_reading_plausible",
        "substituted_signs",
        "notes",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow({
                "term_type": r.term_type,
                "canonical_form": r.canonical_form,
                "ml_substituted_form": r.ml_substituted_form,
                "phonological_improvement": r.phonological_improvement,
                "ml_reading_plausible": r.ml_reading_plausible,
                "substituted_signs": str(r.substituted_signs),
                "notes": r.notes,
            })

    logger.info("Wrote %d result rows to %s", len(results), output_path)


def summarise_results(results: list[TermResult]) -> str:
    """Build a summary string from results."""
    n_total = len(results)
    n_improved = sum(1 for r in results if r.phonological_improvement == "1")
    n_plausible = sum(1 for r in results if r.ml_reading_plausible == "1")
    n_substituted = sum(1 for r in results if r.substituted_signs > 0)

    by_type: dict[str, int] = defaultdict(int)
    for r in results:
        by_type[r.term_type] += 1

    parts = [
        f"Total: {n_total}",
        f"Improved: {n_improved}",
        f"Plausible: {n_plausible}",
        f"With substitutions: {n_substituted}",
        f"By type: {dict(by_type)}",
    ]
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Predictive Toponym & Formula Testing with Phase 4 ML",
    )
    parser.add_argument(
        "--predictions",
        default=DEFAULT_UNCERTAIN_PREDICTIONS,
        help="Path to uncertain_predictions.csv",
    )
    parser.add_argument(
        "--grid",
        default=DEFAULT_PHONETIC_GRID,
        help="Path to refined_phonetic_grid.csv",
    )
    parser.add_argument(
        "--toponyms",
        default=DEFAULT_TOPONYM_ANCHORS,
        help="Path to toponym_anchors.csv",
    )
    parser.add_argument(
        "--loanwords",
        default=DEFAULT_LOANWORD_MATCHES,
        help="Path to loanword_matches.csv",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output CSV path",
    )
    args = parser.parse_args()

    run_toponym_testing(
        predictions_path=args.predictions,
        grid_path=args.grid,
        toponym_path=args.toponyms,
        loanword_path=args.loanwords,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
