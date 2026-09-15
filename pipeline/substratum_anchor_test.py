"""Substratum anchor test: is there a readable Rosetta fragment?

Every method that failed so far inferred values from *distribution within* the
Linear A corpus. The one anchor class with a track record in this project is
different in kind: Minoan words survive inside Linear B, written in a script whose
values we know. If an LA word can be aligned to an LB word — known values at the
known positions, an unknown sign opposite a known one — the unknown sign's value
is readable off the LB side. That is the crossword mechanic, not inference.

What this script measures, with a pre-registered gate:

  1. LEXICON      — LB words as value sequences (fully known), indexed by position.
  2. HOLE-FILLING — for each LA word with holes (signs lacking a transferred
                    value), intersect the LB lexicon at the known positions.
  3. HOLD-OUT     — the honest test: for LA words where EVERY position has a
                    transferred value, hide one position, fill it, and check
                    whether the fill equals the value it hides. Truth here is the
                    transfer grid (imperfect) but the test measures the *lexical*
                    inference, which is what we want to know about.
  4. CONTROL      — the same hold-out under a *permuted* LA→value assignment, which
                    gives the floor that any result must beat.

PRE-REGISTERED GATE (fixed before running; see EXPERIMENT_PROTOCOL.md):
  * hold-out unique-and-correct rate must exceed the permuted control's by >= 5x,
  * and the control's rate must be low (< 10%) for the test to mean anything.
Fail either -> there is no readable fragment: LA words have no unique LB
counterpart beyond chance, and no amount of lexical matching can recover values.

Usage: uv run python pipeline/substratum_anchor_test.py
"""

from __future__ import annotations

import csv
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LA_DB = REPO / "data/database/lineara_full.db"
LB_DB = REPO / "languages/linear-b/data/database/linear-b.db"
MAPPING = REPO / "data/analysis/comparative/la_lb_mapping.csv"

GATE_MARGIN = 5.0
GATE_CONTROL_MAX = 0.10
MIN_WORD_LEN = 3


# ── corpus loading ───────────────────────────────────────────────────────────

def load_la_words() -> list:
    """Linear A words from the consensus segmentation.

    The LA `words` table in the database is empty — segmentation lives in
    data/analysis/segmentation/segmented_texts_consensus.csv, where
    `segmented_text` is a string of Linear A characters with the Aegean word
    divider U+10101 between words. Characters are mapped to sign IDs through the
    (now corrected) `la_char` column of the mapping file. Words containing any
    character that does not map (logograms, damage) are dropped rather than
    silently shortened.
    """
    char2bennett = {r["la_char"]: r["bennett_id"]
                    for r in csv.DictReader(open(MAPPING, encoding="utf-8"))
                    if r.get("la_char") and r.get("bennett_id")}
    path = REPO / "data/analysis/segmentation/segmented_texts_consensus.csv"
    words, dropped = [], 0
    for r in csv.DictReader(open(path, encoding="utf-8")):
        for chunk in (r.get("segmented_text") or "").split("𐄁"):
            chars = [ch for ch in chunk if not ch.isspace()]
            if not chars:
                continue
            ids = [char2bennett.get(ch) for ch in chars]
            if any(i is None for i in ids):
                dropped += 1
                continue
            if len(ids) >= MIN_WORD_LEN:
                words.append(tuple(ids))
    print(f"  (LA words dropped for unmapped characters: {dropped})")
    return words


def load_lb_words_and_values():
    conn = sqlite3.connect(str(LB_DB))
    words = [tuple(s for s in (seq or "").split("-") if s)
             for (seq,) in conn.execute("SELECT sign_sequences FROM words")]
    conn.close()
    values = {}
    key = REPO / "languages/linear-b/answer_key.csv"
    for r in csv.DictReader(open(key, encoding="utf-8")):
        if r["decision"] == "CONFIRM":
            values[r["bennett_id"]] = r["refined_value"].strip()
    return [w for w in words if len(w) >= MIN_WORD_LEN], values


def load_transfer() -> dict:
    """LA sign → Linear B phonetic value (the sign-level transfer, corrected)."""
    out = {}
    for r in csv.DictReader(open(MAPPING, encoding="utf-8")):
        v = (r.get("lb_value") or "").strip()
        if v and v not in ("—", "-", "?"):
            out[r["bennett_id"]] = v.rstrip("?").lower()
    return out


# ── index + fill ─────────────────────────────────────────────────────────────

def build_index(lb_value_words: list) -> dict:
    """(length, position, value) → set of LB words (as value tuples)."""
    idx = defaultdict(set)
    for w in lb_value_words:
        for i, v in enumerate(w):
            idx[(len(w), i, v)].add(w)
    return idx


def candidates(idx, known: list, length: int) -> set:
    """LB words of `length` matching every (position, value) in `known`."""
    sets = [idx.get((length, i, v), set()) for i, v in known]
    if not sets or any(not s for s in sets):
        return set()
    sets.sort(key=len)
    out = set(sets[0])
    for s in sets[1:]:
        out &= s
        if not out:
            break
    return out


