"""Cypro-Minoan acceptance test — pre-registered before the corpus exists.

The chain under test is the only one in this project with a **deciphered endpoint**:

    Linear A  --shape-->  Cypro-Minoan  --shape-->  Cypriot Syllabary  -->  Greek
              (LA value from LB transfer)          (CG value: deciphered 1870s, independent of LA)

If shape correspondence across these scripts carries phonetic identity, the CG value of a CG sign
should agree with the LA value of the sign it corresponds to — two *independent* value routes (CG's
own decipherment versus Linear B transfer) meeting on a shape argument. If it does not, the transfer
chain is falsified as a route to Linear A values.

## Pre-registered decision rule (written before the measurement)

  * **Primary metric:** exact concordance between the **CG value** (Cypriot Syllabary, deciphered
    1870s, an external standard) and the **LB-standard value** of the Linear A sign it corresponds
    to (`la_lb_value`, i.e. the Unicode Linear B value — also an external standard). Both endpoints
    are standards that never saw this project; the *shape correspondence* is the hypothesis under
    test. n = rows where **both values are named** (a value ending in `?` is the standard saying
    "no name for this sign" — unknown, not a disagreement, and it is excluded).
  * **Null:** the same statistic with the CG values permuted across the mapped signs, 20,000 reps,
    same signs, same CG value multiset. `lift = observed / null_mean`.
  * **Gate** (the project's convention): lift > 1.5 → PASS; 0.5–1.5 → INCONCLUSIVE; ≤ 0.5 → NO SIGNAL,
    i.e. the chain is falsified as a value-transfer route.
  * **Power floor:** fewer than 15 usable rows → UNTESTABLE by pre-registration. A chain is not
    credited on 6 rows.
  * **Secondary, pre-declared:** series-level concordance (does the correspondence at least carry the
    consonant class?), and concordance stratified by the correspondence's own hand-assigned
    confidence. Prediction: concordance is HIGHER in the non-LOW stratum.
  * **Usable-region report, pre-declared:** the correspondence rows split into those whose LB value
    is *named* (where the chain can be validated, because an independent value exists to check it
    against) and those where it is *unnamed* (where the chain would be *useful*, because it would
    propose a value nobody has). Both counts and both confidence profiles are reported, because a
    chain that is validated only where values are already known confirms without extending.

## Why not the phonetic grid as the LA-side reference

The obvious-looking version of this test compares the CG value against the project's own
`refined_phonetic_grid.csv`. That version is **circular and was rejected after measuring it**: the
refined grid carries a `cm_suggested_value` / `cm_triangular_confidence` column, and
`phonetic_grid_refinement.py` consumes the CM chain as evidence (weight 1.5) — for **all 87** mapped
rows, at some confidence. So the grid agreeing with the chain is partly the chain agreeing with
itself: the naive version reports 78% (35×) on all rows and still 70% (16.7×) on rows where CM was not
HIGH, but only 11 rows survive excluding CM at every confidence, below the power floor. Using the LB
standard instead removes the dependence entirely.

## Contradictions

Rows where both values are named and differ are reported separately and are neither evidence for nor
against the gate: they are hypotheses to chase (a wrong shape correspondence, or a systematic
voicing/vowel mismatch between the two standards). The same-series-but-different-cell near-misses are
their own class, because a chain that transfers series but not voicing is a different result from one
that transfers nothing.

## Provenance

A corpus supplied as CM data counts only when `languages/cypro-minoan/data/raw/PROVENANCE.json`
declares `synthetic: false`, and independently established values live in
`languages/cypro-minoan/cm_values.csv` with an `independence` column. Values assigned BY Linear A or
Linear B transfer are refused: that is the placeholder trap, and it is the one failure this test
exists to prevent.

    uv run python pipeline/cm_acceptance_test.py
    uv run python pipeline/cm_acceptance_test.py --reps 50000
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CM_GRID = REPO / "data/analysis/comparative/la_cm_shared_phonetic_grid.csv"
LA_GRID = REPO / "data/analysis/bootstrapping/expanded_grid_purged.csv"
REFINED = REPO / "data/analysis/comparative/refined_phonetic_grid.csv"
CM_VALUES = REPO / "languages/cypro-minoan/cm_values.csv"
PROVENANCE = REPO / "languages/cypro-minoan/data/raw/PROVENANCE.json"

SERIES = {"p": "LABIAL", "m": "LABIAL", "t": "DENTAL", "d": "DENTAL", "n": "DENTAL",
          "k": "VELAR", "q": "VELAR", "s": "SIBILANT", "z": "SIBILANT", "r": "LIQUID",
          "l": "LIQUID", "j": "PALATAL", "w": "SEMIVOWEL"}


def series_of(v: str) -> str:
    v = (v or "").strip()
    return SERIES.get(v[0], "?") if v else "?"


def load(path: Path, key: str) -> dict:
    if not path.exists():
        return {}
    return {r[key].strip(): r for r in csv.DictReader(open(path, encoding="utf-8"))}


def readiness() -> dict:
    """Is real CM data here yet, and does it declare its provenance?"""
    out = {"synthetic": None, "independent_values": 0}
    if PROVENANCE.exists():
        out["synthetic"] = json.loads(PROVENANCE.read_text(encoding="utf-8")).get("synthetic")
    if CM_VALUES.exists():
        for r in csv.DictReader(open(CM_VALUES, encoding="utf-8")):
            if (r.get("independence") or "").strip().lower() == "independent":
                out["independent_values"] += 1
    return out


def known(v: str) -> bool:
    """A named value. A trailing '?' is the standard saying 'no name for this sign'.

    Comparing `je` to `je?` as a disagreement (the first version) put 33 unknown-value rows into the
    denominator, all of them at LOW correspondence confidence, and dragged the LOW stratum to 6%.
    They are not disagreements; they are absences of an independent check.
    """
    v = (v or "").strip()
    return bool(v) and not v.endswith("?") and v != "?"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=20000)
    args = p.parse_args()

    cm = list(csv.DictReader(open(CM_GRID, encoding="utf-8")))
    rd = readiness()
    print(f"readiness: provenance synthetic={rd['synthetic']}, independent CM values="
          f"{rd['independent_values']}  (this test needs no corpus: both endpoints are standards)")

    usable, unnamed = [], []
    for r in cm:
        cg, lb = (r.get("cg_value") or "").strip(), (r.get("la_lb_value") or "").strip()
        if not cg:
            continue
        rec = {"ab": r["la_ab"].strip(), "cg": cg, "lb": lb,
               "shape": (r.get("triangular_confidence") or "").strip().upper(),
               "cm": (r.get("cm_sign") or "").strip()}
        (usable if known(cg) and known(lb) else unnamed).append(rec)

    n = len(usable)
    ex = sum(1 for r in usable if r["cg"] == r["lb"])
    se = sum(1 for r in usable if series_of(r["cg"]) == series_of(r["lb"]))
    print(f"\nmapped rows {len(cm)}; both values named {n}; "
          f"LB value unnamed/provisional {len(unnamed)} (excluded — absent check, not a disagreement)")
    print(f"exact concordance   {ex}/{n} = {ex/max(n,1):.1%}")
    print(f"series concordance  {se}/{n} = {se/max(n,1):.1%}")

    if n < 15:
        print(f"\nVERDICT: UNTESTABLE by pre-registration ({n} usable rows < 15)")
        return

    rng = random.Random(0)
    cg_vals = [r["cg"] for r in usable]
    null_exact, null_series = [], []
    for _ in range(args.reps):
        perm = cg_vals[:]
        rng.shuffle(perm)
        null_exact.append(sum(1 for r, v in zip(usable, perm) if r["lb"] == v) / n)
        null_series.append(sum(1 for r, v in zip(usable, perm)
                               if series_of(r["lb"]) == series_of(v)) / n)
    me, ms = sum(null_exact) / args.reps, sum(null_series) / args.reps
    lift_e = (ex / n) / me if me else 0.0
    lift_s = (se / n) / ms if ms else 0.0
    print(f"\npermutation null ({args.reps} reps, same signs, same CG value multiset):")
    print(f"  exact  null mean {me:.1%}  max {max(null_exact):.1%}   lift {lift_e:.2f}x")
    print(f"  series null mean {ms:.1%}  max {max(null_series):.1%}   lift {lift_s:.2f}x")

    print("\nby the correspondence's own hand-assigned shape confidence "
          "(pre-declared prediction: higher in the non-LOW stratum):")
    for bucket in ("HIGH", "MEDIUM", "LOW"):
        sub = [r for r in usable if r["shape"] == bucket]
        if sub:
            ok = sum(1 for r in sub if r["cg"] == r["lb"])
            ss = sum(1 for r in sub if series_of(r["cg"]) == series_of(r["lb"]))
            print(f"  {bucket:6s} n={len(sub):2d}  exact {ok}/{len(sub)} = {ok/len(sub):.0%}  "
                  f"series {ss}/{len(sub)} = {ss/len(sub):.0%}")

    contra = [r for r in usable if r["cg"] != r["lb"] and r["shape"] != "LOW"]
    near = [r for r in usable if r["cg"] != r["lb"]
            and series_of(r["cg"]) == series_of(r["lb"])]
    print(f"\ndisagreements at HIGH/MEDIUM confidence: "
          + (", ".join(f"{r['ab']} CG={r['cg']}/LB={r['lb']} ({r['shape']})" for r in contra)
             or "none"))
    print(f"disagreements that stay within the series ({len(near)} of "
          f"{sum(1 for r in usable if r['cg'] != r['lb'])}): "
          + (", ".join(f"{r['ab']} {r['cg']}/{r['lb']}" for r in near) or "none"))

    verdict = "PASS" if lift_e > 1.5 else "INCONCLUSIVE" if lift_e > 0.5 else "NO SIGNAL"
    print(f"\nVERDICT (pre-registered, primary = exact concordance, CG vs LB-standard): "
          f"{lift_e:.2f}x → {verdict}")
    if verdict == "NO SIGNAL":
        print("  the shape-correspondence chain is falsified as a value-transfer route")

    # The usable-region question, which is what decides whether this confirms or extends.
    print(f"\nusable region — a chain validated only where values are already known confirms without "
          f"extending:")
    for label, sub in (("LB value NAMED (can validate)", usable),
                       ("LB value UNNAMED (would extend)", unnamed)):
        if sub:
            print(f"  {label:30s} n={len(sub):2d}  correspondence confidence: "
                  + ", ".join(f"{b}={sum(1 for r in sub if r['shape'] == b)}"
                              for b in ("HIGH", "MEDIUM", "LOW")))


if __name__ == "__main__":
    main()
