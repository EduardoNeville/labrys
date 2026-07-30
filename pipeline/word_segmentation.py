#!/usr/bin/env python3
"""
Automated word segmentation system for Linear A texts.

Implements multiple segmentation strategies:
  1. Strategy 1: Use existing word divider marks from the corpus (ground truth)
  2. Strategy 2: Bigram transition probability - split where bigram probability drops
  3. Strategy 3: Positional pattern - split based on positional profiles (prefix/suffix markers)
  4. Strategy 4: Boundary entropy - compute H_left and H_right for each sign position
  5. Strategy 5: Viterbi decoding - hidden Markov model for most likely word segmentation

Cross-validates against ground-truth dividers and produces a consensus segmentation
via voting among all applicable strategies.
"""

import csv
import json
import math
import os
import sqlite3
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "lineara_full.db")
INVENTORY_CSV = os.path.join(BASE_DIR, "data", "corpus", "linear_a_inventory.csv")
OUT_DIR = os.path.join(BASE_DIR, "data", "analysis", "segmentation")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AEGEAN_WORD_SEPARATOR = "\U00010101"  # U+10101 AEGEAN WORD SEPARATOR DOT


def is_word_divider_char(char):
    return char == AEGEAN_WORD_SEPARATOR


def is_numeral_char(char):
    cp = ord(char)
    return 0x10107 <= cp <= 0x1013F


def is_non_linguistic(sign_type, char):
    """Return True if this sign should be excluded from linguistic modeling."""
    if is_word_divider_char(char):
        return True
    if sign_type in ("numeral", "fraction", "metrical"):
        return True
    if is_numeral_char(char):
        return True
    return False


# ---------------------------------------------------------------------------
# 1.  Load data
# ---------------------------------------------------------------------------

