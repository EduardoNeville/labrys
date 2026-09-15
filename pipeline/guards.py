"""Permanent guards: the checks that would have caught this project's own defects.

Every one of these is a regression test for a specific failure that actually
happened and cost real time. Run before trusting any analysis output:

    uv run python pipeline/guards.py

Exit code is non-zero if any guard fails. No framework, no fixtures — one
process, one report. See data/analysis/ventris/oracle_repair_report.md.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PIPELINE = REPO / "pipeline"
RESULTS: list[tuple[str, bool, str]] = []


def guard(name: str, fn) -> None:
    try:
        detail = fn() or ""
        RESULTS.append((name, True, detail))
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
    except Exception as e:  # noqa: BLE001 - a guard that crashes is a failure
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))


# ── 1. value leak ────────────────────────────────────────────────────────────
def g_leak() -> str:
    """A hidden sign's value must be unreachable from the corpus tables."""
    from pipeline.lb_ingest import assert_no_leak, DB_PATH
    if not DB_PATH.exists():
        return "skipped (no Linear B DB)"
    assert_no_leak(DB_PATH)
    return "syllabogram transliteration is NULL throughout"


# ── 2. phonetic constants ────────────────────────────────────────────────────
def g_phonetics() -> str:
    """Subscripts resolve; all 74 Linear B values are mapped (defects 4/5)."""
    from pipeline import phonetics
    phonetics._selfcheck()
    return f"{len(phonetics.CONS_SERIES_MAP)} values mapped, subscripts handled"


def g_single_definition() -> str:
    """Phonetic logic must exist once. Four copies drifted; that's a defect class."""
    offenders = []
    for p in PIPELINE.rglob("*.py"):
        if p.name == "phonetics.py":
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^def (vowel_of|_canonical_vowel_of)\b", src, re.M):
            # a delegating shim is acceptable only if it imports the canonical one
            tail = src[m.start():m.start() + 600]
            if "pipeline.phonetics" not in tail:
                offenders.append(f"{p.relative_to(REPO)}:{m.group(1)}")
    assert not offenders, f"duplicate phonetic logic: {offenders}"
    return "one definition of vowel_of"


# ── 3. grid values resolve ───────────────────────────────────────────────────
def g_grid_values() -> str:
    """Grids the pipeline actually uses must resolve to a series.

    The legacy 138-sign grid still carries the phantom rows AGENTS.md records as
    purged (AB 86-96 = 'lo'), so those are reported, not enforced; fail only on
    the honest grids (58 CONFIRMED + 11 UNCERTAIN purged, and the refined grid).
    """
    from pipeline.phonetics import series_of
    enforce = ["data/analysis/bootstrapping/expanded_grid_purged.csv",
               "data/analysis/comparative/refined_phonetic_grid.csv"]
    unchecked: list = []
    unresolved: list = []
    checked = 0

    def scan(rel, collect_bad):
        p = REPO / rel
        if not p.exists():
            return 0
        n = 0
        for r in csv.DictReader(open(p, encoding="utf-8")):
            v = (r.get("refined_value") or "").strip()
            if not v or v == "?":
                continue
            n += 1
            if series_of(v) == "?":
                collect_bad.append(f"{r.get('bennett_id')}={v}")
        return n

    for rel in enforce:
        checked += scan(rel, unresolved)
    legacy_bad: list = []
    scan("data/analysis/bootstrapping/expanded_grid.csv", legacy_bad)
    assert not unresolved, f"unmapped grid values in grids in use: {sorted(set(unresolved))[:8]}"
    note = f"{checked} values resolve"
    if legacy_bad:
        note += (f"; legacy expanded_grid.csv still has {len(legacy_bad)} unmapped "
                 f"phantom values ({sorted(set(legacy_bad))[:3]}…) — deprecated, not used")
    return note


def report_legacy_grid() -> None:
    """Legacy 138-sign grid: phantom rows must not be used (AGENTS.md)."""
    p = REPO / "data/analysis/bootstrapping/expanded_grid.csv"
    if not p.exists():
        return
    from pipeline.phonetics import series_of
    phantoms = [r.get("bennett_id") for r in csv.DictReader(open(p, encoding="utf-8"))
                if (r.get("refined_value") or "").strip()
                and series_of(r["refined_value"]) == "?"]
    if phantoms:
        print(f"\n  legacy grid phantoms (do not use expanded_grid.csv): "
              f"{len(phantoms)} rows, e.g. {phantoms[:6]}")


