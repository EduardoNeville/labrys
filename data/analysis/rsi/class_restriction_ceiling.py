"""Ceiling for the class channel: if the class is handed over for free, can the scorer pick?

`op2d` measures a channel that identifies the (series, vowel) class 4.00x its majority
baseline — the strongest controlled result this project has. Signal is not utility. A class
narrows the oracle's ~40 candidates to ~3; whether that is *useful* depends on something never
measured: **can the shipped scorer pick the right member of a 3-candidate class?**

This is the ceiling test, and it is deliberately generous to the channel: the true class is
handed over for free (an oracle restriction, not the channel's 9.6% prediction). If the scorer
cannot discriminate *within* a class it already knows, then no class-channel + this-scorer
combination can ever recover a value, and the line is closed with a ceiling instead of a hope.

Pre-registered prediction, written before the run: the shipped scorer's within-class accuracy
will be at or below the 1/|class| baseline. Reason: `collect()`'s four channels produce a
unique argmax 0.0% of the time over 40 candidates; restricting to 3 removes the candidates it
was *not* choosing, which is not the same as giving it resolution. If this holds, op2d's class
signal cannot be converted into values by this scorer, and the conversion needs a scoring
change rather than a bigger corpus.

    uv run python data/analysis/rsi/class_restriction_ceiling.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.phonetics import series_of, vowel_of                      # noqa: E402
from pipeline.rsi_evaluate import SHIPPED_METHOD, _weights, draws_for, select  # noqa: E402
from pipeline.rsi_tree import verdict_for                                # noqa: E402


def main() -> None:
    draws, cache_hit = draws_for(SHIPPED_METHOD)
    w = _weights(SHIPPED_METHOD)
    n = len(draws)
    in_class = 0
    picked = 0
    picked_lenient = 0
    truth_in_restricted = 0
    sizes = []
    chance = 0.0
    for d in draws:
        rows = d["rows"]
        truth = d["truth"]
        ts, tv = series_of(truth), vowel_of(truth)
        restr = [r for r in rows
                 if series_of(r["cand"]) == ts and vowel_of(r["cand"]) == tv]
        if not restr:
            continue
        n_ok = 1 if any(r["cand"] == truth for r in restr) else 0
        truth_in_restricted += n_ok
        if not n_ok:
            continue
        in_class += 1
        sizes.append(len(restr))
        chance += 1.0 / len(restr)
        idx, resolved = select(restr, w, SHIPPED_METHOD["tiebreak"])
        picked += int(resolved and restr[idx]["cand"] == truth)
        picked_lenient += int(restr[idx]["cand"] == truth)

    rate = picked / in_class if in_class else 0.0
    rate_len = picked_lenient / in_class if in_class else 0.0
    ch = chance / in_class if in_class else 0.0
    lift = rate / ch if ch else 0.0
    print(f"shipped draws: {n}  (cache_hit={cache_hit})")
    print(f"draws where the TRUE class is in the candidate list: {in_class} "
          f"({in_class/n:.1%} of draws)")
    print(f"  ... of which the truth itself survived candidate generation: "
          f"{truth_in_restricted} ({truth_in_restricted/in_class:.1%})")
    print(f"mean restricted class size: {sum(sizes)/max(len(sizes),1):.2f} candidates")
    print(f"\nORACLE-class-restricted scorer (true class handed over for free):")
    print(f"  exact value, tie-strict : {rate:6.1%}   chance 1/|class| = {ch:.1%}   "
          f"lift {lift:.2f}x -> {verdict_for(lift)}")
    print(f"  exact value, tie-lenient: {rate_len:6.1%}   "
          f"lift {rate_len/ch if ch else 0:.2f}x")
    print(f"\n  collapsed to the real method: the channel's class hit is 9.6%, so an "
          f"end-to-end\n  estimate is 0.096 x {rate:.3f} = {0.096*rate:.2%} absolute "
          f"(assuming the two errors\n  are independent, which is generous), against a "
          f"2.5% uniform chance rate.")
    print(f"\n  VERDICT: {'within-class discrimination exists' if lift > 1.5 else 'the scorer cannot pick within a known class'}"
          f" -> {'the class channel is convertible' if lift > 1.5 else 'op2d cannot be converted to values by this scorer'}")


if __name__ == "__main__":
    main()
