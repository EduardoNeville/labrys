#!/usr/bin/env python3
"""
frequency_profile.py — Compute frequency distribution of syllabograms and
establish expected frequency ranges per consonant class and vowel row.

Inputs:
  - data/database/lineara_full.db (signs table)
  - data/analysis/bootstrapping/expanded_grid.csv

Outputs:
  - data/analysis/frequency_constraints/frequency_profile.csv

Method:
  For all 138 syllabograms with corpus frequency from the DB, group CONFIRMED
  signs by consonant class and vowel row. Compute: mean, std, min, max,
  percentile ranges (25th, 50th, 75th) for each class. These establish the
  expected frequency envelope for new signs assigned to that class.
"""

import csv
import logging
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "database" / "lineara_full.db"
GRID_PATH = PROJECT_ROOT / "data" / "analysis" / "bootstrapping" / "expanded_grid.csv"
OUT_DIR = PROJECT_ROOT / "data" / "analysis" / "frequency_constraints"
OUT_PATH = OUT_DIR / "frequency_profile.csv"


# ---------------------------------------------------------------------------
# Consonant class definitions for Linear A (based on CONFIRMED sign phonology)
# ---------------------------------------------------------------------------
# Each class maps a label to a set of consonant graphemes/phonemes.
# "VOWEL" is a special class for pure-vowel signs (a, e, i, o, u).
CONSONANT_CLASSES: dict[str, set[str]] = {
    "DENTAL": {"t", "d", "n"},
    "LABIAL": {"p", "m"},
    "VELAR":  {"k"},
    "SIBILANT": {"s", "z"},
    "LIQUID": {"r", "l"},
    "PALATAL": {"j"},
    "SEMIVOWEL": {"w"},
    "VOWEL": {""},  # empty consonant = pure vowel sign
}

# Standard five vowels
VOWELS: list[str] = ["a", "e", "i", "o", "u"]

# Named vowel rows for reporting
VOWEL_NAMES: dict[str, str] = {
    "a": "A-row",
    "e": "E-row",
    "i": "I-row",
    "o": "O-row",
    "u": "U-row",
}


