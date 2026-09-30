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


# ── 8. the Dream-RSI seam (PLAN §7.2, §10.5) ────────────────────────────────
def g_rsi_seam() -> str:
    """`evaluate(shipped)` must reproduce the committed oracle result.

    Asserts the gate quantities — lift, recovered, verdict — not `chance`. The
    committed chance (0.0208) belonged to a draw sequence in which trials 2-8 repeated
    trial 2's hidden set, because `score_completion` reseeded the global RNG. That is
    repaired (guard 12) and the report now reads 0.0063 vs chance 0.0273 -> 0.23x, still
    NO SIGNAL: verified by `oracle_test`, not by this guard, which stays cheap.

    `evaluate` counts only *resolved* picks, so its recovered is 0 where the oracle's
    greedy restore reports 1 — the one hit is a tie resolved by candidate order (unique-
    argmax rate is 0.0% over the same draws). Both are recorded; the gate verdict, which
    is what K4 asks about, is identical.
    """
    from pipeline.rsi_evaluate import SHIPPED_METHOD, evaluate

    node = evaluate(SHIPPED_METHOD)
    m = node["metrics"]
    assert node["lift"] == 0.0, f"lift {node['lift']} != committed 0.00x"
    assert node["values_recovered"] == 0, \
        f"recovered {node['values_recovered']} != committed 0"
    assert node["verdict"] == "NO SIGNAL", \
        f"verdict {node['verdict']} != committed NO SIGNAL"
    assert node["n_draws"] == 160, f"{node['n_draws']} draws != committed 160"
    assert m["exact_chance"] > 0, "no chance baseline computed in the same run"
    return (f"shipped config: lift {node['lift']:.2f}x, {node['values_recovered']} "
            f"recovered, {node['verdict']} over {node['n_draws']} independent draws "
            f"(chance {m['exact_chance']:.4f}; committed 0.0208 over its own "
            f"entangled sequence)")


def g_rsi_no_leak_path() -> str:
    """INVARIANT 3: the only path to the components is collect().

    Textual, in the style of g_oracle_chance: any direct `score_completion(` call in
    rsi_evaluate.py would be a path that can omit `confirmed_override` and read a
    hidden sign's real value.
    """
    src = (PIPELINE / "rsi_evaluate.py").read_text(encoding="utf-8")
    offenders = [ln for ln in src.splitlines()
                 if "score_completion(" in ln and not ln.strip().startswith("#")]
    assert not offenders, f"direct score_completion call in rsi_evaluate: {offenders}"
    assert "collect(" in src, "rsi_evaluate does not route through collect()"
    return "components come only from collect() (which always passes confirmed_override)"


# ── 9. replay (PLAN §10.5) ───────────────────────────────────────────────────
def _rsi_replay_all() -> str:
    import json

    from pipeline.rsi_policy import POLICIES
    from pipeline.rsi_replay import report
    from pipeline.rsi_tree import TREE, load

    tree = load(TREE)
    split = json.loads((TREE.parent / "split.json").read_text(encoding="utf-8"))
    return json.dumps({name: report(tree, POLICIES[name], name, split, {})
                       for name in POLICIES}, sort_keys=True)


def g_rsi_replay_determinism() -> str:
    """Same tree + policy twice -> byte-identical output."""
    from pipeline.rsi_tree import TREE

    if not TREE.exists():
        return "skipped (no tree)"
    assert _rsi_replay_all() == _rsi_replay_all(), "replay is not deterministic"
    return "replay is bit-reproducible across all four policies"


def g_rsi_monotone_select() -> str:
    """argmax over a set containing pi_0 never scores below pi_0 (PLAN §10.5).

    Guaranteed, because pi_0 is always a candidate. The guard exists to catch the code
    not doing it — so it also checks the pre-registered reference number itself.
    """
    import json

    from pipeline.rsi_policy import POLICIES
    from pipeline.rsi_replay import report
    from pipeline.rsi_tree import TREE, load

    if not TREE.exists():
        return "skipped (no tree)"
    tree = load(TREE)
    split = json.loads((TREE.parent / "split.json").read_text(encoding="utf-8"))
    scores = {name: report(tree, POLICIES[name], name, split, {})
              for name in POLICIES}
    assert "stop" in scores, "pi_0 is not in the candidate set"
    for part in ("dev", "holdout"):
        pi0 = scores["stop"][part]["V"]
        best = max(s["V"] for s in (x[part] for x in scores.values()))
        assert best >= pi0 - 1e-9, f"argmax {best} < pi_0 {pi0} on {part}"
        assert pi0 == 0.0, f"pi_0 does not score 0 on {part} ({pi0})"
    best = max(scores, key=lambda n: scores[n]["dev"]["V"])
    return (f"pi_0 is in the candidate set and scores 0.00; best on dev is {best} "
            f"({scores[best]['dev']['V']:+.3f}), holdout "
            f"{scores[best]['holdout']['V']:+.3f}")


def g_rsi_score_rng_isolated() -> str:
    """One scoring call must not touch the global RNG (phase0.md D2, repaired).

    Behavioural, not textual: the defect was `random.seed(0)` on the module-level
    stream from inside `score_completion`. Any caller sampling around a scoring call
    then draws a hidden-sign sequence shaped by the scorer's internals — which is how
    trials 2-8 of the committed oracle came out identical, and how 160 scored signs
    were 40 distinct draws. This guard fails on a reintroduction.
    """
    import random

    from pipeline.oracle_diagnose import build

    c = build("linear-b")
    try:
        bids = sorted(c.confirmed)
        hidden = [bids[0]]
        eff = {b: v for b, v in c.confirmed.items() if b not in hidden}
        cand = c.get_candidates(bids[0], confirmed=eff)[0]
        random.seed(12345)
        before = random.getstate()
        c.score_completion({bids[0]: cand}, confirmed_override=eff,
                           uncertain_override=hidden, sample_size=50)
        after = random.getstate()
        assert after == before, \
            "score_completion mutates the global RNG; a caller sampling around it " \
            "(oracle_test's hidden-sign draw) gets a sequence shaped by the scorer"
    finally:
        c.close()
    return "a scoring call leaves the global RNG state untouched"


