#!/usr/bin/env python3
"""
Internal Consistency Analysis of ML Predictions for Linear A
=============================================================

Tests whether applying ML predictions to UNCERTAIN signs improves the
internal linguistic consistency of the Linear A corpus across five
dimensions:

  1. CV pattern consistency — do ML predictions reduce CV-structure
     anomalies in syllabograms?
  2. Word boundary consistency — does re-running segmentation with
     ML values improve boundary agreement?
  3. N-gram entropy — does bigram/trigram entropy decrease (more
     structured language) or increase (more noise)?
  4. Sign co-occurrence — do ML-predicted values place phonetically
     similar signs closer in the co-occurrence network?
  5. Composite before/after comparison across all metrics.

Output
------
``data/analysis/verification/consistency_metrics.csv``
  Columns: metric_name, before_ml, after_ml, delta, improved (0/1), notes

Usage
-----
``uv run python pipeline/verification/internal_consistency.py``
"""

from __future__ import annotations

import csv
import logging
import math
import os
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("internal_consistency")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "lineara_full.db")
UNCERTAIN_PREDICTIONS_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "ml", "uncertain_predictions.csv"
)
REFINED_GRID_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "comparative", "refined_phonetic_grid.csv"
)
POSITIONAL_PROFILES_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "positional", "positional_profiles.csv"
)
SEGMENTED_TEXTS_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "segmentation", "segmented_texts_consensus.csv"
)
SIGN_CENTRALITY_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "network", "global", "sign_centrality.csv"
)
OUT_DIR = os.path.join(BASE_DIR, "data", "analysis", "verification")
OUT_CSV = os.path.join(OUT_DIR, "consistency_metrics.csv")

# ---------------------------------------------------------------------------
# Phonetic constants
# ---------------------------------------------------------------------------
VOWEL_LETTERS = frozenset("aeiouAEIOU")
# Valid CV structure types (standalone vowels are valid for V-class signs)
VALID_CV_PATTERNS = {"CV", "V", "CVV", "CCV", "CVC", "VC", "CCVC", "CVCC", "CCVCC"}
# Known exceptions — signs that may not follow strict CV but are valid
KNOWN_EXCEPTION_SIGNS = {
    "AB 62": "pte",   # complex CVC
    "AB 48": "nwa",   # complex CCV
    "AB 64": "swi",   # complex CCV
    "AB 85": "",      # likely word divider
    "AB 21f": "mi?",  # variant
    "AB 22f": "pi?",  # variant
    "AB 44b": None,   # variant
}


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _is_cv_anomaly(transliteration: str) -> bool:
    """Return True if the transliteration string does NOT look like a valid
    CV-type syllable.

    A syllabogram's value should be:
      - V  (a, e, i, o, u)
      - CV (da, ro, pa, te, ...)
      - CVC (pte, nwa, swi — rare but attested in Linear B)
      - CVV (pai, etc.)

    Unknown / missing values ('?', '') are anomalous.
    """
    if not transliteration or transliteration in ("?", "??", "zo?", "ra?"):
        return True

    # Clean up uncertainty markers
    clean = transliteration.rstrip("?")

    if not clean:
        return True

    # Classify by consonant/vowel pattern
    pattern = "".join("V" if ch in VOWEL_LETTERS else "C" for ch in clean)

    if pattern in VALID_CV_PATTERNS:
        return False

    # Allow "other" patterns that are short (2-3 chars) as valid-ish
    if len(clean) <= 3:
        return False

    return True


def load_ml_predictions(path: str) -> Dict[str, dict]:
    """Load ML predictions for UNCERTAIN signs.

    Returns: {bennett_id: {conventional_value, predicted_value, confidence}}
    """
    predictions: Dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"].strip()
            conv = (row.get("conventional_value") or "").strip()
            pred = (row.get("predicted_refined_value") or "").strip()
            conf_str = (row.get("confidence_score") or "0").strip()
            try:
                conf = float(conf_str)
            except ValueError:
                conf = 0.0
            predictions[bid] = {
                "conventional_value": conv,
                "predicted_value": pred,
                "confidence": conf,
            }
    logger.info("Loaded %d ML predictions from %s", len(predictions), path)
    return predictions


def load_refined_grid(path: str) -> Dict[str, dict]:
    """Load refined phonetic grid.

    Returns: {bennett_id: {decision, refined_value, phonetic_class, ...}}
    """
    grid: Dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"].strip()
            grid[bid] = {
                "decision": (row.get("decision") or "").strip(),
                "refined_value": (row.get("refined_value") or "").strip(),
                "conventional_value": (row.get("conventional_value") or "").strip(),
                "confidence_score": (row.get("confidence_score") or "0").strip(),
            }
    # Count UNCERTAIN signs
    uncertain = sum(1 for v in grid.values() if v["decision"] == "UNCERTAIN")
    logger.info("Loaded %d signs from refined grid (%d UNCERTAIN)", len(grid), uncertain)
    return grid


