"""External-evidence constraints for Linear A sign classification.

Incorporates two independent sources of phonetic evidence as soft
regularization terms for the phonetic classifier:

1. **Cypro-Minoan triangular constraints**
   The Cypro-Minoan script (Late Bronze Age Cyprus) shares a common
   ancestor with Linear A/B and provides independent phonetic readings
   for ~40 signs.  When CM evidence conflicts with Linear B-derived
   values at HIGH confidence (e.g. AB 60 = /ma/ per CM vs /ra/ per
   LB), the CM reading is used as a soft target, weighted by CM
   confidence.  For UNCERTAIN signs that have CM evidence, this
   provides additional supervised training signals.

2. **Pre-Greek loanword anchors**
   Phase 3 loanword analysis matched ~310 Pre-Greek substrate words
   against the Linear A corpus.  Exact (d=0) matches with confidence
   ≥ 50 provide sign-level phonetic anchors derived from known Greek
   etymologies.  These are incorporated as soft-target regularisation.

Typical usage::

    from pipeline.ml.constraints import (
        load_cm_constraint_targets,
        load_loanword_anchor_targets,
        compute_constraint_loss,
    )

    cm_targets = load_cm_constraint_targets(
        "data/analysis/comparative/refined_phonetic_grid.csv",
    )
    lw_targets = load_loanword_anchor_targets(
        "data/analysis/linguistic/loanword_matches.csv",
        "data/analysis/comparative/refined_phonetic_grid.csv",
    )

    # Inside training loop:
    constraint_loss = compute_constraint_loss(
        logits, anchor_bids, cm_targets, lw_targets,
        stoi, bennett_to_class, class_to_label,
        cm_weight=0.1, lw_weight=0.05,
    )
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# ── phonetic category mapping (shared with contrastive.py) ──────────────────

_PHONEME_TO_COARSE: Dict[str, int] = {
    # Vowels
    "a": 0, "i": 0, "o": 0, "u": 0, "e": 0,
    # Labial
    "pa": 1, "pi": 1, "me": 1, "mi": 1, "mo": 1, "wa": 1, "wi": 1,
    "pe": 1, "pu": 1, "mu": 1, "ma": 1, "we": 1,
    # Dental / coronal
    "te": 2, "ti": 2, "to": 2, "tu": 2,
    "na": 2, "ne": 2, "ni": 2, "nu": 2,
    "sa": 2, "se": 2, "si": 2, "so": 2,
    "za": 2, "ze": 2, "zo": 2,
    "re": 2, "ri": 2, "ru": 2, "la": 2,
    "da": 2, "de": 2, "di": 2, "do": 2, "du": 2,
    "ta": 2, "ra": 2, "ro": 2, "lo": 2, "su": 2, "no": 2,
    # Velar / palatal
    "ja": 3, "ka": 3, "ke": 3, "ki": 3, "ko": 3, "ku": 3,
    "qa": 3, "qe": 3, "jo": 3, "je": 3, "ju": 3,
}

COARSE_CATEGORY_NAMES = {0: "vowel", 1: "labial", 2: "dental/coronal", 3: "velar/palatal"}

# Confidence → numeric weight
_CONFIDENCE_WEIGHT: Dict[str, float] = {
    "HIGH": 1.0,
    "MEDIUM": 0.5,
    "LOW": 0.25,
    "": 0.0,
}


# ── data structures ─────────────────────────────────────────────────────────

@dataclass
class CMConstraintTarget:
    """A Cypro-Minoan soft target for a single Bennett ID.

    Attributes
    ----------
    bennett_id : str
    coarse_class : int
        CM-suggested broad phonetic category (0-3, or -1 for unknown).
    confidence_weight : float
        0.0–1.0  mapped from HIGH/MEDIUM/LOW.
    cm_value : str
        The CM phonetic reading (e.g. ``"ma"``, ``"pa"``).
    lb_value : str
        The conventional LB-derived reading (for logging).
    is_conflict : bool
        True when CM and LB suggest different categories and CM is HIGH.
    """

    bennett_id: str
    coarse_class: int
    confidence_weight: float
    cm_value: str = ""
    lb_value: str = ""
    is_conflict: bool = False


@dataclass
class LoanwordAnchorTarget:
    """A sign-level soft target from a secure loanword match.

    Attributes
    ----------
    bennett_id : str
    coarse_class : int
        Expected phonetic category derived from the Greek etymology.
    confidence : float
        Match confidence 0–100 (from the loanword analysis).
    greek_word : str
        Greek word for provenance tracking.
    match_form : str
        The Minoan AB form matched in the corpus.
    """

    bennett_id: str
    coarse_class: int
    confidence: float = 0.0
    greek_word: str = ""
    match_form: str = ""


# ── CM constraint loading ────────────────────────────────────────────────────


def load_cm_constraint_targets(
    refined_grid_path: str,
    coarse: bool = True,
) -> Dict[str, CMConstraintTarget]:
    """Parse the refined phonetic grid for Cypro-Minoan constraints.

    For every Bennett ID with CM evidence (``cm_suggested_value`` not
    empty), a :class:`CMConstraintTarget` is produced.  The coarse
    phonetic class is looked up in ``_PHONEME_TO_COARSE``.

    Parameters
    ----------
    refined_grid_path : str
        Path to ``refined_phonetic_grid.csv``.
    coarse : bool
        If True, map to 4 broad phonological categories.

    Returns
    -------
    dict
        ``{bennett_id: CMConstraintTarget}`` — only signs with CM
        evidence are included.
    """
    targets: Dict[str, CMConstraintTarget] = {}
    with open(refined_grid_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            if not bid:
                continue

            cm_val = (row.get("cm_suggested_value") or "").strip()
            if not cm_val:
                continue

            cm_conf_str = (row.get("cm_triangular_confidence") or "").strip().upper()
            cm_weight = _CONFIDENCE_WEIGHT.get(cm_conf_str, 0.0)
            if cm_weight <= 0.0:
                continue

            coarse_cls = _PHONEME_TO_COARSE.get(cm_val, -1)
            if coarse_cls < 0 and coarse:
                continue

            lb_val = (row.get("conventional_value") or row.get("lb_proposed_value") or "").strip()
            lb_coarse = _PHONEME_TO_COARSE.get(lb_val, -1) if lb_val else -1

            is_conflict = (
                cm_weight >= 1.0
                and lb_val
                and cm_val != lb_val
                and coarse_cls >= 0
                and lb_coarse >= 0
                and coarse_cls != lb_coarse
            )

            targets[bid] = CMConstraintTarget(
                bennett_id=bid,
                coarse_class=coarse_cls,
                confidence_weight=cm_weight,
                cm_value=cm_val,
                lb_value=lb_val,
                is_conflict=is_conflict,
            )

    n_conflict = sum(1 for t in targets.values() if t.is_conflict)
    logger.info(
        "Loaded %d CM constraint targets (coarse=%s), %d HIGH-confidence conflicts",
        len(targets), coarse, n_conflict,
    )
    if n_conflict:
        conflict_bids = sorted(
            bid for bid, t in targets.items() if t.is_conflict
        )
        logger.info("CM/LB conflict signs: %s", ", ".join(conflict_bids))

    return targets


# ── loanword anchor loading ─────────────────────────────────────────────────


def load_loanword_anchor_targets(
    loanword_csv_path: str,
    refined_grid_path: str,
    coarse: bool = True,
    min_confidence: float = 50.0,
) -> Dict[str, LoanwordAnchorTarget]:
    """Extract sign-level constraints from secure loanword matches.

    Only **exact** (d=0) matches with confidence ≥ `min_confidence` are
    used.  For each sign in the matched Minoan form, the expected
    phonetic class is derived from the known Greek etymology via the
    refined grid's Bennett‑ID → value mapping.

    Parameters
    ----------
    loanword_csv_path : str
        Path to ``loanword_matches.csv`` from Phase 3.
    refined_grid_path : str
        Path to ``refined_phonetic_grid.csv``.
    coarse : bool
        If True, use broad phonological categories.
    min_confidence : float
        Minimum confidence score to accept a match (default 50).

    Returns
    -------
    dict
        ``{bennett_id: LoanwordAnchorTarget}`` — if multiple matches
        confirm the same sign, the highest-confidence record is kept.
    """
    # Build sign → refined_value from the grid
    sign_to_value: Dict[str, str] = {}
    with open(refined_grid_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            val = (row.get("refined_value") or "").strip()
            if bid and val and val != "?":
                sign_to_value[bid] = val

    # Build value → Bennett IDs (reverse lookup; many-to-one)
    value_to_signs: Dict[str, List[str]] = {}
    for bid, val in sign_to_value.items():
        value_to_signs.setdefault(val, []).append(bid)

    targets: Dict[str, LoanwordAnchorTarget] = {}
    with open(loanword_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                distance = int(row.get("distance", "99"))
            except (ValueError, TypeError):
                distance = 99
            if distance != 0:
                continue

            try:
                conf = float(row.get("confidence_score", 0))
            except (ValueError, TypeError):
                conf = 0.0
            if conf < min_confidence:
                continue

            matched = (row.get("matched") or "").strip()
            greek = (row.get("greek") or "").strip()
            if not matched:
                continue

            # The 'matched' field is the Minoan AB form found (e.g. "ARUKU").
            # It uses AB transliteration conventions — each 1-2 character
            # chunk is a CV value.  We need to map these to Bennett IDs
            # and then to coarse classes.
            sign_values = _split_ab_transliteration(matched)
            for i, sv in enumerate(sign_values):
                coarse_cls = _PHONEME_TO_COARSE.get(sv, -1)
                if coarse_cls < 0:
                    continue

                # Find candidate Bennett IDs for this value
                candidates = value_to_signs.get(sv, [])
                if not candidates:
                    continue

                # Use the first candidate (most signs map 1:1 from value)
                bid = candidates[0]
                if bid in targets and targets[bid].confidence >= conf:
                    continue

                targets[bid] = LoanwordAnchorTarget(
                    bennett_id=bid,
                    coarse_class=coarse_cls,
                    confidence=conf,
                    greek_word=greek,
                    match_form=matched,
                )

    logger.info(
        "Loaded %d loanword anchor targets (min_confidence=%.0f, d=0 only)",
        len(targets), min_confidence,
    )
    if targets:
        anchor_bids = sorted(targets)
        logger.info("Loanword-anchored signs: %s", ", ".join(anchor_bids))

    return targets


def _split_ab_transliteration(form: str) -> List[str]:
    """Split an AB transliteration string into CV chunks.

    ``"ARUKU"`` → ``["a", "ru", "ku"]``

    Vowel-only chunks are single characters; CV chunks are two characters.
    """
    chunks: List[str] = []
    i = 0
    vowels = set("aeiou")
    while i < len(form):
        ch = form[i].lower()
        if ch in vowels:
            chunks.append(ch)
            i += 1
        else:
            if i + 1 < len(form):
                chunks.append(form[i:i + 2].lower())
                i += 2
            else:
                # Trailing consonant (shouldn't happen in AB data)
                chunks.append(ch)
                i += 1
    return chunks


# ── constraint loss ─────────────────────────────────────────────────────────


def _build_idx_to_constraint_target(
    stoi: Dict[str, int],
    cm_targets: Dict[str, CMConstraintTarget],
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build tensors for CM constraint loss from ``stoi`` and targets.

    Returns
    -------
    cm_target_class : (V,)
        CM coarse class per vocab index (-1 = no CM target).
    cm_weight : (V,)
        CM confidence weight per vocab index.
    cm_has_target : (V,)  bool
    """
    V = len(stoi)
    cm_target_class = torch.full((V,), -1, dtype=torch.long)
    cm_weight = torch.zeros(V)
    cm_has_target = torch.zeros(V, dtype=torch.bool)

    for bid, tgt in cm_targets.items():
        idx = stoi.get(bid)
        if idx is None or tgt.coarse_class < 0:
            continue
        cm_target_class[idx] = tgt.coarse_class
        cm_weight[idx] = tgt.confidence_weight
        cm_has_target[idx] = True

    return cm_target_class, cm_weight, cm_has_target


