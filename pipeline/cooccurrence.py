"""
Sign Co-Occurrence Matrix Generator
====================================
Computes pairwise sign co-occurrence within inscriptions, with multiple
normalisation methods: raw count, Jaccard similarity, and Pointwise
Mutual Information (PMI).

Outputs:
  - CSV matrix (sign × sign with co-occurrence values)
  - NetworkX-compatible edge list
  - Visualisation-ready formats
"""

from __future__ import annotations

import csv
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .models import Inscription

logger = logging.getLogger(__name__)

# Optional networkx import
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("networkx not installed; edge-list export will be limited to CSV.")


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

class CooccurrenceMatrix:
    """
    Build and normalise a sign co-occurrence matrix from a corpus of
    Inscription objects.

    Co-occurrence is defined as two signs appearing in the same inscription
    (document-level co-occurrence).  Optionally, one can constrain to signs
    within the same line or word boundary.

    Attributes:
        corpus         — list of Inscription objects
        min_frequency  — minimum number of occurrences for a sign to be included
        context        — 'document' (default), 'line', or 'word'
        sign_index     — dict mapping sign key → column/row index
        index_sign     — reverse mapping
        raw_matrix     — 2D list of raw co-occurrence counts
        size           — number of distinct signs
    """

    def __init__(self,
                 corpus: list[Inscription],
                 min_frequency: int = 1,
                 context: str = "document"):
        self.corpus = corpus
        self.min_frequency = min_frequency
        self.context = context
        self.sign_index: dict[str, int] = {}
        self.index_sign: dict[int, str] = {}
        self.raw_matrix: list[list[int]] = []
        self._frequency: dict[str, int] = defaultdict(int)
        self.size = 0

    def build(self) -> "CooccurrenceMatrix":
        """Build the co-occurrence matrix from the corpus."""
        logger.info("Building co-occurrence matrix (context=%s, min_freq=%d)...",
                     self.context, self.min_frequency)

        # 1. Count sign frequencies
        for ins in self.corpus:
            signs_in_ins = self._get_sign_keys(ins)
            for s in signs_in_ins:
                self._frequency[s] += 1

        # 2. Filter by min frequency
        valid_signs = {s for s, cnt in self._frequency.items() if cnt >= self.min_frequency}
        self.sign_index = {s: i for i, s in enumerate(sorted(valid_signs))}
        self.index_sign = {i: s for s, i in self.sign_index.items()}
        self.size = len(self.sign_index)

        logger.info("  %d distinct signs after frequency filter (min=%d)",
                     self.size, self.min_frequency)

        # 3. Initialise raw matrix
        self.raw_matrix = [[0] * self.size for _ in range(self.size)]

        # 4. Count co-occurrences
        for ins in self.corpus:
            signs_in_ins = self._get_sign_keys(ins)
            # Only consider valid signs
            valid_local = [s for s in signs_in_ins if s in self.sign_index]
            # Unique signs within this context unit
            unique = sorted(set(valid_local))
            for i in range(len(unique)):
                for j in range(i, len(unique)):
                    a, b = unique[i], unique[j]
                    ai, bi = self.sign_index[a], self.sign_index[b]
                    if ai == bi:
                        # Self-co-occurrence = frequency
                        self.raw_matrix[ai][ai] += 1
                    else:
                        self.raw_matrix[ai][bi] += 1
                        self.raw_matrix[bi][ai] += 1

        logger.info("  Matrix built: %d × %d", self.size, self.size)
        return self

    def _get_sign_keys(self, ins: Inscription) -> list[str]:
        """
        Extract the sign key (Bennett ID) from an inscription,
        respecting the context setting.
        """
        if self.context == "document":
            return [s.bennettId for s in ins.signs if s.bennettId]
        elif self.context == "line":
            # Group by line
            keys: list[str] = []
            if ins.structure and ins.structure.lines:
                # Map sequence numbers to lines
                seq_to_line = {}
                for line in ins.structure.lines:
                    for seq in line.signs:
                        seq_to_line[seq] = line.number
                for s in ins.signs:
                    keys.append(s.bennettId or f"?{s.sequence}")
            else:
                keys = [s.bennettId for s in ins.signs if s.bennettId]
            return keys
        elif self.context == "word":
            # Group by word boundary
            keys = []
            if ins.structure and ins.structure.words:
                word_seqs = {seq for wb in ins.structure.words for seq in wb.signSequences}
                for s in ins.signs:
                    if s.sequence in word_seqs:
                        keys.append(s.bennettId or f"?{s.sequence}")
                    else:
                        keys.append(s.bennettId or f"?{s.sequence}")
            else:
                keys = [s.bennettId for s in ins.signs if s.bennettId]
            return keys
        return [s.bennettId for s in ins.signs if s.bennettId]

    # ------------------------------------------------------------------
    # Normalisation methods
    # ------------------------------------------------------------------

    def jaccard_matrix(self) -> list[list[float]]:
        """
        Convert raw counts to Jaccard similarity:
            J(A,B) = |A ∩ B| / |A ∪ B|
        where |A ∩ B| = co-occurrence count,
              |A ∪ B| = freq(A) + freq(B) - co-occurrence.
        """
        size = self.size
        mat = [[0.0] * size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                if i == j:
                    mat[i][j] = 1.0
                    continue
                cooc = self.raw_matrix[i][j]
                if cooc == 0:
                    continue
                fi = self.raw_matrix[i][i]  # frequency of i
                fj = self.raw_matrix[j][j]  # frequency of j
                union = fi + fj - cooc
                mat[i][j] = cooc / union if union > 0 else 0.0
        return mat

    def pmi_matrix(self) -> list[list[float]]:
        """
        Pointwise Mutual Information:
            PMI(A,B) = log( P(A,B) / (P(A) * P(B)) )
        where probabilities are estimated from co-occurrence counts.

        Returns a matrix of PMI values (can be negative).
        """
        size = self.size
        total_cooc = sum(self.raw_matrix[i][j]
                         for i in range(size)
                         for j in range(i, size))
        if total_cooc == 0:
            return [[0.0] * size for _ in range(size)]

        mat = [[0.0] * size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                if i == j:
                    mat[i][j] = 0.0  # self-PMI not meaningful
                    continue
                cooc = self.raw_matrix[i][j]
                if cooc == 0:
                    mat[i][j] = float("-inf")
                    continue
                p_ab = cooc / total_cooc
                p_a = self.raw_matrix[i][i] / total_cooc
                p_b = self.raw_matrix[j][j] / total_cooc
                if p_a == 0 or p_b == 0:
                    mat[i][j] = float("-inf")
                else:
                    mat[i][j] = math.log2(p_ab / (p_a * p_b))
        return mat

    def tscore_matrix(self) -> list[list[float]]:
        """
        T-score: t = (O - E) / sqrt(O)  where O = observed, E = expected.
        A simple association measure.
        """
        size = self.size
        total_cooc = sum(self.raw_matrix[i][j]
                         for i in range(size)
                         for j in range(i, size))
        if total_cooc == 0:
            return [[0.0] * size for _ in range(size)]

        mat = [[0.0] * size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                if i == j:
                    mat[i][j] = 0.0
                    continue
                o = self.raw_matrix[i][j]
                if o == 0:
                    continue
                fi = self.raw_matrix[i][i]
                fj = self.raw_matrix[j][j]
                expected = (fi * fj) / total_cooc
                mat[i][j] = (o - expected) / math.sqrt(o) if o > 0 else 0.0
        return mat

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def write_csv(self, output_path: str,
                  normalize: Optional[str] = None) -> int:
        """
        Write the matrix as a CSV file.

        Args:
            output_path: destination path
            normalize: None for raw, 'jaccard', 'pmi', 'tscore'

        Returns:
            number of rows written
        """
        if normalize == "jaccard":
            matrix_data = self.jaccard_matrix()
            suffix = "jaccard"
        elif normalize == "pmi":
            matrix_data = self.pmi_matrix()
            suffix = "pmi"
        elif normalize == "tscore":
            matrix_data = self.tscore_matrix()
            suffix = "tscore"
        else:
            matrix_data = [[float(v) for v in row] for row in self.raw_matrix]
            suffix = "raw"

        if not output_path.endswith(".csv"):
            output_path = f"{output_path}_{suffix}.csv"

        signs = [self.index_sign[i] for i in range(self.size)]

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Header row
            writer.writerow([""] + signs)
            for i, sign in enumerate(signs):
                row = [sign] + matrix_data[i]
                writer.writerow(row)

        logger.info("Wrote %s matrix CSV to %s", suffix, output_path)
        return self.size

    def write_edge_list(self, output_path: str,
                        normalize: Optional[str] = None,
                        min_weight: float = 0.0,
                        include_negatives: bool = False) -> int:
        """
        Write an edge list (CSV format: sign_a, sign_b, weight).

        Compatible with NetworkX (nx.read_weighted_edgelist).

        Args:
            output_path: destination path (.csv or .edgelist)
            normalize: None, 'jaccard', 'pmi', 'tscore'
            min_weight: minimum absolute weight to include
            include_negatives: if False, skip edges with negative weights

        Returns:
            number of edges written
        """
        if normalize == "jaccard":
            matrix_data = self.jaccard_matrix()
        elif normalize == "pmi":
            matrix_data = self.pmi_matrix()
        elif normalize == "tscore":
            matrix_data = self.tscore_matrix()
        else:
            matrix_data = [[float(v) for v in row] for row in self.raw_matrix]

        signs = [self.index_sign[i] for i in range(self.size)]
        edge_count = 0

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "weight"])
            for i in range(self.size):
                for j in range(i + 1, self.size):
                    w = matrix_data[i][j]
                    if w == float("-inf") or w == float("inf"):
                        continue
                    if not include_negatives and w < 0:
                        continue
                    if abs(w) < min_weight:
                        continue
                    writer.writerow([signs[i], signs[j], round(w, 6)])
                    edge_count += 1

        logger.info("Wrote %d edges to %s", edge_count, output_path)
        return edge_count

    def to_networkx(self, normalize: Optional[str] = None,
                    min_weight: float = 0.0) -> "nx.Graph":
        """
        Build a NetworkX graph from the co-occurrence matrix.

        Requires networkx to be installed.
        """
        if not HAS_NETWORKX:
            raise ImportError("networkx is required for to_networkx(). "
                              "Install with: pip install networkx")

        if normalize == "jaccard":
            matrix_data = self.jaccard_matrix()
        elif normalize == "pmi":
            matrix_data = self.pmi_matrix()
        elif normalize == "tscore":
            matrix_data = self.tscore_matrix()
        else:
            matrix_data = [[float(v) for v in row] for row in self.raw_matrix]

        signs = [self.index_sign[i] for i in range(self.size)]
        G = nx.Graph()
        G.add_nodes_from(signs)

        for i in range(self.size):
            for j in range(i + 1, self.size):
                w = matrix_data[i][j]
                if w == float("-inf") or w == float("inf"):
                    continue
                if abs(w) >= min_weight:
                    G.add_edge(signs[i], signs[j], weight=round(w, 6))

        return G

    def summary(self) -> dict:
        """Return summary statistics about the matrix."""
        non_zero = sum(1 for i in range(self.size) for j in range(i, self.size)
                       if self.raw_matrix[i][j] > 0)
        return {
            "signs": self.size,
            "context": self.context,
            "min_frequency": self.min_frequency,
            "non_zero_pairs": non_zero,
            "total_possible_pairs": self.size * (self.size + 1) // 2,
            "density": non_zero / (self.size * (self.size + 1) / 2) if self.size > 0 else 0,
        }
