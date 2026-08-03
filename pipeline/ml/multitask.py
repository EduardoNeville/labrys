"""Multi-task transformer for Linear A sign sequences.

Shared encoder learns representations useful for three tasks:
1. Masked language modelling (MLM) — predicting masked signs from context
2. Phonetic classification — coarse 4-class + fine 36-class from context
3. Logogram semantics — predicting commodity cluster from context

Uses Kendall et al. (2018) uncertainty weighting for the multi-task loss
with support for manual coefficient overrides.
"""

from __future__ import annotations

import csv
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, random_split
from tqdm import tqdm

from pipeline.ml.data import PAD_IDX, _build_vocab, _load_sequences

logger = logging.getLogger(__name__)

IGNORE_IDX = -100


# ═══════════════════════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _load_phonetic_classes_both(
    refined_grid_path: str,
) -> Tuple[Dict[str, int], Dict[str, int], Dict[int, str], Dict[int, str], int, int]:
    """Parse refined_phonetic_grid.csv → coarse + fine label mappings.

    Returns
    -------
    bennett_to_coarse : dict  {bennett_id → 0..3 or -1}
    bennett_to_fine   : dict  {bennett_id → 0..35 or -1}
    class_to_coarse   : dict  {coarse_id → category name}
    class_to_fine     : dict  {fine_id → phonetic value}
    num_coarse        : int   (4)
    num_fine          : int   (36)
    """
    # Phonological categories (same as contrastive.py)
    _PHONEME_TO_COARSE: Dict[str, int] = {
        "a": 0, "i": 0, "o": 0, "u": 0,
        "pa": 1, "pi": 1, "me": 1, "mi": 1, "mo": 1, "wa": 1, "wi": 1,
        "te": 2, "ti": 2, "to": 2, "tu": 2,
        "na": 2, "ne": 2, "ni": 2, "nu": 2,
        "sa": 2, "se": 2, "si": 2, "so": 2,
        "za": 2, "ze": 2, "zo": 2,
        "re": 2, "ri": 2, "ru": 2, "la": 2,
        "ja": 3, "ka": 3, "ke": 3, "ki": 3, "ko": 3, "ku": 3,
    }
    _COARSE_NAMES = {0: "vowel", 1: "labial", 2: "dental/coronal", 3: "velar/palatal"}

    confirmed_values: Dict[str, str] = {}
    with open(refined_grid_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("bennett_id", "").strip()
            val = (row.get("refined_value") or "").strip()
            dec = (row.get("decision") or "").strip()
            if not bid:
                continue
            if dec == "CONFIRM" and val and val != "?":
                confirmed_values[bid] = val

    # Fine: one class per unique value
    unique_vals = sorted(set(confirmed_values.values()))
    val_to_fine = {v: i for i, v in enumerate(unique_vals)}
    bennett_to_fine: Dict[str, int] = {}
    for bid, val in confirmed_values.items():
        bennett_to_fine[bid] = val_to_fine[val]

    # Coarse: map through phoneme → category
    bennett_to_coarse: Dict[str, int] = {}
    for bid, val in confirmed_values.items():
        coarse_id = _PHONEME_TO_COARSE.get(val, -1)
        if coarse_id >= 0:
            bennett_to_coarse[bid] = coarse_id

    num_fine = len(unique_vals)
    num_coarse = len(_COARSE_NAMES)
    class_to_fine = {i: v for v, i in val_to_fine.items()}
    class_to_coarse = _COARSE_NAMES.copy()

    logger.info(
        "Phonetic labels: %d CONFIRMED signs → %d fine classes, %d coarse",
        len(confirmed_values), num_fine, num_coarse,
    )
    return (
        bennett_to_coarse, bennett_to_fine,
        class_to_coarse, class_to_fine,
        num_coarse, num_fine,
    )


def _load_logogram_clusters(csv_path: str) -> Tuple[Dict[str, int], int]:
    """Parse commodity_ontology.csv → {bennett_id: coarse cluster label}.

    Uses a 3-way coarse grouping based on the logogram ID prefix:
      0  = VASE variants (commodity vessels)
      1  = A 5xx (supplementary / metrical logograms)
      2  = A 3xx–A 4xx (standard GORILA commodity logograms)

    Returns (bennett_to_cluster, num_clusters).
    """
    bennett_to_cluster: Dict[str, int] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row.get("logogram_id", "").strip()
            if not bid:
                continue
            if bid.startswith("VASE"):
                bennett_to_cluster[bid] = 0
            elif bid.startswith("A 5"):
                bennett_to_cluster[bid] = 1
            else:
                bennett_to_cluster[bid] = 2

    num_clusters = 3
    logger.info(
        "Logogram coarse clusters: %d logograms → %d clusters",
        len(bennett_to_cluster), num_clusters,
    )
    return bennett_to_cluster, num_clusters


# ═══════════════════════════════════════════════════════════════════════════════
# dataset
# ═══════════════════════════════════════════════════════════════════════════════

class MultiTaskDataset(Dataset):
    """Dataset producing per‑position labels for MLM, phonetic, and logogram tasks.

    Each sample is one inscription padded / truncated to ``max_length``.
    Returns:
        input_ids, attention_mask, lm_labels,
        ph_coarse_labels, ph_fine_labels, logogram_labels

    Parameters
    ----------
    db_path : str
        Path to ``lineara_full.db``.
    refined_grid_path : str
        Path to ``refined_phonetic_grid.csv``.
    logogram_cluster_path : str
        Path to ``commodity_ontology.csv``.
    max_length : int
        Pad / truncate sequences.
    mask_prob : float
        Fraction of non‑padding tokens to mask for MLM (default 0.15).
    """

    def __init__(
        self,
        db_path: str,
        refined_grid_path: str,
        logogram_cluster_path: str,
        max_length: int = 64,
        mask_prob: float = 0.15,
    ) -> None:
        self.max_length = max_length
        self.mask_prob = mask_prob
        self.stoi, self.itos = _build_vocab(db_path)
        self.sequences = _load_sequences(db_path, self.stoi)
        self.mask_token = len(self.stoi)  # conforms to SignLM convention

        # Phonetic label maps
        (
            self.bennett_to_coarse,
            self.bennett_to_fine,
            self.coarse_names,
            self.fine_names,
            self.num_coarse,
            self.num_fine,
        ) = _load_phonetic_classes_both(refined_grid_path)

        # Logogram cluster map
        self.bennett_to_cluster, self.num_logogram_clusters = (
            _load_logogram_clusters(logogram_cluster_path)
        )

        # Statistics
        n_phonetic = 0
        n_logogram = 0
        for seq, _ in self.sequences:
            for token_idx in seq:
                bid = self.itos.get(token_idx, "")
                if self.bennett_to_coarse.get(bid, -1) >= 0:
                    n_phonetic += 1
                if self.bennett_to_cluster.get(bid, -1) >= 0:
                    n_logogram += 1

        logger.info(
            "MultiTaskDataset: %d inscriptions, %d tokens (phonetic=%d, "
            "logogram=%d), vocab=%d, mask_token=%d",
            len(self.sequences),
            sum(len(s) for s, _ in self.sequences),
            n_phonetic, n_logogram,
            len(self.stoi), self.mask_token,
        )

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Tuple[
        torch.Tensor, torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor, torch.Tensor,
    ]:
        seq, _ = self.sequences[idx]
        n = min(len(seq), self.max_length)

        # Original token sequence (padded)
        original = torch.full((self.max_length,), PAD_IDX, dtype=torch.long)
        original[:n] = torch.tensor(seq[:n], dtype=torch.long)

        # Input starts as copy; we apply MLM masking below
        input_ids = original.clone()

        # Attention mask
        attn_mask = torch.zeros(self.max_length, dtype=torch.long)
        attn_mask[:n] = 1

        # Per‑position task labels (only valid positions get real labels)
        ph_coarse_labels = torch.full((self.max_length,), IGNORE_IDX, dtype=torch.long)
        ph_fine_labels = torch.full((self.max_length,), IGNORE_IDX, dtype=torch.long)
        logogram_labels = torch.full((self.max_length,), IGNORE_IDX, dtype=torch.long)

        for i in range(n):
            bid = self.itos.get(seq[i], "")
            pc = self.bennett_to_coarse.get(bid, -1)
            pf = self.bennett_to_fine.get(bid, -1)
            lc = self.bennett_to_cluster.get(bid, -1)
            if pc >= 0:
                ph_coarse_labels[i] = pc
            if pf >= 0:
                ph_fine_labels[i] = pf
            if lc >= 0:
                logogram_labels[i] = lc

        # MLM masking: 15 % of non‑padding tokens
        n_mask = max(1, int(n * self.mask_prob))
        positions = torch.randperm(n)[:n_mask]

        lm_labels = torch.full((self.max_length,), IGNORE_IDX, dtype=torch.long)

        for pos in positions:
            lm_labels[pos] = original[pos]  # original token is the target
            prob = torch.rand(1).item()
            if prob < 0.8:
                input_ids[pos] = self.mask_token
            elif prob < 0.9:
                input_ids[pos] = torch.randint(
                    1, len(self.stoi), (1,), dtype=torch.long
                ).item()
            # else: 10 % unchanged, still a valid target

        return (
            input_ids, attn_mask, lm_labels,
            ph_coarse_labels, ph_fine_labels, logogram_labels,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# model
# ═══════════════════════════════════════════════════════════════════════════════

class MultiTaskTransformer(nn.Module):
    """Shared transformer encoder with per‑task prediction heads.

    Parameters
    ----------
    vocab_size : int
        Number of entries in ``stoi`` (incl. PAD).  The embedding table
        gets ``vocab_size + 1`` rows to accommodate the MASK token
        (consistent with ``SignLM``).
    num_logogram_classes : int
        Number of logogram cluster classes.
    d_model : int
        Hidden dimension (default 128).
    n_head : int
        Attention heads (default 4).
    n_layers : int
        Transformer layers (default 2).
    max_len : int
        Maximum sequence length for positional embedding (default 128).
    dropout : float
        Dropout rate (default 0.1).
    """

    def __init__(
        self,
        vocab_size: int,
        num_logogram_classes: int,
        d_model: int = 128,
        n_head: int = 4,
        n_layers: int = 2,
        max_len: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_logogram_classes = num_logogram_classes

        # Embedding: PAD=0 … real tokens 1..vocab_size-1, MASK=vocab_size
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
        self.norm = nn.LayerNorm(d_model)

        # ── task heads ──
        # (a) Masked LM: predict original token at every position
        self.lm_head = nn.Linear(d_model, vocab_size)

        # (b) Phonetic — coarse (4 classes) + fine (36 classes)
        self.phonetic_coarse_head = nn.Linear(d_model, 4)
        self.phonetic_fine_head = nn.Linear(d_model, 36)

        # (c) Logogram semantics
        self.logogram_head = nn.Linear(d_model, num_logogram_classes)

        self._init_weights()

    def _init_weights(self) -> None:
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def encode(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Return per‑position hidden states ``(B, L, d_model)``."""
        B, L = input_ids.shape
        positions = torch.arange(L, device=input_ids.device).unsqueeze(0).expand(B, -1)

        tok_emb = self.token_embedding(input_ids) * math.sqrt(self.d_model)
        pos_emb = self.position_embedding(positions)
        x = self.dropout(tok_emb + pos_emb)

        pad_mask = attention_mask.eq(0)
        x = self.encoder(x, src_key_padding_mask=pad_mask)
        return self.norm(x)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        tasks: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, torch.Tensor]:
        """Return dictionary of logits for active tasks.

        Parameters
        ----------
        input_ids : (B, L)
        attention_mask : (B, L)
        tasks : dict or None
            e.g. ``{"lm": True, "phonetic": True, "logogram": False}``.
            ``None`` means all tasks active.

        Returns
        -------
        outputs : dict
            Keys: ``"lm"``, ``"phonetic_coarse"``, ``"phonetic_fine"``,
            ``"logogram"``.  Each value is ``(B, L, num_classes)``.
        """
        hidden = self.encode(input_ids, attention_mask)  # (B, L, d_model)

        outputs: Dict[str, torch.Tensor] = {}

        if tasks is None:
            tasks = {"lm": True, "phonetic": True, "logogram": True}

        if tasks.get("lm", True):
            outputs["lm"] = self.lm_head(hidden)

        if tasks.get("phonetic", True):
            outputs["phonetic_coarse"] = self.phonetic_coarse_head(hidden)
            outputs["phonetic_fine"] = self.phonetic_fine_head(hidden)

        if tasks.get("logogram", True):
            outputs["logogram"] = self.logogram_head(hidden)

        return outputs


# ═══════════════════════════════════════════════════════════════════════════════
# loss
# ═══════════════════════════════════════════════════════════════════════════════

class MultiTaskLoss(nn.Module):
    """Multi‑task loss with uncertainty weighting or manual coefficients.

    Parameters
    ----------
    tasks_active : dict
        e.g. ``{"lm": True, "phonetic": True, "logogram": False}``.
    manual_weights : dict or None
        If provided, use fixed coefficients (e.g. ``{"lm": 1.0, …}``).
        If ``None``, use learnable uncertainty weighting (Kendall et al.).
    """

    def __init__(
        self,
        tasks_active: Dict[str, bool],
        manual_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        super().__init__()
        self.tasks_active = tasks_active

        # Expand "phonetic" → ["phonetic_coarse", "phonetic_fine"]
        self._task_keys: List[str] = []
        if tasks_active.get("lm", False):
            self._task_keys.append("lm")
        if tasks_active.get("phonetic", False):
            self._task_keys.append("phonetic_coarse")
            self._task_keys.append("phonetic_fine")
        if tasks_active.get("logogram", False):
            self._task_keys.append("logogram")

        if manual_weights is not None:
            self.use_uncertainty = False
            self.weights = manual_weights
        else:
            self.use_uncertainty = True
            self.log_vars = nn.ParameterDict()
            for key in self._task_keys:
                self.log_vars[key] = nn.Parameter(torch.zeros(1))

    def extra_repr(self) -> str:
        if self.use_uncertainty:
            return f"uncertainty_weighting, tasks={list(self.log_vars.keys())}"
        return f"manual_weights={self.weights}"

    def forward(self, losses: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Return (total_loss, detached_per_task_losses).

        Handles missing task keys gracefully and skips NaN losses.
        """
        detached: Dict[str, float] = {}
        device = next(iter(losses.values())).device
        if self.use_uncertainty:
            total = torch.tensor(0.0, device=device)
            has_valid = False
            for task, loss in losses.items():
                if task not in self.log_vars:
                    total = total + loss
                    detached[task] = loss.detach().item()
                    has_valid = True
                    continue
                # Clamp log_vars for numerical stability (detach so grad still flows)
                log_var = torch.clamp(self.log_vars[task], min=-10.0, max=10.0)
                precision = torch.exp(-log_var)
                total = total + precision * loss + 0.5 * log_var
                detached[task] = loss.detach().item()
                has_valid = True
            if not has_valid:
                return total, detached  # will be 0 — skip in caller
            return total, detached
        else:
            total = torch.tensor(0.0, device=device)
            for task, loss in losses.items():
                w = self.weights.get(task, 1.0)
                total = total + w * loss
                detached[task] = loss.detach().item()
            return total, detached


# ═══════════════════════════════════════════════════════════════════════════════
# training
# ═══════════════════════════════════════════════════════════════════════════════

def train_multitask(
    model: MultiTaskTransformer,
    train_loader: DataLoader,
    tasks_active: Dict[str, bool],
    loss_module: MultiTaskLoss,
    epochs: int = 20,
    lr: float = 1e-3,
    device: str = "cuda",
    output_dir: Optional[str] = None,
) -> Tuple[List[float], List[Dict[str, float]]]:
    """Train the multi‑task model.

    Parameters
    ----------
    model : MultiTaskTransformer
    train_loader : DataLoader
        Yields ``(input_ids, attn_mask, lm_labels, ph_coarse, ph_fine, logo_labels)``.
    tasks_active : dict
    loss_module : MultiTaskLoss
    epochs : int
    lr : float
    device : str
    output_dir : str or None

    Returns
    -------
    total_losses : list[float]       per‑epoch total loss
    task_losses  : list[dict]        per‑epoch per‑task losses
    """
    model = model.to(device)
    loss_module = loss_module.to(device)

    # Collect all trainable params (model + loss log_vars)
    params = list(model.parameters())
    if loss_module.use_uncertainty:
        params += list(loss_module.log_vars.parameters())

    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    total_losses: List[float] = []
    task_losses: List[Dict[str, float]] = []

    loss_fn = nn.CrossEntropyLoss(ignore_index=IGNORE_IDX)

    for epoch in range(epochs):
        model.train()
        epoch_total = 0.0
        epoch_tasks: Dict[str, float] = {}
        epoch_steps = 0
        pbar = tqdm(train_loader, desc=f"MTL Epoch {epoch+1}/{epochs}")

        for batch in pbar:
            (
                input_ids, attn_mask, lm_labels,
                ph_coarse_labels, ph_fine_labels, logogram_labels,
            ) = [t.to(device) for t in batch]

            outputs = model(input_ids, attn_mask, tasks=tasks_active)

            losses: Dict[str, torch.Tensor] = {}

            if tasks_active.get("lm", False) and "lm" in outputs:
                losses["lm"] = loss_fn(
                    outputs["lm"].reshape(-1, model.vocab_size),
                    lm_labels.reshape(-1),
                )

            if tasks_active.get("phonetic", False):
                if "phonetic_coarse" in outputs:
                    n_phc = (ph_coarse_labels != IGNORE_IDX).sum().item()
                    if n_phc > 0:
                        losses["phonetic_coarse"] = loss_fn(
                            outputs["phonetic_coarse"].reshape(-1, 4),
                            ph_coarse_labels.reshape(-1),
                        )
                if "phonetic_fine" in outputs:
                    n_phf = (ph_fine_labels != IGNORE_IDX).sum().item()
                    if n_phf > 0:
                        losses["phonetic_fine"] = loss_fn(
                            outputs["phonetic_fine"].reshape(-1, 36),
                            ph_fine_labels.reshape(-1),
                        )

            if tasks_active.get("logogram", False) and "logogram" in outputs:
                n_logo_valid = (logogram_labels != IGNORE_IDX).sum().item()
                if n_logo_valid > 0:
                    # Label smoothing (0.1) for the 3-class logogram task to prevent extreme logits
                    losses["logogram"] = F.cross_entropy(
                        outputs["logogram"].reshape(-1, model.num_logogram_classes),
                        logogram_labels.reshape(-1),
                        ignore_index=IGNORE_IDX,
                        label_smoothing=0.1,
                    )

            if not losses:
                continue

            total, detached = loss_module(losses)

            # Skip batch if loss is NaN
            if torch.isnan(total) or torch.isinf(total):
                logger.warning("NaN/inf loss at epoch %d, step %d – skipping batch", epoch+1, epoch_steps)
                continue

            optimizer.zero_grad()
            total.backward()
            torch.nn.utils.clip_grad_norm_(params, max_norm=1.0)
            optimizer.step()

            epoch_total += total.detach().item()
            for k, v in detached.items():
                epoch_tasks[k] = epoch_tasks.get(k, 0.0) + v
            epoch_steps += 1

            postfix = {k: f"{v:.4f}" for k, v in detached.items()}
            postfix["total"] = f"{total.detach().item():.4f}"
            pbar.set_postfix(postfix)

        scheduler.step()

        avg_total = epoch_total / max(epoch_steps, 1)
        avg_tasks = {k: v / max(epoch_steps, 1) for k, v in epoch_tasks.items()}
        total_losses.append(avg_total)
        task_losses.append(avg_tasks)

        lr_now = optimizer.param_groups[0]["lr"]
        logger.info(
            "MTL Epoch %d/%d — total: %.6f, tasks: %s, lr: %.2e",
            epoch + 1, epochs, avg_total, avg_tasks, lr_now,
        )

        if loss_module.use_uncertainty:
            log_var_str = {
                t: f"{v.item():.4f}" for t, v in loss_module.log_vars.items()
            }
            logger.info("  log_vars: %s", log_var_str)

        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "loss_module_state_dict": loss_module.state_dict(),
                    "total_loss": avg_total,
                    "task_losses": avg_tasks,
                    "vocab_size": model.vocab_size,
                    "d_model": model.d_model,
                },
                out / f"multitask_epoch_{epoch+1:03d}.pt",
            )

    return total_losses, task_losses


# ═══════════════════════════════════════════════════════════════════════════════
# evaluation
# ═══════════════════════════════════════════════════════════════════════════════

@torch.no_grad()
def evaluate_perplexity_multitask(
    model: MultiTaskTransformer,
    eval_loader: DataLoader,
    device: str = "cuda",
) -> float:
    """Compute per‑token perplexity on the evaluation set.

    Masks 15 % of tokens (regardless of sign type) and measures how well
    the LM head predicts them.
    """
    model = model.to(device)
    model.eval()
    loss_fn = nn.CrossEntropyLoss(ignore_index=IGNORE_IDX, reduction="sum")
    total_loss = 0.0
    total_tokens = 0

    for batch in eval_loader:
        input_ids, attn_mask, lm_labels, *_ = [t.to(device) for t in batch]

        # Only use positions that have LM labels
        n_labels = (lm_labels != IGNORE_IDX).sum().item()
        if n_labels == 0:
            continue

        outputs = model(input_ids, attn_mask, tasks={"lm": True, "phonetic": False, "logogram": False})
        loss = loss_fn(
            outputs["lm"].reshape(-1, model.vocab_size),
            lm_labels.reshape(-1),
        )
        total_loss += loss.item()
        total_tokens += n_labels

    avg_loss = total_loss / max(total_tokens, 1)
    ppl = math.exp(avg_loss)
    logger.info("Multi‑task eval — loss: %.4f, perplexity: %.2f", avg_loss, ppl)
    return ppl


@torch.no_grad()
def evaluate_phonetic_nn_accuracy(
    model: MultiTaskTransformer,
    val_loader: DataLoader,
    bennett_to_class: Dict[str, int],
    stoi: Dict[str, int],
    device: str = "cuda",
) -> Tuple[float, int]:
    """Compute 1‑NN accuracy using contextualized encoder embeddings.

    Passes each inscription through the encoder and collects the hidden
    representation at every position with a CONFIRMED phonetic label.
    Then evaluates 1‑NN classification in that latent space.
    """
    model = model.to(device)
    model.eval()

    all_embeddings: List[torch.Tensor] = []
    all_labels: List[int] = []

    for batch in val_loader:
        input_ids, attn_mask, _, ph_coarse, _, _ = [t.to(device) for t in batch]

        B, L = input_ids.shape
        # Get hidden states from the encoder
        hidden = model.encode(input_ids, attn_mask)  # (B, L, d_model)

        # Collect positions with phonetic labels
        for b in range(B):
            for i in range(L):
                label = ph_coarse[b, i].item()
                if label != IGNORE_IDX:
                    all_embeddings.append(hidden[b, i].cpu())
                    all_labels.append(label)

    if len(all_labels) < 2:
        logger.warning("Insufficient phonetic labels for NN eval")
        return 0.0, 0

    emb = torch.stack(all_embeddings)
    emb = F.normalize(emb, p=2, dim=-1)
    labels_t = torch.tensor(all_labels)

    # 1‑NN
    sim = emb @ emb.T
    sim.fill_diagonal_(float("-inf"))
    pred_idx = sim.argmax(dim=-1)
    nn_acc = (labels_t[pred_idx] == labels_t).float().mean().item()

    logger.info("Multi‑task NN accuracy — %.2f%% (%d labels)", nn_acc * 100, len(all_labels))
    return nn_acc, len(all_labels)


@torch.no_grad()
def evaluate_logogram_accuracy(
    model: MultiTaskTransformer,
    eval_loader: DataLoader,
    device: str = "cuda",
) -> float:
    """Compute logogram cluster classification accuracy."""
    model = model.to(device)
    model.eval()

    correct = 0
    total = 0

    for batch in eval_loader:
        input_ids, attn_mask, _, _, _, logogram_labels = [
            t.to(device) for t in batch
        ]

        n_labels = (logogram_labels != IGNORE_IDX).sum().item()
        if n_labels == 0:
            continue

        outputs = model(
            input_ids, attn_mask,
            tasks={"lm": False, "phonetic": False, "logogram": True},
        )
        logits = outputs["logogram"]  # (B, L, num_clusters)

        # Gather only valid logogram positions
        mask = logogram_labels != IGNORE_IDX
        preds = logits[mask].argmax(dim=-1)
        targets = logogram_labels[mask]
        correct += (preds == targets).sum().item()
        total += n_labels

    acc = correct / max(total, 1)
    logger.info("Multi‑task logogram accuracy — %.2f%% (%d samples)", acc * 100, total)
    return acc


def evaluate_multitask(
    model: MultiTaskTransformer,
    eval_loader: DataLoader,
    bennett_to_class: Dict[str, int],
    stoi: Dict[str, int],
    device: str = "cuda",
) -> Dict[str, float]:
    """Run full multi‑task evaluation.

    Returns dict with keys: perplexity, nn_accuracy, logogram_accuracy.
    """
    ppl = evaluate_perplexity_multitask(model, eval_loader, device)
    nn_acc, _ = evaluate_phonetic_nn_accuracy(model, eval_loader, bennett_to_class, stoi, device)
    logogram_acc = evaluate_logogram_accuracy(model, eval_loader, device)

    return {
        "perplexity": ppl,
        "nn_accuracy": nn_acc,
        "logogram_accuracy": logogram_acc,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# comparison harness
# ═══════════════════════════════════════════════════════════════════════════════

def compare_multitask_vs_singletask(
    db_path: str = "data/database/lineara_full.db",
    refined_grid_path: str = "data/analysis/comparative/refined_phonetic_grid.csv",
    logogram_cluster_path: str = "data/analysis/logograms/commodity_ontology.csv",
    output_dir: Optional[str] = None,
    max_length: int = 64,
    batch_size: int = 16,
    epochs: int = 20,
    lr: float = 1e-3,
    d_model: int = 128,
    device: str = "cuda",
) -> Dict[str, Any]:
    """Train multi‑task and single‑task models; compare on held‑out data.

    Trains four variants on the same train/val split:
    1. Multi‑task (all three tasks)
    2. Single‑task LM
    3. Single‑task phonetic
    4. Single‑task logogram

    Returns comparison dict with metrics for each model.
    """
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
    else:
        out = Path("data/analysis/ml")
        out.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Multi‑task vs Single‑task Comparison")
    logger.info("=" * 60)

    # ── Build dataset ──
    ds = MultiTaskDataset(
        db_path, refined_grid_path, logogram_cluster_path,
        max_length=max_length, mask_prob=0.15,
    )

    # Train/val split at inscription level (90/10)
    n_train = int(0.9 * len(ds))
    n_val = len(ds) - n_train
    train_ds, val_ds = random_split(ds, [n_train, n_val])
    logger.info("Train: %d inscriptions, Val: %d", n_train, n_val)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
    )

    vocab_size = ds.mask_token  # = len(stoi)
    num_logogram = ds.num_logogram_clusters

    # For NN accuracy: use coarse phonetic classes from the dataset
    bennett_to_class = ds.bennett_to_coarse
    stoi = ds.stoi

    # Shared model factory
    def _make_model() -> MultiTaskTransformer:
        return MultiTaskTransformer(
            vocab_size=vocab_size,
            num_logogram_classes=num_logogram,
            d_model=d_model,
            n_head=4,
            n_layers=2,
            max_len=max_length,
            dropout=0.1,
        )

    results: Dict[str, Any] = {}

    # ── 1. Multi‑task ──
    logger.info("\n%s", "=" * 60)
    logger.info("  1/4  MULTI‑TASK MODEL  (lm + phonetic + logogram)")
    logger.info("%s", "=" * 60)

    mt_model = _make_model()
    mt_tasks = {"lm": True, "phonetic": True, "logogram": True}
    # Use manual weights to prevent uncertainty-weighting instability with sparse logogram labels
    mt_loss = MultiTaskLoss(mt_tasks, manual_weights={
        "lm": 1.0,
        "phonetic_coarse": 0.5,
        "phonetic_fine": 0.25,
        "logogram": 0.1,
    })

    train_multitask(
        mt_model, train_loader, mt_tasks, mt_loss,
        epochs=epochs, lr=lr, device=device,
        output_dir=str(out / "multitask"),
    )

    mt_metrics = evaluate_multitask(
        mt_model, val_loader, bennett_to_class, stoi, device=device,
    )
    logger.info("Multi‑task results: %s", mt_metrics)
    results["multitask"] = mt_metrics

    # ── 2. Single‑task LM ──
    logger.info("\n%s", "=" * 60)
    logger.info("  2/4  SINGLE‑TASK LM")
    logger.info("%s", "=" * 60)

    lm_model = _make_model()
    lm_tasks = {"lm": True, "phonetic": False, "logogram": False}
    lm_loss = MultiTaskLoss(lm_tasks)

    train_multitask(
        lm_model, train_loader, lm_tasks, lm_loss,
        epochs=epochs, lr=lr, device=device,
        output_dir=str(out / "singletask_lm"),
    )

    lm_metrics = evaluate_multitask(
        lm_model, val_loader, bennett_to_class, stoi, device=device,
    )
    logger.info("Single‑task LM results: %s", lm_metrics)
    results["singletask_lm"] = lm_metrics

    # ── 3. Single‑task phonetic ──
    logger.info("\n%s", "=" * 60)
    logger.info("  3/4  SINGLE‑TASK PHONETIC")
    logger.info("%s", "=" * 60)

    ph_model = _make_model()
    ph_tasks = {"lm": False, "phonetic": True, "logogram": False}
    ph_loss = MultiTaskLoss(ph_tasks)

    train_multitask(
        ph_model, train_loader, ph_tasks, ph_loss,
        epochs=epochs, lr=lr, device=device,
        output_dir=str(out / "singletask_phonetic"),
    )

    ph_metrics = evaluate_multitask(
        ph_model, val_loader, bennett_to_class, stoi, device=device,
    )
    logger.info("Single‑task phonetic results: %s", ph_metrics)
    results["singletask_phonetic"] = ph_metrics

    # ── 4. Single‑task logogram ──
    logger.info("\n%s", "=" * 60)
    logger.info("  4/4  SINGLE‑TASK LOGOGRAM")
    logger.info("%s", "=" * 60)

    logo_model = _make_model()
    logo_tasks = {"lm": False, "phonetic": False, "logogram": True}
    logo_loss = MultiTaskLoss(logo_tasks)

    train_multitask(
        logo_model, train_loader, logo_tasks, logo_loss,
        epochs=epochs, lr=lr, device=device,
        output_dir=str(out / "singletask_logogram"),
    )

    logo_metrics = evaluate_multitask(
        logo_model, val_loader, bennett_to_class, stoi, device=device,
    )
    logger.info("Single‑task logogram results: %s", logo_metrics)
    results["singletask_logogram"] = logo_metrics

    # ── Comparison summary ──
    logger.info("\n%s", "=" * 60)
    logger.info("  COMPARISON SUMMARY")
    logger.info("%s", "=" * 60)

    for metric, label in [
        ("perplexity", "Perplexity (↓)"),
        ("nn_accuracy", "NN Accuracy (↑)"),
        ("logogram_accuracy", "Logogram Acc (↑)"),
    ]:
        mt_val = results["multitask"][metric]
        st_val = {
            "perplexity": results["singletask_lm"]["perplexity"],
            "nn_accuracy": results["singletask_phonetic"]["nn_accuracy"],
            "logogram_accuracy": results["singletask_logogram"]["logogram_accuracy"],
        }[metric]
        better = "MTL ✓" if (
            (metric == "perplexity" and mt_val < st_val) or
            (metric != "perplexity" and mt_val > st_val)
        ) else "STL  "
        logger.info(
            "  %s :  MTL=%.4f  STL=%.4f  %s",
            label, mt_val, st_val, better,
        )

    # Count wins
    wins = 0
    if results["multitask"]["perplexity"] < results["singletask_lm"]["perplexity"]:
        wins += 1
    if results["multitask"]["nn_accuracy"] > results["singletask_phonetic"]["nn_accuracy"]:
        wins += 1
    if results["multitask"]["logogram_accuracy"] > results["singletask_logogram"]["logogram_accuracy"]:
        wins += 1

    results["multitask_wins"] = wins
    results["win_threshold_2_of_3"] = wins >= 2
    logger.info(
        "  MTL beats STL on %d/3 metrics — threshold met: %s",
        wins, wins >= 2,
    )

    # ── Save summary CSV ──
    import csv
    summary_path = out / "multitask_comparison.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "perplexity", "nn_accuracy", "logogram_accuracy"])
        for model_name in ["multitask", "singletask_lm", "singletask_phonetic", "singletask_logogram"]:
            writer.writerow([
                model_name,
                results[model_name].get("perplexity", ""),
                results[model_name].get("nn_accuracy", ""),
                results[model_name].get("logogram_accuracy", ""),
            ])
    logger.info("Summary → %s", summary_path)

    return results
