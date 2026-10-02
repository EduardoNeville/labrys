#!/bin/sh
# Driver for the Dream-RSI inner loop, for cron. See RSI_LOOP.md §6.
#
#   ./tools/rsi_loop.sh          # nightly: re-check every recorded number
#   ./tools/rsi_loop.sh full     # weekly: also the expensive stratified checks
#
# Cron gives a minimal environment, so PATH is set explicitly (uv lives in ~/.local/bin on this
# machine) and the log is written by this script rather than by cron's mail. The loop itself is
# LLM-free and cannot write to the evaluator, which is what makes this safe to schedule.

set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export PATH
cd "$REPO"

MODE="${1:-due}"
case "$MODE" in
  full) ARGS="--run 99 --force --include-expensive" ;;
  due)  ARGS="--run 99 --force" ;;
  *)    echo "usage: $0 [due|full]" >&2; exit 2 ;;
esac

LOG="${RSI_LOOP_LOG:-$REPO/data/analysis/rsi/loop_cron.log}"
mkdir -p "$(dirname "$LOG")"

# Keep the log bounded: a job that runs every night forever must not be a disk leak.
if [ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 5000000 ]; then
  tail -c 1000000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

{
  printf '\n===== %s  mode=%s =====\n' "$(date -Iseconds)" "$MODE"
  uv run python pipeline/rsi_loop.py $ARGS
} >> "$LOG" 2>&1

# Surface flags in the exit status, so cron's mail (or any wrapper) can notice drift.
grep -q '^\[FLAGGED\]' "$LOG" && exit 1
exit 0
