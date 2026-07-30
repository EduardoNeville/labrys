#!/usr/bin/env python3
"""
Deep Loanword Mining
====================
Performs a deeper, semantically-validated analysis of Minoan loanwords in
Greek using the Phase 3 results as a starting point.

For each of the ~471 match records, enriches with:
  a) Database context — surrounding signs from lineara_full.db
  b) Co-occurring logograms (commodities, measures)
  c) Text type (administrative vs. religious)
  d) Findspot distribution

Outputs:
  data/analysis/comparative/deep_loanword_matches.csv  — enriched matches
  data/analysis/comparative/minoan_shadow_lexicon.csv  — curated word list
  data/analysis/comparative/nth_ss_analysis.csv        — suffix pattern analysis
  data/analysis/comparative/deep_loanword_report.md    — detailed report
"""

from __future__ import annotations

import csv
import json
import math
import re
import sqlite3
import statistics
import sys
from collections import defaultdict, Counter, OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DB_PATH = PROJECT_ROOT / "data/database/lineara_full.db"
INPUT_CSV = PROJECT_ROOT / "data/analysis/linguistic/loanword_matches.csv"
OUTPUT_DIR = PROJECT_ROOT / "data/analysis/comparative"
OUTPUT_ENRICHED = OUTPUT_DIR / "deep_loanword_matches.csv"
OUTPUT_LEXICON = OUTPUT_DIR / "minoan_shadow_lexicon.csv"
OUTPUT_NTH_SS = OUTPUT_DIR / "nth_ss_analysis.csv"
OUTPUT_REPORT = OUTPUT_DIR / "deep_loanword_report.md"

# Thresholds
SHADOW_CONFIDENCE_THRESHOLD = 45.0  # minimum for shadow lexicon inclusion
TOP_N_DEEP_DIVES = 10

# Linear AB signs that are logograms for commodities — used for semantic context
COMMODITY_KEYWORDS: Set[str] = {
    "GRA", "VIN", "OLE", "LANA", "FIC", "VAS", "AROM",
    "MUL", "TUN", "CYP", "KIT", "TELA", "PUR", "SES",
    "CROC", "OLE+U", "GRA+U", "VIN+U", "NI", "MA",
}

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    """Open a read-only connection to the database."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_inscription_details(conn: sqlite3.Connection, ins_id: int) -> Optional[Dict]:
    """Fetch full inscription record + findspot."""
    cur = conn.execute("""
        SELECT i.*, f.site AS findspot_site, f.context AS findspot_context,
               f.latitude, f.longitude
        FROM inscriptions i
        LEFT JOIN findspots f ON i.findspot_id = f.id
        WHERE i.id = ?
    """, (ins_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)


def get_signs_for_inscription(conn: sqlite3.Connection, ins_id: int) -> List[Dict]:
    """Fetch all signs for an inscription, ordered by sequence."""
    cur = conn.execute("""
        SELECT * FROM signs
        WHERE inscription_id = ?
        ORDER BY sequence ASC
    """, (ins_id,))
    return [dict(r) for r in cur.fetchall()]


def get_sign_semantics(conn: sqlite3.Connection, sign_id: int) -> Optional[Dict]:
    """Fetch semantic annotations for a given sign."""
    cur = conn.execute("""
        SELECT * FROM sign_semantics WHERE sign_id = ?
    """, (sign_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def get_linear_b_parallels(conn: sqlite3.Connection, ins_id: int) -> List[Dict]:
    """Fetch any Linear B parallel references for an inscription."""
    cur = conn.execute("""
        SELECT * FROM relations_linear_b WHERE inscription_id = ?
    """, (ins_id,))
    return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Text-type classification
# ---------------------------------------------------------------------------

def classify_text_type(inscription: Dict, signs: List[Dict]) -> str:
    """
    Classify an inscription as 'administrative', 'religious', or 'unknown'.
    Administrative: tablets, clay documents, pages-shaped, with numerals/logograms.
    Religious: votive objects, stone, metal, with dedicatory formulas.
    """
    material = (inscription.get("material") or "").lower()
    obj_type = (inscription.get("object_type") or "").lower()
    object_type = (inscription.get("object_type") or "").lower()

    # Religious indicators
    religious_materials = {"stone", "metal", "gold", "silver", "bronze", "marble"}
    religious_objects = {
        "votive", "altar", "dedication", "libation", "table", "offering",
        "vessel", "cup", "bowl", "ring", "seal", "pendant", "statuette",
        "figurine", "double axe", "sacred", "temple",
    }
    admin_objects = {
        "tablet", "page-shaped", "palm-leaf", "roundel", "sealing",
        "label", "nodule", "bar", "account", "ledger",
    }

    if material in religious_materials:
        return "religious"
    # Use word-boundary matching to avoid "table" matching inside "tablet"
    obj_words = set(re.split(r'[\s()-]+', object_type))
    if obj_words & religious_objects:
        return "religious"
    if obj_words & admin_objects:
        return "administrative"
    if material == "clay":
        # Most clay tablets are administrative
        if "tablet" in object_type or "page" in object_type:
            return "administrative"
        # Pottery/ceramic could be either
        return "administrative"  # default for clay
    if material in ("stone", "metal"):
        return "religious"

    return "unknown"


def extract_logogram_commodities(signs: List[Dict]) -> List[str]:
    """Extract commodity names from logogram signs."""
    commodities = []
    for s in signs:
        if s.get("sign_type") == "logogram":
            trans = (s.get("transliteration") or "").strip()
            if trans and trans != "?":
                commodities.append(trans)
            # Also check character field
            char = (s.get("character") or "").strip()
            if char and char not in commodities and len(char) <= 4:
                if char not in commodities:
                    commodities.append(char)
    return commodities


def extract_numerals(signs: List[Dict]) -> List[str]:
    """Extract numeral/fraction values from signs."""
    nums = []
    for s in signs:
        if s.get("sign_type") in ("numeral", "fraction", "metrical"):
            trans = (s.get("transliteration") or "").strip()
            if trans and trans != "?":
                nums.append(trans)
    return nums


def reconstruct_text(signs: List[Dict]) -> str:
    """Reconstruct the full text of an inscription from its signs."""
    parts = []
    for s in signs:
        char = s.get("character") or ""
        trans = s.get("transliteration") or ""
        # Prefer Unicode character if available
        if char and char.strip():
            parts.append(char)
        elif trans and trans.strip() and trans != "?":
            parts.append(trans)
        else:
            parts.append("_")
    return " ".join(parts)


def reconstruct_transliteration(signs: List[Dict]) -> str:
    """Reconstruct the transliteration sequence."""
    parts = []
    for s in signs:
        trans = s.get("transliteration") or ""
        if trans and trans.strip() and trans != "?":
            parts.append(trans)
        else:
            parts.append("?")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Context window extraction
# ---------------------------------------------------------------------------

def extract_context_window(
    signs: List[Dict], match_sign: str,
    window_before: int = 5, window_after: int = 5
) -> Dict:
    """
    Find the context window around the matched sign sequence.
    match_sign is the transliteration of the matched Linear A sequence.
    """
    # Build concatenated transliteration string for searching
    full_trans = [s.get("transliteration", "") or "" for s in signs]
    full_text = "".join(full_trans)

    # Find positions where match appears
    positions = []
    start = 0
    while True:
        pos = full_text.find(match_sign, start)
        if pos == -1:
            break
        # Map position back to sign index
        cum_len = 0
        for i, t in enumerate(full_trans):
            if cum_len == pos:
                positions.append(i)
                break
            cum_len += len(t)
            if cum_len > pos:
                positions.append(i)
                break
        start = pos + 1

    if not positions:
        # Fallback: search in individual sign transliterations
        for i, s in enumerate(signs):
            t = (s.get("transliteration") or "").strip()
            if t and match_sign and (t == match_sign or match_sign.startswith(t)):
                positions.append(i)

    context = {
        "match_positions": positions,
        "signs_before": [],
        "signs_after": [],
        "nearby_logograms": [],
        "nearby_numerals": [],
    }

    if not positions:
        return context

    # Take the first match position for context
    mid = positions[0]
    start_idx = max(0, mid - window_before)
    end_idx = min(len(signs), mid + window_after + 1)

    context["signs_before"] = [
        {
            "seq": s["sequence"],
            "char": s.get("character", ""),
            "trans": s.get("transliteration", ""),
            "type": s.get("sign_type", ""),
        }
        for s in signs[start_idx:mid]
    ]
    context["signs_after"] = [
        {
            "seq": s["sequence"],
            "char": s.get("character", ""),
            "trans": s.get("transliteration", ""),
            "type": s.get("sign_type", ""),
        }
        for s in signs[mid + 1:end_idx]
    ]

    # Collect nearby logograms (within the whole inscription)
    for s in signs:
        if s.get("sign_type") == "logogram":
            context["nearby_logograms"].append({
                "seq": s["sequence"],
                "trans": s.get("transliteration", ""),
                "char": s.get("character", ""),
                "bennett": s.get("bennett_id", ""),
            })
        if s.get("sign_type") in ("numeral", "fraction", "metrical"):
            context["nearby_numerals"].append({
                "seq": s["sequence"],
                "trans": s.get("transliteration", ""),
            })

    return context


# ---------------------------------------------------------------------------
# Findspot distribution analysis
# ---------------------------------------------------------------------------

def get_findspot_distribution(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get count of inscriptions per findspot."""
    cur = conn.execute("""
        SELECT f.site, COUNT(*) as cnt
        FROM inscriptions i
        JOIN findspots f ON i.findspot_id = f.id
        GROUP BY f.site
        ORDER BY cnt DESC
    """)
    return {r["site"]: r["cnt"] for r in cur.fetchall()}