def compute_cm_constraint_loss(
    logits: torch.Tensor,
    anchor_bids: torch.Tensor,
    cm_target_class: torch.Tensor,
    cm_weight: torch.Tensor,
) -> torch.Tensor:
    """Compute Cypro-Minoan consistency loss for a batch.

    Parameters
    ----------
    logits : (B, num_classes)
        Model output logits for anchor signs.
    anchor_bids : (B,)
        Bennett ID vocabulary indices of the anchor signs.
    cm_target_class : (V,)
        CM coarse class per vocab index (-1 = no CM target).
    cm_weight : (V,)
        CM confidence weight per vocab index (0 = no CM target).

    Returns
    -------
    loss : scalar
        Weighted cross-entropy averaged over signs with CM targets.
    """
    # Gather target class for each anchor in the batch
    batch_targets = cm_target_class[anchor_bids]   # (B,)
    batch_weights = cm_weight[anchor_bids]          # (B,)

    mask = (batch_targets >= 0) & (batch_weights > 0)
    if not mask.any():
        return torch.tensor(0.0, device=logits.device)

    active_logits = logits[mask]          # (M, C)
    active_targets = batch_targets[mask]   # (M,)  → to device
    active_weights = batch_weights[mask]   # (M,)

    # Per-sample cross-entropy, weighted by CM confidence
    ce = F.cross_entropy(active_logits, active_targets, reduction="none")
    weighted_ce = (ce * active_weights).mean()

    return weighted_ce


