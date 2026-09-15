"""Audit the two known-defective inputs behind the Linear A phonetic grid.

1. `data/analysis/comparative/la_lb_mapping.csv`
   - glyph columns (`la_unicode`, `la_char`, `lb_unicode`, `lb_char`) were
     assigned by codepoint offset instead of by sign number → wrong glyphs.
     Presentational only: `visual_sim` is a literal, so no score depends on it.
   - `lb_value` conflicts with the Unicode Linear B standard for the row's sign
     number on 6 rows. **Substantive**: this column feeds the LB-transfer term of
     `phonetic_grid_refinement.py`, so those rows propagate into the refined grid.
     This script does NOT rewrite values — it measures the blast radius, because
     changing them requires re-deriving the grid deliberately.

2. `data/analysis/logograms/fraction_values_proposed.csv`
   - the generator fits values as exclusive complements (`proposed = 1 - partner`)
     and the file's own notes then cite "pairs with X to sum ~1" as evidence.
     This script checks whether that pairing is a tautology.

Usage:
    uv run python pipeline/audit_grid_inputs.py                 # report only
    uv run python pipeline/audit_grid_inputs.py --apply-glyphs  # fix glyph columns
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
from collections import Counter
from pathlib import Path

from pipeline.unicode_utils import correct_glyph_columns, linear_b_glyph

REPO = Path(__file__).resolve().parent.parent
MAPPING = REPO / "data/analysis/comparative/la_lb_mapping.csv"
GRIDS = [
    REPO / "data/analysis/bootstrapping/expanded_grid.csv",
    REPO / "data/analysis/bootstrapping/expanded_grid_purged.csv",
    REPO / "data/analysis/comparative/refined_phonetic_grid.csv",
]
FRACTIONS = REPO / "data/analysis/logograms/fraction_values_proposed.csv"
OUT = REPO / "data/analysis/comparative"


def read(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def audit_mapping(apply: bool) -> None:
    rows = read(MAPPING)
    fixed, issues = [], []
    glyph_wrong = value_conflict = value_unverifiable = value_missing = 0

    for row in rows:
        m = re.match(r"^AB\s*(\d+)$", (row.get("bennett_id") or "").strip(), re.I)
        corrected = correct_glyph_columns(row)
        glyph_diff = [k for k in ("la_unicode", "la_char", "lb_unicode", "lb_char")
                      if corrected.get(k, "") != row.get(k, "")]
        if glyph_diff:
            glyph_wrong += 1
        why = []
        if glyph_diff:
            why.append("glyph:" + ",".join(glyph_diff))
        if m:
            n = int(m.group(1))
            std = linear_b_glyph(n)
            repo_val = (row.get("lb_value") or "").strip().rstrip("?").lower()
            if repo_val in ("—", "-", ""):
                repo_val = ""          # no claim, not a bad claim
            # A sign with no Linear B cognate is *supposed* to carry no lb_value
            # (the generator's own rule: "LA-only signs … assigned lb_value='—'"),
            # so absence there is correct behaviour, not a gap.
            cognate = (row.get("attestation") or "").strip().lower() in ("both", "lb_only")
            if std and repo_val and std[2] != repo_val:
                value_conflict += 1
                why.append(f"CONFLICT: repo={repo_val!r} standard={std[2]!r}")
            elif std and not repo_val and cognate:
                value_missing += 1
                why.append(f"MISSING: standard={std[2]!r} not recorded")
            elif not std and repo_val:
                value_unverifiable += 1
                why.append(f"UNVERIFIABLE: asserts {repo_val!r}; no Unicode sign for B{n:03d}")
        if why:
            issues.append({**{k: row.get(k, "") for k in
                              ("bennett_id", "lb_value", "la_hyp_value")},
                           "issue": "; ".join(why)})
        fixed.append(corrected)

    print(f"\n=== la_lb_mapping.csv ({len(rows)} rows) ===")
    print(f"  glyph columns wrong        : {glyph_wrong}   (presentational: visual_sim is a literal)")
    print(f"  lb_value CONFLICT vs standard: {value_conflict}   ← substantive, feeds the grid")
    print(f"  lb_value MISSING (std has one, sign is cognate): {value_missing}")
    print(f"  lb_value UNVERIFIABLE (no such Unicode sign): {value_unverifiable}")
    print("\n  substantive rows:")
    for i in issues:
        if "glyph:" == i["issue"][:6] and "CONFLICT" not in i["issue"] \
                and "MISSING" not in i["issue"] and "UNVERIFIABLE" not in i["issue"]:
            continue
        print(f"    {i['bennett_id']:8s} grid_hyp={i['la_hyp_value'] or '-':6s} {i['issue']}")

    # blast radius: what do the grids currently say for those signs?
    conflicted = {i["bennett_id"] for i in issues if "CONFLICT" in i["issue"]}
    if conflicted:
        print("\n  grid rows carrying a CONFLICTED sign:")
        for g in GRIDS:
            if not g.exists():
                continue
            for r in read(g):
                if r.get("bennett_id") in conflicted:
                    print(f"    {g.name:28s} {r['bennett_id']:8s} "
                          f"refined={r.get('refined_value', '-'):6s} "
                          f"decision={r.get('decision', '-'):9s} "
                          f"conf={r.get('confidence', '-')}")

    if issues:
        out = OUT / "la_lb_mapping_audit.csv"
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["bennett_id", "lb_value",
                                              "la_hyp_value", "issue"])
            w.writeheader()
            w.writerows(issues)
        print(f"\n  wrote {out}")

    if apply and glyph_wrong:
        with open(MAPPING, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(fixed)
        print(f"  APPLIED: {glyph_wrong} rows' glyph columns corrected in {MAPPING.name}")
    elif glyph_wrong:
        print("  (run with --apply-glyphs to correct the presentational columns)")


def audit_fractions() -> None:
    rows = read(FRACTIONS)
    lb_supported = {round(float(r["linear_b_equivalent_value"]), 6)
                    for r in rows if r.get("linear_b_equivalent_value")}
    values = {}
    for r in rows:
        try:
            values[r["fraction_id"]] = float(r["proposed_decimal_value"])
        except (TypeError, ValueError):
            continue
    report, complement_exact, tautological, unsupported = [], 0, 0, 0
    for r in rows:
        fid = r["fraction_id"]
        v = values.get(fid)
        lb = r.get("linear_b_equivalent_value", "")
        note = r.get("notes", "") or ""
        partner = re.search(r"Pairs with (A \d+) \(([\d.]+)\)", note)
        pair_sum = pair_ok = ""
        if partner and v is not None and partner.group(1) in values:
            s = round(v + values[partner.group(1)], 9)
            pair_sum = f"{s:.6f}"
            pair_ok = "yes" if abs(s - 1.0) < 1e-6 else "no"
            if pair_ok == "yes":
                complement_exact += 1
        determined_by_complement = (v is not None and any(
            abs(v + other - 1.0) < 1e-6 for k, other in values.items() if k != fid))
        if determined_by_complement and pair_ok == "yes":
            tautological += 1
        lb_ok = lb and abs(float(lb) - v) < 1e-6 if (lb and v is not None) else False
        if not lb_ok:
            unsupported += 1
        report.append({
            "fraction_id": fid, "proposed": v,
            "lb_equivalent": lb or "(none)", "lb_agrees": "yes" if lb_ok else "no",
            "exact_complement_partner": partner.group(1) if partner else "",
            "pair_sums_to_1": pair_ok,
            "value_determined_by_complement": "yes" if determined_by_complement else "no",
            "occurrences": r.get("occurrences", ""),
        })

    print(f"\n=== fraction_values_proposed.csv ({len(rows)} rows) ===")
    print(f"  LB fraction series present in file     : "
          f"{sorted(round(x, 4) for x in lb_supported)}")
    print(f"  rows whose value equals its LB equivalent: "
          f"{sum(1 for x in report if x['lb_agrees'] == 'yes')}")
    print(f"  rows with an exact 1-complement partner  : {complement_exact}")
    print(f"  → of those, note cites the pairing as evidence (tautology): {tautological}")
    print(f"  rows with no LB corroboration            : {unsupported}")
    noncanon = [x for x in report
                if x["lb_agrees"] == "no" and x["proposed"] not in lb_supported]
    print(f"  rows neither LB-supported nor LB-series  : {len(noncanon)}")
    for x in noncanon:
        print(f"    {x['fraction_id']:8s} proposed={x['proposed']:<9} "
              f"complement_of={x['exact_complement_partner'] or '-':8s} "
              f"sums_to_1={x['pair_sums_to_1'] or '-':4s} occ={x['occurrences']}")
    out = REPO / "data/analysis/logograms/fraction_values_audit.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(report[0].keys()))
        w.writeheader()
        w.writerows(report)
    print(f"  wrote {out}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--apply-glyphs", action="store_true",
                   help="correct the presentational glyph columns in place")
    args = p.parse_args()
    audit_mapping(args.apply_glyphs)
    audit_fractions()


if __name__ == "__main__":
    main()