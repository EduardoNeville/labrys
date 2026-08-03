"""Sign embedding model for Linear A decipherment — phonetic class predictor.

Trains a small transformer to predict the phonetic class of a Linear A
sign from its MASKED context window, using the 44 CONFIRMED syllabograms
as supervised labels.  The anchor sign is replaced with [MASK], forcing
the model to predict purely from context.

Supports two label granularities:
- **fine** (36 classes): exact phonetic value (a, pa, te, ...)
- **coarse** (4 classes): broad phonological category (vowel, labial,
  dental/coronal, velar/palatal)
"""

from __future__ import annotations

import csv
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from pipeline.ml.data import (
    ContrastiveSignDataset,
    PAD_IDX,
    SYLLABOGRAM_RANGE,
)

logger = logging.getLogger(__name__)


# ── phonological category mapping ────────────────────────────────────────────

# Broad phonological groups for the 36 CONFIRMED phonetic values.
# Each value maps to a coarse category ID 0..3.
_PHONEME_TO_COARSE: Dict[str, int] = {
    # Vowels
    "a": 0, "i": 0, "o": 0, "u": 0,
    # Labial
    "pa": 1, "pi": 1, "me": 1, "mi": 1, "mo": 1, "wa": 1, "wi": 1,
    # Dental / coronal
    "te": 2, "ti": 2, "to": 2, "tu": 2,
    "na": 2, "ne": 2, "ni": 2, "nu": 2,
    "sa": 2, "se": 2, "si": 2, "so": 2,
    "za": 2, "ze": 2, "zo": 2,
    "re": 2, "ri": 2, "ru": 2, "la": 2,
    # Velar / palatal
    "ja": 3, "ka": 3, "ke": 3, "ki": 3, "ko": 3, "ku": 3,
}

