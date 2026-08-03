"""Data augmentation strategies for the small Linear A training corpus.

The corpus contains only ~11K tokens across ~1,700 inscriptions — too
small for robust transformer training.  This module provides four
augmentation strategies that exploit the known structure of the Linear A
syllabary:

1. **Sign substitution** — replaces signs with phonetically similar
   alternatives using the Linear B cognate mapping.  Similarity is
   defined by shared consonant or shared vowel in the LB reading.

2. **Window cropping** — extracts random contiguous sub-sequences from
   longer inscriptions, creating new training examples.

3. **Sequence reversal** — reverses the entire sign sequence, creating a
   synthetic reverse corpus that preserves bigram statistics.

4. **Curriculum learning** — sorts sequences by descending length so the
   model sees longer (more informative) examples first.
"""

from __future__ import annotations

import csv
import logging
import random
from typing import Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset

from pipeline.ml.data import PAD_IDX

logger = logging.getLogger(__name__)


# ── phonetic similarity helpers ───────────────────────────────────────────────


def _build_phonetic_groups(
    la_lb_mapping_path: str,
) -> Tuple[Dict[str, List[int]], Dict[str, List[int]], Dict[str, str]]:
    """Build consonant-group and vowel-group mappings from the LA→LB mapping.

    For every syllabogram with a known LB phonetic value (non-empty,
    non-'?'), we assign it to two groups:

    * **consonant group** — keyed by the first character of the LB value
      (e.g. ``"p"`` for ``"pa"``, ``"pi"``, ``"pu"``).  Vowel-only
      values (a, e, i, o, u) are placed in their own groups.
    * **vowel group** — keyed by the vowel (second character for CV
      signs; the value itself for V signs).

    Returns
    -------
    consonant_groups : dict[str, list[int]]
        Consonant-class → list of Bennett ID indices (need ``stoi`` to
        resolve).
    vowel_groups : dict[str, list[int]]
        Vowel-class → list of Bennett ID indices.
    sign_to_lb : dict[str, str]
        Bennett ID → LB phonetic value (for signs that have one).
    """
    consonant_groups: Dict[str, List[str]] = {}
    vowel_groups: Dict[str, List[str]] = {}
    sign_to_lb: Dict[str, str] = {}

    with open(la_lb_mapping_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            lb_val = (row.get("lb_value") or "").strip()
            sign_type = (row.get("sign_type") or "").strip()

            if not bid or not lb_val or lb_val == "?":
                continue
            # Only syllabograms have CV/V phonetic structure
            if sign_type != "syllabogram":
                continue

            sign_to_lb[bid] = lb_val

            # Consonant group
            if len(lb_val) == 1:
                # Vowel sign
                c_group = f"V_{lb_val}"
            else:
                c_group = lb_val[0]  # first char = consonant
            consonant_groups.setdefault(c_group, []).append(bid)

            # Vowel group
            v_group = lb_val[-1]  # last char = vowel
            vowel_groups.setdefault(v_group, []).append(bid)

    logger.info(
        "Phonetic groups: %d consonant classes, %d vowel classes, %d mapped signs",
        len(consonant_groups),
        len(vowel_groups),
        len(sign_to_lb),
    )
    return consonant_groups, vowel_groups, sign_to_lb


def _resolve_phonetic_groups(
    consonant_groups: Dict[str, List[str]],
    vowel_groups: Dict[str, List[str]],
    stoi: Dict[str, int],
) -> Tuple[Dict[str, List[int]], Dict[str, List[int]]]:
    """Convert Bennett-ID-based groups to index-based groups."""
    c_idx: Dict[str, List[int]] = {}
    v_idx: Dict[str, List[int]] = {}

    for key, bids in consonant_groups.items():
        indices = [stoi[b] for b in bids if b in stoi]
        if indices:
            c_idx[key] = indices

    for key, bids in vowel_groups.items():
        indices = [stoi[b] for b in bids if b in stoi]
        if indices:
            v_idx[key] = indices

    return c_idx, v_idx


# ── augmentation transforms ───────────────────────────────────────────────────


def sign_substitution(
    sequence: List[int],
    stoi: Dict[str, int],
    itos: Dict[int, str],
    sign_to_lb: Dict[str, str],
    c_groups: Dict[str, List[int]],
    v_groups: Dict[str, List[int]],
    p_substitute: float = 0.15,
) -> List[int]:
    """Apply phonetic sign substitution to a single sequence.

    Each non-padding sign with a known LB cognate has probability
    *p_substitute* of being replaced by a phonetically similar sign.
    The substitute is chosen randomly from either the same-consonant
    or same-vowel group (50/50 split).

    Parameters
    ----------
    sequence : list[int]
        List of sign indices.
    p_substitute : float
        Probability of substituting each eligible sign.

    Returns
    -------
    list[int]
        Augmented sequence (same length).
    """
    if not sequence:
        return sequence

    augmented = list(sequence)
    for i, idx in enumerate(augmented):
        if idx == PAD_IDX:
            continue
        if random.random() > p_substitute:
            continue

        bid = itos.get(idx, "")
        if not bid or bid not in sign_to_lb:
            continue

        lb_val = sign_to_lb[bid]

        # Determine consonant and vowel groups
        if len(lb_val) == 1:
            c_key = f"V_{lb_val}"
        else:
            c_key = lb_val[0]
        v_key = lb_val[-1]

        candidates: List[int] = []

        # 50% chance: same-consonant substitution
        if random.random() < 0.5:
            group = c_groups.get(c_key, [])
            candidates = [g for g in group if g != idx]
        else:
            group = v_groups.get(v_key, [])
            candidates = [g for g in group if g != idx]

        if candidates:
            augmented[i] = random.choice(candidates)

    return augmented


def window_crop(
    sequence: List[int],
    min_length: int = 3,
    max_length: Optional[int] = None,
) -> List[int]:
    """Extract a random contiguous sub-sequence.

    Parameters
    ----------
    sequence : list[int]
        Original sequence (non-negative indices, PAD at end).
    min_length : int
        Minimum crop length (default 3).  Crops shorter than this are
        not useful for context-based learning.
    max_length : int or None
        Maximum crop length.  If None, uses the full sequence length.

    Returns
    -------
    list[int]
        Cropped sequence (padded to *max_length* if provided).
    """
    # Find actual sequence length (up to first PAD)
    n = len(sequence)
    for i, idx in enumerate(sequence):
        if idx == PAD_IDX:
            n = i
            break

    if n < min_length:
        return list(sequence)

    crop_len = random.randint(min_length, min(n, max_length or n))
    start = random.randint(0, n - crop_len)
    crop = sequence[start : start + crop_len]

    if max_length is not None:
        padded = [PAD_IDX] * max_length
        keep = crop[:max_length]
        padded[: len(keep)] = keep
        return padded

    return crop


def reverse_sequence(sequence: List[int]) -> List[int]:
    """Reverse a sign sequence.

    Padding tokens (PAD_IDX) are moved to the end after reversal so the
    reversed non-padding portion is contiguous at the front.

    Parameters
    ----------
    sequence : list[int]
        Original sequence (may contain trailing PADs).

    Returns
    -------
    list[int]
        Reversed sequence with PADs at the end.
    """
    # Split into content and padding
    content = []
    pads = []
    for idx in sequence:
        if idx == PAD_IDX:
            pads.append(idx)
        else:
            content.append(idx)

    # Reverse content and append pads
    return list(reversed(content)) + pads


# ── dataset wrappers ──────────────────────────────────────────────────────────


class AugmentedSequenceDataset(Dataset):
    """Wraps an existing sequence dataset and applies augmentation.

    Returns both original and augmented versions of each sequence,
    effectively doubling (or more) the dataset size.  Augmentations
    are applied **on-the-fly** during iteration.

    The dataset yields ``(augmented_seq, gorila_id)`` pairs compatible
    with :class:`~pipeline.ml.data.LinearASignDataset`.

    Parameters
    ----------
    base_dataset : Dataset
        Underlying dataset (e.g. ``LinearASignDataset``).  Must return
        ``(tensor, gorila_id)`` pairs.
    la_lb_mapping_path : str
        Path to ``la_lb_mapping.csv`` for phonetic grouping.
    stoi : dict[str, int]
        Sign→index mapping from the base dataset.
    itos : dict[int, str]
        Index→sign mapping from the base dataset.
    max_length : int
        Sequence length for padding/truncation.
    augmentations : list[str]
        Which augmentation strategies to apply.  Options: ``"substitute"``,
        ``"crop"``, ``"reverse"``.  Default applies all three, so the
        augmented dataset has ``4×`` the original size (1 original + 3
        augmentations).
    p_substitute : float
        Probability of substituting an individual sign (default 0.15).
    min_crop_len : int
        Minimum crop length for window cropping (default 3).
    """

    def __init__(
        self,
        base_dataset: Dataset,
        la_lb_mapping_path: str,
        stoi: Dict[str, int],
        itos: Dict[int, str],
        max_length: int = 64,
        augmentations: Optional[List[str]] = None,
        p_substitute: float = 0.15,
        min_crop_len: int = 3,
    ) -> None:
        self.base = base_dataset
        self.max_length = max_length
        self.stoi = stoi
        self.itos = itos
        self.p_substitute = p_substitute
        self.min_crop_len = min_crop_len

        if augmentations is None:
            augmentations = ["substitute", "crop", "reverse"]
        self.augmentations = augmentations

        # Build phonetic groups for sign substitution
        c_raw, v_raw, self.sign_to_lb = _build_phonetic_groups(
            la_lb_mapping_path
        )
        self.c_groups, self.v_groups = _resolve_phonetic_groups(
            c_raw, v_raw, stoi
        )

        self._n_base = len(base_dataset)
        # Augmentation factor: 1 (original) + len(augmentations)
        self._aug_factor = 1 + len(augmentations)

        logger.info(
            "AugmentedSequenceDataset: %d base × %d aug = %d total examples",
            self._n_base,
            self._aug_factor,
            len(self),
        )

    def __len__(self) -> int:
        return self._n_base * self._aug_factor

    def __getitem__(self, idx: int) -> Tuple[torch.LongTensor, str]:
        base_idx = idx % self._n_base
        aug_idx = idx // self._n_base

        tensor, gid = self.base[base_idx]
        seq = tensor.tolist()

        if aug_idx == 0:
            # Original — no augmentation
            return tensor, gid

        aug_name = self.augmentations[aug_idx - 1]

        if aug_name == "substitute":
            augmented_seq = sign_substitution(
                seq,
                self.stoi,
                self.itos,
                self.sign_to_lb,
                self.c_groups,
                self.v_groups,
                p_substitute=self.p_substitute,
            )
        elif aug_name == "crop":
            augmented_seq = window_crop(
                seq, min_length=self.min_crop_len, max_length=self.max_length
            )
        elif aug_name == "reverse":
            augmented_seq = reverse_sequence(seq)
        else:
            augmented_seq = seq

        # Pad / truncate
        result = torch.full(
            (self.max_length,), PAD_IDX, dtype=torch.long
        )
        keep = augmented_seq[: self.max_length]
        result[: len(keep)] = torch.tensor(keep, dtype=torch.long)

        return result, gid


# ── curriculum learning ──────────────────────────────────────────────────────


def curriculum_sorted_sequences(
    dataset: Dataset,
    max_length: int = 64,
) -> List[Tuple[torch.LongTensor, str]]:
    """Sort sequences by descending (non‑padding) length.

    Returns a flat list of ``(tensor, gorila_id)`` tuples sorted so the
    longest sequences come first.  This is intended for use with a
    ``DataLoader(shuffle=False)`` to implement curriculum learning.

    Parameters
    ----------
    dataset : Dataset
        Any dataset that returns ``(tensor, gorila_id)``.
    max_length : int
        Sequence length used for length calculation.

    Returns
    -------
    list
        Sorted list of all examples.
    """
    items: List[Tuple[torch.LongTensor, str, int]] = []
    for i in range(len(dataset)):
        tensor, gid = dataset[i]
        # Count non-padding tokens
        n_tokens = (tensor != PAD_IDX).sum().item()
        items.append((tensor, gid, int(n_tokens)))

    items.sort(key=lambda x: x[2], reverse=True)

    logger.info(
        "Curriculum sort: %d sequences, longest=%d, shortest=%d",
        len(items),
        items[0][2] if items else 0,
        items[-1][2] if items else 0,
    )

    return [(t, g) for t, g, _ in items]


class CurriculumDataset(Dataset):
    """Dataset wrapper that returns sequences in curriculum order.

    Wraps any sequence dataset, sorts its examples by descending
    sequence length, and yields them in that order.  Use with
    ``DataLoader(shuffle=False)``.

    Parameters
    ----------
    dataset : Dataset
        Underlying dataset.
    max_length : int
        Sequence length for length calculation.
    """

    def __init__(
        self,
        dataset: Dataset,
        max_length: int = 64,
    ) -> None:
        self.max_length = max_length
        self._items = curriculum_sorted_sequences(dataset, max_length)

        logger.info(
            "CurriculumDataset: %d sequences sorted by descending length",
            len(self._items),
        )

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, idx: int) -> Tuple[torch.LongTensor, str]:
        return self._items[idx]


