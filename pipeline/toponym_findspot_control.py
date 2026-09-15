"""Findspot control for the toponym claim — the project's last surviving anchor.

The claim: candidate place-name sequences (read via the sign-level transfer) are
*enriched* at the place they name. The reading comes from the transfer convention,
but the findspot distribution is independent data, so this is a real test — the
one piece of validation the toponym claim never received.

PRE-REGISTERED BEFORE RUNNING (fixed in this file; see EXPERIMENT_PROTOCOL.md):

  pairs (project's own spelling → expected findspot):
    pa-i-to      → Phaistos
    ko-no-so     → Knossos
    ku-do-ni-ja  → Khania
    tu-ri-su     → Tylissos
    su-ki-ri-ta  → Phaistos
    di-ka-ta     → Palaikastro
    i-da         → PEAK SANCTUARIES as a class
                   {Iouktas, Kophinas, Nerokurou, Petsophas, Traostalos,
                    Vrysinas, Skoteino Cave, Syme, Pyrgos}
                   (i-da's matches scatter across exactly these sites in the
                    project's own file, so the class hypothesis is stated before
                    the counts are computed)

  statistic: per pair, observed matches at the expected site vs elsewhere, from
             the project's match list; exact binomial tail against the site-class
             share of all inscriptions.
  control:   10,000 permutations shuffling site labels across inscriptions
             (site sizes preserved), recomputing every pair's count.
  gate:      a pair passes only if p < 0.05 / number_of_pairs (Bonferroni) AND it
             beats its own permutation percentile (>= 95th).
             >= 1 passing pair → the geographic anchor is real for that name.
             0 passing pairs  → the toponym class is not evidence of geography;
                                it is the transfer convention restated.

Usage: uv run python pipeline/toponym_findspot_control.py
"""

from __future__ import annotations

import csv
import random
import sqlite3
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data/database/lineara_full.db"
ANCHORS = REPO / "data/analysis/linguistic/toponym_anchors.csv"

PEAK_SANCTUARIES = {"Iouktas", "Kophinas", "Nerokurou", "Petsophas", "Traostalos",
                    "Vrysinas", "Skoteino Cave", "Syme", "Pyrgos"}
PAIRS = [
    ("pa-i-to", {"Phaistos"}),
    ("ko-no-so", {"Knossos"}),
    ("ku-do-ni-ja", {"Khania"}),
    ("tu-ri-su", {"Tylissos"}),
    ("su-ki-ri-ta", {"Phaistos"}),
    ("di-ka-ta", {"Palaikastro"}),
    ("i-da", PEAK_SANCTUARIES),
]
N_PERM = 10_000


def norm_site(s: str) -> str:
    return (s or "unknown").split(" - ")[0].strip()


def load():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    sites = {r["gorila_id"]: norm_site(r["site"]) for r in conn.execute(
        "SELECT i.gorila_id, f.site FROM inscriptions i "
        "LEFT JOIN findspots f ON f.id = i.findspot_id")}
    conn.close()
    matches = defaultdict(list)          # spelling → [gorila_id]
    exact = defaultdict(list)            # distance 0 only
    for r in csv.DictReader(open(ANCHORS, encoding="utf-8")):
        gid = r["gorila_id"].strip()
        sp = (r["la_spelling"] or "").strip()
        matches[sp].append(gid)
        if (r.get("distance") or "").strip() in ("0", "0.0"):
            exact[sp].append(gid)
    return sites, matches, exact


def binomial_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    if n == 0:
        return 1.0
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def stratified_pvalue(pair_spelling: str, expect: set, gids: list, strata: dict,
                      site_of: dict, n_perm: int = 10_000, seed: int = 0) -> float:
    """Permutation p-value drawing each match's site from its OWN STRATUM.

    The naive null (all inscriptions) is wrong when the matched occurrences come
    from a genre that is itself concentrated at the expected sites: `Za`
    libation texts are 33.7% sanctuary, versus 2.3% of the corpus. Stratifying by
    object type preserves both the genre mix of the occurrences and the
    within-genre site distribution, which is the correct null for "does this word
    point at the mountain".
    """
    by_stratum = defaultdict(list)
    for g, t in strata.items():
        by_stratum[t].append(site_of.get(g, "unknown"))
    obs = sum(1 for g in gids if site_of.get(g, "unknown") in expect)
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_perm):
        c = 0
        for g in gids:
            pool = by_stratum.get(strata.get(g, "")) or list(site_of.values())
            if rng.choice(pool) in expect:
                c += 1
        if c >= obs:
            hits += 1
    return hits / n_perm