COARSE_CATEGORY_NAMES = {0: "vowel", 1: "labial", 2: "dental/coronal", 3: "velar/palatal"}


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_phonetic_classes(
    refined_grid_path: str,
    coarse: bool = True,
) -> Tuple[Dict[str, int], Dict[int, str], Dict[str, int]]:
    """Parse the refined phonetic grid → {bennett_id: class_id, …}.

    Parameters
    ----------
    refined_grid_path : str
    coarse : bool
        If True, use 4 broad phonological categories.  If False, use the
        original 36 fine-grained phonetic values.

    Returns
    -------
    bennett_to_class : dict
        Bennett ID → class label (or -1 for UNCERTAIN).
    class_to_label : dict
        Class label → human-readable label string.
    bennett_to_flag : dict
        Bennett ID → 1 (CONFIRMED) or 0 (UNCERTAIN).
    """
    bennett_to_class: Dict[str, int] = {}
    class_to_label: Dict[int, str] = {}
    bennett_to_flag: Dict[str, int] = {}

    confirmed_values: Dict[str, str] = {}
    with open(refined_grid_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            val = (row.get("refined_value") or "").strip()
            dec = (row.get("decision") or "").strip()
            if not bid:
                continue
            bennett_to_flag[bid] = 1 if dec == "CONFIRM" else 0
            if dec == "CONFIRM" and val and val != "?":
                confirmed_values[bid] = val

    if coarse:
        # Map each confirmed sign → broad category
        for bid, val in confirmed_values.items():
            coarse_id = _PHONEME_TO_COARSE.get(val, -1)
            if coarse_id >= 0:
                bennett_to_class[bid] = coarse_id
        for cid in sorted(set(bennett_to_class.values())):
            class_to_label[cid] = COARSE_CATEGORY_NAMES.get(cid, f"group_{cid}")
    else:
        # Fine-grained: one class per unique phonetic value
        unique_vals = sorted(set(confirmed_values.values()))
        val_to_class = {v: i for i, v in enumerate(unique_vals)}
        for bid, val in confirmed_values.items():
            bennett_to_class[bid] = val_to_class[val]
            class_to_label[val_to_class[val]] = val

    logger.info(
        "Phonetic classes: %d %s from %d CONFIRMED signs",
        len(class_to_label),
        "coarse categories" if coarse else "fine values",
        len(confirmed_values),
    )
    return bennett_to_class, class_to_label, bennett_to_flag


# ── model ────────────────────────────────────────────────────────────────────


class SignContextEncoder(nn.Module):
    """Small transformer that encodes a sign from its masked context window.

    The context window has the anchor sign replaced by a [MASK] token at
    index ``vocab_size``, so the encoder must infer the sign's properties
    purely from surrounding signs.

    Parameters
    ----------
    vocab_size : int
        Number of Bennett IDs (excl. PAD).  The embedding table has
        ``vocab_size + 1`` rows to accommodate the MASK token.
    d_model : int
        Hidden dimension.
    n_head : int
        Attention heads.
    n_layers : int
        Transformer layers.
    dropout : float
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        n_head: int = 4,
        n_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        # +1 for the MASK token (at index vocab_size)
        self.token_embedding = nn.Embedding(
            vocab_size + 1, d_model, padding_idx=PAD_IDX
        )
        self.position_embedding = nn.Embedding(256, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_head,
            dropout=dropout,
            batch_first=True,
            dim_feedforward=d_model * 4,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        """Encode each item from its (masked) context window.

        Parameters
        ----------
        context : (B, window_len)
            Context window with anchor at the middle position replaced by
            the MASK token.

        Returns
        -------
        embeddings : (B, d_model)
            Contextualised embedding of the masked position.
        """
        B, L = context.shape
        positions = torch.arange(L, device=context.device).unsqueeze(0).expand(B, -1)
        pad_mask = context.eq(PAD_IDX)

        tok_emb = self.token_embedding(context) * math.sqrt(self.d_model)
        pos_emb = self.position_embedding(positions)
        x = self.dropout(tok_emb + pos_emb)

        x = self.encoder(x, src_key_padding_mask=pad_mask)

        # Pool at anchor position (middle of window)
        anchor_pos = L // 2
        pooled = x[:, anchor_pos, :]  # (B, d_model)
        return self.norm(pooled)


class PhoneticClassifier(nn.Module):
    """Predict a sign's phonetic class from its masked context window.

    Parameters
    ----------
    vocab_size : int
        Number of Bennett IDs in the vocabulary.
    num_classes : int
        Number of output phonetic classes (4 for coarse, 36 for fine).
    d_model : int
    n_head : int
    n_layers : int
    dropout : float
    """

    def __init__(
        self,
        vocab_size: int,
        num_classes: int,
        d_model: int = 128,
        n_head: int = 4,
        n_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.encoder = SignContextEncoder(
            vocab_size=vocab_size,
            d_model=d_model,
            n_head=n_head,
            n_layers=n_layers,
            dropout=dropout,
        )
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(
        self, context: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Return (logits, embeddings).

        Parameters
        ----------
        context : (B, window_len)

        Returns
        -------
        logits : (B, num_classes)
        embeddings : (B, d_model)
            Pre-classifier contextual embeddings.
        """
        emb = self.encoder(context)
        logits = self.classifier(emb)
        return logits, emb


# ── training ─────────────────────────────────────────────────────────────────


def train_phonetic_classifier(
    model: PhoneticClassifier,
    train_loader: DataLoader,
    bennett_to_class: Dict[str, int],
    stoi: Dict[str, int],
    itos: Dict[int, str],
    epochs: int = 20,
    lr: float = 1e-3,
    device: str = "cuda",
    output_dir: Optional[str] = None,
) -> List[float]:
    """Train the phonetic classifier.

    Returns list of per-epoch average losses.
    """
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    loss_fn = nn.CrossEntropyLoss(ignore_index=-1)
    losses: List[float] = []

    # Build lookup: bennett_id index → phonetic class (-1 = UNCERTAIN)
    idx_to_class = torch.full((len(stoi),), -1, dtype=torch.long)
    for bid, cls in bennett_to_class.items():
        if bid in stoi:
            idx_to_class[stoi[bid]] = cls
    idx_to_class = idx_to_class.to(device)

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        epoch_tokens = 0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")

        for anchor, context, _ in pbar:
            anchor = anchor.to(device)
            context = context.to(device)

            labels = idx_to_class[anchor]  # (B,) — -1 = UNCERTAIN
            mask = labels >= 0
            if mask.sum() == 0:
                continue

            logits, _ = model(context)
            loss = loss_fn(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * mask.sum().item()
            epoch_tokens += mask.sum().item()
            pbar.set_postfix(
                {"loss": f"{loss.item():.4f}", "n": mask.sum().item()}
            )

        scheduler.step()

        avg_loss = epoch_loss / max(epoch_tokens, 1)
        losses.append(avg_loss)
        logger.info(
            "Epoch %d/%d — avg loss: %.6f",
            epoch + 1, epochs, avg_loss,
        )

        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "loss": avg_loss,
                    "vocab_size": len(stoi),
                    "stoi": stoi,
                    "itos": itos,
                    "bennett_to_class": bennett_to_class,
                },
                out / f"classifier_epoch_{epoch+1:03d}.pt",
            )

    return losses


def extract_embeddings(
    model: PhoneticClassifier,
    bennett_ids: List[str],
    stoi: Dict[str, int],
    d_model: int = 128,
    device: str = "cuda",
) -> Tuple[torch.Tensor, List[str]]:
    """Extract L2-normalised token embeddings for a set of Bennett IDs.

    Uses raw token embeddings (not contextual) so each sign has a fixed
    vector for nearest-neighbour lookup.
    """
    model = model.to(device)
    model.eval()

    bids = []
    indices = []
    for bid in bennett_ids:
        idx = stoi.get(bid)
        if idx is not None and idx != PAD_IDX:
            bids.append(bid)
            indices.append(idx)

    if not indices:
        return torch.empty(0, d_model), []

    idx_tensor = torch.tensor(indices, device=device)
    with torch.no_grad():
        emb = model.encoder.token_embedding(idx_tensor)
        emb = F.normalize(emb, p=2, dim=-1)

    return emb.cpu(), bids
