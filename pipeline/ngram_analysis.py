#!/usr/bin/env python3
"""
N-Gram Language Modeling, Phonotactic & Entropy Analysis for Linear A
=====================================================================

Performs:
  1) Sign-level n-gram frequency tables (n=1..5)
  2) Character-level (transliteration) n-gram frequencies
  3) Conditional entropy H(sign_n | sign_{n-1}, ..., sign_{n-k}) for k=1..3
  4) Positional entropy (how uniformly a sign distributes across positions)
  5) Mutual information between adjacent signs
  6) Phonotactic summary (CV structure, syllable pattern frequencies)
  7) Bigram disruption scan — identify misvalued signs by comparing
     transition profiles to phonetic-class expectations
  8) Language typology comparison statistics

All outputs written to data/analysis/ngram/

Dependencies: sqlite3, csv, math, collections (stdlib only).
No pandas, matplotlib, or networkx required.
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
import sqlite3
import sys
from collections import Counter, defaultdict, OrderedDict
from typing import Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ngram_analysis")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(BASE_DIR, "data", "database", "lineara_full.db")
DEFAULT_OUT = os.path.join(BASE_DIR, "data", "analysis", "ngram")

# ---------------------------------------------------------------------------
# AB phonetic grid (transferred from Linear B)
# Same as in positional_analysis.py
# ---------------------------------------------------------------------------

AB_PHONETIC_GRID: list[tuple[str, str, str]] = [
    ("AB 01", "da",  "CV"),
    ("AB 02", "ro",  "CV"),
    ("AB 03", "pa",  "CV"),
    ("AB 04", "te",  "CV"),
    ("AB 05", "to",  "CV"),
    ("AB 06", "na",  "CV"),
    ("AB 07", "di",  "CV"),
    ("AB 08", "a",   "V"),
    ("AB 09", "se",  "CV"),
    ("AB 10", "u",   "V"),
    ("AB 11", "si",  "CV"),
    ("AB 12", "so",  "CV"),
    ("AB 13", "me",  "CV"),
    ("AB 14", "do",  "CV"),
    ("AB 15", "mo",  "CV"),
    ("AB 16", "qa",  "CV"),
    ("AB 17", "za",  "CV"),
    ("AB 18", "zo",  "CV"),
    ("AB 19", "?,zo?", "?"),
    ("AB 20", "zo?", "?"),
    ("AB 21", "mi",  "CV"),
    ("AB 21f", "mi?", "?"),
    ("AB 22", "pi",  "CV"),
    ("AB 22f", "pi?", "?"),
    ("AB 23", "mu",  "CV"),
    ("AB 24", "ne",  "CV"),
    ("AB 26", "ru",  "CV"),
    ("AB 27", "re",  "CV"),
    ("AB 28", "i",   "V"),
    ("AB 29", "pu",  "CV"),
    ("AB 30", "ni",  "CV"),
    ("AB 31", "sa",  "CV"),
    ("AB 32", "?",   "?"),
    ("AB 33", "ra?", "?"),
    ("AB 34", "?,pa2?", "?"),
    ("AB 35", "ti",  "CV"),
    ("AB 36", "jo",  "CV"),
    ("AB 37", "?",   "?"),
    ("AB 38", "e",   "V"),
    ("AB 39", "?,pi?", "?"),
    ("AB 40", "wi",  "CV"),
    ("AB 41", "si?", "?"),
    ("AB 42", "ke?", "?"),
    ("AB 43", "ai?", "?"),
    ("AB 44", "?",   "?"),
    ("AB 45", "?,de?", "?"),
    ("AB 46", "?,je?", "?"),
    ("AB 47", "?",   "?"),
    ("AB 48", "?,nwa?", "?"),
    ("AB 49", "?",   "?"),
    ("AB 50", "pu?", "?"),
    ("AB 51", "du?", "?"),
    ("AB 52", "?",   "?"),
    ("AB 53", "ri",  "CV"),
    ("AB 54", "wa",  "CV"),
    ("AB 55", "nu",  "CV"),
    ("AB 56", "?",   "?"),
    ("AB 57", "ja",  "CV"),
    ("AB 58", "?",   "?"),
    ("AB 59", "?",   "?"),
    ("AB 60", "ra",  "CV"),
    ("AB 61", "?",   "?"),
    ("AB 62", "?,pte?", "?"),
    ("AB 63", "?",   "?"),
    ("AB 64", "?,swi?", "?"),
    ("AB 65", "ju?", "?"),
    ("AB 66", "ta?", "?"),
    ("AB 67", "ki",  "CV"),
    ("AB 68", "ro2?", "?"),
    ("AB 69", "tu",  "CV"),
    ("AB 70", "?,ko?", "?"),
    ("AB 71", "?",   "?"),
    ("AB 72", "?",   "?"),
    ("AB 73", "?",   "?"),
    ("AB 74", "ze?", "?"),
    ("AB 75", "?",   "?"),
    ("AB 76", "ra2?", "?"),
    ("AB 77", "ka",  "CV"),
    ("AB 78", "qe",  "CV"),
    ("AB 79", "zo?", "?"),
    ("AB 80", "ma",  "CV"),
    ("AB 81", "ku",  "CV"),
    ("AB 82", "?",   "?"),
    ("AB 83", "?",   "?"),
    ("AB 84", "?",   "?"),
    ("AB 85", "?",   "?"),
    ("AB 86", "?",   "?"),
    ("AB 87", "?",   "?"),
    ("AB 88", "?",   "?"),
    ("AB 89", "?",   "?"),
    ("AB 90", "?",   "?"),
    ("AB 91", "?",   "?"),
    ("AB 92", "?",   "?"),
    ("AB 93", "?",   "?"),
    ("AB 94", "?",   "?"),
    ("AB 95", "?",   "?"),
    ("AB 96", "?",   "?"),
    ("AB 97", "?",   "?"),
    ("AB 98", "?",   "?"),
    ("AB 99", "?",   "?"),
    ("AB 100", "?",  "?"),
    ("AB 101", "?",  "?"),
    ("AB 102", "?",  "?"),
    ("AB 103", "?",  "?"),
    ("AB 104", "?",  "?"),
    ("AB 105", "?",  "?"),
    ("AB 106", "?",  "?"),
    ("AB 107", "?",  "?"),
    ("AB 108", "?",  "?"),
    ("AB 109", "?",  "?"),
    ("AB 110", "?",  "?"),
    ("AB 111", "?",  "?"),
    ("AB 112", "?",  "?"),
    ("AB 113", "?",  "?"),
    ("AB 114", "?",  "?"),
    ("AB 115", "?",  "?"),
    ("AB 116", "?",  "?"),
    ("AB 117", "?",  "?"),
    ("AB 118", "?",  "?"),
    ("AB 119", "?",  "?"),
    ("AB 120", "?",  "?"),
    ("AB 121", "?",  "?"),
    ("AB 122", "?",  "?"),
    ("AB 123", "?",  "?"),
    ("AB 124", "?",  "?"),
    ("AB 125", "?",  "?"),
    ("AB 126", "?",  "?"),
    ("AB 127", "?",  "?"),
    ("AB 128", "?",  "?"),
    ("AB 129", "?",  "?"),
    ("AB 130", "?",  "?"),
    ("AB 131", "?",  "?"),
    ("AB 132", "?",  "?"),
    ("AB 133", "?",  "?"),
    ("AB 134", "?",  "?"),
    ("AB 135", "?",  "?"),
    ("AB 136", "?",  "?"),
    ("AB 137", "?",  "?"),
]

_AB_GRID: dict[str, dict[str, str]] = {}
for _ben, _trans, _cls in AB_PHONETIC_GRID:
    _AB_GRID[_ben] = {"transliteration": _trans, "phonetic_class": _cls}

# Vowel set for CV analysis
VOWEL_LETTERS = frozenset("aeiouAEIOU")

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def entropy(probs: list[float]) -> float:
    """Shannon entropy (base 2) of a probability distribution."""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def kl_divergence(p: list[float], q: list[float]) -> float:
    """KL divergence D_KL(p || q). Both should be valid probability vectors."""
    return sum(p[i] * math.log2(p[i] / q[i]) if p[i] > 0 else 0.0 for i in range(len(p)))


def smooth_add_k(counts: dict, k: float = 1.0) -> dict:
    """Add-k smoothing. Returns probabilities as OrderedDict matching input key order."""
    n_types = len(counts)
    total = sum(counts.values()) + k * n_types
    result = OrderedDict()
    for key in counts:
        result[key] = (counts[key] + k) / total
    return result


def is_cv_syllable(s: str) -> str:
    """
    Classify a transliteration string into a structural type:
      V, CV, VC, CVC, VV, CCV, CVV, CCVC, CVCC, CCVCC, complex, other
    Returns a string label.
    """
    if not s:
        return "other"
    # Map each char to C or V
    # Handle diphthong digraphs? For Linear A, simple approach.
    pattern = []
    for ch in s:
        if ch in VOWEL_LETTERS:
            pattern.append("V")
        else:
            pattern.append("C")

    # Collapse consecutive same-type? No, keep raw.
    raw = "".join(pattern)

    # Common patterns
    cv_map = {
        "V": "V",
        "CV": "CV",
        "VC": "VC",
        "CVC": "CVC",
        "VV": "VV",
        "CCV": "CCV",
        "CVV": "CVV",
        "CCVC": "CCVC",
        "CVCC": "CVCC",
        "CCVCC": "CCVCC",
        "CCCV": "CCCV",
        "CCCVV": "CCCVV",
        "CVVCC": "CVVCC",
        "VVV": "VVV",
    }
    if raw in cv_map:
        return cv_map[raw]

    # If it's long, call it "complex"
    if len(raw) >= 6:
        return "complex"
    return f"other:{raw}"


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def load_corpus(db_path: str) -> tuple[list[list[dict]], list[list[dict]]]:
    """
    Load two parallel views of the corpus:

    1. syllabograms_only — only syllabogram signs with a Bennett ID.
       Used for sign-level n-gram analysis.

    2. all_signs — all signs including logograms, numerals etc.
       Used for character-level (transliteration) analysis.

    Returns:
        (syllabograms_only, all_signs)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""SELECT id, gorila_id FROM inscriptions ORDER BY id""")
    inscriptions = cursor.fetchall()
    logger.info("Loaded %d inscriptions from database", len(inscriptions))

    syllabograms_only: list[list[dict]] = []
    all_signs: list[list[dict]] = []

    for ins in inscriptions:
        cursor.execute(
            """SELECT sequence, bennett_id, sign_type, transliteration, character
               FROM signs WHERE inscription_id = ? ORDER BY sequence""",
            (ins["id"],),
        )
        rows = [dict(r) for r in cursor.fetchall()]

        # All signs for character-level analysis
        all_seq = []
        for r in rows:
            all_seq.append({
                "sequence": r["sequence"],
                "bennett_id": r["bennett_id"] or "",
                "sign_type": r["sign_type"] or "syllabogram",
                "transliteration": (r["transliteration"] or "").strip(),
                "character": r["character"] or "",
            })
        if all_seq:
            all_signs.append(all_seq)

        # Syllabograms only (for sign-level analysis)
        s_seq = [r for r in all_seq if r["sign_type"] == "syllabogram" and r["bennett_id"]]
        if s_seq:
            syllabograms_only.append(s_seq)

    conn.close()
    logger.info(
        "Extracted %d syllabogram sequences, %d all-sign sequences",
        len(syllabograms_only), len(all_signs),
    )
    return syllabograms_only, all_signs


# ---------------------------------------------------------------------------
# N-gram counter
# ---------------------------------------------------------------------------

def count_ngrams(sequences: list[list[dict]],
                 key_func,
                 max_n: int = 5) -> dict[int, Counter]:
    """
    Count n-grams for n = 1 .. max_n.

    Args:
        sequences: list of sign sequences (each a list of dicts)
        key_func: callable(sign_dict) -> str (the token for that sign)
        max_n: maximum n-gram order

    Returns:
        dict[n] -> Counter of n-gram tuples
    """
    ngram_counts: dict[int, Counter] = {n: Counter() for n in range(1, max_n + 1)}

    for seq in sequences:
        tokens = [key_func(s) for s in seq]
        L = len(tokens)
        for n in range(1, max_n + 1):
            for i in range(L - n + 1):
                gram = tuple(tokens[i: i + n])
                ngram_counts[n][gram] += 1

    return ngram_counts


def ngram_counts_to_csv(ngram_counts: dict[int, Counter],
                        output_path: str,
                        label: str = "sign"):
    """
    Write n-gram counts and probabilities to a single CSV file.
    Columns: n, gram, count, probability
    """
    rows = []
    for n in range(1, max(ngram_counts.keys()) + 1):
        cnt = ngram_counts[n]
        total = sum(cnt.values())
        if total == 0:
            continue
        for gram, count in cnt.most_common():
            prob = count / total
            gram_str = " ".join(gram)
            rows.append({
                "n": n,
                "gram": gram_str,
                "count": count,
                "probability": prob,
                "type": label,
            })

    rows.sort(key=lambda r: (r["n"], -r["count"]))

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["n", "gram", "count", "probability", "type"])
        writer.writeheader()
        for r in rows:
            r["probability"] = f"{r['probability']:.8f}"
            writer.writerow(r)

    total_ngrams = sum(len(cnt) for cnt in ngram_counts.values())
    logger.info("Wrote %d n-gram entries (%s) to %s", len(rows), label, output_path)
    return len(rows)


# ---------------------------------------------------------------------------
# Conditional entropy
# ---------------------------------------------------------------------------

def compute_conditional_entropy(sequences: list[list[dict]],
                                key_func,
                                k_values: list[int] = None) -> list[dict]:
    """
    Compute H(sign_n | sign_{n-1}, ..., sign_{n-k}) for k in k_values.

    Uses the empirical conditional distribution P(sign_n | context).

    Returns list of dicts with keys: k, total_contexts, entropy, perplexity
    """
    if k_values is None:
        k_values = [1, 2, 3]

    results = []

    for k in k_values:
        context_counts: dict[tuple, Counter] = defaultdict(Counter)
        total_events = 0

        for seq in sequences:
            tokens = [key_func(s) for s in seq]
            L = len(tokens)
            for i in range(k, L):
                context = tuple(tokens[i - k: i])
                next_token = tokens[i]
                context_counts[context][next_token] += 1
                total_events += 1

        if total_events == 0:
            results.append({
                "k": k,
                "total_events": 0,
                "unique_contexts": 0,
                "entropy": None,
                "perplexity": None,
            })
            continue

        # Compute H = sum_c P(c) * H(sign | c)
        # H(sign | c) = - sum_s P(s|c) log2 P(s|c)
        total_entropy = 0.0
        for context, next_counts in context_counts.items():
            context_total = sum(next_counts.values())
            p_context = context_total / total_events
            # Entropy of the conditional distribution
            cond_ent = 0.0
            for cnt in next_counts.values():
                p = cnt / context_total
                cond_ent -= p * math.log2(p)
            total_entropy += p_context * cond_ent

        perplexity = 2 ** total_entropy if total_entropy > 0 else 1.0

        results.append({
            "k": k,
            "total_events": total_events,
            "unique_contexts": len(context_counts),
            "entropy": total_entropy,
            "perplexity": perplexity,
        })

    return results


# ---------------------------------------------------------------------------
# Positional entropy
# ---------------------------------------------------------------------------

def compute_positional_entropy(sequences: list[list[dict]],
                               key_func) -> list[dict]:
    """
    For each sign type, compute its distribution across positions within
    each text, and the positional entropy.

    Uses same position logic as positional_analysis.py:
      - L==1: sign is both initial and final
      - L==2: sign[0]=initial, sign[1]=final
      - L>=3: sign[0]=initial, sign[L-1]=final, rest=medial

    Also computes distribution across ordinal positions (1st, 2nd, 3rd, ...)
    as a fraction of text length, to detect signs that favour specific
    absolute positions.

    Returns list of dicts per sign.
    """
    pos_counts: dict[str, dict[str, float]] = defaultdict(lambda: {"initial": 0, "medial": 0, "final": 0})
    total_occurrences: dict[str, int] = defaultdict(int)

    # Relative position bins
    REL_BINS = 10
    rel_counts: dict[str, list[int]] = defaultdict(lambda: [0] * REL_BINS)

    for seq in sequences:
        tokens = [key_func(s) for s in seq]
        L = len(tokens)
        for idx, token in enumerate(tokens):
            total_occurrences[token] += 1

            # Absolute position count (initial/medial/final)
            if L == 1:
                pos_counts[token]["initial"] += 1
                pos_counts[token]["final"] += 1
            elif L == 2:
                if idx == 0:
                    pos_counts[token]["initial"] += 1
                else:
                    pos_counts[token]["final"] += 1
            else:
                if idx == 0:
                    pos_counts[token]["initial"] += 1
                elif idx == L - 1:
                    pos_counts[token]["final"] += 1
                else:
                    pos_counts[token]["medial"] += 1

            # Relative position bin
            if L > 0:
                rel_pos = idx / (L - 1) if L > 1 else 0.5
                bin_idx = min(int(rel_pos * REL_BINS), REL_BINS - 1)
                rel_counts[token][bin_idx] += 1

    results = []
    for token in sorted(total_occurrences.keys()):
        total = total_occurrences[token]
        cnts = pos_counts[token]
        init_p = cnts["initial"] / total
        med_p = cnts["medial"] / total
        fin_p = cnts["final"] / total

        # Positional entropy (high = evenly distributed, low = position-biased)
        pos_ent = entropy([init_p, med_p, fin_p])
        # Max entropy for 3 categories = log2(3) ≈ 1.585
        max_ent = math.log2(3)
        pos_norm_ent = pos_ent / max_ent if max_ent > 0 else 0.0

        # Relative-position entropy
        rel_dist = rel_counts[token]
        rel_total = sum(rel_dist)
        if rel_total > 0:
            rel_probs = [c / rel_total for c in rel_dist]
            rel_ent = entropy(rel_probs)
            rel_max_ent = math.log2(REL_BINS)
            rel_norm_ent = rel_ent / rel_max_ent if rel_max_ent > 0 else 0.0
        else:
            rel_ent = 0.0
            rel_norm_ent = 0.0

        # Bias flag
        if init_p > 0.6:
            bias = "initial"
        elif fin_p > 0.6:
            bias = "final"
        elif abs(init_p - fin_p) < 0.1 and med_p > 0.3:
            bias = "flexible"
        else:
            bias = "mixed"

        results.append({
            "sign": token,
            "total_occurrences": total,
            "initial_count": int(cnts["initial"]),
            "medial_count": int(cnts["medial"]),
            "final_count": int(cnts["final"]),
            "initial_fraction": init_p,
            "medial_fraction": med_p,
            "final_fraction": fin_p,
            "positional_entropy": pos_ent,
            "normalized_positional_entropy": pos_norm_ent,
            "relative_bin_entropy": rel_ent,
            "relative_bin_entropy_normalized": rel_norm_ent,
            "bias": bias,
        })

    return results


# ---------------------------------------------------------------------------
# Mutual information between adjacent signs
# ---------------------------------------------------------------------------

def compute_mutual_information(sequences: list[list[dict]],
                               key_func,
                               min_occurrences: int = 3) -> list[dict]:
    """
    Compute Pointwise Mutual Information (PMI) and Mutual Information (MI)
    for all adjacent bigrams.

    PMI(a,b) = log2( P(a,b) / (P(a) * P(b)) )
    I(a,b) = P(a,b) * PMI(a,b)

    Returns list of dicts, one per bigram pair.
    """
    unigram_counts: Counter = Counter()
    bigram_counts: Counter = Counter()

    for seq in sequences:
        tokens = [key_func(s) for s in seq]
        for tok in tokens:
            unigram_counts[tok] += 1
        for i in range(len(tokens) - 1):
            bigram_counts[(tokens[i], tokens[i + 1])] += 1

    total_unigrams = sum(unigram_counts.values())
    total_bigrams = sum(bigram_counts.values())

    if total_unigrams == 0 or total_bigrams == 0:
        return []

    results = []
    for (a, b), cnt in bigram_counts.items():
        if cnt < min_occurrences:
            continue

        p_ab = cnt / total_bigrams
        p_a = unigram_counts.get(a, 0) / total_unigrams
        p_b = unigram_counts.get(b, 0) / total_unigrams

        if p_a == 0 or p_b == 0:
            continue

        pmi = math.log2(p_ab / (p_a * p_b))
        mi_contribution = p_ab * pmi  # actual contribution to overall MI

        results.append({
            "sign_a": a,
            "sign_b": b,
            "count": cnt,
            "pmi": pmi,
            "mi_contribution": mi_contribution,
            "expected_count": total_bigrams * p_a * p_b,
            "log_ratio": math.log2(cnt / (total_bigrams * p_a * p_b)) if p_a * p_b > 0 else 0.0,
        })

    results.sort(key=lambda r: -r["pmi"])
    return results


# ---------------------------------------------------------------------------
# Phonotactic analysis
# ---------------------------------------------------------------------------

def analyze_phonotactics(sequences: list[list[dict]],
                         syllabograms_only: list[list[dict]]) -> dict:
    """
    Analyze phonotactic structure of the corpus.

    For signs with transliteration values, we classify each sign into
    a CV pattern. Then we compute:
      - Frequency of each CV pattern type
      - Bigram CV transitions
      - Syllable pattern frequencies
      - Mean sign length in characters
    """
    # --- CV classification of individual signs (using AB grid + transliteration) ---
    sign_cv: dict[str, str] = {}
    # Collect all unique signs from syllabograms
    all_syllabograms = set()
    for seq in syllabograms_only:
        for s in seq:
            bid = s["bennett_id"]
            if bid:
                all_syllabograms.add(bid)
                if bid in _AB_GRID:
                    trans = _AB_GRID[bid].get("transliteration", "")
                    if trans and trans != "?":
                        sign_cv[bid] = is_cv_syllable(trans)

    # For signs with transliteration directly in DB
    for seq in syllabograms_only:
        for s in seq:
            bid = s["bennett_id"]
            trans = s.get("transliteration", "")
            if bid and trans and trans != "?" and bid not in sign_cv:
                sign_cv[bid] = is_cv_syllable(trans)

    # --- Count CV patterns ---
    cv_counts: Counter = Counter()
    cv_bigram_counts: Counter = Counter()
    cv_trigram_counts: Counter = Counter()

    for seq in syllabograms_only:
        cv_seq = []
        for s in seq:
            bid = s["bennett_id"]
            cv = sign_cv.get(bid, "?")
            cv_seq.append(cv)

        for cv in cv_seq:
            cv_counts[cv] += 1
        for i in range(len(cv_seq) - 1):
            cv_bigram_counts[(cv_seq[i], cv_seq[i + 1])] += 1
        for i in range(len(cv_seq) - 2):
            cv_trigram_counts[(cv_seq[i], cv_seq[i + 1], cv_seq[i + 2])] += 1

    # --- Transition probabilities ---
    cv_transitions = {}
    for (a, b), cnt in cv_bigram_counts.items():
        total_a = sum(v for (ka, _), v in cv_bigram_counts.items() if ka == a)
        if total_a > 0:
            cv_transitions[f"{a}->{b}"] = {
                "from": a,
                "to": b,
                "count": cnt,
                "probability": cnt / total_a,
            }

    # --- Syllable pattern frequencies (sequences of CV types) ---
    syllable_patterns: Counter = Counter()
    for seq in syllabograms_only:
        cv_seq = [sign_cv.get(s["bennett_id"], "?") for s in seq]
        # Encode as string for pattern counting
        for n in [2, 3, 4]:
            for i in range(len(cv_seq) - n + 1):
                pat = " ".join(cv_seq[i: i + n])
                syllable_patterns[pat] += 1

    # --- Aggregate statistics ---
    total_cv = sum(cv_counts.values())
    cv_dist = {k: {"count": v, "fraction": v / total_cv} for k, v in cv_counts.most_common()}

    return {
        "sign_cv_mapping": {k: v for k, v in sorted(sign_cv.items())},
        "cv_type_counts": {k: v for k, v in cv_counts.most_common()},
        "cv_type_frequencies": cv_dist,
        "cv_bigram_transitions": cv_transitions,
        "cv_trigram_counts": {str(k): v for k, v in cv_trigram_counts.most_common(200)},
        "syllable_patterns": {k: v for k, v in syllable_patterns.most_common(200)},
    }


# ---------------------------------------------------------------------------
# Bigram disruption scan (misvalued signs)
# ---------------------------------------------------------------------------

def bigram_disruption_scan(sequences: list[list[dict]],
                           key_func) -> list[dict]:
    """
    For each AB sign with a known (or tentatively assigned) phonetic value,
    compute its bigram transition profile — the set of signs that precede
    and follow it — and compare against the expected profile for its
    phonetic class (V, CV, CVC, etc.).

    A "transition disruption score" is computed based on:
      1. How many of the sign's predecessors/followers are unexpected for
         its class
      2. How much the sign's bigram entropy diverges from its class mean
      3. How many of its top collocates are typically associated with a
         *different* phonetic class

    Returns list of dicts sorted by disruption score (descending).
    """
    # Build forward/backward bigram counts
    fwd_counts: dict[str, Counter] = defaultdict(Counter)  # sign_a -> {sign_b: count}
    bwd_counts: dict[str, Counter] = defaultdict(Counter)  # sign_b -> {sign_a: count}

    for seq in sequences:
        tokens = [key_func(s) for s in seq]
        for i in range(len(tokens) - 1):
            a, b = tokens[i], tokens[i + 1]
            fwd_counts[a][b] += 1
            bwd_counts[b][a] += 1

    # For each AB sign with a known phonetic class, compute metrics
    class_signs: dict[str, list[str]] = defaultdict(list)
    for bid, info in _AB_GRID.items():
        cls = info["phonetic_class"]
        if cls != "?":
            class_signs[cls].append(bid)

    # Compute class-level aggregated bigram profiles
    class_fwd_profiles: dict[str, Counter] = defaultdict(Counter)
    class_bwd_profiles: dict[str, Counter] = defaultdict(Counter)
    class_total_fwd: dict[str, float] = defaultdict(float)

    for cls, signs in class_signs.items():
        for sign in signs:
            if sign in fwd_counts:
                for follower, cnt in fwd_counts[sign].items():
                    class_fwd_profiles[cls][follower] += cnt
                    class_total_fwd[cls] += cnt
            if sign in bwd_counts:
                for precursor, cnt in bwd_counts[sign].items():
                    class_bwd_profiles[cls][precursor] += cnt

    # Compute class mean bigram entropy
    class_entropies: dict[str, list[float]] = defaultdict(list)
    for cls, signs in class_signs.items():
        for sign in signs:
            if sign in fwd_counts:
                follower_counts = list(fwd_counts[sign].values())
                total = sum(follower_counts)
                if total > 0:
                    probs = [c / total for c in follower_counts]
                    class_entropies[cls].append(entropy(probs))

    class_mean_fwd_entropy: dict[str, float] = {}
    for cls, ents in class_entropies.items():
        class_mean_fwd_entropy[cls] = sum(ents) / len(ents) if ents else 0.0

    # Compute disruption score for each AB sign
    results = []
    for bid, info in _AB_GRID.items():
        cls = info["phonetic_class"]
        if cls == "?" or cls not in class_signs:
            continue
        if bid not in fwd_counts and bid not in bwd_counts:
            continue

        # 1. Forward entropy
        fwd_ent = 0.0
        if bid in fwd_counts:
            f_cnts = list(fwd_counts[bid].values())
            f_total = sum(f_cnts)
            if f_total > 0:
                f_probs = [c / f_total for c in f_cnts]
                fwd_ent = entropy(f_probs)
        max_fwd_ent = math.log2(len(fwd_counts.get(bid, {})) or 1)

        # 2. Entropy divergence from class mean
        cls_mean_ent = class_mean_fwd_entropy.get(cls, 0.0)
        ent_divergence = abs(fwd_ent - cls_mean_ent) / (cls_mean_ent + 0.001)

        # 3. Profile overlap with class expectations
        # What fraction of this sign's followers are also common for its class?
        class_fwd = class_fwd_profiles.get(cls, {})
        class_total = class_total_fwd.get(cls, 0.0) or 1.0
        class_expected_followers = {k: v / class_total for k, v in class_fwd.items()}

        overlap_score = 0.0
        if bid in fwd_counts:
            follower_total = sum(fwd_counts[bid].values())
            for follower, cnt in fwd_counts[bid].items():
                p_obs = cnt / follower_total if follower_total > 0 else 0
                p_exp = class_expected_followers.get(follower, 0.0)
                # If the observed sign is rare in this class, that's anomalous
                if p_exp < 0.01 and p_obs > 0.05:
                    overlap_score += p_obs  # penalty

        # 4. Cross-class affinity: does this sign's followers look more like
        # those of another class?
        cross_class_scores = {}
        for other_cls, other_fwd in class_fwd_profiles.items():
            if other_cls == cls:
                continue
            other_total = class_total_fwd.get(other_cls, 0.0) or 1.0
            other_probs = {k: v / other_total for k, v in other_fwd.items()}
            sim = 0.0
            if bid in fwd_counts:
                for follower in fwd_counts[bid]:
                    sim += other_probs.get(follower, 0.0)
            cross_class_scores[other_cls] = sim

        # Find the most similar other class
        best_other = max(cross_class_scores, key=cross_class_scores.get) if cross_class_scores else None
        best_other_score = cross_class_scores.get(best_other, 0.0) if best_other else 0.0

        # 5. Composite disruption score
        #   - ent_divergence (weight 0.4)
        #   - overlap_score (weight 0.3)
        #   - cross_class_affinity (weight 0.3)
        disruption = (0.4 * ent_divergence + 0.3 * overlap_score + 0.3 * best_other_score)

        # Also compute the expected follower set
        expected_top_followers = sorted(class_fwd.items(), key=lambda x: -x[1])[:10]
        expected_top_followers_list = [s for s, _ in expected_top_followers]

        actual_top_followers = []
        if bid in fwd_counts:
            actual_top_followers = [s for s, _ in fwd_counts[bid].most_common(10)]

        # Followers that are in top-10 actual but NOT in top-10 expected
        anomalous_followers = [s for s in actual_top_followers if s not in expected_top_followers_list]

        results.append({
            "bennett_id": bid,
            "transliteration": info["transliteration"],
            "phonetic_class": cls,
            "total_followers": len(fwd_counts.get(bid, {})),
            "total_preceders": len(bwd_counts.get(bid, {})),
            "follower_entropy": fwd_ent,
            "max_follower_entropy": max_fwd_ent,
            "class_mean_follower_entropy": cls_mean_ent,
            "entropy_divergence": ent_divergence,
            "overlap_vs_class_expectation": 1.0 - overlap_score,
            "cross_class_affinity": best_other_score,
            "most_similar_other_class": best_other if best_other else "",
            "disruption_score": disruption,
            "anomalous_followers": "; ".join(anomalous_followers[:5]),
            "num_anomalous_followers": len(anomalous_followers),
            "expected_top_followers": "; ".join(expected_top_followers_list[:5]),
            "actual_top_followers": "; ".join(actual_top_followers[:5]),
        })

    results.sort(key=lambda r: -r["disruption_score"])
    return results


# ---------------------------------------------------------------------------
# Language typology comparison
# ---------------------------------------------------------------------------

def compute_typology_statistics(syllabograms_only: list[list[dict]],
                                all_sign_sequences: list[list[dict]],
                                key_func) -> dict:
    """
    Compute aggregate statistics for language typology comparison.

    Statistics:
      - Total sign tokens and types
      - Type-token ratio (TTR)
      - Repeat rate (sum of squared probabilities) / Simpson's index
      - Entropy of sign distribution (unigram)
      - Mean sequence length (proxy for word length once segmentation available)
      - Hapax count and proportion
      - Frequency distribution skew
    """
    # Build unigram counts
    unigram_counts: Counter = Counter()
    for seq in syllabograms_only:
        for s in seq:
            unigram_counts[key_func(s)] += 1

    total_tokens = sum(unigram_counts.values())
    total_types = len(unigram_counts)

    if total_tokens == 0:
        return {"error": "Empty corpus"}

    # Type-token ratio
    ttr = total_types / total_tokens if total_tokens > 0 else 0.0

    # Repeat rate (Simpson's index) = sum p_i^2
    repeat_rate = sum((c / total_tokens) ** 2 for c in unigram_counts.values())

    # Entropy
    ent = entropy([c / total_tokens for c in unigram_counts.values()])
    max_ent = math.log2(total_types) if total_types > 0 else 1.0
    norm_ent = ent / max_ent if max_ent > 0 else 0.0

    # Hapax count (signs appearing exactly once)
    hapax_count = sum(1 for c in unigram_counts.values() if c == 1)
    hapax_proportion = hapax_count / total_types if total_types > 0 else 0.0

    # Dis legomena
    dis_count = sum(1 for c in unigram_counts.values() if c == 2)

    # Mean sequence length
    seq_lengths = [len(seq) for seq in syllabograms_only]
    mean_seq_len = sum(seq_lengths) / len(seq_lengths) if seq_lengths else 0.0
    max_seq_len = max(seq_lengths) if seq_lengths else 0
    min_seq_len = min(seq_lengths) if seq_lengths else 0

    # Zipfian slope estimation (log-log rank-frequency)
    sorted_freqs = sorted(unigram_counts.values(), reverse=True)
    # Simple slope: log(f_1 / f_n) / log(n)
    if len(sorted_freqs) >= 10 and sorted_freqs[0] > 0 and sorted_freqs[-1] > 0:
        zipf_slope = (math.log10(sorted_freqs[0]) - math.log10(sorted_freqs[-1])) / math.log10(len(sorted_freqs))
    else:
        zipf_slope = 0.0

    # Frequency skew (ratio of top-1 to total)
    top1_freq = sorted_freqs[0] if sorted_freqs else 0
    top1_proportion = top1_freq / total_tokens if total_tokens > 0 else 0.0

    # Top-5 concentration
    top5_freq = sum(sorted_freqs[:5]) if len(sorted_freqs) >= 5 else sum(sorted_freqs)
    top5_proportion = top5_freq / total_tokens if total_tokens > 0 else 0.0

    # --- Also compute on all-sign level (including logograms) ---
    all_unigram: Counter = Counter()
    for seq in all_sign_sequences:
        for s in seq:
            all_unigram[key_func(s)] += 1

    all_tokens = sum(all_unigram.values())
    all_types = len(all_unigram)
    all_ttr = all_types / all_tokens if all_tokens > 0 else 0.0
    all_repeat = sum((c / all_tokens) ** 2 for c in all_unigram.values()) if all_tokens > 0 else 0.0
    all_ent = entropy([c / all_tokens for c in all_unigram.values()]) if all_tokens > 0 else 0.0

    return {
        # Syllabogram-only
        "syllabogram_tokens": total_tokens,
        "syllabogram_types": total_types,
        "syllabogram_ttr": ttr,
        "syllabogram_repeat_rate": repeat_rate,
        "syllabogram_entropy": ent,
        "syllabogram_normalized_entropy": norm_ent,
        "syllabogram_hapax_count": hapax_count,
        "syllabogram_hapax_proportion": hapax_proportion,
        "syllabogram_dis_count": dis_count,
        "syllabogram_mean_seq_length": mean_seq_len,
        "syllabogram_max_seq_length": max_seq_len,
        "syllabogram_min_seq_length": min_seq_len,
        "syllabogram_zipf_slope": zipf_slope,
        "syllabogram_top1_frequency": top1_freq,
        "syllabogram_top1_proportion": top1_proportion,
        "syllabogram_top5_frequency": top5_freq,
        "syllabogram_top5_proportion": top5_proportion,
        # All-signs (including logograms)
        "all_tokens": all_tokens,
        "all_types": all_types,
        "all_ttr": all_ttr,
        "all_repeat_rate": all_repeat,
        "all_entropy": all_ent,
        # Comparison notes
        "comparison_notes": (
            "NOTE: These are sign-level statistics (sign inventory ~130 types), NOT word-level. "
            "Compare with caution. Agglutinative languages (word-level): TTR 0.6-0.8, repeat "
            "rate 0.05-0.15, entropy 4-6. Fusional: TTR 0.4-0.6, repeat rate 0.10-0.25, "
            "entropy 3-5. Isolating: TTR 0.3-0.5, repeat rate 0.15-0.30, entropy 2.5-4. "
            "Linear A sign-level: TTR=%.4f (low because ~5.7K tokens use only 129 signs, "
            "typical for a syllabary of this size). Repeat rate=%.4f is very low, indicating "
            "relatively even sign distribution. Entropy=%.4f is moderately high. "
            "Zipf slope ~%.2f (ideal Zipf = -1.0; positive value indicates the distribution "
            "is flatter than canonical Zipf, suggesting a well-utilised sign inventory)."
        ) % (ttr, repeat_rate, ent, zipf_slope),
    }


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_conditional_entropy(results: list[dict], output_path: str):
    """Write conditional entropy results to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "k", "total_events", "unique_contexts", "entropy", "perplexity",
        ])
        writer.writeheader()
        for r in results:
            row = {
                "k": r["k"],
                "total_events": r["total_events"],
                "unique_contexts": r["unique_contexts"],
                "entropy": f"{r['entropy']:.8f}" if r["entropy"] is not None else "",
                "perplexity": f"{r['perplexity']:.4f}" if r["perplexity"] is not None else "",
            }
            writer.writerow(row)
    logger.info("Wrote conditional entropy to %s", output_path)


