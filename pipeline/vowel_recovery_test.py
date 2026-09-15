"""Is the VOWEL recoverable? Local bigram likelihood vs the shipped estimator.

Diagnosis so far (oracle_diagnose.py, aggregator_bakeoff.py):
  * the corpus round-trips 100% — ingest is correct
  * the true value is in the candidate list 87.5% of the time, mean list size 70
  * the Kober term puts the truth in its argmax set 90% of the time (series ok)
  * NO aggregator ever makes truth the unique argmax (top1 = 0.0%)

So the scorer's job splits in two: identify the consonant series (Kober does
this) and identify the vowel. This script tests the vowel directly, with the
estimator the shipped scorer *tried* to use: instead of a global held-out
cross-entropy over 50 texts, score each candidate by the likelihood of the
sign's own occurrences given only anchor values.

    score(v) = Σ_occ [ log P(next | v) + log P(v | prev) ]

with P estimated from anchor-valued bigrams only, add-k smoothed.

Two reported conditions:
  raw      — all candidates compete
  series   — two-stage: Kober series filter first, then local likelihood
             (this is the "repaired pipeline" proposal)

Usage: uv run python pipeline/vowel_recovery_test.py --language linear-b
"""

from __future__ import annotations

import argparse
import logging
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.oracle_diagnose import CONFIGS, build
from pipeline.ventris.complete import CONS_SERIES_MAP, vowel_of

logger = logging.getLogger("vowel_test")


def anchor_model(seqs: list, anchor_val: dict, k: float = 0.5):
    """Unigram/bigram counts over anchor-valued signs only."""
    uni = Counter()
    bi = Counter()
    for seq in seqs:
        vals = [anchor_val.get(s) for s in seq]
        for v in vals:
            if v:
                uni[v] += 1
        for a, b in zip(vals, vals[1:]):
            if a and b:
                bi[(a, b)] += 1
    vocab = sorted(uni)
    V = max(len(vocab), 1)
    total = sum(uni.values())
    return uni, bi, V, total


def local_scores(seqs, bid, anchor_val, uni, bi, V, cands, k: float = 0.5):
    """Local log-likelihood per candidate for one sign."""
    # occurrences of bid with anchor neighbours
    occ = []
    for seq in seqs:
        for i, s in enumerate(seq):
            if s != bid:
                continue
            prev = anchor_val.get(seq[i - 1]) if i > 0 else None
            nxt = anchor_val.get(seq[i + 1]) if i + 1 < len(seq) else None
            if prev or nxt:
                occ.append((prev, nxt))
    if not occ:
        return None
    out = []
    for v in cands:
        ll = 0.0
        for prev, nxt in occ:
            if prev:
                # P(v | prev)
                num = bi.get((prev, v), 0) + k
                den = uni.get(prev, 0) + k * V
                ll += math.log(num / den)
            if nxt:
                num = bi.get((v, nxt), 0) + k
                den = uni.get(v, 0) + k * V
                ll += math.log(num / den)
        out.append(ll)
    return out, len(occ)


def _pct_ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: -vals[i])
    n = len(vals)
    out = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        pct = 1.0 - (((i + j) / 2) / max(n - 1, 1))
        for t in range(i, j + 1):
            out[order[t]] = pct
        i = j + 1
    return out


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

    print(f"language={args.language} anchors={len(bids)} "
          f"inscriptions={len(seqs)} sign_tokens={sum(len(s) for s in seqs)}")

    st = Counter()
    for cond in ("raw", "series"):
        st[f"{cond}_top1"] = 0
        st[f"{cond}_inarg"] = 0
        st[f"{cond}_n"] = 0
        st[f"{cond}_rank"] = 0.0

    for _ in range(args.trials):
        hs = rng.sample(bids, min(args.hidden, len(bids)))
        eff = {b: v for b, v in confirmed.items() if b not in hs}
        uni, bi, V, _ = anchor_model(seqs, eff)
        for bid in hs:
            truth = confirmed[bid]
            cands = c.get_candidates(bid, confirmed=eff)
            if truth not in cands:
                continue
            res = local_scores(seqs, bid, eff, uni, bi, V, cands)
            if res is None:
                continue
            vals, nocc = res

            # raw
            for cond, keep in (("raw", list(range(len(cands)))),):
                sub = [(cands[i], vals[i]) for i in keep]
                best = max(v for _, v in sub)
                arg = [x for x, v in sub if v == best]
                st["raw_n"] += 1
                if truth in arg:
                    st["raw_inarg"] += 1
                    if len(arg) == 1:
                        st["raw_top1"] += 1
                rr = _pct_ranks([v for _, v in sub])
                st["raw_rank"] += rr[cands.index(truth)] if truth in cands else 0.0

            # two-stage: kober series filter, then local likelihood on the vowel
            kseries = CONS_SERIES_MAP.get(truth, "?")
            partners = c.kober_clinks.get(bid, set())
            votes = Counter()
            for pn in partners:
                if pn in eff:
                    s = CONS_SERIES_MAP.get(eff[pn], "")
                    if s and s != "VOWEL":
                        votes[s] += 1
            if votes:
                thr = max(2, max(votes.values()) // 2)
                allowed = {s for s, n in votes.items() if n >= thr}
            else:
                allowed = None
            idx = [i for i, cd in enumerate(cands)
                   if allowed is None or CONS_SERIES_MAP.get(cd, "?") in allowed
                   or CONS_SERIES_MAP.get(cd, "?") == "VOWEL"]
            if not idx:
                continue
            sub = [(cands[i], vals[i]) for i in idx]
            best = max(v for _, v in sub)
            arg = [x for x, v in sub if v == best]
            st["series_n"] += 1
            if truth in arg:
                st["series_inarg"] += 1
                if len(arg) == 1:
                    st["series_top1"] += 1
            if truth in [x for x, _ in sub]:
                rr = _pct_ranks([v for _, v in sub])
                st["series_rank"] += rr[[x for x, _ in sub].index(truth)]
            st["series_series_ok"] = st.get("series_series_ok", 0) + int(
                allowed is None or kseries in allowed)

    print(f"\n{'condition':38s} {'unique top1':>12s} {'in argmax':>10s} {'mean rank':>10s}")
    for cond, label in (("raw", "local likelihood, all candidates"),
                        ("series", "kober series filter -> local likelihood")):
        n = st[f"{cond}_n"]
        if not n:
            continue
        print(f"{label:38s} {st[f'{cond}_top1']/n:12.1%} "
              f"{st[f'{cond}_inarg']/n:10.1%} {st[f'{cond}_rank']/n:10.3f}")
    if st.get("series_n"):
        print(f"\nkober series filter kept the true series: "
              f"{st.get('series_series_ok',0)}/{st['series_n']} "
              f"({st.get('series_series_ok',0)/st['series_n']:.1%})")
    c.close()


if __name__ == "__main__":
    main()