#!/bin/sh
# Bootstrap a fresh clone into a state where every guard passes.
#
#   ./tools/bootstrap.sh
#
# Why this exists: two of the fourteen guards failed on a fresh clone in the 2026-10-19
# audit, and the reason was *not* a defect — the Linear B sandbox database is gitignored
# (it is 9.7 MB and rebuildable) and nobody had written down that the guards need it.
# A reproducibility gap that looks like a failure is worse than either.
#
# Steps, all idempotent:
#   1. uv sync                       (deps; add --extra ml for the Phase 4 ML stack)
#   2. rebuild the Linear B sandbox  (pipeline/lb_ingest.py, gate: coverage > 0.95)
#   3. rebuild the canonical grid    (pipeline/purge_grid.py --check, must be identical)
#   4. run the guards                (pipeline/guards.py, must be 15/15)
#
# The Python version is pinned in .python-version and pyproject.toml, because `uv run`
# once picked CPython 3.14 on this machine and deleted the venv trying to build a
# cu121 torch wheel that has no 3.14 build. Do not widen requires-python without
# testing that install path.

set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PY="$(cat .python-version 2>/dev/null || echo 3.12)"
echo "== bootstrap: repo=$REPO python=$PY"

case "${1:-}" in
  --extra-ml) EXTRA="--extra ml" ;;
  *)          EXTRA="" ;;
esac

echo "== 1/4 uv sync $EXTRA"
uv sync $EXTRA

echo "== 2/4 Linear B sandbox ingest (gitignored DB, rebuilt from tablets.csv)"
uv run python pipeline/lb_ingest.py | tail -3

echo "== 3/4 canonical grid re-derivation"
uv run python pipeline/purge_grid.py --check

echo "== 4/4 guards"
uv run python pipeline/guards.py