def g_kober_triples_canonical() -> str:
    """The Kober triples file must be canonically ordered (phase0.md D1, repaired).

    The enumeration walked two sets, so `triple_id` — and the positional s1/s2/s3 roles
    that `_load_kober` reads the C/V distinction from — were a per-process permutation.
    The committed content happened to match the deterministic order (verified: identical
    triple set and identical 2,667 C-pairs / 2,564 V-pairs), so this pins the ordering
    rather than the values.
    """
    p = REPO / "languages/linear-b/data/analysis/kober/triple_patterns.csv"
    if not p.exists():
        return "skipped (no LB triples)"
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    keys = [tuple(sorted((r["sign_1"], r["sign_2"], r["sign_3"]))) for r in rows]
    ids = [int(r["triple_id"]) for r in rows]
    assert ids == list(range(1, len(rows) + 1)), "triple_id is not 1..N in file order"
    assert keys == sorted(keys), \
        "triple rows are not in canonical sign-triple order (re-run lb_oracle.py)"
    src = (PIPELINE / "kober/triple_detection.py").read_text(encoding="utf-8")
    for needle in ("for s2 in sorted(c_neighbors_s1):", "for s3 in sorted(candidates):"):
        assert needle in src, f"triple enumeration iterates an unordered set: {needle!r}"
    return f"{len(rows)} triples, canonical order, enumeration sorted"


def g_rsi_tree_consistent() -> str:
    """The pool, its verdicts and its split must agree (PLAN §8.5, §9).

    Catches the drift that actually happened while building this: a node appended to the tree
    but never added to the split (op2d), which silently kept the loop's only live channel out
    of the pool. Enforcement is a three-way partition — dev / holdout / recorded_only — so an
    intentional exclusion stays visible instead of looking like an oversight.

    K2's pre-registered count is REPORTED, not asserted: too few replayable nodes is a scope
    decision (stop searching), not an incoherent artifact, and a guard that fails on it would
    block a legitimate state.
    """
    import json

    from pipeline.rsi_tree import TREE, primary_lift, verdict_for
    from pipeline.rsi_tree import load as load_tree

    tree = load_tree(TREE)
    if not tree["nodes"]:
        return "skipped (no tree)"
    ids = [n["id"] for n in tree["nodes"]]
    assert len(set(ids)) == len(ids), "duplicate node ids in the tree"
    known = set(ids)
    for n in tree["nodes"]:
        assert n["parent"] is None or n["parent"] in known, \
            f"{n['id']}: parent {n['parent']!r} is not in the tree"
        assert "cost_hours" in n, f"{n['id']}: no cost_hours"
        if n["is_world_expanding"]:
            assert n["values_recovered"] is None, f"{n['id']}: world node carries a score"
            assert n["verdict"] == "N/A", f"{n['id']}: world node has a verdict"
        else:
            want = verdict_for(primary_lift(n))
            assert n["verdict"] == want, \
                f"{n['id']}: verdict {n['verdict']!r} drifted from gate({want!r})"
    roots = [n["id"] for n in tree["nodes"] if n["parent"] is None]
    assert roots == [tree["root"]], f"root mismatch: single root is {tree['root']}, found {roots}"

    split = json.loads((TREE.parent / "split.json").read_text(encoding="utf-8"))
    dev, hold = set(split["dev"]), set(split["holdout"])
    only = set(split.get("recorded_only", {}))
    assert not (dev & hold), f"node in both halves: {sorted(dev & hold)}"
    assert not (dev & only) and not (hold & only), "a node is both played and recorded-only"
    missing = known - dev - hold - only
    assert not missing, f"nodes in no part of the split: {sorted(missing)}"
    extra = (dev | hold | only) - known
    assert not extra, f"split names nodes that do not exist: {sorted(extra)}"

    replayable = [n for n in tree["nodes"] if not n["is_world_expanding"]]
    played = [n for n in replayable if n["id"] in dev | hold]
    k2 = (f"K2 {"fires" if len(played) < 12 else "passes"} "
          f"({len(played)} replayable nodes played")
    return (f"{len(tree['nodes'])} nodes, {len(replayable)} replayable, verdicts recompute, "
            f"split covers every node once ({len(dev)} dev / {len(hold)} holdout / "
            f"{len(only)} recorded-only); {k2}")


def main() -> None:
    guard("no value leak in corpus tables", g_leak)
    guard("phonetic constants complete + subscript-safe", g_phonetics)
    guard("phonetic logic defined once", g_single_definition)
    guard("grid values resolve to a series", g_grid_values)
    guard("candidates honour the anchor override", g_candidate_override)
    guard("oracle chance baseline uses effective anchors", g_oracle_chance)
    guard("glyph columns follow Unicode names", g_glyphs)
    guard("rsi seam reproduces the committed oracle", g_rsi_seam)
    guard("rsi has no direct score_completion path", g_rsi_no_leak_path)
    guard("rsi replay is deterministic", g_rsi_replay_determinism)
    guard("rsi argmax never scores below pi_0", g_rsi_monotone_select)
    guard("scoring leaves the global RNG alone", g_rsi_score_rng_isolated)
    guard("kober triples are canonically ordered", g_kober_triples_canonical)
    guard("rsi tree, verdicts and split are consistent", g_rsi_tree_consistent)

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