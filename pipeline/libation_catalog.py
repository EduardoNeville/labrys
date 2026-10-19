"""Libation catalog — the generator for `data/analysis/ventris/libation_catalog.md`.

The catalog is a reference document for the genre that carries the project's only cross-site
positive, and until 2026-10-19 it was **hand-written while claiming "generated from the
corrected DB"**. It rendered the opening as five transliteration tokens (`a-?-i-wa-ja`) where
the corpus has six signs (`AB 08 AB 59 AB 28 A 301 AB 54 AB 57` = a-ta-i-*301-wa-ja) — the
same omitted-`A 301` slip that was found in `libation_recovered.md`. Nothing could catch it,
because nothing generated the file.

It is now generated, with the convention stated in the output:

    one token per sign row, in reading order; `|` = word divider or break;
    `?` = sign with no conventional value recorded in the DB.

That makes the document exact by construction — a length mismatch with the corpus is no longer
possible — and `--check` re-derives it, so a hand-edit fails the guard suite.

Usage:
    uv run python pipeline/libation_catalog.py            # regenerate
    uv run python pipeline/libation_catalog.py --check    # verify (exit 1 on drift)
    uv run python pipeline/libation_catalog.py --stdout    # print without writing
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data/database/lineara_full.db"
OUT = REPO / "data/analysis/ventris/libation_catalog.md"

# The genre's vessel sites. The formula words themselves are counted corpus-wide, because
# they also occur on non-vessel texts (TLZa1, VRYZa1, APZa2) — the hand-written version
# missed those by counting only within this list.
SITES = {
    "IOZa": ("Iouktas", "IOZa"),
    "KOZa": ("Kophinas", "KOZa"),
    "PKZa": ("Palaikastro", "PKZa"),
    "ARKH": ("Arkalochori", "ARKH"),
    "PRZa": ("Prassa", "PRZa"),
    "SYZa": ("Syme", "SYZa"),
    "PSZa": ("Psykhro", "PSZa"),
    "PLZf": ("Platanos", "PLZf"),
}

# Ordered slots of the formula, as established in libation_recovered.md.
SLOTS: list[tuple[str, tuple[str, ...]]] = [
    ("opening (a-ta-i-*301-wa-ja)", ("AB 08", "AB 59", "AB 28", "A 301", "AB 54", "AB 57")),
    ("ja-sa-sa-ra-me", ("AB 57", "AB 31", "AB 31", "AB 60", "AB 13")),
    ("u-na-ka-na-si", ("AB 10", "AB 06", "AB 77", "AB 06", "AB 41")),
    ("i-pi-na-ma", ("AB 28", "AB 39", "AB 06", "AB 80")),
    ("si-ru-te", ("AB 41", "AB 26", "AB 04")),
]

DIVIDERS = {"\U00010101", "\U00010102", "\U0001076b", "\U0001076c", "\U0001076d", "\U0001076e",
            "\U0001076f"}

# Recurring elements that are not slots of the formula but that the hand-written catalog
# tracked. Each pattern is verified against the corpus by this generator (which is why
# `i-da-ki-sa-ri-me` — listed for ZA21b as "AB 28 01 67 31 26 13" — is absent: that pattern
# matches **0** inscriptions, and ZA21b holds 14 signs, not 6. See verification_audit.md
# Phase 17).
EXTRA: list[tuple[str, tuple[str, ...]]] = [
    ("di-ki-te-te (Palaikastro deity root)", ("AB 07", "AB 67", "AB 04", "AB 04")),
    ("ja-di-ki-tu", ("AB 57", "AB 07", "AB 67", "AB 69")),
    ("di-ki-tu-ja", ("AB 07", "AB 67", "AB 69", "AB 57")),
    ("i-da (Mt. Ida)", ("AB 28", "AB 01")),
]


def load() -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    """Return (sign_ids, tokens, transliterations) per inscription, in reading order."""
    conn = sqlite3.connect(DB)
    rows = list(conn.execute(
        "SELECT i.gorila_id, s.bennett_id, s.transliteration FROM signs s "
        "JOIN inscriptions i ON i.id = s.inscription_id ORDER BY i.id, s.sequence"))
    types = dict(conn.execute("SELECT gorila_id, COUNT(*) FROM signs s "
                              "JOIN inscriptions i ON i.id=s.inscription_id GROUP BY gorila_id"))
    conn.close()
    signs: dict[str, list[str]] = defaultdict(list)
    tokens: dict[str, list[str]] = defaultdict(list)
    for g, b, t in rows:
        if b:
            signs[g].append(b)
        raw = (t or "?").strip()
        tokens[g].append("|" if raw in DIVIDERS else (raw.lower() if raw else "?"))
    counts = {g: types.get(g, 0) for g in signs}
    return signs, tokens, counts


def find(seq: list[str], pat: tuple[str, ...]) -> list[int]:
    return [i for i in range(len(seq) - len(pat) + 1)
            if tuple(seq[i:i + len(pat)]) == pat]


def occurrences(signs: dict[str, list[str]]) -> dict[str, list[tuple[str, int]]]:
    out = {}
    for name, pat in SLOTS:
        hits = []
        for g in sorted(signs):
            for i in find(signs[g], pat):
                hits.append((g, i))
        out[name] = hits
    return out


def render() -> str:
    signs, tokens, counts = load()
    occ = occurrences(signs)
    L: list[str] = []
    A = L.append

    A("# Libation Formula Catalog (Corrected Corpus) — Reference Document")
    A("")
    A("**Generated** by `pipeline/libation_catalog.py` from `data/database/lineara_full.db`.")
    A("Do not hand-edit: `pipeline/guards.py` re-derives this file and fails on any drift.")
    A("")
    A("**Convention.** One token per sign row, in reading order. `|` = word divider / break. "
      "`?` = sign with no conventional value recorded in the DB. Tokens are the DB's "
      "`transliteration` column, lowercased — i.e. the Linear B transfer reading, not a "
      "Minoan reading.")
    A("")

    A("## Formula words (whole corpus, not just the vessel sites)")
    A("")
    A("| Slot | Signs | Occurrences | Inscriptions |")
    A("|------|-------|-------------|--------------|")
    for name, pat in SLOTS:
        hits = occ[name]
        ins = ", ".join(f"{g}@{i}" if i else g for g, i in hits[:12])
        more = f" … (+{len(hits) - 12})" if len(hits) > 12 else ""
        A(f"| {name} | `{' '.join(pat)}` | {len(hits)} | {ins}{more} |")
    A("")

    opening = occ[SLOTS[0][0]]
    n_open = len(opening)
    at0 = sum(1 for _, i in opening if i == 0)
    A(f"The opening occurs **{n_open}** times, at position 0 in **{at0}** of them. "
      f"It is the only slot whose pattern includes the logogram `A 301` — a syllabogram-only "
      f"transcription of this slot is a transcription error (see "
      f"`libation_recovered.md`'s corrections note).")
    A("")

    # slot order in texts carrying >= 2 slots
    ordered = []
    for g in sorted(signs):
        present = []
        for name, pat in SLOTS:
            idx = find(signs[g], pat)
            if idx:
                present.append((idx[0], name))
        if len(present) >= 2:
            ordered.append((g, present, present == sorted(present)))
    good = sum(1 for _, _, ok in ordered if ok)
    A(f"**Slot order.** In the {len(ordered)} texts carrying two or more formula slots, the "
      f"slots appear in the documented order in **{good} of {len(ordered)}**.")
    A("")

    A("## Other recurring elements")
    A("")
    A("| Element | Signs | Occurrences | Inscriptions |")
    A("|---------|-------|-------------|--------------|")
    for name, pat in EXTRA:
        hits = []
        for g in sorted(signs):
            for i in find(signs[g], pat):
                hits.append((g, i))
        ins = ", ".join(f"{g}@{i}" if i else g for g, i in hits[:12])
        A(f"| {name} | `{' '.join(pat)}` | {len(hits)} | {ins} |")
    A("")

    A("## Full sequences — the vessel sites")
    A("")
    for prefix, (label, _) in SITES.items():
        if prefix == "ARKH":
            A(f"### {label} ({prefix}) — no formula slots")
            A("")
        else:
            A(f"### {label} ({prefix})")
            A("")
        members = sorted(g for g in signs if g.startswith(prefix))
        if not members:
            A("- *(no inscriptions in the corpus)*")
            A("")
            continue
        for g in members:
            tk = tokens[g]
            marks = [name for name, pat in SLOTS if find(signs[g], pat)]
            note = f"  — {', '.join(marks)}" if marks else ""
            A(f"- **{g}** ({len(signs[g])} signs): `{' '.join(tk)}`{note}")
        A("")

    A("## Reading notes")
    A("")
    A("- Formula slots were found by sign-ID pattern across the whole corpus; the vessel-site "
      "sequences above are the genre's texts, and some formula carriers are not vessels "
      f"(the counts in the table are corpus-wide).")
    A("- `A 301` is a **logogram**, not a syllabogram: it stands inside the opening "
      "(`a-ta-i-*301-wa-ja`) and its 500-odd occurrences were once mis-attributed to the "
      "syllabogram AB 85 (`verification_audit.md`, Phase 12 addendum).")
    A("- Word dividers are rendered as `|` rather than omitted, so the token count of a line is "
      "the sign count of the inscription — the property the hand-written version could not "
      "guarantee.")
    A("- i-pi-na-ma rests on AB 39, whose value is `pi?` (uncertain) in `la_lb_mapping.csv`; the "
      "sign *sequence* is what the corpus supports.")
    A("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify; exit 1 on drift")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing")
    a = ap.parse_args()
    text = render()
    if a.stdout:
        print(text)
        return
    if a.check:
        if not OUT.exists():
            print("libation catalog: MISSING")
            sys.exit(1)
        have = OUT.read_text(encoding="utf-8")
        if have != text:
            import difflib
            diff = list(difflib.unified_diff(have.splitlines(), text.splitlines(),
                                             "committed", "regenerated", lineterm="", n=1))
            print("libation catalog: DRIFT — re-run pipeline/libation_catalog.py")
            print("\n".join(diff[:40]))
            sys.exit(1)
        print("libation catalog: byte-identical to the committed file")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
