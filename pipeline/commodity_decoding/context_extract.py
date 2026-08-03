#!/usr/bin/env python3
"""
Commodity Context Extraction for Linear A
==========================================
Extract ±3 sign windows around commodity logograms, group by commodity class,
and build per-commodity frequency profiles.

Reads: data/database/lineara_full.db
Writes: data/analysis/commodity_decoding/logogram_contexts.csv
        data/analysis/commodity_decoding/commodity_signatures.csv

Key questions:
  - What syllabograms appear near specific commodity logograms?
  - Are there syllabogram sequences that uniquely identify a commodity class?
  - Do the surrounding signs form recognizable patterns (quantities, modifiers)?

Method:
  1. Scan all inscriptions for logograms with known/inferred commodity meanings.
  2. For each logogram occurrence, extract the ±N sign window (N=3 by default).
  3. Classify each sign in the window as syllabogram, numeral, fraction, etc.
  4. Group by commodity class and build frequency profiles.
"""

from __future__ import annotations

import csv
import os
import re
from collections import defaultdict, Counter
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "lineara_full.db")
OUT_DIR = os.path.join(BASE_DIR, "data", "analysis", "commodity_decoding")
os.makedirs(OUT_DIR, exist_ok=True)

# ML predictions for UNCERTAIN signs
ML_PREDICTIONS_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "ml", "uncertain_predictions.csv"
)

# ---------------------------------------------------------------------------
# Commodity classification
# ---------------------------------------------------------------------------


