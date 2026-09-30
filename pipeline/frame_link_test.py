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


def sign_profiles(seqs) -> dict:
    """Per-sign context profile: counts of the signs that precede and follow it.

    Computed once. The inline version of this scanned the whole corpus for every hidden
    sign on every draw, which is what made a null control unaffordable — and a channel
    without a same-draw null is how a 35.7% is read as 1.59x.
    """
    prof: dict = defaultdict(Counter)
    for s in seqs:
        for i, x in enumerate(s):
            if i > 0:
                prof[x][("L", s[i - 1])] += 1
            if i + 1 < len(s):
                prof[x][("R", s[i + 1])] += 1
    return prof


def _cosine(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    num = sum(a[k] * b[k] for k in keys)
    da = sum(v * v for v in a.values()) ** 0.5
    db = sum(v * v for v in b.values()) ** 0.5
    return num / (da * db) if da and db else 0.0


def context_profile_channel(prof, anchors: dict, hidden: list, truth: dict) -> Counter:
    """Classify each hidden sign by cosine of its context profile against each class.

    A class is a (series, vowel) pair, its profile the summed profiles of the anchors
    carrying it. `anchors` maps sign -> value and must already exclude the hidden signs;
    `truth` maps hidden sign -> (series, vowel). Pass a permuted `anchors`/`truth` to get
    the null.
    """
    classes: dict = defaultdict(Counter)
    for other, v in anchors.items():
        ser, vow = series_of(v), vowel_of(v)
        if ser in ("?", "VOWEL") or vow == "?":
            continue
        for k, c in prof.get(other, {}).items():
            classes[(ser, vow)][k] += c
    stats = Counter()
    for bid in hidden:
        px = prof.get(bid)
        if not px or not classes:
            continue
        best = max(classes.items(), key=lambda kv: _cosine(px, kv[1]))[0]
        stats["n"] += 1
        stats["ser_ok"] += int(best[0] == truth[bid][0])
        stats["full_ok"] += int(best == truth[bid])
    return stats


def context_profile_with_controls(prof, confirmed: dict, hidden: list, truth: dict,
                                  rng, reps: int = 20) -> dict:
    """The channel, its majority baseline, and a same-draw permutation null.

    The permutation shuffles values *among all confirmed signs* and then re-splits them
    into anchors and hidden, which destroys any real sign<->value association while
    preserving class sizes, profile shapes and the corpus. Both controls are computed on
    the same draws as the measurement (EXPERIMENT_PROTOCOL §2) — the thing the 35.7%
    figure never had.
    """
    hidden = list(hidden)
    hset = set(hidden)
    anchors = {b: v for b, v in confirmed.items() if b not in hset}
    got = context_profile_channel(prof, anchors, hidden, truth)

    # Majority baseline: always answer with the most common series / (series, vowel)
    # among the anchors on this draw.
    ser_c, full_c = Counter(), Counter()
    for v in anchors.values():
        ser, vow = series_of(v), vowel_of(v)
        if ser in ("?", "VOWEL") or vow == "?":
            continue
        ser_c[ser] += 1
        full_c[(ser, vow)] += 1
    maj_ser = ser_c.most_common(1)[0][0] if ser_c else None
    maj_full = full_c.most_common(1)[0][0] if full_c else None
    maj = Counter()
    for bid in hidden:
        if bid not in prof:
            continue
        maj["n"] += 1
        maj["ser_ok"] += int(truth[bid][0] == maj_ser)
        maj["full_ok"] += int(truth[bid] == maj_full)

    perm_ser, perm_full = [], []
    values = list(confirmed.values())
    for _ in range(reps):
        shuffled = list(values)
        rng.shuffle(shuffled)
        fake = dict(zip(confirmed, shuffled))          # permuted value<->sign assignment
        fake_anchors = {b: fake[b] for b in anchors}
        fake_truth = {b: (series_of(fake[b]), vowel_of(fake[b])) for b in hidden}
        r = context_profile_channel(prof, fake_anchors, hidden, fake_truth)
        if r["n"]:
            perm_ser.append(r["ser_ok"] / r["n"])
            perm_full.append(r["full_ok"] / r["n"])

    return {"got": got, "majority": maj,
            "perm_ser": perm_ser, "perm_full": perm_full}


def _pick_value(prof, anchors: dict, bid: str, cands: list) -> str | None:
    """Nearest-neighbour over contexts: pick the candidate whose anchor signs have the
    closest context profile to the hidden sign's own.

    This is the retrace's open item 1 (`oracle_retrace_findings.md`), and the only
    operationalization in this project that scores a *value* rather than a class.
    """
    px = prof.get(bid)
    if not px or not cands:
        return None
    by_value: dict = defaultdict(list)
    for other, v in anchors.items():
        if v in cands and other in prof:
            by_value[v].append(other)
    best_v, best_s = None, None
    for v in cands:                      # candidate order decides ties, deterministically
        sims = [_cosine(px, prof[o]) for o in by_value.get(v, [])]
        s = max(sims) if sims else 0.0
        if best_s is None or s > best_s:
            best_v, best_s = v, s
    return best_v


def context_profile_values(prof, candidates_for, confirmed: dict, hidden: list,
                           rng, reps: int = 20) -> dict:
    """Does the context-profile channel recover a VALUE, on the oracle's own terms?

    Candidate space is `candidates_for(bid, anchors)` — exactly what the oracle sees — so
    the chance baseline is the same mean 1/|candidates| the pre-registered gate is stated
    against, and the numbers are comparable to op1/op2 rather than to a class metric. The
    permutation null shuffles values among all confirmed signs, on the same draws.
    """
    hidden = list(hidden)
    hset = set(hidden)
    anchors = {b: v for b, v in confirmed.items() if b not in hset}

    def run(anch: dict, truth_of: dict) -> Counter:
        stats = Counter()
        for bid in hidden:
            cands = candidates_for(bid, anch)
            pick = _pick_value(prof, anch, bid, cands)
            if pick is None:
                continue
            stats["n"] += 1
            stats["chance"] += 1.0 / max(len(cands), 1)
            t = truth_of[bid]
            stats["exact_ok"] += int(pick == t)
            stats["ser_ok"] += int(series_of(pick) == series_of(t))
            stats["vow_ok"] += int(vowel_of(pick) == vowel_of(t))
        return stats

    got = run(anchors, confirmed)
    perm = []
    values = list(confirmed.values())
    for _ in range(reps):
        shuffled = list(values)
        rng.shuffle(shuffled)
        fake = dict(zip(confirmed, shuffled))
        r = run({b: fake[b] for b in anchors}, fake)
        if r["n"]:
            perm.append(r["exact_ok"] / r["n"])
    return {"got": got, "perm_exact": perm}


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
    prof = sign_profiles(seqs)
    print(f"language={args.language} anchors={len(bids)} signs_in_corpus="
          f"{sum(len(s) for s in seqs)} linked_signs={len({k[0] for k in c_w})}")

    rng = random.Random(0)
    # The nulls get their OWN stream. Shuffling from `rng` would advance the sequence that
    # samples the hidden sets, so adding a control would silently change the measurement it
    # controls — the same coupling as the D2 defect, one level up.
    perm_rng = random.Random(1)
    st = Counter()
    NULLS = Counter()
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

        # ── distributional channel: context-profile match, with controls ──
        # Per TRIAL, not per hidden sign: `context_profile_channel` classifies the whole
        # hidden set at once. Calling it inside the per-sign loop above made every sign
        # count 20 times and overstated n by 20x (rates were unaffected, n was not).
        truth_all = {b: (CONS_SERIES_MAP.get(confirmed[b], "?"), vowel_of(confirmed[b]))
                     for b in hs}
        r = context_profile_with_controls(prof, confirmed, sorted(hs), truth_all,
                                          perm_rng, reps=20)
        g = r["got"]
        st["dist_n"] += g["n"]
        st["dist_ser_ok"] += g["ser_ok"]
        st["dist_full_ok"] += g["full_ok"]
        if g["n"]:
            NULLS["draws"] += 1
            NULLS["dist_n"] += g["n"]
            NULLS["maj_ser_ok"] += r["majority"]["ser_ok"]
            NULLS["maj_full_ok"] += r["majority"]["full_ok"]
            NULLS["maj_n"] += r["majority"]["n"]
            NULLS["perm_ser"] += (sum(r["perm_ser"]) / len(r["perm_ser"])) * g["n"]
            NULLS["perm_full"] += (sum(r["perm_full"]) / len(r["perm_full"])) * g["n"]

            # ── the same channel, scored on VALUES in the oracle's candidate space ──
            v = context_profile_values(
                prof, lambda b, anch: c.get_candidates(b, confirmed=anch),
                confirmed, sorted(hs), perm_rng, reps=20)
            vg = v["got"]
            if vg["n"]:
                st["val_n"] += vg["n"]
                st["val_exact"] += vg["exact_ok"]
                st["val_ser"] += vg["ser_ok"]
                st["val_vow"] += vg["vow_ok"]
                st["val_chance"] += vg["chance"]
                st["val_perm"] += (sum(v["perm_exact"]) / len(v["perm_exact"])) * vg["n"]

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
        ser_r = st["dist_ser_ok"] / st["dist_n"]
        full_r = st["dist_full_ok"] / st["dist_n"]
        print(f"context-profile match : series {ser_r:.1%}, series+vowel {full_r:.1%}")
        if NULLS["dist_n"]:
            # Fields the original print never had: a same-draw majority baseline and a
            # same-draw permutation null. Uniform chance is the wrong null for a metric
            # that can only ever emit a class (closure paper §5).
            mn, pn = NULLS["maj_n"] or 1, NULLS["dist_n"]
            maj_ser = NULLS["maj_ser_ok"] / (NULLS["maj_n"] or 1)
            maj_full = NULLS["maj_full_ok"] / (NULLS["maj_n"] or 1)
            perm_ser = NULLS["perm_ser"] / pn
            perm_full = NULLS["perm_full"] / pn
            print(f"  {'metric':14s} {'channel':>8s} {'majority':>9s} {'perm null':>10s}"
                  f" {'vs maj':>7s} {'vs perm':>8s}")
            print(f"  {'series':14s} {ser_r:8.1%} {maj_ser:9.1%} {perm_ser:10.1%}"
                  f" {ser_r/maj_ser if maj_ser else 0:6.2f}x "
                  f"{ser_r/perm_ser if perm_ser else 0:7.2f}x")
            print(f"  {'series+vowel':14s} {full_r:8.1%} {maj_full:9.1%} {perm_full:10.1%}"
                  f" {full_r/maj_full if maj_full else 0:6.2f}x "
                  f"{full_r/perm_full if perm_full else 0:7.2f}x")
            print(f"  (n={mn} draws scored, {NULLS['draws']} draws)")
    if st["val_n"]:
        # The pre-registered gate is stated against mean 1/|candidates| (uniform chance),
        # so this table is the one that is directly comparable to op1/op2 — and to the
        # 1.5x threshold in lb_oracle.GATE_THRESHOLD.
        n = st["val_n"]
        exact = st["val_exact"] / n
        chance = st["val_chance"] / n
        perm = st["val_perm"] / n
        print(f"\ncontext-profile VALUES (oracle candidate space, n={n}):")
        print(f"  {'metric':14s} {'channel':>8s} {'perm null':>10s} {'1/|C|':>8s}"
              f" {'vs perm':>8s} {'vs 1/|C|':>9s}")
        print(f"  {'exact value':14s} {exact:8.1%} {perm:10.1%} {chance:8.1%}"
              f" {exact/perm if perm else 0:7.2f}x {exact/chance if chance else 0:8.2f}x")
        print(f"  {'series':14s} {st['val_ser']/n:8.1%}    {'-':>7s} {chance:8.1%}")
        print(f"  {'vowel':14s} {st['val_vow']/n:8.1%}    {'-':>7s} {chance:8.1%}")
        verdict = ("PASS" if exact/chance > 1.5 else
                   "INCONCLUSIVE" if exact/chance > 0.5 else "NO SIGNAL")
        print(f"  gate (exact vs 1/|C|, >1.5x): {exact/chance if chance else 0:.2f}x "
              f"-> {verdict}")
    # Unconditional pairwise test uses EVERY sign with a known value (the loops
    # above mutate `known` per trial; passing that here would silently drop 20 signs).
    pairwise_relations(follow, precede, confirmed)
    c.close()


if __name__ == "__main__":
    main()