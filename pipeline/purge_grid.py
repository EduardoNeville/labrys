"""Grid purge — the phantom filter, and the guard on the canonical Linear A grid.

**The rule.** A grid row survives iff the sign has a valid Unicode codepoint AND at least one
occurrence in the corrected corpus. `expanded_grid_legacy_138.csv` carries 138 entries, 69 of which
refer to signs that do not exist: AB 100-137 (placeholders whose codepoints are actually A 300+
logograms) and a set of signs with a codepoint but zero occurrences. A "CONFIRM" on such a row
asserts a value for a sign nobody has ever seen (AB 68 "ro" was the flagship casualty).

**What changed on 2026-10-19** (`verification_audit.md` Phase 18):

1. The rule was applied at the *generators* (`phonetic_grid_refinement.py`,
   `bootstrapping/grid_expand.py`), so the grids are honest by construction and the purge is no
   longer a separate production step. `grid_expand.py` now writes the canonical grid directly.
2. The 138-row artifact is frozen as `expanded_grid_legacy_138.csv`; the Phase 11 purge result is
   still reconstructible from it.
3. **The rule was wrong for five signs.** The corpus and `languages/linear-a/mapping.csv` spell the
   suffix letters lower-case (`AB 21f`), while the grid lineage upper-cased them (`AB 21F`). The
   exact-string lookup found no codepoint and no occurrences, so the Phase 11 purge dropped
   `AB 21F` and `AB 22F` as phantoms — **two real signs, 37 occurrences**. Matching is now
   case-insensitive and IDs are canonicalised to the mapping's spelling.

Usage:
    uv run python pipeline/purge_grid.py                  # check the canonical grid (guard 20)
    uv run python pipeline/purge_grid.py --legacy-report   # what the frozen 138-row grid yields
    uv run python pipeline/purge_grid.py --grid PATH       # purge any other grid to <stem>_purged.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import sqlite3
import sys
from pathlib import Path

from pipeline.unicode_utils import bennett_to_unicode, canonical_bennett

logger = logging.getLogger("purge_grid")

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data/database/lineara_full.db"
BOOT = REPO / "data/analysis/bootstrapping"
LEGACY = BOOT / "expanded_grid_legacy_138.csv"       # frozen Phase 8 artifact
CANONICAL = BOOT / "expanded_grid_purged.csv"        # the grid everything reads
REFINED = REPO / "data/analysis/comparative/refined_phonetic_grid.csv"


def corpus_counts(db: Path = DB) -> dict[str, int]:
    """Occurrences per sign, indexed **case-insensitively** (upper-cased keys).

    Case matters here. The corpus stores the suffix letters in the mapping file's case (AB 21f,
    AB 22f, …); a grid that writes AB 21F must still find them, or the sign reads as a phantom and
    gets purged. That is how two real signs (37 occurrences) were lost on 2026-08-13; see
    verification_audit.md Phase 18.
    """
    conn = sqlite3.connect(db)
    try:
        out: dict[str, int] = {}
        for bid, n in conn.execute(
                "SELECT bennett_id, COUNT(*) FROM signs WHERE bennett_id <> '' GROUP BY bennett_id"):
            key = bid.strip().upper()
            out[key] = out.get(key, 0) + n
        return out
    finally:
        conn.close()


def reasons(row: dict, counts: dict[str, int]) -> list[str]:
    """Why this row is a phantom. Empty list = the row survives.

    Resolves the ID to the mapping file's spelling first, so a case variant is never mistaken for a
    non-existent sign.
    """
    bid = (row.get("bennett_id") or "").strip()
    why = []
    if not bid:
        return ["no bennett_id"]
    canonical = canonical_bennett(bid)
    if not bennett_to_unicode(canonical):
        why.append("no valid codepoint")
    if counts.get(canonical.upper(), counts.get(bid.upper(), 0)) == 0:
        why.append("0 corpus occurrences")
    return why


def purge(rows: list[dict], counts: dict[str, int]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Split rows into survivors and phantoms, canonicalising the survivors' sign IDs."""
    kept, dropped = [], []
    for r in rows:
        why = reasons(r, counts)
        if why:
            dropped.append(((r.get("bennett_id") or "?").strip(), "; ".join(why)))
        else:
            r = dict(r)
            r["bennett_id"] = canonical_bennett(r.get("bennett_id") or "")
            kept.append(r)
    return kept, dropped


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_canonical() -> str:
    """Guard 20: the grid everything reads contains only real signs, with canonical IDs."""
    if not CANONICAL.exists():
        raise AssertionError(f"{CANONICAL.relative_to(REPO)} is missing")
    rows = _read(CANONICAL)
    counts = corpus_counts()
    bad = [(r.get("bennett_id"), reasons(r, counts)) for r in rows if reasons(r, counts)]
    assert not bad, f"phantom rows in the canonical grid: {bad[:6]}"

    noncanon = [r["bennett_id"] for r in rows
                if r.get("bennett_id") != canonical_bennett(r.get("bennett_id"))]
    assert not noncanon, f"non-canonical sign IDs in the canonical grid: {noncanon[:6]}"

    confirm = sum(1 for r in rows if r.get("decision") == "CONFIRM")
    # a CONFIRM on a sign with no occurrences would be an assertion about nothing
    zero = [r["bennett_id"] for r in rows if r.get("decision") == "CONFIRM"
            and counts.get(r["bennett_id"].upper(), 0) == 0]
    assert not zero, f"CONFIRM on a sign with 0 occurrences: {zero}"
    return (f"{len(rows)} rows, {confirm} CONFIRM, every ID resolves "
            f"(codepoint + occurrences, case-insensitive)")