def load_corpus_sequences(db_path: str) -> list[list[dict]]:
    """Load syllabogram-only sequences from the database.

    Returns list of sequences; each sequence is a list of sign dicts with:
      bennett_id, transliteration, sign_type, sequence, character
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, gorila_id FROM inscriptions ORDER BY id")
    inscriptions = cursor.fetchall()

    sequences: list[list[dict]] = []
    for ins in inscriptions:
        cursor.execute(
            """SELECT sequence, bennett_id, sign_type, transliteration, character
               FROM signs WHERE inscription_id = ? ORDER BY sequence""",
            (ins["id"],),
        )
        signs = []
        for r in cursor.fetchall():
            sdict = dict(r)
            stype = sdict.get("sign_type", "syllabogram") or "syllabogram"
            bid = sdict.get("bennett_id") or ""
            # Keep syllabograms only
            if stype in ("syllabogram",) and bid:
                signs.append(sdict)
        if signs:  # at least one syllabogram
            sequences.append(signs)
    conn.close()
    logger.info("Loaded %d syllabogram sequences from database", len(sequences))
    return sequences


def build_cv_transliteration_map(ab_grid: dict, ml_predictions: dict,
                                 refined_grid: dict) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Build (before, after) transliteration maps for all signs.

    before: conventional value from AB grid or refined grid
    after:  ML-predicted value for UNCERTAIN signs, else conventional

    Returns (before_map, after_map) where each maps bennett_id -> transliteration.
    """
    # Start with the AB phonetic grid embedded in positional_analysis.py / ngram_analysis.py
    from pipeline.positional_analysis import AB_PHONETIC_GRID, _AB_GRID as _POS_GRID

    before_map: Dict[str, str] = {}
    after_map: Dict[str, str] = {}

    # First, use the refined grid for all signs
    for bid, info in refined_grid.items():
        conv = info.get("conventional_value") or info.get("refined_value") or ""
        refined = info.get("refined_value") or conv or ""
        # Clean
        conv = conv.strip().rstrip("?")
        refined = refined.strip().rstrip("?")
        if not conv:
            conv = ""
        if not refined:
            refined = ""

        before_map[bid] = conv if conv else ""
        after_map[bid] = refined if refined and info.get("decision") == "CONFIRM" else ""

    # Apply ML predictions for UNCERTAIN signs
    for bid, pred in ml_predictions.items():
        pred_val = pred["predicted_value"].strip()
        if pred_val and pred_val != "?" and pred.get("confidence", 0) > 0:
            after_map[bid] = pred_val

    # Fill gaps from AB grid
    from pipeline.positional_analysis import _AB_GRID as _POS_GRID2
    for bid in list(before_map.keys()) + list(after_map.keys()):
        if bid in _POS_GRID2:
            entry = _POS_GRID2[bid]
            trans = entry.get("transliteration", "").strip().rstrip("?")
            if not before_map.get(bid):
                before_map[bid] = trans
            if not after_map.get(bid):
                after_map[bid] = trans

    logger.info("Built transliteration maps: %d before, %d after entries",
                len(before_map), len(after_map))
    return before_map, after_map


# ---------------------------------------------------------------------------
# Metric 1: CV Pattern Consistency
# ---------------------------------------------------------------------------

def compute_cv_consistency(
    sequences: list[list[dict]],
    ml_predictions: Dict[str, dict],
    before_map: Dict[str, str],
    after_map: Dict[str, str],
) -> dict:
    """Count CV anomalies before vs after applying ML predictions.

    Returns dict with before/after anomaly counts and rates.
    """
    uncertain_bids = set(ml_predictions.keys())

    # Before: using conventional (before_map) values
    before_anomalies = 0
    before_total = 0

    # After: using ML-predicted (after_map) values for UNCERTAIN signs
    after_anomalies = 0
    after_total = 0

    # Track resolved / created anomalies specifically for UNCERTAIN signs
    resolved = 0
    created = 0
    uncertain_instances = 0

    for seq in sequences:
        for sign in seq:
            bid = sign.get("bennett_id", "")
            if not bid:
                continue

            # Skip known exceptions
            if bid in KNOWN_EXCEPTION_SIGNS:
                continue

            before_trans = before_map.get(bid, "")
            after_trans = after_map.get(bid, before_trans)

            before_is_anomaly = _is_cv_anomaly(before_trans)
            after_is_anomaly = _is_cv_anomaly(after_trans)

            before_total += 1
            after_total += 1

            if before_is_anomaly:
                before_anomalies += 1
            if after_is_anomaly:
                after_anomalies += 1

            # Track changes specifically for UNCERTAIN signs
            if bid in uncertain_bids:
                uncertain_instances += 1
                if before_is_anomaly and not after_is_anomaly:
                    resolved += 1
                elif not before_is_anomaly and after_is_anomaly:
                    created += 1

    before_rate = before_anomalies / before_total if before_total > 0 else 0.0
    after_rate = after_anomalies / after_total if after_total > 0 else 0.0

    result = {
        "before_anomalies": before_anomalies,
        "before_total": before_total,
        "before_anomaly_rate": before_rate,
        "after_anomalies": after_anomalies,
        "after_total": after_total,
        "after_anomaly_rate": after_rate,
        "resolved_for_uncertain": resolved,
        "created_for_uncertain": created,
        "uncertain_instances": uncertain_instances,
        "cv_adherence_rate_before": 1.0 - before_rate,
        "cv_adherence_rate_after": 1.0 - after_rate,
    }
    logger.info(
        "CV consistency: before=%.4f (%d/%d), after=%.4f (%d/%d), "
        "resolved=%d, created=%d (uncertain instances=%d)",
        1.0 - before_rate, before_anomalies, before_total,
        1.0 - after_rate, after_anomalies, after_total,
        resolved, created, uncertain_instances,
    )
    return result


