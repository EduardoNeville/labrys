"""The Dream-RSI inner loop: a draining work queue over this project's evidence.

WHY THIS IS NOT THE LOOP FROM `.pi/PLAN.md` §10. That loop asks "which method next?" and its honest
answer for this corpus is "stop and acquire evidence" — §6.3's degeneracy, measured: pi_0 is optimal
at every beta and nothing beats it. Running *that* continuously would emit a rigorously negative
0.00x forever, which is exactly the failure mode PLAN §15 names. It is the right shape for a paper and
the wrong shape for a system.

So the inner loop runs a different objective: **keep every recorded number true, and keep the
acquisition path ready.** Concretely it does two things no policy in the tree can do:

  verify    re-derive a recorded number from the corpus and flag it if it moved. This is what found
            the D1 (per-process triple permutation) and D2 (a reseeded global RNG turned "8 trials"
            into 2 distinct draws) defects — by hand, once. It should happen on a schedule.
  diagnose  measure a question the tree records only in pooled form, per archive, since the archive
            rule now applies to everything (POSITIVES_AUDIT.md §2 mode 3).

Actions that need *code* (a new channel, a new candidate generator) and actions that need *the world*
(a corpus that does not exist yet) are not executed here: they are emitted as the outer loop's menu,
with their cost and their expected payoff, because pretending an inner loop can do them is how a
system accumulates fake progress. See RSI_LOOP.md.

    uv run python pipeline/rsi_loop.py --plan          # what would run, and why
    uv run python pipeline/rsi_loop.py --run 3         # execute up to 3 executable actions
    uv run python pipeline/rsi_loop.py --status        # coverage and terminal state
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RSI = REPO / "data" / "analysis" / "rsi"
STATE = RSI / "loop_state.json"
LOG = RSI / "loop_log.jsonl"

# ── the registry ─────────────────────────────────────────────────────────────
# kind: verify | diagnose  -> executable here
#       code | acquire     -> outer loop (an agent writes code / the world provides data)
# cost is wall-clock seconds, estimated from measured runs, not guessed.

ACTIONS = [
    dict(id="verify:guards", kind="verify", cost=35,
         what="run the guard suite: 14 invariant checks, each a regression test for a defect "
              "that actually happened",
         executor="guards"),
    dict(id="verify:shipped-node", kind="verify", cost=35,
         what="re-derive the shipped-config node (op1) and compare with what the tree records: "
              "lift, recovered, verdict",
         executor="shipped_node"),
    dict(id="verify:libation-counts", kind="verify", cost=5,
         what="re-derive the libation formula's four counts, the opening at position 0 in 11/11, "
              "and slot order in 9/9 texts — the project's one surviving positive",
         executor="libation"),
    dict(id="verify:commodity-pairs", kind="verify", cost=20,
         what="re-derive the commodity associations' document-level p-values AND the cross-site "
              "replication result (2 of 67, both tautologies)",
         executor="commodity"),
    dict(id="diagnose:membership-by-archive", kind="diagnose", cost=90,
         what="the candidate generator discards the truth on ~46% of draws pooled; measure it per "
              "archive, since the ceiling on any method is set here and the archive rule applies",
         executor="membership"),
    dict(id="diagnose:recall-by-archive", kind="diagnose", cost=420, expensive=True,
         what="conditional unique-argmax per archive (op2f is pooled): does any archive's scorer "
              "identify where the pooled one does not?",
         executor="recall"),
    dict(id="code:cm-acceptance-test", kind="code", cost=3600,
         what="pre-register the LA<->Cypro-Minoan acceptance test: the gate, the null, the "
              "stratification, and the falsification criterion, written before the corpus exists",
         unblocks="x1-cm-corpus"),
    dict(id="code:d4-candidate-generator", kind="code", cost=7200,
         what="a candidate generator that keeps the truth (D4: ~46% of draws void). Must be a NEW "
              "method behind the frozen evaluator, never an edit to it (INVARIANT 1)",
         unblocks="op2f-identifiable-subset"),
    dict(id="code:new-channel", kind="code", cost=10800,
         what="any channel not in the four cached components. The class channel (op2d) is the only "
              "one that ever carried controlled signal, and it was not convertible (op2e) — so a "
              "proposal must say why it can be converted where op2d could not",
         unblocks="op2-per-sign-instrument"),
    dict(id="acquire:cm-corpus", kind="acquire", cost=0, poll=True,
         what="languages/cypro-minoan/data/raw/PROVENANCE.json must declare synthetic=false. "
              "File presence is NOT evidence: that directory currently holds a placeholder "
              "generated from the LA->CM signs the test would confirm",
         unblocks="x1-cm-corpus"),
    dict(id="acquire:anetaki-ii", kind="acquire", cost=0, poll=True,
         what="the KN Zg 57/58 edition: the only non-administrative text since the corpus "
              "correction, and the re-test case for paradigm slots (§7 class 2)",
         unblocks="x2-anetaki-ii"),
]


# ── executors ────────────────────────────────────────────────────────────────
def x_guards(state: dict) -> dict:
    r = subprocess.run([sys.executable, "pipeline/guards.py"], cwd=REPO,
                       capture_output=True, text=True)
    tail = (r.stdout or "").strip().splitlines()[-1:]
    ok = r.returncode == 0
    return {"ok": ok, "detail": tail[0] if tail else "no output", "changed": not ok}


def x_shipped_node(state: dict) -> dict:
    sys.path.insert(0, str(REPO))
    from pipeline.rsi_evaluate import SHIPPED_METHOD, evaluate
    from pipeline.rsi_tree import TREE, load
    node = evaluate(SHIPPED_METHOD)
    recorded = next((n for n in load(TREE)["nodes"] if n["id"] == "op1-shipped-scorer"), None)
    same = bool(recorded) and (
        recorded["metrics"]["exact_rate"] == node["metrics"]["exact_rate"]
        and recorded["verdict"] == node["verdict"])
    return {"ok": True,
            "detail": f"lift {node['lift']:.2f}x, {node['values_recovered']} recovered, "
                      f"{node['verdict']}; matches the recorded node: {same}",
            "changed": not same}


def x_libation(state: dict) -> dict:
    db = REPO / "data/database/lineara_full.db"
    conn = sqlite3.connect(db)
    rows = list(conn.execute(
        "SELECT i.gorila_id g, s.sequence q, s.bennett_id b, s.sign_type t FROM signs s "
        "JOIN inscriptions i ON i.id=s.inscription_id ORDER BY i.id, s.sequence"))
    conn.close()
    seq: dict = {}
    for g, q, b, t in rows:
        if t in ("syllabogram", "logogram") and b:
            seq.setdefault(g, []).append(b)
    words = {"ja-sa-sa-ra-me": 9, "u-na-ka-na-si": 6, "si-ru-te": 7,
             "opening": 11}
    pats = {"ja-sa-sa-ra-me": ("AB 57", "AB 31", "AB 31", "AB 60", "AB 13"),
            "u-na-ka-na-si": ("AB 10", "AB 06", "AB 77", "AB 06", "AB 41"),
            "si-ru-te": ("AB 41", "AB 26", "AB 04"),
            "opening": ("AB 08", "AB 59", "AB 28", "A 301", "AB 54", "AB 57")}
    got = {}
    for name, pat in pats.items():
        n = z = 0
        for g, s in seq.items():
            for i in range(len(s) - len(pat) + 1):
                if tuple(s[i:i + len(pat)]) == pat:
                    n += 1
                    z += int(i == 0)
        got[name] = (n, z)
    changed = [k for k, v in words.items() if got[k][0] != v]
    # SLOT ORDER matters and must be the DOCUMENTED one (opening -> name-anchor -> request ->
    # favour -> divine), not this dict's insertion order. The first version of this check compared
    # against `list(pats)` and flagged 2/7 texts as out of order: a false drift report caused by
    # the reference being wrong, not the corpus. It is the same trap as comparing against a stale
    # baseline, one level down.
    SLOT_ORDER = ["opening", "ja-sa-sa-ra-me", "u-na-ka-na-si", "si-ru-te"]
    order_ok = order_tot = 0
    for g in seq:
        hits = sorted((next(i for i in range(len(seq[g]) - len(p) + 1)
                            if tuple(seq[g][i:i + len(p)]) == p), k)
                      for k, p in pats.items()
                      if any(tuple(seq[g][i:i + len(p)]) == p
                             for i in range(len(seq[g]) - len(p) + 1)))
        if len(hits) >= 2:
            order_tot += 1
            order_ok += int([k for _, k in hits]
                            == sorted((k for _, k in hits), key=SLOT_ORDER.index))
    return {"ok": not changed,
            "detail": f"counts {[got[k][0] for k in words]} (recorded {list(words.values())}); "
                      f"opening at index 0 in {got['opening'][1]}/11; slot order "
                      f"{order_ok}/{order_tot} texts",
            "changed": bool(changed) or order_ok != order_tot}


def x_commodity(state: dict) -> dict:
    """Two scripts, two claims: the document-level p-values, and the cross-site replication.

    The first version grepped only `enrichment_audit.py`'s output for the replication line, which
    lives in `cross_site_replication.py` — so it reported 'replication line present: False' for a
    test that had run and passed its re-check.
    """
    p1 = subprocess.run([sys.executable, "data/analysis/commodity_decoding/enrichment_audit.py"],
                        cwd=REPO, capture_output=True, text=True)
    p2 = subprocess.run([sys.executable,
                         "data/analysis/commodity_decoding/cross_site_replication.py"],
                        cwd=REPO, capture_output=True, text=True)
    out1, out2 = p1.stdout or "", p2.stdout or ""
    p_ok = "2.69e-11" in out1 and "2.63e-05" in out1
    rep_ok = "replicated: 2 of 67" in out2
    return {"ok": p_ok and rep_ok,
            "detail": f"document-level p {'reproduces' if p_ok else 'MOVED'}; "
                      f"cross-site replication {'still 2 of 67' if rep_ok else 'CHANGED'}",
            "changed": not (p_ok and rep_ok)}


def x_membership(state: dict) -> dict:
    """D4 per archive: the share of draws where the truth survives candidate generation."""
    sys.path.insert(0, str(REPO))
    import importlib.util
    from pathlib import Path as P
    spec = importlib.util.spec_from_file_location(
        "strat", REPO / "data/analysis/ventris/stratify_oracle_by_findspot.py")
    strat = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strat)
    import tempfile
    import pipeline.lb_oracle as O
    out = {}
    src_db = P(O.DB_PATH)
    for site in ("KN", "PY", "TH"):
        work = P(tempfile.mkdtemp(prefix=f"mem-{site}-"))
        db, stats = strat.build_stratum(site, work, src_db)
        O.DB_PATH = db
        O.KOBER_DIR = work / "kober"
        O.TRIPLES = O.KOBER_DIR / "triple_patterns.csv"
        O.FREQ_CSV = work / "freq.csv"
        O.RESULT_MD = work / "report.md"
        # The stratum's OWN Kober graph: candidate generation is Kober-constrained, so membership
        # cannot be measured without it -- passing None (the first version) raised a TypeError
        # rather than silently using the pooled graph, which is the good failure.
        O.build_kober()
        from pipeline.ventris.complete import VentrisGridCompleter
        c = VentrisGridCompleter(db_path=str(db), expanded_grid_path=str(O.ANSWER_KEY),
                                 kober_triples_path=str(O.TRIPLES),
                                 freq_constraints_path=str(O.FREQ_CSV), ab68_override=False)
        import random
        rng = random.Random(0)
        bids = sorted(c.confirmed)
        inside = tot = 0
        sizes = []
        for _ in range(8):
            hs = set(rng.sample(bids, 20))
            eff = {b: v for b, v in c.confirmed.items() if b not in hs}
            for b in hs:
                cands = c.get_candidates(b, confirmed=eff)
                sizes.append(len(cands))
                inside += int(c.confirmed[b] in cands)
                tot += 1
        c.close()
        out[site] = {"membership": round(inside / tot, 4), "mean_candidates":
                     round(sum(sizes) / len(sizes), 1), "inscriptions": stats["inscriptions"]}
    return {"ok": True, "detail": json.dumps(out), "changed": False}


def x_recall(state: dict) -> dict:
    return {"ok": True, "detail": "not implemented in the inner loop: needs per-archive "
                                  "collect() passes (~7 min per archive)",
            "changed": False}


EXECUTORS = {"guards": x_guards, "shipped_node": x_shipped_node, "libation": x_libation,
             "commodity": x_commodity, "membership": x_membership, "recall": x_recall}


# ── state ────────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"runs": {}, "terminal": None}


def save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1) + "\n", encoding="utf-8")


def log(entry: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def acquisition_inbox() -> list:
    """Poll the world: is any acquisition available *as evidence*?

    Not "does a file exist". The first version of this function returned 'x1-cm-corpus is ready'
    because `languages/cypro-minoan/data/raw/` was non-empty — and that directory holds a
    **synthetic placeholder generated from the LA->CM signs a transfer test would be trying to
    confirm**, plus random fill. A test run on it would be circular in the most direct possible way,
    and it would have looked like progress.

    So an acquisition counts as available only when a provenance manifest declares
    `synthetic: false`. "An artifact exists" is not "the evidence exists" — the distinction this
    project has had to make thirteen times (POSITIVES_AUDIT.md), and the one a continuous loop is
    most likely to get wrong, because it is the thing that keeps the loop busy.
    """
    ready, blocked = [], []
    for label, rel in (("x1-cm-corpus", "languages/cypro-minoan/data/raw"),
                       ("x2-anetaki-ii", None)):
        if rel is None:
            blocked.append(f"{label}: absent, and no manifest to declare it (needs the edition)")
            continue
        d = REPO / rel
        files = [p for p in d.iterdir() if p.is_file()] if d.exists() else []
        data = [p for p in files if p.name != "PROVENANCE.json"]
        prov = d / "PROVENANCE.json"
        if not data:
            blocked.append(f"{label}: no files")
            continue
        if not prov.exists():
            blocked.append(f"{label}: {len(data)} file(s) present but NO PROVENANCE.json — "
                           f"refusing to treat an undeclared input as evidence")
            continue
        m = json.loads(prov.read_text(encoding="utf-8"))
        if m.get("synthetic") is True:
            blocked.append(f"{label}: present but SYNTHETIC — circular for the test it would be "
                           f"used for ({str(m.get('source', '?'))[:52]}...)")
        elif m.get("synthetic") is False:
            ready.append(f"{label}: REAL corpus, provenance recorded "
                         f"({str(m.get('source', '?'))[:44]})")
        else:
            blocked.append(f"{label}: PROVENANCE.json present but `synthetic` is not declared "
                           f"true/false — refusing to guess")
    return ready + blocked


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", action="store_true")
    p.add_argument("--run", type=int, default=0, metavar="N")
    p.add_argument("--status", action="store_true")
    p.add_argument("--force", action="store_true",
                   help="run actions again even if they passed (a scheduled re-check)")
    p.add_argument("--include-expensive", action="store_true")
    args = p.parse_args()

    state = load_state()
    inbox = acquisition_inbox()

    def runnable(a):
        return a["kind"] in ("verify", "diagnose") and (
            args.include_expensive or not a.get("expensive"))

    def due(a):
        """Not-yet-run, or last run flagged/failed. Otherwise the loop spins on the same checks.

        `verify` actions are meant to be re-run *on a schedule* (drift detection is their point),
        which is what --force is for; but an unscheduled run must move on to unmeasured work.
        """
        prev = state["runs"].get(a["id"])
        return prev is None or prev.get("changed") or not prev.get("ok") or args.force

    if args.plan or not (args.run or args.status):
        print(f"{'action':32s} {'kind':9s} {'cost':>7s}  last run            note")
        for a in ACTIONS:
            last = state["runs"].get(a["id"], {}).get("when", "never")
            note = ""
            if not runnable(a):
                note = "expensive (--include-expensive)" if a.get("expensive") else \
                       "OUTER LOOP" + (f" -> unblocks {a['unblocks']}" if a.get("unblocks") else "")
            print(f"{a['id']:32s} {a['kind']:9s} {a['cost']:6d}s  {last:19s} {note}")
        print("\nacquisition inbox:")
        for line in inbox:
            print(f"  {line}")
        print("inner loop executes verify/diagnose only. code/acquire actions are the outer "
              "loop's menu —\nthey are the only ones that can raise the ceiling, and pretending "
              "an inner loop can do them\nis how a running system accumulates fake progress.")
        return

    if args.status:
        ran = {a["id"]: state["runs"].get(a["id"], {}) for a in ACTIONS}
        print(f"actions attempted: {sum(1 for v in ran.values() if v)}/{len(ACTIONS)}")
        for k, v in ran.items():
            if v:
                print(f"  {k:32s} {v.get('when','?'):20s} {'OK' if v.get('ok') else 'FLAGGED'}"
                      f"  {v.get('detail','')[:70]}")
        print(f"\nacquisition inbox:")
        for line in inbox:
            print(f"  {line}")
        print(f"terminal: {state.get('terminal') or 'not reached — actions remain'}")
        return

    ran = 0
    for a in ACTIONS:
        if ran >= args.run:
            break
        if not runnable(a) or not due(a):
            continue
        t0 = time.time()
        try:
            res = EXECUTORS[a["executor"]](state)
        except Exception as e:                                    # noqa: BLE001
            res = {"ok": False, "detail": f"{type(e).__name__}: {e}", "changed": True}
        entry = {"when": time.strftime("%Y-%m-%d %H:%M:%S"), "ok": res["ok"],
                 "changed": res["changed"], "detail": res["detail"],
                 "seconds": round(time.time() - t0, 1)}
        state["runs"][a["id"]] = entry
        save_state(state)
        log({"action": a["id"], **entry})
        flag = "FLAGGED" if res["changed"] else "ok"
        print(f"[{flag}] {a['id']} ({entry['seconds']}s): {res['detail']}")
        ran += 1

    remaining = [a for a in ACTIONS if runnable(a) and due(a)]
    outer = [a for a in ACTIONS if a["kind"] in ("code", "acquire")]
    if not remaining:
        state["terminal"] = ("inner queue drained: every executable action has run. What remains "
                             "needs code (outer loop) or the world (acquisition inbox).")
        save_state(state)
        print(f"\n{state['terminal']}")
        print("\nouter menu, by expected value:")
        for a in outer:
            print(f"  {a['id']:32s} cost {a['cost']:6d}s  {a['what'][:88]}")
    else:
        print(f"\n{len(remaining)} executable action(s) remain; "
              f"outer menu has {len(outer)} item(s)")


if __name__ == "__main__":
    main()