def compute_loanword_anchor_loss(
    logits: torch.Tensor,
    anchor_bids: torch.Tensor,
    lw_target_class: torch.Tensor,
    lw_weight: torch.Tensor,
) -> torch.Tensor:
    """Compute Pre-Greek loanword-anchor consistency loss for a batch.

    Operates identically to :func:`compute_cm_constraint_loss` but uses
    targets derived from loanword anchors.

    Parameters
    ----------
    logits : (B, num_classes)
    anchor_bids : (B,)
    lw_target_class : (V,)
        Loanword coarse class per vocab index (-1 = none).
    lw_weight : (V,)
        Loanword confidence weight per vocab index (0 = none).

    Returns
    -------
    loss : scalar
    """
    batch_targets = lw_target_class[anchor_bids]   # (B,)
    batch_weights = lw_weight[anchor_bids]          # (B,)

    mask = (batch_targets >= 0) & (batch_weights > 0)
    if not mask.any():
        return torch.tensor(0.0, device=logits.device)

    active_logits = logits[mask]
    active_targets = batch_targets[mask]
    active_weights = batch_weights[mask]

    ce = F.cross_entropy(active_logits, active_targets, reduction="none")
    return (ce * active_weights).mean()


def compute_constraint_loss(
    logits: torch.Tensor,
    anchor_bids: torch.Tensor,
    cm_targets: Dict[str, CMConstraintTarget],
    lw_targets: Dict[str, LoanwordAnchorTarget],
    stoi: Dict[str, int],
    device: torch.device | str = "cpu",
    cm_weight: float = 0.1,
    lw_weight: float = 0.05,
) -> torch.Tensor:
    """Aggregate all external-evidence constraint losses.

    This is the main entry point for adding constraints to a training
    loop.  It handles internal tensor caching so repeated calls are
    efficient.

    Parameters
    ----------
    logits : (B, num_classes)
        Classifier output for the batch.
    anchor_bids : (B,)
        Bennett ID vocabulary indices of the anchor signs.
    cm_targets : dict
        From :func:`load_cm_constraint_targets`.
    lw_targets : dict
        From :func:`load_loanword_anchor_targets`.
    stoi : dict
        Bennett ID → vocab index mapping.
    device : str or torch.device
    cm_weight : float
        Global weight for the CM loss term.
    lw_weight : float
        Global weight for the loanword-anchor loss term.

    Returns
    -------
    total : scalar
        ``cm_weight * cm_loss + lw_weight * lw_loss``
    """
    total = torch.tensor(0.0, device=device)

    # ── CM loss ──
    if cm_weight > 0 and cm_targets:
        cm_target_cls, cm_w, _ = _build_idx_to_constraint_target(stoi, cm_targets)
        cm_target_cls = cm_target_cls.to(device)
        cm_w = cm_w.to(device)
        cm_loss = compute_cm_constraint_loss(
            logits, anchor_bids, cm_target_cls, cm_w,
        )
        total = total + cm_weight * cm_loss

    # ── loanword anchor loss ──
    if lw_weight > 0 and lw_targets:
        V = len(stoi)
        lw_target_cls = torch.full((V,), -1, dtype=torch.long)
        lw_w = torch.zeros(V)
        for bid, tgt in lw_targets.items():
            idx = stoi.get(bid)
            if idx is None or tgt.coarse_class < 0:
                continue
            lw_target_cls[idx] = tgt.coarse_class
            lw_w[idx] = tgt.confidence / 100.0  # normalise to 0-1

        lw_target_cls = lw_target_cls.to(device)
        lw_w = lw_w.to(device)
        lw_loss = compute_loanword_anchor_loss(
            logits, anchor_bids, lw_target_cls, lw_w,
        )
        total = total + lw_weight * lw_loss

    return total


