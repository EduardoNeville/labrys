"""pipeline/phylogenetic — Phylogenetic multi-script sign evolution model.

Phase 7, Approach 3: Model sign form and value evolution across the
attested descent chain:
    Linear A (Minoan) → Linear B (Mycenaean Greek) → Cypro-Minoan →
    Cypriot syllabary (Classical Cypriot Greek).

For UNCERTAIN signs with conflicting LB/CM evidence, enumerate possible
values and score by visual continuity, phonetic naturalness, grid
position, and attestation evidence.
"""

from .alignment import build_alignment, save_alignment_matrix
from .resolve_conflicts import resolve_conflicts, save_conflict_resolutions

__all__ = [
    "build_alignment",
    "save_alignment_matrix",
    "resolve_conflicts",
    "save_conflict_resolutions",
]
