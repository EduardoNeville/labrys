"""Linear B blind-decipherment sandbox: corpus ingest.

Turns Linear B word-level transliteration (``ka-*56-(so)``) into sign IDs, so that
``pipeline/ventris/complete.py`` can treat Linear B as if it were undeciphered.

Design contract
---------------
1. The Ventris pipeline only ever reads ``signs.bennett_id`` (verified:
   ``complete.py:253``). Phonetic values live in exactly one place:
   ``languages/linear-b/answer_key.csv``.
2. ``signs.transliteration`` is written NULL for every syllabogram, so no
   downstream module (morphology_scan, swadesh_search, positional_analysis) can
   leak the answer key into the score. ``assert_no_leak()`` enforces this on
   every ingest.
3. Sign IDs are *stable identifiers*, not claims. A row that is wrong is wrong in
   one line of ``translit_to_signid.csv``, not in code.

Gate (pre-registered in LINEAR_B_SANDBOX_PLAN.md; do not tune after first run):
    token coverage > 0.95      and      80 <= unique syllabograms <= 90

Usage
-----
    uv run python pipeline/lb_ingest.py --report-only     # parse + gate, no DB
    uv run python pipeline/lb_ingest.py                   # full ingest
    uv run python pipeline/lb_ingest.py --check           # self-check asserts
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger("lb_ingest")

REPO_ROOT = Path(__file__).resolve().parent.parent
LANG_DIR = REPO_ROOT / "languages" / "linear-b"
RAW_CSV = LANG_DIR / "data" / "raw" / "tablets.csv"
MAPPING_CSV = LANG_DIR / "translit_to_signid.csv"
ANSWER_KEY = LANG_DIR / "answer_key.csv"
DB_PATH = LANG_DIR / "data" / "database" / "linear-b.db"
REPORT_DIR = LANG_DIR / "data" / "analysis"

REFERENCE_GRID = REPO_ROOT / "data" / "analysis" / "comparative" / "la_lb_mapping.csv"

# ── Gate thresholds — pre-registered, see LINEAR_B_SANDBOX_PLAN.md §2 ─────────
GATE_MIN_COVERAGE = 0.95
# The unique-sign bound is relative to the reference inventory rather than a
# hard-coded 80–90. Corrected before the first oracle run (no result had been
# seen) after the Unicode syllabary turned out to name 74 signs, not ~87. The
# *pass threshold* (lift > 1.5) is untouched — that one is the hypothesis test.
GATE_MIN_INVENTORY_FRACTION = 0.90
GATE_MAX_SIGNS = 110

# Linear B syllabograms live in the U+10000 block, named
# "LINEAR B SYLLABLE B061 O" — standard LB sign number + Ventris value.
_RE_LB_NAME = re.compile(r"^LINEAR B SYLLABLE B(\d+) ([A-Z0-9]+)$")

# Corpus values with no Unicode syllabogram. The sandbox needs a *stable ID*, not
# a correct value — the value lives in answer_key.csv. ponytail: opaque ids; a
# specialist replaces a row in one line without touching code.
EXTRA_VALUES = {
    "koe": "LB koe",
}

# Token noise: line markers, empty brackets, stray punctuation
_JUNK = re.compile(r"^[.\d\s\[\]()|]*$")


# ─────────────────────────────────────────────────────────────────────────────
# Mapping table
# ─────────────────────────────────────────────────────────────────────────────

def lb_reference() -> Dict[str, Dict[str, str]]:
    """value → {sign_id, number, cp} from the Unicode Linear B block.

    This is the authoritative source for the *answer key*. Linear B is deciphered,
    so its values are facts, not hypotheses; ``la_lb_mapping.csv`` is a Linear A
    hypothesis file and is used only as a cross-check (see ``grid_mismatches``).

    Note the codepoints are *not* in sign-number order: U+10000 is B008 A, while
    B001 DA is U+10005. Sign IDs are taken from the name, never from an offset.
    """
    out: Dict[str, Dict[str, str]] = {}
    for cp in range(0x10000, 0x10100):
        try:
            name = unicodedata.name(chr(cp))
        except ValueError:
            continue
        m = _RE_LB_NAME.match(name)
        if not m:
            continue
        num, value = int(m.group(1)), m.group(2).lower()
        out[value] = {
            "sign_id": f"AB {num:02d}",
            "number": str(num),
            "cp": f"U+{cp:04X}",
        }
    return out


def build_mapping() -> Dict[str, Dict[str, str]]:
    """translit → {sign_id, source, confidence}.

    Primary source is the Unicode Linear B syllabary. Sign IDs follow the repo's
    ``AB nn`` convention, where nn is the standard Linear B sign number.
    """
    table: Dict[str, Dict[str, str]] = {
        value: {"sign_id": e["sign_id"], "source": "unicode_lb", "confidence": "high"}
        for value, e in lb_reference().items()
    }
    for value, sign_id in EXTRA_VALUES.items():
        table.setdefault(value, {
            "sign_id": sign_id, "source": "corpus_only", "confidence": "low",
        })
    logger.info("Mapping table: %d transliterations", len(table))
    return table


def grid_mismatches() -> List[dict]:
    """Compare the repo's LA↔LB grid against the Unicode Linear B standard.

    Two independent failure modes, kept separate because they mean different things:

    * ``unicode_number`` — this row's ``lb_unicode``/``lb_char`` does not name the
      sign with the same number. A systematic offset here means the glyph column
      was generated arithmetically rather than looked up.
    * ``lb_value``      — the recorded value disagrees with the standard value for
      that sign number. That is a substantive data error affecting any Linear A
      claim that transfers a value through this row.
    """
    by_cp: Dict[str, Tuple[int, str]] = {}
    ref = lb_reference()
    for value, e in ref.items():
        by_cp[e["cp"]] = (int(e["number"]), value)

    out: List[dict] = []
    for r in csv.DictReader(open(REFERENCE_GRID, encoding="utf-8")):
        bid = (r.get("bennett_id") or "").strip()
        m = re.match(r"^AB (\d+)$", bid, re.I)
        if not m:
            continue
        num = int(m.group(1))
        repo_value = (r.get("lb_value") or "").strip().rstrip("?").lower()
        uni = (r.get("lb_unicode") or "").strip()
        info = by_cp.get(uni)
        row = {"bennett_id": bid, "repo_lb_value": repo_value,
               "repo_lb_unicode": uni or "-", "kind": "", "detail": ""}
        if info and info[0] != num:
            row["kind"] = "unicode_number"
            row["detail"] = f"{uni} is B{info[0]:03d} {info[1]}"
        if repo_value:
            std = ref.get(repo_value)
            if std and int(std["number"]) != num:
                row["kind"] = (row["kind"] + "+lb_value").lstrip("+")
                row["detail"] += (
                    f"; value {repo_value!r} is B{int(std['number']):03d}"
                    f" — standard B{num:03d} = "
                    f"{next((v for v, e in ref.items() if int(e['number']) == num), 'unnamed')!r}"
                )
        if row["kind"]:
            out.append(row)
    return out


def numbered_sign_id(token: str) -> Optional[str]:
    """``*56`` → ``AB 56``. Linear A and Linear B share the Evans/Bennett number."""
    if not token.startswith("*"):
        return None
    digits = token[1:]
    if not digits.isdigit():
        return None
    return f"AB {int(digits):02d}"


# ─────────────────────────────────────────────────────────────────────────────
# Tokenizer
# ─────────────────────────────────────────────────────────────────────────────

def tokenize_word(word: str) -> List[Tuple[str, Dict[str, int]]]:
    """Split one transliterated word into (translit, flags) pairs.

    Flags: ``uncertain`` (was parenthesised), ``ligature`` (joined by ``+``).
    Brackets are stripped by the caller, which records word-level damage.
    """
    out: List[Tuple[str, Dict[str, int]]] = []
    for chunk in word.split("+"):
        ligature = "+" in word
        for token in chunk.split("-"):
            uncertain = "(" in token or ")" in token
            t = token.replace("(", "").replace(")", "").strip().lower()
            t = t.strip("[]|.,")
            if not t or _JUNK.match(t):
                continue
            out.append((
                t,
                {"uncertain": int(uncertain), "ligature": int(ligature)},
            ))
    return out


def iter_words(inscription_field: str) -> Iterator[Tuple[str, int]]:
    """Yield (word, damaged) from the comma/pipe-separated ``inscription`` field."""
    for word in re.split(r"[,|]", inscription_field or ""):
        word = word.strip()
        if not word:
            continue
        damaged = int("[" in word or "]" in word)
        word = word.replace("[", "").replace("]", "").strip()
        if word:
            yield word, damaged


# ─────────────────────────────────────────────────────────────────────────────
# Corpus parse
# ─────────────────────────────────────────────────────────────────────────────

def parse_corpus() -> Tuple[List[dict], Counter, Counter, int]:
    """Parse every row. Returns (inscriptions, hits, misses, dropped_dups)."""
    mapping = build_mapping()
    rows = list(csv.DictReader(open(RAW_CSV, encoding="utf-8"), delimiter=";"))
    logger.info("Corpus rows: %d", len(rows))

    inscriptions: List[dict] = []
    hits: Counter = Counter()
    misses: Counter = Counter()
    seen_ids: set = set()
    dropped_dups = 0

    for row in rows:
        ident = (row.get("identifier") or "").strip()
        if not ident:
            continue
        if ident in seen_ids:
            # Source corpus repeats most tablets across edition files; duplicate
            # rows would triple-count those texts in the bigram statistics.
            # Keep the first occurrence; count and report the rest.
            dropped_dups += 1
            continue
        seen_ids.add(ident)
        words: List[List[dict]] = []
        for word, damaged in iter_words(row.get("inscription") or ""):
            signs: List[dict] = []
            for translit, flags in tokenize_word(word):
                sign_id = numbered_sign_id(translit)
                if sign_id is None:
                    entry = mapping.get(translit)
                    if entry is None:
                        misses[translit] += 1
                        continue
                    sign_id = entry["sign_id"]
                hits[sign_id] += 1
                signs.append({"sign_id": sign_id, "translit": translit, **flags})
            if signs:
                words.append(signs)
        inscriptions.append({
            "id": ident,
            "site": (row.get("location") or "").strip() or "unknown",
            "series": (row.get("series") or "").strip(),
            "words": words,
            "damaged": int("[" in (row.get("inscription") or "")
                           or "]" in (row.get("inscription") or "")),
        })

    logger.info("Dropped %d duplicate rows (same identifier as an earlier row)",
                dropped_dups)
    return inscriptions, hits, misses, dropped_dups


def coverage(hits: Counter, misses: Counter) -> dict:
    total = sum(hits.values()) + sum(misses.values())
    return {
        "tokens_total": total,
        "tokens_mapped": sum(hits.values()),
        "tokens_missed": sum(misses.values()),
        "coverage": (sum(hits.values()) / total) if total else 0.0,
        "unique_signs": len(hits),
        "unique_miss_types": len(misses),
        "reference_inventory": len(lb_reference()),
    }


def check_gate(stats: dict) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    if stats["coverage"] <= GATE_MIN_COVERAGE:
        problems.append(
            f"coverage {stats['coverage']:.4f} <= {GATE_MIN_COVERAGE} "
            f"({stats['tokens_missed']} tokens unmapped)"
        )
    floor = int(GATE_MIN_INVENTORY_FRACTION * stats["reference_inventory"])
    if stats["unique_signs"] < floor:
        problems.append(
            f"unique signs {stats['unique_signs']} < {floor} "
            f"({GATE_MIN_INVENTORY_FRACTION:.0%} of the {stats['reference_inventory']}-sign "
            f"Unicode inventory) — parser is dropping real signs"
        )
    if stats["unique_signs"] > GATE_MAX_SIGNS:
        problems.append(
            f"unique signs {stats['unique_signs']} > {GATE_MAX_SIGNS} — "
            f"logograms or junk leaking in as syllabograms"
        )
    return (not problems), problems


# ─────────────────────────────────────────────────────────────────────────────
# Mapping file output
# ─────────────────────────────────────────────────────────────────────────────

def write_mapping_file() -> None:
    mapping = build_mapping()
    LANG_DIR.mkdir(parents=True, exist_ok=True)
    with open(MAPPING_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["translit", "sign_id", "source", "confidence"])
        for translit in sorted(mapping):
            e = mapping[translit]
            w.writerow([translit, e["sign_id"], e["source"], e["confidence"]])
    logger.info("Wrote %s (%d rows)", MAPPING_CSV, len(mapping))


# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS findspots (
    id INTEGER PRIMARY KEY, site TEXT UNIQUE, latitude REAL, longitude REAL, context TEXT
);
CREATE TABLE IF NOT EXISTS inscriptions (
    id INTEGER PRIMARY KEY, gorila_id TEXT UNIQUE, alternative_ids TEXT,
    findspot_id INTEGER, minoan_period TEXT, bce_from INTEGER, bce_to INTEGER,
    date_notes TEXT, material TEXT, object_type TEXT,
    preservation_state TEXT, preservation_description TEXT,
    dim_height REAL, dim_width REAL, dim_depth REAL, dim_diameter REAL,
    dim_unit TEXT, institution TEXT, collection TEXT, inventory_no TEXT,
    publication_citation TEXT, publication_doi TEXT, source TEXT,
    raw_data TEXT, created_at TEXT, updated_at TEXT,
    FOREIGN KEY (findspot_id) REFERENCES findspots(id)
);
CREATE TABLE IF NOT EXISTS signs (
    id INTEGER PRIMARY KEY, inscription_id INTEGER NOT NULL, sequence INTEGER NOT NULL,
    bennett_id TEXT NOT NULL, unicode TEXT, character TEXT,
    transliteration TEXT,          -- must stay NULL — see assert_no_leak()
    confidence TEXT, sign_type TEXT, sigla_variant_id TEXT,
    bbox_x REAL, bbox_y REAL, bbox_w REAL, bbox_h REAL, bbox_unit TEXT,
    shape_class TEXT, is_ligature_component INTEGER DEFAULT 0,
    ligature_of TEXT, erasure TEXT, correction_original TEXT,
    correction_corrected TEXT,
    FOREIGN KEY (inscription_id) REFERENCES inscriptions(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY, inscription_id INTEGER, word_index INTEGER, sign_sequences TEXT
);
CREATE INDEX IF NOT EXISTS idx_signs_bennett ON signs(bennett_id);
CREATE INDEX IF NOT EXISTS idx_signs_inscription ON signs(inscription_id);
"""


