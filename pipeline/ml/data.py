"""PyTorch Dataset classes for the Linear A corpus.

Loads sign sequences from the SQLite database and provides them as
tensors for ML training. Three dataset variants target different
training objectives:

- LinearASignDataset — raw sequences for language modelling
- ContrastiveSignDataset — anchor/context/cognate triplets for
  contrastive learning across the Linear A / Linear B overlap
- MaskedLMDataset — BERT-style masked token prediction
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)

# ── helpers ──────────────────────────────────────────────────────────────────

# Bennett AB syllabograms that are genuine phonetic signs (AB 01–AB 137).
# Variant / composite signs like AB 21f, AB 22f, AB 44b are excluded here
# because they are rarer and often lack LB cognates.
SYLLABOGRAM_RANGE = tuple(f"AB {i:02d}" for i in range(1, 138))

PAD_IDX = 0
MASK_IDX = -1  # placeholder; replaced by vocab_size in MaskedLMDataset
NO_COGNATE = -1


def _build_vocab(
    db_path: str,
    bennett_ids: Optional[List[str]] = None,
) -> Tuple[Dict[str, int], Dict[int, str]]:
    """Build sign→index and index→sign mappings from the database.

    PAD is always index 0.  Other signs are assigned indices 1..N in
    sorted order of the *bennett_id* strings that appear in the corpus.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if bennett_ids is not None:
        placeholders = ",".join("?" for _ in bennett_ids)
        c.execute(
            f"SELECT DISTINCT bennett_id FROM signs "
            f"WHERE bennett_id IN ({placeholders}) AND bennett_id != '' "
            f"ORDER BY bennett_id",
            bennett_ids,
        )
    else:
        c.execute(
            "SELECT DISTINCT bennett_id FROM signs "
            "WHERE bennett_id != '' "
            "ORDER BY bennett_id"
        )

    stoi: Dict[str, int] = {"<PAD>": PAD_IDX}
    itos: Dict[int, str] = {PAD_IDX: "<PAD>"}

    for idx, row in enumerate(c.fetchall(), start=1):
        bid = row["bennett_id"]
        stoi[bid] = idx
        itos[idx] = bid

    conn.close()
    return stoi, itos


