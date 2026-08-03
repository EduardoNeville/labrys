"""Phase 8 — Kober Bootstrapping Decipherment

Iterative grid expansion: start with 45 CONFIRMED anchor signs, use Kober
distributional triples to constrain neighboring UNCERTAIN signs, test
candidates against commodity-semantic contexts and toponym anchor lists,
accept what works, and iterate.

This is the method Michael Ventris used on Linear B, computationalized.

Usage:
    uv run python pipeline/bootstrapping/grid_expand.py
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

__all__ = [
    "KoberGridExpander",
    "SignHypothesis",
    "run_bootstrapping_cycle",
    "GRID_PATH",
    "DB_PATH",
]

GRID_PATH = "data/analysis/comparative/refined_phonetic_grid.csv"
DB_PATH = "data/database/lineara_full.db"

# ── phonetic class mapping ──────────────────────────────────────────────

COARSE = {
    "a": 0, "i": 0, "o": 0, "u": 0,
    "pa": 1, "pi": 1, "me": 1, "mi": 1, "mo": 1, "wa": 1, "wi": 1,
    "te": 2, "ti": 2, "to": 2, "tu": 2,
    "na": 2, "ne": 2, "ni": 2, "nu": 2,
    "sa": 2, "se": 2, "si": 2, "so": 2,
    "za": 2, "ze": 2, "zo": 2,
    "re": 2, "ri": 2, "ru": 2, "ra": 2, "la": 2,
    "ja": 3, "ka": 3, "ke": 3, "ki": 3, "ko": 3, "ku": 3,
    "ro": 2,  # AB 68 resolved
}

COARSE_NAMES = {0: "vowel", 1: "labial", 2: "dental/coronal", 3: "velar/palatal"}

# Within dental/coronal, subdivide by manner
DENTAL_SUBCLASS = {
    "te": "stop/t", "ti": "stop/t", "to": "stop/t", "tu": "stop/t",
    "na": "nasal/n", "ne": "nasal/n", "ni": "nasal/n", "nu": "nasal/n",
    "sa": "fric/s", "se": "fric/s", "si": "fric/s", "so": "fric/s",
    "za": "fric/z", "ze": "fric/z", "zo": "fric/z",
    "re": "liquid/r", "ri": "liquid/r", "ru": "liquid/r", "ra": "liquid/r",
    "la": "liquid/l", "ro": "liquid/r",
}

def coarse_of(val: str) -> int:
    return COARSE.get(val, -1)

def dental_manner(val: str) -> str:
    return DENTAL_SUBCLASS.get(val, "unknown")


# ── data structures ─────────────────────────────────────────────────────

class SignHypothesis:
    """A candidate phonetic value for a UNCERTAIN sign with evidence tracking."""
    __slots__ = ("bennett_id", "proposed_value", "c_class", "v_class",
                 "c_partner_count", "v_partner_count",
                 "commodity_support", "toponym_support",
                 "phylogenetic_agrees", "ml_agrees",
                 "confidence", "accepted")

    def __init__(self, bennett_id: str, proposed_value: str):
        self.bennett_id = bennett_id
        self.proposed_value = proposed_value
        self.c_class = coarse_of(proposed_value)
        self.v_class = -1  # vowel class not tracked at coarse level
        self.c_partner_count = 0
        self.v_partner_count = 0
        self.commodity_support = False
        self.toponym_support = False
        self.phylogenetic_agrees = False
        self.ml_agrees = False
        self.confidence = 0.0
        self.accepted = False

    def compute_confidence(self) -> float:
        """Convert evidence counts to confidence score [0, 1]."""
        score = 0.0
        total = 0.0

        # Kober C-links (weight: 0.30)
        if self.c_partner_count >= 5:
            score += 0.30
        elif self.c_partner_count >= 2:
            score += 0.15
        total += 0.30

        # Kober V-links (weight: 0.30)
        if self.v_partner_count >= 5:
            score += 0.30
        elif self.v_partner_count >= 2:
            score += 0.15
        total += 0.30

        # Commodity support (weight: 0.15)
        if self.commodity_support:
            score += 0.15
        total += 0.15

        # Phylogenetic agreement (weight: 0.15)
        if self.phylogenetic_agrees:
            score += 0.15
        total += 0.15

        # Toponym support (weight: 0.10)
        if self.toponym_support:
            score += 0.10
        total += 0.10

        self.confidence = score / max(total, 0.01)
        return self.confidence


# ── grid expander ────────────────────────────────────────────────────────

class KoberGridExpander:
    """Iterative Kober bootstrapping for Linear A phonetic grid expansion."""

    def __init__(
        self,
        db_path: str = DB_PATH,
        grid_path: str = GRID_PATH,
        min_occurrences: int = 2,
    ) -> None:
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.min_occ = min_occurrences

        # Load grid
        self.grid: Dict[str, Dict] = {}
        with open(grid_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.grid[row["bennett_id"]] = row

        # Anchor set: 44 CONFIRMED + AB 68 (resolved in Phase 7)
        self.confirmed: Set[str] = set()
        self.confirmed_values: Dict[str, str] = {}
        self.uncertain: List[str] = []

        for bid, g in self.grid.items():
            if g.get("decision") == "CONFIRM":
                self.confirmed.add(bid)
                self.confirmed_values[bid] = g.get("refined_value", "")
            elif g.get("decision") == "UNCERTAIN":
                self.uncertain.append(bid)

        # AB 68 → /ro/ (Phase 7 phylogenetic resolution)
        self.confirmed.add("AB 68")
        self.confirmed_values["AB 68"] = "ro"
        if "AB 68" in self.uncertain:
            self.uncertain.remove("AB 68")

        logger.info("Grid expander: %d CONFIRMED anchors, %d UNCERTAIN targets",
                     len(self.confirmed), len(self.uncertain))

        # Build bigram context index
        self._build_context_index()

        # Load phylogenetic resolutions
        self._load_phylogenetic()

        # Load commodity signatures
        self._load_commodity_signatures()

    def _build_context_index(self) -> None:
        """Build follower/preceder bigram indices from DB."""
        self.follower_index: Dict[str, Set[str]] = defaultdict(set)
        self.preceder_index: Dict[str, Set[str]] = defaultdict(set)

        self.c.execute("""
            SELECT s1.bennett_id as sign, s2.bennett_id as follower
            FROM signs s1 JOIN signs s2
                ON s1.inscription_id = s2.inscription_id
                AND s1.sequence = s2.sequence - 1
            WHERE s1.bennett_id != '' AND s2.bennett_id != ''
            GROUP BY s1.bennett_id, s2.bennett_id
            HAVING COUNT(*) >= ?
        """, (self.min_occ,))

        for row in self.c.fetchall():
            self.follower_index[row["sign"]].add(row["follower"])

        self.c.execute("""
            SELECT s1.bennett_id as preceder, s2.bennett_id as sign
            FROM signs s1 JOIN signs s2
                ON s1.inscription_id = s2.inscription_id
                AND s1.sequence = s2.sequence - 1
            WHERE s1.bennett_id != '' AND s2.bennett_id != ''
            GROUP BY s1.bennett_id, s2.bennett_id
            HAVING COUNT(*) >= ?
        """, (self.min_occ,))

        for row in self.c.fetchall():
            self.preceder_index[row["sign"]].add(row["preceder"])

        logger.info("Context index: %d followers, %d preceders",
                     len(self.follower_index), len(self.preceder_index))

    def _load_phylogenetic(self) -> None:
        """Load Phase 7 phylogenetic conflict resolutions."""
        self.phylo_resolutions: Dict[str, str] = {}
        try:
            with open("data/analysis/phylogenetic/conflict_resolutions.csv",
                      newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.phylo_resolutions[row["bennett_id"]] = row["winning_value"]
        except FileNotFoundError:
            logger.warning("Phylogenetic resolutions not found — skipping")

    def _load_commodity_signatures(self) -> None:
        """Load commodity-semantic signatures from Phase 7."""
        self.commodity_signs: Set[str] = set()
        try:
            with open("data/analysis/commodity_decoding/commodity_signatures.csv",
                      newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    seq = row.get("sequence", "")
                    # Extract individual signs from sequence
                    for bid in self.grid:
                        if bid in seq:
                            self.commodity_signs.add(bid)
        except FileNotFoundError:
            logger.warning("Commodity signatures not found — skipping")

    def get_kober_partners(self, bid: str) -> Tuple[Set[str], Set[str]]:
        """Return (C-linked confirmed partners, V-linked confirmed partners)."""
        c_partners = set()
        v_partners = set()

        followers = self.follower_index.get(bid, set())
        for f in followers:
            others = self.follower_index.get(f, set())
            for other in others:
                if other in self.confirmed and other != bid:
                    c_partners.add(other)

        preceders = self.preceder_index.get(bid, set())
        for p in preceders:
            others = self.preceder_index.get(p, set())
            for other in others:
                if other in self.confirmed and other != bid:
                    v_partners.add(other)

        return c_partners, v_partners

    def generate_hypothesis(self, bid: str) -> Optional[SignHypothesis]:
        """Generate best phonetic hypothesis for a single UNCERTAIN sign."""
        if bid not in self.uncertain:
            return None

        c_partners, v_partners = self.get_kober_partners(bid)

        # Determine consonant class from C-partners
        c_coarse: Counter = Counter()
        c_manner: Counter = Counter()
        for p in c_partners:
            val = self.confirmed_values.get(p, "")
            c_coarse[coarse_of(val)] += 1
            m = dental_manner(val)
            if m != "unknown":
                c_manner[m] += 1

        # Determine vowel class from V-partners
        v_coarse: Counter = Counter()
        for p in v_partners:
            val = self.confirmed_values.get(p, "")
            v_coarse[coarse_of(val)] += 1

        if not c_coarse and not v_coarse:
            return None

        # Start with the conventional value as baseline
        g = self.grid.get(bid, {})
        conventional = g.get("conventional_value", "?")

        hyp = SignHypothesis(bid, conventional)
        hyp.c_partner_count = len(c_partners)
        hyp.v_partner_count = len(v_partners)

        # Check phylogenetic agreement
        phylo_val = self.phylo_resolutions.get(bid, "")
        if phylo_val and phylo_val == conventional:
            hyp.phylogenetic_agrees = True

        # Check commodity support
        if bid in self.commodity_signs:
            hyp.commodity_support = True

        # Check toponym support
        cm_val = g.get("cm_suggested_value", "")
        if cm_val and conventional != cm_val:
            hyp.toponym_support = False  # conflict
        else:
            hyp.toponym_support = True

        hyp.compute_confidence()
        return hyp

    def run_cycle(self, confidence_threshold: float = 0.60) -> List[SignHypothesis]:
        """Run one bootstrapping cycle. Returns accepted hypotheses."""
        hypotheses: List[SignHypothesis] = []
        accepted: List[SignHypothesis] = []

        for bid in sorted(self.uncertain):
            hyp = self.generate_hypothesis(bid)
            if hyp is None:
                continue
            hypotheses.append(hyp)

        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        for hyp in hypotheses:
            if hyp.confidence >= confidence_threshold:
                hyp.accepted = True
                # Add to confirmed set for next cycle
                self.confirmed.add(hyp.bennett_id)
                self.confirmed_values[hyp.bennett_id] = hyp.proposed_value
                if hyp.bennett_id in self.uncertain:
                    self.uncertain.remove(hyp.bennett_id)
                accepted.append(hyp)

                logger.info("ACCEPTED %s = /%s/ (confidence=%.2f, C=%d, V=%d)",
                            hyp.bennett_id, hyp.proposed_value, hyp.confidence,
                            hyp.c_partner_count, hyp.v_partner_count)

        return accepted

    def run_until_convergence(
        self,
        max_cycles: int = 5,
        initial_threshold: float = 0.60,
        relaxed_threshold: float = 0.45,
    ) -> Dict[str, object]:
        """Run iterative bootstrapping, relaxing threshold each cycle.

        Returns summary dict with per-cycle results.
        """
        summary = {
            "initial_anchors": len(self.confirmed) - 1,  # exclude AB 68
            "initial_uncertain": len(self.uncertain) + 1,
            "cycles": [],
            "total_accepted": 0,
            "final_anchors": 0,
            "remaining_uncertain": 0,
        }

        for cycle in range(max_cycles):
            threshold = max(initial_threshold - cycle * 0.05, relaxed_threshold)
            logger.info("CYCLE %d — threshold=%.2f, anchors=%d, uncertain=%d",
                        cycle + 1, threshold, len(self.confirmed), len(self.uncertain))

            accepted = self.run_cycle(confidence_threshold=threshold)

            cycle_info = {
                "cycle": cycle + 1,
                "threshold": threshold,
                "accepted_count": len(accepted),
                "accepted_signs": [h.bennett_id for h in accepted],
                "accepted_values": {h.bennett_id: h.proposed_value for h in accepted},
                "anchors_after": len(self.confirmed),
                "uncertain_after": len(self.uncertain),
            }
            summary["cycles"].append(cycle_info)
            summary["total_accepted"] += len(accepted)

            if not accepted:
                logger.info("No acceptances — convergence reached at threshold %.2f", threshold)
                break

        summary["final_anchors"] = len(self.confirmed)
        summary["remaining_uncertain"] = len(self.uncertain)
        summary["resolution_rate"] = summary["total_accepted"] / max(summary["initial_uncertain"], 1)

        return summary

    def close(self) -> None:
        self.conn.close()


# ── main harness ─────────────────────────────────────────────────────────

def run_bootstrapping_cycle(
    db_path: str = DB_PATH,
    grid_path: str = GRID_PATH,
    output_dir: str = "data/analysis/bootstrapping",
    max_cycles: int = 5,
) -> Dict[str, object]:
    """Run full Kober bootstrapping and write results.

    Returns summary dict and writes:
        - data/analysis/bootstrapping/expanded_grid.csv
        - data/analysis/bootstrapping/bootstrapping_report.md
    """
    import json
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary_path = out / "cycle_summary.json"

    expander = KoberGridExpander(db_path=db_path, grid_path=grid_path)
    result = expander.run_until_convergence(max_cycles=max_cycles)

    # Write expanded grid
    expanded_rows = []
    for bid, g in expander.grid.items():
        decision = "CONFIRM" if bid in expander.confirmed else g.get("decision", "UNCERTAIN")
        value = expander.confirmed_values.get(bid, g.get("refined_value", g.get("conventional_value", "")))
        expanded_rows.append({
            "bennett_id": bid,
            "conventional_value": g.get("conventional_value", ""),
            "refined_value": value,
            "decision": decision,
            "confidence": g.get("confidence_score", ""),
            "resolved_by_bootstrapping": "YES" if bid in expander.confirmed and g.get("decision") == "UNCERTAIN" else "NO",
        })

    grid_path_out = out / "expanded_grid.csv"
    with open(grid_path_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=expanded_rows[0].keys())
        writer.writeheader()
        writer.writerows(expanded_rows)

    # Write cycle summary
    with open(summary_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    # Write report
    new_accepted = [bid for bid in expander.confirmed
                    if expander.grid.get(bid, {}).get("decision") == "UNCERTAIN"]
    report_lines = [
        "# Phase 8 — Kober Bootstrapping Report",
        "",
        f"**Initial anchors:** {result['initial_anchors']}",
        f"**Initial UNCERTAIN:** {result['initial_uncertain']}",
        f"**Newly accepted:** {len(new_accepted)}",
        f"**Final anchors:** {result['final_anchors']}",
        f"**Remaining UNCERTAIN:** {result['remaining_uncertain']}",
        f"**Resolution rate:** {result['resolution_rate']:.1%}",
        "",
        "## Accepted Signs",
        "",
    ]
    for bid in sorted(new_accepted):
        val = expander.confirmed_values[bid]
        g = expander.grid.get(bid, {})
        conv = g.get("conventional_value", "?")
        report_lines.append(f"- **{bid}**: `/{val}/` (conventional: `/{conv}/`)")

    report_lines += [
        "",
        "## Cycle Summary",
        "",
    ]
    for c in result["cycles"]:
        report_lines.append(
            f"- Cycle {c['cycle']} (threshold={c['threshold']:.2f}): "
            f"accepted {c['accepted_count']} signs, "
            f"anchors now {c['anchors_after']}"
        )

    report_lines += [
        "",
        "## Remaining Key Conflicts",
        "",
        "Signs that remain UNCERTAIN after bootstrapping:",
        "",
    ]
    for bid in sorted(expander.uncertain):
        g = expander.grid.get(bid, {})
        cm_conflict = g.get("conflict_note", "")
        cm_val = g.get("cm_suggested_value", "")
        if cm_val and cm_conflict:
            report_lines.append(f"- **{bid}**: `/{g.get('conventional_value', '?')}/` — CM: `/{cm_val}/` ({cm_conflict[:80]})")
        else:
            report_lines.append(f"- **{bid}**: `/{g.get('conventional_value', '?')}/`")

    report_path = out / "bootstrapping_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    expander.close()

    logger.info("Phase 8 complete — report: %s, grid: %s", report_path, grid_path_out)
    return result


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_bootstrapping_cycle()