def holdout_test(la_words, transfer, idx, rng=None, shuffle_map=False):
    """Hide one known position per word; count how often the fill is unique and right."""
    st = Counter()
    transfer = dict(transfer)
    if shuffle_map:
        signs = list(transfer)
        vals = [transfer[s] for s in signs]
        rng.shuffle(vals)
        transfer = dict(zip(signs, vals))

    for w in la_words:
        vals = [transfer.get(s) for s in w]
        if any(v is None for v in vals):
            continue                      # needs every position known to hide one
        for hide in range(len(w)):
            known = [(i, v) for i, v in enumerate(vals) if i != hide]
            cands = candidates(idx, known, len(w))
            st["trials"] += 1
            if len(cands) == 1:
                got = next(iter(cands))[hide]
                st["unique"] += 1
                st["correct"] += int(got == vals[hide])
            elif len(cands) == 0:
                st["none"] += 1
            else:
                st["ambiguous"] += 1
    return st


def fill_unknown(la_words, transfer, idx):
    """The real thing: LA words with holes, filled from unique LB counterparts."""
    st = Counter()
    fills = defaultdict(Counter)
    for w in la_words:
        vals = [transfer.get(s) for s in w]
        holes = [i for i, v in enumerate(vals) if v is None]
        if not holes or len(holes) == len(vals):
            continue
        known = [(i, v) for i, v in enumerate(vals) if v is not None]
        if len(known) < 2:
            continue
        st["words_with_holes"] += 1
        cands = candidates(idx, known, len(w))
        st["words_with_candidates"] += int(bool(cands))
        if len(cands) == 1:
            st["words_unique"] += 1
            w_lb = next(iter(cands))
            for h in holes:
                st["holes_filled"] += 1
                fills[w[h]][w_lb[h]] += 1
    return st, fills


def main() -> None:
    la_words = load_la_words()
    lb_words, lb_values = load_lb_words_and_values()
    transfer = load_transfer()

    lb_value_words = []
    for w in lb_words:
        vals = tuple(lb_values.get(s) for s in w)
        if all(vals):
            lb_value_words.append(vals)
    idx = build_index(lb_value_words)

    print("=== substratum anchor test (pre-registered gate) ===")
    print(f"LA words (>={MIN_WORD_LEN} signs)     : {len(la_words)}")
    print(f"LB words with full values        : {len(lb_value_words)}")
    print(f"LA signs with a transferred value: {len(transfer)}")
    print(f"gate: hold-out unique+correct must exceed control by >= {GATE_MARGIN}x "
          f"and control < {GATE_CONTROL_MAX:.0%}\n")

    # ── 1. hold-out with the real transfer
    real = holdout_test(la_words, transfer, idx)
    # ── 2. control: permuted LA→value assignment, averaged over permutations
    ctrl_tot = Counter()
    rng = random.Random(0)
    N = 5
    for _ in range(N):
        ctrl_tot.update(holdout_test(la_words, transfer, idx, rng=rng,
                                     shuffle_map=True))

    def rate(st, k="correct"):
        return st[k] / st["trials"] if st["trials"] else 0.0

    print(f"1. HOLD-OUT (hide one known position, fill it from the LB lexicon)")
    print(f"   real      : trials {real['trials']}, unique {real['unique']}, "
          f"correct {real['correct']} → unique+correct rate {rate(real):.3f}")
    print(f"   control   : trials {ctrl_tot['trials']}, "
          f"unique+correct rate {rate(ctrl_tot):.3f}  (permuted transfer, {N} runs)")
    print(f"   ambiguous {real['ambiguous']}, no candidate {real['none']}")

    # ── 3. the real fill
    st, fills = fill_unknown(la_words, transfer, idx)
    print(f"\n2. FILLING UNKNOWN SIGNS")
    print(f"   LA words with holes            : {st['words_with_holes']}")
    print(f"   ...with >=1 LB candidate        : {st['words_with_candidates']}")
    print(f"   ...with a UNIQUE LB candidate   : {st['words_unique']}")
    print(f"   hole positions filled           : {st['holes_filled']}")
    multi = {s: m.most_common(3) for s, m in
             sorted(fills.items(), key=lambda kv: -sum(kv[1].values()))}
    print(f"   distinct signs that would receive a value: {len(fills)}")
    for sign, top in list(multi.items())[:15]:
        total = sum(fills[sign].values())
        print(f"     {sign}: {top}  (from {total} fills)")

    # ── gate
    r, c = rate(real), rate(ctrl_tot)
    print(f"\n=== GATE ===")
    print(f"   real {r:.3f} vs control {c:.3f} → ratio {r / c if c else float('inf'):.2f}x")
    if c >= GATE_CONTROL_MAX:
        print("   FAIL: control rate too high — the procedure hits by chance too often")
        sys.exit(1)
    if r < GATE_MARGIN * max(c, 1e-9):
        print("   FAIL: no readable fragment — LA words have no unique LB "
              "counterpart beyond chance")
        sys.exit(1)
    print("   PASS: lexical matching recovers values well above chance")


if __name__ == "__main__":
    main()