def get_inscriptions_at_site(conn: sqlite3.Connection, site: str) -> int:
    """Count total inscriptions from a given findspot site."""
    cur = conn.execute("""
        SELECT COUNT(*) as cnt
        FROM inscriptions i
        JOIN findspots f ON i.findspot_id = f.id
        WHERE f.site = ?
    """, (site,))
    return cur.fetchone()["cnt"]


# ---------------------------------------------------------------------------
# Nth-ss pattern analysis
# ---------------------------------------------------------------------------

# Known Pre-Greek -nth- and -ss- words from Beekes (2010)
NTH_WORDS = {
    "λαβύρινθος": "labyrinthos",
    "ὄλυνθος": "olynthos",
    "ἐρέβινθος": "erebinthos",
    "ὄροβινθος": "orobinthos",
    "κόλυνθος": "kolynthos",
    "μίνθη": "minthē",
    "ἄκανθα": "akantha",
    "κάνθαρος": "kantharos",
    "πλίνθος": "plinthos",
    "ἀσάμινθος": "asaminthos",
    "κόρινθος": "korinthos",
    "ζάκυνθος": "zakynthos",
    "βόλινθος": "bolinthos",
    "σάρισσα": "sarissa",
    "θάλασσα": "thalassa",
    "κυπάρισσος": "kyparissos",
    "ἔλασσον": "elasson",
    "κολοσσός": "kolossos",
    "πύραυσος": "pyrausos",
    "κισσός": "kissos",
}

SS_WORDS = {
    "θάλασσα": "thalassa",
    "κυπάρισσος": "kyparissos",
    "κισσός": "kissos",
    "κισσύβιον": "kissybion",
    "γλῶσσα": "glōssa",
    "κολοσσός": "kolossos",
    "σάρισσα": "sarissa",
    "πέλασσος": "pelassos",
    "ἔλασσον": "elasson",
    "μέλισσα": "melissa",
    "πύραυσος": "pyrausos",
    "κνάσσος": "knassos",
    "λάρυσος": "larysos",
    "πύρασσος": "pyrassos",
    "Ἅλυσσος": "halyssos",
}


