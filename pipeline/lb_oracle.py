"""Condition (a): the blind Linear B decipherment oracle.

Runs the Ventris endgame scorer on Linear B with all phonetic values withheld.
Values live in exactly one file (``answer_key.csv``, from the Unicode Linear B
standard); the scorer only ever sees ``signs.bennett_id`` (``complete.py:253``
and :func:`lb_ingest.assert_no_leak`).

Steps (each idempotent):
    1. ``answer_key.csv``        — CONFIRM for signs with a Unicode standard
                                   value, UNCERTAIN for LB signs with no
                                   accepted reading (e.g. *56, *82).
    2. Kober triples             — real ``TripleDetector`` on the LB DB.
    3. oracle_test()             — hide-20-recover, trials times.

Gate (pre-registered, LINEAR_B_SANDBOX_PLAN.md §2, do not tune):
    lift_over_chance > 1.5 → PASS       0.5–1.5 → INCONCLUSIVE       ≤0.5 → NO SIGNAL

Usage:
    uv run python pipeline/lb_oracle.py --trials 8 --hidden 20
"""

from __future__ import annotations

import argparse
import csv
import logging
import sqlite3
from collections import Counter
from pathlib import Path

logger = logging.getLogger("lb_oracle")

REPO_ROOT = Path(__file__).resolve().parent.parent
LANG_DIR = REPO_ROOT / "languages" / "linear-b"
DB_PATH = LANG_DIR / "data" / "database" / "linear-b.db"
ANSWER_KEY = LANG_DIR / "answer_key.csv"
KOBER_DIR = LANG_DIR / "data" / "analysis" / "kober"
TRIPLES = KOBER_DIR / "triple_patterns.csv"
FREQ_CSV = LANG_DIR / "data" / "analysis" / "frequency_constraints" / "constrained_candidates.csv"
RESULT_MD = LANG_DIR / "data" / "analysis" / "ventris" / "ventris_report.md"

# ── Pre-registered gate — see LINEAR_B_SANDBOX_PLAN.md §2 ────────────────────
GATE_THRESHOLD = 1.5
# The shipped TripleDetector keeps only triples with >= 2 UNCERTAIN members.
# That filter is Linear A bookkeeping (LA is 68% unknown: 94 UNCERTAIN / 44
# CONFIRM), not part of the method. With the sandbox's 15 uncertain signs it
# reduced the graph to a 101-triple hub-star in which only 3 signs had a named
# partner, disabling the Kober channel entirely. Passing every observed sign as
# "uncertain" makes the filter inert, so the frame-link graph is the real one
# (60k triples over 76 linked signs). See data/analysis/ventris/lb_sandbox_findings.md.
MAX_TRIPLES = 250_000  # inert by default: the shipped builder sets
                       # total_connections=3 for every row, so ranking is
                       # arbitrary — never truncate on it without a real key.


def observed_signs() -> set:
    conn = sqlite3.connect(DB_PATH)
    rows = {r[0] for r in conn.execute(
        "SELECT DISTINCT bennett_id FROM signs WHERE bennett_id != ''")}
    conn.close()
    return rows


def make_answer_key() -> dict:
    """CONFIRM every corpus sign whose value is in the Unicode LB standard;
    UNCERTAIN for signs with no accepted reading. The key is the *fact file* of
    the sandbox: it is never handed to the scorer."""
    from pipeline.lb_ingest import lb_reference

    known = {e["sign_id"]: value for value, e in lb_reference().items()}
    rows, stats = [], Counter()
    for bid in sorted(observed_signs()):
        if bid in known:
            val = known[bid]
            rows.append({"bennett_id": bid, "conventional_value": val,
                         "refined_value": val, "decision": "CONFIRM",
                         "confidence": "100", "resolved_by_bootstrapping": "NO"})
            stats["confirmed"] += 1
        else:
            rows.append({"bennett_id": bid, "conventional_value": "?",
                         "refined_value": "?", "decision": "UNCERTAIN",
                         "confidence": "0", "resolved_by_bootstrapping": "NO"})
            stats["uncertain"] += 1
    with open(ANSWER_KEY, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"answer key: {stats['confirmed']} CONFIRM, {stats['uncertain']} UNCERTAIN"
          f" -> {ANSWER_KEY}")
    return dict(stats)


def kober_profiles() -> dict:
    """initial/medial/final fractions per sign, from the editor's word division
    (the words table). Faithful to what LA's positional analysis consumes."""
    conn = sqlite3.connect(DB_PATH)
    tot, init, fin = Counter(), Counter(), Counter()
    for (seq,) in conn.execute("SELECT sign_sequences FROM words"):
        signs = [s for s in (seq or "").split("-") if s]
        if not signs:
            continue
        tot.update(signs)
        init[signs[0]] += 1
        fin[signs[-1]] += 1
    conn.close()
    profiles = {}
    for s, t in tot.items():
        i, f = init.get(s, 0), fin.get(s, 0)
        profiles[s] = {"initial": i / t, "medial": max(0.0, (t - i - f) / t),
                       "final": f / t, "total": t}
    return profiles


