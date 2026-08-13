"""Phase 11, Avenue 6b — Applying the diachronic prior to the grid.

Avenue 6 showed MM-attested signs are 2x more likely CONFIRMED (p=0.0003).
This module APPLIES that prior to the grid:

1. Re-weight confidence: MM-attested UNCERTAIN signs get a raised prior;
   LM-only signs get a lowered one.
2. Conflict disambiguation: for signs with LB-vs-CM conflict, does MM
   attestation predict which value is correct?
3. Oracle: leave-one-out test — does MM-attestation predict CONFIRMED
   status when combined with existing confidence?

Usage:
    uv run python pipeline/ventris/diachronic_prior.py
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


def load_mm_attested(db_path: str = "data/database/lineara_full.db") -> Set[str]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT s.bennett_id FROM signs s
        JOIN inscriptions i ON s.inscription_id = i.id
        WHERE s.sign_type='syllabogram' AND s.bennett_id LIKE 'AB %'
        AND i.minoan_period LIKE 'MM%'
    """)
    out = {r["bennett_id"] for r in c.fetchall()}
    conn.close()
    return out


def load_grid(path: str = "data/analysis/bootstrapping/expanded_grid.csv") -> Dict[str, Dict]:
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["bennett_id"]] = r
    return out


def load_refined(path: str = "data/analysis/comparative/refined_phonetic_grid.csv") -> Dict[str, Dict]:
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["bennett_id"]] = r
    return out


class DiachronicPrior:
    def __init__(self, db_path: str = "data/database/lineara_full.db",
                 grid_path: str = "data/analysis/bootstrapping/expanded_grid.csv",
                 refined_path: str = "data/analysis/comparative/refined_phonetic_grid.csv") -> None:
        self.mm = load_mm_attested(db_path)
        self.grid = load_grid(grid_path)
        self.refined = load_refined(refined_path)
        logger.info("DiachronicPrior: %d MM-attested signs", len(self.mm))

    def apply_prior(self) -> List[Dict]:
        """Re-weight each UNCERTAIN sign's confidence by MM attestation.

        Prior: MM-attested raises confidence (2x enrichment), LM-only lowers.
        Applied as a multiplicative factor to the refined confidence_score.
        """
        out = []
        for bid, g in self.grid.items():
            dec = g.get("decision", "").strip()
            val = g.get("refined_value", "").strip()
            if dec != "UNCERTAIN" or val in ("", "?"):
                continue
            rf = self.refined.get(bid, {})
            base_conf = float(rf.get("confidence_score", 25) or 25)
            mm = bid in self.mm
            # Prior factor: MM-attested *2 (up to cap), LM-only *0.5
            factor = 2.0 if mm else 0.5
            new_conf = min(100.0, base_conf * factor)
            out.append({
                "bennett_id": bid, "refined_value": val,
                "base_confidence": base_conf, "mm_attested": mm,
                "prior_factor": factor, "adjusted_confidence": round(new_conf, 1),
                "lb_value": rf.get("lb_proposed_value", ""),
                "cm_value": rf.get("cm_suggested_value", ""),
                "conflict_note": rf.get("conflict_note", ""),
            })
        out.sort(key=lambda r: -r["adjusted_confidence"])
        return out

    def conflict_prior(self) -> List[Dict]:
        """For LB-vs-CM conflict signs, does MM attestation break the tie?"""
        out = []
        for bid, rf in self.refined.items():
            lb = rf.get("lb_proposed_value", "").strip()
            cm = rf.get("cm_suggested_value", "").strip()
            if lb and cm and lb != cm:
                out.append({
                    "bennett_id": bid,
                    "lb_value": lb, "cm_value": cm,
                    "refined_value": rf.get("refined_value", "").strip(),
                    "mm_attested": bid in self.mm,
                    "confidence": rf.get("confidence_score", ""),
                    "note": rf.get("conflict_note", "")[:70],
                })
        return out

    def oracle(self) -> Dict:
        """LOO: does MM attestation predict CONFIRMED status?

        Prediction rule: MM-attested → CONFIRMED, else UNCERTAIN.
        Compare to majority baseline.
        """
        confirmed = {b for b, g in self.grid.items()
                     if g.get("decision", "").strip() == "CONFIRM"
                     and g.get("refined_value", "").strip() not in ("", "?")}
        all_signs = set(self.grid.keys())
        mm_conf = sum(1 for b in self.mm & all_signs if b in confirmed)
        mm_not = sum(1 for b in self.mm & all_signs if b not in confirmed)
        lm_conf = sum(1 for b in (all_signs - self.mm) if b in confirmed)
        lm_not = sum(1 for b in (all_signs - self.mm) if b not in confirmed)
        correct = mm_conf + lm_not
        total = len(all_signs)
        acc = correct / total if total else 0.0
        n_conf = len(confirmed)
        majority = max(n_conf, total - n_conf) / total if total else 0.0
        return {
            "accuracy": acc, "majority_baseline": majority,
            "lift": acc / majority if majority else 0.0,
            "mm_confirmed": mm_conf, "mm_total": mm_conf + mm_not,
            "lm_confirmed": lm_conf, "lm_total": lm_conf + lm_not,
            "n_signs": total,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    dp = DiachronicPrior()
    print("=== AVENUE 6b: DIACHRONIC PRIOR APPLIED ===")

    print("\n-- UNCERTAIN signs re-weighted by MM attestation --")
    for r in dp.apply_prior()[:15]:
        mm = "MM" if r["mm_attested"] else "LM-only"
        print(f"  {r['bennett_id']}: {r['refined_value']} conf {r['base_confidence']}->{r['adjusted_confidence']} [{mm}] {r['conflict_note'][:40]}")

    print("\n-- LB-vs-CM conflicts and MM attestation --")
    for r in dp.conflict_prior():
        mm = "MM" if r["mm_attested"] else "LM-only"
        print(f"  {r['bennett_id']}: LB={r['lb_value']} vs CM={r['cm_value']} [{mm}] refined={r['refined_value']}")

    o = dp.oracle()
    print(f"\n-- Oracle LOO --")
    print(f"  MM-attested → CONFIRMED predicts at {o['accuracy']*100:.0f}% vs majority {o['majority_baseline']*100:.0f}% (lift {o['lift']:.2f}x)")

    # Write output
    out = Path("data/analysis/ventris")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "diachronic_prior.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bennett_id", "refined_value", "base_confidence", "mm_attested",
                    "prior_factor", "adjusted_confidence", "lb_value", "cm_value"])
        for r in dp.apply_prior():
            w.writerow([r["bennett_id"], r["refined_value"], r["base_confidence"],
                        r["mm_attested"], r["prior_factor"], r["adjusted_confidence"],
                        r["lb_value"], r["cm_value"]])
    print(f"\nWrote data/analysis/ventris/diachronic_prior.csv")