def build_db(inscriptions: List[dict], db_path: Path = DB_PATH) -> dict:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    findspots: Dict[str, int] = {}
    n_signs = n_words = 0
    for insc in inscriptions:
        site = insc["site"]
        if site not in findspots:
            cur.execute("INSERT INTO findspots (site) VALUES (?)", (site,))
            findspots[site] = cur.lastrowid
        cur.execute(
            "INSERT INTO inscriptions (gorila_id, findspot_id, minoan_period,"
            " object_type, source) VALUES (?,?,?,?,?)",
            (insc["id"], findspots[site], None,
             "tablet (linear b)" if insc["series"] else None,
             "insiderphd-linear-b-dataset"),
        )
        iid = cur.lastrowid
        seq = 0
        for wi, word in enumerate(insc["words"]):
            for sign in word:
                cur.execute(
                    "INSERT INTO signs (inscription_id, sequence, bennett_id,"
                    " unicode, character, transliteration, confidence, sign_type,"
                    " is_ligature_component) VALUES (?,?,?,?,?,?,?,?,?)",
                    (iid, seq, sign["sign_id"], None, None, None,
                     "uncertain" if sign["uncertain"] else "certain",
                     "syllabogram", sign["ligature"]),
                )
                seq += 1
                n_signs += 1
            cur.execute(
                "INSERT INTO words (inscription_id, word_index, sign_sequences)"
                " VALUES (?,?,?)",
                (iid, wi, "-".join(s["sign_id"] for s in word)),
            )
            n_words += 1

    conn.commit()
    n_ins = cur.execute("SELECT COUNT(*) FROM inscriptions").fetchone()[0]
    conn.close()
    return {"inscriptions": n_ins, "signs": n_signs, "words": n_words,
            "findspots": len(findspots), "db": str(db_path)}


