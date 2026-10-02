"""Cross-site replication of the commodity associations. Pre-registered before the run.

The Phase 14 audit produced eight surviving sign-commodity pairs - but they were SELECTED on all
sites and then re-tested on the same documents, which inflates them. This is the test that
answers whether they generalize:

  selection  : take one site only, and select every (commodity, sign) pair clearing
               0.05/122 = 0.00041 within that site's documents. Fix the set.
  replication: test that fixed set on a DIFFERENT site, one never used in selection. A pair
               replicates if it clears 0.05/|selected set| there.
  then swap the two sites and repeat, so the answer is not an artifact of which site is which.

Pre-registered prediction, written before the run: **partial replication, and it will fail on the
weak members.** The three strongest LIVESTOCK pairs (AB 30, AB 81, AB 31; z 6.9-7.7 in the pooled
stratified test) should replicate. AB 41 - marginal at p=4.0e-04 pooled, the threshold itself -
should not. The WINE pairs cannot be tested on Khania at all: WINE has 8 Haghia Triada documents
and 1 each at Knossos and Zakros, so a Khania-internal WINE test has no population.

Recording the prediction is the point: "the strongest members replicate and the weak one does not"
is a falsifiable claim, and it is written here before the numbers are computed.

    uv run python data/analysis/commodity_decoding/cross_site_replication.py
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.ventris.commodity_semantics import hypergeom_tail  # noqa: E402

DB = REPO / "data" / "database" / "lineara_full.db"
CONTEXTS = REPO / "data/analysis/commodity_decoding/logogram_contexts.csv"
FAMILY = 122          # the full family used in Phase 14
ALPHA_FAMILY = 0.05 / FAMILY
SITES = ("Haghia Triada", "Khania")
COMmodity_MIN_DOCS = 5   # a commodity needs at least this many documents to be testable


def main() -> None:
    rows = list(csv.DictReader(open(CONTEXTS)))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    sign_docs: dict = defaultdict(set)
    for r in conn.execute("SELECT i.gorila_id gid, s.bennett_id bid FROM signs s "
                          "JOIN inscriptions i ON i.id = s.inscription_id "
                          "WHERE s.bennett_id != ''"):
        sign_docs[r["bid"]].add(r["gid"])
    conn.close()

    contexts = [(r["gorila_id"], r["site"].split(" - ")[0],
                 (r.get("commodity_class") or "").strip()) for r in rows]
    contexts = [(g, s, c) for g, s, c in contexts if c]
    by_site_docs: dict = defaultdict(set)
    for g, s, _ in contexts:
        by_site_docs[s].add(g)
    print(f"contexts with a commodity class: {len(contexts)};  sites: "
          f"{ {s: len(d) for s, d in sorted(by_site_docs.items(), key=lambda kv: -len(kv[1]))} }")

    def select(site: str) -> list:
        """Pairs clearing the family alpha on this site's documents alone."""
        docs = by_site_docs[site]
        N = len(docs)
        comm_of: dict = defaultdict(set)
        for g, s, c in contexts:
            if s == site:
                comm_of[c].add(g)
        pairs = []
        for cc, cdocs in comm_of.items():
            if len(cdocs) < COMmodity_MIN_DOCS:
                continue
            for sign in sign_docs:
                sd = sign_docs[sign] & docs
                if len(sd) < 3:
                    continue
                k = len(sd & cdocs)
                if k == 0:
                    continue
                p = hypergeom_tail(N, len(sd), len(cdocs), k)
                if p < ALPHA_FAMILY:
                    pairs.append((cc, sign, k, len(cdocs), p))
        return pairs

    def test(pairs: list, site: str) -> list:
        """Re-test a fixed set on another site's documents. Threshold 0.05/|set|."""
        docs = by_site_docs[site]
        N = len(docs)
        thresh = 0.05 / max(len(pairs), 1)
        out = []
        for cc, sign, *_ in pairs:
            cdocs = {g for g, s, c in contexts if s == site and c == cc}
            if len(cdocs) < COMmodity_MIN_DOCS:
                out.append((cc, sign, None, len(cdocs), None, "untestable"))
                continue
            sd = sign_docs[sign] & docs
            k = len(sd & cdocs)
            p = hypergeom_tail(N, len(sd), len(cdocs), k) if k else 1.0
            out.append((cc, sign, k, len(cdocs), p, "pass" if p < thresh else "fail"))
        return out

    for dev, hold in (("Haghia Triada", "Khania"), ("Khania", "Haghia Triada")):
        sel = select(dev)
        print(f"\n=== selection on {dev}: {len(sel)} pairs clear {ALPHA_FAMILY:.5f} ===")
        for cc, sign, k, n, p in sorted(sel, key=lambda x: x[4]):
            print(f"    {cc} <-> {sign}: k={k}/{n} p={p:.2e}")
        if not sel:
            print("    (none -> nothing to replicate; a null selection result)")
            continue
        res = test(sel, hold)
        print(f"--- replication on {hold} (threshold {0.05/len(sel):.5f} over "
              f"{len(sel)} pairs) ---")
        for cc, sign, k, n, p, status in res:
            if p is None:
                print(f"    {cc} <-> {sign}: UNTESTABLE ({n} {hold} documents for this class)")
            else:
                print(f"    {cc} <-> {sign}: k={k}/{n} p={p:.2e}  {status.upper()}")
        passed = [r for r in res if r[5] == "pass"]
        print(f"    replicated: {len(passed)} of {len(sel)}")


if __name__ == "__main__":
    main()
