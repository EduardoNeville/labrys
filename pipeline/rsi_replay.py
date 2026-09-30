"""Dream-RSI §3 replay: the recorded tree as a simulator (PLAN.md §10.1).

Selecting a node reveals its next recorded child. Every outcome is already saved, so a
candidate policy is evaluated by reading records — no re-running the evaluator.

    uv run python pipeline/rsi_replay.py --policy control
    uv run python pipeline/rsi_replay.py --policy all --sensitivity
"""

from __future__ import annotations

import argparse
import json

from pipeline.rsi_tree import TREE, child_of, leaves, load, node, value_of

# PLAN §10.4. Calibrated once against Phase 0.2's wall-clock (one collect() pass is
# seconds; a new channel is hours), then never tuned against the tree it replays.
B1 = 1.0   # hours charged per revealed node
B2 = 0.5   # reward per parallel batch

DEFAULT_K2 = 8   # max batches


def replay(tree: dict, policy, W: dict, K2: int = DEFAULT_K2) -> dict:
    """Deterministic. Ties in a policy's batch choice break on lowest node id.

    beta lives in W rather than in a module global, so a sensitivity sweep cannot
    mutate the constants a previous replay used.
    """
    b1, b2 = W.get("B1", B1), W.get("B2", B2)
    obs = {tree["root"]}
    revealed: list[str] = []
    batches: list[list[str]] = []
    for _ in range(K2):
        C = sorted(policy(leaves(tree, obs), tree, obs, W))
        if not C:
            break
        for v in C:
            child = child_of(tree, v, obs)
            if child is not None:
                obs.add(child)
                revealed.append(child)
        batches.append(C)   # never empty: the loop breaks above
    # World-expanding nodes are excluded from the quality term AND from N: a replay
    # cannot simulate a corpus arriving, and charging for it would teach the policy
    # that acquiring data is expensive, which is the opposite of true (PLAN §10.1).
    scored = [v for v in revealed if not node(tree, v)["is_world_expanding"]]
    N = len(scored)
    quality = max([0.0, *(value_of(tree, v) for v in scored)])
    k = len(batches)
    return {
        "V": round(quality - b1 * N + b2 * N / max(1, k), 4),
        "quality": round(quality, 4),
        "N": N, "k": k,
        "revealed": revealed, "batches": batches,
        "stopped": len(batches) < K2,
    }


def report(tree: dict, policy, name: str, split: dict, W: dict, K2: int = DEFAULT_K2) -> dict:
    """Dev and holdout reported separately — never as one number (PLAN §9, §10.6)."""
    out = {"policy": name, "K2": K2}
    for part in ("dev", "holdout"):
        # The root's record rides along even when it is not in the split: a policy has
        # to see the class and verdict of the node it is expanding. It is observed from
        # the start and never lands in `revealed`, so it is never charged for.
        sub_nodes = [n for n in tree["nodes"] if n["id"] in split[part]]
        if not any(n["id"] == tree["root"] for n in sub_nodes):
            sub_nodes.insert(0, node(tree, tree["root"]))
        sub = {"root": tree["root"], "nodes": sub_nodes}
        out[part] = replay(sub, policy, W, K2)
    return out


def _selfcheck() -> None:
    tree = load(TREE)
    # determinism: same tree + policy twice -> byte-identical output (guard 10)
    from pipeline.rsi_policy import POLICIES

    a = json.dumps(report(tree, POLICIES["control"], "control",
                          json.loads((TREE.parent / "split.json").read_text()), {}),
                   sort_keys=True)
    b = json.dumps(report(tree, POLICIES["control"], "control",
                          json.loads((TREE.parent / "split.json").read_text()), {}),
                   sort_keys=True)
    assert a == b, "replay is not deterministic"
    print("rsi_replay selfcheck ok")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--policy", default="control", choices=["control", "stop",
                                                           "clairvoyant", "all"])
    p.add_argument("--sensitivity", action="store_true",
                   help="also replay at B1 in {0.5, 1.0, 2.0} (PLAN §10.4)")
    p.add_argument("--K2", type=int, default=DEFAULT_K2)
    args = p.parse_args()

    from pipeline.rsi_policy import POLICIES

    tree = load(TREE)
    split = json.loads((TREE.parent / "split.json").read_text())
    names = list(POLICIES) if args.policy == "all" else [args.policy]

    print(f"tree: {len(tree['nodes'])} nodes "
          f"({sum(1 for n in tree['nodes'] if n['is_world_expanding'])} world-expanding)  "
          f"B1={B1} B2={B2} K2={args.K2}")
    print(f"\n{'policy':14s} {'split':8s} {'V':>8s} {'quality':>8s} {'N':>3s} {'k':>3s}  "
          f"revealed")
    rows = []
    for name in names:
        r = report(tree, POLICIES[name], name, split, {}, args.K2)
        rows.append(r)
        for part in ("dev", "holdout"):
            s = r[part]
            print(f"{name:14s} {part:8s} {s['V']:8.3f} {s['quality']:8.3f} "
                  f"{s['N']:3d} {s['k']:3d}  {','.join(s['revealed']) or '-'}")

    if args.sensitivity:
        print(f"\nB1 sensitivity (PLAN §10.4 — a flip is a finding, not a bug):")
        for b1 in (0.5, 1.0, 2.0):
            line = []
            for name in names:
                r = report(tree, POLICIES[name], name, split, {"B1": b1}, args.K2)
                line.append(f"{name}={r['dev']['V']:+.2f}/{r['holdout']['V']:+.2f}")
            print(f"  B1={b1:<4}  " + "  ".join(line))

    if args.policy == "all" or args.sensitivity:
        best = max(rows, key=lambda r: r["dev"]["V"])
        print(f"\nbest on dev: {best['policy']} (V={best['dev']['V']:+.3f}); "
              f"its holdout V={best['holdout']['V']:+.3f}")


if __name__ == "__main__":
    if "--selfcheck" in __import__("sys").argv:
        _selfcheck()
    else:
        main()
