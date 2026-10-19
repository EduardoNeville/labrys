"""Grid purge — the generator for `expanded_grid_purged.csv`, the honest grid.

The rule (from `data/analysis/ventris/grid_purge_result.md`, 2026-08-13):

    a row survives iff it has a valid Unicode codepoint AND >= 1 occurrence in the corpus

The committed purged grid was produced once by hand and had no generator, so as long as
that stayed true the project's most-cited artifact could not be re-derived or checked. It
can now. `--check` is wired into `pipeline/guards.py`.

Why the rule is the right one
-----------------------------
`expanded_grid.csv` carries 138 entries, 69 of which refer to signs that do not exist:
AB 100-137 (placeholders whose codepoints are actually A 300+ logograms) and a set of
signs with a codepoint but zero occurrences in the corrected corpus. A "CONFIRM" on such
a row asserts a value for a sign nobody has ever seen (AB 68 "ro" was the flagship
casualty). Removing them is not a judgement call — it is the difference between a claim
and a placeholder.

Usage
-----
    uv run python pipeline/purge_grid.py --check          # verify the committed grid
    uv run python pipeline/purge_grid.py --write          # regenerate it
    uv run python pipeline/purge_grid.py --grid data/analysis/comparative/refined_phonetic_grid.csv
                                                          # purge any other grid to <stem>_purged.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import sqlite3
import sys
from pathlib import Path

from pipeline.unicode_utils import bennett_to_unicode

logger = logging.getLogger("purge_grid")

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data/database/lineara_full.db"
SOURCE = REPO / "data/analysis/bootstrapping/expanded_grid.csv"
PURGED = REPO / "data/analysis/bootstrapping/expanded_grid_purged.csv"


def corpus_counts(db: Path = DB) -> dict[str, int]:
    conn = sqlite3.connect(db)
    try:
        return {bid: n for bid, n in conn.execute(
            "SELECT bennett_id, COUNT(*) FROM signs WHERE bennett_id <> '' GROUP BY bennett_id")}
    finally:
        conn.close()


def reasons(row: dict, counts: dict[str, int]) -> list[str]:
    """Why this row is a phantom. Empty list = the row survives."""
    bid = (row.get("bennett_id") or "").strip()
    why = []
    if not bid:
        return ["no bennett_id"]
    if not bennett_to_unicode(bid):
        why.append("no valid codepoint")
    if counts.get(bid, 0) == 0:
        why.append("0 corpus occurrences")
    return why


def purge(rows: list[dict], counts: dict[str, int]) -> tuple[list[dict], list[tuple[str, str]]]:
    kept, dropped = [], []
    for r in rows:
        why = reasons(r, counts)
        if why:
            dropped.append(((r.get("bennett_id") or "?").strip(), "; ".join(why)))
        else:
            kept.append(r)
    return kept, dropped


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def check() -> int:
    """The committed purged grid must equal purge(expanded_grid.csv), row for row."""
    counts = corpus_counts()
    src = list(csv.DictReader(open(SOURCE, encoding="utf-8")))
    committed = list(csv.DictReader(open(PURGED, encoding="utf-8")))
    rebuilt, dropped = purge(src, counts)

    if rebuilt != committed:
        by_id = {r["bennett_id"]: r for r in committed}
        diffs = [r["bennett_id"] for r in rebuilt if by_id.get(r["bennett_id"]) != r]
        missing = sorted(set(by_id) - {r["bennett_id"] for r in rebuilt})
        extra = sorted({r["bennett_id"] for r in rebuilt} - set(by_id))
        raise AssertionError(
            f"purged grid is not reproducible: {len(rebuilt)} rebuilt vs {len(committed)} "
            f"committed; changed rows {diffs[:6]}; only-committed {missing[:6]}; "
            f"only-rebuilt {extra[:6]}")

    confirm = sum(1 for r in rebuilt if r.get("decision") == "CONFIRM")
    return (f"{len(rebuilt)}/{len(src)} rows survive ({len(dropped)} phantoms dropped); "
            f"{confirm} CONFIRM — byte-identical to the committed grid")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="verify the committed purged grid")
    p.add_argument("--write", action="store_true", help="regenerate the purged grid")
    p.add_argument("--grid", type=Path, default=None,
                   help="purge any other grid; writes <stem>_purged.csv next to it")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if a.grid:
        counts = corpus_counts()
        rows = list(csv.DictReader(open(a.grid, encoding="utf-8")))
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

    if a.write:
        counts = corpus_counts()
        rows = list(csv.DictReader(open(SOURCE, encoding="utf-8")))
        kept, dropped = purge(rows, counts)
        write_csv(PURGED, kept, list(rows[0].keys()))
        logger.info("wrote %s: %d rows (%d dropped)", PURGED.relative_to(REPO),
                    len(kept), len(dropped))
        return

    # default and --check: verify
    try:
        print(check())
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
