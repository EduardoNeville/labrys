"""Oracle failure attribution: where does a 0.00x recovery come from?

Three separable failure modes, measured independently:

  A. CORPUS    — round-trip the DB back to transliteration and diff against the
                 source. If this fails, the ingest is wrong.
  B. CANDIDATES— is the true value even IN get_candidates() for a hidden sign?
                 If not, recovery is impossible by construction (constraint bug).
  C. SCORE     — with every other sign set to its true value, what rank does the
                 true value get? Also per-term, and a flatness measure. If the
                 true value ranks first but the search returns something else,
                 the bug is in the search, not the objective.
  D. SEARCH    — a stronger local search (multi-pass coordinate ascent from
                 several inits) on the same objective: does recovery improve?

Usage:
    uv run python pipeline/oracle_diagnose.py --language linear-b
    uv run python pipeline/oracle_diagnose.py --language linear-a
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger("oracle_diagnose")

REPO = Path(__file__).resolve().parent.parent

CONFIGS = {
    "linear-b": dict(
        db=REPO / "languages/linear-b/data/database/linear-b.db",
        grid=REPO / "languages/linear-b/answer_key.csv",
        kober=REPO / "languages/linear-b/data/analysis/kober/triple_patterns.csv",
        freq=REPO / "languages/linear-b/data/analysis/frequency_constraints/constrained_candidates.csv",
        raw=REPO / "languages/linear-b/data/raw/tablets.csv",
        raw_delim=";",
        ab68=False,
    ),
    "linear-a": dict(
        db=REPO / "data/database/lineara_full.db",
        grid=REPO / "data/analysis/bootstrapping/expanded_grid.csv",
        kober=REPO / "data/analysis/kober/triple_patterns.csv",
        freq=REPO / "data/analysis/frequency_constraints/constrained_candidates.csv",
        raw=None,
        raw_delim=None,
        ab68=True,
    ),
}


def build(lang: str):
    from pipeline.ventris.complete import VentrisGridCompleter

    c = CONFIGS[lang]
    return VentrisGridCompleter(
        db_path=str(c["db"]), expanded_grid_path=str(c["grid"]),
        kober_triples_path=str(c["kober"]), freq_constraints_path=str(c["freq"]),
        ab68_override=c["ab68"],
    )


# ── A. corpus round-trip ─────────────────────────────────────────────────────

def check_roundtrip(lang: str) -> None:
    c = CONFIGS[lang]
    if not c["raw"]:
        print("A. round-trip: skipped (no raw source configured)")
        return
    from pipeline.lb_ingest import parse_corpus, lb_reference

    value_of = {e["sign_id"]: v for v, e in lb_reference().items()}
    inscriptions, _, _, _ = parse_corpus()

    conn = sqlite3.connect(str(c["db"]))
    db_seqs = {}
    for iid, seq, bid in conn.execute(
        "SELECT i.gorila_id, s.sequence, s.bennett_id FROM signs s "
        "JOIN inscriptions i ON i.id = s.inscription_id ORDER BY i.id, s.sequence"
    ):
        db_seqs.setdefault(iid, []).append(bid)
    conn.close()

    total = matched = 0
    length_ok = 0
    for insc in inscriptions:
        parsed = [s["sign_id"] for w in insc["words"] for s in w]
        db = db_seqs.get(insc["id"], [])
        if [x for x in parsed] == [x for x in db]:
            length_ok += 1
        # value round-trip for named signs
        for sign in [s for w in insc["words"] for s in w]:
            if sign["sign_id"] not in value_of:
                continue
            total += 1
            if value_of[sign["sign_id"]] == sign["translit"]:
                matched += 1
    print(f"A. round-trip: {length_ok}/{len(inscriptions)} inscriptions identical "
          f"to the DB; {matched}/{total} named-sign tokens map back to their own "
          f"source transliteration ({matched/max(total,1):.4f})")


# ── B/C. candidates + score gradient ─────────────────────────────────────────

def check_gradient(completer, trials: int, hidden: int) -> dict:
    confirmed = completer.confirmed
    bids = sorted(confirmed)
    rng = random.Random(0)
    st = Counter()
    term_rank = defaultdict(list)     # term -> rank percentile of the true value
    term_top1 = Counter()
    n_links = []

    for t in range(trials):
        hs = rng.sample(bids, min(hidden, len(bids)))
        eff = {b: v for b, v in confirmed.items() if b not in hs}
        truth_all = {b: confirmed[b] for b in hs}

        for bid in hs:
            truth = confirmed[bid]
            cands = completer.get_candidates(bid, confirmed=eff)
            st["signs"] += 1
            st["truth_in_cands"] += int(truth in cands)
            st["singleton"] += int(len(cands) == 1)
            st["cand_total"] += len(cands)
            n_links.append(len(completer.kober_clinks.get(bid, ())))

            vals = dict(truth_all)
            rows = []
            for cand in cands:
                vals[bid] = cand
                m, e, p, k = completer.score_completion(
                    vals, confirmed_override=eff, uncertain_override=hs,
                    sample_size=50,
                )
                rows.append((cand, m, e, p, k, 0.45 * m + 0.15 * e + 0.10 * p + 0.30 * k))

            totals = {r[5] for r in rows}
            st["flat"] += int(len(totals) == 1)
            if truth not in cands:
                st["truth_absent_excluded"] += 1
                continue

            for idx, name in [(1, "morph"), (2, "entropy"), (3, "prefix"),
                              (4, "kober"), (5, "TOTAL")]:
                vals_arr = [r[idx] for r in rows]
                tval = [r[idx] for r in rows if r[0] == truth][0]
                better = sum(1 for v in vals_arr if v > tval)
                term_rank[name].append(better / max(len(rows) - 1, 1))
                if better == 0:
                    term_top1[name] += 1

    n = max(st["signs"], 1)
    print(f"\nB. candidate generator ({st['signs']} hidden-sign draws)")
    print(f"   true value IS in candidate list : {st['truth_in_cands']}/{n} "
          f"({st['truth_in_cands']/n:.1%})")
    print(f"   singleton candidate lists       : {st['singleton']} "
          f"({st['singleton']/n:.1%})")
    print(f"   mean candidate-list size        : {st['cand_total']/n:.1f}")
    print(f"   flat score (all candidates tie) : {st['flat']} ({st['flat']/n:.1%})")
    print(f"   kober links per hidden sign     : mean {sum(n_links)/n:.1f}, "
          f"zero for {sum(1 for x in n_links if x == 0)}/{n}")

    print(f"\nC. score gradient — rank of the TRUE value with everything else true")
    print(f"   (0.00 = best possible, 1.00 = worst; 0.5 = coin flip)")
    for name in ["morph", "entropy", "prefix", "kober", "TOTAL"]:
        arr = term_rank[name]
        if not arr:
            continue
        print(f"   {name:8s} mean rank {sum(arr)/len(arr):.3f}   "
              f"top-1 ({term_top1[name]}/{len(arr)} = {term_top1[name]/len(arr):.1%})")
    st["term_rank"] = dict(term_rank)
    st["term_top1"] = dict(term_top1)
    return st


# ── D. stronger search on the same objective ─────────────────────────────────

def stronger_search(completer, trials: int, hidden: int, passes: int = 3) -> dict:
    """Multi-pass coordinate ascent: repeat until no change (the shipped
    _greedy_restore does a single pass, so signs optimised early never see the
    final values of the others)."""
    confirmed = completer.confirmed
    bids = sorted(confirmed)
    rng = random.Random(0)
    recovered = total = 0
    for t in range(trials):
        hs = rng.sample(bids, min(hidden, len(bids)))
        eff = {b: v for b, v in confirmed.items() if b not in hs}
        cands = {b: completer.get_candidates(b, confirmed=eff) for b in hs}
        vals = {b: cands[b][0] for b in hs}
        for _ in range(passes):
            changed = False
            for bid in sorted(hs, key=lambda b: len(cands[b])):
                best = vals[bid]
                best_s = -1.0
                for cand in cands[bid]:
                    vals[bid] = cand
                    m, e, p, k = completer.score_completion(
                        vals, confirmed_override=eff, uncertain_override=hs,
                        sample_size=50)
                    s = 0.45 * m + 0.15 * e + 0.10 * p + 0.30 * k
                    if s > best_s:
                        best_s, best = s, cand
                changed |= (best != vals[bid])
                vals[bid] = best
            if not changed:
                break
        for b in hs:
            total += 1
            recovered += int(vals[b] == confirmed[b])
    return {"recovered": recovered, "total": total,
            "rate": recovered / max(total, 1)}


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--language", default="linear-b", choices=list(CONFIGS))
    p.add_argument("--trials", type=int, default=4)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    print(f"=== oracle failure attribution: {args.language} ===")
    check_roundtrip(args.language)
    c = build(args.language)
    print(f"\ncorpus: {len(c.inscriptions)} inscriptions, {len(c.confirmed)} anchors, "
          f"{len(c.uncertain)} uncertain; kober link graph: "
          f"{len(c.kober_clinks)} signs with C-links")
    check_gradient(c, args.trials, args.hidden)
    s = stronger_search(c, args.trials, args.hidden)
    print(f"\nD. multi-pass coordinate ascent on the same objective: "
          f"{s['recovered']}/{s['total']} recovered ({s['rate']:.3f})")
    c.close()


if __name__ == "__main__":
    main()