#!/usr/bin/env python3
"""
Kober-Style Positional Grid Analysis for Linear A Corpus
=========================================================
Implements the core method pioneered by Alice Kober (1945–1948): by tabulating
where each sign occurs *within* a text (initial, medial, final position), we
derive a *positional profile* for every sign.  These profiles are then:

  1. Clustered via K-means to reveal natural functional classes
     (prefix-like, suffix-like, neutral/flexible).
  2. Analysed against the conventional AB phonetic grid (transferred from
     Linear B) to flag signs whose positional distribution contradicts their
     presumed phonetic class — candidates for misvaluation from the AB transfer.

Outputs (all written to ``data/analysis/positional/``):
  - positional_profiles.csv   — per-sign initial/medial/final fractions
  - sign_clusters.csv         — K-means cluster assignments + centroids
  - candidate_prefixes.csv    — signs strongly biased toward text-initial
  - candidate_suffixes.csv    — signs strongly biased toward text-final
  - misvalued_signs_ranked.csv — AB signs ranked by phonetic-class anomaly

Dependencies: sqlite3 (stdlib), csv (stdlib), math (stdlib), json (stdlib).
No pandas, networkx, or matplotlib required.
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict, Counter
from typing import Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("positional_analysis")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "database", "lineara_full.db",
)
DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "analysis", "positional",
)

# ---------------------------------------------------------------------------
# Embedded AB phonetic grid (transferred from Linear B)
#
# Source: GORILA / Bennett AB numbering + conventional Linear B values.
# Format: (bennett_id, transliteration, phonetic_class)
#
# Phonetic classes:
#   "V"   = pure vowel (a, e, i, o, u)
#   "CV"  = consonant + vowel (da, ro, pa, te, …)
#   "CVC" = consonant + vowel + consonant / complex (pte, nwa, …)
#   "?"   = unknown / uncertain
# ---------------------------------------------------------------------------

AB_PHONETIC_GRID: list[tuple[str, str, str]] = [
    # Bennett ID  ,  transliteration,  class
    ("AB 01", "da",  "CV"),
    ("AB 02", "ro",  "CV"),
    ("AB 03", "pa",  "CV"),
    ("AB 04", "te",  "CV"),
    ("AB 05", "to",  "CV"),
    ("AB 06", "na",  "CV"),
    ("AB 07", "di",  "CV"),
    ("AB 08", "a",   "V"),
    ("AB 09", "se",  "CV"),
    ("AB 10", "u",   "V"),
    ("AB 11", "si",  "CV"),
    ("AB 12", "so",  "CV"),
    ("AB 13", "me",  "CV"),
    ("AB 14", "do",  "CV"),
    ("AB 15", "mo",  "CV"),
    ("AB 16", "qa",  "CV"),
    ("AB 17", "za",  "CV"),
    ("AB 18", "zo",  "CV"),
    ("AB 19", "?,zo?", "?"),
    ("AB 20", "zo?", "?"),
    ("AB 21", "mi",  "CV"),
    ("AB 21f", "mi?", "?"),
    ("AB 22", "pi",  "CV"),
    ("AB 22f", "pi?", "?"),
    ("AB 23", "mu",  "CV"),
    ("AB 24", "ne",  "CV"),
    ("AB 26", "ru",  "CV"),
    ("AB 27", "re",  "CV"),
    ("AB 28", "i",   "V"),
    ("AB 29", "pu",  "CV"),
    ("AB 30", "ni",  "CV"),
    ("AB 31", "sa",  "CV"),
    ("AB 32", "?",   "?"),
    ("AB 33", "ra?", "?"),
    ("AB 34", "?,pa2?", "?"),
    ("AB 35", "ti",  "CV"),
    ("AB 36", "jo",  "CV"),
    ("AB 37", "?",   "?"),
    ("AB 38", "e",   "V"),
    ("AB 39", "?,pi?", "?"),
    ("AB 40", "wi",  "CV"),
    ("AB 41", "si?", "?"),
    ("AB 42", "ke?", "?"),
    ("AB 43", "ai?", "?"),
    ("AB 44", "?",   "?"),
    ("AB 45", "?,de?", "?"),
    ("AB 46", "?,je?", "?"),
    ("AB 47", "?",   "?"),
    ("AB 48", "?,nwa?", "?"),
    ("AB 49", "?",   "?"),
    ("AB 50", "pu?", "?"),
    ("AB 51", "du?", "?"),
    ("AB 52", "?",   "?"),
    ("AB 53", "ri",  "CV"),
    ("AB 54", "wa",  "CV"),
    ("AB 55", "nu",  "CV"),
    ("AB 56", "?",   "?"),
    ("AB 57", "ja",  "CV"),
    ("AB 58", "?",   "?"),
    ("AB 59", "?",   "?"),
    ("AB 60", "ra",  "CV"),
    ("AB 61", "?",   "?"),
    ("AB 62", "?,pte?", "?"),
    ("AB 63", "?",   "?"),
    ("AB 64", "?,swi?", "?"),
    ("AB 65", "ju?", "?"),
    ("AB 66", "ta?", "?"),
    ("AB 67", "ki",  "CV"),
    ("AB 68", "ro2?", "?"),
    ("AB 69", "tu",  "CV"),
    ("AB 70", "?,ko?", "?"),
    ("AB 71", "?",   "?"),
    ("AB 72", "?",   "?"),
    ("AB 73", "?",   "?"),
    ("AB 74", "ze?", "?"),
    ("AB 75", "?",   "?"),
    ("AB 76", "ra2?", "?"),
    ("AB 77", "ka",  "CV"),
    ("AB 78", "qe",  "CV"),
    ("AB 79", "zo?", "?"),
    ("AB 80", "ma",  "CV"),
    ("AB 81", "ku",  "CV"),
    ("AB 82", "?",   "?"),
    ("AB 83", "?",   "?"),
    ("AB 84", "?",   "?"),
    ("AB 85", "?",   "?"),
    ("AB 86", "?",   "?"),
    ("AB 87", "?",   "?"),
    ("AB 88", "?",   "?"),
    ("AB 89", "?",   "?"),
    ("AB 90", "?",   "?"),
    ("AB 91", "?",   "?"),
    ("AB 92", "?",   "?"),
    ("AB 93", "?",   "?"),
    ("AB 94", "?",   "?"),
    ("AB 95", "?",   "?"),
    ("AB 96", "?",   "?"),
    ("AB 97", "?",   "?"),
    ("AB 98", "?",   "?"),
    ("AB 99", "?",   "?"),
    ("AB 100", "?",  "?"),
    ("AB 101", "?",  "?"),
    ("AB 102", "?",  "?"),
    ("AB 103", "?",  "?"),
    ("AB 104", "?",  "?"),
    ("AB 105", "?",  "?"),
    ("AB 106", "?",  "?"),
    ("AB 107", "?",  "?"),
    ("AB 108", "?",  "?"),
    ("AB 109", "?",  "?"),
    ("AB 110", "?",  "?"),
    ("AB 111", "?",  "?"),
    ("AB 112", "?",  "?"),
    ("AB 113", "?",  "?"),
    ("AB 114", "?",  "?"),
    ("AB 115", "?",  "?"),
    ("AB 116", "?",  "?"),
    ("AB 117", "?",  "?"),
    ("AB 118", "?",  "?"),
    ("AB 119", "?",  "?"),
    ("AB 120", "?",  "?"),
    ("AB 121", "?",  "?"),
    ("AB 122", "?",  "?"),
    ("AB 123", "?",  "?"),
    ("AB 124", "?",  "?"),
    ("AB 125", "?",  "?"),
    ("AB 126", "?",  "?"),
    ("AB 127", "?",  "?"),
    ("AB 128", "?",  "?"),
    ("AB 129", "?",  "?"),
    ("AB 130", "?",  "?"),
    ("AB 131", "?",  "?"),
    ("AB 132", "?",  "?"),
    ("AB 133", "?",  "?"),
    ("AB 134", "?",  "?"),
    ("AB 135", "?",  "?"),
    ("AB 136", "?",  "?"),
    ("AB 137", "?",  "?"),
]

# Build lookup dictionaries
_AB_GRID: dict[str, dict[str, str]] = {}
for _ben, _trans, _cls in AB_PHONETIC_GRID:
    _AB_GRID[_ben] = {"transliteration": _trans, "phonetic_class": _cls}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def entropy(probs: list[float]) -> float:
    """Shannon entropy (base 2) of a probability distribution."""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def k_means(data: list[list[float]], k: int,
            max_iter: int = 100, seed: int = 42) -> tuple[list[int], list[list[float]]]:
    """
    Classic K-means clustering.

    Args:
        data: list of N vectors (each of length D).
        k: number of clusters.
        max_iter: maximum iterations.
        seed: random seed for reproducibility.

    Returns:
        labels: list[N] of cluster assignments (0 … k-1).
        centroids: list[k] of centroid vectors.
    """
    N = len(data)
    if N == 0:
        return [], []
    D = len(data[0])

    rng = random.Random(seed)

    # Initialise centroids by sampling k distinct data points (Forgy method)
    indices = list(range(N))
    rng.shuffle(indices)
    centroids = [data[indices[i]][:] for i in range(min(k, N))]

    # If k > N, pad with random points
    while len(centroids) < k:
        centroids.append([rng.random() for _ in range(D)])

    labels = [0] * N

    for iteration in range(max_iter):
        # Assign each point to nearest centroid
        changed = 0
        for i in range(N):
            best_d = float("inf")
            best_c = 0
            for c_idx, cent in enumerate(centroids):
                d = euclidean_distance(data[i], cent)
                if d < best_d:
                    best_d = d
                    best_c = c_idx
            if labels[i] != best_c:
                labels[i] = best_c
                changed += 1

        # Update centroids
        new_centroids = [[0.0] * D for _ in range(k)]
        counts = [0] * k
        for i in range(N):
            c = labels[i]
            for d_idx in range(D):
                new_centroids[c][d_idx] += data[i][d_idx]
            counts[c] += 1

        for c_idx in range(k):
            if counts[c_idx] > 0:
                for d_idx in range(D):
                    new_centroids[c_idx][d_idx] /= counts[c_idx]
            else:
                # Empty cluster: reinitialise to a random point
                ri = rng.randint(0, N - 1)
                new_centroids[c_idx] = data[ri][:]

        # Check convergence
        shift = sum(euclidean_distance(centroids[c], new_centroids[c]) for c in range(k))
        centroids = new_centroids

        if shift < 1e-6 or changed == 0:
            logger.debug("K-means converged after %d iterations (shift=%g)", iteration + 1, shift)
            break

    return labels, centroids


def kl_divergence(p: list[float], q: list[float]) -> float:
    """
    Kullback–Leibler divergence D_KL(p || q).
    Assumes p and q are valid probability vectors (sum ~ 1).
    """
    return sum(p[i] * math.log2(p[i] / q[i]) if p[i] > 0 else 0.0 for i in range(len(p)))


# ---------------------------------------------------------------------------
# Core analysis class
# ---------------------------------------------------------------------------

class PositionalGridAnalyzer:
    """
    Performs Kober-style positional grid analysis on the Linear A corpus.

    1. Extracts sign sequences from the database.
    2. Computes per-sign positional frequency tables.
    3. Clusters signs by positional profile using K-means.
    4. Identifies prefix/suffix candidates.
    5. Evaluates AB phonetic grid consistency.
    """

    def __init__(self, db_path: str, min_occurrences: int = 5):
        self.db_path = db_path
        self.min_occurrences = min_occurrences
        self.conn: Optional[sqlite3.Connection] = None

        # Results populated by run()
        self.positional_counts: dict[str, dict[str, float]] = {}   # sign -> {initial, medial, final}
        self.positional_profiles: dict[str, dict[str, float]] = {} # sign -> fraction vectors
        self.cluster_labels: dict[str, int] = {}
        self.cluster_centroids: list[list[float]] = []
        self.prefix_candidates: list[tuple[str, float]] = []      # (sign, initial_bias)
        self.suffix_candidates: list[tuple[str, float]] = []

    # ------------------------------------------------------------------
    # Database connection
    # ------------------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        """Open connection to the SQLite database."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                "Run the corpus ingestion pipeline first."
            )
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        logger.info("Connected to database: %s", self.db_path)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Step 1: Extract sign sequences per inscription
    # ------------------------------------------------------------------

    def fetch_sign_sequences(self) -> list[list[dict]]:
        """
        Fetch all inscriptions with their signs in reading order.

        Returns a list of sign sequences, where each sequence is a list of
        dicts with keys: bennett_id, sign_type, transliteration, sequence.
        Only syllabograms are included (logograms, numerals, fractions skipped).
        """
        if not self.conn:
            raise RuntimeError("Not connected. Call connect() first.")

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, gorila_id FROM inscriptions ORDER BY id"""
        )
        inscriptions = cursor.fetchall()
        logger.info("Found %d inscriptions", len(inscriptions))

        sequences = []
        skipped_no_bennett = 0
        skipped_short = 0

        for ins in inscriptions:
            ins_id = ins["id"]
            gorila = ins["gorila_id"]
            cursor.execute(
                """SELECT sequence, bennett_id, sign_type, transliteration
                   FROM signs
                   WHERE inscription_id = ?
                   ORDER BY sequence""",
                (ins_id,),
            )
            sign_rows = cursor.fetchall()

            # Filter to syllabograms only (skip logograms, numerals, fractions, etc.)
            syllabograms = []
            for sr in sign_rows:
                sdict = dict(sr)
                stype = sdict.get("sign_type", "syllabogram") or "syllabogram"
                bennett = sdict.get("bennett_id") or ""
                if stype in ("syllabogram",) and bennett:
                    syllabograms.append(sdict)
                else:
                    if not bennett:
                        skipped_no_bennett += 1

            # We need at least 1 sign to count position
            if len(syllabograms) < 1:
                skipped_short += 1
                continue

            sequences.append(syllabograms)

        logger.info(
            "Extracted %d sign sequences (%d skipped: no bennett_id=%d, <1 signs=%d)",
            len(sequences), skipped_no_bennett + skipped_short,
            skipped_no_bennett, skipped_short,
        )
        return sequences

    # ------------------------------------------------------------------
    # Step 2: Compute positional frequency tables
    # ------------------------------------------------------------------

    def compute_positional_counts(self, sequences: list[list[dict]]):
        """
        For each sign, count occurrences in initial, medial, and final
        position of each text.

        Position rules:
          - L == 1: the sole sign is counted as BOTH initial AND final.
          - L == 2: sign[0] = initial, sign[1] = final.
          - L >= 3: sign[0] = initial, sign[L-1] = final,
                    signs[1..L-2] = medial.
        """
        counts: dict[str, dict[str, float]] = defaultdict(lambda: {"initial": 0, "medial": 0, "final": 0})
        total_signs = 0

        for seq in sequences:
            L = len(seq)
            for idx, s in enumerate(seq):
                bennett = s["bennett_id"]
                if not bennett:
                    continue
                total_signs += 1

                if L == 1:
                    counts[bennett]["initial"] += 1
                    counts[bennett]["final"] += 1
                elif L == 2:
                    if idx == 0:
                        counts[bennett]["initial"] += 1
                    else:  # idx == 1
                        counts[bennett]["final"] += 1
                else:  # L >= 3
                    if idx == 0:
                        counts[bennett]["initial"] += 1
                    elif idx == L - 1:
                        counts[bennett]["final"] += 1
                    else:
                        counts[bennett]["medial"] += 1

        self.positional_counts = dict(counts)
        logger.info(
            "Positional counts computed for %d signs (%d total sign occurrences)",
            len(counts), total_signs,
        )

    # ------------------------------------------------------------------
    # Step 3: Build positional profiles (fractions)
    # ------------------------------------------------------------------

    def build_profiles(self):
        """
        Convert absolute counts to fractional profiles.
        Only signs with >= min_occurrences total are retained.
        """
        profiles: dict[str, dict[str, float]] = {}
        for sign, cnts in self.positional_counts.items():
            total = cnts["initial"] + cnts["medial"] + cnts["final"]
            if total < self.min_occurrences:
                continue
            profiles[sign] = {
                "initial": cnts["initial"] / total,
                "medial": cnts["medial"] / total,
                "final": cnts["final"] / total,
                "total": total,
                "raw_initial": cnts["initial"],
                "raw_medial": cnts["medial"],
                "raw_final": cnts["final"],
            }
        self.positional_profiles = profiles
        logger.info(
            "Profiles built for %d signs (min_occurrences=%d)",
            len(profiles), self.min_occurrences,
        )

    # ------------------------------------------------------------------
    # Step 4: K-means clustering
    # ------------------------------------------------------------------

    def cluster_profiles(self, k: int = 4):
        """
        Cluster signs by their [initial, medial, final] fractional profile
        using K-means with k clusters.

        The expected cluster archetypes:
          - Prefix-like: high initial, low medial/final
          - Suffix-like: high final, low initial/medial
          - Flexible: roughly even across all three
          - Medial-biased: high medial (rare but possible for function words)
        """
        signs = sorted(self.positional_profiles.keys())
        if len(signs) < k:
            logger.warning("Fewer signs than clusters (%d < %d); reducing k", len(signs), k)
            k = max(2, len(signs))

        data = [
            [
                self.positional_profiles[s]["initial"],
                self.positional_profiles[s]["medial"],
                self.positional_profiles[s]["final"],
            ]
            for s in signs
        ]

        labels, centroids = k_means(data, k=k, seed=42)

        self.cluster_labels = {signs[i]: labels[i] for i in range(len(signs))}
        self.cluster_centroids = centroids

        logger.info("K-means clustering (k=%d) complete", k)

        # Describe clusters
        for ci, cent in enumerate(centroids):
            init_p, med_p, fin_p = cent
            if init_p > 0.6:
                label = "prefix-like"
            elif fin_p > 0.6:
                label = "suffix-like"
            elif init_p > 0.4 and med_p > 0.4 and fin_p > 0.4:
                label = "flexible"
            elif med_p > 0.6:
                label = "medial-biased"
            elif init_p > fin_p and init_p > med_p:
                label = "initial-tendency"
            elif fin_p > init_p and fin_p > med_p:
                label = "final-tendency"
            else:
                label = "mixed"
            members = [s for s, c in self.cluster_labels.items() if c == ci]
            logger.info(
                "  Cluster %d (%s, n=%d): init=%.3f, med=%.3f, fin=%.3f",
                ci, label, len(members), init_p, med_p, fin_p,
            )

    # ------------------------------------------------------------------
    # Step 5: Identify prefix / suffix candidates
    # ------------------------------------------------------------------

    def find_boundary_candidates(self,
                                  initial_threshold: float = 0.50,
                                  final_threshold: float = 0.50,
                                  min_total: int = 10):
        """
        Identify signs that are strongly biased toward text-initial
        (prefix candidates) or text-final (suffix candidates).

        Args:
            initial_threshold: minimum fraction of occurrences in initial
                               position to be considered a prefix candidate.
            final_threshold:   minimum fraction in final position for suffix.
            min_total:         minimum total occurrences to consider.
        """
        prefixes = []
        suffixes = []

        for sign, prof in self.positional_profiles.items():
            total = prof["total"]
            if total < min_total:
                continue
            if prof["initial"] >= initial_threshold:
                prefixes.append((sign, prof["initial"], prof["final"], total))
            if prof["final"] >= final_threshold:
                suffixes.append((sign, prof["final"], prof["initial"], total))

        # Sort by bias strength (descending)
        prefixes.sort(key=lambda x: x[1], reverse=True)
        suffixes.sort(key=lambda x: x[1], reverse=True)

        self.prefix_candidates = [(s, bias) for (s, bias, _, _) in prefixes]
        self.suffix_candidates = [(s, bias) for (s, bias, _, _) in suffixes]

        logger.info(
            "Found %d prefix candidates (init>=%.2f) and %d suffix candidates (fin>=%.2f)",
            len(prefixes), initial_threshold, len(suffixes), final_threshold,
        )

    # ------------------------------------------------------------------
    # Step 6: AB phonetic grid consistency analysis
    # ------------------------------------------------------------------

    def analyze_ab_phonetic_grid(self) -> list[dict]:
        """
        For each AB sign with a known (or tentative) phonetic value from the
        Linear B transfer, compute:
          - Positional entropy
          - Phonetic class expectation
          - Anomaly score: divergence between this sign's profile and the
            mean profile of its phonetic class (CV, V, etc.)

        Returns a list of dicts sorted by anomaly score (descending).
        """
        # Group signs by phonetic class
        class_profiles: dict[str, list[list[float]]] = defaultdict(list)
        sign_info: list[dict] = []

        for sign, prof in self.positional_profiles.items():
            if sign not in _AB_GRID:
                continue
            grid_entry = _AB_GRID[sign]
            pclass = grid_entry["phonetic_class"]
            if pclass == "?":
                continue  # skip unknown phonetic values

            vector = [prof["initial"], prof["medial"], prof["final"]]
            ent = entropy(vector)

            info = {
                "bennett_id": sign,
                "transliteration": grid_entry["transliteration"],
                "phonetic_class": pclass,
                "initial_fraction": prof["initial"],
                "medial_fraction": prof["medial"],
                "final_fraction": prof["final"],
                "total_occurrences": prof["total"],
                "positional_entropy": ent,
            }
            sign_info.append(info)
            class_profiles[pclass].append(vector)

        # Compute mean profile for each phonetic class
        class_mean: dict[str, list[float]] = {}
        for cls, vectors in class_profiles.items():
            n = len(vectors)
            if n == 0:
                continue
            mean_vec = [0.0, 0.0, 0.0]
            for v in vectors:
                for i in range(3):
                    mean_vec[i] += v[i]
            for i in range(3):
                mean_vec[i] /= n
            class_mean[cls] = mean_vec

        # Compute anomaly score: KL divergence from class mean
        for info in sign_info:
            cls = info["phonetic_class"]
            if cls in class_mean:
                vec = [info["initial_fraction"], info["medial_fraction"], info["final_fraction"]]
                mean_vec = class_mean[cls]
                # Add small epsilon to avoid log(0)
                eps = 1e-10
                vec_smooth = [v + eps for v in vec]
                mean_smooth = [m + eps for m in mean_vec]
                # Renormalise
                s1 = sum(vec_smooth)
                vec_smooth = [v / s1 for v in vec_smooth]
                s2 = sum(mean_smooth)
                mean_smooth = [v / s2 for v in mean_smooth]
                info["class_mean_initial"] = mean_vec[0]
                info["class_mean_medial"] = mean_vec[1]
                info["class_mean_final"] = mean_vec[2]
                info["kl_divergence"] = kl_divergence(vec_smooth, mean_smooth)
                # Also compute a simpler deviation: euclidean distance from class mean
                info["euclidean_deviation"] = euclidean_distance(vec, mean_vec)
            else:
                info["class_mean_initial"] = None
                info["class_mean_medial"] = None
                info["class_mean_final"] = None
                info["kl_divergence"] = None
                info["euclidean_deviation"] = None

            # Positional bias flags
            flags = []
            if info["initial_fraction"] > 0.5:
                flags.append("initial-biased")
            if info["final_fraction"] > 0.5:
                flags.append("final-biased")
            if info["final_fraction"] > 0.4 and cls == "CV":
                flags.append("ANOMALOUS: CV sign in final position")
            if info["initial_fraction"] > 0.4 and cls == "CV":
                flags.append("prefix-like CV sign")
            if info["initial_fraction"] > 0.5 and cls == "V":
                flags.append("vowel-prefix candidate")
            info["flags"] = "; ".join(flags) if flags else ""

        # Sort by KL divergence descending (most anomalous first)
        sign_info.sort(key=lambda x: x.get("kl_divergence") or 0, reverse=True)

        logger.info(
            "AB phonetic grid analysis: %d signs with known values, %d classes",
            len(sign_info), len(class_mean),
        )
        return sign_info

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def run(self, output_dir: str = DEFAULT_OUT,
            k_clusters: int = 4,
            initial_threshold: float = 0.50,
            final_threshold: float = 0.50,
            min_total_boundary: int = 10):
        """Execute the full positional grid analysis pipeline."""
        logger.info("=" * 60)
        logger.info("Kober-Style Positional Grid Analysis")
        logger.info("=" * 60)

        # 1. Connect
        self.connect()

        # 2. Fetch sequences
        sequences = self.fetch_sign_sequences()

        # 3. Compute counts
        self.compute_positional_counts(sequences)

        # 4. Build profiles
        self.build_profiles()

        # 5. Cluster
        self.cluster_profiles(k=k_clusters)

        # 6. Find boundary candidates
        self.find_boundary_candidates(
            initial_threshold=initial_threshold,
            final_threshold=final_threshold,
            min_total=min_total_boundary,
        )

        # 7. AB phonetic grid analysis
        ab_analysis = self.analyze_ab_phonetic_grid()

        # 8. Write outputs
        os.makedirs(output_dir, exist_ok=True)
        self.write_positional_profiles(output_dir)
        self.write_clusters(output_dir)
        self.write_boundary_candidates(output_dir)
        self.write_misvalued_signs(output_dir, ab_analysis)
        self.write_summary_report(output_dir, ab_analysis)

        self.close()
        logger.info("All outputs written to %s", output_dir)

    # ------------------------------------------------------------------
    # Output writers
    # ------------------------------------------------------------------

    def write_positional_profiles(self, output_dir: str):
        """Write positional_profiles.csv: per-sign initial/medial/final fractions."""
        path = os.path.join(output_dir, "positional_profiles.csv")
        fieldnames = [
            "bennett_id", "sign_type", "transliteration", "phonetic_class",
            "total_occurrences",
            "raw_initial", "raw_medial", "raw_final",
            "initial_fraction", "medial_fraction", "final_fraction",
            "positional_entropy",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for sign in sorted(self.positional_profiles.keys()):
                prof = self.positional_profiles[sign]
                grid = _AB_GRID.get(sign, {})
                trans = grid.get("transliteration", "")
                pclass = grid.get("phonetic_class", "")
                ent = entropy([prof["initial"], prof["medial"], prof["final"]])
                # Determine sign type from bennett prefix
                stype = "syllabogram"
                if sign.startswith("A ") or sign.startswith("VASE"):
                    stype = "logogram"
                elif sign.startswith("NUM"):
                    stype = "numeral"
                elif sign.startswith("ADJ"):
                    stype = "adjunct"

                writer.writerow({
                    "bennett_id": sign,
                    "sign_type": stype,
                    "transliteration": trans,
                    "phonetic_class": pclass,
                    "total_occurrences": int(prof["total"]),
                    "raw_initial": int(prof["raw_initial"]),
                    "raw_medial": int(prof["raw_medial"]),
                    "raw_final": int(prof["raw_final"]),
                    "initial_fraction": round(prof["initial"], 6),
                    "medial_fraction": round(prof["medial"], 6),
                    "final_fraction": round(prof["final"], 6),
                    "positional_entropy": round(ent, 6),
                })
        count = len(self.positional_profiles)
        logger.info("Wrote %d profiles to %s", count, path)

    def write_clusters(self, output_dir: str):
        """Write sign_clusters.csv: cluster assignments and centroids."""
        path = os.path.join(output_dir, "sign_clusters.csv")
        # Describe centroids
        centroid_descriptions = []
        for ci, cent in enumerate(self.cluster_centroids):
            init_p, med_p, fin_p = cent
            if init_p > 0.6:
                desc = "prefix-like"
            elif fin_p > 0.6:
                desc = "suffix-like"
            elif med_p > 0.6:
                desc = "medial-biased"
            elif init_p > 0.35 and fin_p > 0.35:
                desc = "flexible"
            elif init_p > fin_p and init_p > med_p:
                desc = "initial-tendency"
            elif fin_p > init_p and fin_p > med_p:
                desc = "final-tendency"
            else:
                desc = "mixed"
            centroid_descriptions.append(desc)

        fieldnames = [
            "bennett_id", "cluster_id", "cluster_label",
            "initial_fraction", "medial_fraction", "final_fraction",
            "distance_to_centroid",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sign in sorted(self.cluster_labels.keys()):
                cid = self.cluster_labels[sign]
                prof = self.positional_profiles[sign]
                cent = self.cluster_centroids[cid]
                vec = [prof["initial"], prof["medial"], prof["final"]]
                dist = euclidean_distance(vec, cent)
                writer.writerow({
                    "bennett_id": sign,
                    "cluster_id": cid,
                    "cluster_label": centroid_descriptions[cid] if cid < len(centroid_descriptions) else f"cluster_{cid}",
                    "initial_fraction": round(prof["initial"], 6),
                    "medial_fraction": round(prof["medial"], 6),
                    "final_fraction": round(prof["final"], 6),
                    "distance_to_centroid": round(dist, 6),
                })

            # Append centroid rows
            for ci, cent in enumerate(self.cluster_centroids):
                writer.writerow({
                    "bennett_id": f"CENTROID_{ci}",
                    "cluster_id": ci,
                    "cluster_label": centroid_descriptions[ci] if ci < len(centroid_descriptions) else f"cluster_{ci}",
                    "initial_fraction": round(cent[0], 6),
                    "medial_fraction": round(cent[1], 6),
                    "final_fraction": round(cent[2], 6),
                    "distance_to_centroid": 0.0,
                })

        logger.info("Wrote cluster assignments to %s", path)

    def write_boundary_candidates(self, output_dir: str):
        """Write candidate_prefixes.csv and candidate_suffixes.csv."""
        # Prefixes
        path_pre = os.path.join(output_dir, "candidate_prefixes.csv")
        fieldnames = [
            "bennett_id", "transliteration", "phonetic_class",
            "initial_fraction", "final_fraction", "total_occurrences",
        ]
        with open(path_pre, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for sign, _ in self.prefix_candidates:
                prof = self.positional_profiles[sign]
                grid = _AB_GRID.get(sign, {})
                writer.writerow({
                    "bennett_id": sign,
                    "transliteration": grid.get("transliteration", ""),
                    "phonetic_class": grid.get("phonetic_class", ""),
                    "initial_fraction": round(prof["initial"], 6),
                    "final_fraction": round(prof["final"], 6),
                    "total_occurrences": int(prof["total"]),
                })
        logger.info("Wrote %d prefix candidates to %s", len(self.prefix_candidates), path_pre)

        # Suffixes
        path_suf = os.path.join(output_dir, "candidate_suffixes.csv")
        with open(path_suf, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for sign, _ in self.suffix_candidates:
                prof = self.positional_profiles[sign]
                grid = _AB_GRID.get(sign, {})
                writer.writerow({
                    "bennett_id": sign,
                    "transliteration": grid.get("transliteration", ""),
                    "phonetic_class": grid.get("phonetic_class", ""),
                    "initial_fraction": round(prof["initial"], 6),
                    "final_fraction": round(prof["final"], 6),
                    "total_occurrences": int(prof["total"]),
                })
        logger.info("Wrote %d suffix candidates to %s", len(self.suffix_candidates), path_suf)

    def write_misvalued_signs(self, output_dir: str, ab_analysis: list[dict]):
        """
        Write misvalued_signs_ranked.csv: signs with anomalous positional
        distribution for their presumed phonetic class, ranked by anomaly.
        """
        path = os.path.join(output_dir, "misvalued_signs_ranked.csv")
        fieldnames = [
            "rank", "bennett_id", "transliteration", "phonetic_class",
            "total_occurrences",
            "initial_fraction", "medial_fraction", "final_fraction",
            "positional_entropy",
            "class_mean_initial", "class_mean_medial", "class_mean_final",
            "kl_divergence", "euclidean_deviation",
            "flags",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rank, info in enumerate(ab_analysis, start=1):
                writer.writerow({
                    "rank": rank,
                    "bennett_id": info["bennett_id"],
                    "transliteration": info["transliteration"],
                    "phonetic_class": info["phonetic_class"],
                    "total_occurrences": info["total_occurrences"],
                    "initial_fraction": round(info["initial_fraction"], 6),
                    "medial_fraction": round(info["medial_fraction"], 6),
                    "final_fraction": round(info["final_fraction"], 6),
                    "positional_entropy": round(info["positional_entropy"], 6),
                    "class_mean_initial": round(info["class_mean_initial"], 6) if info["class_mean_initial"] is not None else "",
                    "class_mean_medial": round(info["class_mean_medial"], 6) if info["class_mean_medial"] is not None else "",
                    "class_mean_final": round(info["class_mean_final"], 6) if info["class_mean_final"] is not None else "",
                    "kl_divergence": round(info["kl_divergence"], 6) if info["kl_divergence"] is not None else "",
                    "euclidean_deviation": round(info["euclidean_deviation"], 6) if info["euclidean_deviation"] is not None else "",
                    "flags": info["flags"],
                })
        logger.info("Wrote %d ranked misvalued-sign entries to %s", len(ab_analysis), path)

    def write_summary_report(self, output_dir: str, ab_analysis: list[dict]):
        """
        Write a human-readable summary report as CSV data tables, containing
        aggregate statistics.
        """
        path = os.path.join(output_dir, "analysis_summary.csv")

        # Build summary rows as a flat table
        rows = []

        # Header section
        rows.append({"section": "META", "key": "database", "value": self.db_path})
        rows.append({"section": "META", "key": "min_occurrences", "value": str(self.min_occurrences)})

        # Corpus stats
        total_signs_distinct = len(self.positional_profiles)
        total_counts = sum(
            p["raw_initial"] + p["raw_medial"] + p["raw_final"]
            for p in self.positional_profiles.values()
        )
        rows.append({"section": "CORPUS", "key": "signs_with_profiles", "value": str(total_signs_distinct)})
        rows.append({"section": "CORPUS", "key": "total_sign_occurrences_analysed", "value": str(int(total_counts))})

        # Cluster summary
        cluster_sizes = Counter(self.cluster_labels.values())
        for cid in range(len(self.cluster_centroids)):
            cent = self.cluster_centroids[cid]
            size = cluster_sizes.get(cid, 0)
            if cent[0] > 0.6:
                label = "prefix-like"
            elif cent[2] > 0.6:
                label = "suffix-like"
            elif cent[1] > 0.6:
                label = "medial-biased"
            elif cent[0] > 0.35 and cent[2] > 0.35:
                label = "flexible"
            elif cent[0] > cent[2] and cent[0] > cent[1]:
                label = "initial-tendency"
            elif cent[2] > cent[0] and cent[2] > cent[1]:
                label = "final-tendency"
            else:
                label = "mixed"
            rows.append({
                "section": "CLUSTER",
                "key": f"cluster_{cid}",
                "value": json.dumps({
                    "label": label,
                    "size": size,
                    "initial": round(cent[0], 4),
                    "medial": round(cent[1], 4),
                    "final": round(cent[2], 4),
                }),
            })

        # Prefix/suffix counts
        rows.append({"section": "BOUNDARY", "key": "prefix_candidates", "value": str(len(self.prefix_candidates))})
        rows.append({"section": "BOUNDARY", "key": "suffix_candidates", "value": str(len(self.suffix_candidates))})

        # Top prefix candidates (top 10)
        for sign, bias in self.prefix_candidates[:10]:
            rows.append({
                "section": "TOP_PREFIX",
                "key": sign,
                "value": f"init_bias={bias:.4f}",
            })

        # Top suffix candidates (top 10)
        for sign, bias in self.suffix_candidates[:10]:
            rows.append({
                "section": "TOP_SUFFIX",
                "key": sign,
                "value": f"final_bias={bias:.4f}",
            })

        # AB grid: most anomalous signs (top 20)
        for info in ab_analysis[:20]:
            flags = info.get("flags", "")
            if flags:
                rows.append({
                    "section": "ANOMALOUS_AB",
                    "key": info["bennett_id"],
                    "value": json.dumps({
                        "trans": info["transliteration"],
                        "class": info["phonetic_class"],
                        "kl_div": round(info.get("kl_divergence") or 0, 4),
                        "final_frac": round(info["final_fraction"], 4),
                        "init_frac": round(info["initial_fraction"], 4),
                        "flags": flags,
                    }),
                })

        # Phonetic class means
        for cls_name in ("CV", "V", "CVC", "?"):
            members = [i for i in ab_analysis if i["phonetic_class"] == cls_name]
            if members:
                avg_init = sum(m["initial_fraction"] for m in members) / len(members)
                avg_med = sum(m["medial_fraction"] for m in members) / len(members)
                avg_fin = sum(m["final_fraction"] for m in members) / len(members)
                rows.append({
                    "section": "PHONETIC_CLASS",
                    "key": cls_name,
                    "value": json.dumps({
                        "count": len(members),
                        "mean_initial": round(avg_init, 4),
                        "mean_medial": round(avg_med, 4),
                        "mean_final": round(avg_fin, 4),
                    }),
                })

        # Write
        fieldnames = ["section", "key", "value"]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        logger.info("Wrote analysis summary with %d rows to %s", len(rows), path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Kober-Style Positional Grid Analysis for Linear A",
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB,
        help=f"Path to SQLite database (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--out", default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--min-occurrences", type=int, default=5,
        help="Minimum occurrences for a sign to be profiled (default: 5)",
    )
    parser.add_argument(
        "--k-clusters", type=int, default=4,
        help="Number of K-means clusters (default: 4)",
    )
    parser.add_argument(
        "--initial-threshold", type=float, default=0.50,
        help="Initial fraction threshold for prefix candidates (default: 0.50)",
    )
    parser.add_argument(
        "--final-threshold", type=float, default=0.50,
        help="Final fraction threshold for suffix candidates (default: 0.50)",
    )
    parser.add_argument(
        "--min-total-boundary", type=int, default=10,
        help="Minimum total occurrences for boundary candidate consideration (default: 10)",
    )
    args = parser.parse_args()

    analyzer = PositionalGridAnalyzer(
        db_path=args.db,
        min_occurrences=args.min_occurrences,
    )
    analyzer.run(
        output_dir=args.out,
        k_clusters=args.k_clusters,
        initial_threshold=args.initial_threshold,
        final_threshold=args.final_threshold,
        min_total_boundary=args.min_total_boundary,
    )


if __name__ == "__main__":
    main()