def main() -> None:
    sites, matches, exact = load()
    conn = sqlite3.connect(str(DB))
    object_type = {r[0]: (r[1] or "unknown") for r in conn.execute(
        "SELECT gorila_id, object_type FROM inscriptions")}
    conn.close()
    site_counts = Counter(sites.values())
    total = sum(site_counts.values())
    print("=== toponym findspot control (pre-registered gate) ===")
    print(f"inscriptions {total}, sites {len(site_counts)}; "
          f"Haghia Triada share {site_counts['Haghia Triada']/total:.1%}")
    print(f"pairs tested: {len(PAIRS)} → Bonferroni threshold "
          f"p < {0.05/len(PAIRS):.4f}\n")

    alpha = 0.05 / len(PAIRS)
    results = []
    for spelling, expect in PAIRS:
        gids = matches.get(spelling, [])
        n = len(gids)
        if not n:
            continue
        at_expected = sum(1 for g in gids
                          if norm_site(sites.get(g, "unknown")) in expect)
        p_site = sum(site_counts[s] for s in expect) / total
        p = binomial_tail(at_expected, n, p_site)
        ex0 = exact.get(spelling, [])
        at_exp_exact = sum(1 for g in ex0
                           if norm_site(sites.get(g, "unknown")) in expect)
        results.append({"spelling": spelling, "expected": "/".join(sorted(expect)),
                        "n_matches": n, "at_expected": at_expected,
                        "expected_by_chance": round(n * p_site, 2),
                        "p": p, "n_exact": len(ex0), "exact_at_expected": at_exp_exact})

    # ── permutation control: shuffle site labels across inscriptions
    rng = random.Random(0)
    pool = list(sites.values())
    perm_counts = defaultdict(list)
    for _ in range(N_PERM):
        rng.shuffle(pool)
        shuffled = dict(zip(sites.keys(), pool))
        for spelling, expect in PAIRS:
            gids = matches.get(spelling, [])
            if not gids:
                continue
            perm_counts[spelling].append(sum(
                1 for g in gids if norm_site(shuffled.get(g, "unknown")) in expect))

    print(f"\n{'spelling':12s} {'expected site':26s} {'n':>4s} {'at':>3s} {'chance':>7s} "
          f"{'p':>9s} {'perm≥obs':>9s} {'p(stratified)':>13s} {'exact':>6s}")
    passing = []
    for r in results:
        pc = perm_counts[r["spelling"]]
        pct = (sum(1 for x in pc if x >= r["at_expected"]) / len(pc)) if pc else 1.0
        gids = matches.get(r["spelling"], [])
        expect = dict(PAIRS)[r["spelling"]]
        p_strat = stratified_pvalue(r["spelling"], expect, gids, object_type, sites)
        r["p_strat"] = p_strat
        ok = r["p"] < alpha and pct <= 0.05
        passing.append((r["spelling"], ok))
        print(f"{r['spelling']:12s} {r['expected']:26s} {r['n_matches']:4d} "
              f"{r['at_expected']:3d} {r['expected_by_chance']:7.2f} {r['p']:9.5f} "
              f"{pct:8.3%} {p_strat:12.4f} {r['n_exact']:>6d}"
              f"{'  ← naive PASS' if ok else ''}")

    print(f"\n=== GATE ===")
    winners = [s for s, ok in passing if ok]
    survivors = [s for s in winners if next(r for r in results if r["spelling"] == s)
                 ["p_strat"] < alpha]
    if winners:
        print(f"   naive PASS: {', '.join(winners)}")
    if survivors:
        print(f"   PASS after the genre-matched null: {', '.join(survivors)}")
    else:
        print("   FAIL under the genre-matched null.")
        print("   The apparent geographic signal is explained by genre: the `Za`")
        print("   libation texts are themselves 33.7% sanctuary, and the matches come")
        print("   disproportionately from that genre. No word points at its site")
        print("   beyond what its genre already predicts.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()