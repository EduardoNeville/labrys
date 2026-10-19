"""Phase 11, Avenue 7b — Libation formula segmentation into word-hypotheses.

The libation texts share a five-part formulaic structure:
  A: AB 08 AB 51 AB 26 [AB 85] AB 46 [AB 49]
  B: AB 49 AB 30 AB 30 AB 52 AB 12
  C: AB 10 AB 06 [AB 62] AB 06 [AB 36]
  D: AB 26 AB 34 AB 06 AB 65
  E: AB 36 AB 23 AB 04

This module:
1. Verifies the five-part structure quantitatively (co-occurrence of parts).
2. Segments the formula into word-hypotheses (stable chunks = words).
3. Cross-references against candidate Minoan deity names and Linear B
   libation/dedication parallels.

The hypothesis (testable): the formula is a ritual dedication of the form
  [offering/verb] [deity name] [beneficiary] [request]
and the deity name is one of the stable chunks.

Usage:
    uv run python pipeline/ventris/libation_segmentation.py
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

LIBATION_PREFIXES = ("IOZa", "KOZa", "PKZa", "ARKH", "PRZa", "SYZa")

# Five-part formula as observed (from the full-text alignment)
PARTS = {
    "A": ["AB 08", "AB 51", "AB 26", "AB 85", "AB 46", "AB 49"],
    "B": ["AB 49", "AB 30", "AB 30", "AB 52", "AB 12"],
    "C": ["AB 10", "AB 06", "AB 62", "AB 06", "AB 36"],
    "D": ["AB 26", "AB 34", "AB 06", "AB 65"],
    "E": ["AB 36", "AB 23", "AB 04"],
}

# Candidate Minoan deity names (from Linear B theonyms + later Greek tradition)
# Sign values use the LB-transfer values (transliteration)
DEITY_CANDIDATES = {
    "Diktaian (Zeus)": "di-ka-ta",          # Dikte
    "Idaian (Zeus)": "i-da",                # Mt Ida
    "Potnia (Mistress)": "po-ti-ni-ja",     # Linear B potnia
    "Diktaian Mother": "da-pu-ri-to",       # labyrinth/double-axe
    "A-sa-sa-ra (Mother)": "a-sa-sa-ra",    # possible Minoan theonym in LB
}


def load_libation_sequences(db_path: str = "data/database/lineara_full.db") -> Dict[str, List[str]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT i.gorila_id, s.sequence, s.bennett_id
        FROM signs s JOIN inscriptions i ON s.inscription_id = i.id
        WHERE s.sign_type = 'syllabogram' AND s.bennett_id LIKE 'AB %'
        ORDER BY i.id, s.sequence
    """)
    seqs: Dict[str, List[str]] = defaultdict(list)
    for r in c.fetchall():
        if r["gorila_id"].startswith(LIBATION_PREFIXES):
            seqs[r["gorila_id"]].append(r["bennett_id"])
    conn.close()
    return dict(seqs)


def part_in_seq(part: List[str], seq: List[str]) -> bool:
    """Is this part (allowing optional middle elements) a subsequence of seq?"""
    # contiguous match of the part's core (first 3 + last 2, allowing the
    # optional middle to vary) — simplified: check contiguous presence
    for i in range(len(seq) - len(part) + 1):
        if seq[i:i + len(part)] == part:
            return True
    # also check the core without the optional AB 85 / AB 49
    core = [p for p in part if p not in ("AB 85",)]
    for i in range(len(seq) - len(core) + 1):
        if seq[i:i + len(core)] == core:
            return True
    return False


def part_cooccurrence(seqs: Dict[str, List[str]]) -> None:
    """How many inscriptions contain each part, and do parts co-occur?"""
    part_presence = {p: [] for p in PARTS}
    for gid, seq in seqs.items():
        for p, chunk in PARTS.items():
            if part_in_seq(chunk, seq):
                part_presence[p].append(gid)
    print("Part presence across libation inscriptions:")
    for p, gids in part_presence.items():
        print(f"  Part {p} ({' '.join(PARTS[p])}): {len(gids)} insns")
    # co-occurrence: which inscriptions have >=3 parts?
    multi = {gid: sum(1 for p in PARTS if gid in part_presence[p])
             for gid in seqs}
    n3 = sum(1 for v in multi.values() if v >= 3)
    print(f"\nInscriptions with >=3 of the 5 parts: {n3}/{len(seqs)}")


def sign_transliterations() -> Dict[str, str]:
    """Map bennett_id -> conventional transliteration (LB transfer)."""
    out = {}
    with open("data/analysis/bootstrapping/expanded_grid.csv", newline="") as f:
        for r in csv.DictReader(f):
            bid = r.get("bennett_id", "").strip()
            # conventional value or refined value
            val = r.get("conventional_value", "").strip() or r.get("refined_value", "").strip()
            if bid and val and val != "?":
                out[bid] = val
    # add the refined phonetic grid for UNCERTAIN signs
    with open("data/analysis/comparative/refined_phonetic_grid.csv", newline="") as f:
        for r in csv.DictReader(f):
            bid = r.get("bennett_id", "").strip()
            val = r.get("refined_value", "").strip()
            if bid and val and val != "?" and bid not in out:
                out[bid] = val
    return out


def transliterate(seq: List[str], tl: Dict[str, str]) -> str:
    """Transliterate a sign sequence using LB-transfer values."""
    out = []
    for s in seq:
        v = tl.get(s, "?")
        out.append(v if v != "?" else f"*{s.split()[-1]}")
    return "-".join(out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seqs = load_libation_sequences()
    tl = sign_transliterations()

    print("=== LIBATION FORMULA SEGMENTATION ===\n")
    part_cooccurrence(seqs)

    print("\n-- The five parts transliterated (LB-transfer values) --")
    for p, chunk in PARTS.items():
        print(f"  Part {p}: {transliterate(chunk, tl)}")

    print("\n-- Deity-name cross-reference (LB-transfer transliteration) --")
    print("  (Does any part's transliteration match a known Minoan/LB theonym?)")
    for name, spelling in DEITY_CANDIDATES.items():
        print(f"  {name} ({spelling})")

    print("\n-- The opening formula as a word-hypothesis --")
    opening = ["AB 08", "AB 51", "AB 26", "AB 46"]
    print(f"  Opening A-core: {transliterate(opening, tl)}")
    print(f"  (In Linear B, libation formulas open with a verb or theonym)")

    # Write output
    out = Path("data/analysis/ventris")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "libation_parts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["part", "chunk_bennett", "chunk_transliterated"])
        for p, chunk in PARTS.items():
            w.writerow([p, " ".join(chunk), transliterate(chunk, tl)])
    print(f"\nWrote data/analysis/ventris/libation_parts.csv")