def write_sign_entropy(results: list[dict], output_path: str):
    """Write per-sign entropy to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sign", "total_occurrences",
            "initial_count", "medial_count", "final_count",
            "initial_fraction", "medial_fraction", "final_fraction",
            "positional_entropy", "normalized_positional_entropy",
            "relative_bin_entropy", "relative_bin_entropy_normalized",
            "bias",
        ])
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in writer.fieldnames}
            for fld in ("initial_fraction", "medial_fraction", "final_fraction",
                        "positional_entropy", "normalized_positional_entropy",
                        "relative_bin_entropy", "relative_bin_entropy_normalized"):
                if isinstance(row.get(fld), (int, float)):
                    row[fld] = f"{row[fld]:.6f}"
            writer.writerow(row)
    logger.info("Wrote %d sign entropy rows to %s", len(results), output_path)


def write_mutual_information(results: list[dict], output_path: str):
    """Write mutual information data to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sign_a", "sign_b", "count",
            "pmi", "mi_contribution",
            "expected_count", "log_ratio",
        ])
        writer.writeheader()
        for r in results:
            row = {
                "sign_a": r["sign_a"],
                "sign_b": r["sign_b"],
                "count": r["count"],
                "pmi": f"{r['pmi']:.6f}",
                "mi_contribution": f"{r['mi_contribution']:.8f}",
                "expected_count": f"{r['expected_count']:.4f}",
                "log_ratio": f"{r['log_ratio']:.6f}",
            }
            writer.writerow(row)
    logger.info("Wrote %d MI rows to %s", len(results), output_path)