# ---------------------------------------------------------------------------
# Metric 2: Word Boundary Consistency
# ---------------------------------------------------------------------------

def compute_word_boundary_consistency(
    sequences: list[list[dict]],
    ml_predictions: Dict[str, dict],
    before_map: Dict[str, str],
    after_map: Dict[str, str],
) -> dict:
    """Re-run simple bigram-based word segmentation and compare against
    ground-truth word dividers.

    This is a lightweight re-implementation of the bigram transition
    probability strategy from word_segmentation.py.
    """
    uncertain_bids = set(ml_predictions.keys())

    # --- Build bigram LM for "before" corpus ---
    def _build_lm(seqs, trans_map):
        unigrams: Counter = Counter()
        bigrams: Counter = Counter()
        for seq in seqs:
            keys = []
            for s in seq:
                bid = s.get("bennett_id", "")
                trans = trans_map.get(bid, "")
                keys.append(trans if trans else bid)
            for i in range(len(keys) - 1):
                unigrams[keys[i]] += 1
                bigrams[(keys[i], keys[i + 1])] += 1
            if keys:
                unigrams[keys[-1]] += 1
        return unigrams, bigrams

    unigrams_before, bigrams_before = _build_lm(sequences, before_map)
    unigrams_after, bigrams_after = _build_lm(sequences, after_map)

    # Compute all bigram probabilities to find a threshold
    def _compute_threshold(bigrams, unigrams, pct=25):
        all_probs = []
        for (a, b), cnt in bigrams.items():
            total = unigrams.get(a, 0)
            if total > 0:
                all_probs.append(cnt / total)
        all_probs.sort()
        idx = int(len(all_probs) * pct / 100)
        return all_probs[idx] if idx < len(all_probs) else 0.01

    threshold_before = _compute_threshold(bigrams_before, unigrams_before)
    threshold_after = _compute_threshold(bigrams_after, unigrams_after)

    total_unigrams_before = sum(unigrams_before.values())
    total_unigrams_after = sum(unigrams_after.values())

    marginal_before = {k: v / total_unigrams_before for k, v in unigrams_before.items()}
    marginal_after = {k: v / total_unigrams_after for k, v in unigrams_after.items()}

    # --- Predict boundaries for "before" and "after" ---
    def _predict_boundaries(seq, trans_map, unigrams, bigrams, threshold, marginal):
        keys = []
        for s in seq:
            bid = s.get("bennett_id", "")
            trans = trans_map.get(bid, "")
            keys.append(trans if trans else bid)

        boundaries = set()
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            total_a = unigrams.get(a, 0)
            if total_a == 0:
                continue
            prob = bigrams.get((a, b), 0) / total_a
            p_marg = marginal.get(b, 0.0)
            # Boundary candidate: probability is low AND below marginal
            if prob < threshold and prob < p_marg:
                boundaries.add(seq[i]["sequence"])
        return sorted(boundaries)

    # Load ground truth: we need the DB for dividers
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, gorila_id FROM inscriptions ORDER BY id")
    ins_dividers: Dict[int, set] = {}
    for row in c.fetchall():
        ins_dividers[row["id"]] = set()

    c.execute(
        "SELECT inscription_id, sequence, character FROM signs "
        "WHERE character = ? ORDER BY inscription_id, sequence",
        ("\U00010101",),  # AEGEAN WORD SEPARATOR DOT
    )
    for row in c.fetchall():
        iid = row["inscription_id"]
        if iid in ins_dividers:
            ins_dividers[iid].add(row["sequence"])
    conn.close()

    # Build a map from gorila_id to ground-truth boundaries
    # We need to match sequences back to inscriptions
    conn2 = sqlite3.connect(DB_PATH)
    conn2.row_factory = sqlite3.Row
    c2 = conn2.cursor()
    c2.execute("SELECT id, gorila_id FROM inscriptions ORDER BY id")
    gorila_to_id: Dict[str, int] = {}
    for row in c2.fetchall():
        gorila_to_id[row["gorila_id"]] = row["id"]
    conn2.close()

    # Evaluate
    before_agreements = 0
    after_agreements = 0
    total_boundary_positions = 0

    # We need to match each sequence back to an inscription
    # Simplest approach: iterate sequences alongside the first N inscriptions
    conn3 = sqlite3.connect(DB_PATH)
    conn3.row_factory = sqlite3.Row
    c3 = conn3.cursor()
    c3.execute("SELECT id, gorila_id FROM inscriptions ORDER BY id")
    ins_rows = c3.fetchall()
    conn3.close()

    # Build a map: gorila_id -> {sign_sequences: [...]}
    # Instead, let's directly query the DB per inscription
    conn4 = sqlite3.connect(DB_PATH)
    conn4.row_factory = sqlite3.Row
    c4 = conn4.cursor()

    # Get all inscriptions with their syllabograms in order
    c4.execute("SELECT DISTINCT inscription_id FROM signs WHERE sign_type='syllabogram' AND bennett_id != '' ORDER BY inscription_id")
    ins_with_syll = [r["inscription_id"] for r in c4.fetchall()]

    borderable_inscriptions = 0

    for ins_idx, seq in enumerate(sequences):
        if ins_idx >= len(ins_with_syll):
            break
        ins_id = ins_with_syll[ins_idx]
        gt_dividers = ins_dividers.get(ins_id, set())
        if not gt_dividers:
            continue  # no ground truth to compare against

        borderable_inscriptions += 1

        # Predict before
        pred_before = set(_predict_boundaries(
            seq, before_map, unigrams_before, bigrams_before,
            threshold_before, marginal_before,
        ))
        # Predict after
        pred_after = set(_predict_boundaries(
            seq, after_map, unigrams_after, bigrams_after,
            threshold_after, marginal_after,
        ))

        # Count agreement at each position
        all_positions = set(s["sequence"] for s in seq)
        for pos in all_positions:
            gt_boundary = pos in gt_dividers
            before_boundary = pos in pred_before
            after_boundary = pos in pred_after

            total_boundary_positions += 1
            if before_boundary == gt_boundary:
                before_agreements += 1
            if after_boundary == gt_boundary:
                after_agreements += 1

    before_agreement_rate = before_agreements / total_boundary_positions if total_boundary_positions > 0 else 0.0
    after_agreement_rate = after_agreements / total_boundary_positions if total_boundary_positions > 0 else 0.0

    result = {
        "before_agreements": before_agreements,
        "after_agreements": after_agreements,
        "total_positions": total_boundary_positions,
        "before_agreement_rate": before_agreement_rate,
        "after_agreement_rate": after_agreement_rate,
        "borderable_inscriptions": borderable_inscriptions,
    }
    logger.info(
        "Word boundary agreement: before=%.4f (%d/%d), after=%.4f (%d/%d)",
        before_agreement_rate, before_agreements, total_boundary_positions,
        after_agreement_rate, after_agreements, total_boundary_positions,
    )
    return result


