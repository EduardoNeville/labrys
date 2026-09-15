"""Do frame links actually identify series and vowel? (Repaired-constraint feasibility.)

Kober's method, stated correctly:
  * two signs that share the same FOLLOWING sign  → same CONSONANT (C-link)
  * two signs that share the same PRECEDING sign → same VOWEL    (V-link)

The shipped pipeline threw that away (unweighted cliques, both graphs identical,
global threshold). Before rebuilding it, measure the ceiling: using only partners
whose values are known, how often does the weighted partner vote recover the
hidden sign's true series / vowel?

Also measures a distributional channel that needs no links at all:
  * does the hidden sign's context profile (which signs precede / follow it)
    match the profile of the anchor sign carrying a given candidate value?

Usage:
    uv run python pipeline/frame_link_test.py --language linear-b
    uv run python pipeline/frame_link_test.py --language linear-a
"""

from __future__ import annotations

import argparse
import logging
import random
from collections import Counter, defaultdict
from itertools import combinations

from pipeline.oracle_diagnose import CONFIGS, build
from pipeline.ventris.complete import CONS_SERIES_MAP, vowel_of
from pipeline.phonetics import series_of

logger = logging.getLogger("frame_link_test")


def build_links(seqs):
    """Weighted frame links: weight = number of DISTINCT shared frame signs."""
    follow = defaultdict(set)   # x -> {y : (x,y) seen}
    precede = defaultdict(set)  # y -> {x : (x,y) seen}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            follow[a].add(b)
            precede[b].add(a)

    c_w = defaultdict(int)  # consonant-candidate: share a FOLLOWING sign
    for f, xs in precede.items():
        for a, b in combinations(sorted(xs), 2):
            c_w[(a, b)] += 1
            c_w[(b, a)] += 1

    v_w = defaultdict(int)  # vowel-candidate: share a PRECEDING sign
    for p, ys in follow.items():
        for a, b in combinations(sorted(ys), 2):
            v_w[(a, b)] += 1
            v_w[(b, a)] += 1
    return follow, precede, c_w, v_w


