"""Is the vowel identifiable in principle, given the consonant series?

Chain of findings (see lb_sandbox_findings.md):
  * ingest correct (round-trip 4794/4794)
  * Kober channel is degenerate at both extremes: sparse graph → no votes,
    dense graph (60k triples / 76 signs) → votes from ~71 partners = noise
  * individual score terms rank the true value top-1 when ties are allowed
    (morph 65%, entropy 59%, prefix 69%) but NO aggregator ever produces a
    unique argmax, so nothing is ever recovered

That last point says the shipped estimator has no *resolution*: it is a
corpus-level statistic, not a per-sign likelihood. This script asks the cleanest
possible version of the remaining question, deliberately giving the method the
series for free (oracle knowledge, diagnostic only):

    given the series, can a per-occurrence estimator pick the vowel?

Estimator: local log-likelihood over the sign's own occurrences, restricted to
anchor-valued neighbours, with a PMI-style base-rate correction
(`log P(next|v) - log P(v)`) so that frequent values do not win by frequency.

Reported for three estimators:
  local-LL       — Σ log P(next|v) + log P(v|prev)
  local-PMI      — same, minus log P(v) (base-rate corrected)
  shipped        — the pipeline's own score_completion total, same candidates

Usage: uv run python pipeline/local_vowel_test.py --language linear-b
"""

from __future__ import annotations

import argparse
import logging
import math
import random
from collections import Counter
from pathlib import Path

from pipeline.oracle_diagnose import CONFIGS, build
from pipeline.ventris.complete import CONS_SERIES_MAP, VOWEL_COLUMNS

logger = logging.getLogger("local_vowel")

SERIES_CONS = {"LABIAL": "pm", "DENTAL": "tdn", "VELAR": "kq", "SIBILANT": "sz",
               "LIQUID": "rl", "PALATAL": "j", "SEMIVOWEL": "w"}


def model(seqs, anchor_val, k=0.5):
    uni, bi = Counter(), Counter()
    for seq in seqs:
        vals = [anchor_val.get(s) for s in seq]
        for v in vals:
            if v:
                uni[v] += 1
        for a, b in zip(vals, vals[1:]):
            if a and b:
                bi[(a, b)] += 1
    V = max(len(uni), 1)
    return uni, bi, V


def occurrences(seqs, bid, anchor_val):
    occ = []
    for seq in seqs:
        for i, s in enumerate(seq):
            if s != bid:
                continue
            prev = anchor_val.get(seq[i - 1]) if i > 0 else None
            nxt = anchor_val.get(seq[i + 1]) if i + 1 < len(seq) else None
            if prev or nxt:
                occ.append((prev, nxt))
    return occ


def local_ll(occ, v, uni, bi, V, k=0.5, pmi=False):
    ll = 0.0
    for prev, nxt in occ:
        if prev:
            ll += math.log((bi.get((prev, v), 0) + k) / (uni.get(prev, 0) + k * V))
        if nxt:
            ll += math.log((bi.get((v, nxt), 0) + k) / (uni.get(v, 0) + k * V))
    if pmi:
        tot = sum(uni.values())
        pv = (uni.get(v, 0) + k) / (tot + k * V)
        ll -= len(occ) * math.log(pv) * (1 if occ else 0)
    return ll


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--language", default="linear-b", choices=list(CONFIGS))
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = build(args.language)
    seqs = list(c.inscriptions.values())
    confirmed = c.confirmed
    bids = sorted(confirmed)
    rng = random.Random(0)

    print(f"language={args.language} anchors={len(bids)}")
    st = Counter()

    for _ in range(args.trials):
        hs = rng.sample(bids, min(args.hidden, len(bids)))
        eff = {b: v for b, v in confirmed.items() if b not in hs}
        uni, bi, V = model(seqs, eff)
        truth_all = {b: confirmed[b] for b in hs}

        for bid in hs:
            truth = confirmed[bid]
            series = CONS_SERIES_MAP.get(truth, "?")
            if series in ("?", "VOWEL"):
                continue
            # candidates: the TRUE series x vowels (oracle-given series)
            cands = [f"{cons}{v}" for cons in SERIES_CONS.get(series, "")
                     for v in VOWEL_COLUMNS]
            occ = occurrences(seqs, bid, eff)
            if truth not in cands:
                continue
            st["n"] += 1
            st["no_ctx"] += int(not occ)
            st["mean_occ"] += len(occ)

            # 1. local log-likelihood
            for cond, pmi in (("ll", False), ("pmi", True)):
                sc = [(local_ll(occ, cd, uni, bi, V, pmi=pmi), cd) for cd in cands]
                best = max(s for s, _ in sc)
                arg = [cd for s, cd in sc if abs(s - best) < 1e-12]
                st[f"{cond}_top1"] += int(len(arg) == 1 and arg[0] == truth)
                st[f"{cond}_inarg"] += int(truth in arg)

            # 2. shipped scorer on the same reduced candidate set
            vals = dict(truth_all)
            sc = []
            for cd in cands:
                vals[bid] = cd
                m, e, pr, k = c.score_completion(
                    vals, confirmed_override=eff, uncertain_override=hs,
                    sample_size=50)
                sc.append((0.45 * m + 0.15 * e + 0.10 * pr + 0.30 * k, cd))
            best = max(s for s, _ in sc)
            arg = [cd for s, cd in sc if s == best]
            st["shipped_top1"] += int(len(arg) == 1 and arg[0] == truth)
            st["shipped_inarg"] += int(truth in arg)

    n = max(st["n"], 1)
    chance = 1.0 / max(len([x for x in SERIES_CONS.get("DENTAL", "")]) * len(VOWEL_COLUMNS), 1)
    print(f"\ndraws with usable series: {st['n']}  "
          f"mean occurrences {st['mean_occ']/n:.1f}  "
          f"no anchor context for {st['no_ctx']} ({st['no_ctx']/n:.1%})")
    print(f"chance for a 5-vowel choice after series filter ~ {chance:.1%}\n")
    print(f"{'estimator':34s} {'unique top1':>12s} {'in argmax':>10s} {'lift':>7s}")
    for cond, label in (("ll", "local log-likelihood"),
                        ("pmi", "local PMI (base-rate corrected)"),
                        ("shipped", "shipped score_completion total")):
        print(f"{label:34s} {st[f'{cond}_top1']/n:12.1%} {st[f'{cond}_inarg']/n:10.1%} "
              f"{(st[f'{cond}_top1']/n)/chance:6.2f}x")
    c.close()


if __name__ == "__main__":
    main()