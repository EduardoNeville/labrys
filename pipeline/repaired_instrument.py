"""Repaired oracle instrument: per-sign discrimination instead of a global scalar.

What was wrong with the shipped one (see data/analysis/ventris/oracle_retrace_findings.md):
  * candidate stage: Kober links consumed as unweighted cliques with the C/V
    distinction discarded and a meaningless global threshold → candidate lists of
    39-70 values, or the truth removed outright
  * estimator: four whole-corpus aggregates (final-sign entropy, held-out CE,
    prefix concentration, link agreement) summed on incomparable scales → never
    a unique argmax, so nothing is ever recovered

This instrument scores each hidden sign INDEPENDENTLY, using only anchor values:

  series_vote(x)  weighted plurality of the consonant series of x's C-partners
                  (C-partner = shares a FOLLOWING sign; weight = |follow(x) ∩ follow(y)|)
  vowel_vote(x)   weighted plurality of the vowels of x's V-partners
                  (V-partner = shares a PRECEDING sign)
  profile(x)      counter over (L, preceding sign) and (R, following sign)

  score(v) = cos(profile(x), profile(sign(v))) + α·[series(v) == series_vote]
                                              + β·[vowel(v)  == vowel_vote]

Measures are reported against the right baselines: uniform chance AND the
majority-class rate observed among the anchors, because a vote that only ever
predicts the most common class carries no per-sign information.

Usage:
    uv run python pipeline/repaired_instrument.py --language linear-b
    uv run python pipeline/repaired_instrument.py --language linear-a
"""

from __future__ import annotations

import argparse
import logging
import random
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.ventris.complete import CONS_SERIES_MAP, vowel_of

logger = logging.getLogger("repaired")
REPO = Path(__file__).resolve().parent.parent

CONFIGS = {
    "linear-b": dict(
        db=REPO / "languages/linear-b/data/database/linear-b.db",
        grid=REPO / "languages/linear-b/answer_key.csv",
    ),
    "linear-a": dict(
        db=REPO / "data/database/lineara_full.db",
        # honest grid: 58 CONFIRMED + 11 UNCERTAIN, phantoms purged
        grid=REPO / "data/analysis/bootstrapping/expanded_grid_purged.csv",
    ),
}

ALPHA, BETA = 0.5, 0.5


