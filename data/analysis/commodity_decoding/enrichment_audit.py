"""Audit of the sign-commodity enrichment: does it survive a null that matches its unit?

AGENTS.md lists exactly one statistical positive among the "verified findings":

    AB 30 <-> LIVESTOCK (p=0.0001, 2.6x) and AB 28 <-> WINE (p=0.0001, 8.6x), surviving
    Bonferroni over 61 (commodity, sign) pairs.

Every other member of that list has since been retracted, corrected, or shown to be a class
metric, so this one is worth the same treatment the toponyms got - where the "geographic signal"
turned out to be genre, and p moved from 0.00086 to 0.38 the moment the null was matched to the
data's structure.

The structure here: `commodity_semantics.py` runs a hypergeometric test over adjacent *slots*
from a +/-3-sign window around each commodity logogram. Slots are not independent draws - they
overlap within a window, they overlap between windows of nearby logograms, and a short tablet's
window spans most of the text. WINE has 10 contexts and 14 slots; the effective sample is closer
to 10 documents than to 14 independent slots.

This script re-tests at the **document** level, where the hypergeometric's assumption holds, and
compares. Same 61-pair family, same Bonferroni threshold (0.05/61 = 0.00082).

    uv run python data/analysis/commodity_decoding/enrichment_audit.py
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.ventris.commodity_semantics import (  # noqa: E402
    CommoditySemantics, adjacent_slots, hypergeom_tail)

DB = REPO / "data" / "database" / "lineara_full.db"
ALPHA = 0.05


def main() -> None:
    cs = CommoditySemantics()
    fam_alpha, n_tests = cs.bonferroni_alpha(list(cs.commodity_slots.keys()))
    print(f"slot-level (as committed): N={cs.N} slots, family={n_tests} tests, "
          f"Bonferroni alpha={fam_alpha:.5f}")

    # ── the committed numbers, reproduced ──
    committed = {}
    with open(REPO / "data/analysis/commodity_decoding/sign_commodity_enrichment.csv") as f:
        for r in csv.DictReader(f):
            committed[(r["commodity_class"], r["sign"])] = (
                int(r["cooccurrences"]), int(r["slots"]), float(r["p_value"]),
                float(r["fold_enrichment"]))

    # ── document level: presence of the sign anywhere in the inscription ──
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    sign_docs: dict = defaultdict(set)
    for row in conn.execute(
            "SELECT i.gorila_id AS gid, s.bennett_id AS bid FROM signs s "
            "JOIN inscriptions i ON i.id = s.inscription_id WHERE s.bennett_id != ''"):
        sign_docs[row["bid"]].add(row["gid"])
    conn.close()

    rows = list(csv.DictReader(open(REPO / "data/analysis/commodity_decoding/logogram_contexts.csv")))
    docs_by_commodity: dict = defaultdict(set)
    all_docs: set = set()
    for r in rows:
        cc = (r.get("commodity_class") or "").strip()
        if not cc:
            continue
        docs_by_commodity[cc].add(r["gorila_id"])
        all_docs.add(r["gorila_id"])
    N_doc = len(all_docs)
    print(f"document-level: {N_doc} inscriptions carry a classified commodity context "
          f"(vs {cs.N} slots)\n")

    print(f"{'pair':26s} {'slots k/n':>11s} {'p':>9s} {'fold':>6s}   "
          f"{'docs k/n':>10s} {'p':>9s} {'fold':>6s}  survives")
    survivors_slot, survivors_doc, rows_out = [], [], []
    for (cc, sign), (k, n, p, fold) in sorted(committed.items(), key=lambda kv: kv[1][2]):
        docs_cc = docs_by_commodity.get(cc, set())
        n_doc = len(docs_cc)
        k_doc = sum(1 for d in docs_cc if d in sign_docs.get(sign, set()))
        K_doc = sum(1 for d in all_docs if d in sign_docs.get(sign, set()))
        p_doc = hypergeom_tail(N_doc, K_doc, n_doc, k_doc)
        exp = (K_doc / N_doc) * n_doc if N_doc else 0
        fold_doc = k_doc / exp if exp else 0.0
        ok_slot = p < fam_alpha
        ok_doc = p_doc < fam_alpha
        if ok_slot:
            survivors_slot.append((cc, sign, p))
        if ok_doc:
            survivors_doc.append((cc, sign, p_doc))
        rows_out.append((cc, sign, k, n, p, fold, k_doc, n_doc, p_doc, fold_doc))
        if k >= 2 or ok_slot:            # print the interesting ones, not all 61
            print(f"{cc+' <-> '+sign:26s} {k:4d}/{n:<6d} {p:9.2e} {fold:6.2f}x   "
                  f"{k_doc:4d}/{n_doc:<5d} {p_doc:9.2e} {fold_doc:6.2f}x  "
                  f"{'slot' if ok_slot else '----'} {'doc' if ok_doc else ''}")

    print(f"\nsurviving Bonferroni at the SLOT level (as committed): {len(survivors_slot)}")
    for cc, sign, p in survivors_slot:
        print(f"  {cc} <-> {sign}: p={p:.2e}")
    print(f"surviving Bonferroni at the DOCUMENT level:            {len(survivors_doc)}")
    for cc, sign, p in survivors_doc:
        print(f"  {cc} <-> {sign}: p={p:.2e}")

    # ── every document-level survivor gets the stratified permutation ──
    # Note the resolution requirement: the family-wise alpha is 0.05/122 = 0.00041, so 2,000
    # reps (floor 0.0005) cannot resolve it. 20,000 gives a floor of 5e-5, below the threshold.
    import random

    rng = random.Random(0)
    REPS = 20000
    site_of = {r["gorila_id"]: r["site"].split(" - ")[0]
               for r in rows if r["gorila_id"] in all_docs}
    docs_by_site: dict = defaultdict(list)
    for d in sorted(all_docs):
        docs_by_site[site_of[d]].append(d)
    print(f"\nsite-stratified permutation, all document-level survivors ({REPS} reps, "
          f"floor {1/REPS:.0e} < family alpha {fam_alpha:.5f}):")
    print(f"  {'pair':26s} {'k':>4s} {'null mean':>10s} {'null sd':>8s} {'null max':>9s} "
          f"{'p_perm':>8s} {'z':>7s}")
    tested = [(cc, sign) for cc, sign, _ in survivors_doc]
    # also the two originals even if the survivor list ever changes
    for pair in (("LIVESTOCK", "AB 30"), ("WINE", "AB 28")):
        if pair not in tested:
            tested.append(pair)
    promoted, demoted = [], []
    for cc, sign in tested:
        docs_cc = docs_by_commodity[cc]
        docs_sign = {d for d in all_docs if d in sign_docs.get(sign, set())}
        obs = len(docs_sign & docs_cc)
        per_site = Counter(site_of[d] for d in docs_sign)
        nulls = []
        for _ in range(REPS):
            fake: set = set()
            for s, cnt in per_site.items():
                pool = docs_by_site[s]
                fake |= set(rng.sample(pool, min(cnt, len(pool))))
            nulls.append(len(fake & docs_cc))
        mean = sum(nulls) / len(nulls)
        var = sum((x - mean) ** 2 for x in nulls) / len(nulls)
        sd = var ** 0.5
        ge = sum(1 for x in nulls if x >= obs)
        p_perm = max(ge, 1) / len(nulls)
        z = (obs - mean) / sd if sd else float("inf")
        ok = p_perm < fam_alpha
        (promoted if ok else demoted).append((cc, sign, obs, p_perm))
        print(f"  {cc + ' <-> ' + sign:26s} {obs:4d} {mean:10.1f} {sd:8.2f} {max(nulls):9d} "
              f"{p_perm:8.1e} {z:7.1f}  {'<-- survives' if ok else ''}")

    print(f"\n  survive the stratified permutation at family alpha: {len(promoted)}")
    for cc, sign, obs, p in promoted:
        print(f"    {cc} <-> {sign}: {obs} documents, p_perm={p:.1e}")
    if demoted:
        print(f"  do not: {', '.join(f'{cc} <-> {sign} (p={p:.1e})' for cc, sign, _, p in demoted)}")
    print("  Caveat: these pairs were SELECTED by the document-level test, then re-tested"
          " here. The selection step inflates them, which is why the family alpha used is the"
          " full 122-test threshold rather than a smaller one. Treat as candidates still.")

    # ── are the survivors independent, or one entry template? ──
    # The AB 82<->LIVESTOCK retraction was exactly this failure: both hits from one inscription.
    # Here the question is whether the six LIVESTOCK signs are facets of a single formula. They
    # are neither: most documents carry at most one of them, and no pair exceeds Jaccard 0.52.
    live_signs = [s for cc, s, _, _ in promoted if cc == "LIVESTOCK"]
    docs_live = docs_by_commodity["LIVESTOCK"]
    present = {s: sign_docs[s] & docs_live for s in live_signs}
    hist = Counter(sum(1 for s in live_signs if d in present[s]) for d in docs_live)
    print(f"\nindependence check among the {len(live_signs)} LIVESTOCK survivors "
          f"({len(docs_live)} documents):")
    for k in sorted(hist):
        print(f"  {k} of {len(live_signs)} signs present: {hist[k]:3d} documents "
              f"({hist[k]/len(docs_live):4.0%})")
    pairs = []
    for a, b in ((x, y) for i, x in enumerate(live_signs) for y in live_signs[i + 1:]):
        u = present[a] | present[b]
        if u:
            pairs.append((len(present[a] & present[b]) / len(u), a, b))
    pairs.sort(reverse=True)
    print("  highest pairwise overlap (Jaccard): "
          + ", ".join(f"{a}/{b}={j:.2f}" for j, a, b in pairs[:3]))
    print(f"  -> not one template ({hist.get(0, 0) + hist.get(1, 0)} documents carry at most "
          f"one of them) and not independent either; reported as a SET with this matrix, not as "
          f"{len(promoted)} discoveries.")

    # ── where do the commodity documents live? (the toponym lesson) ──
    print("\nsite concentration of the two claims' documents:")
    for cc in ("LIVESTOCK", "WINE"):
        docs = [r for r in rows if (r.get("commodity_class") or "").strip() == cc]
        sites = Counter(r["site"].split(" - ")[0] for r in docs)
        print(f"  {cc}: {dict(sites.most_common(4))}")
    for sign in ("AB 28", "AB 30"):
        d = set(sign_docs.get(sign, set()))
        in_pop = d & all_docs
        sites = Counter(site_of[x] for x in in_pop if x in site_of)
        print(f"  {sign}: {len(d)} documents corpus-wide, {len(in_pop)} in the population; "
              f"{dict(sites.most_common(4))}")


if __name__ == "__main__":
    main()
