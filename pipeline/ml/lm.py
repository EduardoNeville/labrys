"""Masked language model for Linear A sign sequences.

Trains a small BERT-style transformer to predict masked signs in
inscription sequences.  Serves as a baseline for the contrastive model
and provides contextual sign representations that can be probed for
phonetic structure.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from pipeline.ml.data import MaskedLMDataset, PAD_IDX

logger = logging.getLogger(__name__)


class SignLM(nn.Module):
    """Small BERT-like transformer for Linear A sign sequences.

    Parameters
    ----------
    vocab_size : int
        Number of unique Bennett IDs in the vocabulary, excluding PAD
        and MASK.  Input dimensionality becomes ``vocab_size + 2``.
    d_model : int
        Hidden dimension (default 128).
    n_head : int
        Attention heads (default 4).
    n_layers : int
        Transformer layers (default 2).
    max_len : int
        Maximum sequence length for positional embeddings (default 128).
    dropout : float
        Dropout rate (default 0.1).
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        n_head: int = 4,
        n_layers: int = 2,
        max_len: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model

        # Token embeddings: vocab_size sign tokens + [PAD]=0 + [MASK]=vocab_size
        self.token_embedding = nn.Embedding(
            vocab_size + 1, d_model, padding_idx=PAD_IDX
        )
        self.position_embedding = nn.Embedding(max_len, d_model)
        self.dropout = nn.Dropout(dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_head,
            dropout=dropout,
            batch_first=True,
            dim_feedforward=d_model * 4,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        self.output_proj = nn.Linear(d_model, vocab_size)
        # Tie output projection to token embedding for efficiency
        # (skipped — weight tying causes issues with mismatched vocab sizes)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Return logits for every position.

        Parameters
        ----------
        input_ids : (B, L)
            Token indices including PAD and MASK.
        attention_mask : (B, L) or None
            1 for real tokens, 0 for padding.

        Returns
        -------
        logits : (B, L, vocab_size)
        """
        B, L = input_ids.shape
        positions = torch.arange(L, device=input_ids.device).unsqueeze(0).expand(B, -1)

        tok_emb = self.token_embedding(input_ids) * math.sqrt(self.d_model)
        pos_emb = self.position_embedding(positions)
        x = self.dropout(tok_emb + pos_emb)

        pad_mask = None
        if attention_mask is not None:
            pad_mask = attention_mask.eq(0)

        x = self.encoder(x, src_key_padding_mask=pad_mask)
        logits = self.output_proj(x)  # (B, L, vocab_size)
        return logits


# ── training ─────────────────────────────────────────────────────────────────


def train_lm(
    model: SignLM,
    train_loader: DataLoader,
    epochs: int = 20,
    lr: float = 1e-3,
    device: str = "cuda",
    output_dir: Optional[str] = None,
) -> List[float]:
    """Train the masked language model.

    Parameters
    ----------
    model : SignLM
    train_loader : DataLoader
        Yields ``(masked_seq, original_seq, attention_mask)``.
    epochs : int
    lr : float
    device : str
    output_dir : str or None
        Directory for checkpoint saves.

    Returns
    -------
    losses : list[float]
        Per-epoch average loss values.
    """
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    losses: List[float] = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        epoch_tokens = 0
        pbar = tqdm(train_loader, desc=f"LM Epoch {epoch+1}/{epochs}")

        for masked, original, attn_mask in pbar:
            masked = masked.to(device)
            original = original.to(device)
            attn_mask = attn_mask.to(device)

            logits = model(masked, attn_mask)  # (B, L, V)

            # Compute loss only on non-padding tokens
            loss = loss_fn(
                logits.reshape(-1, model.vocab_size),
                original.reshape(-1),
            )

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * attn_mask.sum().item()
            epoch_tokens += attn_mask.sum().item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        scheduler.step()

        avg_loss = epoch_loss / max(epoch_tokens, 1)
        losses.append(avg_loss)
        lr_now = optimizer.param_groups[0]["lr"]
        logger.info(
            "LM Epoch %d/%d — avg loss: %.6f, lr: %.2e",
            epoch + 1, epochs, avg_loss, lr_now,
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
                    "vocab_size": model.vocab_size,
                    "d_model": model.d_model,
                },
                out / f"signlm_epoch_{epoch+1:03d}.pt",
            )

    return losses


def evaluate_perplexity(
    model: SignLM,
    eval_loader: DataLoader,
    device: str = "cuda",
) -> float:
    """Compute per-token perplexity on the evaluation set.

    Returns the perplexity (exp of average cross-entropy).
    """
    model = model.to(device)
    model.eval()
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD_IDX, reduction="sum")
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for masked, original, attn_mask in eval_loader:
            masked = masked.to(device)
            original = original.to(device)
            attn_mask = attn_mask.to(device)

            logits = model(masked, attn_mask)
            loss = loss_fn(
                logits.reshape(-1, model.vocab_size),
                original.reshape(-1),
            )
            total_loss += loss.item()
            total_tokens += attn_mask.sum().item()

    avg_loss = total_loss / max(total_tokens, 1)
    ppl = math.exp(avg_loss)
    logger.info("Evaluation — loss: %.4f, perplexity: %.2f", avg_loss, ppl)
    return ppl
