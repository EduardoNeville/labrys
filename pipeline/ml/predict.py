"""Predict refined phonetic values for UNCERTAIN Linear A signs.

Uses the trained phonetic classifier's token embeddings plus all available
evidence (LB composite, CM triangular, grid confidence) to generate a
prediction for each UNCERTAIN sign in the refined phonetic grid.

The prediction blends:
- Embedding-space nearest-neighbour similarity to CONFIRMED signs
- Existing grid confidence scores from Phases 2–5
- LB composite scores (Linear B transfer confidence)
- CM triangular confidence (Cypro-Minoan inference)

Output is written to data/analysis/ml/uncertain_predictions.csv with:
bennett_id, conventional_value, predicted_refined_value, confidence_score,
top3_candidates, evidence_sources
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import torch

from pipeline.ml.contrastive import _load_phonetic_classes

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────


def _load_refined_grid(path: str) -> List[Dict[str, str]]:
    """Load the refined phonetic grid as list of dicts."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _parse_float(val: str, default: float = 0.0) -> float:
    """Safely parse a float or return default."""
    if not val or val.strip() == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _cm_to_score(level: str) -> float:
    """Map CM confidence level to numeric score."""
    mapping = {"HIGH": 80.0, "MEDIUM": 50.0, "LOW": 25.0}
    return mapping.get((level or "").strip().upper(), 0.0)


def _load_embeddings_and_mappings(
    embeddings_path: str,
    refined_grid_path: str,
) -> Tuple[
    Dict[str, torch.Tensor],
    Dict[str, str],
    Dict[str, int],
]:
    """Load embeddings and build sign→value mapping for CONFIRMED signs.

    Returns
    -------
    confirmed_embeddings : dict
        bennett_id → L2-normalised embedding tensor for CONFIRMED signs.
    confirmed_values : dict
        bennett_id → refined phonetic value for CONFIRMED signs.
    bennett_to_coarse : dict
        bennett_id → coarse phonetic class ID (for all signs with a class).
    """
    data = torch.load(embeddings_path, map_location="cpu", weights_only=False)
    all_emb: torch.Tensor = data["embeddings"]
    all_bids: List[str] = data["bennett_ids"]

    # Map bennett_id to its embedding
    emb_by_bid: Dict[str, torch.Tensor] = {}
    for i, bid in enumerate(all_bids):
        emb_by_bid[bid] = all_emb[i]

    # Get CONFIRMED signs and their refined values from the grid
    confirmed_values: Dict[str, str] = {}
    grid_rows = _load_refined_grid(refined_grid_path)
    for row in grid_rows:
        bid = row["bennett_id"].strip()
        dec = row["decision"].strip()
        val = row["refined_value"].strip()
        if dec == "CONFIRM" and val and val != "?" and bid in emb_by_bid:
            confirmed_values[bid] = val

    logger.info(
        "Loaded %d CONFIRMED signs with embeddings (%d total signs)",
        len(confirmed_values),
        len(emb_by_bid),
    )

    # Also get coarse class mapping for all signs
    bennett_to_coarse, _, _ = _load_phonetic_classes(
        refined_grid_path, coarse=True
    )

    return emb_by_bid, confirmed_values, bennett_to_coarse


def _top_k_neighbors(
    query_bid: str,
    query_emb: torch.Tensor,
    candidate_embeddings: Dict[str, torch.Tensor],
    candidate_values: Dict[str, str],
    k: int = 3,
) -> List[Tuple[str, str, float]]:
    """Return top-k nearest CONFIRMED neighbours with their values.

    Returns
    -------
    list of (bennett_id, phonetic_value, cosine_similarity)
    """
    results = []
    query_norm = query_emb / query_emb.norm(p=2)

    for cbid, cemb in candidate_embeddings.items():
        if cbid == query_bid:
            continue
        cval = candidate_values.get(cbid, "?")
        cemb_norm = cemb / cemb.norm(p=2)
        sim = (query_norm * cemb_norm).sum().item()
        results.append((cbid, cval, sim))

    results.sort(key=lambda x: x[2], reverse=True)
    return results[:k]


def _compute_confidence(
    nn_similarity: float,
    grid_confidence: float,
    lb_composite: float,
    cm_score: float,
) -> float:
    """Compute a blended confidence score in [0, 1].

    Weights:
    - Nearest-neighbor similarity: 40% (when available)
    - Grid confidence (Phase 3): 25%
    - LB composite (Phase 5): 20%
    - CM triangular (Phase 5): 15%

    Scores are clamped to [0, 1].
    """
    weights = [0.40, 0.25, 0.20, 0.15]
    values = [nn_similarity, grid_confidence, lb_composite, cm_score]

    # If no embedding available, redistribute weight to grid evidence
    if nn_similarity <= 0.0:
        weights = [0.0, 0.45, 0.30, 0.25]
        values = [0.0, grid_confidence, lb_composite, cm_score]

    score = sum(w * v / 100.0 if v > 1.0 else w * v for w, v in zip(weights, values))
    return round(max(0.0, min(1.0, score)), 4)