# ── 4. candidate generation honours the anchor override ──────────────────────
def g_candidate_override() -> str:
    """get_candidates(confirmed=...) must actually change the candidate set.

    Guards the anchor leak: if hidden signs keep constraining their own
    candidates, the oracle measures nothing (defect found in Phase 12).
    """
    from pipeline.ventris.complete import VentrisGridCompleter
    c = VentrisGridCompleter()
    try:
        bids = [b for b in c.confirmed if c.kober_clinks.get(b)]
        assert bids, "no sign has Kober links — cannot test"
        differs = None
        for b in bids[:60]:
            with_full = len(c.get_candidates(b, confirmed=c.confirmed))
            with_none = len(c.get_candidates(b, confirmed={}))
            if with_full != with_none:
                differs = (b, with_full, with_none)
                break
        assert differs, "candidates ignore the confirmed= argument"
        return f"override changes candidates (e.g. {differs[0]}: {differs[1]}→{differs[2]})"
    finally:
        c.close()


# ── 5. oracle chance baseline ────────────────────────────────────────────────
def g_oracle_chance() -> str:
    """The chance baseline must be computed per trial from effective anchors.

    Textual regression guard: the baseline must not be derived from the full
    anchor set, which inflates it (defect 2).
    """
    src = (PIPELINE / "ventris/complete.py").read_text(encoding="utf-8")
    body = src.split("def oracle_test", 1)[1].split("\n    def ", 1)[0]
    assert "confirmed=eff_confirmed" in body, \
        "oracle_test chance baseline does not use the effective anchor set"
    assert "trial_chances" in body, "oracle_test has no per-trial chance record"
    return "chance baseline uses per-trial effective anchors"


# ── 6. glyph columns ─────────────────────────────────────────────────────────
def g_glyphs() -> str:
    """Glyph columns must come from Unicode names, never codepoint offsets."""
    from pipeline.unicode_utils import correct_glyph_columns
    p = REPO / "data/analysis/comparative/la_lb_mapping.csv"
    if not p.exists():
        return "skipped (no mapping file)"
    bad = 0
    for r in csv.DictReader(open(p, encoding="utf-8")):
        fixed = correct_glyph_columns(r)
        if any(fixed.get(k, "") != r.get(k, "")
               for k in ("la_unicode", "la_char", "lb_unicode", "lb_char")):
            bad += 1
    assert bad == 0, f"{bad} rows have offset-derived glyphs (run audit_grid_inputs.py --apply-glyphs)"
    return "all glyph columns match the Unicode names"


# ── 7. known defects (reported, not enforced) ────────────────────────────────
def report_known_defects() -> None:
    p = REPO / "data/analysis/comparative/la_lb_mapping_audit.csv"
    if not p.exists():
        return
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    conflict = [r["bennett_id"] for r in rows if "CONFLICT" in r["issue"]]
    missing = [r["bennett_id"] for r in rows if "MISSING" in r["issue"]]
    unver = [r["bennett_id"] for r in rows if "UNVERIFIABLE" in r["issue"]]
    print("\n  known defects awaiting deliberate re-derivation (NOT enforced):")
    print(f"    lb_value conflicts standard ({len(conflict)}): {', '.join(conflict)}")
    print(f"    standard value not recorded ({len(missing)}): {', '.join(missing)}")
    print(f"    asserts a value for an unencoded sign ({len(unver)}): {', '.join(unver)}")


def main() -> None:
    guard("no value leak in corpus tables", g_leak)
    guard("phonetic constants complete + subscript-safe", g_phonetics)
    guard("phonetic logic defined once", g_single_definition)
    guard("grid values resolve to a series", g_grid_values)
    guard("candidates honour the anchor override", g_candidate_override)
    guard("oracle chance baseline uses effective anchors", g_oracle_chance)
    guard("glyph columns follow Unicode names", g_glyphs)

    print("=== Labrys guards ===")
    for name, ok, detail in RESULTS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if detail:
            print(f"         {detail}")
    report_known_defects()
    report_legacy_grid()
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} guards passed")
    if failed:
        print("FAILED: " + "; ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()