# ── convenience ──────────────────────────────────────────────────────────────


def create_augmented_loader(
    base_dataset: Dataset,
    la_lb_mapping_path: str,
    stoi: Dict[str, int],
    itos: Dict[int, str],
    max_length: int = 64,
    batch_size: int = 16,
    augmentations: Optional[List[str]] = None,
    curriculum: bool = False,
    p_substitute: float = 0.15,
) -> Tuple[Dataset, torch.utils.data.DataLoader]:
    """Create an augmented dataset and DataLoader.

    Parameters
    ----------
    base_dataset : Dataset
        Underlying sequence dataset.
    la_lb_mapping_path : str
        Path to the LA→LB sign mapping CSV.
    stoi : dict
        Sign→index mapping.
    itos : dict
        Index→sign mapping.
    max_length : int
        Sequence length.
    batch_size : int
        DataLoader batch size.
    augmentations : list[str] or None
        Augmentation strategies to apply.
    curriculum : bool
        If True, sort sequences by descending length before batching.
    p_substitute : float
        Sign substitution probability.

    Returns
    -------
    dataset : Dataset
        The augmented (and optionally curriculum-sorted) dataset.
    loader : DataLoader
        Configured DataLoader.
    """
    aug_dataset: Dataset = AugmentedSequenceDataset(
        base_dataset,
        la_lb_mapping_path,
        stoi,
        itos,
        max_length=max_length,
        augmentations=augmentations,
        p_substitute=p_substitute,
    )

    if curriculum:
        aug_dataset = CurriculumDataset(aug_dataset, max_length)

    shuffle = not curriculum  # curriculum needs deterministic order
    loader = torch.utils.data.DataLoader(
        aug_dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=True,
    )

    logger.info(
        "Augmented loader: %d batches, batch_size=%d, curriculum=%s",
        len(loader),
        batch_size,
        curriculum,
    )
    return aug_dataset, loader