class RepairedInstrument:
    def __init__(self, db_path: Path, grid_path: Path) -> None:
        self.seqs = self._load_sequences(db_path)
        self.grid = {}
        for row in _csv(grid_path):
            self.grid[row["bennett_id"]] = row
        self.follow: dict = defaultdict(set)
        self.precede: dict = defaultdict(set)
        self.profile: dict = defaultdict(Counter)
        for seq in self.seqs:
            for i, x in enumerate(seq):
                if i > 0:
                    self.precede[x].add(seq[i - 1])
                    self.profile[x][("L", seq[i - 1])] += 1
                if i + 1 < len(seq):
                    self.follow[x].add(seq[i + 1])
                    self.profile[x][("R", seq[i + 1])] += 1

    @staticmethod
    def _load_sequences(db_path: Path) -> list:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        out, cur = {}, None
        for r in conn.execute(
            "SELECT i.id AS iid, s.sequence AS seq, s.bennett_id AS bid "
            "FROM signs s JOIN inscriptions i ON i.id = s.inscription_id "
            "WHERE s.bennett_id != '' ORDER BY i.id, s.sequence"
        ):
            out.setdefault(r["iid"], []).append(r["bid"])
        conn.close()
        return list(out.values())

    def anchors(self) -> dict:
        return {b: r["refined_value"].strip() for b, r in self.grid.items()
                if r.get("decision", "").strip() == "CONFIRM"
                and r.get("refined_value", "").strip() not in ("", "?")}

    def series_vote(self, x: str, known: dict) -> Counter:
        votes: Counter = Counter()
        for y, v in known.items():
            if y == x:
                continue
            w = len(self.follow.get(x, set()) & self.follow.get(y, set()))
            if w:
                s = CONS_SERIES_MAP.get(v, "?")
                if s not in ("?", "VOWEL"):
                    votes[s] += w
        return votes

    def vowel_vote(self, x: str, known: dict) -> Counter:
        votes: Counter = Counter()
        for y, v in known.items():
            if y == x:
                continue
            w = len(self.precede.get(x, set()) & self.precede.get(y, set()))
            if w:
                vw = vowel_of(v)
                if vw != "?":
                    votes[vw] += w
        return votes

    @staticmethod
    def _cos(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        keys = set(a) | set(b)
        num = sum(a[k] * b[k] for k in keys)
        da = sum(v * v for v in a.values()) ** 0.5
        db = sum(v * v for v in b.values()) ** 0.5
        return num / (da * db) if da and db else 0.0

    def rank(self, x: str, known: dict, alpha: float = ALPHA, beta: float = BETA):
        """Return candidates with scores, best first. Candidate values are the
        values carried by the anchors (the instrument's whole vocabulary)."""
        sv = self.series_vote(x, known)
        vv = self.vowel_vote(x, known)
        top_ser = sv.most_common(1)[0][0] if sv else None
        top_vow = vv.most_common(1)[0][0] if vv else None

        by_value: dict = defaultdict(Counter)
        for y, v in known.items():
            by_value[v] += self.profile.get(y, Counter())

        scored = []
        for v, prof in by_value.items():
            s = self._cos(self.profile.get(x, Counter()), prof)
            if top_ser and CONS_SERIES_MAP.get(v, "?") == top_ser:
                s += alpha
            if top_vow and vowel_of(v) == top_vow:
                s += beta
            scored.append((s, v))
        scored.sort(reverse=True)
        return scored, top_ser, top_vow


def _csv(path: Path):
    import csv

    with open(path, encoding="utf-8") as f:
        yield from csv.DictReader(f)


def evaluate(inst: RepairedInstrument, trials: int, hidden: int, label: str) -> dict:
    anchors = inst.anchors()
    bids = sorted(anchors)
    rng = random.Random(0)
    st = Counter()

    for _ in range(trials):
        hs = set(rng.sample(bids, min(hidden, len(bids))))
        known = {b: v for b, v in anchors.items() if b not in hs}
        values = list(known.values())
        # Majority baselines must ignore the junk label "?" (unmapped values),
        # otherwise 'predict the unmapped class' scores as a real prediction.
        real_series = [s for s in (CONS_SERIES_MAP.get(v, "?") for v in values) if s != "?"]
        maj_ser = Counter(real_series).most_common(1)[0][0] if real_series else "?"
        real_vowels = [v for v in (vowel_of(v) for v in values) if v != "?"]
        maj_vow = Counter(real_vowels).most_common(1)[0][0] if real_vowels else "?"
        maj_val = Counter(values).most_common(1)[0][0]

        for bid in hs:
            truth = anchors[bid]
            t_ser, t_vow = CONS_SERIES_MAP.get(truth, "?"), vowel_of(truth)
            if t_ser == "?" or t_vow == "?":
                st["skipped_unmapped"] += 1
                continue
            scored, top_ser, top_vow = inst.rank(bid, known)
            if not scored:
                continue
            st["n"] += 1
            best = scored[0][1]
            st["exact"] += int(best == truth)
            st["series_ok"] += int(CONS_SERIES_MAP.get(best, "?") == t_ser)
            st["vowel_ok"] += int(vowel_of(best) == t_vow)
            st["ser_truth_in_top2"] += int(
                t_ser in [CONS_SERIES_MAP.get(v, "?") for _, v in scored[:2]])
            # baselines on the same draws
            st["base_exact"] += int(maj_val == truth)
            st["base_series"] += int(maj_ser == t_ser)
            st["base_vowel"] += int(maj_vow == t_vow)
            st["vote_ser_ok"] += int(top_ser == t_ser)
            st["vote_vow_ok"] += int(top_vow == t_vow)
            st["n_values"] += len(scored)

    n = max(st["n"], 1)
    chance = 1.0 / (st["n_values"] / n) if st["n_values"] else 1.0
    print(f"\n=== repaired instrument: {label} ===")
    print(f"anchors {len(bids)}, usable draws {st['n']} "
          f"(skipped {st['skipped_unmapped']} unmapped), "
          f"candidate values per draw {st['n_values']/n:.1f}")
    print(f"\n{'metric':38s} {'instrument':>11s} {'majority':>9s} {'chance':>8s} {'ratio':>7s}")
    print(f"{'exact value recovered':38s} {st['exact']/n:11.1%} {st['base_exact']/n:9.1%} "
          f"{chance:8.1%} {(st['exact']/n)/chance:6.2f}x")
    print(f"{'consonant series correct':38s} {st['series_ok']/n:11.1%} "
          f"{st['base_series']/n:9.1%} {'—':>8s} "
          f"{(st['series_ok']/n)/max(st['base_series']/n,1e-9):6.2f}x(maj)")
    print(f"{'vowel correct':38s} {st['vowel_ok']/n:11.1%} {st['base_vowel']/n:9.1%} "
          f"{'—':>8s} {(st['vowel_ok']/n)/max(st['base_vowel']/n,1e-9):6.2f}x(maj)")
    print(f"\n  vote-only channels: series {st['vote_ser_ok']/n:.1%} "
          f"(majority {st['base_series']/n:.1%}), vowel {st['vote_vow_ok']/n:.1%} "
          f"(majority {st['base_vowel']/n:.1%})")
    print(f"  true series in instrument top-2: {st['ser_truth_in_top2']/n:.1%}")
    return {"exact": st["exact"] / n, "chance": chance,
            "lift": (st["exact"] / n) / chance,
            "series": st["series_ok"] / n, "series_majority": st["base_series"] / n,
            "vowel": st["vowel_ok"] / n, "vowel_majority": st["base_vowel"] / n}


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--language", default="linear-b", choices=list(CONFIGS))
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    c = CONFIGS[args.language]
    inst = RepairedInstrument(c["db"], c["grid"])
    print(f"sequences {len(inst.seqs)}, sign tokens {sum(len(s) for s in inst.seqs)}, "
          f"grid rows {len(inst.grid)}")
    evaluate(inst, args.trials, args.hidden, args.language)


if __name__ == "__main__":
    main()