def classify_commodity(bennett_id: str, transliteration: str) -> str:
    """Classify a logogram into a commodity class based on transliteration hints.

    Returns commodity class string, or empty string if unclassified.
    """
    t = (transliteration or "").strip().upper()

    # Direct commodity abbreviations in transliteration
    if "VIN" in t:
        return "WINE"
    if "OLE" in t:
        return "OLIVE_OIL"
    if "OLIV" in t:
        return "OLIVES"
    if "GRA" in t:
        return "GRAIN"
    if "TELA" in t:
        return "CLOTH"
    if "VIR" in t:
        return "MANPOWER"
    if "CAP" in t:
        return "LIVESTOCK"
    if "HIDE" in t:
        return "HIDES"
    if "AROM" in t:
        return "AROMATICS"

    # VASE-type logograms: classify by ID
    if bennett_id.startswith("VASE"):
        return "VESSELS"

    # Some logograms have compound IDs that hint at commodity
    if bennett_id.startswith("A 3"):
        # Check for known scholarly commodity IDs
        # Many A 3xx logograms are commodities; we use known mappings:
        known_a3xx = {
            "A 301": "PERSONNEL",
            "A 302": "LIVESTOCK",
            "A 303": "LIVESTOCK",
            "A 304": "LIVESTOCK",
            "A 305": "LIVESTOCK",
            "A 306": "LIVESTOCK",
            "A 307": "LIVESTOCK",
            "A 308": "HIDES",
            "A 309": "GRAIN",     # barley?
            "A 310": "WINE",       # wine?
            "A 311": "OLIVE_OIL",  # oil?
            "A 312": "UNKNOWN_COMMODITY",
            "A 313": "UNKNOWN_COMMODITY",
            "A 314": "UNKNOWN_COMMODITY",
            "A 316": "UNKNOWN_COMMODITY",
            "A 317": "UNKNOWN_COMMODITY",
            "A 318": "UNKNOWN_COMMODITY",
            "A 319": "UNKNOWN_COMMODITY",
            "A 320": "UNKNOWN_COMMODITY",
            "A 321": "UNKNOWN_COMMODITY",
            "A 322": "UNKNOWN_COMMODITY",
            "A 325": "UNKNOWN_COMMODITY",
            "A 326": "UNKNOWN_COMMODITY",
            "A 327": "VESSELS",
            "A 328": "UNKNOWN_COMMODITY",
            "A 329": "UNKNOWN_COMMODITY",
            "A 331": "UNKNOWN_COMMODITY",
            "A 332": "UNKNOWN_COMMODITY",
            "A 333": "VESSELS",
            "A 334": "UNKNOWN_COMMODITY",
            "A 335": "VESSELS",
            "A 338": "VESSELS",
            "A 339": "VESSELS",
            "A 340": "UNKNOWN_COMMODITY",
            "A 342": "UNKNOWN_COMMODITY",
            "A 343": "UNKNOWN_COMMODITY",
            "A 344": "UNKNOWN_COMMODITY",
            "A 345": "UNKNOWN_COMMODITY",
            "A 346": "UNKNOWN_COMMODITY",
            "A 347": "UNKNOWN_COMMODITY",
            "A 348": "UNKNOWN_COMMODITY",
            "A 349": "UNKNOWN_COMMODITY",
            "A 350": "UNKNOWN_COMMODITY",
            "A 351": "UNKNOWN_COMMODITY",
            "A 352": "UNKNOWN_COMMODITY",
            "A 353": "UNKNOWN_COMMODITY",
            "A 354": "UNKNOWN_COMMODITY",
            "A 355": "UNKNOWN_COMMODITY",
            "A 356": "UNKNOWN_COMMODITY",
            "A 357": "UNKNOWN_COMMODITY",
            "A 358": "UNKNOWN_COMMODITY",
            "A 359": "UNKNOWN_COMMODITY",
            "A 360": "UNKNOWN_COMMODITY",
            "A 361": "UNKNOWN_COMMODITY",
            "A 362": "UNKNOWN_COMMODITY",
            "A 363": "UNKNOWN_COMMODITY",
            "A 364": "GRAIN",
            "A 365": "UNKNOWN_COMMODITY",
            "A 366": "UNKNOWN_COMMODITY",
            "A 367": "UNKNOWN_COMMODITY",
            "A 368": "UNKNOWN_COMMODITY",
            "A 369": "UNKNOWN_COMMODITY",
            "A 370": "UNKNOWN_COMMODITY",
            "A 371": "UNKNOWN_COMMODITY",
            "A 372": "UNKNOWN_COMMODITY",
            "A 373": "UNKNOWN_COMMODITY",
            "A 374": "UNKNOWN_COMMODITY",
            "A 375": "UNKNOWN_COMMODITY",
            "A 376": "UNKNOWN_COMMODITY",
            "A 377": "UNKNOWN_COMMODITY",
            "A 378": "UNKNOWN_COMMODITY",
            "A 379": "UNKNOWN_COMMODITY",
            "A 380": "UNKNOWN_COMMODITY",
            "A 381": "OLIVE_OIL",
            "A 382": "UNKNOWN_COMMODITY",
            "A 383": "UNKNOWN_COMMODITY",
            "A 384": "UNKNOWN_COMMODITY",
            "A 385": "UNKNOWN_COMMODITY",
            "A 386": "GRAIN",
            "A 387": "UNKNOWN_COMMODITY",
            "A 388": "UNKNOWN_COMMODITY",
            "A 389": "UNKNOWN_COMMODITY",
            "A 390": "UNKNOWN_COMMODITY",
            "A 391": "UNKNOWN_COMMODITY",
            "A 392": "UNKNOWN_COMMODITY",
            "A 393": "UNKNOWN_COMMODITY",
            "A 394": "MANPOWER",
            "A 395": "MANPOWER",
            "A 396": "UNKNOWN_COMMODITY",
            "A 397": "UNKNOWN_COMMODITY",
            "A 398": "UNKNOWN_COMMODITY",
            "A 399": "GRAIN",
            "A 400": "GRAIN",
            "A 401": "UNKNOWN_COMMODITY",
            "A 402": "GRAIN",
        }
        if bennett_id in known_a3xx:
            return known_a3xx[bennett_id]
        return "UNKNOWN_COMMODITY"

    return "UNCLASSIFIED"


def _sign_is_syllabogram(bennett_id: str, sign_type: str) -> bool:
    """Determine if a sign is a true syllabogram (AB-range Bennett ID)."""
    if sign_type == "syllabogram" and bennett_id and bennett_id.startswith("AB "):
        return True
    return False


def _is_ml_uncertain(bennett_id: str, ml_map: dict[str, dict]) -> bool:
    """Check if a Bennett ID is among the UNCERTAIN (not CONFIRM) signs via ML predictions."""
    return bennett_id in ml_map


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------


