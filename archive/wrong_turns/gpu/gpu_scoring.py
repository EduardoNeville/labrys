"""ARCHIVED — WRONG TURN. Do not run, import, or extend.

Batches a scorer with no measured signal (oracle 0.00×, 0/160; weight sweep
0/1,771). Speed was never the limit; evidence was. See ../../README.md and
../../../CODE_AUDIT.md.

Original docstring follows.

GPU-accelerated batched grammatical scoring for the Ventris endgame.

Scores thousands of grid completions simultaneously using tensor operations
on GPU. Operations:
  1. Sign indices → phonetic values (embedding lookup)
  2. Read corpus as tensor once, cache bigram/position counts
  3. Morphology: word-final sign entropy (batched histogram)
  4. Entropy: bigram entropy change (batched counting)
  5. Prefix: prefix concentration (batched argmax)
"""

from __future__ import annotations

import csv
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

__all__ = ["GPUCorpusCache", "batch_score_completions"]


# ═══════════════════════════════════════════════════════════════════════════════
# phoneme encoding
# ═══════════════════════════════════════════════════════════════════════════════

# All unique phonetic values we might encounter
_ALL_VALUES = []
for v in "aeiou":
    _ALL_VALUES.append(v)
for c in "ptkmnslrzwjdhqg":
    for v in "aeiou":
        _ALL_VALUES.append(f"{c}{v}")
_VALUE_TO_IDX = {v: i for i, v in enumerate(_ALL_VALUES)}
_NUM_PHONEMES = len(_ALL_VALUES)

# Consonant series (8) and vowel columns (5)
CONS_SERIES = ["VOWEL", "LABIAL", "DENTAL", "VELAR", "SIBILANT", "LIQUID", "PALATAL", "SEMIVOWEL"]
VOWEL_COLS = ["a", "e", "i", "o", "u"]

def phoneme_to_idx(val: str) -> int:
    """Convert phonetic value to index for embedding lookup."""
    return _VALUE_TO_IDX.get(val.lower(), 0)


def phoneme_idx_to_series(idx: int) -> int:
    """Phoneme index → consonant series index (0..7)."""
    val = _ALL_VALUES[idx]
    if len(val) == 1:
        return 0  # VOWEL
    c = val[0]
    if c in "pm":
        return 1  # LABIAL
    if c in "tdn":
        return 2  # DENTAL
    if c in "kq":
        return 3  # VELAR
    if c in "sz":
        return 4  # SIBILANT
    if c in "rl":
        return 5  # LIQUID
    if c == "j":
        return 6  # PALATAL
    return 7  # SEMIVOWEL


def phoneme_idx_to_vowel(idx: int) -> int:
    """Phoneme index → vowel column index (0..4)."""
    val = _ALL_VALUES[idx]
    v = val[-1] if len(val) > 1 else val
    return VOWEL_COLS.index(v) if v in VOWEL_COLS else 0


# ═══════════════════════════════════════════════════════════════════════════════
# GPU corpus cache
# ═══════════════════════════════════════════════════════════════════════════════

