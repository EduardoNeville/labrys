"""Doc claims vs the corpus — the check that was missing.

Written 2026-10-19, after sign-ID slips were found in the project's only cross-site positive.
The libation documents had listed the opening as five signs where the corpus has six
(`AB 08 AB 59 AB 28 A 301 AB 54 AB 57` — A 301 was omitted), and slot 5 as `AB 28 54 06 80`
where the corpus reads `AB 28 AB 39 AB 06 AB 80` (i-pi-na-ma). Both wrong forms match **zero**
inscriptions. The live verifier (`rsi_loop.py:x_libation`) always had it right; nothing
compared the prose to the data, so the prose drifted.

Two claims are checked, both against `lineara_full.db`:

1. **Sign-ID sequences** — a run of >= 3 `AB nn` / `A nnn` tokens in a canonical document must
   occur somewhere in the corpus. Enumerations (comma-separated sign *lists*) are not sequences
   and are skipped.
2. **The retracted 5-sign opening** must not be asserted as a corpus reading. It may be quoted
   where it is marked as the wrong form (before/after tables, corrections notes).

A third check was attempted and **removed rather than kept as false comfort**: comparing the
libation catalog's hyphenated readings token-by-token. That document's `?` convention is lossy
in both directions — it means "no conventional value" *and* it silently absorbed the omitted
`A 301` — so no comparison of it could be sound. The catalog is now **generated** by
`pipeline/libation_catalog.py` with an exact convention, and `--check` guards it. The lesson:
a document that cannot be checked should be made derivable, not given a lenient checker.

This checks that the strings a document attributes to the corpus exist in the corpus. It cannot
check interpretation (a right sequence read as the wrong word).

Usage:
    uv run python pipeline/doc_claims_check.py            # report, exit 1 on failures
    uv run python pipeline/doc_claims_check.py --quiet    # exit code only
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data/database/lineara_full.db"

# Documents whose data-bearing claims are checked. Historical reports (bannered superseded) and
# audit trails are deliberately NOT checked: an audit trail records what was believed, and
# rewriting it to match today's corpus would destroy the evidence that a correction happened.
CANONICAL_DOCS = [
    "data/analysis/ventris/libation_recovered.md",
    "data/analysis/ventris/corrected_rerun_results.md",
    "data/analysis/ventris/verification_audit.md",
    "CLEANUP_PLAN.md",
]

SIGN = r"(?:AB\s*\d+[A-Za-z]?|A\s*\d{3})"
TOKEN = re.compile(r"\b" + SIGN + r"\b")
# a sequence: >=3 sign tokens joined only by space / hyphen / en-dash / middot / slash
SEQ = re.compile(
    r"\b" + SIGN + r"\b(?:\s*[-–·/]\s*|\s+)" + r"(?:" + SIGN + r"(?:\s*[-–·/]\s*|\s+))+"
    + SIGN + r"\b")

# The retracted 5-sign opening as a contiguous claim.
WRONG_OPENING = "AB 08 AB 59 AB 28 AB 54 AB 57"
WRONG_OPENING_ALLOWED = {
    "data/analysis/ventris/libation_recovered.md",    # the corrections note
    "CLEANUP_PLAN.md",                                # the record of the fix
    "EXPERIMENT_PROTOCOL.md",                         # the rule
    "pipeline/guards.py",                             # guard docstring
    "pipeline/doc_claims_check.py",                   # this file
    "data/analysis/ventris/corpus_bias_finding.md",   # before/after table
    "data/analysis/ventris/libation_catalog.md",      # generated: names the error in prose
    "data/analysis/ventris/verification_audit.md",    # Phase 17 record
}


def load_corpus() -> list[str]:
    conn = sqlite3.connect(DB)
    by_sign: dict[str, list[str]] = {}
    for g, b in conn.execute(
            "SELECT i.gorila_id, s.bennett_id FROM signs s "
            "JOIN inscriptions i ON i.id = s.inscription_id ORDER BY i.id, s.sequence"):
        if b:
            by_sign.setdefault(g, []).append(b)
    conn.close()
    return [" ".join(v) for v in by_sign.values()]


def check_sequences(corpus: list[str]) -> list[str]:
    problems = []
    for rel in CANONICAL_DOCS:
        p = REPO / rel
        if not p.exists():
            continue
        for ln, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for m in SEQ.finditer(line):
                frag = m.group(0)
                if "," in frag:
                    continue                      # an enumeration, not a sequence
                toks = [re.sub(r"\s+", " ", t.strip()) for t in TOKEN.findall(frag)]
                if len(toks) < 3:
                    continue
                pat = " ".join(toks)
                if not any(pat in c for c in corpus):
                    problems.append(f"{rel}:{ln}: sequence not in corpus: {pat}")
    return problems


def check_wrong_opening() -> list[str]:
    problems = []
    for rel in CANONICAL_DOCS + ["EXPERIMENT_PROTOCOL.md"]:
        p = REPO / rel
        if not p.exists():
            continue
        for ln, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if WRONG_OPENING in line and rel not in WRONG_OPENING_ALLOWED:
                problems.append(
                    f"{rel}:{ln}: asserts the retracted 5-sign opening: {line.strip()[:80]}")
    return problems


def run() -> int:
    if not DB.exists():
        print("no database; run tools/bootstrap.sh")
        return 2
    corpus = load_corpus()
    problems = check_sequences(corpus) + check_wrong_opening()
    print(f"doc claims vs corpus — {len(CANONICAL_DOCS)} canonical docs, {len(corpus)} inscriptions")
    print(f"  failures: {len(problems)}")
    for x in problems:
        print("  [FAIL] " + x)
    if not problems:
        print("  [PASS] every checked claim matches the corpus")
    return 1 if problems else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true")
    ap.parse_args()
    sys.exit(run())


if __name__ == "__main__":
    main()
