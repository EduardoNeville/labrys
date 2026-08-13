"""Phase 11, Avenue 3 — Statistical cryptanalysis of the raw sign stream.

The Ventris scorer failed at the *grammar* level (morphology/prefix/entropy
had no signal). Avenue 3 asks a more basic question: is there exploitable
STATISTICAL structure in the raw sign sequence itself, independent of any
phonetic or grammatical assumption?

Tests (all phonetic-independent, operate on raw bennett_id sign sequences):
1. Zipf's law — does sign frequency follow a power law (natural language)?
2. Bigram predictability — is P(sign2 | sign1) > P(sign2)? Sequential dependency
   beyond chance (a language-like signal the sign-level scorer collapsed).
3. Entropy rate / compressibility — how predictable is the stream?
4. Vowel-class structure via Kober V-links — do signs that share a vowel
   (per Kober) show stronger bigram cohesion than chance?

If the raw stream shows language-like statistics, the failed scorer's problem
was the *grammatical hypothesis*, not the data. If it shows near-random
structure, the corpus is too small/degenerate for ANY statistical attack.

Usage:
    uv run python pipeline/ventris/cryptanalysis.py
"""

from __future__ import annotations

import csv
import logging
import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def load_sequences(db_path: str = "data/database/lineara_full.db",
                   min_len: int = 5) -> List[List[str]]:
    """Load all syllabogram-only sign sequences (min_len or longer)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT i.id, s.sequence, s.bennett_id
        FROM signs s JOIN inscriptions i ON s.inscription_id = i.id
        WHERE s.sign_type = 'syllabogram' AND s.bennett_id != ''
        ORDER BY i.id, s.sequence
    """)
    seqs: Dict[int, List[str]] = {}
    for row in c.fetchall():
        seqs.setdefault(row["id"], []).append(row["bennett_id"])
    conn.close()
    return [s for s in seqs.values() if len(s) >= min_len]


def zipf_check(seqs: List[List[str]]) -> Dict:
    """Check if sign frequency follows a power law (Zipf)."""
    counts = Counter(s for seq in seqs for s in seq)
    ranked = sorted(counts.values(), reverse=True)
    n = len(ranked)
    # Fit log-log slope: log(freq) ~ -alpha * log(rank)
    if n < 5:
        return {"n_signs": n, "alpha": None}
    xs = [math.log(i + 1) for i in range(n)]
    ys = [math.log(c) for c in ranked]
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    alpha = -num / den if den else 0.0
    # R^2
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = 0.0
    for x, y in zip(xs, ys):
        y_hat = my + (-alpha) * (x - mx)
        ss_res += (y - y_hat) ** 2
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {"n_signs": n, "alpha": alpha, "r2": r2,
            "top5": ranked[:5]}


def bigram_predictability(seqs: List[List[str]]) -> Dict:
    """Compare P(s2|s1) vs P(s2): sequential dependency beyond chance.

    Computes average conditional entropy H(s2|s1) vs marginal H(s2).
    If H(s2|s1) << H(s2), there is real sequential structure.
    """
    unigrams = Counter()
    bigrams = Counter()
    for seq in seqs:
        for i in range(len(seq) - 1):
            unigrams[seq[i + 1]] += 1
            bigrams[(seq[i], seq[i + 1])] += 1
    total_unig = sum(unigrams.values())
    total_big = sum(bigrams.values())
    if total_big == 0 or total_unig == 0:
        return {}
    # Marginal entropy H(s2)
    h_marg = -sum((c / total_unig) * math.log2(c / total_unig)
                  for c in unigrams.values())
    # Conditional entropy H(s2|s1) from bigram counts
    h_cond = 0.0
    ctx_total = Counter()
    ctx_bigrams = defaultdict(Counter)
    for (s1, s2), cnt in bigrams.items():
        ctx_total[s1] += cnt
        ctx_bigrams[s1][s2] += cnt
    for s1, tot in ctx_total.items():
        for s2, cnt in ctx_bigrams[s1].items():
            p = cnt / tot
            h_cond -= (tot / total_big) * p * math.log2(p)
    # Reduction: how much does knowing s1 reduce uncertainty about s2?
    reduction = h_marg - h_cond
    return {
        "H_marginal": h_marg,
        "H_conditional": h_cond,
        "reduction": reduction,
        "reduction_frac": reduction / h_marg if h_marg else 0.0,
        "n_bigrams": total_big,
    }


def load_kober_vlinks(path: str = "data/analysis/kober/triple_patterns.csv") -> Dict[str, set]:
    """Load Kober V-links (signs sharing a vowel column)."""
    vlinks = defaultdict(set)
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                s1, s2, s3 = (row.get("sign_1", ""), row.get("sign_2", ""),
                              row.get("sign_3", ""))
                for a, b in [(s1, s2), (s1, s3), (s2, s3)]:
                    if a and b and a != b:
                        vlinks[a].add(b)
                        vlinks[b].add(a)
    except FileNotFoundError:
        logger.warning("Kober triples not found")
    return dict(vlinks)


def vowel_class_cohesion(seqs: List[List[str]]) -> Dict:
    """Do Kober-vowel-linked signs show bigram cohesion beyond chance?

    If signs sharing a vowel (per Kober V-links) appear as bigrams more than
    chance, that's a vowel-harmony-like signal — language structure the
    sign-level scorer couldn't see.
    """
    vlinks = load_kober_vlinks()
    # Observed: fraction of adjacent pairs that are V-linked
    linked_pairs = 0
    total_pairs = 0
    for seq in seqs:
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            if a != b:
                total_pairs += 1
                if b in vlinks.get(a, set()):
                    linked_pairs += 1
    if total_pairs == 0:
        return {}
    observed = linked_pairs / total_pairs
    # Chance: expected fraction of random sign pairs that are V-linked
    # = sum over signs of P(a) * (degree_v(a) / N_signs)
    counts = Counter(s for seq in seqs for s in seq)
    N = sum(counts.values())
    n_signs = len(counts)
    expected = 0.0
    for sign, cnt in counts.items():
        deg = len(vlinks.get(sign, set()))
        expected += (cnt / N) * (deg / max(n_signs, 1))
    return {
        "observed_fraction": observed,
        "chance_fraction": expected,
        "lift": observed / expected if expected else 0.0,
        "linked_pairs": linked_pairs,
        "total_pairs": total_pairs,
        "n_signs": n_signs,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seqs = load_sequences()
    logger.info("Loaded %d sequences (min_len=5)", len(seqs))

    print("=== AVENUE 3: STATISTICAL CRYPTANALYSIS ===\n")

    z = zipf_check(seqs)
    print(f"Zipf: {z['n_signs']} signs, alpha={z['alpha']:.3f} (R^2={z['r2']:.3f})")
    print(f"  (natural language: alpha~1.0, R^2 high; random: alpha~0, flat)")

    b = bigram_predictability(seqs)
    if b:
        print(f"\nBigram: H(s2|s1)={b['H_conditional']:.3f} vs H(s2)={b['H_marginal']:.3f}")
        print(f"  reduction={b['reduction']:.3f} bits ({b['reduction_frac']*100:.1f}% of uncertainty removed)")

    v = vowel_class_cohesion(seqs)
    if v:
        print(f"\nKober V-link cohesion: observed={v['observed_fraction']:.4f} vs chance={v['chance_fraction']:.4f}")
        print(f"  lift={v['lift']:.2f}x ({v['linked_pairs']}/{v['total_pairs']} adjacent pairs V-linked)")

    print("\n(All metrics phonetic-independent — raw sign sequences, no values assumed)")