def load_inscriptions(db_path):
    """Return list of dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, gorila_id FROM inscriptions ORDER BY id")
    inscriptions = []
    id_map = {}
    for row in c.fetchall():
        d = {"inscription_id": row["id"], "gorila_id": row["gorila_id"],
             "signs": [], "dividers": set()}
        inscriptions.append(d)
        id_map[row["id"]] = d

    c.execute(
        "SELECT inscription_id, sequence, character, bennett_id, "
        "       transliteration, sign_type "
        "FROM signs ORDER BY inscription_id, sequence"
    )
    for row in c.fetchall():
        ins_id = row["inscription_id"]
        char = row["character"] or ""
        trans = (row["transliteration"] or "").strip()
        sign_type = row["sign_type"] or "syllabogram"
        sign = {
            "sequence": row["sequence"],
            "character": char,
            "bennett_id": row["bennett_id"],
            "transliteration": trans,
            "sign_type": sign_type,
            "is_divider": is_word_divider_char(char),
            "is_non_linguistic": is_non_linguistic(sign_type, char),
        }
        ins = id_map.get(ins_id)
        if ins:
            ins["signs"].append(sign)
            if sign["is_divider"]:
                ins["dividers"].add(row["sequence"])

    conn.close()
    inscriptions = [i for i in inscriptions if i["signs"]]
    return inscriptions


def load_inventory(csv_path):
    """Load inventory CSV, return dict gorila_id -> num_signs."""
    result = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gid = (row.get("GORILA_ID") or "").strip()
            ns_str = (row.get("Num_Signs") or "").strip()
            if not gid or not ns_str:
                continue
            if "-" in ns_str:
                try:
                    ns = int(ns_str.split("-")[-1])
                except ValueError:
                    continue
            else:
                try:
                    ns = int(ns_str)
                except ValueError:
                    continue
            result[gid] = ns
    return result


# ---------------------------------------------------------------------------
# Segmentation Result container
# ---------------------------------------------------------------------------

class SegmentationResult:
    def __init__(self, strategy_name, inscription_id, gorila_id,
                 boundaries, confidence=1.0, details=""):
        self.strategy_name = strategy_name
        self.inscription_id = inscription_id
        self.gorila_id = gorila_id
        self.boundaries = sorted(set(boundaries))
        self.confidence = confidence
        self.details = details

    def get_words(self, signs):
        """Return list of word strings for display."""
        if not self.boundaries:
            return ["".join(s["character"] for s in signs)]
        words = []
        chars = [s["character"] for s in signs]
        start = 0
        for b in self.boundaries:
            if b >= start:
                words.append("".join(chars[start:b + 1]))
                start = b + 1
        if start < len(chars):
            words.append("".join(chars[start:]))
        return words


# ---------------------------------------------------------------------------
# Helper: get canonical sign key
# ---------------------------------------------------------------------------

def sign_key(sign):
    if sign["transliteration"] and sign["transliteration"] not in ("", "?"):
        return sign["transliteration"]
    return sign["character"]


# ---------------------------------------------------------------------------
# Strategy 1: Ground-truth word dividers
# ---------------------------------------------------------------------------

def strategy_ground_truth(inscriptions):
    results = []
    for ins in inscriptions:
        dividers = sorted(ins["dividers"])
        conf = 1.0 if dividers else 0.0
        results.append(SegmentationResult(
            "ground_truth", ins["inscription_id"], ins["gorila_id"],
            dividers, confidence=conf,
            details=f"{len(dividers)} divider(s)"
        ))
    return results


# ---------------------------------------------------------------------------
# Strategy 2: Bigram transition probability (improved)
# ---------------------------------------------------------------------------
# We compute the expected probability P(b|a) = count(a->b) / count(a).
# A boundary is likely when P(b|a) is much lower than expected by chance.
# We use a threshold based on the percentile of all bigram probabilities:
# only gaps with probability in the bottom quartile and below a fraction of
# the marginal probability P(b) are marked as boundaries.

def build_lm(inscriptions):
    """Build unigram and bigram counts from all non-divider, non-numeral signs."""
    unigrams = Counter()
    bigrams = Counter()
    for ins in inscriptions:
        keys = []
        for s in ins["signs"]:
            if s["is_divider"] or s["is_non_linguistic"]:
                continue
            keys.append(sign_key(s))
        for i in range(len(keys) - 1):
            unigrams[keys[i]] += 1
            bigrams[(keys[i], keys[i + 1])] += 1
        if keys:
            unigrams[keys[-1]] += 1
    return unigrams, bigrams


def strategy_bigram(inscriptions, percentile_threshold=25):
    """Strategy 2: Score each gap by bigram probability.
       A gap is a boundary candidate if P(next|curr) is in the bottom
       `percentile_threshold` percentile of all bigram probabilities AND
       P(next|curr) < P(next) (marginal probability of the next sign).
    """
    unigrams, bigrams = build_lm(inscriptions)

    # Compute all bigram probabilities and find the threshold
    all_probs = []
    for (a, b), cnt in bigrams.items():
        total = unigrams.get(a, 0)
        if total > 0:
            all_probs.append(cnt / total)
    all_probs.sort()

    # Threshold at the given percentile
    idx = int(len(all_probs) * percentile_threshold / 100)
    threshold = all_probs[idx] if idx < len(all_probs) else 0.01

    # Compute marginal probabilities P(sign)
    total_unigrams = sum(unigrams.values())
    marginal = {k: v / total_unigrams for k, v in unigrams.items()}

    results = []
    for ins in inscriptions:
        signs = ins["signs"]
        keys = [sign_key(s) for s in signs]
        boundaries = set()

        for i in range(len(signs) - 1):
            if signs[i]["is_divider"] or signs[i + 1]["is_divider"]:
                continue
            # Skip if either sign is non-linguistic
            if signs[i]["is_non_linguistic"] or signs[i + 1]["is_non_linguistic"]:
                continue

            key_curr = keys[i]
            key_next = keys[i + 1]

            cnt_curr = unigrams.get(key_curr, 0)
            cnt_bigram = bigrams.get((key_curr, key_next), 0)
            prob = cnt_bigram / cnt_curr if cnt_curr > 0 else 0.0

            # Marginal probability of next sign
            p_next = marginal.get(key_next, 0.0)

            # Boundary if bigram prob is in the lowest percentile AND
            # lower than the marginal prob of the next sign
            # (meaning the transition is unexpectedly rare)
            if cnt_curr >= 5 and prob < threshold and prob < p_next * 0.5:
                boundaries.add(i)

        for d in ins["dividers"]:
            boundaries.add(d)

        results.append(SegmentationResult(
            "bigram_transition", ins["inscription_id"], ins["gorila_id"],
            sorted(boundaries),
            details=f"threshold={threshold:.6f}, p{percentile_threshold}"
        ))
    return results


# ---------------------------------------------------------------------------
# Strategy 3: Positional pattern (prefix/suffix markers)
# ---------------------------------------------------------------------------

def build_positional_profiles(inscriptions):
    """Analyze positional tendencies using ground-truth dividers."""
    start_counts = Counter()
    end_counts = Counter()
    total_counts = Counter()

    for ins in inscriptions:
        dividers = sorted(ins["dividers"])
        if not dividers:
            continue

        signs = ins["signs"]
        word_starts = set()
        word_ends = set()

        prev = -1
        for d in dividers:
            if d > prev + 1:
                word_starts.add(prev + 1)
                word_ends.add(d - 1)
            prev = d
        if prev < len(signs) - 1:
            word_starts.add(prev + 1)
            word_ends.add(len(signs) - 1)

        for idx, s in enumerate(signs):
            if s["is_divider"] or s["is_non_linguistic"]:
                continue
            key = sign_key(s)
            total_counts[key] += 1
            if idx in word_starts:
                start_counts[key] += 1
            if idx in word_ends:
                end_counts[key] += 1

    return start_counts, end_counts, total_counts


def strategy_positional(inscriptions):
    """Strategy 3: Use positional profiles.
       Look for pairs where a common word-final sign is followed by a common
       word-initial sign. Use an adaptive threshold based on data availability.
    """
    start_counts, end_counts, total_counts = build_positional_profiles(inscriptions)

    # Compute ratios and also compute a threshold dynamically
    start_ratio = {}
    end_ratio = {}
    for key, total in total_counts.items():
        if total >= 3:
            start_ratio[key] = start_counts.get(key, 0) / total
            end_ratio[key] = end_counts.get(key, 0) / total

    # Use adaptive thresholds: require that the sign appears as start/end
    # more often than expected by random chance (1 / average word length)
    # and at least 20% of its occurrences
    avg_word_length = 3.0  # rough estimate for Linear A
    chance_level = 1.0 / avg_word_length

    start_threshold = max(chance_level, 0.15)
    end_threshold = max(chance_level, 0.15)

    start_markers = {k for k, v in start_ratio.items()
                     if v >= start_threshold and start_counts.get(k, 0) >= 2}
    end_markers = {k for k, v in end_ratio.items()
                   if v >= end_threshold and end_counts.get(k, 0) >= 2}

    results = []
    for ins in inscriptions:
        signs = ins["signs"]
        keys = [sign_key(s) for s in signs]
        boundaries = set()

        for i in range(len(signs) - 1):
            if signs[i]["is_divider"] or signs[i + 1]["is_divider"]:
                continue
            if signs[i]["is_non_linguistic"] or signs[i + 1]["is_non_linguistic"]:
                continue
            k_curr = keys[i]
            k_next = keys[i + 1]

            if k_curr in end_markers and k_next in start_markers:
                boundaries.add(i)

        for d in ins["dividers"]:
            boundaries.add(d)

        results.append(SegmentationResult(
            "positional_profile", ins["inscription_id"], ins["gorila_id"],
            sorted(boundaries),
            details=f"start={len(start_markers)}, end={len(end_markers)}, "
                    f"thr_start={start_threshold:.3f}, thr_end={end_threshold:.3f}"
        ))
    return results


# ---------------------------------------------------------------------------
# Strategy 4: Boundary entropy
# ---------------------------------------------------------------------------

def build_bigram_entropy(inscriptions):
    """Build forward and backward bigram models for entropy computation."""
    fwd_counts = Counter()
    fwd_bigrams = Counter()
    bwd_counts = Counter()
    bwd_bigrams = Counter()

    for ins in inscriptions:
        keys = []
        for s in ins["signs"]:
            if s["is_divider"] or s["is_non_linguistic"]:
                continue
            keys.append(sign_key(s))

        for i in range(len(keys) - 1):
            fwd_counts[keys[i]] += 1
            fwd_bigrams[(keys[i], keys[i + 1])] += 1
        if keys:
            fwd_counts[keys[-1]] += 1

        for i in range(len(keys) - 1):
            bwd_counts[keys[i + 1]] += 1
            bwd_bigrams[(keys[i + 1], keys[i])] += 1

    return fwd_counts, fwd_bigrams, bwd_counts, bwd_bigrams


def entropy_of_distribution(counts, total):
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def strategy_entropy(inscriptions):
    """Strategy 4: Compute forward and backward boundary entropy.
       A boundary is likely where both H_left and H_right are high,
       meaning there is high uncertainty in what precedes/follows.
       We use a dynamic threshold: the median entropy value.
    """
    fwd_counts, fwd_bigrams, bwd_counts, bwd_bigrams = build_bigram_entropy(inscriptions)

    # Precompute entropies
    entropy_right = {}
    for curr, total in fwd_counts.items():
        continuation_counts = Counter()
        for (p, n), cnt in fwd_bigrams.items():
            if p == curr:
                continuation_counts[n] += cnt
        entropy_right[curr] = entropy_of_distribution(continuation_counts, total)

    entropy_left = {}
    for nxt, total in bwd_counts.items():
        prev_counts = Counter()
        for (n, p), cnt in bwd_bigrams.items():
            if n == nxt:
                prev_counts[p] += cnt
        entropy_left[nxt] = entropy_of_distribution(prev_counts, total)

    # Determine median entropy for thresholding
    all_entropy_values = list(entropy_right.values()) + list(entropy_left.values())
    all_entropy_values.sort()
    if all_entropy_values:
        median_h = all_entropy_values[len(all_entropy_values) // 2]
    else:
        median_h = 1.0

    # Use median as threshold
    h_threshold = max(median_h, 0.5)

    results = []
    for ins in inscriptions:
        signs = ins["signs"]
        keys = [sign_key(s) for s in signs]
        boundaries = set()

        for i in range(len(signs) - 1):
            if signs[i]["is_divider"] or signs[i + 1]["is_divider"]:
                continue
            if signs[i]["is_non_linguistic"] or signs[i + 1]["is_non_linguistic"]:
                continue
            k_curr = keys[i]
            k_next = keys[i + 1]

            hr = entropy_right.get(k_curr, 0.0)
            hl = entropy_left.get(k_next, 0.0)

            # Use min of left/right entropy (both must be high for a good boundary)
            boundary_score = min(hr, hl)

            # Boundary if both sides have high entropy (above median)
            if boundary_score >= h_threshold:
                boundaries.add(i)

        for d in ins["dividers"]:
            boundaries.add(d)

        results.append(SegmentationResult(
            "boundary_entropy", ins["inscription_id"], ins["gorila_id"],
            sorted(boundaries),
            details=f"threshold={h_threshold:.4f}, median={median_h:.4f}"
        ))
    return results


# ---------------------------------------------------------------------------
# Strategy 5: Viterbi decoding (HMM)
# ---------------------------------------------------------------------------

def build_hmm(inscriptions):
    """Build within-word and cross-word bigram counts from ground-truth data."""
    within = Counter()
    cross = Counter()
    within_total = 0
    cross_total = 0

    for ins in inscriptions:
        dividers = sorted(ins["dividers"])
        if not dividers:
            continue

        signs = ins["signs"]
        keys = [sign_key(s) for s in signs]

        intervals = []
        prev = -1
        for d in dividers:
            if d > prev + 1:
                intervals.append((prev + 1, d - 1))
            prev = d
        if prev < len(signs) - 1:
            intervals.append((prev + 1, len(signs) - 1))

        for start, end in intervals:
            for i in range(start, end):
                if signs[i]["is_divider"] or signs[i + 1]["is_divider"]:
                    continue
                if signs[i]["is_non_linguistic"] or signs[i + 1]["is_non_linguistic"]:
                    continue
                within[(keys[i], keys[i + 1])] += 1
                within_total += 1

        for j in range(len(intervals) - 1):
            end_idx = intervals[j][1]
            next_start = intervals[j + 1][0]
            if end_idx < 0 or next_start >= len(signs):
                continue
            if signs[end_idx]["is_divider"] or signs[next_start]["is_divider"]:
                continue
            if signs[end_idx]["is_non_linguistic"] or signs[next_start]["is_non_linguistic"]:
                continue
            cross[(keys[end_idx], keys[next_start])] += 1
            cross_total += 1

    return within, cross, within_total, cross_total


def strategy_viterbi(inscriptions):
    """Strategy 5: Viterbi decoding with HMM.
       States: 0 = within-word, 1 = boundary (new word starts at this position).
    """
    within, cross, within_total, cross_total = build_hmm(inscriptions)

    within_given_prev = defaultdict(Counter)
    for (a, b), cnt in within.items():
        within_given_prev[a][b] += cnt

    cross_given_prev = defaultdict(Counter)
    for (a, b), cnt in cross.items():
        cross_given_prev[a][b] += cnt

    if within_total + cross_total > 0:
        p_within_state = within_total / (within_total + cross_total)
        p_cross_state = cross_total / (within_total + cross_total)
    else:
        p_within_state = 0.9
        p_cross_state = 0.1

    all_keys = set()
    for k in list(within_given_prev.keys()) + list(cross_given_prev.keys()):
        all_keys.add(k)
    for pair in within:
        all_keys.add(pair[0]); all_keys.add(pair[1])
    for pair in cross:
        all_keys.add(pair[0]); all_keys.add(pair[1])
    n_sign_types = len(all_keys) if all_keys else 100
    smooth = 0.01

    results = []
    for ins in inscriptions:
        signs = ins["signs"]
        keys = [sign_key(s) for s in signs]
        n = len(signs)

        if n < 2:
            results.append(SegmentationResult(
                "viterbi_hmm", ins["inscription_id"], ins["gorila_id"],
                sorted(ins["dividers"]), details="too short"
            ))
            continue

        NEG = float('-inf')
        dp = [[NEG, NEG] for _ in range(n)]
        back = [[-1, -1] for _ in range(n)]

        dp[0][1] = math.log(p_within_state)

        for i in range(1, n):
            s_curr = signs[i]
            s_prev = signs[i - 1]

            if s_curr["is_divider"] or s_prev["is_divider"]:
                for prev_state in (0, 1):
                    if dp[i - 1][prev_state] > NEG:
                        score = dp[i - 1][prev_state]
                        if score > dp[i][1]:
                            dp[i][1] = score
                            back[i][1] = prev_state
                continue

            k_curr = keys[i]
            k_prev = keys[i - 1]

            if s_curr["is_non_linguistic"] or s_prev["is_non_linguistic"]:
                for prev_state in (0, 1):
                    if dp[i - 1][prev_state] > NEG:
                        dp[i][prev_state] = max(dp[i][prev_state],
                                                 dp[i - 1][prev_state])
                        back[i][prev_state] = prev_state
                continue

            known_boundary = (i - 1) in ins["dividers"]

            w_dist = within_given_prev.get(k_prev, {})
            w_total = sum(w_dist.values()) + smooth * n_sign_types
            w_prob = (w_dist.get(k_curr, 0) + smooth) / w_total
            log_w = math.log(w_prob)

            c_dist = cross_given_prev.get(k_prev, {})
            c_total = sum(c_dist.values()) + smooth * n_sign_types
            c_prob = (c_dist.get(k_curr, 0) + smooth) / c_total
            log_c = math.log(c_prob)

            if known_boundary:
                for prev_state in (0, 1):
                    if dp[i - 1][prev_state] > NEG:
                        score = dp[i - 1][prev_state]
                        if score > dp[i][1]:
                            dp[i][1] = score
                            back[i][1] = prev_state
            else:
                for prev_state in (0, 1):
                    if dp[i - 1][prev_state] > NEG:
                        score_continue = dp[i - 1][prev_state] + log_w
                        if score_continue > dp[i][0]:
                            dp[i][0] = score_continue
                            back[i][0] = prev_state

                        score_boundary = dp[i - 1][prev_state] + log_c
                        if score_boundary > dp[i][1]:
                            dp[i][1] = score_boundary
                            back[i][1] = prev_state

        best_final = 0 if dp[n - 1][0] > dp[n - 1][1] else 1
        if max(dp[n - 1]) == NEG:
            results.append(SegmentationResult(
                "viterbi_hmm", ins["inscription_id"], ins["gorila_id"],
                sorted(ins["dividers"]), details="viterbi failed"
            ))
            continue

        boundaries = set()
        state = best_final
        for i in range(n - 1, 0, -1):
            if state == 1 and not signs[i]["is_divider"]:
                boundaries.add(i - 1)
            state = back[i][state]

        for d in ins["dividers"]:
            boundaries.add(d)

        results.append(SegmentationResult(
            "viterbi_hmm", ins["inscription_id"], ins["gorila_id"],
            sorted(boundaries),
            details=f"within_pairs={within_total}, cross_pairs={cross_total}"
        ))

    return results


# ---------------------------------------------------------------------------
# Cross-validation (FIXED evaluation)
# ---------------------------------------------------------------------------

def evaluate_segmentation(predicted_boundaries, actual_boundaries, signs):
    """Compare predicted boundaries vs ground truth.
       A boundary at position i means 'split after sign at index i'.
       Valid boundary positions are 0..n-2 (cannot split after last sign).
    """
    pred = set(predicted_boundaries)
    actual = set(actual_boundaries)

    # Valid positions: 0 to n-2 (all positions except the last sign)
    # A boundary at position i means split between i and i+1
    n = len(signs)
    valid = set(range(n - 1))

    pred_valid = pred & valid
    actual_valid = actual & valid

    tp = len(pred_valid & actual_valid)
    fp = len(pred_valid - actual_valid)
    fn = len(actual_valid - pred_valid)

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    return {"precision": prec, "recall": rec, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn,
            "num_gt": len(actual_valid), "num_pred": len(pred_valid)}


def cross_validate(inscriptions, all_results):
    """Cross-validate all strategies against ground truth."""
    strat_results = defaultdict(list)
    for r in all_results:
        strat_results[r.strategy_name].append(r)

    metrics = {}
    for name, results in strat_results.items():
        if name == "ground_truth":
            continue
        precs, recalls, f1s = [], [], []
        num_with_gt = 0
        for r in results:
            ins = next((i for i in inscriptions
                        if i["inscription_id"] == r.inscription_id), None)
            if ins and ins["dividers"]:
                num_with_gt += 1
                ev = evaluate_segmentation(r.boundaries, ins["dividers"],
                                           ins["signs"])
                precs.append(ev["precision"])
                recalls.append(ev["recall"])
                f1s.append(ev["f1"])

        metrics[name] = {
            "avg_precision": sum(precs) / len(precs) if precs else 0.0,
            "avg_recall": sum(recalls) / len(recalls) if recalls else 0.0,
            "avg_f1": sum(f1s) / len(f1s) if f1s else 0.0,
            "num_inscriptions_with_gt": num_with_gt,
        }
    return metrics


# ---------------------------------------------------------------------------
# Consensus
# ---------------------------------------------------------------------------

def compute_consensus(inscriptions, all_results):
    """Majority voting among non-ground-truth strategies."""
    ins_results = defaultdict(list)
    for r in all_results:
        ins_results[r.inscription_id].append(r)

    consensus = []
    for ins in inscriptions:
        iid = ins["inscription_id"]
        if iid not in ins_results:
            continue

        strat_boundaries = [set(r.boundaries) for r in ins_results[iid]
                            if r.strategy_name != "ground_truth"]
        if not strat_boundaries:
            gt = [r for r in ins_results[iid] if r.strategy_name == "ground_truth"]
            if gt:
                consensus.append(SegmentationResult(
                    "consensus", iid, ins["gorila_id"],
                    list(gt[0].boundaries), confidence=1.0,
                    details="only ground truth available"
                ))
            else:
                consensus.append(SegmentationResult(
                    "consensus", iid, ins["gorila_id"],
                    [], confidence=0.0,
                    details="no strategies available"
                ))
            continue

        n_strat = len(strat_boundaries)
        votes = Counter()
        for bset in strat_boundaries:
            for b in bset:
                votes[b] += 1

        accepted = sorted([b for b, v in votes.items() if v > n_strat / 2.0])

        if accepted:
            avg_conf = sum(votes[b] / n_strat for b in accepted) / len(accepted)
        else:
            avg_conf = 0.0

        consensus.append(SegmentationResult(
            "consensus", iid, ins["gorila_id"],
            accepted, confidence=avg_conf,
            details=f"{n_strat} strategies, {len(accepted)} accepted"
        ))

    return consensus


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_segmented_texts(inscriptions, consensus_results, out_path):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["gorila_id", "inscription_id", "num_signs",
                         "num_words", "segmented_text",
                         "ground_truth_boundaries",
                         "predicted_boundaries", "confidence"])
        for cr in sorted(consensus_results, key=lambda x: x.gorila_id):
            ins = next((i for i in inscriptions
                        if i["inscription_id"] == cr.inscription_id), None)
            if not ins:
                continue
            words = cr.get_words(ins["signs"])
            segmented = " | ".join(words)
            writer.writerow([
                cr.gorila_id, cr.inscription_id, len(ins["signs"]),
                len(words), segmented,
                json.dumps(sorted(ins["dividers"])),
                json.dumps(cr.boundaries),
                f"{cr.confidence:.4f}",
            ])


def write_confidence(inscriptions, all_results, consensus_results, out_path):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["gorila_id", "inscription_id", "num_signs",
                         "strategy", "num_boundaries", "confidence",
                         "has_ground_truth", "details"])

        all_items = all_results + consensus_results
        for r in sorted(all_items, key=lambda x: (x.gorila_id, x.strategy_name)):
            ins = next((i for i in inscriptions
                        if i["inscription_id"] == r.inscription_id), None)
            has_gt = len(ins["dividers"]) > 0 if ins else False
            writer.writerow([
                r.gorila_id,
                r.inscription_id,
                len(ins["signs"]) if ins else 0,
                r.strategy_name, len(r.boundaries),
                f"{r.confidence:.4f}",
                has_gt,
                r.details,
            ])


def write_strategy_comparison(metrics, out_path):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["strategy", "num_inscriptions_with_gt",
                         "avg_precision", "avg_recall", "avg_f1",
                         "notes"])
        for name, m in sorted(metrics.items()):
            note = ""
            if m["avg_f1"] == 0 and m["num_inscriptions_with_gt"] > 0:
                note = "no overlap with ground truth boundaries"
            writer.writerow([
                name, m["num_inscriptions_with_gt"],
                f"{m['avg_precision']:.4f}",
                f"{m['avg_recall']:.4f}",
                f"{m['avg_f1']:.4f}",
                note,
            ])


def write_longest_40(inscriptions, consensus_results, inventory, out_path):
    scored = [(len(i["signs"]), i["inscription_id"], i["gorila_id"])
              for i in inscriptions]
    scored.sort(key=lambda x: -x[0])
    top40 = [s for s in scored if s[0] >= 20][:40]

    cons_map = {cr.inscription_id: cr for cr in consensus_results}

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("LINEAR A - 40 LONGEST TEXTS (>=20 SIGNS) - SEGMENTED\n")
        f.write(f"Total texts in corpus: {len(inscriptions)}\n")
        f.write(f"Showing top {len(top40)} by sign count\n")
        f.write("=" * 80 + "\n\n")

        for rank, (cnt, iid, gid) in enumerate(top40, 1):
            ins = next((i for i in inscriptions
                        if i["inscription_id"] == iid), None)
            if not ins:
                continue

            cr = cons_map.get(iid)
            f.write("-" * 70 + "\n")
            f.write(f"#{rank:2d}  {gid:15s}  {cnt} signs")

            if cr:
                words = cr.get_words(ins["signs"])
                f.write(f"  ->  {len(words)} words  "
                        f"(confidence: {cr.confidence:.3f})\n")
            else:
                f.write("  (no consensus)\n")

            raw = "".join(s["character"] for s in ins["signs"])
            f.write(f"\n  Raw: {raw}\n")

            dividers = sorted(ins["dividers"])
            if dividers:
                marks = [" "] * len(ins["signs"])
                for d in dividers:
                    if d < len(marks):
                        marks[d] = "\u2193"
                f.write("  Gnd: " + "".join(marks) +
                        "  (ground-truth divider)\n")

            if cr:
                seg = " | ".join(words)
                f.write(f"  Seg: {seg}\n")

                bmarks = [" "] * len(ins["signs"])
                for b in cr.boundaries:
                    if b < len(bmarks):
                        bmarks[b] = "|"
                f.write("  Bnd: " + "".join(bmarks) + "\n")
                f.write(f"  Boundaries: {cr.boundaries}\n")
            else:
                f.write("  (no consensus segmentation)\n")
            f.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("LINEAR A WORD SEGMENTATION SYSTEM")
    print("=" * 70)

    print("\n[1] Loading inscriptions from database...")
    inscriptions = load_inscriptions(DB_PATH)
    print(f"    Loaded {len(inscriptions)} inscriptions with signs.")

    inventory = load_inventory(INVENTORY_CSV)
    print(f"    Loaded {len(inventory)} entries from inventory CSV.")

    num_with = sum(1 for i in inscriptions if i["dividers"])
    num_div = sum(len(i["dividers"]) for i in inscriptions)
    print(f"    Inscriptions with word dividers: {num_with}")
    print(f"    Total word-divider signs: {num_div}")

    print("\n[2] Running segmentation strategies...")

    print("    Strategy 1: Ground-truth word dividers...")
    r1 = strategy_ground_truth(inscriptions)

    print("    Strategy 2: Bigram transition probability...")
    r2 = strategy_bigram(inscriptions, percentile_threshold=25)

    print("    Strategy 3: Positional profiles...")
    r3 = strategy_positional(inscriptions)

    print("    Strategy 4: Boundary entropy...")
    r4 = strategy_entropy(inscriptions)

    print("    Strategy 5: Viterbi decoding (HMM)...")
    r5 = strategy_viterbi(inscriptions)

    all_results = r1 + r2 + r3 + r4 + r5

    for name, res_list in [("ground_truth", r1), ("bigram", r2),
                           ("positional", r3), ("entropy", r4),
                           ("viterbi", r5)]:
        total_b = sum(len(r.boundaries) for r in res_list)
        ins_w_b = sum(1 for r in res_list if r.boundaries)
        print(f"       {name:25s}: {ins_w_b:4d} inscriptions, "
              f"{total_b:5d} total boundaries")

    print("\n[3] Computing consensus segmentation...")
    consensus = compute_consensus(inscriptions, all_results)
    ins_w_cons = sum(1 for r in consensus if r.boundaries)
    print(f"       {ins_w_cons} inscriptions with consensus boundaries")

    print("\n[4] Cross-validating against ground truth...")
    metrics = cross_validate(inscriptions, all_results)
    for name, m in metrics.items():
        print(f"    {name:25s}  F1={m['avg_f1']:.4f}  "
              f"P={m['avg_precision']:.4f}  R={m['avg_recall']:.4f}  "
              f"(n={m['num_inscriptions_with_gt']})")

    print("\n[5] Writing output files...")
    os.makedirs(OUT_DIR, exist_ok=True)

    paths = [
        ("segmented_texts_consensus.csv",
         lambda p: write_segmented_texts(inscriptions, consensus, p)),
        ("segmentation_confidence.csv",
         lambda p: write_confidence(inscriptions, all_results, consensus, p)),
        ("strategy_comparison.csv",
         lambda p: write_strategy_comparison(metrics, p)),
        ("longest_40_segmented.txt",
         lambda p: write_longest_40(inscriptions, consensus, inventory, p)),
    ]
    for fname, writer_fn in paths:
        out_path = os.path.join(OUT_DIR, fname)
        writer_fn(out_path)
        print(f"    ... {out_path}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
