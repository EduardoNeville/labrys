"""Phase 2 backfill: recorded LB method results -> data/analysis/rsi/tree.json.

Reconstructed from METHOD_CLOSURE_PAPER.md §4/§6 and the scripts those sections name.
Every node is appended through `rsi_tree.append`, which recomputes the verdict from the
node's own primary metric — a typed-in verdict is rejected.

Counting rule (PLAN §8.4 says "do not invent a flatter tree", §8.3 allows a node to carry
several metrics): **one node = one method hypothesis, one primary metric, one measured
outcome.** Sub-measurements of one hypothesis are that node's `metrics`, not extra nodes —
which is why op3's four frame directions are one node and op2b's eight aggregators are one
node. Counting them as nodes would clear K2 by construction, which is the game the
recomputed-verdict rule exists to prevent.

    uv run python data/analysis/rsi/backfill.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.rsi_tree import append  # noqa: E402

D = "distributional"
H = {"cost_estimated": True}


def node(nid, parent, cls, lift, metrics, primary, recovered, cost, source, **extra):
    from pipeline.rsi_tree import verdict_for

    n = {
        "id": nid, "parent": parent, "evidence_class": cls, "is_world_expanding": False,
        "lift": lift, "metrics": metrics, "primary_metric": primary,
        "values_recovered": recovered, "control_ok": True, "leak_ok": True,
        # Derived from the node's own primary metric, never typed in — and the store
        # recomputes it on append, so a disagreement is a hard failure.
        "verdict": verdict_for(metrics[primary]),
        "cost_hours": cost, "source": source,
    }
    n.update(H)
    n.update(extra)
    return n


def world(nid, parent, cost, source, note):
    return {
        "id": nid, "parent": parent, "evidence_class": "external-data",
        "is_world_expanding": True, "values_recovered": None, "lift": None,
        "verdict": "N/A", "cost_hours": cost, "cost_estimated": True,
        "source": source, "note": note,
    }


NODES = [
    node("op1-shipped-scorer", None, D,
         lift=None,
         metrics={"exact": 0.0, "exact_rate": 0.0, "exact_chance": 0.0208,
                  "in_argmax_rate": 0.0312, "unique_argmax_rate": 0.0,
                  "forced_rate": 0.5563, "exact_membership": 0.4437},
         primary="exact", recovered=0, cost=30.0,
         source="METHOD_CLOSURE_PAPER.md §4.1 + pipeline/lb_oracle.py",
         n_draws=160,
         note="Root. Committed run. Nominal n=160 is 40 distinct sign draws — see "
              "phase0.md D2 (score_completion reseeds the global RNG, so trials 2-8 "
              "repeat trial 2's hidden set). The gate quantities reproduce: 0.0000, "
              "0 recovered, NO SIGNAL. chance 0.0208 belongs to that entangled "
              "sequence; over 8 independent draws it is 0.0273 (guard 8 asserts the "
              "gate quantities, not chance)."),

    node("op1a-six-defect-repair", "op1-shipped-scorer", D,
         lift=None, metrics={"exact": 0.0, "exact_rate": 0.0}, primary="exact",
         recovered=0, cost=40.0,
         source="METHOD_CLOSURE_PAPER.md §6 + data/analysis/ventris/oracle_repair_report.md",
         n_draws=160,
         note="Six defects repaired (incl. the 1.28x anchor-word leak, which was the "
              "only spurious positive). Oracle re-run unchanged at 0.00x: a zero "
              "multiplied by anything is zero, but this one was measured by repaired "
              "machinery. A seventh defect found 2026-09-30 is recorded in phase0.md."),

    node("op2-per-sign-instrument", "op1a-six-defect-repair", D,
         lift=None, metrics={"exact": 0.0, "series": 1.03, "vowel": 1.00},
         primary="exact", recovered=0, cost=12.0,
         source="METHOD_CLOSURE_PAPER.md §4.2 + pipeline/repaired_instrument.py",
         n_draws=160,
         note="Independently written instrument: one sign at a time, context-profile "
              "cosine against candidate-bearing anchors plus series/vowel votes, no "
              "shared code with the shipped scorer. Lands exactly on the majority-class "
              "baseline — the shipped code was not uniquely bad."),

    node("op2a-coordinate-ascent-4inits", "op2-per-sign-instrument", D,
         lift=None, metrics={"exact": 0.0, "exact_rate": 0.0, "recovered": 0, "of": 60},
         primary="exact", recovered=0, cost=6.0,
         source="METHOD_CLOSURE_PAPER.md §4.1 + pipeline/oracle_diagnose.py part D",
         n_draws=60,
         note="Multi-pass coordinate ascent from several initialisations on the same "
              "objective: 0/60. Search is not the limiting factor — the objective has "
              "no resolution to optimise."),

    node("op2b-aggregator-bakeoff", "op2-per-sign-instrument", D,
         lift=None, metrics={"exact": 0.0, "exact_rate": 0.0,
                             "unique_argmax_rate": 0.0,
                             "in_argmax_min": 0.022, "in_argmax_max": 0.358},
         primary="exact", recovered=0, cost=4.0,
         source="pipeline/aggregator_bakeoff.py (this run, n=500: 25 trials x 20 hidden)",
         n_draws=500,
         note="Eight aggregators incl. the shipped sum, kober-only, Borda rank-"
              "normalisation and the two-stage kober-then-entropy variant. Unique-"
              "argmax rate 0.0% for all eight. The docstring's 67/47/59/100% top-1 "
              "figures are pre-repair and do not reproduce."),

    node("op2c-in-argmax-null-control", "op2b-aggregator-bakeoff", D,
         lift=None, metrics={"in_argmax_lift": 0.52, "best_channel": "morph only",
                             "in_argmax": 0.358, "null_in_argmax": 0.694,
                             "mean_argmax": 32.2, "n_candidates": 46.1},
         primary="in_argmax_lift", recovered=None, cost=1.0,
         source="data/analysis/rsi/phase0_null_control.py (2026-09-30)",
         n_draws=500,
         note="Permutation control for op2b, same draws. Every channel's in_argmax is "
              "BELOW its null (0.25-0.52x): the 27-36% figures were argmax sets covering "
              "~59% of the candidate list, not orientation. This is the measurement that "
              "retires PLAN §6.4's tie-collapse hypothesis and with it op5 (PLAN §8.4)."),

    node("op3-frame-sharing", "op1-shipped-scorer", D,
         lift=None, metrics={"share_follow_cons": 0.85, "share_follow_vow": 0.98,
                             "share_prec_cons": 0.88, "share_prec_vow": 0.95,
                             "n_pairs": 71804},
         primary="share_follow_cons", recovered=0, cost=8.0,
         source="METHOD_CLOSURE_PAPER.md §4.3 + pipeline/frame_link_test.py",
         n_draws=71804,
         note="Kober's own recorded relation, four directions, all at or below chance. "
              "primary_metric is the consonant direction because that is the one Kober's "
              "method needs; the verdict is not taken from the best of the four (§8.3)."),

    node("op3a-link-vote-and-context-profile", "op3-frame-sharing", D,
         lift=None, metrics={"c_link_series": 1.02, "c_link_series_rate": 0.229,
                             "v_link_vowel": 0.85, "v_link_vowel_rate": 0.143,
                             "context_profile_series_rate": 0.357},
         primary="c_link_series", recovered=0, cost=2.0,
         source="pipeline/frame_link_test.py (this run, n=70 usable draws)",
         n_draws=70,
         note="Per-sign use of the same relation, not the pairwise table: link-vote "
              "series 22.9% vs a 22.5% majority baseline, so 1.02x. The context-profile "
              "series rate 35.7% is the strongest number recorded anywhere in this "
              "project, and its null is NOT measured on the same draw set (the script's "
              "own uniform 1.3% is the wrong null for a class metric) — so it is carried "
              "as an unvalidated sub-metric, not as this node's primary. If a channel is "
              "ever worth a real node, it is this one, with a same-draw null."),

    node("op4-slot-alternation-A", "op1-shipped-scorer", D,
         lift=None, metrics={"series_ratio": 0.51, "series_share": 0.139,
                             "majority_series": 0.274,
                             "vowel_unique_ratio": 0.64, "vowel_unique": 0.125,
                             "control_unique": 0.194, "correct_when_unique": 1.0,
                             "control_correct": 0.738, "n_unique": 9},
         primary="series_ratio", recovered=0, cost=5.0,
         source="METHOD_CLOSURE_PAPER.md §4.4 + pipeline/paradigm_slot_probe.py",
         n_draws=4520,
         note="Definition A (shared slot). Ventris's actual method. Slot-alternating "
              "partners share a series at roughly HALF the majority baseline — "
              "anti-predictive. The eliminative vowel step's 9/9 is n=9 (protocol §7: "
              "a plausible number outrunning its control) and its control reaches 73.8% "
              "by accident. primary_metric is the series ratio, the paper's conclusion 1."),

    node("op4b-minimal-pair-B", "op4-slot-alternation-A", D,
         lift=None, metrics={"correct_when_unique_ratio": 0.98,
                             "correct_when_unique": 0.786, "control_correct": 0.80,
                             "vowel_unique_ratio": 1.05, "vowel_unique": 0.194,
                             "control_unique": 0.185, "series_ratio": 0.52,
                             "series_share": 0.143, "n_unique": 14},
         primary="correct_when_unique_ratio", recovered=0, cost=2.0,
         source="METHOD_CLOSURE_PAPER.md §4.4 + pipeline/paradigm_slot_probe.py",
         n_draws=4510,
         note="Definition B, the strictest available (word types differing in exactly "
              "one position). Signal and permutation control converge: 78.6% vs 80.0%, "
              "and the eliminative step fires less often than its own control "
              "(19.4% vs 18.5% -> 1.05x). Built because definition A failed its control."),

    world("x1-cm-corpus", "op1-shipped-scorer", 2.0,
          "languages/cypro-minoan/CORPUS_REQUEST.md",
          "Cypro-Minoan is a direct daughter script of Linear A; ~30 LA values free if "
          "it breaks. Currently a synthetic placeholder. The only move that can raise "
          "the ceiling."),
    world("x2-anetaki-ii", "op1-shipped-scorer", 2.0,
          "AGENTS.md §Key Findings; METHOD_CLOSURE_PAPER.md §7.2",
          "The continuous transliteration of the Knossos scepter (KN Zg 57/58), 119 "
          "signs, ritual — the first genuinely new long text since the corpus "
          "correction, and the correct re-test case for op4b."),
    world("x3-bilingual-find", "x1-cm-corpus", 2.0,
          "METHOD_CLOSURE_PAPER.md §7.1",
          "Evidence class #1 in §7: semantic anchors. The failure of distributional "
          "methods says nothing about a bilingual of adequate length."),
]


def main() -> None:
    from pipeline.rsi_tree import TREE, load

    if load(TREE)["nodes"]:
        raise SystemExit(f"{TREE} is not empty — this backfill is append-only and "
                         "refuses to double-append. Move the file aside to redo it.")
    for n in NODES:
        append(n)
    tree = load(TREE)
    replay = [n for n in tree["nodes"] if not n["is_world_expanding"]]
    print(f"appended {len(tree['nodes'])} nodes -> {TREE}")
    print(f"replayable {len(replay)}  world-expanding "
          f"{len(tree['nodes']) - len(replay)}  root {tree['root']}")
    from collections import Counter
    print("verdicts:", dict(Counter(n["verdict"] for n in tree["nodes"])))


if __name__ == "__main__":
    main()
