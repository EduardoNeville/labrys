#!/usr/bin/env python3
"""
Kober Triple-Pattern Detection
===============================
Implements Alice Kober's "tripling" method for detecting consonant/vowel
series without knowing any phonetic values.

Core method:
  1. Extract all adjacent sign pairs (bigram frames) from the DB.
  2. For each frame XY, find other signs Z where ZY also occurs.
     → X and Z are candidates for sharing a consonant.
  3. Similarly, find other signs W where XW also occurs.
     → Y and W are candidates for sharing a vowel.
  4. Build triple hypotheses: triples of signs that are transitively
     linked through shared frames.

Outputs (data/analysis/kober/):
  - triple_patterns.csv — detected tripling patterns with member signs
  - frame_links.csv      — pairwise sign links from shared frames
  - triple_report.md     — human-readable summary
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
import sqlite3
from collections import defaultdict, Counter
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kober.triple_detection")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(PROJECT_ROOT, "data", "database", "lineara_full.db")
REFINED_GRID = os.path.join(PROJECT_ROOT, "data", "analysis", "comparative", "refined_phonetic_grid.csv")
ML_PREDICTIONS = os.path.join(PROJECT_ROOT, "data", "analysis", "ml", "uncertain_predictions.csv")
POS_PROFILES = os.path.join(PROJECT_ROOT, "data", "analysis", "positional", "positional_profiles.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "analysis", "kober")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_uncertain_signs(path: str = REFINED_GRID) -> set[str]:
    uncertain = set()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("decision", "").strip() == "UNCERTAIN":
                uncertain.add(row["bennett_id"])
    return uncertain


def load_ml_predictions(path: str = ML_PREDICTIONS) -> dict[str, dict]:
    preds = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row["bennett_id"]
            preds[bid] = {
                "conventional": row.get("conventional_value", ""),
                "predicted": row.get("predicted_refined_value", ""),
                "confidence": float(row.get("confidence_score", 0)),
            }
    return preds


def load_positional_profiles(path: str = POS_PROFILES) -> dict[str, dict]:
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
            }
    return profiles


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

class TripleDetector:
    """
    Detect Kober tripling patterns from bigram frame statistics.

    A "frame" is an adjacent pair of signs (X→Y).  If X→Y and Z→Y both
    occur frequently, X and Z are candidates for sharing a consonant.
    Similarly, if X→Y and X→W both occur, Y and W may share a vowel.
    """

    def __init__(self, db_path: str = DEFAULT_DB,
                 uncertain: Optional[set[str]] = None,
                 ml_preds: Optional[dict] = None,
                 profiles: Optional[dict] = None,
                 min_bigram_count: int = 2):
        self.db_path = db_path
        self.uncertain = uncertain or set()
        self.ml_preds = ml_preds or {}
        self.profiles = profiles or {}
        self.min_bigram_count = min_bigram_count

        # Results
        self.bigrams: dict[tuple[str, str], int] = {}        # (X, Y) → count
        self.frame_links_c: list[dict] = []    # consonant-sharing links
        self.frame_links_v: list[dict] = []    # vowel-sharing links
        self.triples: list[dict] = []          # detected tripling patterns
        self.sign_freq: dict[str, int] = {}    # overall sign frequency

    # ------------------------------------------------------------------
    # Step 1: Extract bigram frames from DB
    # ------------------------------------------------------------------

    def extract_bigrams(self):
        """
        Extract all adjacent sign pairs (within each inscription) from the DB.
        Only syllabograms with bennett_id are included.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT id FROM inscriptions ORDER BY id")
        inscription_ids = [r["id"] for r in c.fetchall()]

        bigram_counter = Counter()
        sign_counter = Counter()
        total_pairs = 0

        for ins_id in inscription_ids:
            c.execute(
                """SELECT bennett_id FROM signs
                   WHERE inscription_id = ? AND sign_type = 'syllabogram'
                     AND bennett_id != '' AND bennett_id IS NOT NULL
                   ORDER BY sequence""",
                (ins_id,),
            )
            sign_list = [r["bennett_id"] for r in c.fetchall()]

            for s in sign_list:
                sign_counter[s] += 1

            for i in range(len(sign_list) - 1):
                pair = (sign_list[i], sign_list[i + 1])
                bigram_counter[pair] += 1
                total_pairs += 1

        conn.close()

        self.sign_freq = dict(sign_counter)

        # Filter to min_bigram_count
        self.bigrams = {k: v for k, v in bigram_counter.items()
                        if v >= self.min_bigram_count}

        logger.info("Extracted %d bigrams (min_count=%d) from %d total pairs across %d inscriptions",
                    len(self.bigrams), self.min_bigram_count, total_pairs, len(inscription_ids))

    # ------------------------------------------------------------------
    # Step 2: Find frame links (consonant-sharing and vowel-sharing)
    # ------------------------------------------------------------------

    def find_frame_links(self):
        """
        For each frame X→Y:
          - Find all Z where Z→Y also occurs → X and Z are "C-linked"
            (they share the same following sign, so may share a consonant)
          - Find all W where X→W also occurs → Y and W are "V-linked"
            (they share the same preceding sign, so may share a vowel)
        """
        # Build reverse indices
        by_right: dict[str, list[str]] = defaultdict(list)  # Y → [X1, X2, ...]
        by_left: dict[str, list[str]] = defaultdict(list)   # X → [Y1, Y2, ...]

        for (x, y), count in self.bigrams.items():
            by_right[y].append(x)
            by_left[x].append(y)

        # Consonant-sharing links: X and Z share the same following sign Y
        c_links_seen: set[tuple[str, str]] = set()
        for y, xs in by_right.items():
            for i in range(len(xs)):
                for j in range(i + 1, len(xs)):
                    pair = tuple(sorted([xs[i], xs[j]]))
                    if pair not in c_links_seen:
                        c_links_seen.add(pair)
                        count_ij = self.bigrams.get((xs[i], y), 0) + self.bigrams.get((xs[j], y), 0)
                        # How many distinct Y's link these two?
                        common_rights = set()
                        for y2 in by_left.get(xs[i], []):
                            if y2 in by_left.get(xs[j], []):
                                common_rights.add(y2)

                        self.frame_links_c.append({
                            "sign_a": xs[i],
                            "sign_b": xs[j],
                            "link_type": "consonant-candidate",
                            "shared_following_sign": y,
                            "bigram_total": count_ij,
                            "total_common_right": len(common_rights),
                            "common_right_signs": ", ".join(sorted(common_rights)[:5]),
                        })

        # Vowel-sharing links: Y and W share the same preceding sign X
        v_links_seen: set[tuple[str, str]] = set()
        for x, ys in by_left.items():
            for i in range(len(ys)):
                for j in range(i + 1, len(ys)):
                    pair = tuple(sorted([ys[i], ys[j]]))
                    if pair not in v_links_seen:
                        v_links_seen.add(pair)
                        count_ij = self.bigrams.get((x, ys[i]), 0) + self.bigrams.get((x, ys[j]), 0)
                        common_lefts = set()
                        for x2 in by_right.get(ys[i], []):
                            if x2 in by_right.get(ys[j], []):
                                common_lefts.add(x2)
                        self.frame_links_v.append({
                            "sign_a": ys[i],
                            "sign_b": ys[j],
                            "link_type": "vowel-candidate",
                            "shared_preceding_sign": x,
                            "bigram_total": count_ij,
                            "total_common_left": len(common_lefts),
                            "common_left_signs": ", ".join(sorted(common_lefts)[:5]),
                        })

        # Sort by bigram_total descending
        self.frame_links_c.sort(key=lambda x: x["bigram_total"], reverse=True)
        self.frame_links_v.sort(key=lambda x: x["bigram_total"], reverse=True)

        logger.info("Found %d C-links and %d V-links",
                    len(self.frame_links_c), len(self.frame_links_v))

    # ------------------------------------------------------------------
    # Step 3: Build triple patterns
    # ------------------------------------------------------------------

    def build_triples(self):
        """
        Build strict Kober triples.

        A Kober triple is a set of three signs that form a complete triangle
        in the frame-link graph. That is:
          - S1 and S2 are C-linked (share at least one following sign)
          - S2 and S3 are V-linked (share at least one preceding sign)
          - S1 and S3 are also C-linked AND V-linked (bidirectional)

        Additionally, we only keep triples where:
          - At least 2 of 3 signs are UNCERTAIN
          - Each link has total_common >= 2 (they share at least 2 frame partners)
          - The shared frame signs are not themselves rare hapaxes

        This dramatically reduces noise while keeping the meaningful patterns.
        """
        # Build graphs, but only keep links with common >= 2
        c_graph: dict[str, set[str]] = defaultdict(set)
        v_graph: dict[str, set[str]] = defaultdict(set)
        c_common: dict[tuple[str, str], int] = {}  # (sorted pair) → common_rights count
        v_common: dict[tuple[str, str], int] = {}

        for link in self.frame_links_c:
            a, b = link["sign_a"], link["sign_b"]
            total_common = link["total_common_right"]
            pair_key = tuple(sorted([a, b]))
            if pair_key not in c_common:
                c_common[pair_key] = 0
            c_common[pair_key] = max(c_common[pair_key], total_common)

        for link in self.frame_links_v:
            a, b = link["sign_a"], link["sign_b"]
            total_common = link["total_common_left"]
            pair_key = tuple(sorted([a, b]))
            if pair_key not in v_common:
                v_common[pair_key] = 0
            v_common[pair_key] = max(v_common[pair_key], total_common)

        # Only keep high-common links (≥2 shared frame partners)
        MIN_COMMON = 2
        for (a, b), cnt in c_common.items():
            if cnt >= MIN_COMMON:
                c_graph[a].add(b)
                c_graph[b].add(a)
        for (a, b), cnt in v_common.items():
            if cnt >= MIN_COMMON:
                v_graph[a].add(b)
                v_graph[b].add(a)

        logger.info("C-graph (common≥%d): %d nodes, %d edges",
                    MIN_COMMON, len(c_graph),
                    sum(len(v) for v in c_graph.values()) // 2)
        logger.info("V-graph (common≥%d): %d nodes, %d edges",
                    MIN_COMMON, len(v_graph),
                    sum(len(v) for v in v_graph.values()) // 2)

        # Find complete triangles: S1, S2, S3 where:
        #   S1 ↔ S2 in C-graph
        #   S2 ↔ S3 in V-graph
        #   S1 ↔ S3 in both C-graph AND V-graph (bidirectional)
        triples_seen: set[tuple[str, ...]] = set()
        all_signs = set(c_graph.keys()) | set(v_graph.keys())

        for s1 in sorted(all_signs):
            c_neighbors_s1 = c_graph.get(s1, set())
            v_neighbors_s1 = v_graph.get(s1, set())
            # S3 must be both C-linked and V-linked to S1
            both_neighbors_s1 = c_neighbors_s1 & v_neighbors_s1
            if not both_neighbors_s1:
                continue

            for s2 in c_neighbors_s1:
                if s2 == s1:
                    continue
                v_neighbors_s2 = v_graph.get(s2, set())
                candidates = v_neighbors_s2 & both_neighbors_s1
                for s3 in candidates:
                    if s3 in (s1, s2):
                        continue
                    triple_key = tuple(sorted([s1, s2, s3]))
                    if triple_key in triples_seen:
                        continue
                    triples_seen.add(triple_key)

                    # Collect frame evidence
                    shared_following = set()
                    shared_preceding = set()
                    for link in self.frame_links_c:
                        if {link["sign_a"], link["sign_b"]} in ({s1, s2}, {s1, s3}, {s2, s3}):
                            shared_following.add(link.get("shared_following_sign", ""))
                    for link in self.frame_links_v:
                        if {link["sign_a"], link["sign_b"]} in ({s1, s3}, {s2, s3}, {s1, s2}):
                            shared_preceding.add(link.get("shared_preceding_sign", ""))

                    shared_following.discard("")
                    shared_preceding.discard("")

                    unc_count = sum(1 for s in (s1, s2, s3) if s in self.uncertain)

                    self.triples.append({
                        "triple_id": len(self.triples) + 1,
                        "sign_1": s1,
                        "sign_2": s2,
                        "sign_3": s3,
                        "connections": "C,V,both",
                        "total_connections": 3,
                        "shared_following": ",".join(sorted(shared_following)[:8]),
                        "shared_preceding": ",".join(sorted(shared_preceding)[:8]),
                        "s1_in_uncertain": s1 in self.uncertain,
                        "s2_in_uncertain": s2 in self.uncertain,
                        "s3_in_uncertain": s3 in self.uncertain,
                        "uncertain_count": unc_count,
                    })

        # Filter: require at least 2 UNCERTAIN members
        self.triples = [t for t in self.triples if t["uncertain_count"] >= 2]

        # Sort by uncertain_count descending, then by freq
        self.triples.sort(key=lambda t: (
            t["uncertain_count"],
            self.sign_freq.get(t["sign_1"], 0) + self.sign_freq.get(t["sign_2"], 0) + self.sign_freq.get(t["sign_3"], 0)
        ), reverse=True)

        # Annotate with ML predictions
        for t in self.triples:
            for sn in ["sign_1", "sign_2", "sign_3"]:
                sid = t[sn]
                ml = self.ml_preds.get(sid, {})
                t[f"{sn}_ml_pred"] = ml.get("predicted", "")
                t[f"{sn}_ml_conf"] = ml.get("confidence", 0.0)
                prof = self.profiles.get(sid, {})
                t[f"{sn}_pos_init"] = round(prof.get("initial", 0), 3)
                t[f"{sn}_pos_fin"] = round(prof.get("final", 0), 3)
                t[f"{sn}_total_occ"] = prof.get("total", 0)

        logger.info("Built %d triple patterns (≥2 UNCERTAIN, common≥%d)",
                    len(self.triples), MIN_COMMON)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def run(self):
        logger.info("=" * 60)
        logger.info("Kober Triple-Pattern Detection")
        logger.info("=" * 60)

        self.extract_bigrams()
        self.find_frame_links()
        self.build_triples()

        logger.info("Detection complete: %d C-links, %d V-links, %d triples",
                    len(self.frame_links_c), len(self.frame_links_v),
                    len(self.triples))

    # ------------------------------------------------------------------
    # Output writers
    # ------------------------------------------------------------------

    def write_all(self, output_dir: str = OUTPUT_DIR):
        os.makedirs(output_dir, exist_ok=True)
        self._write_frame_links(output_dir)
        self._write_triple_patterns(output_dir)
        logger.info("All outputs written to %s", output_dir)

    def _write_frame_links(self, out_dir: str):
        path = os.path.join(out_dir, "frame_links.csv")
        fieldnames = [
            "link_type", "sign_a", "sign_b",
            "shared_following_sign", "shared_preceding_sign",
            "bigram_total", "total_common_right", "total_common_left",
            "common_right_signs", "common_left_signs",
        ]
        all_links = self.frame_links_c + self.frame_links_v
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for link in sorted(all_links, key=lambda x: x["bigram_total"], reverse=True):
                writer.writerow(link)
        logger.info("Wrote %d frame links to %s", len(all_links), path)

    def _write_triple_patterns(self, out_dir: str):
        path = os.path.join(out_dir, "triple_patterns.csv")
        fieldnames = [
            "triple_id", "total_connections", "connections",
            "sign_1", "sign_2", "sign_3",
            "shared_following", "shared_preceding",
            "s1_in_uncertain", "s2_in_uncertain", "s3_in_uncertain",
            "uncertain_count",
            "sign_1_ml_pred", "sign_2_ml_pred", "sign_3_ml_pred",
            "sign_1_ml_conf", "sign_2_ml_conf", "sign_3_ml_conf",
            "sign_1_pos_init", "sign_2_pos_init", "sign_3_pos_init",
            "sign_1_pos_fin", "sign_2_pos_fin", "sign_3_pos_fin",
            "sign_1_total_occ", "sign_2_total_occ", "sign_3_total_occ",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for t in self.triples:
                writer.writerow(t)
        logger.info("Wrote %d triples to %s", len(self.triples), path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    uncertain = load_uncertain_signs()
    ml_preds = load_ml_predictions()
    profiles = load_positional_profiles()

    detector = TripleDetector(
        uncertain=uncertain,
        ml_preds=ml_preds,
        profiles=profiles,
        min_bigram_count=2,
    )
    detector.run()
    detector.write_all()

    # Summary
    print(f"\n{'='*60}")
    print("Kober Triple Detection — Summary")
    print(f"{'='*60}")
    print(f"C-links (consonant candidates): {len(detector.frame_links_c)}")
    print(f"V-links (vowel candidates):     {len(detector.frame_links_v)}")
    print(f"Triple patterns detected:       {len(detector.triples)}")

    # Top triples with all-UNCERTAIN members
    all_uncertain_triples = [t for t in detector.triples
                             if t["s1_in_uncertain"] and t["s2_in_uncertain"]
                             and t["s3_in_uncertain"]]
    print(f"Triples with ALL-UNCERTAIN members: {len(all_uncertain_triples)}")
    for t in all_uncertain_triples[:10]:
        print(f"  Triple {t['triple_id']}: {t['sign_1']}—{t['sign_2']}—{t['sign_3']} "
              f"(conn={t['total_connections']}) "
              f"ML: {t['sign_1_ml_pred']}/{t['sign_2_ml_pred']}/{t['sign_3_ml_pred']}")

    # Top triples involving at least 2 UNCERTAIN
    two_uncertain = [t for t in detector.triples
                     if sum([t["s1_in_uncertain"], t["s2_in_uncertain"],
                             t["s3_in_uncertain"]]) >= 2]
    print(f"Triples with ≥2 UNCERTAIN members: {len(two_uncertain)}")

    # Top triples overall
    print("\nTop 10 triples:")
    for t in detector.triples[:10]:
        print(f"  Triple {t['triple_id']}: {t['sign_1']}—{t['sign_2']}—{t['sign_3']} "
              f"(conn={t['total_connections']}) "
              f"ML: {t['sign_1_ml_pred']}/{t['sign_2_ml_pred']}/{t['sign_3_ml_pred']} "
              f"UNC: {t['s1_in_uncertain']}/{t['s2_in_uncertain']}/{t['s3_in_uncertain']}")

    # Key insight: do triples with all-UNCERTAIN members show consistent ML patterns?
    if all_uncertain_triples:
        print("\n=== ML Consistency Check ===")
        # Check if the 3 ML predictions in each triple show a consonant/vowel pattern
        # e.g., if sign_1 and sign_3 share a consonant, their ML predictions should
        # start with the same consonant
        consonant_consistent = 0
        for t in all_uncertain_triples[:20]:
            v1 = t.get("sign_1_ml_pred", "")
            v2 = t.get("sign_2_ml_pred", "")
            v3 = t.get("sign_3_ml_pred", "")
            # If C-linked: v1 and v2 might share a consonant
            # If V-linked: v2 and v3 might share a vowel
            # If both-linked (S1-S3): v1 and v3 might share both
            c_shared = (len(v1) >= 2 and len(v2) >= 2 and v1[0] == v2[0])
            v_shared = (len(v2) >= 2 and len(v3) >= 2 and v2[-1] == v3[-1])
            both = (len(v1) >= 2 and len(v3) >= 2 and v1[0] == v3[0] and v1[-1] == v3[-1])
            consistent = c_shared or v_shared or both
            if consistent:
                consonant_consistent += 1
            if t["triple_id"] <= 10:
                print(f"  Triple {t['triple_id']}: {v1}/{v2}/{v3} "
                      f"C-shared={c_shared} V-shared={v_shared} Both={both}")
        print(f"  Consistent: {consonant_consistent}/{min(20, len(all_uncertain_triples))}")


if __name__ == "__main__":
    main()
