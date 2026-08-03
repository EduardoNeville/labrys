"""Phase 9 — Formulaic Parallelism Decipherment

Exploits repeated variant sequences across the Linear A corpus where
a single sign substitution encodes morphological or phonetic alternation.
This is a mini parallel corpus within Linear A itself — no external
language assumptions needed.

Method:
1. Find all n-gram sequences (length 2-6) repeated across inscriptions
2. Identify variant pairs: sequences differing by exactly 1 sign
3. Classify each substitution as MORPHOLOGICAL (prefix/suffix position,
   different phonetic class) or PHONETIC (medial position, same class)
4. For PHONETIC substitutions, the two signs share either a consonant
   or a vowel — this constrains the grid
5. For MORPHOLOGICAL substitutions, we learn grammatical patterns

Usage:
    uv run python pipeline/formulaic/analyze.py
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict
import sqlite3

logger = logging.getLogger(__name__)

__all__ = [
    "FormulaicAnalyzer",
    "Substitution",
    "run_formulaic_analysis",
]

# ── phonetic class mapping ──────────────────────────────────────────────

COARSE = {
    "a": 0, "i": 0, "o": 0, "u": 0, "e": 0,
    "pa": 1, "pi": 1, "me": 1, "mi": 1, "mo": 1, "wa": 1, "wi": 1,
    "te": 2, "ti": 2, "to": 2, "tu": 2,
    "na": 2, "ne": 2, "ni": 2, "nu": 2,
    "sa": 2, "se": 2, "si": 2, "so": 2,
    "za": 2, "ze": 2, "zo": 2,
    "re": 2, "ri": 2, "ru": 2, "ra": 2, "la": 2, "ro": 2,
    "ja": 3, "ka": 3, "ke": 3, "ki": 3, "ko": 3, "ku": 3,
    "ta": 2, "da": 2, "di": 2, "do": 2, "du": 2,
    "ju": 3, "jo": 3, "nu": 2, "mi": 1, "mu": 2,
    "pi": 1, "pu": 2, "qi": 3, "qa": 3,
    "si": 2, "su": 2, "so": 2, "se": 2,
    "ti": 2, "to": 2, "te": 2,
    "wi": 1, "wo": 1, "we": 1,
}

COARSE_NAMES = {0: "vowel", 1: "labial", 2: "dental/coronal", 3: "velar/palatal"}

def coarse_of(val: str) -> int:
    v = val.strip().lower()
    return COARSE.get(v, -1)

# Vowel extraction from CV sign
VOWEL_MAP = {"a": "a", "i": "i", "o": "o", "u": "u", "e": "e"}
def vowel_of(val: str) -> str:
    """Extract vowel from CV value, or return the value if monophthong."""
    v = val.strip().lower()
    if len(v) == 1 and v in VOWEL_MAP:
        return v
    if len(v) == 2:
        return v[1] if v[1] in VOWEL_MAP else v[0]
    return v[-1] if v[-1] in VOWEL_MAP else "?"


# ── data structures ─────────────────────────────────────────────────────

class Substitution:
    """A single-sign substitution found in parallel formulaic context."""
    __slots__ = (
        "sign_a", "sign_b", "position", "ngram_len",
        "frame_before", "frame_after",
        "count_a", "count_b",
        "class_a", "class_b", "vowel_a", "vowel_b",
        "sub_type",  # "phonetic", "morphological", "unknown"
        "inference",  # human-readable inference
        "confidence",
    )

    def __init__(self):
        self.sign_a = ""
        self.sign_b = ""
        self.position = 0
        self.ngram_len = 0
        self.frame_before = []  # signs before substitution position
        self.frame_after = []   # signs after
        self.count_a = 0
        self.count_b = 0
        self.class_a = -1
        self.class_b = -1
        self.vowel_a = "?"
        self.vowel_b = "?"
        self.sub_type = "unknown"
        self.inference = ""
        self.confidence = 0.0


# ── analyzer ────────────────────────────────────────────────────────────

class FormulaicAnalyzer:
    """Analyze formulaic parallelism in the Linear A corpus."""

    def __init__(self, db_path: str = "data/database/lineara_full.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

        # Load grid values
        self.grid: Dict[str, Dict] = {}
        with open("data/analysis/comparative/refined_phonetic_grid.csv",
                  newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.grid[row["bennett_id"]] = row

        # Load Phase 8 expanded values
        self.expanded: Dict[str, Dict] = {}
        try:
            with open("data/analysis/bootstrapping/expanded_grid.csv",
                      newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.expanded[row["bennett_id"]] = row
        except FileNotFoundError:
            pass

    def sign_value(self, bid: str) -> str:
        """Best available phonetic value for a Bennett ID."""
        if bid in self.expanded:
            v = self.expanded[bid].get("refined_value", "")
            if v and v != "?":
                return v
        g = self.grid.get(bid, {})
        return g.get("conventional_value", "?")

    def load_inscriptions(self) -> Dict[int, List[str]]:
        """Return {inscription_id: [bennett_id, ...]}."""
        self.c.execute("""
            SELECT i.id, s.sequence, s.bennett_id
            FROM signs s JOIN inscriptions i ON s.inscription_id = i.id
            WHERE s.bennett_id != ''
            ORDER BY i.id, s.sequence
        """)
        inscriptions: Dict[int, List[str]] = defaultdict(list)
        for row in self.c.fetchall():
            inscriptions[row["id"]].append(row["bennett_id"])
        logger.info("Loaded %d inscriptions", len(inscriptions))
        return dict(inscriptions)

    def find_variant_pairs(
        self,
        inscriptions: Dict[int, List[str]],
        min_len: int = 3,
        max_len: int = 5,
        min_freq: int = 2,
    ) -> List[Substitution]:
        """Find all single-sign substitution pairs in repeated sequences."""
        # Build n-gram index
        ngram_index: Dict[int, Dict[Tuple, List[int]]] = defaultdict(lambda: defaultdict(list))
        for n in range(min_len, max_len + 1):
            for ins_id, signs in inscriptions.items():
                for i in range(len(signs) - n + 1):
                    ngram = tuple(signs[i:i+n])
                    ngram_index[n][ngram].append(ins_id)

        substitutions: List[Substitution] = []

        for n in range(min_len, max_len + 1):
            ngrams = ngram_index[n]
            ngram_list = list(ngrams.keys())

            for i, a in enumerate(ngram_list):
                count_a = len(ngrams[a])
                for j, b in enumerate(ngram_list):
                    if i >= j:
                        continue
                    count_b = len(ngrams[b])

                    # Count differences
                    diffs = [(k, p, q) for k, (p, q) in enumerate(zip(a, b)) if p != q]
                    if len(diffs) != 1:
                        continue

                    pos, sign_a, sign_b = diffs[0]

                    # Build shared frame
                    frame_before = list(a[:pos])
                    frame_after = list(a[pos+1:])

                    sub = Substitution()
                    sub.sign_a = sign_a
                    sub.sign_b = sign_b
                    sub.position = pos
                    sub.ngram_len = n
                    sub.frame_before = frame_before
                    sub.frame_after = frame_after
                    sub.count_a = count_a
                    sub.count_b = count_b

                    # Phonetic classification
                    val_a = self.sign_value(sign_a)
                    val_b = self.sign_value(sign_b)
                    sub.class_a = coarse_of(val_a)
                    sub.class_b = coarse_of(val_b)
                    sub.vowel_a = vowel_of(val_a)
                    sub.vowel_b = vowel_of(val_b)

                    # Classify substitution type
                    is_boundary = (pos == 0) or (pos == n - 1)
                    same_class = (sub.class_a >= 0 and sub.class_b >= 0 and
                                  sub.class_a == sub.class_b)

                    if is_boundary and not same_class:
                        sub.sub_type = "morphological"
                        sub.inference = f"prefix/suffix substitution: {sign_a}({val_a}) ↔ {sign_b}({val_b})"
                    elif not is_boundary and same_class:
                        sub.sub_type = "phonetic"
                        if sub.vowel_a != "?" and sub.vowel_b != "?" and sub.vowel_a == sub.vowel_b:
                            sub.inference = f"same vowel /{sub.vowel_a}/, different consonant: {sign_a}({val_a}) ↔ {sign_b}({val_b})"
                            sub.confidence = 0.7
                        elif sub.vowel_a != "?" and sub.vowel_b != "?":
                            sub.inference = f"same class ({COARSE_NAMES.get(sub.class_a, '?')}), different vowel: {sign_a}({val_a}) ↔ {sign_b}({val_b})"
                            sub.confidence = 0.5
                        else:
                            sub.inference = f"same class, consonant/vowel uncertain: {sign_a}({val_a}) ↔ {sign_b}({val_b})"
                            sub.confidence = 0.3
                    else:
                        sub.sub_type = "unknown"
                        sub.inference = f"unclassified: {sign_a}({val_a}) ↔ {sign_b}({val_b})"

                    substitutions.append(sub)

        # Sort by total frequency (higher = more formulaic)
        substitutions.sort(key=lambda s: s.count_a + s.count_b, reverse=True)
        logger.info("Found %d substitution pairs", len(substitutions))
        return substitutions

    def generate_grid_constraints(
        self,
        substitutions: List[Substitution],
    ) -> List[Dict]:
        """Extract grid constraint implications from phonetic substitutions."""
        constraints = []

        for sub in substitutions:
            if sub.sub_type != "phonetic":
                continue

            val_a = self.sign_value(sub.sign_a)
            val_b = self.sign_value(sub.sign_b)

            # If same vowel, infer same row (consonant series)
            if sub.vowel_a != "?" and sub.vowel_b != "?" and sub.vowel_a == sub.vowel_b:
                constraints.append({
                    "type": "shared_vowel",
                    "sign_a": sub.sign_a,
                    "sign_b": sub.sign_b,
                    "vowel": sub.vowel_a,
                    "evidence": f"substitute in same frame at pos {sub.position}",
                    "frequency": sub.count_a + sub.count_b,
                    "confidence": 0.7,
                })

            # If same class but different vowel, infer same column
            if (sub.class_a >= 0 and sub.class_b >= 0 and
                sub.class_a == sub.class_b and
                sub.vowel_a != sub.vowel_b):
                constraints.append({
                    "type": "shared_consonant_series",
                    "sign_a": sub.sign_a,
                    "sign_b": sub.sign_b,
                    "class": COARSE_NAMES.get(sub.class_a, "?"),
                    "evidence": f"substitute in same frame at pos {sub.position}",
                    "frequency": sub.count_a + sub.count_b,
                    "confidence": 0.5,
                })

        return constraints

    def analyze(self) -> Tuple[List[Substitution], List[Dict], Dict]:
        """Run full formulaic parallelism analysis."""
        inscriptions = self.load_inscriptions()
        substitutions = self.find_variant_pairs(inscriptions)
        constraints = self.generate_grid_constraints(substitutions)

        # Summary stats
        phonetic_subs = [s for s in substitutions if s.sub_type == "phonetic"]
        morph_subs = [s for s in substitutions if s.sub_type == "morphological"]

        summary = {
            "total_substitutions": len(substitutions),
            "phonetic_substitutions": len(phonetic_subs),
            "morphological_substitutions": len(morph_subs),
            "grid_constraints": len(constraints),
            "signs_involved": len(set(s.sign_a for s in substitutions) | set(s.sign_b for s in substitutions)),
        }

        logger.info("Analysis complete: %s", summary)
        return substitutions, constraints, summary

    def close(self) -> None:
        self.conn.close()


# ── main harness ─────────────────────────────────────────────────────────

def run_formulaic_analysis(
    db_path: str = "data/database/lineara_full.db",
    output_dir: str = "data/analysis/formulaic",
) -> Dict:
    """Run full Phase 9 analysis and write outputs."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    analyzer = FormulaicAnalyzer(db_path=db_path)
    substitutions, constraints, summary = analyzer.analyze()

    # Write substitutions CSV
    sub_path = out / "substitutions.csv"
    with open(sub_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sign_a", "sign_b", "position", "ngram_len",
            "class_a", "class_b", "vowel_a", "vowel_b",
            "count_a", "count_b", "sub_type", "inference", "confidence",
            "frame",
        ])
        writer.writeheader()
        for s in substitutions:
            frame = "-".join(
                list(s.frame_before) + [f"[{s.sign_a}|{s.sign_b}]"] + list(s.frame_after)
            )
            writer.writerow({
                "sign_a": s.sign_a,
                "sign_b": s.sign_b,
                "position": s.position,
                "ngram_len": s.ngram_len,
                "class_a": COARSE_NAMES.get(s.class_a, "?"),
                "class_b": COARSE_NAMES.get(s.class_b, "?"),
                "vowel_a": s.vowel_a,
                "vowel_b": s.vowel_b,
                "count_a": s.count_a,
                "count_b": s.count_b,
                "sub_type": s.sub_type,
                "inference": s.inference,
                "confidence": s.confidence,
                "frame": frame,
            })

    # Write constraints CSV
    if constraints:
        cons_path = out / "grid_constraints.csv"
        fieldnames = ["type", "sign_a", "sign_b", "vowel", "class", "evidence", "frequency", "confidence"]
        with open(cons_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(constraints)

    # Write report
    phonetic_subs = [s for s in substitutions if s.sub_type == "phonetic"]
    morph_subs = [s for s in substitutions if s.sub_type == "morphological"]

    # Key findings
    key_constraints = sorted(constraints, key=lambda c: c["frequency"], reverse=True)[:20]

    # Best inferences: phonetic substitutions with clear vowels
    strong_phonetic = sorted(
        [s for s in phonetic_subs if s.confidence >= 0.5],
        key=lambda s: s.count_a + s.count_b, reverse=True
    )

    report_lines = [
        "# Phase 9 — Formulaic Parallelism Report",
        "",
        f"**Total substitutions found:** {summary['total_substitutions']}",
        f"**Phonetic substitutions:** {summary['phonetic_substitutions']}",
        f"**Morphological substitutions:** {summary['morphological_substitutions']}",
        f"**Grid constraints generated:** {summary['grid_constraints']}",
        f"**Unique signs involved:** {summary['signs_involved']}",
        "",
        "## Key Morphological Patterns",
        "",
    ]

    # Group morphological subs by position
    by_pos = defaultdict(list)
    for s in morph_subs:
        by_pos[s.position].append(s)

    for pos in sorted(by_pos.keys()):
        subs = sorted(by_pos[pos], key=lambda s: s.count_a + s.count_b, reverse=True)[:8]
        pos_label = "PREFIX (pos 0)" if pos == 0 else f"SUFFIX (pos {pos})" if pos >= 3 else f"pos {pos}"
        report_lines.append(f"### {pos_label}")
        report_lines.append("")
        for s in subs:
            val_a = analyzer.sign_value(s.sign_a)
            val_b = analyzer.sign_value(s.sign_b)
            report_lines.append(
                f"- **{s.sign_a}** (`/{val_a}/`) ↔ **{s.sign_b}** (`/{val_b}/`) "
                f"— appeared {s.count_a}x / {s.count_b}x in frame: "
                f"`{'-'.join(s.frame_before)}-[X]-{'-'.join(s.frame_after)}`"
            )
        report_lines.append("")

    report_lines += [
        "## Key Phonetic Constraints",
        "",
    ]
    for s in strong_phonetic[:20]:
        val_a = analyzer.sign_value(s.sign_a)
        val_b = analyzer.sign_value(s.sign_b)
        report_lines.append(
            f"- **{s.sign_a}** ↔ **{s.sign_b}**: {s.inference} "
            f"(freq={s.count_a + s.count_b}, conf={s.confidence:.2f})"
        )

    report_lines += [
        "",
        "## Grid Implications",
        "",
        "From the strongest shared-vowel substitutions:",
        "",
    ]

    shared_vowel = [c for c in constraints if c["type"] == "shared_vowel"]
    shared_vowel.sort(key=lambda c: c["frequency"], reverse=True)

    seen_pairs = set()
    for c in shared_vowel[:15]:
        pair = tuple(sorted([c["sign_a"], c["sign_b"]]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        report_lines.append(
            f"- **{c['sign_a']}** and **{c['sign_b']}** share vowel `/{c['vowel']}/` "
            f"(evidence: {c['evidence']}, freq={c['frequency']})"
        )

    report_lines += [
        "",
        "## Newly Constrainable Signs",
        "",
    ]

    # Signs that gained new constraints
    constrained_signs = set()
    for s in strong_phonetic:
        val_a = analyzer.sign_value(s.sign_a)
        val_b = analyzer.sign_value(s.sign_b)
        g_a = analyzer.grid.get(s.sign_a, {})
        g_b = analyzer.grid.get(s.sign_b, {})

        if g_a.get("decision") == "UNCERTAIN" and val_a != "?":
            constrained_signs.add((s.sign_a, val_a, s))
        if g_b.get("decision") == "UNCERTAIN" and val_b != "?":
            constrained_signs.add((s.sign_b, val_b, s))

    for bid, val, sub in sorted(constrained_signs, key=lambda x: x[0]):
        report_lines.append(
            f"- **{bid}** (`/{val}/`): newly constrained by substitution "
            f"with known sign (conf={sub.confidence:.2f})"
        )

    report_lines += [
        "",
        "## Limitations",
        "",
        "- Substitutions at position 0 (prefix) may be morphological, not phonetic — vowel sharing inference is weaker for prefixes",
        "- Single-occurrence variants (count=1) have low statistical confidence",
        "- Signs with unknown values (? ) on both sides of a substitution produce no constraint",
        "- This method cannot constrain AB 60 (appears only once in multi-sign context)",
        "",
        "---",
        "",
        "*Phase 9 — Formulaic Parallelism. Built from repeated variant sequences within the Linear A corpus itself.*",
    ]

    report_path = out / "formulaic_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    analyzer.close()

    logger.info("Phase 9 complete: %s, %s", sub_path, report_path)
    return summary


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_formulaic_analysis()