def load_database_frequencies(db_path: Path) -> dict[str, int]:
    """Return {bennett_id: frequency} for all syllabogram occurrences."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT bennett_id, COUNT(*) AS freq FROM signs "
        "WHERE sign_type = 'syllabogram' AND bennett_id != '' "
        "GROUP BY bennett_id ORDER BY freq DESC"
    )
    freqs: dict[str, int] = {}
    for row in c.fetchall():
        freqs[row["bennett_id"]] = row["freq"]
    conn.close()
    return freqs


def load_grid(path: Path) -> list[dict]:
    """Load expanded_grid.csv and return list of row dicts."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def parse_cv(refined_value: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a refined phonetic value into (consonant, vowel).

    Returns (None, None) for unknown/missing values.
    Handles pure vowels (e.g. 'a' -> ('', 'a')), standard CV,
    and some CCV patterns.
    """
    if not refined_value or refined_value.strip() in ("?", ""):
        return None, None
    val = refined_value.strip().lower()

    # Known consonant digraphs in the data
    digraphs = [
        "kh", "th", "ph", "ts", "dz", "kw",
        "gw", "tw", "dw", "sw", "qw",
    ]

    # Pure vowel
    if val in ("a", "e", "i", "o", "u"):
        return "", val

    # Try digraph consonant
    consonant = ""
    rest = val
    for dg in digraphs:
        if val.startswith(dg):
            consonant = dg
            rest = val[len(dg):]
            break

    if not consonant:
        consonant = val[0]
        rest = val[1:]

    # Find first vowel in rest
    vowel = ""
    for i, ch in enumerate(rest):
        if ch in "aeiou":
            vowel = rest[i:]
            # The consonant includes everything before the first vowel
            if i > 0:
                consonant = consonant + rest[:i]
            break

    if not vowel:
        # No vowel found — treat whole thing as consonant (shouldn't happen
        # for standard CV, but be robust)
        return consonant, ""

    return consonant, vowel


def classify_sign(
    consonant: Optional[str], vowel: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    """Map (consonant, vowel) to a consonant class label and vowel."""
    if consonant is None or vowel is None:
        return None, None

    for cls_label, consonants in CONSONANT_CLASSES.items():
        if consonant in consonants:
            return cls_label, vowel if vowel in VOWELS else None

    # Unknown consonant — treat as its own class for profiling
    return f"OTHER({consonant})", vowel if vowel in VOWELS else None


def compute_class_statistics(
    frequencies: list[float],
) -> dict:
    """Compute descriptive statistics for a list of frequency values."""
    if not frequencies:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "total_tokens": 0,
        }

    freq_sorted = sorted(frequencies)
    n = len(freq_sorted)

    mean = sum(freq_sorted) / n
    var = sum((x - mean) ** 2 for x in freq_sorted) / n  # population std
    std = math.sqrt(var) if n > 1 else 0.0

    def percentile(p: float) -> float:
        """Linear interpolation percentile."""
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return freq_sorted[int(k)]
        d0 = freq_sorted[f] * (c - k)
        d1 = freq_sorted[c] * (k - f)
        return d0 + d1

    return {
        "count": n,
        "mean": round(mean, 1),
        "std": round(std, 1),
        "min": freq_sorted[0],
        "max": freq_sorted[-1],
        "p25": round(percentile(0.25), 1),
        "p50": round(percentile(0.50), 1),
        "p75": round(percentile(0.75), 1),
        "total_tokens": int(sum(freq_sorted)),
    }


def build_profile() -> list[dict]:
    """Main: build the frequency profile."""
    freqs = load_database_frequencies(DB_PATH)
    grid = load_grid(GRID_PATH)

    # Index grid by bennett_id
    grid_map: dict[str, dict] = {r["bennett_id"]: r for r in grid}

    # Parse all CONFIRMED signs with known values
    confirmed_signs: list[dict] = []
    for r in grid:
        if r["decision"] != "CONFIRM":
            continue
        c, v = parse_cv(r.get("refined_value", ""))
        consonant_class, vowel = classify_sign(c, v)
        freq = freqs.get(r["bennett_id"], 0)
        if consonant_class is not None and vowel is not None:
            confirmed_signs.append({
                "bennett_id": r["bennett_id"],
                "refined_value": r["refined_value"],
                "consonant": c,
                "vowel": v,
                "consonant_class": consonant_class,
                "vowel": vowel,
                "frequency": freq,
            })

    log.info("CONFIRMED signs with known CV: %d", len(confirmed_signs))

    # --- Per-consonant-class statistics ---
    by_consonant_class: dict[str, list[float]] = defaultdict(list)
    for s in confirmed_signs:
        by_consonant_class[s["consonant_class"]].append(s["frequency"])

    # --- Per-vowel statistics ---
    by_vowel: dict[str, list[float]] = defaultdict(list)
    for s in confirmed_signs:
        by_vowel[s["vowel"]].append(s["frequency"])

    # --- Per-CV-slot statistics ---
    by_cv: dict[str, list[float]] = defaultdict(list)
    for s in confirmed_signs:
        slot = f"{s['consonant_class']}_{s['vowel']}"
        by_cv[slot].append(s["frequency"])

    # --- Global statistics for all syllabograms ---
    all_freqs = [f for f in freqs.values() if f > 0]
    global_stats = compute_class_statistics(all_freqs)

    # --- Build output rows ---
    rows: list[dict] = []

    # 1. Global
    rows.append({
        "profile_type": "GLOBAL",
        "profile_label": "All syllabograms",
        **global_stats,
    })

    # 2. Per consonant class
    for cls_label in sorted(CONSONANT_CLASSES.keys()):
        stats = compute_class_statistics(by_consonant_class.get(cls_label, []))
        rows.append({
            "profile_type": "CONSONANT_CLASS",
            "profile_label": cls_label,
            **stats,
        })

    # 3. Per vowel
    for v in VOWELS:
        stats = compute_class_statistics(by_vowel.get(v, []))
        rows.append({
            "profile_type": "VOWEL_ROW",
            "profile_label": f"{v} ({VOWEL_NAMES.get(v, v)})",
            **stats,
        })

    # 4. Per CV slot (only those with ≥2 signs for meaningful stats)
    for slot in sorted(by_cv.keys()):
        vals = by_cv[slot]
        if len(vals) >= 2:
            stats = compute_class_statistics(vals)
            rows.append({
                "profile_type": "CV_SLOT",
                "profile_label": slot,
                **stats,
            })

    return rows


def write_profile(rows: list[dict], path: Path) -> None:
    """Write frequency profile CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "profile_type", "profile_label",
        "count", "mean", "std", "min", "max",
        "p25", "p50", "p75", "total_tokens",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %d profile rows to %s", len(rows), path)


def main() -> None:
    """Entry point."""
    log.info("Building frequency profile...")
    rows = build_profile()
    write_profile(rows, OUT_PATH)
    log.info("Done.")


if __name__ == "__main__":
    main()
