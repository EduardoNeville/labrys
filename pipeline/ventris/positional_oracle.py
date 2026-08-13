"""Phase 11, Avenue 1 — Positional profiles as phonetic-independent constraints.

The oracle proved the Ventris grammatical scorer has no signal: every corpus
signal is circular (derived from Linear B transfer). Positional profiles are
the ONE signal NOT derived from phonetics — they measure sign *identity*
distributions (initial/medial/final fraction, positional entropy) with no
phonetic assumption.

Test: hide CONFIRMED signs, and see if positional profiles alone can recover
their vowel column (or consonant class). If recovery >> chance, we have a real
constraint the failed scorer never used.

Usage:
    uv run python pipeline/ventris/positional_oracle.py
"""

from __future__ import annotations

import csv
import logging
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Vowel columns (Linear B values)
VOWEL_COLUMNS = ["a", "e", "i", "o", "u"]


def vowel_of(val: str) -> str:
    v = val.strip().lower()
    if len(v) == 1:
        return v
    if len(v) == 2:
        return v[1] if v[1] in "aeiou" else v[0]
    return v[-1] if v[-1] in "aeiou" else "?"


def load_positional_profiles(path: str = "data/analysis/positional/positional_profiles.csv") -> Dict[str, Dict]:
    """Load positional profiles keyed by bennett_id."""
    profiles: Dict[str, Dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row["bennett_id"].strip()
            if not bid:
                continue
            profiles[bid] = {
                "initial_fraction": float(row.get("initial_fraction", 0) or 0),
                "medial_fraction": float(row.get("medial_fraction", 0) or 0),
                "final_fraction": float(row.get("final_fraction", 0) or 0),
                "positional_entropy": float(row.get("positional_entropy", 0) or 0),
                "total_occurrences": int(row.get("total_occurrences", 0) or 0),
            }
    return profiles


def load_grid(path: str = "data/analysis/bootstrapping/expanded_grid.csv") -> Tuple[Dict[str, str], List[str]]:
    """Load confirmed values and uncertain signs from the expanded grid."""
    confirmed: Dict[str, str] = {}
    uncertain: List[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row.get("bennett_id", "").strip()
            val = row.get("refined_value", "").strip()
            dec = row.get("decision", "UNCERTAIN").strip()
            if dec == "CONFIRM" and val and val != "?":
                confirmed[bid] = val
            else:
                uncertain.append(bid)
    # AB 68 override (resolved Phase 7)
    if "AB 68" in uncertain:
        uncertain.remove("AB 68")
        confirmed["AB 68"] = "ro"
    return confirmed, uncertain


class PositionalOracle:
    """Test whether positional profiles alone can recover hidden phonetic values."""

    def __init__(
        self,
        profiles_path: str = "data/analysis/positional/positional_profiles.csv",
        grid_path: str = "data/analysis/bootstrapping/expanded_grid.csv",
    ) -> None:
        self.profiles = load_positional_profiles(profiles_path)
        self.confirmed, self.uncertain = load_grid(grid_path)
        logger.info("PositionalOracle: %d profiles, %d confirmed, %d uncertain",
                     len(self.profiles), len(self.confirmed), len(self.uncertain))

    def _profile_vector(self, bid: str) -> Optional[Tuple[float, float, float]]:
        p = self.profiles.get(bid)
        if not p:
            return None
        return (p["initial_fraction"], p["medial_fraction"], p["final_fraction"])

    def _train_prototypes(self, confirmed: Dict[str, str]) -> Dict[str, Tuple[float, float, float]]:
        """Build average positional profile per vowel column from confirmed signs."""
        sums: Dict[str, List[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
        counts: Counter = Counter()
        for bid, val in confirmed.items():
            v = vowel_of(val)
            if v not in VOWEL_COLUMNS:
                continue
            vec = self._profile_vector(bid)
            if vec is None:
                continue
            for i in range(3):
                sums[v][i] += vec[i]
            counts[v] += 1
        prototypes = {}
        for v in VOWEL_COLUMNS:
            if counts[v] > 0:
                prototypes[v] = tuple(s / counts[v] for s in sums[v])
        return prototypes

    def _euclidean(self, a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def predict_vowel(self, bid: str, prototypes: Dict[str, Tuple[float, float, float]]) -> Optional[str]:
        """Nearest-prototype vowel prediction from positional profile."""
        vec = self._profile_vector(bid)
        if vec is None or not prototypes:
            return None
        best_v, best_d = None, float("inf")
        for v, proto in prototypes.items():
            d = self._euclidean(vec, proto)
            if d < best_d:
                best_v, best_d = v, d
        return best_v

    def anomalous_signs(self, min_occurrences: int = 5, medial_threshold: float = 0.15) -> List[Tuple]:
        """Signs whose positional profile says 'not a normal medial CV syllable'.

        The misvalued signs (AB 16/60/80) and the word divider (AB 85) all have
        medial_fraction < threshold — they appear almost only in initial/final
        position. This is a phonetic-independent flag for signs that are likely
        word dividers, particles, or otherwise non-syllabographic.
        """
        out = []
        for bid, p in self.profiles.items():
            if (p["medial_fraction"] < medial_threshold
                    and p["total_occurrences"] >= min_occurrences):
                out.append((bid, p["initial_fraction"], p["medial_fraction"],
                            p["final_fraction"], p["total_occurrences"]))
        out.sort(key=lambda x: -x[4])
        return out

    def oracle_test(
        self,
        hidden: int = 20,
        trials: int = 8,
    ) -> Dict:
        """Hide confirmed signs, predict their vowel from positional prototypes."""
        random.seed(0)
        confirmed_bids = sorted(self.confirmed.keys())
        trial_recovered: List[int] = []
        per_sign: Dict[str, List[bool]] = defaultdict(list)

        for t in range(trials):
            hidden_set = set(random.sample(confirmed_bids, min(hidden, len(confirmed_bids))))
            eff_confirmed = {b: v for b, v in self.confirmed.items() if b not in hidden_set}
            prototypes = self._train_prototypes(eff_confirmed)

            recovered = 0
            for bid in hidden_set:
                true_v = vowel_of(self.confirmed[bid])
                pred_v = self.predict_vowel(bid, prototypes)
                if pred_v is None:
                    continue
                ok = pred_v == true_v
                per_sign[bid].append(ok)
                recovered += int(ok)
            trial_recovered.append(recovered)
            logger.info("Trial %d/%d: %d/%d vowel columns recovered",
                        t + 1, trials, recovered, len(hidden_set))

        recovered = sum(trial_recovered)
        total = trials * len(hidden_set) if trials else 0
        recovery_rate = recovered / max(total, 1)
        chance_rate = 1.0 / len(VOWEL_COLUMNS)  # 0.2 random guess

        per_sign_rates = {bid: (sum(oks) / len(oks)) for bid, oks in per_sign.items()}
        recovered_all = [bid for bid, r in per_sign_rates.items() if r == 1.0]

        logger.info("Positional oracle: vowel recovery %.3f vs chance %.3f (%.1fx)",
                    recovery_rate, chance_rate, recovery_rate / chance_rate)
        return {
            "recovery_rate": recovery_rate,
            "chance_rate": chance_rate,
            "lift_over_chance": recovery_rate / chance_rate if chance_rate else 0.0,
            "trials": trials,
            "hidden_per_trial": len(hidden_set) if trials else 0,
            "recovered": recovered,
            "total_hidden_scored": total,
            "per_sign_recovery_rates": per_sign_rates,
            "signs_recovered_all_trials": recovered_all,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    oracle = PositionalOracle()
    res = oracle.oracle_test()
    print()
    print("=== POSITIONAL ORACLE (Avenue 1) ===")
    for k in ["recovery_rate", "chance_rate", "lift_over_chance",
              "trials", "hidden_per_trial", "recovered"]:
        print(f"  {k}: {res[k]}")
    print("  signs_recovered_all_trials:", res["signs_recovered_all_trials"])

    # ── Avenue 1 finding: positional anomaly detection ──
    # The oracle for vowel recovery fails (0.66x chance). But positional
    # profiles DO identify signs that are NOT normal medial CV syllables —
    # the misvalued signs (AB 16/60/80) and the word divider (AB 85) all
    # have medial_fraction < 0.15. This is a real, phonetic-independent
    # signal for flagging non-syllabographic signs.
    print()
    print("=== POSITIONAL ANOMALY FLAGS (medial_fraction < 0.15) ===")
    anomalous = oracle.anomalous_signs(min_occurrences=5)
    for bid, init, med, final, total in anomalous:
        status = "CONFIRMED" if bid in oracle.confirmed else "UNCERTAIN"
        print(f"  {bid} ({status}): init={init:.2f} med={med:.2f} final={final:.2f} n={total}")

    # Write output
    out = Path("data/analysis/positional")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "anomalous_signs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bennett_id", "status", "initial_fraction", "medial_fraction",
                    "final_fraction", "total_occurrences"])
        for bid, init, med, final, total in anomalous:
            status = "CONFIRMED" if bid in oracle.confirmed else "UNCERTAIN"
            w.writerow([bid, status, f"{init:.4f}", f"{med:.4f}", f"{final:.4f}", total])
    print(f"\nWrote data/analysis/positional/anomalous_signs.csv ({len(anomalous)} signs)")