def extract_contexts(window: int = 3) -> tuple[list[dict], dict[str, dict]]:
    """Extract sign context windows around commodity logograms.

    Returns:
        (context_rows, commodity_profiles)
        context_rows: list of dicts, each representing one logogram occurrence
            with its ±window context signs.
        commodity_profiles: dict[commodity_class, {
            'syllabograms': Counter of adjacent syllabogram transliterations,
            'syllabogram_bennett': Counter of adjacent syllabogram bennett_ids,
            'numerals': Counter of adjacent numeral values,
            'fractions': Counter of adjacent fraction signs,
            'total_occurrences': int,
            'distinct_logograms': set of bennett_ids,
            'context_sequences': list of tokenized sequences around logogram,
        }]
    """
    import sqlite3

    # Load ML predictions for UNCERTAIN signs
    ml_map: dict[str, dict] = {}
    if os.path.exists(ML_PREDICTIONS_PATH):
        with open(ML_PREDICTIONS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_map[row["bennett_id"]] = row
    print(f"Loaded {len(ml_map)} ML predictions for UNCERTAIN signs.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Load all signs with inscription metadata
    cur.execute("""
        SELECT
            s.id, s.inscription_id, s.sequence, s.bennett_id,
            s.sign_type, s.transliteration, s.character,
            i.gorila_id, i.object_type, i.material,
            f.site
        FROM signs s
        JOIN inscriptions i ON s.inscription_id = i.id
        LEFT JOIN findspots f ON i.findspot_id = f.id
        ORDER BY s.inscription_id, s.sequence
    """)
    all_rows = cur.fetchall()
    print(f"Loaded {len(all_rows)} sign rows.")

    # Group signs by inscription
    inscriptions: dict[int, list[dict]] = defaultdict(list)
    for row in all_rows:
        d = dict(row)
        inscriptions[d["inscription_id"]].append(d)

    # Build accessible sign lookup: (ins_id, seq) -> sign dict
    sign_lookup: dict[tuple[int, int], dict] = {}
    for d in all_rows:
        s = dict(d)
        sign_lookup[(s["inscription_id"], s["sequence"])] = s

    context_rows: list[dict] = []
    commodity_profiles: dict[str, dict] = {}

    def _get_or_create_profile(comm: str) -> dict:
        if comm not in commodity_profiles:
            commodity_profiles[comm] = {
                "syllabograms": Counter(),
                "syllabogram_bennett": Counter(),
                "numerals": Counter(),
                "fractions": Counter(),
                "total_occurrences": 0,
                "distinct_logograms": set(),
                "context_sequences": [],
            }
        return commodity_profiles[comm]

    # Process each inscription
    for ins_id, sign_list in inscriptions.items():
        meta = sign_list[0]
        gorila_id = meta["gorila_id"] or ""
        site = meta["site"] or "unknown"
        obj_type = meta["object_type"] or ""

        # Find logogram occurrences with commodity classification
        for i, sign in enumerate(sign_list):
            if sign["sign_type"] != "logogram":
                continue

            bennett_id = sign["bennett_id"] or ""
            if not bennett_id:
                continue

            translit = sign["transliteration"] or ""
            commodity = classify_commodity(bennett_id, translit)

            if not commodity or commodity in ("UNCLASSIFIED",):
                continue

            seq = sign["sequence"]

            # Extract ±window signs
            before_signs = []
            after_signs = []
            before_seq = seq - 1
            while len(before_signs) < window and before_seq >= 0:
                bs = sign_lookup.get((ins_id, before_seq))
                if bs:
                    before_signs.insert(0, bs)
                before_seq -= 1
            after_seq = seq + 1
            while len(after_signs) < window and after_seq <= max(
                s["sequence"] for s in sign_list
            ):
                as_ = sign_lookup.get((ins_id, after_seq))
                if as_:
                    after_signs.append(as_)
                after_seq += 1

            # Build context row
            context_row = {
                "gorila_id": gorila_id,
                "site": site,
                "object_type": obj_type,
                "commodity_class": commodity,
                "logogram_bennett": bennett_id,
                "logogram_transliteration": translit,
                "logogram_sequence": seq,
            }
            for j, s in enumerate(before_signs):
                context_row[f"before_{-j-1}_bennett"] = s["bennett_id"]
                context_row[f"before_{-j-1}_translit"] = s["transliteration"]
                context_row[f"before_{-j-1}_type"] = s["sign_type"]
            for j, s in enumerate(after_signs):
                context_row[f"after_{j+1}_bennett"] = s["bennett_id"]
                context_row[f"after_{j+1}_translit"] = s["transliteration"]
                context_row[f"after_{j+1}_type"] = s["sign_type"]
            context_rows.append(context_row)

            # Update commodity profile
            profile = _get_or_create_profile(commodity)
            profile["total_occurrences"] += 1
            profile["distinct_logograms"].add(bennett_id)

            # Count adjacent syllabograms
            token_seq = []
            for s in before_signs + after_signs:
                st = s["sign_type"]
                bid = (s.get("bennett_id") or "").strip()
                tlit = (s.get("transliteration") or "").strip()

                if _sign_is_syllabogram(bid, st) and tlit:
                    profile["syllabograms"][tlit] += 1
                    profile["syllabogram_bennett"][bid] += 1
                    # Mark if this is an UNCERTAIN sign
                    is_uncertain = _is_ml_uncertain(bid, ml_map)
                    token_seq.append(f"{tlit}{'[U]' if is_uncertain else ''}")
                elif st == "numeral" or st == "fraction":
                    if tlit:
                        profile["fractions" if st == "fraction" else "numerals"][tlit] += 1
                    token_seq.append(f"[{st[:4]}:{tlit}]")
                elif st == "logogram":
                    token_seq.append(f"[LOGO:{bid}]")
                else:
                    token_seq.append(f"[{st[:4]}]")

            profile["context_sequences"].append("-".join(token_seq))

    conn.close()

    # Convert sets to counts for serialization
    for comm in commodity_profiles:
        commodity_profiles[comm]["distinct_logogram_count"] = len(
            commodity_profiles[comm]["distinct_logograms"]
        )
        commodity_profiles[comm]["distinct_logograms"] = sorted(
            list(commodity_profiles[comm]["distinct_logograms"])
        )

    print(f"Extracted {len(context_rows)} logogram context windows.")
    print(f"Grouped into {len(commodity_profiles)} commodity classes:")
    for comm, prof in sorted(commodity_profiles.items(),
                             key=lambda x: -x[1]["total_occurrences"]):
        print(f"  {comm}: {prof['total_occurrences']} occurrences, "
              f"{prof['distinct_logogram_count']} distinct logograms")

    return context_rows, commodity_profiles


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    """Write a list of dicts to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    print("=" * 60)
    print("Commodity Context Extraction — Phase 2a")
    print("=" * 60)

    context_rows, commodity_profiles = extract_contexts(window=3)

    # --- Output 1: logogram_contexts.csv ---
    # Dynamically determine fieldnames from first row
    if context_rows:
        fieldnames = list(context_rows[0].keys())
    else:
        fieldnames = [
            "gorila_id", "site", "object_type", "commodity_class",
            "logogram_bennett", "logogram_transliteration", "logogram_sequence",
        ]
    write_csv(
        os.path.join(OUT_DIR, "logogram_contexts.csv"),
        context_rows,
        fieldnames,
    )
    print(f"Wrote {len(context_rows)} rows to logogram_contexts.csv")

    # --- Output 2: commodity_signatures.csv ---
    # Load ML map for UNCERTAIN sign checking
    ml_map_local: dict[str, dict] = {}
    if os.path.exists(ML_PREDICTIONS_PATH):
        with open(ML_PREDICTIONS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_map_local[row["bennett_id"]] = row

    sig_rows = []
    for comm, prof in sorted(commodity_profiles.items()):
        total_syll = sum(prof["syllabograms"].values())
        top_sylls = prof["syllabograms"].most_common(15)
        top_syll_strs = []
        for tlit, cnt in top_sylls:
            pct = round(100 * cnt / total_syll, 1) if total_syll else 0
            top_syll_strs.append(f"{tlit}({cnt},{pct}%)")

        top_bennetts = prof["syllabogram_bennett"].most_common(10)
        top_bennett_strs = []
        uncertain_in_top: list[str] = []
        for bid, cnt in top_bennetts:
            top_bennett_strs.append(f"{bid}({cnt})")
            if bid in ml_map_local:
                uncertain_in_top.append(bid)

        sig_rows.append({
            "commodity_class": comm,
            "total_occurrences": prof["total_occurrences"],
            "distinct_logogram_count": prof["distinct_logogram_count"],
            "distinct_logograms": "; ".join(str(l) for l in prof["distinct_logograms"]),
            "total_adjacent_syllabograms": total_syll,
            "top_syllabograms": "; ".join(top_syll_strs),
            "top_syllabogram_bennetts": "; ".join(top_bennett_strs),
            "uncertain_signs_in_top10": "; ".join(uncertain_in_top),
            "unique_context_sequences": "; ".join(
                list(set(prof["context_sequences"]))[:20]
            ),
        })

    write_csv(
        os.path.join(OUT_DIR, "commodity_signatures.csv"),
        sig_rows,
        [
            "commodity_class", "total_occurrences", "distinct_logogram_count",
            "distinct_logograms", "total_adjacent_syllabograms",
            "top_syllabograms", "top_syllabogram_bennetts",
            "uncertain_signs_in_top10", "unique_context_sequences",
        ],
    )
    print(f"Wrote {len(sig_rows)} rows to commodity_signatures.csv")

    print("\nDone!")


if __name__ == "__main__":
    main()
