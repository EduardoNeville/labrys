"""Provenance inventory for `data/analysis/` — which file came from what, and is it still real.

Every artifact under `data/analysis/` is either **live** (a live generator, current inputs), **retired**
(its generator moved to `legacy/`, or its measurement was replaced), or an **orphan** (nothing
generates it and nothing cites it). Before this script existed, that had to be reconstructed by hand
from commit dates, which is how a 2026-08-03 Kober graph sat under a live oracle for two months.

The table is generated, with the same rule as the libation catalog: `--check` re-renders it and fails
on drift, so a hand-edit or a new untracked artifact is visible.

What "generator" means here: a module whose source names the artifact's filename inside a string
literal. That is a *reference*, not proof of ownership — a reader and a writer look the same. The
column therefore says "referenced by", and the status column distinguishes live from retired by
which tree the referencing module lives in. It is a map, not a certificate; where a generator is
proven, the guards (20, 21, 24) enforce the artifact instead.

Usage:
    uv run python pipeline/analysis_provenance.py            # regenerate PROVENANCE.md
    uv run python pipeline/analysis_provenance.py --check    # verify (exit 1 on drift)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ANALYSIS = REPO / "data/analysis"
OUT = ANALYSIS / "PROVENANCE.md"
SKIP_DIRS = {"_superseded", "rsi/cache", "__pycache__", "overseer"}

# artifacts that are inputs, not outputs
INPUTS = {
    "logogram_contexts.csv", "toponym_anchors.csv", "sign_commodity_enrichment.csv",
    "constrained_candidates.csv", "positional_profiles.csv", "misvalued_signs_ranked.csv",
    "misvalued_signs_ngram.csv", "phonetic_grid_confidence.csv", "la_lb_mapping.csv",
    "la_lb_misaligned.csv", "la_cm_shared_phonetic_grid.csv", "minoan_shadow_lexicon.csv",
    "la_lb_ideogram_map.csv", "fraction_alignment.csv", "commodity_contexts.csv",
    "refined_phonetic_grid.csv", "expanded_grid_legacy_138.csv", "answer_key.csv",
}

# Directory-level owners, because many modules build output paths with f-strings and the literal
# index cannot see them ("network/" writes one centrality file per site). A file-level reference
# always wins; this table answers "who owns this directory" when the index finds nothing.
DIR_OWNER: dict[str, tuple[str, str]] = {
    "anatolian_search": ("legacy", "legacy/anatolian_search/comparison.py"),
    "bootstrapping": ("live", "pipeline/bootstrapping/grid_expand.py"),
    "commodity_decoding": ("mixed", "pipeline/commodity_decoding/context_extract.py"),
    "comparative": ("mixed", "pipeline/{linear_b_mapping,cypro_minoan_bridge,commodity_alignment,phonetic_grid_refinement}.py"),
    "egyptian_bridge": ("legacy", "legacy/egyptian_bridge/search.py"),
    "eteocretan": ("legacy", "legacy/eteocretan/compare.py"),
    "formulaic": ("legacy", "legacy/formulaic/analyze.py"),
    "frequency_constraints": ("legacy", "legacy/frequency_constraints/constrain.py"),
    "kober": ("live", "pipeline/kober/{triple_detection,positional_grid}.py"),
    "linguistic": ("live", "pipeline/{swadesh_search,wals_analysis,loanword_matching,toponym_alignment,morphology_scan,falsification_report}.py"),
    "logograms": ("live", "pipeline/logogram_analysis.py"),
    "ml": ("legacy", "legacy/ml/predict.py"),
    "network": ("live", "pipeline/network_analysis.py"),
    "ngram": ("live", "pipeline/ngram_analysis.py"),
    "phylogenetic": ("legacy", "legacy/phylogenetic/alignment.py"),
    "positional": ("live", "pipeline/positional_analysis.py"),
    "rsi": ("live", "pipeline/rsi_*.py + data/analysis/rsi/*.py"),
    "segmentation": ("live", "pipeline/word_segmentation.py"),
    "synthesis": ("report", "hand-written synthesis reports"),
    "ventris": ("mixed", "pipeline/ventris/complete.py + reports"),
    "verification": ("legacy", "legacy/verification/*.py"),
}

LIT = re.compile(r'["\']([A-Za-z0-9_./ -]+\.(?:csv|md|json))["\']')


def module_index() -> dict[str, dict[str, set[str]]]:
    """basename -> {'live': {...}, 'legacy': {...}} for every .py that names it.

    `live` is pipeline/ plus the audit instruments that live under data/analysis/ and tools/;
    `legacy` is the archived tree. A module in `live` may still be a *reader* of the artifact —
    the index cannot tell read from write, which is why the table says "references", not "generates".
    """
    idx: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"live": set(), "legacy": set()})
    for tree in ("pipeline", "legacy", "data/analysis", "tools"):
        bucket = "legacy" if tree == "legacy" else "live"
        for p in (REPO / tree).rglob("*.py"):
            try:
                src = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in LIT.finditer(src):
                idx[Path(m.group(1)).name][bucket].add(str(p.relative_to(REPO)))
    return idx


def doc_index() -> dict[str, set[str]]:
    """basename -> markdown docs that name it (excluding archive/ and legacy/)."""
    idx: dict[str, set[str]] = defaultdict(set)
    for p in REPO.rglob("*.md"):
        if {".venv", ".git", "archive", "legacy", ".pi", ".pi-subagents"} & set(p.parts):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name in re.findall(r"[A-Za-z0-9_./-]+\.(?:csv|md|json)", txt):
            idx[Path(name).name].add(str(p.relative_to(REPO)))
    return idx


def commit_date(path: Path) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", str(path)],
                             cwd=REPO, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "untracked"
    except Exception:
        return "?"


def artifacts() -> list[Path]:
    out = []
    for p in sorted(ANALYSIS.rglob("*")):
        if p.is_dir() or p.suffix not in {".csv", ".md", ".json"}:
            continue
        rel = str(p.relative_to(ANALYSIS))
        if any(rel.startswith(s + "/") or s in p.parts for s in SKIP_DIRS):
            continue
        if p.name in {"README.md", "PROVENANCE.md"}:
            continue
        out.append(p)
    return out


def status(name: str, refs: dict[str, set[str]], cited: set[str], top: str) -> tuple[str, str]:
    live = sorted(refs.get("live", set()))
    legacy = sorted(refs.get("legacy", set()))
    if name in INPUTS:
        return "INPUT", "consumed by an instrument; not a result"
    if live:
        return "LIVE", f"`{live[0]}`" + (f" (+{len(live) - 1})" if len(live) > 1 else "")
    if legacy:
        return "RETIRED", f"generator now `{legacy[0]}`"
    kind, who = DIR_OWNER.get(top, ("unknown", ""))
    if kind == "live":
        return "LIVE", f"directory owner `{who}`"
    if kind == "legacy":
        return "RETIRED", f"directory owner `{who}` (now in legacy/)"
    if kind == "mixed":
        return "MIXED", f"directory owner `{who}` — check the file"
    if kind == "report":
        return "REPORT", "hand-written synthesis, not a generated artifact"
    if cited:
        return "ORPHAN", "cited, but nothing generates it"
    return "ORPHAN", "nothing generates or cites it"


def render() -> str:
    idx, docs = module_index(), doc_index()
    rows = []
    for p in artifacts():
        name = p.name
        refs = idx.get(name, {"live": set(), "legacy": set()})
        cited = docs.get(name, set())
        top = str(p.relative_to(ANALYSIS)).split("/")[0]
        st, why = status(name, refs, cited, top)
        rows.append((str(p.relative_to(REPO)), st, why, commit_date(p),
                     len(cited), ", ".join(sorted(cited)[:1])))

    order = {"LIVE": 0, "INPUT": 1, "MIXED": 2, "REPORT": 3, "RETIRED": 4, "ORPHAN": 5}
    rows.sort(key=lambda r: (order[r[1]], r[0]))
    counts = defaultdict(int)
    for r in rows:
        counts[r[1]] += 1

    L = ["# Provenance of `data/analysis/` — generated, do not hand-edit", "",
         "**Generated** by `pipeline/analysis_provenance.py`. `pipeline/guards.py` re-renders this file",
         "and fails on drift, so an artifact added or moved without updating the map is visible.", "",
         "**Status key**", "",
         "| status | meaning |", "|---|---|",
         "| **LIVE** | a `pipeline/` module names it, and the inputs are current |",
         "| **INPUT** | consumed by an instrument; it is not a result |",
         "| **MIXED** | the directory has live and retired owners; the file needs a human look |",
         "| **REPORT** | hand-written synthesis, not a generated artifact |",
         "| **RETIRED** | only a `legacy/` module names it (or owns its directory) — superseded, kept for the record |",
         "| **ORPHAN** | nothing generates it and nothing (live) cites it |", "",
         f"Totals: {', '.join(f'{k} {v}' for k, v in sorted(counts.items()))}.", "",
         "| artifact | status | provenance | last commit | cited |", "|---|---|---|---|---|"]
    for rel, st, why, date, n, first in rows:
        L.append(f"| `{rel}` | {st} | {why} | {date} | {n}" + (f" — `{first}`" if first else "") + " |")
    L += ["", "---", "",
          "**How to read it.** `RETIRED` does not mean wrong; it means *its measurement belongs to its",
          "phase*, and the module that produced it no longer lives in `pipeline/`. `ORPHAN` means the",
          "file has no owner left — it is either cited history or a deletion candidate.", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render()
    if a.check:
        if not OUT.exists():
            print("PROVENANCE.md: MISSING")
            sys.exit(1)
        if OUT.read_text(encoding="utf-8") != text:
            print("PROVENANCE.md: DRIFT — re-run pipeline/analysis_provenance.py")
            sys.exit(1)
        print("PROVENANCE.md: byte-identical to the committed map")
        return
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
