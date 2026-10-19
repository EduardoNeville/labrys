"""`legacy/` — code kept because deleting it would delete the reasoning.

Everything here was **used once and is no longer helpful for new work**: a concluded avenue
whose negative is already recorded, or an implementation superseded by a better one. It is
importable (`legacy.ml.data`, `legacy.eteocretan.corpus`, …) so that re-running an old check
is still possible, and nothing under `pipeline/` imports any of it — `pipeline/guards.py`
enforces that.

Three rules, same as `archive/`:

1. **Nothing here is a result.** A number is only citable from
   `data/analysis/ventris/verification_audit.md` and the artifact it names.
2. **Do not extend it.** A concluded avenue stays concluded. If a new method is wanted,
   write it in `pipeline/` and let it pass the guards.
3. **Move it back only with a plan.** `legacy/ml/` in particular: restarting Phase 4 begins
   with the grid re-derivation (`CODE_AUDIT.md` §8 item 1), not with a training run.

Old-path → new-path map for every move is in `../CLEANUP_PLAN.md`, and the state of each
module (CORE / INSTRUMENT / RECORD / STALE) is in `../CODE_AUDIT.md`.
"""