def write_phonotactic_summary(phonotactics: dict, output_path: str):
    """Write phonotactic summary to CSV (multi-section)."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        # Section 1: CV type frequencies
        writer.writerow(["SECTION", "CV_TYPE_FREQUENCIES"])
        writer.writerow(["cv_type", "count", "fraction"])
        for cv_type, info in sorted(phonotactics["cv_type_frequencies"].items()):
            writer.writerow([cv_type, info["count"], f"{info['fraction']:.6f}"])
        writer.writerow([])

        # Section 2: CV bigram transitions
        writer.writerow(["SECTION", "CV_BIGRAM_TRANSITIONS"])
        writer.writerow(["from", "to", "count", "probability"])
        for key, info in sorted(phonotactics["cv_bigram_transitions"].items()):
            writer.writerow([
                info["from"], info["to"],
                info["count"], f"{info['probability']:.6f}",
            ])
        writer.writerow([])

        # Section 3: Syllable patterns (top 100)
        writer.writerow(["SECTION", "SYLLABLE_PATTERNS"])
        writer.writerow(["pattern", "count"])
        for pat, cnt in list(phonotactics["syllable_patterns"].items())[:100]:
            writer.writerow([pat, cnt])
        writer.writerow([])

        # Section 4: Sign-to-CV mapping
        writer.writerow(["SECTION", "SIGN_CV_MAPPING"])
        writer.writerow(["bennett_id", "cv_structure"])
        for bid, cv in sorted(phonotactics["sign_cv_mapping"].items()):
            writer.writerow([bid, cv])

    logger.info("Wrote phonotactic summary to %s", output_path)


def write_misvalued_signs(results: list[dict], output_path: str):
    """Write misvalued signs (bigram disruption) to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "bennett_id", "transliteration", "phonetic_class",
            "total_followers", "total_preceders",
            "follower_entropy", "max_follower_entropy",
            "class_mean_follower_entropy", "entropy_divergence",
            "overlap_vs_class_expectation", "cross_class_affinity",
            "most_similar_other_class", "disruption_score",
            "num_anomalous_followers", "anomalous_followers",
            "expected_top_followers", "actual_top_followers",
        ])
        writer.writeheader()
        for rank, r in enumerate(results, start=1):
            row = {
                "rank": rank,
                "bennett_id": r["bennett_id"],
                "transliteration": r["transliteration"],
                "phonetic_class": r["phonetic_class"],
                "total_followers": r["total_followers"],
                "total_preceders": r["total_preceders"],
                "follower_entropy": f"{r['follower_entropy']:.6f}",
                "max_follower_entropy": f"{r['max_follower_entropy']:.6f}",
                "class_mean_follower_entropy": f"{r['class_mean_follower_entropy']:.6f}",
                "entropy_divergence": f"{r['entropy_divergence']:.6f}",
                "overlap_vs_class_expectation": f"{r['overlap_vs_class_expectation']:.6f}",
                "cross_class_affinity": f"{r['cross_class_affinity']:.6f}",
                "most_similar_other_class": r["most_similar_other_class"],
                "disruption_score": f"{r['disruption_score']:.6f}",
                "num_anomalous_followers": r["num_anomalous_followers"],
                "anomalous_followers": r["anomalous_followers"],
                "expected_top_followers": r["expected_top_followers"],
                "actual_top_followers": r["actual_top_followers"],
            }
            writer.writerow(row)
    logger.info("Wrote %d misvalued-sign entries to %s", len(results), output_path)