class GPUCorpusCache:
    """Pre-load and cache the corpus as GPU tensors for fast scoring.

    Stores:
        - sequences: (N, L) tensor of sign indices
        - attention_mask: (N, L) boolean tensor
        - word_final_mask: (N, L) boolean tensor marking final sign of each word
        - prefix_mask: (N, L) boolean marking position-0 signs
    """

    def __init__(
        self,
        db_path: str = "data/database/lineara_full.db",
        expanded_grid_path: str = "data/analysis/bootstrapping/expanded_grid.csv",
        max_len: int = 64,
        device: str = "cuda",
    ) -> None:
        self.device = device
        self.max_len = max_len

        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Build sign → index mapping
        c.execute("SELECT DISTINCT bennett_id FROM signs WHERE bennett_id != '' ORDER BY bennett_id")
        self.sign_to_idx: Dict[str, int] = {}
        self.idx_to_sign: Dict[int, str] = {}
        for i, row in enumerate(c.fetchall(), start=1):  # 0 = PAD
            bid = row["bennett_id"]
            self.sign_to_idx[bid] = i
            self.idx_to_sign[i] = bid
        self.vocab_size = len(self.sign_to_idx) + 1
        self.PAD_IDX = 0

        # Load inscriptions, pad to max_len
        c.execute("""
            SELECT i.id, s.sequence, s.bennett_id
            FROM signs s JOIN inscriptions i ON s.inscription_id = i.id
            WHERE s.bennett_id != ''
            ORDER BY i.id, s.sequence
        """)
        inscriptions: Dict[int, List[str]] = defaultdict(list)
        for row in c.fetchall():
            inscriptions[row["id"]].append(row["bennett_id"])

        # Filter to inscriptions with >=3 signs (meaningful for scoring)
        valid = {k: v for k, v in inscriptions.items() if len(v) >= 3}
        sorted_ins = sorted(valid.items(), key=lambda x: len(x[1]), reverse=True)

        N = len(sorted_ins)
        L = max_len
        sequences = torch.full((N, L), self.PAD_IDX, dtype=torch.long)
        attention = torch.zeros(N, L, dtype=torch.bool)
        word_final = torch.zeros(N, L, dtype=torch.bool)
        prefix_mask = torch.zeros(N, L, dtype=torch.bool)

        for i, (ins_id, signs) in enumerate(sorted_ins):
            seq_len = min(len(signs), L)
            for j, bid in enumerate(signs[:seq_len]):
                sequences[i, j] = self.sign_to_idx.get(bid, 0)
            attention[i, :seq_len] = True
            word_final[i, seq_len - 1] = True
            prefix_mask[i, 0] = True

        self.sequences = sequences.to(device)
        self.attention = attention.to(device)
        self.word_final = word_final.to(device)
        self.prefix_mask = prefix_mask.to(device)

        # Precompute bigram pairs for entropy scoring
        # (sign_i, sign_i+1) pairs
        self.bigram_pairs: List[Tuple[torch.Tensor, torch.Tensor]] = []
        for i in range(N):
            row = sequences[i]
            att = attention[i]
            idx = att.nonzero(as_tuple=False).squeeze(-1)
            if len(idx) >= 2:
                s1 = row[idx[:-1]]
                s2 = row[idx[1:]]
                self.bigram_pairs.append((s1, s2))

        # Build mapping: sign index → conventional phonetic value index
        grid = {}
        with open(expanded_grid_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                grid[row["bennett_id"]] = row

        self.sign_to_phoneme = torch.full((self.vocab_size,), -1, dtype=torch.long)
        for bid, idx in self.sign_to_idx.items():
            g = grid.get(bid, {})
            val = g.get("refined_value", g.get("conventional_value", "?"))
            if val and val != "?":
                self.sign_to_phoneme[idx] = phoneme_to_idx(val)

        self.sign_to_phoneme = self.sign_to_phoneme.to(device)

        logger.info("GPU corpus cache: %d inscriptions, %d bigram pairs, vocab=%d",
                     N, len(self.bigram_pairs), self.vocab_size)

    def get_baseline_bigram_entropy(self) -> float:
        """Compute bigram entropy using conventional values as baseline."""
        bg_counts: Dict[int, int] = {}
        total = 0
        for s1, s2 in self.bigram_pairs:
            s1p = self.sign_to_phoneme[s1]  # tensor of phoneme indices
            s2p = self.sign_to_phoneme[s2]
            valid = (s1p >= 0) & (s2p >= 0)
            s1p = s1p[valid]
            s2p = s2p[valid]
            for j in range(len(s1p)):
                k1 = int(s1p[j].item())
                k2 = int(s2p[j].item())
                key = k1 * _NUM_PHONEMES + k2
                bg_counts[key] = bg_counts.get(key, 0) + 1
                total += 1
        if total == 0:
            return 0.0
        ent = 0.0
        for cnt in bg_counts.values():
            p = cnt / total
            ent -= p * math.log2(p)
        return ent


# ═══════════════════════════════════════════════════════════════════════════════
# batched scoring
# ═══════════════════════════════════════════════════════════════════════════════

def batch_score_completions(
    cache: GPUCorpusCache,
    sign_to_candidate: Dict[str, torch.Tensor],  # sign → (K,) tensor of candidate phoneme indices
    target_signs: List[str],  # signs being resolved
    completion_indices: torch.Tensor,  # (B, S) — batch_size × num_target_signs, candidate indices
    baseline_entropy: float,
    device: str = "cuda",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Score B grid completions simultaneously on GPU.

    Parameters
    ----------
    cache : GPUCorpusCache
        Pre-loaded corpus tensors
    sign_to_candidate : dict
        sign → (K,) tensor of candidate phoneme indices for each target sign
    target_signs : list[str]
        Ordered list of signs being resolved (corresponds to columns of completion_indices)
    completion_indices : (B, S)
        For each batch item and each target sign, which candidate index was chosen
    baseline_entropy : float
        Baseline bigram entropy for reference
    device : str

    Returns
    -------
    morphology_scores : (B,) — word-final sign entropy reduction
    entropy_scores : (B,) — bigram entropy reduction
    prefix_scores : (B,) — prefix concentration
    """
    B, S = completion_indices.shape

    # Build full phoneme mapping for each batch item
    # Start with baseline mapping, then override target signs
    baseline_phonemes = cache.sign_to_phoneme.clone()  # (V,)
    baseline_phonemes_known = baseline_phonemes >= 0

    # For each target sign, gather the chosen phoneme index
    target_sign_idxs = torch.tensor(
        [cache.sign_to_idx.get(s, 0) for s in target_signs],
        device=device,
    )

    # Gather candidate phoneme indices: (S, K)
    max_cands = max(len(sign_to_candidate[s]) for s in target_signs)
    cand_phonemes = torch.full((S, max_cands), -1, dtype=torch.long, device=device)
    for i, s in enumerate(target_signs):
        cands = sign_to_candidate[s]
        cand_phonemes[i, :len(cands)] = cands.to(device)

    # completion_indices picks which candidate per sign per batch
    # cand_phonemes: (S, max_cands), completion_indices: (B, S)
    # For each (b, s), chosen_phonemes[b, s] = cand_phonemes[s, completion_indices[b, s]]
    # Index: expand arange(S) to (B, S), pair with completion_indices
    s_idx = torch.arange(S, device=device).unsqueeze(0).expand(B, -1)  # (B, S)
    chosen_phonemes = cand_phonemes[s_idx, completion_indices]  # (B, S)

    # Build full phoneme mapping per batch: (B, V)
    full_phonemes = baseline_phonemes.unsqueeze(0).expand(B, -1).clone()
    full_phonemes[:, target_sign_idxs] = chosen_phonemes

    # ── Morphology score ──
    # Compute word-final phoneme entropy per batch item
    # Get the sequences, convert to phoneme indices
    seq = cache.sequences  # (N, L) sign indices
    N = seq.shape[0]
    L = seq.shape[1]
    word_final = cache.word_final  # (N, L)
    attn = cache.attention  # (N, L)

    # For each batch, build (N, L) phoneme tensor
    morphology_scores = torch.zeros(B, device=device)
    entropy_scores = torch.zeros(B, device=device)
    prefix_scores = torch.zeros(B, device=device)

    # Process in chunks to avoid OOM
    chunk_size = min(B, 32)
    for b_start in range(0, B, chunk_size):
        b_end = min(b_start + chunk_size, B)
        b_slice = slice(b_start, b_end)
        b_actual = b_end - b_start

        batch_phonemes = full_phonemes[b_slice]  # (b_actual, V)

        # Map sequences to phonemes for this batch: (b_actual, N, L)
        # Use index_select: batch_phonemes[:, seq] but seq is (N,L) of sign indices
        seq_expanded = seq.unsqueeze(0).expand(b_actual, -1, -1)  # (b_actual, N, L)
        batch_seq_phonemes = torch.gather(
            batch_phonemes, 1, seq_expanded.reshape(b_actual, -1)
        ).reshape(b_actual, N, L)  # (b_actual, N, L)

        # Morphology: word-final positions
        wf = word_final.unsqueeze(0) & attn.unsqueeze(0) & (batch_seq_phonemes >= 0)
        final_phonemes = batch_seq_phonemes[wf]  # total_final_phonemes

        # Compute per-batch entropy of final phonemes
        for i in range(b_actual):
            batch_i_phonemes = batch_seq_phonemes[i]
            final_i = batch_i_phonemes[word_final & attn & (batch_i_phonemes >= 0)]
            if len(final_i) >= 10:
                counts = torch.bincount(final_i, minlength=_NUM_PHONEMES).float()
                probs = counts / counts.sum()
                nonzero = probs > 0
                ent = -(probs[nonzero] * probs[nonzero].log2()).sum()
                morphology_scores[b_start + i] = max(0.0, float(1.0 - (ent / 5.3)))
            else:
                morphology_scores[b_start + i] = 0.5

        # Entropy: bigram entropy change
        # Sample a few bigram pairs per batch item
        sample_pairs = cache.bigram_pairs[:50]  # Use first 50 for speed
        for i in range(b_actual):
            total_bg = 0
            bg_counts: dict = {}
            for s1, s2 in sample_pairs:
                s1p = batch_phonemes[i, s1]
                s2p = batch_phonemes[i, s2]
                valid = (s1p >= 0) & (s2p >= 0)
                s1p = s1p[valid]
                s2p = s2p[valid]
                for j in range(len(s1p)):
                    key = int(s1p[j].item()) * _NUM_PHONEMES + int(s2p[j].item())
                    bg_counts[key] = bg_counts.get(key, 0) + 1
                    total_bg += 1
            if total_bg > 0 and baseline_entropy > 0:
                ent = 0.0
                for cnt in bg_counts.values():
                    p = cnt / total_bg
                    ent -= p * math.log2(p)
                entropy_scores[b_start + i] = max(0.0, float(1.0 - (ent / baseline_entropy)))
            else:
                entropy_scores[b_start + i] = 0.5

        # Prefix: prefix position concentration
        prefix = cache.prefix_mask  # (N, L)
        for i in range(b_actual):
            batch_i = batch_seq_phonemes[i]
            pre = batch_i[prefix & attn & (batch_i >= 0)]
            if len(pre) >= 3:
                counts = torch.bincount(pre, minlength=_NUM_PHONEMES).float()
                top3_sum = float(counts.topk(3).values.sum())
                total = float(counts.sum())
                prefix_scores[b_start + i] = top3_sum / max(total, 1.0)
            else:
                prefix_scores[b_start + i] = 0.3

    return morphology_scores, entropy_scores, prefix_scores