def build_kober() -> None:
    from pipeline.kober.triple_detection import TripleDetector

    # Every sign counts as uncertain here: the >=2-UNCERTAIN filter in the
    # shipped detector would otherwise strangle the graph (see MAX_TRIPLES note).
    uncertain = observed_signs()
    # stub ML columns the detector writes into its CSV; the Ventris loader
    # ignores them (reads sign_1..3 only).
    stub_ml = {bid: {"conventional": "", "predicted": "", "confidence": 0.0}
               for bid in observed_signs()}
    d = TripleDetector(db_path=str(DB_PATH), uncertain=uncertain,
                       ml_preds=stub_ml, profiles=kober_profiles(),
                       min_bigram_count=2)
    d.extract_bigrams()
    d.find_frame_links()
    d.build_triples()
    KOBER_DIR.mkdir(parents=True, exist_ok=True)
    d.write_all(str(KOBER_DIR))

    rows = list(csv.DictReader(open(TRIPLES, encoding="utf-8")))
    print(f"kober: {len(rows)} triples, {len(d.frame_links_c)} C-links, "
          f"{len(d.frame_links_v)} V-links")


def run_oracle(trials: int, hidden: int) -> dict:
    from pipeline.ventris.complete import VentrisGridCompleter

    # No frequency-typology prior for the sandbox: LA's file encodes
    # Linear-A-specific plausibility guesses, and an LB-derived one would feed
    # the corpus's own statistics back into candidate restriction. An
    # explicit empty constraints file makes the choice intentional.
    FREQ_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(FREQ_CSV, "w", encoding="utf-8", newline="") as f:
        f.write("bennett_id,frequency,consonant_class,vowel,plausible,series,reasons\n")

    completer = VentrisGridCompleter(
        db_path=str(DB_PATH),
        expanded_grid_path=str(ANSWER_KEY),
        kober_triples_path=str(TRIPLES),
        freq_constraints_path=str(FREQ_CSV),
        ab68_override=False,
    )
    print(f"corpus: {len(completer.inscriptions)} inscriptions, "
          f"{len(completer.confirmed)} anchors, {len(completer.uncertain)} uncertain")

    # Pre-registration block written BEFORE any scoring (plan §2/§5).
    RESULT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULT_MD, "w", encoding="utf-8") as f:
        f.write("# Ventris Oracle — Linear B sandbox, condition (a)\n\n")
        f.write("## Pre-registered decision rule (committed before the run)\n\n")
        f.write(f"- pass threshold: lift > {GATE_THRESHOLD}x chance "
                f"(MULTI_LANGUAGE_DECYPHR_PLAN.md §3.4)\n")
        f.write(f"- trials: {trials}, hidden per trial: {hidden}\n")
        f.write("- interpretation: PASS → method has signal (LB is the best case:\n")
        f.write("  perfect anchors, real Greek; treat as an upper bound, not a\n")
        f.write("  Linear A green light). INCONCLUSIVE → do not build on it.\n")
        f.write("  NO SIGNAL → publish the negative; stop LA-specific search.\n\n")
        f.write("## Results (appended after the run)\n\n")

    res = completer.oracle_test(hidden=hidden, trials=trials)
    completer.close()

    lift = res["lift_over_chance"]
    if lift > GATE_THRESHOLD:
        verdict = "PASS"
    elif lift > 0.5:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "NO SIGNAL"
    res["verdict"] = verdict

    with open(RESULT_MD, "a", encoding="utf-8") as f:
        f.write(f"- recovery: {res['recovery_rate']:.4f} vs chance "
                f"{res['chance_rate']:.4f} → lift {lift:.2f}x\n")
        f.write(f"- verdict: **{verdict}** "
                f"(gate > {GATE_THRESHOLD}x — pre-registered)\n")
        f.write(f"- total hidden signs scored: {res['total_hidden_scored']}\n\n")
        if res.get("signs_recovered_all_trials"):
            f.write("Signs recovered in ALL trials: "
                    + ", ".join(sorted(res["signs_recovered_all_trials"])) + "\n")
    print(f"\nRESULT: recovery {res['recovery_rate']:.4f} vs chance "
          f"{res['chance_rate']:.4f} → lift {lift:.2f}x — {verdict}")
    return res


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="Linear B blind oracle (condition a)")
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--hidden", type=int, default=20)
    args = p.parse_args()

    from pipeline.lb_ingest import assert_no_leak

    assert_no_leak(DB_PATH)
    make_answer_key()
    build_kober()
    run_oracle(trials=args.trials, hidden=args.hidden)


if __name__ == "__main__":
    main()