def _build_evidence_sources(
    row: Dict[str, str],
    top3: List[Tuple[str, str, float]],
    has_embedding: bool,
) -> str:
    """Build human-readable evidence string."""
    parts = []

    if has_embedding and top3:
        best_bid, best_val, best_sim = top3[0]
        parts.append(
            f"NN: {best_bid}={best_val} (cos={best_sim:.3f})"
        )
    else:
        parts.append("NN: no embedding available")

    gc = _parse_float(row.get("grid_confidence_score", ""))
    if gc > 0:
        parts.append(f"GC={gc:.0f}")

    lb = _parse_float(row.get("lb_composite_score", ""))
    if lb > 0:
        parts.append(f"LB={lb:.0f}")

    cm = row.get("cm_triangular_confidence", "").strip()
    if cm:
        parts.append(f"CM={cm}")

    evidence = row.get("evidence_summary", "").strip()
    if evidence and evidence != "no evidence":
        parts.append(f"summary: {evidence}")

    return "; ".join(parts)


def _format_top3(top3: List[Tuple[str, str, float]]) -> str:
    """Format top3 candidates as a semicolon-separated string."""
    if not top3:
        return "?"
    return "; ".join(
        f"{bid}={val} ({sim:.3f})"
        for bid, val, sim in top3
    )


# ── main prediction pipeline ────────────────────────────────────────────────


def predict_uncertain_signs(
    refined_grid_path: str = "data/analysis/comparative/refined_phonetic_grid.csv",
    embeddings_path: str = "data/analysis/ml/classifier_embeddings.pt",
    output_path: str = "data/analysis/ml/uncertain_predictions.csv",
) -> str:
    """Run inference on all UNCERTAIN signs and write predictions CSV.

    Returns path to the written CSV.
    """
    # Load embeddings and mappings
    emb_by_bid, confirmed_values, bennett_to_coarse = _load_embeddings_and_mappings(
        embeddings_path, refined_grid_path,
    )
    confirmed_embeddings = {
        bid: emb_by_bid[bid]
        for bid in confirmed_values
        if bid in emb_by_bid
    }

    grid_rows = _load_refined_grid(refined_grid_path)

    # Build lookup for all grid info by bennett_id
    grid_by_bid: Dict[str, Dict[str, str]] = {}
    for row in grid_rows:
        grid_by_bid[row["bennett_id"].strip()] = row

    # Process UNCERTAIN signs
    predictions: List[Dict[str, str]] = []
    uncertain_count = 0

    for row in grid_rows:
        bid = row["bennett_id"].strip()
        decision = row["decision"].strip()

        if decision != "UNCERTAIN":
            continue

        uncertain_count += 1
        conv_val = row["conventional_value"].strip() or "?"
        has_emb = bid in emb_by_bid

        # Nearest-neighbour lookup
        top3: List[Tuple[str, str, float]] = []
        nn_similarity = 0.0

        if has_emb:
            query_emb = emb_by_bid[bid]
            top3 = _top_k_neighbors(
                bid, query_emb, confirmed_embeddings, confirmed_values, k=3
            )
            nn_similarity = top3[0][2] if top3 else 0.0

        predicted_value = top3[0][1] if top3 else "?"

        # If no embedding or very low NN similarity, fall back to the
        # existing refined_value if it has some evidence behind it.
        if not top3 or nn_similarity < 0.3:
            refined_val = row["refined_value"].strip()
            if refined_val and refined_val != "?":
                predicted_value = refined_val
            elif conv_val and conv_val != "?":
                predicted_value = conv_val

        # Compute confidence
        gc = _parse_float(row.get("grid_confidence_score", "")) / 100.0
        lb = _parse_float(row.get("lb_composite_score", "")) / 100.0
        cm_raw = row.get("cm_triangular_confidence", "").strip()
        cm = _cm_to_score(cm_raw) / 100.0

        confidence = _compute_confidence(nn_similarity, gc * 100, lb * 100, cm * 100)

        # Build evidence
        evidence = _build_evidence_sources(row, top3, has_emb)
        top3_str = _format_top3(top3)

        predictions.append({
            "bennett_id": bid,
            "conventional_value": conv_val,
            "predicted_refined_value": predicted_value,
            "confidence_score": str(confidence),
            "top3_candidates": top3_str,
            "evidence_sources": evidence,
        })

    # Write CSV
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "bennett_id",
        "conventional_value",
        "predicted_refined_value",
        "confidence_score",
        "top3_candidates",
        "evidence_sources",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(predictions)

    # Summary stats
    confidences = [float(p["confidence_score"]) for p in predictions]
    high = sum(1 for c in confidences if c > 0.7)
    med = sum(1 for c in confidences if 0.4 <= c <= 0.7)
    low = sum(1 for c in confidences if c < 0.4)

    logger.info(
        "Wrote %d predictions to %s",
        len(predictions),
        out_path,
    )
    logger.info(
        "Confidence: high (>0.7)=%d, medium (0.4-0.7)=%d, low (<0.4)=%d",
        high, med, low,
    )

    return str(out_path)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    grid = sys.argv[1] if len(sys.argv) > 1 else "data/analysis/comparative/refined_phonetic_grid.csv"
    emb = sys.argv[2] if len(sys.argv) > 2 else "data/analysis/ml/classifier_embeddings.pt"
    out = sys.argv[3] if len(sys.argv) > 3 else "data/analysis/ml/uncertain_predictions.csv"

    path = predict_uncertain_signs(grid, emb, out)
    print(f"Predictions written to {path}")
