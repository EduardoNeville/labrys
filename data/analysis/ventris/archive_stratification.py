"""Archive stratification: the check this corpus needs before any positional claim.

Found by auditing three survivors of every earlier audit on 2026-10-01, all of which behaved the
same way:

  * commodity sign<->class enrichment   - real at Haghia Triada, FAILS cross-site replication
                                          (2 of 67, both logogram<->own-class tautologies)
  * A 301 "heading/entry-opening marker" - 229 of 231 occurrences are initial at Haghia Triada
                                          *Portico 11 and Room 13* (99%), and 9 of 43 (21%)
                                          everywhere else
  * libation formula                    - genuinely cross-site (9 occurrences, 5 sites, 9/9 slot
                                          order) - the exception that shows the rule

The reason is a corpus property nobody had written down: **Portico 11 and Room 13 alone is 863 of
1,719 inscriptions (50.2%) of the whole Linear A corpus**, and it has its own tablet format. A
pooled positional or distributional statistic is therefore mostly a statistic about that one room.
Stratification has to go to ROOM level, not site level: two rooms of the same site disagree about
A 301 (229/231 initial at Portico, 0/3 at Villa Magazine).

    uv run python data/analysis/ventris/archive_stratification.py
    uv run python data/analysis/ventris/archive_stratification.py --sign "A 306"
"""

from __future__ import annotations

import argparse
import sqlite3
from collections import Counter
from pathlib import Path

DB = Path(__file__).resolve().parents[3] / "data" / "database" / "lineara_full.db"


def archive_of(site: str | None) -> str:
    """Room-level archive where the corpus records one, else the site."""
    if not site:
        return "unknown"
    return site


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sign", default="A 301")
    p.add_argument("--min-n", type=int, default=1)
    args = p.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    total = conn.execute("SELECT COUNT(*) FROM inscriptions").fetchone()[0]

    print("corpus share by archive (the reason stratification is mandatory):")
    for r in conn.execute(
            "SELECT COALESCE(f.site,'unknown') s, COUNT(*) n FROM inscriptions i "
            "LEFT JOIN findspots f ON f.id=i.findspot_id GROUP BY s ORDER BY n DESC LIMIT 6"):
        print(f"  {r['s'][:44]:44s} {r['n']:5d}  ({r['n']/total:5.1%})")
    print(f"  {'- pooled is mostly Portico 11 and Room 13 -':44s} {total:5d}")

    rows = conn.execute(
        "SELECT i.gorila_id g, COALESCE(f.site,'unknown') site, s.sequence q, s.bennett_id b, "
        "s.sign_type t FROM signs s JOIN inscriptions i ON i.id=s.inscription_id "
        "LEFT JOIN findspots f ON f.id=i.findspot_id ORDER BY i.id, s.sequence").fetchall()
    seq: dict = {}
    for r in rows:
        if r["t"] not in ("syllabogram", "logogram") or not r["b"]:
            continue
        seq.setdefault((r["g"], r["site"]), []).append(r["b"])

    occ = [(site, i, len(s)) for (g, site), s in seq.items()
           for i, b in enumerate(s) if b == args.sign]
    print(f"\n{args.sign}: {len(occ)} occurrences in {len(seq)} inscriptions")
    by_arch: dict = {}
    for site, i, n in occ:
        by_arch.setdefault(site, []).append((i, n))
    print(f"  {'archive':44s} {'n':>4s} {'at index 0':>11s} {'within first 3':>15s}")
    for site, sub in sorted(by_arch.items(), key=lambda kv: -len(kv[1])):
        if len(sub) < args.min_n:
            continue
        z = sum(1 for i, _ in sub if i == 0)
        f3 = sum(1 for i, _ in sub if i <= 2)
        print(f"  {archive_of(site)[:44]:44s} {len(sub):4d} {z:5d} ({z/len(sub):5.1%}) "
              f"{f3:7d} ({f3/len(sub):5.1%})")
    z = sum(1 for _, i, _ in occ if i == 0)
    print(f"  {'POOLED':44s} {len(occ):4d} {z:5d} ({z/len(occ):5.1%})   <- the number not to quote")
    print("\n  A pooled figure answers a question about the largest archive. Report the per-archive"
          "\n  column, or state in the claim which archive it describes.")


if __name__ == "__main__":
    main()