def write_typology_statistics(stats: dict, output_path: str):
    """Write typology comparison statistics to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["SECTION", "LANGUAGE_TYPOLOGY_STATISTICS"])
        writer.writerow([])

        # Syllabogram section
        writer.writerow(["METRIC", "SYLLABOGRAMS", "ALL_SIGNS", "NOTES"])
        syllab_keys = [
            ("Total Tokens", "syllabogram_tokens", "all_tokens"),
            ("Total Types", "syllabogram_types", "all_types"),
            ("Type-Token Ratio (TTR)", "syllabogram_ttr", "all_ttr"),
            ("Repeat Rate (Simpson's Index)", "syllabogram_repeat_rate", "all_repeat"),
            ("Shannon Entropy", "syllabogram_entropy", "all_entropy"),
        ]
        for label, s_key, a_key in syllab_keys:
            s_val = stats.get(s_key, "")
            a_val = stats.get(a_key, "")
            if isinstance(s_val, float):
                s_val = f"{s_val:.6f}"
            if isinstance(a_val, float):
                a_val = f"{a_val:.6f}"
            writer.writerow([label, s_val, a_val, ""])

        writer.writerow([])
        writer.writerow(["SYLLABOGRAM-ONLY METRICS", "VALUE", "DESCRIPTION"])
        extra_metrics = [
            ("Normalized Entropy", "syllabogram_normalized_entropy",
             "H / log2(N_types); 1 = uniform, 0 = maximally skewed"),
            ("Hapax Count", "syllabogram_hapax_count",
             "Number of signs appearing exactly once"),
            ("Hapax Proportion", "syllabogram_hapax_proportion",
             "Fraction of types that are hapax legomena"),
            ("Dis Legomena Count", "syllabogram_dis_count",
             "Number of signs appearing exactly twice"),
            ("Mean Sequence Length", "syllabogram_mean_seq_length",
             "Average number of signs per inscription"),
            ("Max Sequence Length", "syllabogram_max_seq_length",
             "Longest inscription (signs)"),
            ("Min Sequence Length", "syllabogram_min_seq_length",
             "Shortest inscription (signs)"),
            ("Zipf Slope (approx)", "syllabogram_zipf_slope",
             "Log-log frequency rank slope; -1.0 is canonical Zipf"),
            ("Top-1 Frequency", "syllabogram_top1_frequency",
             "Count of most frequent sign"),
            ("Top-1 Proportion", "syllabogram_top1_proportion",
             "Fraction of all tokens for most frequent sign"),
            ("Top-5 Proportion", "syllabogram_top5_proportion",
             "Fraction of all tokens for top 5 signs"),
        ]
        for label, key, desc in extra_metrics:
            val = stats.get(key, "")
            if isinstance(val, float):
                val = f"{val:.6f}"
            writer.writerow([label, val, desc])

        writer.writerow([])
        writer.writerow(["COMPARISON NOTES", stats.get("comparison_notes", "")])

    logger.info("Wrote typology statistics to %s", output_path)


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def write_summary_report(ngram_counts_sign: dict[int, Counter],
                         ngram_counts_char: dict[int, Counter],
                         cond_ent_results: list[dict],
                         mi_results: list[dict],
                         typology: dict,
                         output_path: str):
    """Write a human-readable summary as CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["SECTION", "KEY", "VALUE"])

        # Corpus overview
        total_sign_tokens = sum(ngram_counts_sign[1].values())
        total_sign_types = len(ngram_counts_sign[1])
        total_char_tokens = sum(ngram_counts_char[1].values())
        total_char_types = len(ngram_counts_char[1])

        writer.writerow(["CORPUS", "sign_tokens", str(total_sign_tokens)])
        writer.writerow(["CORPUS", "sign_types", str(total_sign_types)])
        writer.writerow(["CORPUS", "char_tokens", str(total_char_tokens)])
        writer.writerow(["CORPUS", "char_types", str(total_char_types)])
        writer.writerow(["CORPUS", "sign_bigrams", str(sum(ngram_counts_sign[2].values()))])

        # N-gram sparsity
        for n in [1, 2, 3, 4, 5]:
            cnt = ngram_counts_sign.get(n, Counter())
            possible = total_sign_types ** n
            actual = len(cnt)
            sparsity = 1.0 - (actual / possible) if possible > 0 else 0.0
            writer.writerow([f"NGRAM_SIGN_n={n}", "possible_ngrams", str(possible)])
            writer.writerow([f"NGRAM_SIGN_n={n}", "observed_ngrams", str(actual)])
            writer.writerow([f"NGRAM_SIGN_n={n}", "sparsity", f"{sparsity:.6f}"])

        # Conditional entropy
        writer.writerow([])
        writer.writerow(["SECTION", "CONDITIONAL_ENTROPY", ""])
        for r in cond_ent_results:
            writer.writerow([
                "COND_ENT",
                f"k={r['k']}",
                json.dumps({
                    "entropy": r.get("entropy"),
                    "perplexity": r.get("perplexity"),
                    "unique_contexts": r.get("unique_contexts"),
                    "total_events": r.get("total_events"),
                }),
            ])

        # Top bigrams by PMI
        writer.writerow([])
        writer.writerow(["SECTION", "TOP_BIGRAMS_BY_PMI", ""])
        for r in mi_results[:30]:
            writer.writerow([
                "MI_PAIR",
                f"{r['sign_a']} -> {r['sign_b']}",
                json.dumps({"pmi": f"{r['pmi']:.3f}", "count": r["count"]}),
            ])

        # Typology
        writer.writerow([])
        writer.writerow(["SECTION", "TYPOLOGY", ""])
        for key, val in sorted(typology.items()):
            if key == "comparison_notes":
                continue
            if isinstance(val, float):
                writer.writerow(["TYPOLOGY", key, f"{val:.6f}"])
            else:
                writer.writerow(["TYPOLOGY", key, str(val)])

        writer.writerow([])
        writer.writerow(["TYPOLOGY_NOTES", typology.get("comparison_notes", ""), ""])

    logger.info("Wrote summary report to %s", output_path)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

