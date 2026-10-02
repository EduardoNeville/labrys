"""Stratify the §4.1 oracle by findspot — with per-stratum Kober graphs.

The paper's headline result (0.00×, now 0.23×, NO SIGNAL) is pooled over a corpus that is 69.4%
Knossos. `stratify_lb_by_findspot.py` closed that exposure for §4.3/§4.4 and left §4.1 named as
remaining. This closes it.

**The contamination this avoids.** A stratum cannot be scored with the corpus-wide Kober triples:
those links are derived from every site's texts, so a "Knossos-only" run would silently use PY/TH/MY
frame structure in its constraint channel. So each stratum gets

  1. its own filtered corpus (a copy of the DB with other findspots' inscriptions, signs and words
     deleted), and
  2. **its own Kober graph**, rebuilt from that corpus by the same `TripleDetector` configuration
     `lb_oracle.build_kober()` uses.

The canonical functions are driven by patching `lb_oracle`'s module constants — including
`RESULT_MD`, so a stratum run cannot overwrite the pooled pre-registration report.

    uv run python data/analysis/ventris/stratify_oracle_by_findspot.py
    uv run python data/analysis/ventris/stratify_oracle_by_findspot.py --trials 4
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

import pipeline.lb_oracle as O  # noqa: E402
from pipeline.lb_ingest import assert_no_leak  # noqa: E402

POOLED = {"recovery": 0.0063, "chance": 0.0273, "lift": 0.23, "verdict": "NO SIGNAL"}


def build_stratum(site: str, work: Path, src_db: Path) -> tuple[Path, dict]:
    db = work / "corpus.db"
    shutil.copy(src_db, db)
    conn = sqlite3.connect(db)
    fid = conn.execute("SELECT id FROM findspots WHERE site = ?", (site,)).fetchone()
    assert fid, f"no findspot {site!r}"
    fid = fid[0]
    where = "inscription_id IN (SELECT id FROM inscriptions WHERE findspot_id IS NOT ?)"
    n_signs = conn.execute(f"DELETE FROM signs WHERE {where}", (fid,)).rowcount
    conn.execute(f"DELETE FROM words WHERE {where}", (fid,))
    n_ins = conn.execute("DELETE FROM inscriptions WHERE findspot_id IS NOT ?",
                         (fid,)).rowcount
    conn.commit()
    stats = {
        "inscriptions": conn.execute("SELECT COUNT(*) FROM inscriptions").fetchone()[0],
        "signs": conn.execute("SELECT COUNT(*) FROM signs").fetchone()[0],
        "distinct_signs": conn.execute(
            "SELECT COUNT(DISTINCT bennett_id) FROM signs WHERE bennett_id != ''").fetchone()[0],
    }
    conn.close()
    assert_no_leak(db)
    return db, stats


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--hidden", type=int, default=20)
    p.add_argument("--min-inscriptions", type=int, default=100)
    args = p.parse_args()

    src = sqlite3.connect(O.DB_PATH)
    sites = [(s, n) for s, n in src.execute(
        "SELECT COALESCE(f.site,'?') s, COUNT(*) n FROM inscriptions i "
        "LEFT JOIN findspots f ON f.id=i.findspot_id GROUP BY s ORDER BY n DESC")]
    src.close()
    # Capture the pooled corpus path BEFORE any patching. O.DB_PATH is patched per stratum (the
    # canonical functions read it at call time), so re-reading it inside the loop copies the
    # previous stratum's filtered DB and silently scores an empty corpus -- which is what the first
    # version of this script did for PY and TH.
    src_db = Path(O.DB_PATH)

    print(f"pooled reference (the committed report): recovery {POOLED['recovery']:.4f} vs chance "
          f"{POOLED['chance']:.4f} -> lift {POOLED['lift']:.2f}x, {POOLED['verdict']}")
    print(f"trials={args.trials} hidden={args.hidden} per stratum; strata with < "
          f"{args.min_inscriptions} inscriptions are listed but not scored\n")
    print(f"{'stratum':9s} {'inscr':>6s} {'tokens':>7s} {'signs':>6s} {'anchors':>8s} "
          f"{'recovery':>9s} {'chance':>8s} {'lift':>7s}  verdict")

    for site, n in sites:
        if n < args.min_inscriptions:
            print(f"{site:9s} {n:6d} {'-':>7s} {'-':>6s} {'-':>8s} {'-':>9s} {'-':>8s} {'-':>7s}"
                  f"  skipped (too small)")
            continue
        work = Path(tempfile.mkdtemp(prefix=f"strat-{site}-"))
        t0 = time.time()
        db, stats = build_stratum(site, work, src_db)
        # Patch every module constant the canonical functions read, including the report
        # path: a stratum run must not overwrite the pooled pre-registration record.
        O.DB_PATH = db
        O.KOBER_DIR = work / "kober"
        O.TRIPLES = O.KOBER_DIR / "triple_patterns.csv"
        O.FREQ_CSV = work / "constrained_candidates.csv"
        O.RESULT_MD = work / "report.md"
        O.build_kober()
        res = O.run_oracle(trials=args.trials, hidden=args.hidden)
        anchors = len(res.get("per_sign_trials", {}))
        print(f"{site:9s} {stats['inscriptions']:6d} {stats['signs']:7d} "
              f"{stats['distinct_signs']:6d} {anchors:8d} {res['recovery_rate']:9.4f} "
              f"{res['chance_rate']:8.4f} {res['lift_over_chance']:6.2f}x  "
              f"{res['verdict']}   ({time.time() - t0:.0f}s)")

    print("\nthe question this answers: does any stratum recover where the pooled run does not?")
    print("A stratum clearing the pre-registered 1.5x gate would falsify the pooled negative.")


if __name__ == "__main__":
    main()