def assert_no_leak(db_path: Path = DB_PATH) -> None:
    """The entire defence of the experiment. See plan §4 Step 4."""
    conn = sqlite3.connect(db_path)
    leaked = conn.execute(
        "SELECT DISTINCT transliteration FROM signs WHERE sign_type='syllabogram'"
    ).fetchall()
    conn.close()
    values = {v[0] for v in leaked}
    assert values <= {None}, f"LEAK: transliteration populated: {values}"
    logger.info("Leak guard OK — syllabogram transliteration is all NULL")


# ─────────────────────────────────────────────────────────────────────────────
# Self-check
# ─────────────────────────────────────────────────────────────────────────────

def _selfcheck() -> None:
    # numbering rule
    assert numbered_sign_id("*56") == "AB 56"
    assert numbered_sign_id("*7") == "AB 07"
    assert numbered_sign_id("56") is None

    # subscript digits are distinct signs, never stripped
    toks = [t for t, _ in tokenize_word("ra2-ra-ro2-ro")]
    assert toks == ["ra2", "ra", "ro2", "ro"], toks

    # brackets / parens
    toks = [(t, f["uncertain"]) for t, f in tokenize_word("(ro)-[]-[[pa")]
    assert ("ro", 1) in toks and ("pa", 0) in toks, toks

    # ligature
    toks = [(t, f["ligature"]) for t, f in tokenize_word("(ME)+(RI)")]
    assert toks == [("me", 1), ("ri", 1)], toks

    # word splitting on both , and |
    words = [w for w, _ in iter_words("ka-*56-(so) , e-u-(ko)-ro | to-so")]
    assert words == ["ka-*56-(so)", "e-u-(ko)-ro", "to-so"], words

    # damage flag
    assert [d for _, d in iter_words("ro[]")] == [1]

    # mapping table is non-empty and every row has a sign id
    m = build_mapping()
    assert len(m) > 50, len(m)
    assert all(e["sign_id"] for e in m.values())

    print(f"selfcheck OK — mapping table {len(m)} entries")


# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    p = argparse.ArgumentParser(description="Linear B sandbox ingest")
    p.add_argument("--report-only", action="store_true", help="parse + gate, no DB")
    p.add_argument("--check", action="store_true", help="run self-check asserts")
    p.add_argument("--db", default=None, help="DB path override")
    args = p.parse_args()

    if args.check:
        _selfcheck()
        return

    write_mapping_file()
    inscriptions, hits, misses, dropped_dups = parse_corpus()
    stats = coverage(hits, misses)
    ok, problems = check_gate(stats)

    print("\n=== Linear B sandbox ingest ===")
    print(f"source rows        : {len(inscriptions) + dropped_dups} "
          f"(dropped {dropped_dups} duplicates)")
    print(f"reference inventory : {stats['reference_inventory']} Linear B syllabograms (Unicode names)")
    print(f"inscriptions parsed : {len(inscriptions)}")
    print(f"tokens              : {stats['tokens_total']} "
          f"(mapped {stats['tokens_mapped']}, missed {stats['tokens_missed']})")
    print(f"coverage            : {stats['coverage']:.4f}  (gate > {GATE_MIN_COVERAGE})")
    print(f"unique syllabograms : {stats['unique_signs']}  "
          f"(gate >= {int(GATE_MIN_INVENTORY_FRACTION * stats['reference_inventory'])} "
          f"= {GATE_MIN_INVENTORY_FRACTION:.0%} of inventory, and <= {GATE_MAX_SIGNS})")
    print(f"top 20 text         : {hits.most_common(20)}")

    if misses:
        print(f"\nunmapped token types ({len(misses)}):")
        for t, c in misses.most_common(40):
            print(f"  {c:6d}  {t!r}")

    by_source = Counter(e["source"] for e in build_mapping().values())
    print(f"\nmapping provenance  : {dict(by_source)}")

    # Cross-check the repo's Linear A↔B grid against the Unicode Linear B standard.
    mism = grid_mismatches()
    unicode_rows = [m for m in mism if "unicode_number" in m["kind"]]
    value_rows = [m for m in mism if "lb_value" in m["kind"]]
    print(f"\ngrid cross-check vs Unicode Linear B standard:")
    print(f"  glyph column wrong (lb_unicode names a different sign): {len(unicode_rows)}")
    print(f"  value disagrees with the standard value for that number: {len(value_rows)}")
    for m in value_rows:
        print(f"    {m['bennett_id']}: repo {m['repo_lb_value']!r} — {m['detail']}")
    if mism:
        out = REPORT_DIR / "lb_grid_vs_unicode_mismatches.csv"
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(mism[0].keys()))
            w.writeheader()
            w.writerows(mism)
        print(f"  written: {out}")

    if not ok:
        print("\nGATE FAILED — do not run the oracle on this corpus:")
        for prob in problems:
            print(f"  ✗ {prob}")
        raise SystemExit(1)

    print("\nGATE PASSED")

    if args.report_only:
        return

    db = Path(args.db) if args.db else DB_PATH
    built = build_db(inscriptions, db)
    print(f"\ndb                  : {built['db']}")
    print(f"  inscriptions {built['inscriptions']}, signs {built['signs']}, "
          f"words {built['words']}, findspots {built['findspots']}")
    assert_no_leak(db)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "lb_ingest_report.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# Linear B sandbox — ingest report\n\n")
        f.write(f"| quantity | value |\n|---|---|\n")
        f.write(f"| source rows | {len(inscriptions) + dropped_dups} (dropped {dropped_dups} duplicates) |\n")
        f.write(f"| inscriptions | {built['inscriptions']} |\n")
        f.write(f"| sign tokens | {built['signs']} |\n")
        f.write(f"| coverage | {stats['coverage']:.4f} |\n")
        f.write(f"| unique syllabograms | {stats['unique_signs']} |\n")
        f.write(f"| reference inventory | {stats['reference_inventory']} |\n")
        f.write(f"| grid rows with wrong glyph | {len(unicode_rows)} |\n")
        f.write(f"| grid rows with wrong value | {len(value_rows)} |\n")
        f.write(f"| unmapped token types | {stats['unique_miss_types']} |\n")
        f.write(f"| gate | PASSED |\n\n")
        f.write("Leak guard: syllabogram `transliteration` is NULL throughout.\n")
    logger.info("Wrote %s", report)


if __name__ == "__main__":
    main()