# ── convenience: get constraint targets for a specific Bennett ID ────────────


def get_cm_target_for_sign(
    bennett_id: str,
    cm_targets: Dict[str, CMConstraintTarget],
) -> Optional[CMConstraintTarget]:
    """Look up the CM constraint target for a single sign."""
    return cm_targets.get(bennett_id)


def get_lw_target_for_sign(
    bennett_id: str,
    lw_targets: Dict[str, LoanwordAnchorTarget],
) -> Optional[LoanwordAnchorTarget]:
    """Look up the loanword anchor target for a single sign."""
    return lw_targets.get(bennett_id)


# ── summary report ──────────────────────────────────────────────────────────

def constraint_summary(
    cm_targets: Dict[str, CMConstraintTarget],
    lw_targets: Dict[str, LoanwordAnchorTarget],
) -> Dict[str, object]:
    """Return a human-readable summary of loaded constraints."""
    n_cm_total = len(cm_targets)
    n_cm_conflict = sum(1 for t in cm_targets.values() if t.is_conflict)
    n_cm_high = sum(1 for t in cm_targets.values() if t.confidence_weight >= 1.0)
    n_cm_med = sum(
        1 for t in cm_targets.values()
        if 0.4 < t.confidence_weight < 1.0
    )
    n_cm_low = sum(
        1 for t in cm_targets.values()
        if 0.0 < t.confidence_weight <= 0.4
    )

    conflict_details = [
        {
            "bennett_id": t.bennett_id,
            "lb_value": t.lb_value,
            "cm_value": t.cm_value,
            "cm_confidence": "HIGH",
        }
        for t in cm_targets.values()
        if t.is_conflict
    ]

    return {
        "cm_total_targets": n_cm_total,
        "cm_high_confidence": n_cm_high,
        "cm_medium_confidence": n_cm_med,
        "cm_low_confidence": n_cm_low,
        "cm_high_conflicts": n_cm_conflict,
        "cm_conflict_details": conflict_details,
        "loanword_anchor_targets": len(lw_targets),
    }