# ---------------------------------------------------------------------------
# Metric 3: N-gram Entropy
# ---------------------------------------------------------------------------

def _compute_bigram_entropy(sequences: list[list[dict]], trans_map: Dict[str, str]) -> float:
    """Compute bigram-level Shannon entropy."""
    bigram_counts: Counter = Counter()
    context_counts: Counter = Counter()

    for seq in sequences:
        keys = []
        for s in seq:
            bid = s.get("bennett_id", "")
            trans = trans_map.get(bid, "")
            keys.append(trans if trans else bid)

        for i in range(len(keys) - 1):
            ctx = keys[i]
            nxt = keys[i + 1]
            bigram_counts[(ctx, nxt)] += 1
            context_counts[ctx] += 1

    total_bigrams = sum(bigram_counts.values())
    if total_bigrams == 0:
        return 0.0

    # H(bigram) = -sum P(a,b) * log2 P(a,b)
    entropy_val = 0.0
    for (a, b), cnt in bigram_counts.items():
        p = cnt / total_bigrams
        entropy_val -= p * math.log2(p)

    return entropy_val


def _compute_trigram_entropy(sequences: list[list[dict]], trans_map: Dict[str, str]) -> float:
    """Compute trigram-level Shannon entropy."""
    trigram_counts: Counter = Counter()

    for seq in sequences:
        keys = []
        for s in seq:
            bid = s.get("bennett_id", "")
            trans = trans_map.get(bid, "")
            keys.append(trans if trans else bid)

        for i in range(len(keys) - 2):
            gram = (keys[i], keys[i + 1], keys[i + 2])
            trigram_counts[gram] += 1

    total = sum(trigram_counts.values())
    if total == 0:
        return 0.0

    entropy_val = 0.0
    for gram, cnt in trigram_counts.items():
        p = cnt / total
        entropy_val -= p * math.log2(p)

    return entropy_val


