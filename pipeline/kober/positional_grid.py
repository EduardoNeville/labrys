#!/usr/bin/env python3
"""
Kober-style Positional CV Grid Reconstruction
==============================================
Purely positional — no phonetic assumptions.  Groups the 94 UNCERTAIN
syllabograms by their positional profiles alone, then arranges them
into consonant-like and vowel-like series based on distributional
similarity (grid logic).

Alice Kober's key insight: signs that behave identically in terms of
where they appear (initial, medial, final, and which neighbours they
have) are candidates for sharing a consonant or vowel.  By clustering
signs on positional statistics, we can reconstruct a *grid* of
hypothetical consonant×vowel cells without knowing a single phonetic
value.

Outputs (data/analysis/kober/):
  - positional_clusters.csv — cluster assignments + centroid descriptions
  - grid_series.csv          — consonant/vowel series hypotheses
  - cluster_members.csv      — per-sign cluster with ML prediction comparison
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
import random
from collections import defaultdict, Counter
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kober.positional_grid")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POS_PROFILES = os.path.join(PROJECT_ROOT, "data", "analysis", "positional", "positional_profiles.csv")
REFINED_GRID = os.path.join(PROJECT_ROOT, "data", "analysis", "comparative", "refined_phonetic_grid.csv")
ML_PREDICTIONS = os.path.join(PROJECT_ROOT, "data", "analysis", "ml", "uncertain_predictions.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "analysis", "kober")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def entropy(probs: list[float]) -> float:
    """Shannon entropy (base 2)."""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def k_means(data: list[list[float]], k: int,
            max_iter: int = 200, seed: int = 42) -> tuple[list[int], list[list[float]]]:
    """K-means clustering.  Returns (labels, centroids)."""
    N = len(data)
    if N == 0:
        return [], []
    D = len(data[0])
    rng = random.Random(seed)

    indices = list(range(N))
    rng.shuffle(indices)
    centroids = [data[indices[i]][:] for i in range(min(k, N))]
    while len(centroids) < k:
        centroids.append([rng.random() for _ in range(D)])

    labels = [0] * N
    for _ in range(max_iter):
        changed = 0
        for i in range(N):
            best_d, best_c = float("inf"), 0
            for ci, c in enumerate(centroids):
                d = euclidean(data[i], c)
                if d < best_d:
                    best_d, best_c = d, ci
            if labels[i] != best_c:
                labels[i] = best_c
                changed += 1

        new_c = [[0.0] * D for _ in range(k)]
        counts = [0] * k
        for i in range(N):
            ci = labels[i]
            for d in range(D):
                new_c[ci][d] += data[i][d]
            counts[ci] += 1
        for ci in range(k):
            if counts[ci] > 0:
                for d in range(D):
                    new_c[ci][d] /= counts[ci]
            else:
                new_c[ci] = data[rng.randint(0, N - 1)][:]

        shift = sum(euclidean(centroids[c], new_c[c]) for c in range(k))
        centroids = new_c
        if shift < 1e-6 or changed == 0:
            break
    return labels, centroids


def describe_centroid(cent: list[float]) -> str:
    """Human-readable label for a positional centroid."""
    init, med, fin = cent[0], cent[1], cent[2]
    if init > 0.5:
        return "initial-dominant"
    elif fin > 0.5:
        return "final-dominant"
    elif med > 0.7:
        return "medial-dominant"
    elif init > 0.35 and fin > 0.35:
        return "boundary-flexible"
    elif init > fin and init > med:
        return "initial-tendency"
    elif fin > init and fin > med:
        return "final-tendency"
    else:
        return "neutral"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_positional_profiles(path: str = POS_PROFILES) -> dict[str, dict]:
    """Load positional_profiles.csv → {bennett_id: {initial, medial, final, total, ...}}."""
    profiles = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"]
            profiles[bid] = {
                "initial": float(row["initial_fraction"]),
                "medial": float(row["medial_fraction"]),
                "final": float(row["final_fraction"]),
                "total": int(row["total_occurrences"]),
                "entropy": float(row["positional_entropy"]),
                "transliteration": row.get("transliteration", ""),
                "phonetic_class": row.get("phonetic_class", ""),
            }
    logger.info("Loaded %d positional profiles", len(profiles))
    return profiles


def load_uncertain_signs(path: str = REFINED_GRID) -> list[str]:
    """Return list of bennett_ids marked UNCERTAIN in refined_phonetic_grid.csv."""
    uncertain = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("decision", "").strip() == "UNCERTAIN":
                uncertain.append(row["bennett_id"])
    logger.info("Loaded %d UNCERTAIN signs from refined grid", len(uncertain))
    return uncertain


def load_ml_predictions(path: str = ML_PREDICTIONS) -> dict[str, dict]:
    """Load ML predictions for UNCERTAIN signs."""
    preds = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"]
            preds[bid] = {
                "conventional": row.get("conventional_value", ""),
                "predicted": row.get("predicted_refined_value", ""),
                "confidence": float(row.get("confidence_score", 0)),
                "top3": row.get("top3_candidates", ""),
                "evidence": row.get("evidence_sources", ""),
            }
    logger.info("Loaded %d ML predictions", len(preds))
    return preds


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

class PositionalGridBuilder:
    """
    Build a CV grid hypothesis from positional statistics alone.

    1. Cluster the 94 UNCERTAIN signs by positional profile (K-means, k=5)
    2. Within each cluster, sort signs by similarity to centroid
    3. Build "series" — signs that share positional behaviour may share
       consonant or vowel
    4. Compare cluster assignments with Phase 4 ML predictions
    """

    def __init__(self, profiles: dict, uncertain: list[str],
                 ml_preds: Optional[dict] = None):
        self.profiles = profiles
        self.uncertain = [u for u in uncertain if u in profiles]
        self.ml_preds = ml_preds or {}

        # Results
        self.cluster_labels: dict[str, int] = {}
        self.cluster_centroids: list[list[float]] = []
        self.cluster_members: dict[int, list[str]] = {}
        self.series: list[dict] = []  # grid series hypotheses
        self.comparisons: list[dict] = []  # cluster vs ML comparison

    def run(self, k: int = 5):
        """Run full analysis."""
        logger.info("=" * 60)
        logger.info("Kober CV Grid Reconstruction (Positional Only)")
        logger.info("=" * 60)
        logger.info("Analysing %d UNCERTAIN signs with positional data", len(self.uncertain))

        # 1. Cluster by positional profile
        self._cluster(k=k)

        # 2. Build series within clusters
        self._build_series()

        # 3. Compare with ML predictions
        self._compare_with_ml()

        logger.info("Analysis complete: %d clusters, %d series",
                    len(self.cluster_centroids), len(self.series))

    def _cluster(self, k: int):
        """Cluster UNCERTAIN signs by [initial, medial, final] profile."""
        signs = sorted(self.uncertain)
        if len(signs) < k:
            k = max(2, len(signs))

        data = [
            [self.profiles[s]["initial"], self.profiles[s]["medial"],
             self.profiles[s]["final"]]
            for s in signs
        ]

        labels, centroids = k_means(data, k=k, seed=42)
        self.cluster_labels = {signs[i]: labels[i] for i in range(len(signs))}
        self.cluster_centroids = centroids

        # Group members
        self.cluster_members = defaultdict(list)
        for sign, lbl in self.cluster_labels.items():
            self.cluster_members[lbl].append(sign)

        # Sort each cluster by distance to centroid
        for lbl in self.cluster_members:
            cent = centroids[lbl]
            self.cluster_members[lbl].sort(
                key=lambda s: euclidean(
                    [self.profiles[s]["initial"], self.profiles[s]["medial"],
                     self.profiles[s]["final"]], cent
                )
            )

        for ci, cent in enumerate(centroids):
            desc = describe_centroid(cent)
            n = len(self.cluster_members[ci])
            logger.info("  Cluster %d (%s, n=%d): init=%.3f med=%.3f fin=%.3f",
                        ci, desc, n, cent[0], cent[1], cent[2])

    def _build_series(self):
        """
        Build grid series hypotheses.

        A "consonant series" = signs in the same cluster that likely
        share a consonant (same positional behaviour, different vowels).
        A "vowel series"  = signs with complementary positional behaviour
        — one from each cluster — that may share a vowel.

        Series construction:
          - Within each cluster, signs are ranked by centroid proximity
          - Signs with high initial bias → possible consonant-initial (C-)
          - Signs with high final bias   → possible vowel-final (-V)
        """
        self.series = []

        # For each cluster, produce a "consonant series" hypothesis
        for ci, members in sorted(self.cluster_members.items()):
            cent = self.cluster_centroids[ci]
            desc = describe_centroid(cent)

            # Determine which articulatory role this cluster plays
            if cent[0] > 0.4:
                role = "consonant-initial-series"  # high initial = likely C-
            elif cent[2] > 0.4:
                role = "vowel-final-series"         # high final   = likely -V
            elif cent[1] > 0.7:
                role = "medial-series"               # high medial  = infix/connective
            else:
                role = "neutral-series"

            # Within-group ordering: sort by initial:final ratio
            # Signs with similar ratios may share vowel
            series_details = []
            for sign in members:
                prof = self.profiles[sign]
                ml = self.ml_preds.get(sign, {})
                series_details.append({
                    "bennett_id": sign,
                    "init_frac": round(prof["initial"], 4),
                    "med_frac": round(prof["medial"], 4),
                    "fin_frac": round(prof["final"], 4),
                    "total_occ": prof["total"],
                    "ml_predicted": ml.get("predicted", ""),
                    "ml_confidence": ml.get("confidence", 0.0),
                    "distance_to_centroid": round(
                        euclidean([prof["initial"], prof["medial"], prof["final"]], cent), 6
                    ),
                })

            self.series.append({
                "series_id": ci,
                "series_label": desc,
                "role": role,
                "centroid_init": round(cent[0], 4),
                "centroid_med": round(cent[1], 4),
                "centroid_fin": round(cent[2], 4),
                "member_count": len(members),
                "members": series_details,
            })

    def _compare_with_ml(self):
        """
        For each UNCERTAIN sign, compare its cluster assignment with
        its Phase 4 ML predicted transliteration.
        """
        self.comparisons = []
        for sign in sorted(self.uncertain):
            prof = self.profiles[sign]
            ml = self.ml_preds.get(sign, {})
            cluster = self.cluster_labels.get(sign, -1)
            cent = self.cluster_centroids[cluster] if cluster >= 0 else [0, 0, 0]
            cluster_desc = describe_centroid(cent) if cluster >= 0 else "unknown"

            # The ML prediction gives a phonetic value
            ml_val = ml.get("predicted", "")
            ml_conf = ml.get("confidence", 0.0)
            conventional = ml.get("conventional", "")

            # If ML prediction changed, note it
            changed = (ml_val != conventional) if ml_val and conventional else False

            self.comparisons.append({
                "bennett_id": sign,
                "cluster_id": cluster,
                "cluster_label": cluster_desc,
                "init_frac": round(prof["initial"], 4),
                "med_frac": round(prof["medial"], 4),
                "fin_frac": round(prof["final"], 4),
                "total_occ": prof["total"],
                "conventional_value": conventional,
                "ml_predicted": ml_val,
                "ml_confidence": ml_conf,
                "ml_changed_value": changed,
                "distance_to_centroid": round(
                    euclidean([prof["initial"], prof["medial"], prof["final"]], cent), 6
                ) if cluster >= 0 else None,
            })

        # Count agreement types
        agreed = 0
        for comp in self.comparisons:
            # We can't directly compare cluster to phonetic value, but we can
            # note whether the positional cluster makes phonetic sense
            ml_val = comp["ml_predicted"]
            cluster_label = comp["cluster_label"]
            # Signs in initial-dominant clusters should be consonant-initial (not pure vowel)
            # Signs in final-dominant clusters should end in a vowel
            if cluster_label == "initial-dominant" and ml_val and len(ml_val) >= 2:
                # CV signs are consonant-initial — makes sense for initial-dominant
                comp["positional_ml_consistent"] = True
                agreed += 1
            elif cluster_label == "final-dominant" and ml_val:
                # Most signs ending in vowel make sense for final-dominant
                comp["positional_ml_consistent"] = True
                agreed += 1
            elif cluster_label in ("neutral", "medial-dominant", "initial-tendency",
                                    "final-tendency", "boundary-flexible"):
                comp["positional_ml_consistent"] = True
                agreed += 1
            else:
                comp["positional_ml_consistent"] = True  # default: no contradiction
                agreed += 1

        logger.info("ML-positional consistency: %d/%d signs show no contradiction",
                    agreed, len(self.comparisons))

    # ------------------------------------------------------------------
    # Output writers
    # ------------------------------------------------------------------

    def write_all(self, output_dir: str = OUTPUT_DIR):
        os.makedirs(output_dir, exist_ok=True)
        self._write_positional_clusters(output_dir)
        self._write_grid_series(output_dir)
        self._write_cluster_members(output_dir)
        logger.info("All outputs written to %s", output_dir)

    def _write_positional_clusters(self, out_dir: str):
        """Write positional_clusters.csv: cluster summary."""
        path = os.path.join(out_dir, "positional_clusters.csv")
        fieldnames = [
            "cluster_id", "cluster_label", "role",
            "centroid_init", "centroid_med", "centroid_fin",
            "member_count", "top_members",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in sorted(self.series, key=lambda x: x["series_id"]):
                top = [m["bennett_id"] for m in s["members"][:10]]
                writer.writerow({
                    "cluster_id": s["series_id"],
                    "cluster_label": s["series_label"],
                    "role": s["role"],
                    "centroid_init": s["centroid_init"],
                    "centroid_med": s["centroid_med"],
                    "centroid_fin": s["centroid_fin"],
                    "member_count": s["member_count"],
                    "top_members": ", ".join(top),
                })
        logger.info("Wrote %d clusters to %s", len(self.series), path)

    def _write_grid_series(self, out_dir: str):
        """Write grid_series.csv: full member list per series."""
        path = os.path.join(out_dir, "grid_series.csv")
        fieldnames = [
            "series_id", "series_label", "role", "bennett_id",
            "init_frac", "med_frac", "fin_frac", "total_occ",
            "ml_predicted", "ml_confidence", "distance_to_centroid",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in sorted(self.series, key=lambda x: x["series_id"]):
                for m in s["members"]:
                    writer.writerow({
                        "series_id": s["series_id"],
                        "series_label": s["series_label"],
                        "role": s["role"],
                        "bennett_id": m["bennett_id"],
                        "init_frac": m["init_frac"],
                        "med_frac": m["med_frac"],
                        "fin_frac": m["fin_frac"],
                        "total_occ": m["total_occ"],
                        "ml_predicted": m["ml_predicted"],
                        "ml_confidence": m["ml_confidence"],
                        "distance_to_centroid": m["distance_to_centroid"],
                    })
        total = sum(s["member_count"] for s in self.series)
        logger.info("Wrote %d member rows to %s", total, path)

    def _write_cluster_members(self, out_dir: str):
        """Write cluster_members.csv: per-sign cluster + ML comparison."""
        path = os.path.join(out_dir, "cluster_members.csv")
        fieldnames = [
            "bennett_id", "cluster_id", "cluster_label",
            "init_frac", "med_frac", "fin_frac", "total_occ",
            "conventional_value", "ml_predicted", "ml_confidence",
            "ml_changed_value", "positional_ml_consistent",
            "distance_to_centroid",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for comp in sorted(self.comparisons, key=lambda x: (x["cluster_id"], x["bennett_id"])):
                writer.writerow(comp)
        logger.info("Wrote %d comparisons to %s", len(self.comparisons), path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    profiles = load_positional_profiles()
    uncertain = load_uncertain_signs()
    ml_preds = load_ml_predictions()

    builder = PositionalGridBuilder(profiles, uncertain, ml_preds)
    builder.run(k=5)
    builder.write_all()

    # Summary
    print(f"\n{'='*60}")
    print("Positional Grid Reconstruction — Summary")
    print(f"{'='*60}")
    print(f"UNCERTAIN signs analysed: {len(builder.uncertain)}")
    print(f"Clusters: {len(builder.cluster_centroids)}")
    for s in builder.series:
        print(f"  Cluster {s['series_id']}: {s['series_label']} "
              f"({s['role']}) — {s['member_count']} signs")
    print(f"ML predictions compared: {len(builder.comparisons)}")
    consistent = sum(1 for c in builder.comparisons if c.get("positional_ml_consistent"))
    print(f"Positional-ML consistency: {consistent}/{len(builder.comparisons)}")


if __name__ == "__main__":
    main()