def extract_nth_ss_patterns(
    conn: sqlite3.Connection,
    loanword_rows: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Analyze -nth- and -ss- suffix patterns in the loanword data and the DB.

    Returns a list of analysis records.
    """
    results = []

    # 1. Check existing loanword matches for nth/ss words
    all_greek_words = set()
    for r in loanword_rows:
        g = r["greek"]
        t = r["transliteration"]
        all_greek_words.add((g, t, r["minoan_form"]))

    # Pattern: Greek words ending in -νθος, -νθη, -νθα, -σσος, -σσα, -σσον
    nth_pattern = re.compile(r"νθ[οαη]ς?$|υνθο[σς]?$")
    ss_pattern = re.compile(r"σ[σσοα]ς?$|σσον$")

    # Analyze from loanword matches
    for r in loanword_rows:
        greek = r["greek"]
        trans = r["transliteration"]
        minoan = r["minoan_form"]
        score = float(r["confidence_score"])

        suffix_type = None
        suffix_pattern = None

        # Check for -nth- suffix
        if re.search(r"[νn]θ|νθ", greek) or re.search(r"nth|ynth", trans, re.IGNORECASE):
            suffix_type = "nth"
            # Determine specific pattern
            if re.search(r"ινθος$|ινθοσ", greek):
                suffix_pattern = "-ινθος"
            elif re.search(r"υνθος$", greek):
                suffix_pattern = "-υνθος"
            elif re.search(r"ινθη$", greek):
                suffix_pattern = "-ινθη"
            elif re.search(r"ανθ[αος]$", greek):
                suffix_pattern = "-ανθ-"
            else:
                suffix_pattern = "-νθ- (other)"

        # Check for -ss- suffix
        if re.search(r"[σς][σς]", greek) or re.search(r"ss", trans, re.IGNORECASE):
            suffix_type = "ss"
            if re.search(r"ισσος$|ισσοσ", greek):
                suffix_pattern = "-ισσος"
            elif re.search(r"ασσα$", greek):
                suffix_pattern = "-ασσα"
            elif re.search(r"ωσσα$", greek):
                suffix_pattern = "-ωσσα"
            elif re.search(r"υσσος$", greek):
                suffix_pattern = "-υσσος"
            else:
                suffix_pattern = "-σσ- (other)"

        if suffix_type:
            results.append({
                "greek_word": greek,
                "transliteration": trans,
                "minoan_reconstructed": minoan,
                "english_gloss": r["english_gloss"],
                "suffix_type": suffix_type,
                "suffix_pattern": suffix_pattern,
                "confidence_score": score,
                "matched_sequence": r["matched"],
                "gorila_id": r["gorila_id"],
                "site": r["site"],
                "source": "loanword_matches",
                "linear_a_candidate": minoan,
                "notes": "",
            })

    # 2. Search the database for sign sequences that could represent -nth- or -ss-
    # Look for sequences ending in TA, TI, TU (dental stops) that could be -nth-
    # and SA, SI, SU (sibilants) that could be -ss-
    nth_sign_clusters = ["TA", "TI", "TU", "DA", "DE", "DI", "DO", "DU"]
    ss_sign_clusters = ["SA", "SI", "SU", "ZA", "ZE", "ZO", "ZU"]

    # Get all syllabogram sequences from the DB
    cur = conn.execute("""
        SELECT i.gorila_id, s.inscription_id, s.sequence, s.transliteration, s.sign_type,
               s.character, f.site
        FROM signs s
        JOIN inscriptions i ON s.inscription_id = i.id
        LEFT JOIN findspots f ON i.findspot_id = f.id
        WHERE s.sign_type = 'syllabogram'
          AND s.transliteration != ''
          AND s.transliteration NOT IN ('?', '𐄁', '')
        ORDER BY s.inscription_id, s.sequence
    """)
    all_syllabograms = [dict(r) for r in cur.fetchall()]

    # Group by inscription
    ins_sigs: Dict[int, List[Dict]] = defaultdict(list)
    for s in all_syllabograms:
        ins_sigs[s["inscription_id"]].append(s)

    # Find terminal sequences: look at the last 1-3 syllabograms of each inscription
    nth_candidates_seen: Set[str] = set()
    ss_candidates_seen: Set[str] = set()

    for ins_id, sigs in ins_sigs.items():
        if not sigs:
            continue
        # Get transliteration sequence
        trans_seq = [s["transliteration"] for s in sigs if s["transliteration"] not in ("", "?", "𐄁")]
        if not trans_seq:
            continue

        # Build full text
        full_text = "".join(trans_seq)

        # Look for sequences ending with dental or sibilant signs
        # Terminal bigrams that could represent -nth- or -ss-
        if len(trans_seq) >= 1:
            last = trans_seq[-1] if len(trans_seq) >= 1 else ""
            second_last = trans_seq[-2] if len(trans_seq) >= 2 else ""
            third_last = trans_seq[-3] if len(trans_seq) >= 3 else ""

            # -nth- candidates: final TA, TI, TU preceded by a vowel sign
            vowels = {"A", "E", "I", "O", "U", "JA", "JE", "JO", "JU", "WA", "WE", "WI", "WO"}
            dentals = {"TA", "TI", "TU", "DA", "DE", "DI", "DO", "DU"}

            # Check if inscription ends with a dental preceded by a vowel → possible -Vnth-
            if last in dentals and second_last in vowels:
                candidate = second_last + last
                if candidate not in nth_candidates_seen:
                    nth_candidates_seen.add(candidate)
                    # Look up the gorila_id for this inscription
                    gorila = sigs[0].get("gorila_id", "")
                    site = sigs[0].get("site", "")
                    results.append({
                        "greek_word": f"*{candidate}",
                        "transliteration": candidate,
                        "minoan_reconstructed": candidate,
                        "english_gloss": "(possible -nth- pattern)",
                        "suffix_type": "nth",
                        "suffix_pattern": f"-{last} (terminal dental)",
                        "confidence_score": 0,
                        "matched_sequence": candidate,
                        "gorila_id": gorila,
                        "site": site,
                        "source": "database_search",
                        "linear_a_candidate": candidate,
                        "notes": f"Terminal dental {last} preceded by vowel {second_last}; possible -nth- correspondence",
                    })

            # -ss- candidates: final SA, SI, SU preceded by vowel
            sibilants = {"SA", "SI", "SU", "ZA", "ZO", "ZU"}
            if last in sibilants and second_last in vowels:
                candidate = second_last + last
                if candidate not in ss_candidates_seen:
                    ss_candidates_seen.add(candidate)
                    gorila = sigs[0].get("gorila_id", "")
                    site = sigs[0].get("site", "")
                    results.append({
                        "greek_word": f"*{candidate}",
                        "transliteration": candidate,
                        "minoan_reconstructed": candidate,
                        "english_gloss": "(possible -ss- pattern)",
                        "suffix_type": "ss",
                        "suffix_pattern": f"-{last} (terminal sibilant)",
                        "confidence_score": 0,
                        "matched_sequence": candidate,
                        "gorila_id": gorila,
                        "site": site,
                        "source": "database_search",
                        "linear_a_candidate": candidate,
                        "notes": f"Terminal sibilant {last} preceded by vowel {second_last}; possible -ss- correspondence",
                    })

    # Sort results by confidence (desc), with DB search results at end
    results.sort(key=lambda x: x["confidence_score"], reverse=True)

    return results


# ---------------------------------------------------------------------------
# Shadow lexicon builder
# ---------------------------------------------------------------------------

def build_shadow_lexicon(
    conn: sqlite3.Connection,
    loanword_rows: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Build a curated list of Linear A words with:
    - Strong correspondences to Greek substrate words (confidence >= threshold)
    - Semantic plausibility (context matches expected meaning)
    - Consistent transliteration across multiple attestations
    """
    lexicon = []

    # Group by minoan_form to find consistently attested words
    by_minoan: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for r in loanword_rows:
        by_minoan[r["minoan_form"]].append(r)

    for minoan_form, matches in by_minoan.items():
        # Take the highest confidence match for this form
        best = max(matches, key=lambda r: float(r["confidence_score"]))
        confidence = float(best["confidence_score"])

        if confidence < SHADOW_CONFIDENCE_THRESHOLD:
            continue

        # Check semantic plausibility
        semantic_score = float(best["semantic_score"])
        context_ok = semantic_score >= 0.1  # At least minimal semantic match

        # Check consistency: multiple attestations should have same Greek form
        greek_forms = set(r["greek"] for r in matches)
        transliterations = set(r["transliteration"] for r in matches)
        consistent = len(greek_forms) == 1 or len(matches) == 1

        # Determine category
        category = best.get("category", "unknown")

        # Get database context for the best match
        ins_id_str = best.get("inscription_id", "")
        try:
            ins_id = int(ins_id_str)
        except (ValueError, TypeError):
            ins_id = None

        commodity_context = ""
        text_type = "unknown"
        if ins_id:
            details = get_inscription_details(conn, ins_id)
            if details:
                signs = get_signs_for_inscription(conn, ins_id)
                commodities = extract_logogram_commodities(signs)
                if commodities:
                    commodity_context = "; ".join(commodities)
                text_type = classify_text_type(details, signs)

        lexicon.append({
            "linear_a_sequence_ab": minoan_form.upper(),
            "minoan_reconstructed_form": minoan_form.lower(),
            "greek_descendant": best["greek"],
            "greek_transliteration": best["transliteration"],
            "english_gloss": best["english_gloss"],
            "category": category,
            "confidence": confidence,
            "semantic_score": semantic_score,
            "num_attestations": len(matches),
            "consistency": "consistent" if consistent else "variable",
            "matched_sequences": "; ".join(set(r["matched"] for r in matches)),
            "findspots": "; ".join(set(r["site"] for r in matches)),
            "commodity_context": commodity_context,
            "text_type": text_type,
            "context_plausible": "yes" if context_ok else "no",
        })

    # Sort by confidence descending
    lexicon.sort(key=lambda x: x["confidence"], reverse=True)

    return lexicon


# ---------------------------------------------------------------------------
# Deep dive for top N matches
# ---------------------------------------------------------------------------

def produce_deep_dives(
    conn: sqlite3.Connection,
    loanword_rows: List[Dict[str, str]],
    n: int = 10
) -> List[Dict[str, Any]]:
    """
    For the N most secure matches (by confidence score), produce detailed analysis.
    """
    # Sort by confidence, then by distance (lower = better)
    sorted_rows = sorted(
        loanword_rows,
        key=lambda r: (-float(r["confidence_score"]), int(r["distance"]))
    )

    # Deduplicate by (minoan_form, greek) to get unique match pairs
    seen_pairs: Set[Tuple[str, str]] = set()
    unique_top = []
    for r in sorted_rows:
        key = (r["minoan_form"], r["greek"])
        if key not in seen_pairs:
            seen_pairs.add(key)
            unique_top.append(r)
        if len(unique_top) >= n:
            break

    dives = []
    for r in unique_top[:n]:
        ins_id_str = r.get("inscription_id", "")
        try:
            ins_id = int(ins_id_str)
        except (ValueError, TypeError):
            ins_id = None

        dive = {
            "greek": r["greek"],
            "transliteration": r["transliteration"],
            "english_gloss": r["english_gloss"],
            "minoan_form": r["minoan_form"],
            "category": r.get("category", ""),
            "query": r.get("query", ""),
            "matched": r.get("matched", ""),
            "distance": r.get("distance", ""),
            "confidence_score": r["confidence_score"],
            "findspot": r.get("site", ""),
            "inscription_id": ins_id_str,
            "gorila_id": r.get("gorila_id", ""),
            "full_text": "",
            "transliteration_full": "",
            "sign_count": 0,
            "logograms_present": [],
            "numerals_present": [],
            "text_type": "unknown",
            "period": r.get("period", ""),
            "material": r.get("material", ""),
            "object_type": "",
            "linear_b_parallels": [],
            "context_window_before": [],
            "context_window_after": [],
            "semantic_field": "",
            "context_supports": "",
            "notes": "",
        }

        if ins_id:
            details = get_inscription_details(conn, ins_id)
            signs = get_signs_for_inscription(conn, ins_id)

            if details:
                dive["object_type"] = details.get("object_type", "")

            if signs:
                dive["sign_count"] = len(signs)
                dive["full_text"] = reconstruct_text(signs)
                dive["transliteration_full"] = reconstruct_transliteration(signs)

                # Extract context
                match_seq = r.get("matched", "")
                ctx = extract_context_window(signs, match_seq)
                dive["context_window_before"] = [
                    f"{s['trans']}({s['type']})" for s in ctx["signs_before"]
                ]
                dive["context_window_after"] = [
                    f"{s['trans']}({s['type']})" for s in ctx["signs_after"]
                ]

                # Logograms
                dive["logograms_present"] = [
                    f"{s['trans']}({s['bennett']})" for s in ctx["nearby_logograms"]
                ]

                # Numerals
                dive["numerals_present"] = [
                    s["trans"] for s in ctx["nearby_numerals"]
                ]

                # Text type
                dive["text_type"] = classify_text_type(details, signs)

            # Linear B parallels
            lb = get_linear_b_parallels(conn, ins_id)
            dive["linear_b_parallels"] = [
                f"{p.get('phonetic_value', '')} ({p.get('dmic_id', '')})"
                for p in lb if p.get("phonetic_value")
            ]

            # Semantic field inference from context
            commodities = set(
                c.split("(")[0] for c in dive["logograms_present"]
            )
            semantic_fields = []
            if commodities & {"GRA", "GRA+U", "NI", "PU", "MA", "SESAM"}:
                semantic_fields.append("agriculture/grain")
            if commodities & {"VIN", "VIN+U"}:
                semantic_fields.append("wine/viticulture")
            if commodities & {"OLE", "OLE+U", "OLE+NE", "AROM"}:
                semantic_fields.append("oil/aromatics")
            if commodities & {"LANA", "TELA", "PUR"}:
                semantic_fields.append("textiles/wool")
            if commodities & {"FIC", "CROC", "CYPERUS"}:
                semantic_fields.append("spices/condiments")
            if commodities & {"VAS", "VASE"}:
                semantic_fields.append("vessels/containers")

            # Also infer from word category
            cat = r.get("category", "")
            if cat == "place_name":
                semantic_fields.append("toponym")
            elif cat == "plant":
                semantic_fields.append("flora")
            elif cat == "animal":
                semantic_fields.append("fauna")
            elif cat in ("implement", "tool", "weapon"):
                semantic_fields.append("material_culture")
            elif cat in ("religion", "ritual", "deity"):
                semantic_fields.append("religion/ritual")

            dive["semantic_field"] = "; ".join(semantic_fields) if semantic_fields else "uncertain"

            # Does context support the expected meaning?
            # For place names: administrative tablets with commodities make sense
            # For plants: nearby plant-related logograms support it
            context_supports = []
            if dive["text_type"] == "administrative" and cat == "place_name":
                context_supports.append("administrative context consistent with toponym")
            if semantic_fields:
                context_supports.append(f"semantic field: {dive['semantic_field']}")
            if commodities:
                context_supports.append(f"co-occurring commodities: {', '.join(commodities)}")
            if not context_supports:
                context_supports.append("limited contextual evidence")

            dive["context_supports"] = "; ".join(context_supports)

            # Additional notes
            notes = []
            if r.get("distance") == "0":
                notes.append("exact match")
            else:
                notes.append(f"approximate match (distance={r['distance']})")
            if dive["text_type"] != "unknown":
                notes.append(f"text type: {dive['text_type']}")
            if float(r["semantic_score"]) > 0.5:
                notes.append("strong semantic score")
            dive["notes"] = "; ".join(notes)

        dives.append(dive)

    return dives


# ---------------------------------------------------------------------------
# Main enrichment function
# ---------------------------------------------------------------------------

def enrich_loanword_matches(
    conn: sqlite3.Connection,
    rows: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """Enrich each loanword match record with database context and analysis."""
    enriched = []

    for r in rows:
        ins_id_str = r.get("inscription_id", "")
        try:
            ins_id = int(ins_id_str)
        except (ValueError, TypeError):
            ins_id = None

        record: Dict[str, Any] = {
            # Original fields
            "greek": r["greek"],
            "transliteration": r["transliteration"],
            "english_gloss": r["english_gloss"],
            "minoan_form": r["minoan_form"],
            "category": r.get("category", ""),
            "query": r.get("query", ""),
            "matched": r.get("matched", ""),
            "distance": r.get("distance", ""),
            "distance_threshold": r.get("distance_threshold", ""),
            "inscription_id": ins_id_str,
            "gorila_id": r.get("gorila_id", ""),
            "site": r.get("site", ""),
            "material": r.get("material", ""),
            "period": r.get("period", ""),
            "semantic_score": r.get("semantic_score", ""),
            "confidence_score": r.get("confidence_score", ""),
            "found_commodities": r.get("found_commodities", ""),
            "context_syllabograms": r.get("context_syllabograms", ""),

            # Enriched fields
            "text_type": "",
            "object_type": "",
            "full_inscription_text": "",
            "full_transliteration": "",
            "sign_count": 0,
            "num_logograms": 0,
            "num_numerals": 0,
            "num_fractions": 0,
            "logogram_list": "",
            "numeral_list": "",
            "context_before_5": "",
            "context_after_5": "",
            "findspot_context": "",
            "findspot_lat": "",
            "findspot_lon": "",
            "findspot_inscription_count": 0,
            "findspot_has_parallels": "",
            "linear_b_parallels": "",
            "semantic_field": "",
            "context_plausibility": "",
            "notes": "",
        }

        if not ins_id:
            enriched.append(record)
            continue

        # --- Get inscription details ---
        details = get_inscription_details(conn, ins_id)
        if not details:
            enriched.append(record)
            continue

        # --- Get signs ---
        signs = get_signs_for_inscription(conn, ins_id)
        if signs:
            record["sign_count"] = len(signs)
            record["full_inscription_text"] = reconstruct_text(signs)
            record["full_transliteration"] = reconstruct_transliteration(signs)

            # Count types
            type_counts = Counter(s["sign_type"] for s in signs)
            record["num_logograms"] = type_counts.get("logogram", 0)
            record["num_numerals"] = type_counts.get("numeral", 0)
            record["num_fractions"] = type_counts.get("fraction", 0)

            # Extract commodities and names
            commodities = extract_logogram_commodities(signs)
            record["logogram_list"] = "; ".join(commodities) if commodities else ""

            numerals = extract_numerals(signs)
            record["numeral_list"] = "; ".join(numerals) if numerals else ""

            # Context window around the matched sequence
            match_seq = r.get("matched", "")
            ctx = extract_context_window(signs, match_seq)
            before_str = " ".join(
                f"{s['trans']}" for s in ctx["signs_before"]
            )
            after_str = " ".join(
                f"{s['trans']}" for s in ctx["signs_after"]
            )
            record["context_before_5"] = before_str
            record["context_after_5"] = after_str

        # --- Text type ---
        record["text_type"] = classify_text_type(details, signs if signs else [])

        # --- Object type ---
        record["object_type"] = details.get("object_type", "")

        # --- Findspot context ---
        record["findspot_context"] = details.get("findspot_context", "")
        record["findspot_lat"] = details.get("latitude", "")
        record["findspot_lon"] = details.get("longitude", "")

        # Count inscriptions at this findspot for distribution
        site = details.get("findspot_site", "")
        if site:
            record["findspot_inscription_count"] = get_inscriptions_at_site(conn, site)

        # --- Linear B parallels ---
        lb = get_linear_b_parallels(conn, ins_id)
        if lb:
            lb_strs = [
                f"{p.get('phonetic_value', '')} ({p.get('dmic_id', '')})"
                for p in lb if p.get("phonetic_value") or p.get("dmic_id")
            ]
            record["linear_b_parallels"] = "; ".join(lb_strs)
            record["findspot_has_parallels"] = "yes"
        else:
            record["linear_b_parallels"] = ""
            record["findspot_has_parallels"] = "no"

        # --- Semantic field inference ---
        cat = r.get("category", "")
        comm_set = set(c.lower() for c in commodities)
        fields = []

        if cat == "place_name":
            fields.append("toponym/geography")
        elif cat == "plant":
            fields.append("flora/botany")
        elif cat == "animal":
            fields.append("fauna/zoology")
        elif cat == "deity":
            fields.append("religion/theonym")
        elif cat == "implement":
            fields.append("material_culture")
        elif cat == "substance":
            fields.append("substance/material")
        elif cat == "body_part":
            fields.append("anatomy")
        elif cat == "social":
            fields.append("social/political")

        # Commodity-based field hints
        for c in commodities:
            c_lower = c.lower()
            if c_lower in ("gra", "ni", "pu", "ma"):
                if "agriculture" not in str(fields).lower():
                    fields.append("agriculture (grain)")
            elif c_lower in ("vin",):
                if "viticulture" not in str(fields).lower():
                    fields.append("viticulture (wine)")
            elif c_lower in ("ole", "arom"):
                if "oil" not in str(fields).lower():
                    fields.append("oil/aromatics")
            elif c_lower in ("lana", "tela", "pur"):
                if "textiles" not in str(fields).lower():
                    fields.append("textiles")

        record["semantic_field"] = "; ".join(fields) if fields else "unknown"

        # --- Context plausibility ---
        # A match is plausible if:
        # 1. For place names: appears on administrative tablet with commodities
        # 2. For plants/animals: appears with relevant logograms
        # 3. For religious terms: appears on religious object
        plausible = True
        reasons = []

        if cat == "place_name":
            if record["text_type"] == "administrative":
                reasons.append("administrative context typical for toponyms")
            else:
                reasons.append(f"unexpected text type for toponym: {record['text_type']}")
                plausible = False
            if commodities:
                reasons.append(f"co-occurs with commodities: {', '.join(commodities[:3])}")

        elif cat in ("plant", "animal"):
            if commodities:
                relevant = [c for c in commodities if c.lower() in ("gra", "ni", "ma", "vin", "ole", "fic", "croc")]
                if relevant:
                    reasons.append(f"botanical context: {', '.join(relevant)}")
                else:
                    reasons.append(f"commodities present but not obviously botanical: {', '.join(commodities[:3])}")
            else:
                reasons.append("no commodity context available")

        elif cat in ("deity", "ritual"):
            if record["text_type"] == "religious":
                reasons.append("religious context appropriate")
            else:
                reasons.append(f"secular context for religious term: {record['text_type']}")

        else:
            reasons.append(f"category '{cat}' — no specific plausibility criteria")

        if not plausible:
            reasons.append("⚠ context mismatch")

        record["context_plausibility"] = "; ".join(reasons) if reasons else "undetermined"

        # --- Notes ---
        notes = []
        if r.get("distance") == "0":
            notes.append("exact phonetic match")
        else:
            notes.append(f"approximate match (levenshtein={r['distance']})")
        if float(r.get("semantic_score", "0")) > 0.3:
            notes.append("above-average semantic score")
        if record["num_logograms"] > 0:
            notes.append(f"{record['num_logograms']} logogram(s) present")
        if record["text_type"] != "unknown":
            notes.append(f"text: {record['text_type']}")
        record["notes"] = "; ".join(notes)

        enriched.append(record)

    return enriched


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    enriched: List[Dict[str, Any]],
    lexicon: List[Dict[str, Any]],
    nth_ss: List[Dict[str, Any]],
    dives: List[Dict[str, Any]]
) -> str:
    """Generate a detailed markdown report."""
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# Deep Loanword Mining Report")
    lines.append(f"*Generated: {ts}*")
    lines.append("")
    lines.append("## 1. Overview")
    lines.append("")
    lines.append(f"- **Total Phase 3 loanword matches analyzed:** {len(enriched)}")
    wc_high = sum(1 for r in enriched if float(r.get("confidence_score", 0)) >= 45)
    wc_mid = sum(1 for r in enriched if 30 <= float(r.get("confidence_score", 0)) < 45)
    wc_low = sum(1 for r in enriched if float(r.get("confidence_score", 0)) < 30)
    lines.append(f"- **High-confidence (≥45):** {wc_high}")
    lines.append(f"- **Medium-confidence (30–44):** {wc_mid}")
    lines.append(f"- **Low-confidence (<30):** {wc_low}")
    lines.append("")

    # Text type distribution
    text_types = Counter(r.get("text_type", "unknown") for r in enriched)
    lines.append("### Text Type Distribution")
    lines.append("")
    for tt, cnt in text_types.most_common():
        lines.append(f"- **{tt}:** {cnt} ({cnt/len(enriched)*100:.1f}%)")
    lines.append("")

    # Findspot distribution
    site_counts = Counter(r.get("site", "unknown") for r in enriched)
    lines.append("### Top Findspots")
    lines.append("")
    lines.append("| Site | Count | Percentage |")
    lines.append("|------|-------|------------|")
    for site, cnt in site_counts.most_common(15):
        lines.append(f"| {site} | {cnt} | {cnt/len(enriched)*100:.1f}% |")
    lines.append("")

    # Category distribution
    cat_counts = Counter(r.get("category", "unknown") for r in enriched)
    lines.append("### Category Distribution")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, cnt in cat_counts.most_common():
        lines.append(f"| {cat} | {cnt} |")
    lines.append("")

    # Material distribution
    mat_counts = Counter(r.get("material", "unknown") for r in enriched)
    lines.append("### Material Distribution")
    lines.append("")
    lines.append("| Material | Count |")
    lines.append("|----------|-------|")
    for mat, cnt in mat_counts.most_common():
        lines.append(f"| {mat} | {cnt} |")
    lines.append("")

    # --- Shadow Lexicon ---
    lines.append("## 2. Minoan Shadow Lexicon")
    lines.append("")
    lines.append(f"*Curated list of Linear A words with confidence ≥ {SHADOW_CONFIDENCE_THRESHOLD}*")
    lines.append("")
    lines.append(f"**Total entries:** {len(lexicon)}")
    lines.append("")

    # Top entries
    lines.append("### Top Entries by Confidence")
    lines.append("")
    lines.append("| Linear A (AB) | Minoan | Greek | Gloss | Confidence | Attestations | Field |")
    lines.append("|---------------|--------|-------|-------|------------|-------------|-------|")
    for entry in lexicon[:25]:
        lines.append(
            f"| {entry['linear_a_sequence_ab']} | {entry['minoan_reconstructed_form']} "
            f"| {entry['greek_descendant']} | {entry['english_gloss']} "
            f"| {entry['confidence']} | {entry['num_attestations']} "
            f"| {entry['category']} |"
        )
    lines.append("")

    # Categories in lexicon
    lex_cats = Counter(e["category"] for e in lexicon)
    lines.append("### Shadow Lexicon Categories")
    lines.append("")
    for cat, cnt in lex_cats.most_common():
        lines.append(f"- **{cat}:** {cnt}")
    lines.append("")

    # --- Nth/SS Analysis ---
    lines.append("## 3. -nth- and -ss- Suffix Analysis")
    lines.append("")
    lines.append(f"*Pre-Greek substrate suffixes: the strongest markers of Minoan substrate*")
    lines.append("")
    nth_count = sum(1 for r in nth_ss if r["suffix_type"] == "nth")
    ss_count = sum(1 for r in nth_ss if r["suffix_type"] == "ss")
    lines.append(f"- **-nth- pattern words:** {nth_count}")
    lines.append(f"- **-ss- pattern words:** {ss_count}")
    lines.append("")

    # Nth words from loanword matches (with actual Greek correspondences)
    nth_confirmed = [r for r in nth_ss if r["source"] == "loanword_matches" and r["suffix_type"] == "nth"]
    if nth_confirmed:
        lines.append("### Confirmed -nth- Words from Loanword Matches")
        lines.append("")
        lines.append("| Greek | Transliteration | Minoan | Gloss | Confidence | Pattern |")
        lines.append("|-------|-----------------|--------|-------|------------|---------|")
        for r in nth_confirmed:
            lines.append(
                f"| {r['greek_word']} | {r['transliteration']} | {r['minoan_reconstructed']} "
                f"| {r['english_gloss']} | {r['confidence_score']} | {r['suffix_pattern']} |"
            )
        lines.append("")

    # SS words from loanword matches
    ss_confirmed = [r for r in nth_ss if r["source"] == "loanword_matches" and r["suffix_type"] == "ss"]
    if ss_confirmed:
        lines.append("### Confirmed -ss- Words from Loanword Matches")
        lines.append("")
        lines.append("| Greek | Transliteration | Minoan | Gloss | Confidence | Pattern |")
        lines.append("|-------|-----------------|--------|-------|------------|---------|")
        for r in ss_confirmed:
            lines.append(
                f"| {r['greek_word']} | {r['transliteration']} | {r['minoan_reconstructed']} "
                f"| {r['english_gloss']} | {r['confidence_score']} | {r['suffix_pattern']} |"
            )
        lines.append("")

    # DB-discovered patterns
    db_nth = [r for r in nth_ss if r["source"] == "database_search" and r["suffix_type"] == "nth"]
    db_ss = [r for r in nth_ss if r["source"] == "database_search" and r["suffix_type"] == "ss"]
    if db_nth:
        lines.append(f"### Linear A Terminal Dental Sequences (possible -nth- correspondences)")
        lines.append("")
        lines.append(f"Found {len(db_nth)} unique terminal dental sequences in the database.")
        lines.append("")
        lines.append("| Sequence | Inscription | Site | Notes |")
        lines.append("|----------|-------------|------|-------|")
        for r in db_nth[:15]:
            lines.append(
                f"| {r['linear_a_candidate']} | {r['gorila_id']} | {r['site']} | {r['notes']} |"
            )
        lines.append("")

    if db_ss:
        lines.append(f"### Linear A Terminal Sibilant Sequences (possible -ss- correspondences)")
        lines.append("")
        lines.append(f"Found {len(db_ss)} unique terminal sibilant sequences in the database.")
        lines.append("")
        lines.append("| Sequence | Inscription | Site | Notes |")
        lines.append("|----------|-------------|------|-------|")
        for r in db_ss[:15]:
            lines.append(
                f"| {r['linear_a_candidate']} | {r['gorila_id']} | {r['site']} | {r['notes']} |"
            )
        lines.append("")

    # --- Deep Dives ---
    lines.append("## 4. Deep Dives — Top Matches")
    lines.append("")
    lines.append(f"*Detailed analysis of the {TOP_N_DEEP_DIVES} most secure matches*")
    lines.append("")

    for i, dive in enumerate(dives, 1):
        lines.append(f"### 4.{i}. {dive['greek']} ← {dive['minoan_form']}")
        lines.append("")
        lines.append(f"- **Greek:** {dive['greek']} ({dive['transliteration']})")
        lines.append(f"- **Gloss:** {dive['english_gloss']}")
        lines.append(f"- **Minoan etymon:** {dive['minoan_form']}")
        lines.append(f"- **Matched Linear A sequence:** {dive['matched']} (distance={dive['distance']})")
        lines.append(f"- **Confidence score:** {dive['confidence_score']}")
        lines.append(f"- **Category:** {dive['category']}")
        lines.append(f"- **Findspot:** {dive['findspot']}")
        lines.append(f"- **Inscription:** {dive['gorila_id']} ({dive['period']}, {dive['material']}, {dive['object_type']})")
        lines.append(f"- **Text type:** {dive['text_type']}")
        lines.append(f"- **Sign count:** {dive['sign_count']}")
        lines.append("")

        if dive.get("full_text"):
            lines.append("**Full text (Unicode):**")
            lines.append(f"```")
            lines.append(dive["full_text"][:200])
            lines.append("```")
            lines.append("")

        if dive.get("transliteration_full"):
            lines.append("**Full transliteration:**")
            lines.append(f"```")
            lines.append(dive["transliteration_full"][:200])
            lines.append("```")
            lines.append("")

        if dive.get("context_window_before") or dive.get("context_window_after"):
            lines.append("**Context window:**")
            ctx_before = " ".join(dive["context_window_before"][-5:])
            ctx_after = " ".join(dive["context_window_after"][:5])
            lines.append(f"- Signs before: `{ctx_before}`")
            lines.append(f"- Signs after: `{ctx_after}`")
            lines.append("")

        if dive.get("logograms_present"):
            lines.append(f"**Co-occurring logograms:** {', '.join(dive['logograms_present'])}")
            lines.append("")

        if dive.get("linear_b_parallels"):
            lines.append(f"**Linear B parallels:** {', '.join(dive['linear_b_parallels'])}")
            lines.append("")

        lines.append(f"**Semantic field:** {dive['semantic_field']}")
        lines.append(f"**Context supports:** {dive['context_supports']}")
        lines.append(f"**Notes:** {dive['notes']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Summary statistics ---
    lines.append("## 5. Summary Statistics")
    lines.append("")

    # Average confidence by category
    cat_conf: Dict[str, List[float]] = defaultdict(list)
    for r in enriched:
        cat = r.get("category", "unknown")
        try:
            conf = float(r["confidence_score"])
        except (ValueError, TypeError):
            continue
        cat_conf[cat].append(conf)

    lines.append("### Average Confidence by Category")
    lines.append("")
    lines.append("| Category | Avg Confidence | Count |")
    lines.append("|----------|---------------|-------|")
    for cat in sorted(cat_conf.keys(), key=lambda c: statistics.mean(cat_conf[c]), reverse=True):
        vals = cat_conf[cat]
        lines.append(f"| {cat} | {statistics.mean(vals):.1f} | {len(vals)} |")
    lines.append("")

    # Findspot diversity
    unique_findspots = len(set(r.get("site", "") for r in enriched if r.get("site")))
    lines.append(f"- **Unique findspots represented:** {unique_findspots}")
    lines.append(f"- **Total signs analyzed across all matches:** {sum(int(r.get('sign_count', 0)) for r in enriched if r.get('sign_count'))}")
    lines.append(f"- **Entries with logograms present:** {sum(1 for r in enriched if int(r.get('num_logograms', 0)) > 0)}")
    lines.append(f"- **Entries with Linear B parallels:** {sum(1 for r in enriched if r.get('findspot_has_parallels') == 'yes')}")
    lines.append("")

    # Commodity co-occurrence
    all_commodities: List[str] = []
    for r in enriched:
        if r.get("logogram_list"):
            all_commodities.extend(r["logogram_list"].split("; "))
    comm_counts = Counter(c.strip() for c in all_commodities if c.strip())
    if comm_counts:
        lines.append("### Top Co-occurring Commodities")
        lines.append("")
        lines.append("| Commodity | Count |")
        lines.append("|-----------|-------|")
        for comm, cnt in comm_counts.most_common(15):
            lines.append(f"| {comm} | {cnt} |")
        lines.append("")

    lines.append("---")
    lines.append("*End of report*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Main entry point."""
    print("=" * 70)
    print("  Deep Loanword Mining — Minoan Loanwords in Greek")
    print("=" * 70)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Load input data ----
    print(f"[1] Loading Phase 3 loanword matches from {INPUT_CSV}...")
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loanword_rows = list(reader)
    print(f"    → {len(loanword_rows)} match records loaded")

    # ---- Connect to database ----
    print(f"[2] Connecting to database {DB_PATH}...")
    conn = get_db_connection()
    print("    → connected")

    # ---- Enrich all matches ----
    print(f"[3] Enriching {len(loanword_rows)} match records...")
    enriched = enrich_loanword_matches(conn, loanword_rows)
    print(f"    → {len(enriched)} records enriched")

    # Write enriched CSV
    if enriched:
        fieldnames = list(enriched[0].keys())
        with open(OUTPUT_ENRICHED, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)
        print(f"    → written to {OUTPUT_ENRICHED}")

    # ---- Build Minoan Shadow Lexicon ----
    print(f"[4] Building Minoan Shadow Lexicon (confidence ≥ {SHADOW_CONFIDENCE_THRESHOLD})...")
    lexicon = build_shadow_lexicon(conn, loanword_rows)
    print(f"    → {len(lexicon)} entries in shadow lexicon")

    if lexicon:
        fieldnames = list(lexicon[0].keys())
        with open(OUTPUT_LEXICON, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lexicon)
        print(f"    → written to {OUTPUT_LEXICON}")

    # ---- Nth/SS Analysis ----
    print(f"[5] Analyzing -nth- and -ss- suffix patterns...")
    nth_ss = extract_nth_ss_patterns(conn, loanword_rows)
    print(f"    → {len(nth_ss)} records in suffix analysis")

    if nth_ss:
        fieldnames = list(nth_ss[0].keys())
        with open(OUTPUT_NTH_SS, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(nth_ss)
        print(f"    → written to {OUTPUT_NTH_SS}")

    # ---- Deep Dives ----
    print(f"[6] Producing deep dives for top {TOP_N_DEEP_DIVES} matches...")
    dives = produce_deep_dives(conn, loanword_rows, n=TOP_N_DEEP_DIVES)
    print(f"    → {len(dives)} deep dives produced")
    for dive in dives:
        print(f"      • {dive['greek']:25s} ← {dive['minoan_form']:15s} (confidence={dive['confidence_score']:>5s})")

    # ---- Generate Report ----
    print(f"[7] Generating detailed report...")
    report = generate_report(enriched, lexicon, nth_ss, dives)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"    → written to {OUTPUT_REPORT}")

    # ---- Cleanup ----
    conn.close()
    print()
    print("Done. All outputs written to:")
    print(f"  • {OUTPUT_ENRICHED}")
    print(f"  • {OUTPUT_LEXICON}")
    print(f"  • {OUTPUT_NTH_SS}")
    print(f"  • {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