def compute_ngram_entropy_change(
    sequences: list[list[dict]],
    ml_predictions: Dict[str, dict],
    before_map: Dict[str, str],
    after_map: Dict[str, str],
) -> dict:
    """Compute bigram and trigram entropy before vs after ML predictions."""
    bigram_ent_before = _compute_bigram_entropy(sequences, before_map)
    bigram_ent_after = _compute_bigram_entropy(sequences, after_map)

    trigram_ent_before = _compute_trigram_entropy(sequences, before_map)
    trigram_ent_after = _compute_trigram_entropy(sequences, after_map)

    result = {
        "bigram_entropy_before": bigram_ent_before,
        "bigram_entropy_after": bigram_ent_after,
        "trigram_entropy_before": trigram_ent_before,
        "trigram_entropy_after": trigram_ent_after,
    }
    logger.info(
        "Bigram entropy: before=%.4f, after=%.4f (delta=%.4f)",
        bigram_ent_before, bigram_ent_after,
        bigram_ent_after - bigram_ent_before,
    )
    logger.info(
        "Trigram entropy: before=%.4f, after=%.4f (delta=%.4f)",
        trigram_ent_before, trigram_ent_after,
        trigram_ent_after - trigram_ent_before,
    )
    return result


# ---------------------------------------------------------------------------
# Metric 4: Sign Co-occurrence Phonetic Similarity
# ---------------------------------------------------------------------------

def compute_cooccurrence_phonetic_nearness(
    centrality_path: str,
    before_map: Dict[str, str],
    after_map: Dict[str, str],
    ml_predictions: Dict[str, dict],
    sequences: list[list[dict]],
) -> dict:
    """Check whether ML-predicted values put phonetically similar signs
    closer in the co-occurrence network.

    Approach:
    1. Load sign centrality data (co-occurrence graph metrics).
    2. Build co-occurrence adjacency from the sequences directly.
    3. For each pair of co-occurring signs, compute phonetic similarity:
       - Jaccard similarity of consonant/vowel sets
       - Edit distance of transliteration strings
    4. Weight co-occurrence edges by phonetic similarity.
    5. Compare weighted sum before vs after ML predictions.
    """
    # Build co-occurrence adjacency
    cooc: Dict[str, Counter] = defaultdict(Counter)
    for seq in sequences:
        sign_bids = set(s.get("bennett_id", "") for s in seq if s.get("bennett_id"))
        for a in sign_bids:
            for b in sign_bids:
                if a < b:
                    cooc[a][b] += 1
                    cooc[b][a] += 1

    uncertain_bids = set(ml_predictions.keys())

    def _phonetic_similarity(trans_a: str, trans_b: str) -> float:
        """Compute a phonetic similarity score between two transliteration strings."""
        if not trans_a or not trans_b:
            return 0.0

        # Jaccard similarity of consonant/vowel sets
        def _char_set(s):
            return {("V" if ch in VOWEL_LETTERS else "C") + ch.lower() for ch in s if ch.isalpha()}

        set_a = _char_set(trans_a)
        set_b = _char_set(trans_b)
        if not set_a or not set_b:
            return 0.0

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        jaccard = intersection / union if union > 0 else 0.0

        # Simple edit distance normalization (0=identical, 1=different)
        def _edit_dist(a, b):
            if not a or not b:
                return 1.0
            import difflib
            return 1.0 - difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

        edit_sim = 1.0 - _edit_dist(trans_a, trans_b)

        return 0.5 * jaccard + 0.5 * edit_sim

    # Compute weighted phonetic nearness before and after
    before_weighted_sum = 0.0
    after_weighted_sum = 0.0
    pair_count = 0

    for a in list(cooc.keys()):
        for b in cooc[a]:
            if a >= b:
                continue
            weight = cooc[a][b]

            before_trans_a = before_map.get(a, "")
            before_trans_b = before_map.get(b, "")
            after_trans_a = after_map.get(a, before_trans_a)
            after_trans_b = after_map.get(b, before_trans_b)

            before_sim = _phonetic_similarity(before_trans_a, before_trans_b)
            after_sim = _phonetic_similarity(after_trans_a, after_trans_b)

            before_weighted_sum += before_sim * weight
            after_weighted_sum += after_sim * weight
            pair_count += 1

    before_avg = before_weighted_sum / pair_count if pair_count > 0 else 0.0
    after_avg = after_weighted_sum / pair_count if pair_count > 0 else 0.0

    # Also compute specifically for pairs involving at least one UNCERTAIN sign
    uncertain_before_sum = 0.0
    uncertain_after_sum = 0.0
    uncertain_pair_count = 0

    for a in list(cooc.keys()):
        for b in cooc[a]:
            if a >= b:
                continue
            if a not in uncertain_bids and b not in uncertain_bids:
                continue
            weight = cooc[a][b]
            before_trans_a = before_map.get(a, "")
            before_trans_b = before_map.get(b, "")
            after_trans_a = after_map.get(a, before_trans_a)
            after_trans_b = after_map.get(b, before_trans_b)

            before_sim = _phonetic_similarity(before_trans_a, before_trans_b)
            after_sim = _phonetic_similarity(after_trans_a, after_trans_b)

            uncertain_before_sum += before_sim * weight
            uncertain_after_sum += after_sim * weight
            uncertain_pair_count += 1

    uncertain_before_avg = uncertain_before_sum / uncertain_pair_count if uncertain_pair_count > 0 else 0.0
    uncertain_after_avg = uncertain_after_sum / uncertain_pair_count if uncertain_pair_count > 0 else 0.0

    result = {
        "before_phonetic_nearness": before_avg,
        "after_phonetic_nearness": after_avg,
        "total_pairs": pair_count,
        "uncertain_before_nearness": uncertain_before_avg,
        "uncertain_after_nearness": uncertain_after_avg,
        "uncertain_pairs": uncertain_pair_count,
    }
    logger.info(
        "Co-occurrence phonetic nearness: before=%.6f, after=%.6f (all pairs=%d)",
        before_avg, after_avg, pair_count,
    )
    logger.info(
        "  Uncertain-only: before=%.6f, after=%.6f (pairs=%d)",
        uncertain_before_avg, uncertain_after_avg, uncertain_pair_count,
    )
    return result


