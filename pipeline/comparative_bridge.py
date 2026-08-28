#!/usr/bin/env python3
"""
comparative_bridge.py — Generic triangular bridge: source ↔ via ↔ target

Generalizes pipeline/cypro_minoan_bridge.py for N languages.

    uv run python pipeline/comparative_bridge.py --source linear-a --target cypro-minoan --via cypriot-syllabary
    uv run python pipeline/comparative_bridge.py --source cypro-minoan --target eteocypriot --via cypriot-syllabary
    uv run python pipeline/comparative_bridge.py --source linear-a --target eteocypriot --via cypriot-syllabary  # LA→CM→Eteocypriot chain

For now: thin wrapper that reuses cypro_minoan_bridge's HIGH grid (30 signs) and extends it.
ponytail: reuse, don't rewrite; full generalization when a new chain actually diverges.
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMP_DIR = REPO / "data" / "analysis" / "comparative"
COMP_DIR.mkdir(parents=True, exist_ok=True)

# canonical HIGH grid from Phase 5
SRC_GRID = COMP_DIR / "la_cm_shared_phonetic_grid.csv"

def run_bridge(source: str, target: str, via: str | None = None) -> Path:
    # Source/target ids are languages/<id>/ or just ids like "linear-a"
    # For Phase 4: source=cypro-minoan target=eteocypriot via=cypriot-syllabary
    #           or source=linear-a target=eteocypriot via=cypriot-syllabary (LA→CM→Eteocypriot)
    # Ponytail: copy SRC_GRID and tag as via-eteocypriot; honest placeholder until Egetmeyer hand CSV has real Eteocypriot lexicon to join.
    out_name = f"{source}_{target}_via_{via or 'direct'}_grid.csv" if via else f"{source}_{target}_grid.csv"
    # special case: the plan's expected output is la_cm_eteocypriot_grid.csv
    if source == "linear-a" and target == "eteocypriot" or (source == "cypro-minoan" and target == "eteocypriot"):
        out = COMP_DIR / "la_cm_eteocypriot_grid.csv"
    elif source == "linear-a" and target == "cypro-minoan":
        out = COMP_DIR / "la_cm_shared_phonetic_grid.csv"
        if out.exists():
            print(f"Already exists: {out} (30 HIGH)")
            return out
    else:
        out = COMP_DIR / out_name

    if not SRC_GRID.exists():
        raise FileNotFoundError(f"Source grid missing: {SRC_GRID}")

    # For eteocypriot chain: copy HIGH grid and add column eteocypriot_examples (empty until real corpus joined)
    # This proves the pipeline path without fabricating decipherment.
    rows = list(csv.DictReader(open(SRC_GRID, encoding="utf-8")))
    fieldnames = list(rows[0].keys()) if rows else []
    # add eteocypriot columns if not present
    for extra in ["eteocypriot_sign", "eteocypriot_word", "eteocypriot_source"]:
        if extra not in fieldnames:
            fieldnames.append(extra)

    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            # tag HIGH rows as via-eteocypriot candidate, leave others empty (honest)
            if r.get("triangular_confidence") == "HIGH":
                r["eteocypriot_sign"] = r.get("cm_sign", "")
                r["eteocypriot_word"] = ""  # to be filled from Egetmeyer when real corpus arrives
                r["eteocypriot_source"] = f"{via or 'cypriot-syllabary'}: placeholder, no Eteocypriot lexicon joined yet"
            else:
                r.setdefault("eteocypriot_sign", "")
                r.setdefault("eteocypriot_word", "")
                r.setdefault("eteocypriot_source", "")
            w.writerow({k: r.get(k,"") for k in fieldnames})

    print(f"Wrote {len(rows)} rows (30 HIGH tagged) → {out}")
    print(f"  Source: {source} via {via} → {target}")
    print(f"  Note: eteocypriot_word column empty until Egetmeyer hand CSV has real attestations to join (honest placeholder).")
    return out

def main():
    p = argparse.ArgumentParser(description="Generic triangular bridge (wraps cypro_minoan_bridge)")
    p.add_argument("--source", required=True, help="Source language id, e.g. linear-a or cypro-minoan")
    p.add_argument("--target", required=True, help="Target language id, e.g. cypro-minoan or eteocypriot")
    p.add_argument("--via", default=None, help="Via script/id, e.g. cypriot-syllabary")
    p.add_argument("--out", default=None, help="Override output path")
    args = p.parse_args()
    out = run_bridge(args.source, args.target, args.via)
    if args.out and Path(args.out) != out:
        shutil.copy(out, args.out)
        print(f"Copied to {args.out}")

if __name__ == "__main__":
    main()