def _load_sequences(
    db_path: str,
    stoi: Dict[str, int],
    period: Optional[str] = None,
    site: Optional[str] = None,
) -> List[Tuple[List[int], str]]:
    """Return [(sign_id_list, gorila_id), …] for every inscription.

    Only signs whose *bennett_id* is in *stoi* are kept (others are
    silently dropped).  Empty sequences are excluded.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = """
        SELECT i.id, i.gorila_id, s.sequence, s.bennett_id
        FROM inscriptions i
        JOIN signs s ON s.inscription_id = i.id
        WHERE s.bennett_id != ''
    """
    params: list = []

    if period is not None:
        query += " AND i.minoan_period = ?"
        params.append(period)

    if site is not None:
        query += " AND (i.gorila_id LIKE ? OR f.site LIKE ?)"
        # Gorila IDs are usually site-prefixed, e.g. "HT" = Hagia Triada.
        # We also check the findspots table but that requires a richer join.
        # For the simple case we use the gorila_id prefix.
        params.extend([f"{site}%", f"%{site}%"])

    query += " ORDER BY i.id, s.sequence"

    c.execute(query, params)
    rows = c.fetchall()

    # Group by inscription and convert to sign-id lists
    sequences: Dict[int, Tuple[List[int], str]] = {}
    for row in rows:
        ins_id = row["id"]
        bid = row["bennett_id"]
        if bid not in stoi:
            continue
        if ins_id not in sequences:
            sequences[ins_id] = ([], row["gorila_id"])
        sequences[ins_id][0].append(stoi[bid])

    conn.close()

    # Drop empty sequences and return
    return [(seq, gid) for seq, gid in sequences.values() if seq]


def _load_lb_cognate_map(csv_path: str) -> Dict[str, int]:
    """Parse la_lb_mapping.csv → {la_bennett_id: has_lb_cognate (1/0)}.

    A sign is considered to have a Linear B cognate if its *visual_sim*
    is ≥ 0.9 and the *lb_value* is not empty / '?'.  Returns 1 for
    cognates, 0 otherwise.
    """
    cog: Dict[str, int] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            if not bid:
                continue
            try:
                vsim = float(row.get("visual_sim", 0))
            except (ValueError, TypeError):
                vsim = 0.0
            lb_val = (row.get("lb_value") or "").strip()
            # Treat as cognate if visual similarity is high AND we have a
            # concrete LB phonetic reading (not '?', not empty).
            has_cog = int(vsim >= 0.9 and lb_val and lb_val != "?")
            cog[bid] = has_cog
    return cog


# ── dataset classes ──────────────────────────────────────────────────────────

class LinearASignDataset(Dataset):
    """Load Linear A inscriptions as (padded_sequence, gorila_id) pairs.

    Parameters
    ----------
    db_path : str
        Path to ``lineara_full.db``.
    max_length : int
        Pad / truncate every sequence to this length (default 64).
    period : str or None
        Filter inscriptions by *minoan_period* (e.g. ``"LM IB"``).
    site : str or None
        Filter by site prefix in *gorila_id* (e.g. ``"HT"`` for Hagia
        Triada, ``"KN"`` for Knossos).
    bennett_ids : list[str] or None
        Restrict vocabulary to these Bennett IDs.  When ``None`` all
        signs from the database are used.  Pass ``pipeline.ml.data.
        SYLLABOGRAM_RANGE`` for syllabograms only.
    """

    def __init__(
        self,
        db_path: str,
        max_length: int = 64,
        period: Optional[str] = None,
        site: Optional[str] = None,
        bennett_ids: Optional[List[str]] = None,
    ) -> None:
        self.max_length = max_length
        self.stoi, self.itos = _build_vocab(db_path, bennett_ids)
        self.sequences = _load_sequences(db_path, self.stoi, period, site)
        logger.info(
            "LinearASignDataset: %d inscriptions, vocab=%d, max_len=%d",
            len(self.sequences),
            len(self.stoi),
            max_length,
        )

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Tuple[torch.LongTensor, str]:
        seq, gid = self.sequences[idx]
        tensor = torch.full((self.max_length,), PAD_IDX, dtype=torch.long)
        keep = seq[: self.max_length]
        tensor[: len(keep)] = torch.tensor(keep, dtype=torch.long)
        return tensor, gid


class ContrastiveSignDataset(Dataset):
    """Produce (anchor, context_window, lb_cognate) triplets.

    For every sign in every (filtered) inscription a triplet is created:

    * **anchor** — the Bennett ID index of the current sign.
    * **context_window** — tensor of sign IDs in a window of
      ``± window_size`` around the anchor (padded at boundaries).
    * **lb_cognate** — 1 if the anchor sign has a secure Linear B
      cognate (visual similarity ≥ 0.9 + non‑empty LB reading), else 0.
      ``-1`` (NO_COGNATE) is used for signs outside the syllabogram
      range.

    Parameters
    ----------
    db_path : str
        Path to ``lineara_full.db``.
    la_lb_mapping_path : str
        Path to ``la_lb_mapping.csv``.
    max_length : int
        Upper bound for the context-window span.  The window itself has
        ``2 * window_size + 1`` elements.
    period : str or None
        Filter by *minoan_period*.
    site : str or None
        Filter by site prefix.
    bennett_ids : list[str] or None
        Restrict vocabulary.
    window_size : int
        Number of signs to include on each side of the anchor (default 5).
    """

    def __init__(
        self,
        db_path: str,
        la_lb_mapping_path: str,
        max_length: int = 64,
        period: Optional[str] = None,
        site: Optional[str] = None,
        bennett_ids: Optional[List[str]] = None,
        window_size: int = 5,
    ) -> None:
        self.max_length = max_length
        self.window_size = window_size
        self.stoi, self.itos = _build_vocab(db_path, bennett_ids)
        self.sequences = _load_sequences(db_path, self.stoi, period, site)
        self.lb_cognate = _load_lb_cognate_map(la_lb_mapping_path)

        # Pre-compute flat list of (seq_idx, pos) for O(1) indexing
        self._positions: List[Tuple[int, int]] = []
        for seq_idx, (seq, _) in enumerate(self.sequences):
            for pos in range(len(seq)):
                self._positions.append((seq_idx, pos))

        n_cog = sum(
            1
            for si, p in self._positions
            if self._cognate_for_seq_pos(si, p) > 0
        )
        logger.info(
            "ContrastiveSignDataset: %d triplets, %d with LB cognate, vocab=%d",
            len(self._positions),
            n_cog,
            len(self.stoi),
        )

    def _cognate_for_seq_pos(self, seq_idx: int, pos: int) -> int:
        """Return LB cognate flag for the sign at (seq_idx, pos)."""
        bid_idx = self.sequences[seq_idx][0][pos]
        bid = self.itos.get(bid_idx, "")
        if not bid:
            return NO_COGNATE
        return self.lb_cognate.get(bid, NO_COGNATE)

    def __len__(self) -> int:
        return len(self._positions)

    def __getitem__(self, idx: int) -> Tuple[
        torch.LongTensor,
        torch.LongTensor,
        torch.LongTensor,
    ]:
        seq_idx, pos = self._positions[idx]
        seq, _ = self.sequences[seq_idx]

        anchor = torch.tensor(seq[pos], dtype=torch.long)

        # Build context window with anchor MASKED so the model must use
        # surrounding context, not the token identity, to predict.
        w = self.window_size
        window_len = 2 * w + 1
        context = torch.full((window_len,), PAD_IDX, dtype=torch.long)
        mask_token = len(self.stoi)  # vocab_size = MASK for context encoder

        for i, offset in enumerate(range(-w, w + 1)):
            src_idx = pos + offset
            if 0 <= src_idx < len(seq):
                if offset == 0:
                    context[i] = mask_token  # mask the anchor!
                else:
                    context[i] = seq[src_idx]

        lb = torch.tensor(
            self._cognate_for_seq_pos(seq_idx, pos),
            dtype=torch.long,
        )
        return anchor, context, lb


class MaskedLMDataset(Dataset):
    """BERT-style masked language modelling over Linear A sign sequences.

    Each item returns ``(masked_seq, original_seq, attention_mask)``.
    15 % of non‑padding tokens are masked according to the standard
    scheme: 80 % → ``[MASK]``, 10 % → random token, 10 % → unchanged.

    Parameters
    ----------
    db_path : str
        Path to ``lineara_full.db``.
    max_length : int
        Pad / truncate each sequence.
    mask_prob : float
        Fraction of non‑padding tokens to mask (default 0.15).
    period : str or None
        Filter by *minoan_period*.
    site : str or None
        Filter by site prefix.
    bennett_ids : list[str] or None
        Restrict vocabulary.
    """

    def __init__(
        self,
        db_path: str,
        max_length: int = 64,
        mask_prob: float = 0.15,
        period: Optional[str] = None,
        site: Optional[str] = None,
        bennett_ids: Optional[List[str]] = None,
    ) -> None:
        self.max_length = max_length
        self.mask_prob = mask_prob
        self.stoi, self.itos = _build_vocab(db_path, bennett_ids)
        self.sequences = _load_sequences(db_path, self.stoi, period, site)
        # [MASK] token is vocab_size; [PAD] is 0
        self.mask_token = len(self.stoi)

        logger.info(
            "MaskedLMDataset: %d sequences, vocab=%d, mask_token=%d, "
            "max_len=%d, mask_prob=%.2f",
            len(self.sequences),
            len(self.stoi),
            self.mask_token,
            max_length,
            mask_prob,
        )

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Tuple[
        torch.LongTensor,
        torch.LongTensor,
        torch.LongTensor,
    ]:
        seq, _ = self.sequences[idx]

        # Pad / truncate
        original = torch.full((self.max_length,), PAD_IDX, dtype=torch.long)
        mask = torch.zeros(self.max_length, dtype=torch.long)
        keep = seq[: self.max_length]
        n = len(keep)
        original[:n] = torch.tensor(keep, dtype=torch.long)
        mask[:n] = 1  # attention mask: 1 = real token, 0 = pad

        masked = original.clone()

        # Determine which tokens to mask
        n_mask = max(1, int(n * self.mask_prob))
        candidate_positions = torch.arange(n)
        perm = torch.randperm(n)[:n_mask]

        for pos in perm:
            prob = torch.rand(1).item()
            if prob < 0.8:
                masked[pos] = self.mask_token
            elif prob < 0.9:
                # Random token in [1, vocab_size)
                masked[pos] = torch.randint(
                    1, len(self.stoi), (1,), dtype=torch.long
                ).item()
            # else: 10 % unchanged (keep original)

        return masked, original, mask