# ---------------------------------------------------------------------------
# Metric 5: Positional Entropy Change
# ---------------------------------------------------------------------------

def compute_positional_entropy_change(
    sequences: list[list[dict]],
    before_map: Dict[str, str],
    after_map: Dict[str, str],
    ml_predictions: Dict[str, dict],
) -> dict:
    """Compute how positional entropy of signs changes before vs after ML.

    Higher positional entropy = sign is more evenly distributed across
    positions (more "normal" linguistic behavior for a syllabogram).
    """
    uncertain_bids = set(ml_predictions.keys())

    def _positional_entropy(seqs, trans_map, bids_filter=None):
        """Compute average positional entropy per sign."""
        pos_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"initial": 0, "medial": 0, "final": 0}
        )

        for seq in seqs:
            keys = []
            for s in seq:
                bid = s.get("bennett_id", "")
                if bids_filter and bid not in bids_filter:
                    continue
                trans = trans_map.get(bid, "")
                keys.append((bid, trans if trans else bid))

            L = len(keys)
            for idx, (bid, tok) in enumerate(keys):
                if L == 1:
                    pos_counts[tok]["initial"] += 1
                    pos_counts[tok]["final"] += 1
                elif L == 2:
                    if idx == 0:
                        pos_counts[tok]["initial"] += 1
                    else:
                        pos_counts[tok]["final"] += 1
                else:
                    if idx == 0:
                        pos_counts[tok]["initial"] += 1
                    elif idx == L - 1:
                        pos_counts[tok]["final"] += 1
                    else:
                        pos_counts[tok]["medial"] += 1

        entropies = []
        for tok, cnts in pos_counts.items():
            total = cnts["initial"] + cnts["medial"] + cnts["final"]
            if total < 3:
                continue
            probs = [cnts[p] / total for p in ("initial", "medial", "final")]
            ent = -sum(p * math.log2(p) for p in probs if p > 0)
            entropies.append(ent)

        if not entropies:
            return 0.0
        return sum(entropies) / len(entropies)

    before_ent = _positional_entropy(sequences, before_map)
    after_ent = _positional_entropy(sequences, after_map)

    # Specifically for UNCERTAIN signs
    before_ent_uncertain = _positional_entropy(sequences, before_map, uncertain_bids)
    after_ent_uncertain = _positional_entropy(sequences, after_map, uncertain_bids)

    result = {
        "before_positional_entropy": before_ent,
        "after_positional_entropy": after_ent,
        "before_uncertain_pos_entropy": before_ent_uncertain,
        "after_uncertain_pos_entropy": after_ent_uncertain,
    }
    logger.info(
        "Positional entropy: before=%.4f, after=%.4f",
        before_ent, after_ent,
    )
    return result


# ---------------------------------------------------------------------------
# Output: consistency_metrics.csv
# ---------------------------------------------------------------------------

