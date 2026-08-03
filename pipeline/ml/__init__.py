"""Phase 4 — ML-based Linear A Decipherment.

This package provides dataset classes and models for learning sign
representations from the Linear A corpus, leveraging Linear B cognate
transfer, positional signals, and structural constraints from Phases 1–5.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from pipeline.ml.data import (
    ContrastiveSignDataset,
    LinearASignDataset,
    MaskedLMDataset,
    PAD_IDX,
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
from pipeline.ml.evaluate import run_baselines, plot_loss_curves
from pipeline.ml.augment import (
    AugmentedSequenceDataset,
    CurriculumDataset,
    create_augmented_loader,
    curriculum_sorted_sequences,
    reverse_sequence,
    sign_substitution,
    window_crop,
)
from pipeline.ml.transfer import (
    LBPhoneticPretrainer,
    TransferSignLM,
    compare_transfer_vs_baseline,
    pretrain_lb_embeddings,
    train_transfer_lm,
)
from pipeline.ml.constraints import (
    CMConstraintTarget,
    LoanwordAnchorTarget,
    compute_constraint_loss,
    compute_cm_constraint_loss,
    compute_loanword_anchor_loss,
    constraint_summary,
    create_constraint_target_tensors,
    get_cm_target_for_sign,
    get_lw_target_for_sign,
    load_cm_constraint_targets,
    load_loanword_anchor_targets,
)
from pipeline.ml.multitask import (
    MultiTaskDataset,
    MultiTaskLoss,
    MultiTaskTransformer,
    compare_multitask_vs_singletask,
    evaluate_logogram_accuracy,
    evaluate_multitask,
    evaluate_perplexity_multitask,
    evaluate_phonetic_nn_accuracy,
    train_multitask,
)

__all__ = [
    "AugmentedSequenceDataset",
    "CMConstraintTarget",
    "compare_multitask_vs_singletask",
    "compare_transfer_vs_baseline",
    "compute_constraint_loss",
    "compute_cm_constraint_loss",
    "compute_loanword_anchor_loss",
    "constraint_summary",
    "ContrastiveSignDataset",
    "create_augmented_loader",
    "create_constraint_target_tensors",
    "CurriculumDataset",
    "curriculum_sorted_sequences",
    "evaluate_logogram_accuracy",
    "evaluate_multitask",
    "evaluate_perplexity",
    "evaluate_perplexity_multitask",
    "evaluate_phonetic_nn_accuracy",
    "extract_embeddings",
    "get_cm_target_for_sign",
    "get_lw_target_for_sign",
    "LBPhoneticPretrainer",
    "LinearASignDataset",
    "load_cm_constraint_targets",
    "load_loanword_anchor_targets",
    "LoanwordAnchorTarget",
    "MaskedLMDataset",
    "MultiTaskDataset",
    "MultiTaskLoss",
    "MultiTaskTransformer",
    "PAD_IDX",
    "PhoneticClassifier",
    "plot_loss_curves",
    "pretrain_lb_embeddings",
    "reverse_sequence",
    "run_baselines",
    "SignContextEncoder",
    "SignLM",
    "sign_substitution",
    "SYLLABOGRAM_RANGE",
    "train_lm",
    "train_multitask",
    "train_phonetic_classifier",
    "train_transfer_lm",
    "TransferSignLM",
    "window_crop",
]
