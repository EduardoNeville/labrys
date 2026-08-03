"""Evaluation harness for Phase 4 ML baseline models.

Runs a complete train + eval cycle for:
1. Phonetic classifier (predicts CONFIRMED phonetic classes from context)
2. Masked language model baseline

Evaluates on the 44 CONFIRMED signs and produces loss curves + saved
model artifacts in ``data/analysis/ml/``.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from torch.utils.data import DataLoader, random_split

from pipeline.ml.data import (
    ContrastiveSignDataset,
    MaskedLMDataset,
    SYLLABOGRAM_RANGE,
)
from pipeline.ml.contrastive import (
    PhoneticClassifier,
    SignContextEncoder,
    extract_embeddings,
    train_phonetic_classifier,
    _load_phonetic_classes,
)
from pipeline.ml.lm import SignLM, train_lm, evaluate_perplexity

logger = logging.getLogger(__name__)

ML_DATA_DIR = Path("data/analysis/ml")


def ensure_output_dir(path: Optional[str] = None) -> Path:
    out = Path(path) if path else ML_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── phonetic classifier evaluation ───────────────────────────────────────────


def evaluate_embedding_separation(
    model: PhoneticClassifier,
    bennett_to_class: Dict[str, int],
    stoi: Dict[str, int],
    device: str = "cuda",
) -> Dict[str, float]:
    """Measure cluster separation of CONFIRMED sign token embeddings.

    Computes intra/inter-class cosine similarity and 1-NN accuracy.
    """
    confirmed_bids = [bid for bid, cls in bennett_to_class.items() if cls >= 0]
    if len(confirmed_bids) < 2:
        logger.warning("< 2 CONFIRMED signs — skipping eval")
        return {"intra_sim": 0.0, "inter_sim": 0.0, "ratio": 1.0, "nn_acc": 0.0}

    emb, bids = extract_embeddings(model, confirmed_bids, stoi, device=device)
    emb = emb.to(device)

    # Rebuild class mapping for the extracted subset
    classes = torch.tensor([bennett_to_class[b] for b in bids], device=device)
    unique_classes = torch.unique(classes)

    intra_sims = []
    for c in unique_classes:
        mask = classes == c
        if mask.sum() < 2:
            continue
        c_emb = emb[mask]
        sim = (c_emb @ c_emb.T).fill_diagonal_(0.0)
        n = mask.sum().item()
        intra_sims.append(sim.sum().item() / (n * (n - 1)))

    inter_sims = []
    for i, c1 in enumerate(unique_classes):
        for c2 in unique_classes[i + 1:]:
            sim = emb[classes == c1] @ emb[classes == c2].T
            inter_sims.append(sim.mean().item())

    intra = sum(intra_sims) / max(len(intra_sims), 1) if intra_sims else 0.0
    inter = sum(inter_sims) / max(len(inter_sims), 1) if inter_sims else 0.0
    ratio = intra / inter if inter > 0 else 1.0

    # 1-NN accuracy
    all_sim = emb @ emb.T
    all_sim.fill_diagonal_(float("-inf"))
    pred_idx = all_sim.argmax(dim=-1)
    nn_acc = (classes[pred_idx] == classes).float().mean().item()

    logger.info(
        "Embedding — intra: %.4f, inter: %.4f, ratio: %.2f, nn_acc: %.2f%%",
        intra, inter, ratio, nn_acc * 100,
    )
    return {"intra_sim": intra, "inter_sim": inter, "ratio": ratio, "nn_acc": nn_acc}


# ── end-to-end run ───────────────────────────────────────────────────────────


def run_baselines(
    db_path: str = "data/database/lineara_full.db",
    la_lb_mapping_path: str = "data/analysis/comparative/la_lb_mapping.csv",
    refined_grid_path: str = "data/analysis/comparative/refined_phonetic_grid.csv",
    output_dir: Optional[str] = None,
    max_length: int = 64,
    batch_size: int = 16,
    epochs: int = 20,
    lr: float = 1e-3,
    d_model: int = 128,
    device: str = "cuda",
) -> Dict[str, object]:
    """Train and evaluate both baseline models."""
    out = ensure_output_dir(output_dir)
    logger.info("Phase 4 baseline run → %s", out)

    bennett_to_class, class_to_phoneme, _ = _load_phonetic_classes(
        refined_grid_path, coarse=True
    )

    syll_ids = list(SYLLABOGRAM_RANGE)

    # ── 1. Phonetic classifier ──
    logger.info("=" * 60)
    logger.info("Training PHONETIC CLASSIFIER")
    logger.info("=" * 60)

    cds = ContrastiveSignDataset(
        db_path,
        la_lb_mapping_path,
        max_length=max_length,
        bennett_ids=syll_ids,
    )

    n_train = int(0.9 * len(cds))
    n_val = len(cds) - n_train
    train_cds, _ = random_split(cds, [n_train, n_val])

    train_loader = DataLoader(
        train_cds, batch_size=batch_size, shuffle=True, drop_last=True
    )

    model = PhoneticClassifier(
        vocab_size=len(cds.stoi),
        num_classes=len(class_to_phoneme),
        d_model=d_model,
        n_head=4,
        n_layers=2,
        dropout=0.1,
    )

    classifier_losses = train_phonetic_classifier(
        model,
        train_loader,
        bennett_to_class,
        cds.stoi,
        cds.itos,
        epochs=epochs,
        lr=lr,
        device=device,
        output_dir=str(out),
    )

    sep = evaluate_embedding_separation(
        model, bennett_to_class, cds.stoi, device=device
    )

    # Save final embeddings
    all_syll = list(SYLLABOGRAM_RANGE)
    final_emb, final_bids = extract_embeddings(model, all_syll, cds.stoi, device=device)
    emb_path = out / "classifier_embeddings.pt"
    torch.save(
        {
            "embeddings": final_emb,
            "bennett_ids": final_bids,
            "stoi": cds.stoi,
            "itos": cds.itos,
            "bennett_to_class": bennett_to_class,
            "class_to_phoneme": class_to_phoneme,
        },
        emb_path,
    )
    logger.info("Saved embeddings → %s", emb_path)

    # ── 2. Masked LM ──
    logger.info("=" * 60)
    logger.info("Training MASKED LANGUAGE MODEL")
    logger.info("=" * 60)

    mds = MaskedLMDataset(
        db_path,
        max_length=max_length,
        mask_prob=0.15,
        bennett_ids=syll_ids,
    )

    n_train_lm = int(0.9 * len(mds))
    n_val_lm = len(mds) - n_train_lm
    train_mds, val_mds = random_split(mds, [n_train_lm, n_val_lm])

    train_lm_loader = DataLoader(
        train_mds, batch_size=batch_size, shuffle=True, drop_last=True
    )
    val_lm_loader = DataLoader(val_mds, batch_size=batch_size, shuffle=False)

    lm_model = SignLM(
        vocab_size=mds.mask_token,
        d_model=d_model,
        n_head=4,
        n_layers=2,
        max_len=max_length,
        dropout=0.1,
    )

    lm_losses = train_lm(
        lm_model,
        train_lm_loader,
        epochs=epochs,
        lr=lr,
        device=device,
        output_dir=str(out),
    )

    ppl = evaluate_perplexity(lm_model, val_lm_loader, device=device)

    # ── 3. Plot loss curves ──
    plot_loss_curves(
        classifier_losses, lm_losses, output_path=str(out / "loss_curves.png")
    )

    # ── 4. Summary ──
    results = {
        "classifier_losses": classifier_losses,
        "classifier_final_loss": classifier_losses[-1] if classifier_losses else None,
        "embedding_intra_sim": sep["intra_sim"],
        "embedding_inter_sim": sep["inter_sim"],
        "embedding_ratio": sep["ratio"],
        "embedding_nn_acc": sep["nn_acc"],
        "lm_losses": lm_losses,
        "lm_final_loss": lm_losses[-1] if lm_losses else None,
        "lm_perplexity": ppl,
        "num_phonetic_classes": len(class_to_phoneme),
        "output_dir": str(out),
    }

    summary_path = out / "baseline_summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in results.items():
            if k.endswith("_losses"):
                continue
            writer.writerow([k, v])

    logger.info("Summary → %s", summary_path)
    return results


def plot_loss_curves(
    classifier_losses: List[float],
    lm_losses: List[float],
    output_path: str,
) -> None:
    """Plot loss curves for both models."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    if classifier_losses:
        epochs = list(range(1, len(classifier_losses) + 1))
        ax1.plot(epochs, classifier_losses, "b-o", markersize=4, linewidth=1.5)
        ax1.set_title("Phonetic Classifier (Cross-Entropy)")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Loss (per confirmed sign)")
        ax1.grid(True, alpha=0.3)

    if lm_losses:
        epochs = list(range(1, len(lm_losses) + 1))
        ax2.plot(epochs, lm_losses, "r-o", markersize=4, linewidth=1.5)
        ax2.set_title("Masked Language Model")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Cross-Entropy Loss (per token)")
        ax2.grid(True, alpha=0.3)

    fig.suptitle("Phase 4 — Linear A ML Baseline Loss Curves", fontsize=13)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    logger.info("Loss curves → %s", output_path)


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Using device: %s", device)

    results = run_baselines(
        db_path=sys.argv[1] if len(sys.argv) > 1 else "data/database/lineara_full.db",
        epochs=int(sys.argv[2]) if len(sys.argv) > 2 else 20,
        device=device,
    )

    print("\n" + "=" * 60)
    print("  Phase 4 Baseline Results")
    print("=" * 60)
    print(f"  Phonetic classes:           {results['num_phonetic_classes']}")
    print(f"  Classifier final loss:      {results['classifier_final_loss']:.6f}")
    print(f"  Embedding intra-sim:        {results['embedding_intra_sim']:.4f}")
    print(f"  Embedding inter-sim:        {results['embedding_inter_sim']:.4f}")
    print(f"  Embedding ratio:            {results['embedding_ratio']:.2f}")
    print(f"  Embedding NN accuracy:      {results['embedding_nn_acc']:.2%}")
    print(f"  LM final loss:              {results['lm_final_loss']:.6f}")
    print(f"  LM perplexity:              {results['lm_perplexity']:.2f}")
    print(f"  Output:                     {results['output_dir']}")