def pairwise_relations(follow, precede, known) -> None:
    """Unconditional pairwise test: does sharing a frame sign predict agreement?

    Uses every sign whose value is known (no hiding) — this measures an intrinsic
    property of the corpus, not a recovery result. Chance = marginal agreement
    rate (the probability that two independently drawn values agree), which is the
    correct null for this question.
    """
    from itertools import combinations

    def pairs_sharing_following():
        # for each sign f, all pairs of signs that both precede f
        out = []
        for f, xs in precede.items():
            out.extend(combinations(sorted(xs), 2))
        return out

    def pairs_sharing_preceding():
        out = []
        for p, ys in follow.items():
            out.extend(combinations(sorted(ys), 2))
        return out

    def attribute(val, attr):
        return series_of(val) if attr == "cons" else vowel_of(val)

    def marginal_chance(attr):
        c = Counter(attribute(v, attr) for v in known.values())
        c.pop("?", None)
        n = sum(c.values())
        return sum((x / n) ** 2 for x in c.values()) if n else 0.0

    def measure(pairs, attr):
        ok = tot = 0
        for x, y in pairs:
            if x in known and y in known:
                ax, ay = attribute(known[x], attr), attribute(known[y], attr)
                if "?" in (ax, ay):
                    continue
                tot += 1
                ok += int(ax == ay)
        return ok, tot

    print("\n--- unconditional pairwise relations ---")
    for label, pairs in (("share FOLLOWING sign", pairs_sharing_following()),
                         ("share PRECEDING sign", pairs_sharing_preceding())):
        for attr, name in (("cons", "same consonant"), ("vowel", "same vowel")):
            ok, tot = measure(pairs, attr)
            ch = marginal_chance(attr)
            if tot:
                print(f"  {label:20s} → {name:14s}: {ok/tot:.3f}  "
                      f"(chance {ch:.3f}, ratio {(ok/tot)/ch:.2f}×, n={tot})")


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--language", default="linear-b", choices=list(CONFIGS))
    p.add_argument("--trials", type=int, default=4)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = build(args.language)
    seqs = list(c.inscriptions.values())
    confirmed = c.confirmed
    bids = sorted(confirmed)
    follow, precede, c_w, v_w = build_links(seqs)
    print(f"language={args.language} anchors={len(bids)} signs_in_corpus="
          f"{sum(len(s) for s in seqs)} linked_signs={len({k[0] for k in c_w})}")

    rng = random.Random(0)
    st = Counter()
    per = Counter()
    for _ in range(args.trials):
        hs = set(rng.sample(bids, min(args.hidden, len(bids))))
        known = {b: v for b, v in confirmed.items() if b not in hs}  # anchors only

        for bid in hs:
            truth = confirmed[bid]
            t_ser, t_vow = CONS_SERIES_MAP.get(truth, "?"), vowel_of(truth)
            if t_ser in ("?", "VOWEL") or t_vow == "?":
                continue
            st["n"] += 1

            # ── C-link vote (series) over KNOWN partners only ──
            votes = Counter()
            for other, v in known.items():
                w = c_w.get((bid, other), 0)
                if w:
                    s = CONS_SERIES_MAP.get(v, "?")
                    if s not in ("?", "VOWEL"):
                        votes[s] += w
            if votes:
                st["c_vote"] += 1
                st["c_ok"] += int(votes.most_common(1)[0][0] == t_ser)
                st["c_in_top2"] += int(t_ser in [s for s, _ in votes.most_common(2)])

            # ── V-link vote (vowel) over KNOWN partners only ──
            vv = Counter()
            for other, v in known.items():
                w = v_w.get((bid, other), 0)
                if w:
                    vo = vowel_of(v)
                    if vo != "?":
                        vv[vo] += w
            if vv:
                st["v_vote"] += 1
                st["v_ok"] += int(vv.most_common(1)[0][0] == t_vow)
                st["v_in_top2"] += int(t_vow in [s for s, _ in vv.most_common(2)])

            # ── BOTH votes agree with truth → unique identification? ──
            if votes and vv:
                cs, vs = votes.most_common(1)[0][0], vv.most_common(1)[0][0]
                st["both_votes"] += 1
                st["both_ok"] += int(cs == t_ser and vs == t_vow)

            # ── distributional channel: context-profile match ──
            # profile of bid = its preceding+following sign multiset
            prof_x = Counter()
            for s in seqs:
                for i, x in enumerate(s):
                    if x != bid:
                        continue
                    if i > 0:
                        prof_x[("L", s[i - 1])] += 1
                    if i + 1 < len(s):
                        prof_x[("R", s[i + 1])] += 1
            if prof_x:
                prof_by_value = {}
                for other, v in known.items():
                    k = ("series", CONS_SERIES_MAP.get(v, "?"), vowel_of(v))
                    prof_by_value.setdefault(k, Counter())
                for other, v in known.items():
                    key = ("series", CONS_SERIES_MAP.get(v, "?"), vowel_of(v))
                    for s in seqs:
                        for i, x in enumerate(s):
                            if x != other:
                                continue
                            if i > 0:
                                prof_by_value[key][("L", s[i - 1])] += 1
                            if i + 1 < len(s):
                                prof_by_value[key][("R", s[i + 1])] += 1
                # cosine-ish overlap
                def sim(a, b):
                    keys = set(a) | set(b)
                    num = sum(a[k] * b[k] for k in keys)
                    da = sum(v * v for v in a.values()) ** 0.5
                    db = sum(v * v for v in b.values()) ** 0.5
                    return num / (da * db) if da and db else 0.0
                best = None
                for key, prof in prof_by_value.items():
                    s = sim(prof_x, prof)
                    if best is None or s > best[0]:
                        best = (s, key)
                if best:
                    st["dist_n"] += 1
                    st["dist_ser_ok"] += int(best[1][1] == t_ser and best[1][2] != "?")
                    st["dist_full_ok"] += int(best[1][1] == t_ser and best[1][2] == t_vow)
                    per[bid] += int(best[1][1] == t_ser and best[1][2] == t_vow)

    print(f"\ndraws with a usable series/vowel: {st['n']}")
    if st["c_vote"]:
        print(f"C-link vote (series)  : top-1 correct {st['c_ok']}/{st['c_vote']} "
              f"({st['c_ok']/st['c_vote']:.1%}), in top-2 {st['c_in_top2']/st['c_vote']:.1%}")
    else:
        print("C-link vote (series)  : no votes fired")
    if st["v_vote"]:
        print(f"V-link vote (vowel)   : top-1 correct {st['v_ok']}/{st['v_vote']} "
              f"({st['v_ok']/st['v_vote']:.1%}), in top-2 {st['v_in_top2']/st['v_vote']:.1%}")
    else:
        print("V-link vote (vowel)   : no votes fired")
    if st["both_votes"]:
        print(f"BOTH votes correct    : {st['both_ok']}/{st['both_votes']} "
              f"({st['both_ok']/st['both_votes']:.1%}) → exact identification")
    if st["dist_n"]:
        print(f"context-profile match : series {st['dist_ser_ok']/st['dist_n']:.1%}, "
              f"series+vowel {st['dist_full_ok']/st['dist_n']:.1%} "
              f"(vs UNIFORM chance ~1.3% — see the pairwise table below for the "
              f"correct null)")
    # Unconditional pairwise test uses EVERY sign with a known value (the loops
    # above mutate `known` per trial; passing that here would silently drop 20 signs).
    pairwise_relations(follow, precede, confirmed)
    c.close()


if __name__ == "__main__":
    main()