"""Dream-RSI tree store (PLAN.md §8). Append-only JSON — no database, no ORM.

The tree is the replay pool: recorded method hypotheses and their realized outcomes.
`leaves` and `child_of` are the whole replay API (PLAN §8.5); everything else is
bookkeeping.

One rule matters more than the rest: `verdict` is **always recomputed** from
`lift[primary_metric]` through the gate in `pipeline/lb_oracle.py`, never accepted from
a file. A tree whose verdicts were typed in by a human is a tree the loop can game.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RSI_DIR = REPO / "data" / "analysis" / "rsi"
TREE = RSI_DIR / "tree.json"
RETRACTED = RSI_DIR / "retracted.json"

# PLAN §8.1 — this is the policy's action space, so it is closed.
TAXONOMY = ("distributional", "cross-script", "semantic-anchor", "long-text",
            "external-data")


def verdict_for(lift: float) -> str:
    """The pre-registered gate. Threshold is imported, never re-declared (PLAN §3)."""
    from pipeline.lb_oracle import GATE_THRESHOLD

    if lift > GATE_THRESHOLD:
        return "PASS"
    if lift > 0.5:
        return "INCONCLUSIVE"
    return "NO SIGNAL"


def primary_lift(node: dict) -> float:
    """The node's declared primary metric, or its plain lift. Never the best of many."""
    if node.get("is_world_expanding"):
        raise AssertionError(f"{node.get('id')}: a world-expanding node has no lift")
    if isinstance(node.get("lift"), (int, float)):
        return float(node["lift"])
    metrics = node.get("metrics") or {}
    key = node.get("primary_metric")
    assert key, f"{node.get('id')}: metrics dict without primary_metric"
    assert key in metrics, f"{node.get('id')}: primary_metric {key!r} not in metrics {sorted(metrics)}"
    return float(metrics[key])


def load(path: Path = TREE) -> dict:
    if not path.exists():
        return {"root": None, "nodes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def root(path: Path = TREE) -> str:
    r = load(path)["root"]
    assert r, f"{path} has no root"
    return r


def validate(node: dict, tree: dict) -> None:
    nid = node.get("id")
    assert nid, "node has no id"
    existing = {n["id"] for n in tree["nodes"]}
    assert nid not in existing, f"duplicate node id {nid}"
    parent = node.get("parent")
    assert parent is None or parent in existing, f"{nid}: parent {parent!r} is not in the tree"
    assert parent is not None or not existing, "a second root node"
    assert node.get("evidence_class") in TAXONOMY, \
        f"{nid}: evidence_class {node.get('evidence_class')!r} outside the taxonomy"
    assert "cost_hours" in node, f"{nid}: no cost_hours — -beta*N would be meaningless"
    assert isinstance(node.get("cost_estimated"), bool), f"{nid}: cost_estimated must be set"
    if node.get("is_world_expanding"):
        # A world-expanding node produces no score (PLAN §8.1): it grows the tree, it
        # does not traverse it. Exempt from the gate rather than given a fake lift.
        assert node.get("values_recovered") is None, \
            f"{nid}: a world-expanding node produces no score"
        assert "lift" not in node or node["lift"] is None, \
            f"{nid}: a world-expanding node must not carry a lift"
        assert node.get("verdict") == "N/A", f"{nid}: a world-expanding node has no verdict"
        return
    want = verdict_for(primary_lift(node))
    assert node.get("verdict") == want, \
        f"{nid}: verdict {node.get('verdict')!r} != gate({primary_lift(node):.2f}) = {want!r}"


def append(node: dict, path: Path = TREE) -> dict:
    tree = load(path)
    validate(node, tree)
    if tree["root"] is None:
        tree["root"] = node["id"]
    tree["nodes"].append(node)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree, indent=1) + "\n", encoding="utf-8")
    return node


# ── the replay API (PLAN §8.5) ───────────────────────────────────────────────

def children(tree: dict, v: str) -> list:
    """Recorded children of v, in creation order (file order is earliest-first)."""
    return [n["id"] for n in tree["nodes"] if n.get("parent") == v]


def leaves(tree: dict, obs: set) -> set:
    """The expandable frontier: observed nodes that still have an unrevealed child.

    PLAN §8.5 words this as "{root} ∪ {v ∈ obs : no observed child}", but that
    literal reading is unplayable on a branched tree: once op1 reveals one child, its
    siblings could never be revealed, so the holdout branches of §9.2 would be
    unreachable. The plan's own replay prose ("selecting the root reveals the next
    unrevealed root child") is the intended semantics, generalised to every node.
    """
    obs = set(obs)
    observed = [n for n in tree["nodes"] if n["id"] in obs]
    return {n["id"] for n in observed if child_of(tree, n["id"], obs) is not None}


def child_of(tree: dict, v: str, obs: set) -> str | None:
    """v's first child not yet revealed, or None. Deterministic by file order."""
    for c in children(tree, v):
        if c not in obs:
            return c
    return None


def node(tree: dict, nid: str) -> dict:
    for n in tree["nodes"]:
        if n["id"] == nid:
            return n
    raise KeyError(nid)


def exists(tree: dict, nid: str) -> bool:
    return any(n["id"] == nid for n in tree["nodes"])


def value_of(tree: dict, nid: str) -> float:
    """s_v — the quality term. PLAN §10.1 writes `tree["values"][v]` and never defines it.

    Defined here, in one place, because it is what V maximises and what "flat" means:
    **the node's excess over its own baseline**, `max(0, primary_lift - 1)`.

    Why not the raw lift: the tree mixes nodes whose primary metric has different
    baselines (exact-value lift over uniform chance; a series ratio over the majority
    baseline; a permutation-control ratio). Raw lift would let a node measured at 0.5x
    its own baseline (op2c: the null control) contribute +0.52 of *value* and outrank a
    real one, and it would make "flat" mean "lift <= 0" — which no node is. Excess over
    baseline makes every flat node contribute exactly 0, which is what §6.3's
    degeneracy analysis assumes.
    """
    n = node(tree, nid)
    if n["is_world_expanding"]:
        return 0.0
    return max(0.0, primary_lift(n) - 1.0)


def _selfcheck() -> None:
    tree = {"root": "a", "nodes": [
        {"id": "a", "parent": None}, {"id": "b", "parent": "a"}, {"id": "c", "parent": "a"}]}
    assert leaves(tree, {"a"}) == {"a"}
    assert leaves(tree, {"a", "b"}) == {"a"}          # a is still expandable: c unrevealed
    assert leaves(tree, {"a", "b", "c"}) == set()
    assert child_of(tree, "a", {"a"}) == "b"
    assert child_of(tree, "a", {"a", "b"}) == "c"
    assert child_of(tree, "a", {"a", "b", "c"}) is None
    assert verdict_for(0.0) == "NO SIGNAL" and verdict_for(1.0) == "INCONCLUSIVE"
    assert verdict_for(9.0) == "PASS"
    assert primary_lift({"metrics": {"k": 0.4}, "primary_metric": "k"}) == 0.4
    # a typed-in verdict that disagrees with the gate must be rejected
    bad = {"id": "x", "parent": "a", "evidence_class": "distributional",
           "lift": 0.85, "verdict": "NO SIGNAL", "cost_hours": 1.0, "cost_estimated": True}
    try:
        validate(bad, tree)
    except AssertionError:
        pass
    else:
        raise AssertionError("validate accepted a human-typed verdict")
    print("rsi_tree selfcheck ok")


if __name__ == "__main__":
    _selfcheck()
