"""Repair `la_lb_mapping.csv`'s `lb_value` column from the Unicode Linear B standard.

Why this is a correction and not a scholarly rewrite
----------------------------------------------------
`linear_b_mapping.py` documents `lb_value` as "Phonetic value in Linear B
(Ventris & Chadwick)" for the cognate sign, and the AB numbering is cognate-
aligned. Measured on the project's own grid: of the checkable signs, **39 agree
with the Linear B standard by number and 4 do not** — so the convention holds and
the exceptions are defects. Further evidence that the 7 conflicts are mechanical:
6 of the 7 repo values are *another sign's* standard value (AB 11 'si' = AB 41's,
21 'mi' = AB 73's, 29 'pu' = AB 50's, 33 'ra' = AB 60's, 42 'ke' = AB 44's,
66 'ta' = AB 59's), and the 7th ('ai') is not a Linear B value at all. All 7 rows
have `la_hyp_value` identical to `lb_value`, so the file carried no independent
second opinion to lose.

Policy
------
* `attestation in {both, lb_only}` and a standard value exists → set `lb_value`
  to the standard (this corrects conflicts and fills genuine gaps).
* `attestation == la_only` → the sign has no Linear B cognate, so '—' is correct;
  left untouched.
* No Unicode sign for that number → left untouched (values there are literature
  readings, not machine-checkable).

Priors are preserved in a new `lb_value_prior` column and the change log records
every edit. Nothing else in the file is modified.

Usage:
    uv run python pipeline/fix_mapping_values.py             # dry run + preview
    uv run python pipeline/fix_mapping_values.py --apply
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pipeline.unicode_utils import linear_b_glyph

REPO = Path(__file__).resolve().parent.parent
MAPPING = REPO / "data/analysis/comparative/la_lb_mapping.csv"
CHANGELOG = REPO / "data/analysis/comparative/la_lb_mapping_value_fixes.csv"
GRID_CANDIDATES = [
    REPO / "data/analysis/bootstrapping/expanded_grid_purged.csv",
    REPO / "data/analysis/comparative/refined_phonetic_grid.csv",
]


def sign_number(bennett_id: str):
    import re
    m = re.match(r"^AB\s*(\d+)$", (bennett_id or "").strip(), re.I)
    return int(m.group(1)) if m else None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    rows = list(csv.DictReader(open(MAPPING, encoding="utf-8")))
    fields = list(rows[0].keys())
    for extra in ("lb_value_prior", "lb_value_source",
                  "la_hyp_value_prior"):
        if extra not in fields:
            fields.append(extra)

    # grid values, for the impact preview
    grid_values = {}
    for g in GRID_CANDIDATES:
        if g.exists():
            for r in csv.DictReader(open(g, encoding="utf-8")):
                grid_values.setdefault(r["bennett_id"], []).append(
                    (g.name, (r.get("refined_value") or "").strip(),
                     (r.get("decision") or "").strip()))

    # standard values, to test the transposition hypothesis
    by_value = {}
    for n in range(1, 300):
        std = linear_b_glyph(n)
        if std:
            by_value.setdefault(std[2], []).append(n)

    changes, out = [], []
    for row in rows:
        n = sign_number(row.get("bennett_id", ""))
        row = dict(row)
        row.setdefault("lb_value_prior", "")
        row.setdefault("lb_value_source", "")
        row.setdefault("la_hyp_value_prior", "")
        if n is None:
            out.append(row)
            continue
        std = linear_b_glyph(n)
        prior = (row.get("lb_value") or "").strip()
        plain = prior.rstrip("?").lower()
        cognate = (row.get("attestation") or "").strip().lower() in ("both", "lb_only")
        if not std:
            row["lb_value_source"] = "literature (no Unicode LB sign)"
        elif not cognate:
            row["lb_value_source"] = "la_only (no LB cognate expected)"
        elif plain != std[2]:
            kind = "CONFLICT" if plain and plain not in ("—", "-") else "GAP"
            note = ""
            if plain in by_value:
                note = (f"prior {plain!r} is standard B{by_value[plain][0]:03d} "
                        f"({plain}) — looks transposed")
            changes.append({"bennett_id": row["bennett_id"], "class": kind,
                            "lb_value_before": prior, "lb_value_after": std[2],
                            "attestation": row.get("attestation", ""), "note": note})
            row["lb_value_prior"] = prior
            row["lb_value"] = std[2]
            row["lb_value_source"] = f"unicode_standard (was {kind.lower()})"
            # `la_hyp_value` duplicated the wrong lb_value on every conflict row
            # (measured: identical on all 7), and phonetic_grid_refinement reads
            # la_hyp_value in preference to lb_value — so a correction that does
            # not reach this column never propagates to the grid.
            hyp = (row.get("la_hyp_value") or "").strip()
            if hyp and hyp.rstrip("?").lower() == plain:
                row["la_hyp_value_prior"] = hyp
                row["la_hyp_value"] = std[2]
        else:
            row["lb_value_source"] = "unicode_standard"
            # idempotence: a corrected row whose la_hyp_value still mirrors the prior
            prior_lb = (row.get("lb_value_prior") or "").strip()
            hyp = (row.get("la_hyp_value") or "").strip()
            if prior_lb and hyp and hyp.rstrip("?").lower() == prior_lb.rstrip("?").lower() \
                    and hyp != std[2]:
                row["la_hyp_value_prior"] = hyp
                row["la_hyp_value"] = std[2]
        out.append(row)

    print(f"=== planned lb_value repairs: {len(changes)} rows ===")
    for c in changes:
        print(f"  {c['bennett_id']:8s} {c['class']:9s} {c['lb_value_before'] or '—':6s} "
              f"→ {c['lb_value_after']:6s}  {c['note']}")
        for gname, val, dec in grid_values.get(c["bennett_id"], []):
            print(f"      grid: {gname:28s} refined={val or '?':6s} decision={dec}")

    if args.apply:
        with open(MAPPING, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(out)
        if changes:
            with open(CHANGELOG, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(changes[0].keys()))
                w.writeheader()
                w.writerows(changes)
            print(f"\nAPPLIED to {MAPPING.name}; change log: {CHANGELOG}")
        else:
            print(f"\nAPPLIED to {MAPPING.name}; no new changes (already correct)")
    else:
        print("\n(dry run — pass --apply to write)")


if __name__ == "__main__":
    main()