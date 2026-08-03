"""Cross-evidence triangulation for Phase 4 ML predictions.

Systematically compares all 94 ML predictions from
data/analysis/ml/uncertain_predictions.csv against independent
evidence sources:

1. CM triangular evidence (cm_suggested_value + cm_triangular_confidence)
2. LB composite scores (lb_composite_score)
3. Positional anomalies (positional_flags from refined grid)
4. N-gram disruption scores

Outputs to data/analysis/verification/cross_evidence_triangulation.csv.
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_float(val: str) -> Optional[float]:
    """Parse a CSV field to float, returning None if empty or unparseable."""
    val = val.strip()
    if not val:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _clean(val: str) -> str:
    """Strip whitespace and trailing question marks from a phonetic value."""
    return val.strip().rstrip("?")


def _is_null(val: str) -> bool:
    """Return True if a phonetic value is effectively absent."""
    return not val or _clean(val) in ("", "?")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_predictions(path: str) -> list[dict]:
    """Load uncertain_predictions.csv and return 94 rows as a list of dicts."""
    preds: list[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            preds.append(
                {
                    "bennett_id": row["bennett_id"].strip(),
                    "conventional_value": row.get("conventional_value", "").strip(),
                    "predicted_refined_value": row.get(
                        "predicted_refined_value", ""
                    ).strip(),
                    "confidence_score": _parse_float(
                        row.get("confidence_score", "0")
                    ),
                    "top3_candidates": row.get("top3_candidates", "").strip(),
                    "evidence_sources": row.get("evidence_sources", "").strip(),
                }
            )
    logger.info("Loaded %d ML predictions", len(preds))
    return preds


def load_refined_grid(path: str) -> dict[str, dict]:
    """Load refined_phonetic_grid.csv keyed by bennett_id."""
    grid: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"].strip()
            grid[bid] = {
                "conventional_value": row.get("conventional_value", "").strip(),
                "lb_proposed_value": row.get("lb_proposed_value", "").strip(),
                "cm_suggested_value": row.get("cm_suggested_value", "").strip(),
                "cm_triangular_confidence": row.get(
                    "cm_triangular_confidence", ""
                ).strip(),
                "lb_composite_score": _parse_float(
                    row.get("lb_composite_score", "")
                ),
                "grid_confidence_score": _parse_float(
                    row.get("grid_confidence_score", "")
                ),
                "positional_flags": row.get("positional_flags", "").strip(),
                "positional_anomaly_rank": _parse_float(
                    row.get("positional_anomaly_rank", "")
                ),
                "ngram_disruption_score": _parse_float(
                    row.get("ngram_disruption_score", "")
                ),
                "ngram_rank": _parse_float(row.get("ngram_rank", "")),
                "conflict_note": row.get("conflict_note", "").strip(),
                "decision": row.get("decision", "").strip(),
            }
    logger.info("Loaded %d signs from refined phonetic grid", len(grid))
    return grid


def load_positional_profiles(path: str) -> dict[str, dict]:
    """Load positional_profiles.csv keyed by bennett_id (for reference)."""
    profiles: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"].strip()
            profiles[bid] = row
    logger.info("Loaded %d positional profiles", len(profiles))
    return profiles


def load_ngram_disruption_index(path: str) -> dict[str, float]:
    """Extract per-sign disruption index from ngram_freqs.csv.

    The refined grid already provides ngram_disruption_score per sign;
    this function exists for API completeness and to provide raw access
    to the n-gram frequency data.  Returns an empty dict since
    ngram_freqs.csv does not contain a direct per-sign disruption index.
    """
    # ngram_freqs.csv contains raw n-gram counts/probabilities, not a
    # per-sign disruption index.  The refined grid synthesises those.
    logger.debug("ngram_freqs.csv does not contain per-sign disruption index")
    return {}

# ---------------------------------------------------------------------------
# Evidence computation
# ---------------------------------------------------------------------------

# Confidence-to-weight mapping for CM evidence.
_CM_WEIGHT: dict[str, float] = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.25}


def compute_cm_agreement(
    ml_predicted: str,
    cm_suggested: str,
    cm_confidence: str,
) -> tuple[Optional[bool], float]:
    """Does the ML prediction agree with the CM suggested value?

    Returns (binary_agreement, confidence_weight):
    - binary_agreement  — True/False if CM data exists, else None
    - confidence_weight — HIGH=1.0, MEDIUM=0.5, LOW=0.25, absent=0.0
    """
    if _is_null(cm_suggested):
        return None, 0.0

    weight = _CM_WEIGHT.get(cm_confidence, 0.25)

    ml_clean = _clean(ml_predicted)
    if _is_null(ml_clean):
        return None, weight

    return ml_clean == _clean(cm_suggested), weight


def compute_lb_agreement(
    ml_predicted: str,
    conv_value: str,
    lb_value: str,
) -> Optional[bool]:
    """Does the ML prediction match the conventional Linear B value?

    Prefers lb_proposed_value from the refined grid; falls back to
    conventional_value.
    """
    lb_target = lb_value if not _is_null(lb_value) else conv_value
    if _is_null(lb_target):
        return None

    ml_clean = _clean(ml_predicted)
    if _is_null(ml_clean):
        return None

    return ml_clean == _clean(lb_target)


def compute_positional_consistency(
    ml_predicted: str,
    conv_value: str,
    positional_flags: str,
) -> Optional[bool]:
    """Check whether the ML prediction might resolve a positional anomaly.

    True  — positional flags exist AND ML prediction differs from
            conventional value (i.e. the ML proposes a change that
            could resolve the anomalous pattern).
    False — positional flags exist but ML prediction matches
            conventional (anomaly persists).
    None  — no positional flags recorded for this sign.
    """
    if not positional_flags:
        return None

    ml_clean = _clean(ml_predicted)
    if _is_null(ml_clean):
        return None

    conv_clean = _clean(conv_value)
    return ml_clean != conv_clean


def compute_ngram_consistency(
    ngram_score: Optional[float],
) -> Optional[bool]:
    """Assess n-gram disruption.

    Low disruption (≤ 0.3) → n-gram patterns *consistent* with ML.
    High disruption (> 0.3) → n-gram patterns *inconsistent*.
    No score → None.
    """
    if ngram_score is None:
        return None
    return ngram_score <= 0.3


def compute_convergence_score(
    cm_agrees: Optional[bool],
    lb_agrees: Optional[bool],
    positional_improved: Optional[bool],
    ngram_consistent: Optional[bool],
) -> int:
    """Count how many evidence sources support the ML prediction (0-4).

    Each source contributes 1 if its agreement indicator is True.
    """
    score = 0
    if cm_agrees is True:
        score += 1
    if lb_agrees is True:
        score += 1
    if positional_improved is True:
        score += 1
    if ngram_consistent is True:
        score += 1
    return score


def generate_conflict_flag(
    cm_agrees: Optional[bool],
    lb_agrees: Optional[bool],
    positional_improved: Optional[bool],
    ngram_consistent: Optional[bool],
    convergence: int,
) -> str:
    """Categorise the overall evidence pattern.

    Returns one of:
        convergent                     — 3+ sources agree
        cm_conflict                    — CM disagrees with ML
        lb_conflict                    — LB disagrees with ML
        cm_conflict; lb_conflict       — both CM and LB disagree
        positional_anomaly_unresolved  — flags exist, not improved
        ngram_disruption               — high ngram disruption
        no_conflict                    — sources exist, no disagreement
        no_evidence                    — no usable evidence at all
    """
    if convergence >= 3:
        return "convergent"

    flags: list[str] = []

    if cm_agrees is False:
        flags.append("cm_conflict")
    if lb_agrees is False:
        flags.append("lb_conflict")
    if positional_improved is False:
        flags.append("positional_anomaly_unresolved")
    if ngram_consistent is False:
        flags.append("ngram_disruption")

    if not flags:
        any_evidence = any(
            x is not None
            for x in (cm_agrees, lb_agrees, positional_improved, ngram_consistent)
        )
        return "no_conflict" if any_evidence else "no_evidence"

    return "; ".join(flags)

# ---------------------------------------------------------------------------
# Record
# ---------------------------------------------------------------------------


@dataclass
class TriangulationRecord:
    """One sign's cross-evidence triangulation result."""

    bennett_id: str
    conventional_value: str
    ml_predicted: str
    ml_confidence: float
    cm_agrees: Optional[bool]
    lb_agrees: Optional[bool]
    positional_consistency_improved: Optional[bool]
    ngram_consistency: Optional[bool]
    convergence_score: int
    conflict_flag: str
    notes: str = ""

    def validate(self) -> None:
        """Assert invariants."""
        assert 0 <= self.convergence_score <= 4, (
            f"convergence_score {self.convergence_score} out of [0,4]"
        )
        # cm_agrees / lb_agrees / positional / ngram are Optional[bool] — ok

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_triangulation(
    predictions_path: str,
    grid_path: str,
    output_path: str,
) -> list[TriangulationRecord]:
    """Run cross-evidence triangulation and write the output CSV.

    Args:
        predictions_path: Path to data/analysis/ml/uncertain_predictions.csv
        grid_path:        Path to data/analysis/comparative/refined_phonetic_grid.csv
        output_path:      Destination CSV path

    Returns:
        List of TriangulationRecord instances (one per UNCERTAIN sign).
    """
    predictions = load_predictions(predictions_path)
    grid = load_refined_grid(grid_path)

    records: list[TriangulationRecord] = []

    for pred in predictions:
        bid = pred["bennett_id"]
        g = grid.get(bid, {})

        ml_pred = pred["predicted_refined_value"]
        conv_val = pred["conventional_value"]
        ml_conf = pred["confidence_score"] or 0.0

        cm_val = g.get("cm_suggested_value", "")
        cm_conf = g.get("cm_triangular_confidence", "")
        lb_val = g.get("lb_proposed_value", "")
        pos_flags = g.get("positional_flags", "")
        ngram_score: Optional[float] = g.get("ngram_disruption_score")

        # ---- compute each evidence stream ----
        cm_agrees, cm_weight = compute_cm_agreement(ml_pred, cm_val, cm_conf)
        lb_agrees = compute_lb_agreement(ml_pred, conv_val, lb_val)
        pos_improved = compute_positional_consistency(
            ml_pred, conv_val, pos_flags
        )
        ng_consistent = compute_ngram_consistency(ngram_score)

        convergence = compute_convergence_score(
            cm_agrees, lb_agrees, pos_improved, ng_consistent
        )

        conflict_flag = generate_conflict_flag(
            cm_agrees, lb_agrees, pos_improved, ng_consistent, convergence
        )

        # ---- notes ----
        note_parts: list[str] = []
        if cm_agrees is not None:
            note_parts.append(
                f"CM={'agrees' if cm_agrees else 'disagrees'}"
                f" ({cm_conf}, weight={cm_weight:.2f})"
            )
        if lb_agrees is not None:
            note_parts.append(f"LB={'agrees' if lb_agrees else 'disagrees'}")
        if pos_improved is not None:
            note_parts.append(
                f"Pos={'improved' if pos_improved else 'unchanged'}"
            )
        if ng_consistent is not None:
            label = "consistent" if ng_consistent else "disrupted"
            note_parts.append(f"Ngram={ngram_score:.3f} ({label})")
        if g.get("conflict_note"):
            note_parts.append(f"Grid: {g['conflict_note']}")

        record = TriangulationRecord(
            bennett_id=bid,
            conventional_value=conv_val,
            ml_predicted=ml_pred,
            ml_confidence=round(ml_conf, 4),
            cm_agrees=cm_agrees,
            lb_agrees=lb_agrees,
            positional_consistency_improved=pos_improved,
            ngram_consistency=ng_consistent,
            convergence_score=convergence,
            conflict_flag=conflict_flag,
            notes="; ".join(note_parts),
        )
        record.validate()
        records.append(record)

    # ---- write CSV ----
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        "bennett_id",
        "conventional_value",
        "ml_predicted",
        "ml_confidence",
        "cm_agrees",
        "lb_agrees",
        "positional_consistency_improved",
        "ngram_consistency",
        "convergence_score",
        "conflict_flag",
        "notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))

    logger.info(
        "Wrote %d triangulation records to %s", len(records), output_path
    )
    return records
