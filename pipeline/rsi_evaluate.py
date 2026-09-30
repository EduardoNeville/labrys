"""Method -> recorded outcome (PLAN.md §7). The only scorer entry point for the tree.

A method is **data, not code** (PLAN §7.1) — weights and a tiebreak order over the four
channels `collect()` already computes. `rsi_evaluate` never calls `score_completion`
itself: every value it reads comes from `aggregator_bakeoff.collect()`, which always
passes `confirmed_override` (INVARIANT 3, asserted textually by guard 9).

    uv run python pipeline/rsi_evaluate.py --method shipped
    uv run python pipeline/rsi_evaluate.py --method shipped --no-cache
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

from pipeline.aggregator_bakeoff import collect
from pipeline.aggregator_bakeoff import evaluate as bakeoff_evaluate
from pipeline.oracle_diagnose import CONFIGS, build

REPO = Path(__file__).resolve().parent.parent
RSI_DIR = REPO / "data" / "analysis" / "rsi"
CACHE_DIR = RSI_DIR / "cache"

# What collect() computes. A method naming anything else is a channel that does not
# exist, and a silent 0.0 would produce a flat node that means nothing (PLAN §7.1).
CHANNELS = ("m", "e", "p", "k")
PRIMARY_METRICS = ("exact", "series", "vowel")   # "frame" is not computable by collect()

SHIPPED_METHOD = {
    "id": "op1-shipped-scorer",
    "parent": None,
    "evidence_class": "distributional",
    "channels": ["m", "e", "p", "k"],
    "weights": {"m": 0.45, "e": 0.15, "p": 0.10, "k": 0.30},
    "tiebreak": [],
    "search": "greedy",
    "primary_metric": "exact",
    "trials": 8, "hidden": 20, "sample_size": 50,
    "cost_hours": 30.0,
    "cost_estimated": True,
    "source": "pipeline/lb_oracle.py + METHOD_CLOSURE_PAPER.md §4.1",
}


# ── cache key ────────────────────────────────────────────────────────────────

def _sha(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def _kober_digest(path: Path) -> str:
    """Canonical content digest of the Kober triples.

    NOT the file's mtime or bytes: `lb_oracle.py` rewrites this file with a fresh
    `triple_id` permutation on every run (same 60,155 triples, same 2,716 linked sign
    pairs — verified in data/analysis/rsi/phase0.md), so an mtime key would never hit
    and a byte key would invalidate the cache for no reason. Hashing the sorted
    sign-triple set still catches a real corpus correction, which is the stated intent.
    """
    triples = set()
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            triples.add(tuple(sorted((r["sign_1"], r["sign_2"], r["sign_3"]))))
    blob = "\n".join("|".join(t) for t in sorted(triples))
    return hashlib.sha1(blob.encode()).hexdigest()


def cache_key(method: dict, lang: str) -> str:
    cfg = CONFIGS[lang]
    parts = {
        "lang": lang,
        "channels": sorted(method["channels"]),
        "trials": method["trials"],
        "hidden": method["hidden"],
        "sample_size": method["sample_size"],
        "grid": _sha(cfg["grid"]),
        "freq": _sha(cfg["freq"]) if Path(cfg["freq"]).exists() else "missing",
        "kober": _kober_digest(cfg["kober"]) if Path(cfg["kober"]).exists() else "missing",
        "db": f"{Path(cfg['db']).stat().st_size}",
    }
    return hashlib.sha1(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:20]


def draws_for(method: dict, lang: str = "linear-b", use_cache: bool = True) -> tuple[list, bool]:
    """The component cache. One scoring pass; every weight vector after it is free."""
    from pipeline.lb_ingest import assert_no_leak

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{cache_key(method, lang)}.json"
    if use_cache and path.exists():
        return json.loads(path.read_text(encoding="utf-8")), True
    assert_no_leak(Path(CONFIGS[lang]["db"]))
    c = build(lang)
    try:
        draws = collect(c, method["trials"], method["hidden"])
    finally:
        c.close()
    path.write_text(json.dumps(draws), encoding="utf-8")
    return draws, False


# ── scoring: weights, then the tiebreak chain, then candidate order ───────────

def _check(method: dict) -> None:
    bad = [ch for ch in method["channels"] if ch not in CHANNELS]
    assert not bad, f"{method['id']}: channel(s) {bad} are not computable by collect()"
    assert "cost_hours" in method, f"{method['id']}: no cost_hours (PLAN §7.1)"
    assert method.get("primary_metric") in PRIMARY_METRICS, \
        f"{method['id']}: primary_metric {method.get('primary_metric')!r} — " \
        f"declare one of {PRIMARY_METRICS}; 'frame' is not computable by collect()"
    assert method.get("search") == "greedy", \
        f"{method['id']}: search {method.get('search')!r} is not implemented over a " \
        "component cache — a stronger search needs re-scoring, i.e. a new channel"
    unknown = set(method.get("weights", {})) | set(method.get("tiebreak", []))
    assert unknown <= set(CHANNELS), f"{method['id']}: unknown channels {sorted(unknown)}"


def _weights(method: dict):
    w = method.get("weights", {})
    return lambda r: sum(w.get(ch, 0.0) * r[ch] for ch in CHANNELS)


def select(rows: list, weights, tiebreak: list) -> tuple[int, bool]:
    """Primary score -> argmax set -> tiebreak chain. Returns (index, resolved).

    `resolved` is False when the argmax set still has more than one member after the
    tiebreak chain: the pick then depends on candidate-list order and is not an
    identification. Counting those as recoveries would be a measurement of list order,
    not of the method — and it is why the shipped config reports exactly 0 recovered.
    """
    vals = [weights(r) for r in rows]
    best = max(vals)
    arg = [i for i, v in enumerate(vals) if v == best]
    for ch in tiebreak:
        if len(arg) == 1:
            break
        top = max(rows[i][ch] for i in arg)
        arg = [i for i in arg if rows[i][ch] == top]
    return min(arg, key=lambda i: i), len(arg) == 1


def _correct(truth: str, cand: str, key: str) -> bool:
    from pipeline.phonetics import series_of, vowel_of

    if key == "exact":
        return cand == truth
    if key == "series":
        return series_of(cand) == series_of(truth)
    return vowel_of(cand) == vowel_of(truth)


def _chance(rows: list, truth: str, key: str) -> float:
    """Uniform-chance rate for this metric on this draw, same candidate generator.

    This is lb_oracle's pre-registered baseline (mean 1/|candidates|, = 0.0208 on the
    committed run) for `exact`, generalised to a class metric. It deliberately does
    *not* depend on whether the truth survived candidate generation — that separate
    fact is reported as `exact_membership`, because conflating the two would hide it.
    """
    if key == "exact":
        return 1.0 / max(len(rows), 1)
    return sum(1.0 for r in rows if _correct(truth, r["cand"], key)) / max(len(rows), 1)


def evaluate(method: dict, lang: str = "linear-b", use_cache: bool = True) -> dict:
    """Method hypothesis -> recorded outcome. Returns one node; does not write it.

    The tree has exactly one writer, `rsi_tree.append`, so that a guard can call this
    (guard 8, on every `guards.py` run) without rewriting a tracked artifact.

    Structural guarantees (EXPERIMENT_PROTOCOL.md §1, 2, 5):
      §1  the gate is read from lb_oracle.GATE_THRESHOLD via rsi_tree.verdict_for
      §2  the null control is computed inside the same pass, same draws
      §5  the only path to the components is collect(), which always passes
          confirmed_override. Asserted textually by guard 9.
    """
    from pipeline.rsi_tree import verdict_for

    _check(method)
    t0 = time.time()
    draws, cache_hit = draws_for(method, lang, use_cache)
    weights = _weights(method)
    tiebreak = list(method.get("tiebreak", []))
    key = method["primary_metric"]

    hits: list[float] = []
    chances: list[float] = []
    forced = 0
    in_candidates = 0
    scorable = [d for d in draws if d["rows"]]
    for d in scorable:
        rows = d["rows"]
        idx, resolved = select(rows, weights, tiebreak)
        hits.append(1.0 if resolved and _correct(d["truth"], rows[idx]["cand"], key) else 0.0)
        chances.append(_chance(rows, d["truth"], key))
        forced += int(resolved)
        in_candidates += int(any(r["cand"] == d["truth"] for r in rows))

    n = len(hits)
    assert n, f"{method['id']}: no scorable draws"
    rate = sum(hits) / n
    chance = sum(chances) / n
    lift = rate / chance if chance else 0.0
    # The plan's top1/in_argmax, from the same cached draws via the existing evaluator.
    agg = bakeoff_evaluate(scorable, method["id"], lambda r: weights(r))

    node = {
        "id": method["id"],
        "parent": method.get("parent"),
        "evidence_class": method["evidence_class"],
        "is_world_expanding": bool(method.get("is_world_expanding", False)),
        "method": method,
        "lift": round(lift, 4),
        "metrics": {
            key: round(lift, 4),
            f"{key}_rate": round(rate, 4),
            f"{key}_chance": round(chance, 4),
            "in_argmax_rate": round(agg["in_argmax"], 4),
            "unique_argmax_rate": round(agg["top1"], 4),
            "forced_rate": round(forced / n, 4),
            "exact_membership": round(in_candidates / n, 4),
        },
        "primary_metric": key,
        "values_recovered": round(rate * n),
        "n_draws": n,
        "control_ok": n >= 30,
        "leak_ok": True,
        "verdict": verdict_for(lift),
        "cache_hit": cache_hit,
        "seconds": round(time.time() - t0, 1),
    }
    assert node["values_recovered"] == round(sum(hits)), "recovered disagrees with the rate"
    assert node["verdict"] == verdict_for(node["metrics"][key])
    return node


def main() -> None:
    p = argparse.ArgumentParser(description="Dream-RSI: method -> recorded outcome")
    p.add_argument("--method", default="shipped", choices=["shipped"])
    p.add_argument("--no-cache", action="store_true")
    args = p.parse_args()
    assert args.method == "shipped", "only the shipped config is registered so far"
    node = evaluate(SHIPPED_METHOD, use_cache=not args.no_cache)
    print(json.dumps(node, indent=1))
    print(f"\ncommitted report says: recovery 0.0000 vs chance 0.0208 -> lift 0.00x "
          f"-- NO SIGNAL")
    print(f"this run says:         recovery "
          f"{node['metrics']['exact_rate']:.4f} vs chance "
          f"{node['metrics']['exact_chance']:.4f} -> lift {node['lift']:.2f}x "
          f"-- {node['verdict']}")


if __name__ == "__main__":
    main()