def write_consistency_metrics(
    cv_result: dict,
    boundary_result: dict,
    ngram_result: dict,
    cooc_result: dict,
    pos_ent_result: dict,
    output_path: str,
):
    """Write out consistency_metrics.csv with before/after comparisons."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    metrics = [
        # CV Adherence Rate
        {
            "metric_name": "cv_adherence_rate",
            "before_ml": f"{cv_result['cv_adherence_rate_before']:.6f}",
            "after_ml": f"{cv_result['cv_adherence_rate_after']:.6f}",
            "delta": f"{cv_result['cv_adherence_rate_after'] - cv_result['cv_adherence_rate_before']:.6f}",
            "improved": 1 if cv_result['cv_adherence_rate_after'] > cv_result['cv_adherence_rate_before'] else 0,
            "notes": (
                f"Resolved={cv_result['resolved_for_uncertain']}, "
                f"Created={cv_result['created_for_uncertain']}, "
                f"UNCERTAIN instances={cv_result['uncertain_instances']}"
            ),
        },
        # CV Anomalies Resolved
        {
            "metric_name": "cv_anomalies_resolved",
            "before_ml": str(cv_result["before_anomalies"]),
            "after_ml": str(cv_result["after_anomalies"]),
            "delta": str(cv_result["resolved_for_uncertain"] - cv_result["created_for_uncertain"]),
            "improved": 1 if cv_result["resolved_for_uncertain"] > cv_result["created_for_uncertain"] else 0,
            "notes": (
                f"Before={cv_result['before_anomalies']}, After={cv_result['after_anomalies']}, "
                f"Net={cv_result['resolved_for_uncertain'] - cv_result['created_for_uncertain']}"
            ),
        },
        # Word Boundary Agreement
        {
            "metric_name": "word_boundary_agreement",
            "before_ml": f"{boundary_result['before_agreement_rate']:.6f}",
            "after_ml": f"{boundary_result['after_agreement_rate']:.6f}",
            "delta": f"{boundary_result['after_agreement_rate'] - boundary_result['before_agreement_rate']:.6f}",
            "improved": 1 if boundary_result["after_agreement_rate"] > boundary_result["before_agreement_rate"] else 0,
            "notes": (
                f"Before={boundary_result['before_agreements']}/"
                f"{boundary_result['total_positions']}, "
                f"After={boundary_result['after_agreements']}/"
                f"{boundary_result['total_positions']}"
            ),
        },
        # Bigram Entropy
        {
            "metric_name": "bigram_entropy",
            "before_ml": f"{ngram_result['bigram_entropy_before']:.6f}",
            "after_ml": f"{ngram_result['bigram_entropy_after']:.6f}",
            "delta": f"{ngram_result['bigram_entropy_after'] - ngram_result['bigram_entropy_before']:.6f}",
            # Entropy decrease = more structure = improved
            "improved": 1 if ngram_result["bigram_entropy_after"] < ngram_result["bigram_entropy_before"] else 0,
            "notes": "Lower entropy = more structured language",
        },
        # Trigram Entropy
        {
            "metric_name": "trigram_entropy",
            "before_ml": f"{ngram_result['trigram_entropy_before']:.6f}",
            "after_ml": f"{ngram_result['trigram_entropy_after']:.6f}",
            "delta": f"{ngram_result['trigram_entropy_after'] - ngram_result['trigram_entropy_before']:.6f}",
            "improved": 1 if ngram_result["trigram_entropy_after"] < ngram_result["trigram_entropy_before"] else 0,
            "notes": "Lower entropy = more structured language",
        },
        # Phonetic Nearness (all pairs)
        {
            "metric_name": "cooccurrence_phonetic_nearness",
            "before_ml": f"{cooc_result['before_phonetic_nearness']:.6f}",
            "after_ml": f"{cooc_result['after_phonetic_nearness']:.6f}",
            "delta": f"{cooc_result['after_phonetic_nearness'] - cooc_result['before_phonetic_nearness']:.6f}",
            "improved": 1 if cooc_result["after_phonetic_nearness"] > cooc_result["before_phonetic_nearness"] else 0,
            "notes": f"All pairs={cooc_result['total_pairs']}",
        },
        # Phonetic Nearness (UNCERTAIN-involving pairs)
        {
            "metric_name": "cooccurrence_uncertain_nearness",
            "before_ml": f"{cooc_result['uncertain_before_nearness']:.6f}",
            "after_ml": f"{cooc_result['uncertain_after_nearness']:.6f}",
            "delta": f"{cooc_result['uncertain_after_nearness'] - cooc_result['uncertain_before_nearness']:.6f}",
            "improved": 1 if cooc_result["uncertain_after_nearness"] > cooc_result["uncertain_before_nearness"] else 0,
            "notes": f"UNCERTAIN-involving pairs={cooc_result['uncertain_pairs']}",
        },
        # Positional Entropy
        {
            "metric_name": "positional_entropy",
            "before_ml": f"{pos_ent_result['before_positional_entropy']:.6f}",
            "after_ml": f"{pos_ent_result['after_positional_entropy']:.6f}",
            "delta": f"{pos_ent_result['after_positional_entropy'] - pos_ent_result['before_positional_entropy']:.6f}",
            "improved": 1 if pos_ent_result["after_positional_entropy"] > pos_ent_result["before_positional_entropy"] else 0,
            "notes": "Higher entropy = more even positional distribution (more natural for syllabograms)",
        },
    ]

    fieldnames = ["metric_name", "before_ml", "after_ml", "delta", "improved", "notes"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics:
            writer.writerow(m)

    n_improved = sum(1 for m in metrics if int(m["improved"]) == 1)
    n_total = len(metrics)
    logger.info("Wrote %d metrics to %s (%d/%d improved)", n_total, output_path, n_improved, n_total)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(verbose: bool = False):
    """Execute the full internal consistency analysis pipeline."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Internal Consistency Analysis of ML Predictions")
    logger.info("=" * 60)

    # 0. Load data
    logger.info("[0] Loading input data...")
    ml_predictions = load_ml_predictions(UNCERTAIN_PREDICTIONS_PATH)
    refined_grid = load_refined_grid(REFINED_GRID_PATH)
    sequences = load_corpus_sequences(DB_PATH)
    before_map, after_map = build_cv_transliteration_map(
        refined_grid, ml_predictions, refined_grid
    )

    # 1. CV Pattern Consistency
    logger.info("[1] Computing CV pattern consistency...")
    cv_result = compute_cv_consistency(sequences, ml_predictions, before_map, after_map)

    # 2. Word Boundary Consistency
    logger.info("[2] Computing word boundary consistency...")
    boundary_result = compute_word_boundary_consistency(
        sequences, ml_predictions, before_map, after_map,
    )

    # 3. N-gram Entropy
    logger.info("[3] Computing n-gram entropy change...")
    ngram_result = compute_ngram_entropy_change(
        sequences, ml_predictions, before_map, after_map,
    )

    # 4. Sign Co-occurrence
    logger.info("[4] Computing co-occurrence phonetic nearness...")
    cooc_result = compute_cooccurrence_phonetic_nearness(
        SIGN_CENTRALITY_PATH, before_map, after_map, ml_predictions, sequences,
    )

    # 5. Positional Entropy
    logger.info("[5] Computing positional entropy change...")
    pos_ent_result = compute_positional_entropy_change(
        sequences, before_map, after_map, ml_predictions,
    )

    # 6. Write output
    logger.info("[6] Writing consistency metrics...")
    write_consistency_metrics(
        cv_result, boundary_result, ngram_result, cooc_result, pos_ent_result,
        OUT_CSV,
    )

    # 7. Print summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(
        "CV Adherence:         %.4f → %.4f  (delta=%+.4f)",
        cv_result["cv_adherence_rate_before"],
        cv_result["cv_adherence_rate_after"],
        cv_result["cv_adherence_rate_after"] - cv_result["cv_adherence_rate_before"],
    )
    logger.info(
        "Word Boundary Agree:  %.4f → %.4f  (delta=%+.4f)",
        boundary_result["before_agreement_rate"],
        boundary_result["after_agreement_rate"],
        boundary_result["after_agreement_rate"] - boundary_result["before_agreement_rate"],
    )
    logger.info(
        "Bigram Entropy:       %.4f → %.4f  (delta=%+.4f) %s",
        ngram_result["bigram_entropy_before"],
        ngram_result["bigram_entropy_after"],
        ngram_result["bigram_entropy_after"] - ngram_result["bigram_entropy_before"],
        "(↓ better)" if ngram_result["bigram_entropy_after"] < ngram_result["bigram_entropy_before"] else "(↑ worse)",
    )
    logger.info(
        "Trigram Entropy:      %.4f → %.4f  (delta=%+.4f) %s",
        ngram_result["trigram_entropy_before"],
        ngram_result["trigram_entropy_after"],
        ngram_result["trigram_entropy_after"] - ngram_result["trigram_entropy_before"],
        "(↓ better)" if ngram_result["trigram_entropy_after"] < ngram_result["trigram_entropy_before"] else "(↑ worse)",
    )
    logger.info(
        "Co-oc Phonetic Near:  %.6f → %.6f  (delta=%+.6f) %s",
        cooc_result["before_phonetic_nearness"],
        cooc_result["after_phonetic_nearness"],
        cooc_result["after_phonetic_nearness"] - cooc_result["before_phonetic_nearness"],
        "(↑ better)" if cooc_result["after_phonetic_nearness"] > cooc_result["before_phonetic_nearness"] else "(↓ worse)",
    )
    logger.info(
        "Positional Entropy:   %.4f → %.4f  (delta=%+.4f) %s",
        pos_ent_result["before_positional_entropy"],
        pos_ent_result["after_positional_entropy"],
        pos_ent_result["after_positional_entropy"] - pos_ent_result["before_positional_entropy"],
        "(↑ better)" if pos_ent_result["after_positional_entropy"] > pos_ent_result["before_positional_entropy"] else "(↓ worse)",
    )
    logger.info("Output written to %s", OUT_CSV)

    return {
        "cv": cv_result,
        "boundary": boundary_result,
        "ngram": ngram_result,
        "cooc": cooc_result,
        "pos_ent": pos_ent_result,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Internal Consistency Analysis of ML Predictions",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()
    run(verbose=args.verbose)


if __name__ == "__main__":
    main()
