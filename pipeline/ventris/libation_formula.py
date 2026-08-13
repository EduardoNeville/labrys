"""Phase 11, Avenue 7 — Libation formula segmentation.

The libation vessels (IOZa/KOZa/PKZa/ARKH/PRZa/SYZa — Iouktas, Kophinas,
Palaikastro, Arkalochori, Prassa, Syme) carry a fixed recurring formula.
This module:

1. Extracts all libation-site sign sequences.
2. Finds recurring n-grams (2-6 signs) across inscriptions.
3. Clusters them into a formula "grammar" — which chunks co-occur in order.
4. Identifies the most stable chunks (likely words) vs variable slots.

Usage:
    uv run python pipeline/ventris/libation_formula.py
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

LIBATION_PREFIXES = ("IOZa", "KOZa", "PKZa", "ARKH", "PRZa", "SYZa")


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
        gid = r["gorila_id"]
        if gid.startswith(LIBATION_PREFIXES):
            seqs[gid].append(r["bennett_id"])
    conn.close()
    return dict(seqs)


def recurring_ngrams(seqs: Dict[str, List[str]], min_insns: int = 2,
                     max_n: int = 6) -> List[Tuple[int, Tuple, int, List[str]]]:
    """Return (n, gram, n_insns, inscription_ids) for n-grams repeating across
    >= min_insns inscriptions."""
    grams: Dict[Tuple[int, Tuple], List[str]] = defaultdict(list)
    for gid, seq in seqs.items():
        for n in range(2, max_n + 1):
            for i in range(len(seq) - n + 1):
                grams[(n, tuple(seq[i:i + n]))].append(gid)
    out = []
    for (n, gram), gids in grams.items():
        uniq = sorted(set(gids))
        if len(uniq) >= min_insns:
            out.append((n, gram, len(uniq), uniq))
    out.sort(key=lambda x: (-x[2], -x[0]))
    return out


def formula_positions(seqs: Dict[str, List[str]]) -> Dict[Tuple, List[int]]:
    """For each recurring chunk, its start positions across inscriptions."""
    pos: Dict[Tuple, List[int]] = defaultdict(list)
    for gid, seq in seqs.items():
        for n in (2, 3, 4, 5, 6):
            for i in range(len(seq) - n + 1):
                gram = tuple(seq[i:i + n])
                pos[gram].append(i)
    return dict(pos)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seqs = load_libation_sequences()
    logger.info("Loaded %d libation inscriptions", len(seqs))

    print("=== LIBATION FORMULA: RECURRING CHUNKS ===")
    print(f"({len(seqs)} inscriptions, lengths {sorted({len(s) for s in seqs.values()})})\n")

    ng = recurring_ngrams(seqs, min_insns=3)
    print(f"-- n-grams repeating across >=3 inscriptions: {len(ng)} --")
    for n, gram, n_ins, gids in ng[:20]:
        print(f"  {list(gram)}  [{n_ins} insns: {gids[:5]}{'...' if len(gids)>5 else ''}]")

    print("\n-- The opening formula across all libation texts --")
    # find the longest chunk that starts at position 0 of many inscriptions
    pos = formula_positions(seqs)
    starts = {g: p for g, p in pos.items() if 0 in p}
    for gram, ps in sorted(starts.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  starts at pos 0 in {len(ps)}: {list(gram)}")

    # Write output
    out = Path("data/analysis/ventris")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "libation_formula_chunks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "chunk", "n_inscriptions", "inscriptions"])
        for n, gram, n_ins, gids in ng:
            w.writerow([n, " ".join(gram), n_ins, ";".join(gids)])
    print(f"\nWrote data/analysis/ventris/libation_formula_chunks.csv")