def check_row_agreement() -> str:
    """Guard 21: the two lineages must cover the same signs, or one of them is missing a sign."""
    if not (CANONICAL.exists() and REFINED.exists()):
        return "skipped (a grid is missing)"
    a = {r["bennett_id"] for r in _read(CANONICAL)}
    b = {r["bennett_id"] for r in _read(REFINED)}
    only_c, only_r = sorted(a - b), sorted(b - a)
    assert not only_c and not only_r, (
        f"grid row sets disagree — only in the canonical Phase 8 grid: {only_c[:6]}; "
        f"only in the refined Phase 5 grid: {only_r[:6]}")
    return f"both grids cover the same {len(a)} signs (row sets identical)"


def legacy_report() -> int:
    """What the frozen 138-row grid yields under the corrected rule (a report, not a guard)."""
    if not LEGACY.exists():
        print("no frozen legacy grid")
        return 2
    rows = _read(LEGACY)
    kept, dropped = purge(rows, corpus_counts())
    print(f"frozen legacy grid: {LEGACY.name}")
    print(f"  rows            : {len(rows)}")
    print(f"  survive (today) : {len(kept)}   CONFIRM {sum(1 for r in kept if r.get('decision') == 'CONFIRM')}")
    print(f"  dropped         : {len(dropped)}")
    print("  Phase 11 record : 69 survived (58 CONFIRM); the difference is two case variants")
    print("                    (AB 21F/AB 22F) that the exact-string rule dropped as phantoms.")
    for bid, why in dropped:
        if bid.upper() in {b.upper() for b in ("AB 21f", "AB 22f")}:
            print(f"    corrected: {bid} — {why}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="check the canonical grid (default)")
    p.add_argument("--legacy-report", action="store_true", help="report on the frozen 138-row grid")
    p.add_argument("--grid", type=Path, default=None,
                   help="purge any other grid; writes <stem>_purged.csv next to it")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if a.grid:
        counts = corpus_counts()
        rows = _read(a.grid)
        kept, dropped = purge(rows, counts)
        out = a.grid.with_name(a.grid.stem + "_purged.csv")
        write_csv(out, kept, list(rows[0].keys()))
        logger.info("%s: %d/%d rows survive (%d dropped) -> %s",
                    a.grid.name, len(kept), len(rows), len(dropped), out)
        for bid, why in dropped[:10]:
            logger.info("  dropped %s (%s)", bid, why)
        if len(dropped) > 10:
            logger.info("  ... and %d more", len(dropped) - 10)
        return

    if a.legacy_report:
        sys.exit(legacy_report())

    try:
        print(check_canonical())
        print(check_row_agreement())
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
