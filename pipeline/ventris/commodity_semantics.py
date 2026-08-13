"""Phase 11, Avenue 2 — "Reverse Rosetta": commodity logograms as semantic anchors.

The Ventris scorer failed (oracle: no signal). But logograms are *semantically*
known even though phonetically unreadable. If a syllabogram co-occurs with a
commodity logogram (GRAIN, OLIVE_OIL, VESSELS...) far beyond chance, it's likely
that commodity's word, a measure word, or a qualifier.

Phase 5/7 did *descriptive* co-occurrence (top syllabograms per commodity).
Avenue 2 adds the missing piece: a **statistical significance test** — is the
association beyond chance?

Method: hypergeometric enrichment (exact, no scipy needed).
For each (commodity, sign) pair:
  N  = total adjacent syllabogram slots across all contexts
  K  = times this sign appears in any adjacent slot
  n  = adjacent slots belonging to this commodity's contexts
  k  = times this sign appears in this commodity's slots
  P(X >= k) = 1 - CDF_hypergeom(N, K, n, k-1)
  -- probability of seeing this many co-occurrences by chance.
Low p-value = sign is significantly enriched in this commodity's context.

Usage:
    uv run python pipeline/ventris/commodity_semantics.py
"""

from __future__ import annotations

import csv
import logging
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def _log_comb(n: int, k: int) -> float:
    """log(C(n,k)) via lgamma — stable for large n."""
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def hypergeom_tail(N: int, K: int, n: int, k: int) -> float:
    """P(X >= k) under hypergeometric(N, K, n).

    N = population, K = successes in population, n = draws, k = observed successes.
    Computes the upper tail by summing log-probabilities (stable for small counts).
    """
    if k <= 0:
        return 1.0
    if k > min(K, n):
        return 0.0
    # log P(X = i) for i from k up to min(K, n)
    p = 0.0
    for i in range(k, min(K, n) + 1):
        logp = _log_comb(K, i) + _log_comb(N - K, n - i) - _log_comb(N, n)
        p += math.exp(logp)
    return min(1.0, p)


def load_contexts(path: str = "data/analysis/commodity_decoding/logogram_contexts.csv") -> List[Dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def adjacent_slots(row: Dict) -> List[str]:
    """All adjacent syllabogram bennett_ids for one context row."""
    slots = []
    for side in ("before", "after"):
        for off in ("1", "2", "3"):
            bid = row.get(f"{side}_{off}_bennett", "").strip()
            typ = row.get(f"{side}_{off}_type", "").strip()
            if bid and typ == "syllabogram":
                slots.append(bid)
    return slots


class CommoditySemantics:
    """Hypergeometric enrichment of syllabograms against commodity logograms."""

    def __init__(self, contexts_path: str = "data/analysis/commodity_decoding/logogram_contexts.csv") -> None:
        self.rows = load_contexts(contexts_path)
        # Commodity → list of adjacent syllabogram slots
        self.commodity_slots: Dict[str, List[str]] = defaultdict(list)
        for r in self.rows:
            cc = r.get("commodity_class", "").strip()
            if not cc:
                continue
            self.commodity_slots[cc].extend(adjacent_slots(r))
        # Total population: all adjacent slots across all contexts
        self.all_slots: List[str] = [s for slots in self.commodity_slots.values() for s in slots]
        self.N = len(self.all_slots)
        self.sign_totals: Counter = Counter(self.all_slots)
        logger.info("CommoditySemantics: %d contexts, %d total adjacent syllabogram slots",
                     len(self.rows), self.N)

    def enrichments(self, commodity: str, min_sign_total: int = 3) -> List[Tuple]:
        """Signs significantly enriched in a commodity's context.

        Returns sorted list of (sign, k, n, p_value, fold_enrichment).
        """
        slots = self.commodity_slots.get(commodity, [])
        n = len(slots)
        if n == 0:
            return []
        sign_counts = Counter(slots)
        out = []
        for sign, k in sign_counts.items():
            K = self.sign_totals.get(sign, 0)
            if K < min_sign_total:
                continue
            p = hypergeom_tail(self.N, K, n, k)
            # Fold enrichment: observed proportion vs global proportion
            expected = K / self.N * n
            fold = k / expected if expected > 0 else float("inf")
            out.append((sign, k, n, p, fold))
        out.sort(key=lambda x: x[3])  # by p-value
        return out

    def significant_signs(self, commodity: str, alpha: float = 0.05,
                          min_sign_total: int = 3) -> List[Tuple]:
        """Signs with p < alpha (uncorrected) in a commodity's context."""
        return [e for e in self.enrichments(commodity, min_sign_total)
                if e[3] < alpha]

    def bonferroni_alpha(self, commodities: List[str], alpha: float = 0.05,
                         min_sign_total: int = 3) -> float:
        """Family-wise alpha after Bonferroni over all (commodity, sign) tests."""
        n_tests = sum(len(self.enrichments(cc, min_sign_total))
                      for cc in commodities)
        return alpha / max(n_tests, 1), n_tests

    def significant_bonferroni(self, commodity: str, alpha: float = 0.05,
                               min_sign_total: int = 3) -> List[Tuple]:
        """Signs surviving Bonferroni correction (family-wise alpha)."""
        fam_alpha, _ = self.bonferroni_alpha(
            list(self.commodity_slots.keys()), alpha, min_sign_total)
        return [e for e in self.enrichments(commodity, min_sign_total)
                if e[3] < fam_alpha]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cs = CommoditySemantics()

    # Test commodities with enough contexts
    targets = ["GRAIN", "OLIVE_OIL", "VESSELS", "MANPOWER", "LIVESTOCK", "WINE"]
    print("=== AVENUE 2: SIGN-COMMODITY ENRICHMENT (hypergeometric p) ===\n")
    fam_alpha, n_tests = cs.bonferroni_alpha(list(cs.commodity_slots.keys()))
    print(f"(Bonferroni family-wise alpha = {fam_alpha:.5f} over {n_tests} tests)\n")
    for cc in targets:
        slots = cs.commodity_slots.get(cc, [])
        sig = cs.significant_signs(cc)
        sig_bonf = cs.significant_bonferroni(cc)
        print(f"{cc} ({len(slots)} adjacent slots):")
        if not sig:
            print("  no significant associations at p<0.05")
        for sign, k, n, p, fold in sig[:8]:
            star = " *" if p < fam_alpha else ""
            print(f"  {sign}: k={k}/{n} p={p:.4f} fold={fold:.1f}x{star}")
        if not sig_bonf:
            print("  (nothing survives Bonferroni)")
        print()

    # Output
    out = Path("data/analysis/commodity_decoding")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "sign_commodity_enrichment.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commodity_class", "sign", "cooccurrences", "slots",
                    "p_value", "fold_enrichment"])
        for cc in targets:
            for sign, k, n, p, fold in cs.enrichments(cc):
                w.writerow([cc, sign, k, n, f"{p:.6f}", f"{fold:.2f}"])
    print(f"Wrote data/analysis/commodity_decoding/sign_commodity_enrichment.csv")