class NgramAnalyzer:
    """Orchestrates the full n-gram analysis pipeline."""

    def __init__(self, db_path: str, output_dir: str):
        self.db_path = db_path
        self.output_dir = output_dir

    def run(self):
        """Execute the full analysis pipeline."""
        logger.info("=" * 60)
        logger.info("N-Gram Language Modeling & Phonotactic Analysis")
        logger.info("=" * 60)

        os.makedirs(self.output_dir, exist_ok=True)

        # 1. Load corpus
        logger.info("[1] Loading corpus from database...")
        syllabograms_only, all_signs = load_corpus(self.db_path)
        logger.info("    %d syllabogram sequences, %d all-sign sequences",
                     len(syllabograms_only), len(all_signs))

        # 2. Sign-key functions
        def sign_bennett(s):
            return s["bennett_id"]

        def sign_translit(s):
            t = s.get("transliteration") or ""
            if t:
                return t
            return s.get("character") or s.get("bennett_id") or "?"

        def sign_char(s):
            return s.get("character") or s.get("bennett_id") or "?"

        # 3. Sign-level n-grams
        logger.info("[2] Computing sign-level n-gram frequencies (n=1..5)...")
        ngram_counts_sign = count_ngrams(syllabograms_only, sign_bennett, max_n=5)
        ngram_path = os.path.join(self.output_dir, "ngram_freqs.csv")
        ngram_counts_to_csv(ngram_counts_sign, ngram_path, label="sign_bennett")

        # 4. Character-level (transliteration) n-grams
        logger.info("[3] Computing transliteration-level n-gram frequencies (n=1..5)...")
        ngram_counts_char = count_ngrams(all_signs, sign_translit, max_n=5)
        # Append to the same CSV
        ngram_counts_to_csv(ngram_counts_char, ngram_path, label="transliteration")

        # 5. Conditional entropy
        logger.info("[4] Computing conditional entropy H(sign|context) for k=1..3...")
        cond_ent_results = compute_conditional_entropy(syllabograms_only, sign_bennett, k_values=[1, 2, 3])
        cond_ent_path = os.path.join(self.output_dir, "conditional_entropy.csv")
        write_conditional_entropy(cond_ent_results, cond_ent_path)

        # 6. Positional entropy
        logger.info("[5] Computing per-sign positional entropy...")
        pos_ent_results = compute_positional_entropy(syllabograms_only, sign_bennett)
        sign_ent_path = os.path.join(self.output_dir, "sign_entropy.csv")
        write_sign_entropy(pos_ent_results, sign_ent_path)

        # 7. Mutual information
        logger.info("[6] Computing mutual information between adjacent signs...")
        mi_results = compute_mutual_information(syllabograms_only, sign_bennett, min_occurrences=3)
        mi_path = os.path.join(self.output_dir, "mutual_information.csv")
        write_mutual_information(mi_results, mi_path)

        # 8. Phonotactic analysis
        logger.info("[7] Computing phonotactic structure analysis...")
        phonotactics = analyze_phonotactics(all_signs, syllabograms_only)
        phonotactic_path = os.path.join(self.output_dir, "phonotactic_summary.csv")
        write_phonotactic_summary(phonotactics, phonotactic_path)

        # 9. Bigram disruption scan (misvalued signs)
        logger.info("[8] Running bigram disruption scan for misvalued signs...")
        disruption_results = bigram_disruption_scan(syllabograms_only, sign_bennett)
        misvalued_path = os.path.join(self.output_dir, "misvalued_signs_ngram.csv")
        write_misvalued_signs(disruption_results, misvalued_path)

        # 10. Language typology comparison
        logger.info("[9] Computing language typology comparison statistics...")
        typology = compute_typology_statistics(syllabograms_only, all_signs, sign_bennett)
        typology_path = os.path.join(self.output_dir, "typology_statistics.csv")
        write_typology_statistics(typology, typology_path)

        # 11. Summary report
        logger.info("[10] Writing summary report...")
        summary_path = os.path.join(self.output_dir, "analysis_summary.csv")
        write_summary_report(
            ngram_counts_sign, ngram_counts_char,
            cond_ent_results, mi_results, typology,
            summary_path,
        )

        logger.info("=" * 60)
        logger.info("All outputs written to %s", self.output_dir)
        logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="N-Gram Language Modeling, Phonotactic & Entropy Analysis for Linear A",
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB,
        help=f"Path to SQLite database (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--out", default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()

    analyzer = NgramAnalyzer(db_path=args.db, output_dir=args.out)
    analyzer.run()


if __name__ == "__main__":
    main()