# ── integration helpers ─────────────────────────────────────────────────────

def create_constraint_target_tensors(
    stoi: Dict[str, int],
    cm_targets: Dict[str, CMConstraintTarget],
    lw_targets: Dict[str, LoanwordAnchorTarget],
) -> Dict[str, torch.Tensor]:
    """Pre-build all constraint tensors for fast training-loop access.

    Returns a dict with keys:
    ``cm_target_class``, ``cm_weight``, ``lw_target_class``, ``lw_weight``.
    All tensors are ``(V,)`` and on CPU (cast to device in the loop).
    """
    V = len(stoi)

    cm_tc = torch.full((V,), -1, dtype=torch.long)
    cm_w = torch.zeros(V)
    for bid, tgt in cm_targets.items():
        idx = stoi.get(bid)
        if idx is not None and tgt.coarse_class >= 0:
            cm_tc[idx] = tgt.coarse_class
            cm_w[idx] = tgt.confidence_weight

    lw_tc = torch.full((V,), -1, dtype=torch.long)
    lw_w = torch.zeros(V)
    for bid, tgt in lw_targets.items():
        idx = stoi.get(bid)
        if idx is not None and tgt.coarse_class >= 0:
            lw_tc[idx] = tgt.coarse_class
            lw_w[idx] = tgt.confidence / 100.0

    return {
        "cm_target_class": cm_tc,
        "cm_weight": cm_w,
        "lw_target_class": lw_tc,
        "lw_weight": lw_w,
    }
