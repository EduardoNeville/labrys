#!/bin/sh
# Tier 1: the daily overseer. A cheap model reads what the deterministic loop recorded and reports.
#
#   ./tools/rsi_overseer.sh                 # one review, pinned model + thinking level
#   RSI_OVERSEER_MODEL=... ./tools/rsi_overseer.sh
#
# Design constraints, each from a measured lesson:
#   * the model is PINNED (model + thinking level), because an overseer whose judgement drifts is not
#     an overseer (INVARIANT 2 in spirit: the improver stays fixed);
#   * the agent is treated as UNTRUSTED: the frozen evaluator files are hashed before and after, and
#     any modification is reverted and reported. pi's flags do not offer per-path read-only, so the
#     guarantee is enforced here rather than requested in the prompt;
#   * the digest is precomputed, so the model does not roam the repository burning tokens on a free
#     tier and inventing context;
#   * the report is written by THIS script from the model's stdout, so the agent never needs write
#     access to produce its one artifact.

set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
# cron's environment is minimal: uv is in ~/.local/bin, pi in ~/.bun/bin (a bun global), and pi is a
# bundle run by node, so node's dir is needed too.
PATH="$HOME/.bun/bin:$HOME/.local/bin:$HOME/.nvm/versions/node/v24.21.0/bin:/usr/local/bin:/usr/bin:/bin"
export PATH
command -v pi >/dev/null || { echo "tools/rsi_overseer.sh: pi not on PATH" >&2; exit 3; }
cd "$REPO"

MODEL="${RSI_OVERSEER_MODEL:-space-bunny-free}"
THINKING="${RSI_OVERSEER_THINKING:-max}"
OUT="$REPO/data/analysis/rsi/overseer/$(date +%F-%H%M).md"
LOG="$REPO/data/analysis/rsi/overseer_log.jsonl"
mkdir -p "$(dirname "$OUT")"

# The frozen set: the evaluator and the answer key. Nothing may touch these.
FROZEN="languages/linear-b/answer_key.csv
data/analysis/bootstrapping/expanded_grid_purged.csv
data/analysis/comparative/refined_phonetic_grid.csv
languages/linear-b/data/analysis/kober/triple_patterns.csv
languages/linear-b/data/analysis/frequency_constraints/constrained_candidates.csv
pipeline/ventris/complete.py
pipeline/lb_oracle.py"

hash_frozen() { echo "$FROZEN" | while read -r f; do [ -f "$f" ] && printf '%s  %s\n' \
  "$(sha1sum "$f" | cut -c1-40)" "$f"; done | sha1sum | cut -c1-40; }

DIGEST="$(mktemp)"
trap 'rm -f "$DIGEST"' EXIT
{
  echo "# Loops status"
  uv run python pipeline/rsi_loop.py --status 2>&1
  echo
  echo "# Guard suite"
  uv run python pipeline/guards.py 2>&1 | tail -25
  echo
  echo "# Recorded tree (id, class, primary metric, verdict, s_v)"
  uv run python - <<'PY' 2>&1
import sys
sys.path.insert(0, ".")
from pipeline.rsi_tree import load, primary_lift, value_of, TREE
t = load(TREE)
print(f"{len(t['nodes'])} nodes, root {t['root']}")
for n in t["nodes"]:
    try:
        lift = f"{primary_lift(n):.2f}"
    except AssertionError:
        lift = "n/a"
    print(f"  {n['id']:34s} {n['evidence_class']:15s} {lift:>5s}  "
          f"{n['verdict']:13s} s_v={value_of(t, n['id']):.2f}  {n.get('source','')[:46]}")
PY
  echo
  echo "# Last 40 lines of the loop log"
  tail -40 data/analysis/rsi/loop_log.jsonl 2>/dev/null || echo "(no log yet)"
} > "$DIGEST" 2>&1

BEFORE="$(hash_frozen)"
DIRTY_BEFORE="$(git status --porcelain)"

# Print mode: piped stdin and stdout make pi non-interactive; --no-session keeps runs independent.
set +e
{ cat tools/rsi_overseer_prompt.md; echo; cat "$DIGEST"; } \
  | pi --print --model "$MODEL" --thinking "$THINKING" --no-session > "$OUT.tmp" 2>"$OUT.err"
RC=$?
set -e
mv "$OUT.tmp" "$OUT" 2>/dev/null || : > "$OUT"
[ -s "$OUT" ] || { echo "overseer produced no output (rc=$RC)"; cat "$OUT.err" >&2; }

# ── the freeze check: an untrusted agent, a deterministic guarantee ──
AFTER="$(hash_frozen)"
VIOLATION=0
if [ "$BEFORE" != "$AFTER" ]; then
  VIOLATION=1
  {
    echo
    echo "## VIOLATION — frozen files modified by the overseer"
    git --no-pager diff --stat -- $(echo "$FROZEN" | tr '\n' ' ')
    echo
    echo "(the driver has reverted them; the run is still recorded as a violation)"
  } >> "$OUT"
  # shellcheck disable=SC2086
  git checkout -- $(echo "$FROZEN" | tr '\n' ' ')
fi

# Anything the agent touched beyond the frozen set is reported, not silently kept. Compared against
# the status BEFORE the run, so files that were already untracked (this script itself, before a
# commit) are not blamed on the model — and SQLite's WAL sidecars are excluded, because the
# driver's own read-only digest queries create them and they are not the agent's doing.
DIRTY_AFTER="$(git status --porcelain | grep -vE '^\?\? (data/analysis/rsi/overseer/|data/database/.*\.db-(shm|wal))' || true)"
NEW_DIRT="$(printf '%s\n' "$DIRTY_AFTER" | grep -vxF "$(printf '%s\n' "$DIRTY_BEFORE")" || true)"
if [ -n "$NEW_DIRT" ]; then
  {
    echo
    echo "## VIOLATION — files touched during the run, outside the frozen set"
    echo '```'
    echo "$NEW_DIRT"
    echo '```'
    echo "Review and revert manually; the driver only reverts the frozen set automatically."
  } >> "$OUT"
  VIOLATION=1
fi

printf '{"when":"%s","model":"%s","thinking":"%s","rc":%s,"violation":%s,"report":"%s"}\n' \
  "$(date -Iseconds)" "$MODEL" "$THINKING" "$RC" "$([ "$VIOLATION" = 1 ] && echo true || echo false)" \
  "${OUT#$REPO/}" >> "$LOG"
rm -f "$OUT.err"

if [ "$VIOLATION" = 1 ]; then
  echo "OVERSEER VIOLATION — see $OUT" >&2
  exit 2
fi
[ "$RC" = 0 ] || { echo "overseer exited $RC (report still written to $OUT)" >&2; exit "$RC"; }
echo "overseer report: $OUT"
