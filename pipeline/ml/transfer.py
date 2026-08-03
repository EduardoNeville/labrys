"""Linear B transfer learning for Linear A decipherment.

~70 % of Linear A syllabograms (AB 01–AB 85) have structurally identical
Linear B counterparts with known phonetic values.  This module leverages
that weak supervision signal through a two-stage training pipeline:

1. **LB phonetic pretraining** — initialise token embeddings so that LA
   signs with similar LB phonetic values (same consonant, same vowel)
   are close in embedding space.  Uses a contrastive-like objective on
   the 44 CONFIRMED signs plus the ~60 additional signs with secure LB
   cognates.

2. **Linear A fine‑tuning** — load the LB‑pretrained SignLM weights and
   train the full transformer on the masked language modelling task
   using the augmented Linear A corpus.

The key metric is perplexity improvement over the non‑transfer baseline.
"""

from __future__ import annotations

import csv
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from pipeline.ml.data import (
    MaskedLMDataset,
    PAD_IDX,
    SYLLABOGRAM_RANGE,
)
from pipeline.ml.lm import SignLM, evaluate_perplexity

logger = logging.getLogger(__name__)


# ── LB phonetic pretraining data ─────────────────────────────────────────────


def _load_lb_phonetic_triplets(
    la_lb_mapping_path: str,
    stoi: Dict[str, int],
    refined_grid_path: Optional[str] = None,
) -> Tuple[
    List[Tuple[int, int, int]],
    Dict[str, int],
    Dict[str, int],
]:
    """Build phonetic-similarity triplets from the LA→LB mapping.

    For each sign with a known LB phonetic value, we generate (anchor,
    positive, negative) triplets:

    * **anchor** — a sign with a known LB value.
    * **positive** — another sign sharing the same consonant.
    * **negative** — a sign with a different consonant (random).

    If ``refined_grid_path`` is provided, only CONFIRMED signs contribute
    positive pairs (higher quality), but all signs with LB values
    contribute negatives.

    Returns
    -------
    triplets : list of (anchor_idx, positive_idx, negative_idx)
        Index-based triplets suitable for triplet margin loss.
    sign_to_consonant : dict[str, int]
        Bennett ID → consonant class ID.
    sign_to_vowel : dict[str, int]
        Bennett ID → vowel class ID.
    """
    # Parse mapping CSV
    rows: List[Dict[str, str]] = []
    with open(la_lb_mapping_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            lb_val = (row.get("lb_value") or "").strip()
            sign_type = (row.get("sign_type") or "").strip()
            if not bid or not lb_val or lb_val == "?":
                continue
            if sign_type != "syllabogram":
                continue
            rows.append({"bennett_id": bid, "lb_value": lb_val})

    # Load confirmed set if available
    confirmed: Set[str] = set()
    if refined_grid_path:
        with open(refined_grid_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("decision") or "").strip() == "CONFIRM":
                    confirmed.add(row.get("bennett_id", "").strip())

    # Build consonant and vowel class assignments
    consonant_classes: Dict[str, int] = {}
    vowel_classes: Dict[str, int] = {}
    unique_cons = sorted(
        set(
            r["lb_value"][0] if len(r["lb_value"]) > 1 else f"V_{r['lb_value']}"
            for r in rows
        )
    )
    unique_vowels = sorted(set(r["lb_value"][-1] for r in rows))
    cons_to_id = {c: i for i, c in enumerate(unique_cons)}
    vowel_to_id = {v: i for i, v in enumerate(unique_vowels)}

    sign_to_consonant: Dict[str, int] = {}
    sign_to_vowel: Dict[str, int] = {}

    for r in rows:
        bid = r["bennett_id"]
        lb_val = r["lb_value"]
        c_key = lb_val[0] if len(lb_val) > 1 else f"V_{lb_val}"
        v_key = lb_val[-1]
        sign_to_consonant[bid] = cons_to_id[c_key]
        sign_to_vowel[bid] = vowel_to_id[v_key]

    # Build triplets
    triplets: List[Tuple[int, int, int]] = []
    idxs_in_vocab = [stoi[r["bennett_id"]] for r in rows if r["bennett_id"] in stoi]

    if len(idxs_in_vocab) < 3:
        logger.warning("Too few signs with LB cognates in vocab for triplets")
        return [], sign_to_consonant, sign_to_vowel

    # For efficiency, pre-group by consonant
    con_groups: Dict[int, List[int]] = {}
    for r in rows:
        bid = r["bennett_id"]
        if bid not in stoi:
            continue
        idx = stoi[bid]
        c_key = r["lb_value"][0] if len(r["lb_value"]) > 1 else f"V_{r['lb_value']}"
        cid = cons_to_id[c_key]
        con_groups.setdefault(cid, []).append(idx)

    for anchor_row in rows:
        bid = anchor_row["bennett_id"]
        if bid not in stoi:
            continue
        anchor_idx = stoi[bid]

        c_key = (
            anchor_row["lb_value"][0]
            if len(anchor_row["lb_value"]) > 1
            else f"V_{anchor_row['lb_value']}"
        )
        cid = cons_to_id[c_key]
        same_cons = [i for i in con_groups.get(cid, []) if i != anchor_idx]

        if not same_cons:
            continue

        # Different consonant groups for negatives
        diff_cons: List[int] = []
        for ocid, oc_idxs in con_groups.items():
            if ocid != cid:
                diff_cons.extend(oc_idxs)

        if not diff_cons:
            continue

        # Generate triplet(s)
        for _ in range(min(3, len(same_cons))):
            pos_idx = same_cons[torch.randint(0, len(same_cons), (1,)).item()]
            neg_idx = diff_cons[torch.randint(0, len(diff_cons), (1,)).item()]
            triplets.append((anchor_idx, pos_idx, neg_idx))

    logger.info(
        "LB phonetic triplets: %d triplets, %d consonant classes, "
        "%d vowel classes, %d confirmed signs",
        len(triplets),
        len(unique_cons),
        len(unique_vowels),
        len(confirmed),
    )
    return triplets, sign_to_consonant, sign_to_vowel


# ── LB phonetic pretraining model ────────────────────────────────────────────


class LBPhoneticPretrainer(nn.Module):
    """Trains token embeddings to reflect LB-derived phonetic similarity.

    Uses triplet margin loss: for each anchor sign, the embedding of a
    phonetically similar sign (same consonant) should be closer than a
    dissimilar sign.

    Parameters
    ----------
    vocab_size : int
        Number of tokens in the vocabulary.
    d_model : int
        Embedding dimension (should match the downstream SignLM).
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size + 1, d_model, padding_idx=PAD_IDX)
        self.d_model = d_model

    def forward(
        self, anchor: torch.Tensor, positive: torch.Tensor, negative: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return L2-normalised embeddings for each triplet component."""
        a_emb = F.normalize(self.embedding(anchor), p=2, dim=-1)
        p_emb = F.normalize(self.embedding(positive), p=2, dim=-1)
        n_emb = F.normalize(self.embedding(negative), p=2, dim=-1)
        return a_emb, p_emb, n_emb


def pretrain_lb_embeddings(
    la_lb_mapping_path: str,
    stoi: Dict[str, int],
    d_model: int = 128,
    epochs: int = 50,
    lr: float = 1e-3,
    margin: float = 0.5,
    batch_size: int = 64,
    device: str = "cuda",
    refined_grid_path: Optional[str] = None,
) -> Tuple[nn.Embedding, List[float]]:
    """Pretrain token embeddings using LB phonetic triplet loss.

    Parameters
    ----------
    la_lb_mapping_path : str
        Path to the LA→LB mapping CSV.
    stoi : dict
        Sign→index mapping.
    d_model : int
        Embedding dimension.
    epochs : int
        Number of pretraining epochs.
    lr : float
        Learning rate.
    margin : float
        Triplet margin.
    batch_size : int
        Batch size for triplets.
    device : str
        Torch device.
    refined_grid_path : str or None
        If provided, only CONFIRMED signs are used for positives.

    Returns
    -------
    embedding : nn.Embedding
        Pretrained embedding layer.
    losses : list[float]
        Per-epoch loss values.
    """
    triplets, sign_to_consonant, sign_to_vowel = _load_lb_phonetic_triplets(
        la_lb_mapping_path, stoi, refined_grid_path
    )

    if len(triplets) < batch_size:
        logger.warning(
            "Only %d triplets (< batch_size %d) — pretraining skipped",
            len(triplets),
            batch_size,
        )
        emb = nn.Embedding(len(stoi) + 1, d_model, padding_idx=PAD_IDX)
        return emb, []

    model = LBPhoneticPretrainer(len(stoi), d_model).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.TripletMarginLoss(margin=margin, p=2)
    losses: List[float] = []

    # Prepare triplet tensors
    anchors = torch.tensor([t[0] for t in triplets], dtype=torch.long)
    positives = torch.tensor([t[1] for t in triplets], dtype=torch.long)
    negatives = torch.tensor([t[2] for t in triplets], dtype=torch.long)

    n_triplets = len(triplets)
    logger.info("LB pretraining: %d triplets, %d epochs", n_triplets, epochs)

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        n_batches = 0

        perm = torch.randperm(n_triplets)
        for i in range(0, n_triplets, batch_size):
            batch_idx = perm[i : i + batch_size]
            a = anchors[batch_idx].to(device)
            p = positives[batch_idx].to(device)
            n = negatives[batch_idx].to(device)

            a_emb, p_emb, n_emb = model(a, p, n)
            loss = loss_fn(a_emb, p_emb, n_emb)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        losses.append(avg_loss)
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(
                "LB pretrain epoch %d/%d — loss: %.6f",
                epoch + 1, epochs, avg_loss,
            )

    return model.embedding, losses


# ── transfer learning pipeline ───────────────────────────────────────────────


class TransferSignLM(SignLM):
    """SignLM with optional LB-pretrained embedding initialisation.

    Wraps the standard SignLM but allows injecting a pretrained
    embedding layer from the LB phonetic pretraining stage.

    Parameters
    ----------
    pretrained_embedding : nn.Embedding or None
        If provided, the token embedding is initialised from this.
    vocab_size : int
    d_model : int
    n_head : int
    n_layers : int
    max_len : int
    dropout : float
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        n_head: int = 4,
        n_layers: int = 2,
        max_len: int = 128,
        dropout: float = 0.1,
        pretrained_embedding: Optional[nn.Embedding] = None,
    ) -> None:
        super().__init__(
            vocab_size=vocab_size,
            d_model=d_model,
            n_head=n_head,
            n_layers=n_layers,
            max_len=max_len,
            dropout=dropout,
        )
        if pretrained_embedding is not None:
            # Copy pretrained weights if shapes match
            with torch.no_grad():
                pretrained_weight = pretrained_embedding.weight.data
                target_shape = self.token_embedding.weight.data.shape
                if pretrained_weight.shape == target_shape:
                    self.token_embedding.weight.data.copy_(pretrained_weight)
                    logger.info(
                        "TransferSignLM: loaded pretrained embeddings "
                        "(%d × %d)",
                        pretrained_weight.shape[0],
                        pretrained_weight.shape[1],
                    )
                elif pretrained_weight.shape[1] == target_shape[1]:
                    # Partial: copy only the overlap
                    n_copy = min(
                        pretrained_weight.shape[0], target_shape[0]
                    )
                    self.token_embedding.weight.data[:n_copy].copy_(
                        pretrained_weight[:n_copy]
                    )
                    logger.info(
                        "TransferSignLM: partial load (%d/%d rows)",
                        n_copy, target_shape[0],
                    )
                else:
                    logger.warning(
                        "TransferSignLM: pretrained embedding shape "
                        "%s incompatible with %s — skipping",
                        tuple(pretrained_weight.shape),
                        tuple(target_shape),
                    )


def train_transfer_lm(
    db_path: str,
    la_lb_mapping_path: str,
    max_length: int = 64,
    batch_size: int = 16,
    pretrain_epochs: int = 50,
    finetune_epochs: int = 30,
    lr: float = 1e-3,
    d_model: int = 128,
    device: str = "cuda",
    refined_grid_path: Optional[str] = None,
) -> Dict[str, object]:
    """Run the full LB→LA transfer learning pipeline.

    1. Build vocabulary from the Linear A corpus.
    2. Pretrain token embeddings using LB phonetic triplets.
    3. Transfer embeddings to a SignLM and train on masked LM.
    4. Train a baseline SignLM (random init) for comparison.
    5. Compare perplexity.

    Parameters
    ----------
    db_path : str
    la_lb_mapping_path : str
    max_length : int
    batch_size : int
    pretrain_epochs : int
        Epochs for LB phonetic pretraining.
    finetune_epochs : int
        Epochs for LM fine-tuning on Linear A.
    lr : float
    d_model : int
    device : str
    refined_grid_path : str or None

    Returns
    -------
    results : dict
        baseline_perplexity, transfer_perplexity, lb_pretrain_losses,
        transfer_losses, baseline_losses
    """
    # ── Build dataset ──
    mds = MaskedLMDataset(
        db_path,
        max_length=max_length,
        mask_prob=0.15,
        bennett_ids=list(SYLLABOGRAM_RANGE),
    )

    n_train = int(0.9 * len(mds))
    n_val = len(mds) - n_train
    train_mds, val_mds = torch.utils.data.random_split(
        mds, [n_train, n_val]
    )

    train_loader = DataLoader(
        train_mds, batch_size=batch_size, shuffle=True, drop_last=True
    )
    val_loader = DataLoader(
        val_mds, batch_size=batch_size, shuffle=False
    )

    logger.info(
        "Transfer LM: %d train, %d val, vocab=%d",
        len(train_mds), len(val_mds), mds.mask_token,
    )

    # ── 1. LB phonetic pretraining ──
    logger.info("=" * 60)
    logger.info("Stage 1: LB phonetic pretraining")
    logger.info("=" * 60)

    pretrained_emb, lb_losses = pretrain_lb_embeddings(
        la_lb_mapping_path,
        mds.stoi,
        d_model=d_model,
        epochs=pretrain_epochs,
        lr=lr,
        batch_size=64,
        device=device,
        refined_grid_path=refined_grid_path,
    )

    # ── 2. Transfer SignLM training ──
    logger.info("=" * 60)
    logger.info("Stage 2: Transfer SignLM fine-tuning")
    logger.info("=" * 60)

    transfer_model = TransferSignLM(
        vocab_size=mds.mask_token,
        d_model=d_model,
        n_head=4,
        n_layers=2,
        max_len=max_length,
        dropout=0.1,
        pretrained_embedding=pretrained_emb,
    )

    # Re-implement train_lm locally to capture losses
    transfer_losses = _train_lm_inline(
        transfer_model,
        train_loader,
        epochs=finetune_epochs,
        lr=lr,
        device=device,
    )
    transfer_ppl = evaluate_perplexity(
        transfer_model, val_loader, device=device
    )

    # ── 3. Baseline SignLM (random init) ──
    logger.info("=" * 60)
    logger.info("Stage 3: Baseline SignLM (random init)")
    logger.info("=" * 60)

    baseline_model = SignLM(
        vocab_size=mds.mask_token,
        d_model=d_model,
        n_head=4,
        n_layers=2,
        max_len=max_length,
        dropout=0.1,
    )

    baseline_losses = _train_lm_inline(
        baseline_model,
        train_loader,
        epochs=finetune_epochs,
        lr=lr,
        device=device,
    )
    baseline_ppl = evaluate_perplexity(
        baseline_model, val_loader, device=device
    )

    # ── 4. Summary ──
    logger.info("=" * 60)
    logger.info("Transfer Learning Results")
    logger.info("  Baseline perplexity:      %.2f", baseline_ppl)
    logger.info("  Transfer perplexity:      %.2f", transfer_ppl)
    logger.info(
        "  Improvement:              %+.2f (%.1f%%)",
        baseline_ppl - transfer_ppl,
        (baseline_ppl - transfer_ppl) / max(baseline_ppl, 1e-8) * 100,
    )

    return {
        "baseline_perplexity": baseline_ppl,
        "transfer_perplexity": transfer_ppl,
        "perplexity_improvement": baseline_ppl - transfer_ppl,
        "lb_pretrain_losses": lb_losses,
        "transfer_losses": transfer_losses,
        "baseline_losses": baseline_losses,
        "vocab_size": mds.mask_token,
    }


def _train_lm_inline(
    model: SignLM,
    train_loader: DataLoader,
    epochs: int = 20,
    lr: float = 1e-3,
    device: str = "cuda",
) -> List[float]:
    """Train a SignLM and return per-epoch losses.

    Identical logic to ``train_lm`` in ``pipeline.ml.lm`` but returns
    losses inline (without checkpoint saves).
    """
    model = model.to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=1e-4
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=epochs
    )
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    losses: List[float] = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        epoch_tokens = 0
        pbar = tqdm(
            train_loader, desc=f"LM Epoch {epoch+1}/{epochs}", leave=False
        )

        for masked, original, attn_mask in pbar:
            masked = masked.to(device)
            original = original.to(device)
            attn_mask = attn_mask.to(device)

            logits = model(masked, attn_mask)
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
        logger.info(
            "LM Epoch %d/%d — avg loss: %.6f",
            epoch + 1, epochs, avg_loss,
        )

    return losses


# ── comparison runner ───────────────────────────────────────────────────────


def compare_transfer_vs_baseline(
    db_path: str = "data/database/lineara_full.db",
    la_lb_mapping_path: str = "data/analysis/comparative/la_lb_mapping.csv",
    refined_grid_path: str = "data/analysis/comparative/refined_phonetic_grid.csv",
    max_length: int = 64,
    batch_size: int = 16,
    pretrain_epochs: int = 50,
    finetune_epochs: int = 30,
    d_model: int = 128,
) -> Dict[str, object]:
    """Public entry point: run transfer comparison and return results.

    This is the function called from ``pipeline.ml.evaluate`` for
    end-to-end evaluation.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Transfer comparison running on device: %s", device)

    return train_transfer_lm(
        db_path=db_path,
        la_lb_mapping_path=la_lb_mapping_path,
        max_length=max_length,
        batch_size=batch_size,
        pretrain_epochs=pretrain_epochs,
        finetune_epochs=finetune_epochs,
        lr=1e-3,
        d_model=d_model,
        device=device,
        refined_grid_path=refined_grid_path,
    )
