"""Candidate exploration policies (PLAN.md §10.3).

`policy(frontier, tree, obs, W) -> batch` — the same interface online and in replay.
A batch is a set of nodes to expand this round; the empty batch means stop.

The control is the closure paper's §8 reasoning, hand-executed: expand untried nodes in
a class that last produced a non-flat result, switch class after two consecutive flat
classes, prefer an untried node in a live class over deepening an exhausted one, and if
everything is flat take the acquisition instead — or stop. It has to be good, or beating
it proves nothing, so it is transcribed rather than invented.

Three readings a policy needs, all recorded in the tree README:
  * "flat" is `rsi_tree.value_of == 0` — the node's primary metric is at or below its
    own baseline. The verdict is a gate call on the same number, so the two agree
    whenever the gate says NO SIGNAL.
  * "untried" = a frontier node with no *observed* child. That is the plan's "untried
    node in a live class" as against "deepening an exhausted one": expanding a node that
    already has an observed child is the deepening the rule deprioritises.
  * Acquisitions are ordinary tree nodes. They cannot be "always selectable": a policy
    chooses a *parent* and the parent reveals its next child in file order (PLAN §10.1),
    so a selectable-but-unobserved node would break the replay. Consequence, reported in
    the README: the policy's real decisions are pace (how many parents per batch) and
    stopping, not which branch comes next.
"""

from __future__ import annotations

from pipeline.rsi_tree import child_of, node, value_of


def _world(tree: dict, nid: str) -> bool:
    return bool(node(tree, nid)["is_world_expanding"])


def _live(tree: dict, nid: str) -> bool:
    return not _world(tree, nid) and value_of(tree, nid) > 0.0


def _untried(tree: dict, frontier: set, obs: set) -> list:
    """Frontier nodes with no observed child — new nodes, not deepenings."""
    return sorted(v for v in frontier
                  if not any(n.get("parent") == v and n["id"] in obs
                             for n in tree["nodes"]))


def control(frontier: set, tree: dict, obs: set, W: dict) -> list:
    """The closure paper's §8 policy, transcribed (PLAN §10.3)."""
    untried = _untried(tree, frontier, obs)
    live = [v for v in untried if _live(tree, v)]
    if live:
        return live                        # untried node in a live class: keep digging
    if untried:
        return untried                     # still unexplored nodes in the current class
    # Nothing untried: revealing another child of a frontier node means widening into a
    # class already shown flat. PLAN §8's "switch class / take the acquisition" is the
    # closest thing to that move this replay can express — and the next unrevealed child
    # of op1 may itself be an acquisition (x1, x2). Whether to keep widening is what §9.3
    # is asking about, so the honest control keeps narrowing and then stops.
    widening = sorted(v for v in frontier if child_of(tree, v, obs) is not None)
    return widening[:1]


def stop(frontier: set, tree: dict, obs: set, W: dict) -> list:
    """pi_0: the empty policy. Always available, always V=0."""
    return []


def clairvoyant(frontier: set, tree: dict, obs: set, W: dict) -> list:
    """Upper bound, not a policy: go to the branch whose next node scores highest.

    One node per batch, chosen by the winner's own value — knowledge no real policy has
    (it is post-hoc about which child won, §10.2). It exists to measure how much of the
    value is reachability rather than decision quality, which is §11's entry condition.
    """
    best, best_v = None, None
    for v in sorted(frontier):
        c = child_of(tree, v, obs)
        if c is None:
            continue
        val = value_of(tree, c)
        if best_v is None or val > best_v:
            best, best_v = v, val
    return [best] if best else []


def acquire(frontier: set, tree: dict, obs: set, W: dict) -> list:
    """Spend the remaining budget on data if that is what the next node is (PLAN §15).

    Expresses "prefer acquisition over another distributional attempt" only as far as
    the replay allows: a policy can select a parent, not a child.
    """
    return sorted(v for v in frontier
                  if child_of(tree, v, obs) and _world(tree, child_of(tree, v, obs)))[:1]


POLICIES = {
    "control": control,
    "stop": stop,
    "clairvoyant": clairvoyant,
    "acquire": acquire,
}
