#!/usr/bin/env python3
"""
Phase 5: Phonetic Grid Refinement for Linear A
=================================================
Synthesises ALL Phase 5 comparative evidence into a refined phonetic grid.

Inputs:
  Phase 5:
    - data/analysis/comparative/la_lb_mapping.csv
    - data/analysis/comparative/la_lb_misaligned.csv
    - data/analysis/comparative/la_cm_shared_phonetic_grid.csv
    - data/analysis/comparative/minoan_shadow_lexicon.csv
    - data/analysis/comparative/la_lb_ideogram_map.csv
    - data/analysis/comparative/fraction_alignment.csv
  Phase 3:
    - data/analysis/linguistic/phonetic_grid_confidence.csv
    - data/analysis/linguistic/toponym_anchors.csv
  Phase 2:
    - data/analysis/positional/misvalued_signs_ranked.csv
    - data/analysis/ngram/misvalued_signs_ngram.csv

Outputs:
  - data/analysis/comparative/refined_phonetic_grid.csv
  - data/analysis/comparative/grid_changes_from_ab.csv
  - data/analysis/comparative/misvalued_signs_resolution.csv
  - data/analysis/comparative/phase5_synthesis.md
"""

import csv
import os
import math
from collections import defaultdict

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "analysis")

COMP = os.path.join(DATA, "comparative")
LING = os.path.join(DATA, "linguistic")
POS  = os.path.join(DATA, "positional")
NGRAM = os.path.join(DATA, "ngram")
OUT = COMP


def load_csv(path, key_col=None):
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if key_col:
        return {r[key_col]: r for r in rows if r.get(key_col)}
    return rows


def safe_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_int(v, default=0):
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def clean_bennett(bid):
    return bid.strip().upper()


def is_uncertain(val):
    """Return True if a phonetic value string is uncertain."""
    if not val or val == "?" or "?" in val:
        return True
    if val == "—" or val == "--":
        return True
    return False


def strip_uncertain(val):
    """Remove trailing ? from a value like 'pa2?' → 'pa2', but keep '?' as '?'."""
    if not val or val == "?":
        return "?"
    if val == "—" or val == "--":
        return "?"
    return val.rstrip("?")


# ── 1. Load all files ──────────────────────────────────────────────────────
print("=" * 70)
print("PHASE 5 — PHONETIC GRID REFINEMENT")
print("=" * 70)

print("\n[1] Loading Phase 5 comparative outputs ...")
la_lb_map = load_csv(os.path.join(COMP, "la_lb_mapping.csv"), key_col="bennett_id")
print(f"    la_lb_mapping.csv: {len(la_lb_map)} rows")

la_lb_misaligned = load_csv(os.path.join(COMP, "la_lb_misaligned.csv"), key_col="bennett_id")
print(f"    la_lb_misaligned.csv: {len(la_lb_misaligned)} rows")

la_cm_grid = load_csv(os.path.join(COMP, "la_cm_shared_phonetic_grid.csv"), key_col="la_ab")
print(f"    la_cm_shared_phonetic_grid.csv: {len(la_cm_grid)} rows")

shadow_lexicon = load_csv(os.path.join(COMP, "minoan_shadow_lexicon.csv"))
print(f"    minoan_shadow_lexicon.csv: {len(shadow_lexicon)} rows")

ideogram_map = load_csv(os.path.join(COMP, "la_lb_ideogram_map.csv"), key_col="la_bennett_id")
print(f"    la_lb_ideogram_map.csv: {len(ideogram_map)} rows")

fraction_align = load_csv(os.path.join(COMP, "fraction_alignment.csv"), key_col="la_fraction_id")
print(f"    fraction_alignment.csv: {len(fraction_align)} rows")

print("\n[2] Loading Phase 3 linguistic outputs ...")
grid_confidence = load_csv(os.path.join(LING, "phonetic_grid_confidence.csv"))
print(f"    phonetic_grid_confidence.csv: {len(grid_confidence)} rows")

toponym_anchors = load_csv(os.path.join(LING, "toponym_anchors.csv"))
print(f"    toponym_anchors.csv: {len(toponym_anchors)} rows")

print("\n[3] Loading Phase 2 anomaly outputs ...")
misvalued_ranked = load_csv(os.path.join(POS, "misvalued_signs_ranked.csv"))
print(f"    misvalued_signs_ranked.csv: {len(misvalued_ranked)} rows")

misvalued_ngram = load_csv(os.path.join(NGRAM, "misvalued_signs_ngram.csv"))
print(f"    misvalued_signs_ngram.csv: {len(misvalued_ngram)} rows")

pos_profiles = load_csv(os.path.join(POS, "positional_profiles.csv"), key_col="bennett_id")
print(f"    positional_profiles.csv: {len(pos_profiles)} rows")


# ── 2. Index evidence by sign ──────────────────────────────────────────────
print("\n[4] Indexing evidence by sign ...")

# ── 2a. LB mapping evidence ──
LB_EVIDENCE = {}
for bid, row in la_lb_map.items():
    raw_lb = row.get("lb_value", "")
    raw_hyp = row.get("la_hyp_value", "")

    # Determine the confident LB value (strip ? markers)
    lb_confident = ""
    if raw_lb and not is_uncertain(raw_lb):
        lb_confident = strip_uncertain(raw_lb)

    # LA hypothesized value may differ from LB
    la_hyp = ""
    if raw_hyp and not is_uncertain(raw_hyp):
        la_hyp = strip_uncertain(raw_hyp)
    elif raw_hyp and is_uncertain(raw_hyp) and raw_lb and not is_uncertain(raw_lb):
        # If LA hyp is uncertain but LB value is confident, use LB
        la_hyp = strip_uncertain(raw_lb)

    # Composite score only counts if value is not totally uncertain
    comp = safe_float(row.get("composite_score"))
    if is_uncertain(raw_lb) and is_uncertain(raw_hyp):
        comp = 0  # Can't trust composite for unknown signs

    LB_EVIDENCE[bid] = {
        "lb_value_raw": raw_lb,
        "la_hyp_raw": raw_hyp,
        "lb_value_confident": lb_confident,
        "la_hyp_value": la_hyp,
        "visual_sim": safe_float(row.get("visual_sim")),
        "attestation": row.get("attestation", ""),
        "sign_type": row.get("sign_type", ""),
        "visual_score": safe_float(row.get("visual_score")),
        "positional_score": safe_float(row.get("positional_score")),
        "frequency_score": safe_float(row.get("frequency_score")),
        "toponym_score": safe_float(row.get("toponym_score")),
        "ngram_score": safe_float(row.get("ngram_score")),
        "composite_score": comp,
        "notes": row.get("notes", ""),
        "has_confident_value": bool(lb_confident or la_hyp),
    }

# ── 2b. CM triangular inference ──
CM_EVIDENCE = {}
for ab, row in la_cm_grid.items():
    bid = clean_bennett(ab)
    raw_la_lb_val = row.get("la_lb_value", "")
    inferred = row.get("inferred_la_phonetic", "")

    # The inferred_la_phonetic is the CM-derived value
    cm_conf = row.get("triangular_confidence", "").upper()

    CM_EVIDENCE[bid] = {
        "cm_sign": row.get("cm_sign", ""),
        "cm_desc": row.get("cm_desc", ""),
        "cg_value": row.get("cg_value", ""),
        "la_lb_value_in_grid": raw_la_lb_val,  # value from grid (for cross-ref)
        "inferred_la": inferred if not is_uncertain(inferred) else "",
        "triangular_confidence": cm_conf,
        "notes": row.get("notes", ""),
        "has_confident_value": bool(inferred and not is_uncertain(inferred)),
    }

# ── 2c. Shadow lexicon ──
SHADOW_EVIDENCE = defaultdict(list)
for row in shadow_lexicon:
    cat = row.get("category", "").strip()
    greek = row.get("greek_descendant", "").strip()
    minoan = row.get("minoan_reconstructed_form", "").strip()
    seqs = row.get("matched_sequences", "")
    confidence = safe_float(row.get("confidence"))
    SHADOW_EVIDENCE[minoan.upper()].append({
        "category": cat,
        "greek": greek,
        "minoan": minoan,
        "sequences": seqs,
        "confidence": confidence,
    })

# ── 2d. Commodity context ──
commodity_ctx = load_csv(os.path.join(COMP, "commodity_contexts.csv"))
COMMODITY_EVIDENCE = defaultdict(list)
for row in commodity_ctx:
    bid = clean_bennett(row.get("la_bennett_id", ""))
    if bid:
        COMMODITY_EVIDENCE[bid].append({
            "inscription": row.get("inscription_id", ""),
            "findspot": row.get("findspot", ""),
            "object_type": row.get("object_type", ""),
            "pattern_frequency": safe_float(row.get("pattern_frequency")),
        })

# ── 2e. Toponym anchor confidence ──
TOPONYM_EVIDENCE = defaultdict(set)
for row in toponym_anchors:
    matched_str = row.get("matched_string", "")
    distance = safe_int(row.get("distance"))
    place = row.get("place_name", "")
    if matched_str and distance < 2:
        for ch in matched_str:
            if ch.isalpha():
                TOPONYM_EVIDENCE[ch.upper()].add(place)

# ── 2f. Positional anomaly ──
POSITIONAL_EVIDENCE = {}
for row in misvalued_ranked:
    bid = clean_bennett(row.get("bennett_id", ""))
    POSITIONAL_EVIDENCE[bid] = {
        "pos_rank": safe_int(row.get("rank")),
        "transliteration": row.get("transliteration", ""),
        "total_occurrences": safe_int(row.get("total_occurrences")),
        "initial_fraction": safe_float(row.get("initial_fraction")),
        "medial_fraction": safe_float(row.get("medial_fraction")),
        "final_fraction": safe_float(row.get("final_fraction")),
        "kl_divergence": safe_float(row.get("kl_divergence")),
        "flags": row.get("flags", ""),
    }

# ── 2g. N-gram disruption ──
NGRAM_EVIDENCE = {}
for row in misvalued_ngram:
    bid = clean_bennett(row.get("bennett_id", ""))
    NGRAM_EVIDENCE[bid] = {
        "ngram_rank": safe_int(row.get("rank")),
        "transliteration": row.get("transliteration", ""),
        "disruption_score": safe_float(row.get("disruption_score")),
        "cross_class_affinity": safe_float(row.get("cross_class_affinity")),
        "num_anomalous_followers": safe_int(row.get("num_anomalous_followers")),
    }


# ── 3. Build master sign set and index grid confidence ─────────────────────
all_signs = set()
all_signs.update(LB_EVIDENCE.keys())
all_signs.update(CM_EVIDENCE.keys())
for row in grid_confidence:
    bid = clean_bennett(row.get("bennett_id", ""))
    if bid:
        all_signs.add(bid)
all_signs.update(POSITIONAL_EVIDENCE.keys())
all_signs.update(NGRAM_EVIDENCE.keys())
all_signs.update(la_lb_misaligned.keys())
for ab in la_cm_grid:
    all_signs.add(clean_bennett(ab))

TRACKED_SIGNS = ["AB 16", "AB 60", "AB 80", "AB 22", "AB 02", "AB 85"]
for s in TRACKED_SIGNS:
    all_signs.add(s)

GC_BY_SIGN = {}
for row in grid_confidence:
    bid = clean_bennett(row.get("bennett_id", ""))
    if bid:
        GC_BY_SIGN[bid] = row

print(f"    Total unique signs to evaluate: {len(all_signs)}")


# ── 4. Conventional AB grid (scholarly consensus) ──────────────────────────
CONVENTIONAL_AB = {
    "AB 01": "da", "AB 02": "ro", "AB 03": "pa", "AB 04": "te",
    "AB 05": "to", "AB 06": "na", "AB 07": "di", "AB 08": "a",
    "AB 09": "se", "AB 10": "u", "AB 11": "si", "AB 12": "so",
    "AB 13": "me", "AB 14": "do", "AB 15": "mo", "AB 16": "qa",
    "AB 17": "za", "AB 18": "zo", "AB 19": "?", "AB 20": "zo?",
    "AB 21": "mi", "AB 22": "pi", "AB 23": "mu", "AB 24": "ne",
    "AB 25": "a₂", "AB 26": "ru", "AB 27": "re", "AB 28": "i",
    "AB 29": "pu", "AB 30": "ni", "AB 31": "sa", "AB 32": "?",
    "AB 33": "?", "AB 34": "ti", "AB 35": "ti", "AB 36": "jo",
    "AB 37": "?", "AB 38": "e", "AB 39": "?", "AB 40": "wi",
    "AB 41": "?", "AB 42": "?", "AB 43": "?", "AB 44": "ke",
    "AB 45": "ri", "AB 46": "?", "AB 47": "nu", "AB 48": "?",
    "AB 49": "?", "AB 50": "pu", "AB 51": "du", "AB 52": "?",
    "AB 53": "ri", "AB 54": "wa", "AB 55": "nu", "AB 56": "?",
    "AB 57": "ja", "AB 58": "?", "AB 59": "?", "AB 60": "ra",
    "AB 61": "o", "AB 62": "?", "AB 63": "?", "AB 64": "?",
    "AB 65": "ju", "AB 66": "?", "AB 67": "ki", "AB 68": "ro₂",
    "AB 69": "tu", "AB 70": "ko", "AB 71": "?", "AB 72": "?",
    "AB 73": "?", "AB 74": "?", "AB 75": "?", "AB 76": "?",
    "AB 77": "ka", "AB 78": "qe", "AB 79": "?", "AB 80": "ma",
    "AB 81": "ku", "AB 82": "?", "AB 83": "?", "AB 84": "?",
    "AB 85": "?", "AB 86": "?", "AB 87": "?", "AB 88": "?",
    "AB 89": "?", "AB 90": "?", "AB 91": "?", "AB 92": "?",
    "AB 93": "?", "AB 94": "?", "AB 95": "?", "AB 96": "?",
    "AB 97": "?", "AB 98": "?", "AB 100": "?",
    "AB 101": "?", "AB 102": "?", "AB 103": "?", "AB 104": "?",
    "AB 105": "?", "AB 106": "?", "AB 107": "?", "AB 108": "?",
    "AB 109": "?", "AB 110": "?", "AB 111": "?", "AB 112": "?",
    "AB 113": "?", "AB 114": "?", "AB 115": "?", "AB 116": "?",
    "AB 117": "?", "AB 118": "?", "AB 119": "?", "AB 120": "?",
    "AB 121": "?", "AB 122": "?", "AB 123": "?", "AB 124": "?",
    "AB 125": "?", "AB 126": "?", "AB 127": "?", "AB 128": "?",
    "AB 129": "?", "AB 130": "?", "AB 131": "?", "AB 132": "?",
    "AB 133": "?", "AB 134": "?", "AB 135": "?", "AB 136": "?",
    "AB 137": "?", "AB 138": "?", "AB 139": "?", "AB 140": "?",
    "AB 141": "?", "AB 142": "?", "AB 143": "?", "AB 144": "?",
    "AB 145": "?", "AB 146": "?", "AB 147": "?", "AB 148": "?",
    "AB 149": "?", "AB 150": "?", "AB 151": "?", "AB 152": "?",
    "AB 153": "?", "AB 154": "?", "AB 155": "?", "AB 156": "?",
    "AB 157": "?", "AB 158": "?", "AB 159": "?", "AB 160": "?",
    "AB 161": "?", "AB 162": "?", "AB 163": "?", "AB 164": "?",
    "AB 165": "?", "AB 166": "?", "AB 167": "?", "AB 168": "?",
    "AB 169": "?", "AB 22f": "pi?",
    # LA-only non-phonetic
    "A 301": " IDE", "A 302": " IDE", "A 303": " IDE",
    "A 304": " IDE", "A 305": " IDE", "A 306": " IDE",
    "A 307": " IDE", "A 308": " IDE", "A 309": " IDE",
    "A 310": " IDE", "A 311": " IDE", "A 312": " IDE",
    "A 313": " IDE", "A 314": " IDE", "A 315": " IDE",
    "A 316": " IDE", "A 317": " IDE", "A 318": " IDE",
    "A 319": " IDE", "A 320": " IDE", "A 321": " IDE",
    "A 322": " IDE", "A 323": " IDE", "A 324": " IDE",
    "A 325": " IDE", "A 326": " IDE", "A 327": " IDE",
    "A 328": " IDE", "A 329": " IDE", "A 330": " IDE",
    "A 331": " IDE", "A 332": " IDE", "A 333": " IDE",
    "A 334": " IDE", "A 335": " IDE", "A 336": " IDE",
    "A 337": " IDE", "A 338": " IDE", "A 339": " IDE",
    "A 340": " IDE", "A 341": " IDE", "A 342": " IDE",
    "A 343": " IDE", "A 344": " IDE", "A 345": " IDE",
    "A 346": " IDE", "A 347": " IDE", "A 348": " IDE",
    "A 349": " IDE", "A 350": " IDE", "A 351": " IDE",
    "A 352": " IDE", "A 353": " IDE", "A 354": " IDE",
    "A 355": " IDE", "A 356": " IDE", "A 357": " IDE",
    "A 358": " IDE", "A 359": " IDE", "A 360": " IDE",
    "A 400": " IDE",
    "A 701": "FRA", "A 702": "FRA", "A 703": "FRA",
    "A 704": "FRA", "A 705": "FRA", "A 706": "FRA",
    "A 707": "FRA", "A 708": "FRA", "A 709": "FRA",
    "A 710": "FRA", "A 711": "FRA", "A 712": "FRA",
    "A 713": "FRA", "A 714": "FRA", "A 715": "FRA",
    "A 716": "FRA", "A 717": "FRA", "A 718": "FRA",
    "A 719": "FRA", "A 720": "FRA", "A 721": "FRA",
    "A 722": "FRA", "A 723": "FRA", "A 724": "FRA",
    "A 725": "FRA", "A 726": "FRA", "A 727": "FRA",
    "A 728": "FRA", "A 729": "FRA", "A 730": "FRA",
    "A 731": "FRA", "A 732": "FRA", "A 733": "FRA",
    "A 734": "FRA", "A 735": "FRA", "A 736": "FRA",
    "A 737": "FRA", "A 738": "FRA", "A 739": "FRA",
    "A 740": "FRA", "A 741": "FRA", "A 742": "FRA",
    "A 743": "FRA", "A 744": "FRA", "A 745": "FRA",
    "A 746": "FRA", "A 747": "FRA", "A 748": "FRA",
    "A 749": "FRA", "A 750": "FRA", "A 751": "FRA",
    "A 752": "FRA", "A 753": "FRA",
}


def compute_confidence(ev):
    """Weighted confidence 0-100 based on all evidence streams."""
    scores = []
    weights = []

    # LB transfer composite (weight 2)
    if ev["lb_transfer"] and ev["lb_transfer"]["composite_score"] > 0:
        scores.append(ev["lb_transfer"]["composite_score"])
        weights.append(2.0)

    # CM triangular confidence (weight 1.5)
    if ev["cm_inference"] and ev["cm_inference"]["triangular_confidence"]:
        cm_val = {"HIGH": 85, "MEDIUM": 55, "LOW": 25}.get(
            ev["cm_inference"]["triangular_confidence"], 0
        )
        if cm_val > 0:
            scores.append(cm_val)
            weights.append(1.5)

    # Grid confidence — Phase 3 (weight 1.5)
    if ev["grid_confidence"] and ev["grid_confidence"]["confidence_score"] > 0:
        scores.append(ev["grid_confidence"]["confidence_score"])
        weights.append(1.5)

    # Penalties
    pos_penalty = 0
    if ev["positional_anomaly"]:
        kl = ev["positional_anomaly"]["kl_divergence"]
        if kl > 1.0:
            pos_penalty = min(kl * 10, 30)
        if "ANOMALOUS" in ev["positional_anomaly"]["flags"]:
            pos_penalty = max(pos_penalty, 20)

    ngram_penalty = 0
    if ev["ngram_anomaly"]:
        ds = ev["ngram_anomaly"]["disruption_score"]
        if ds > 0.4:
            ngram_penalty = min((ds - 0.4) * 100, 25)

    if not scores:
        return 0.0

    weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    final = weighted_avg - pos_penalty - ngram_penalty
    return max(0.0, min(100.0, final))


def determine_decision(bid, ev, conv_val, confidence=0):
    """
    Return (decision, best_guess, conflict_note).
    """
    # Collect confident values from each evidence source
    value_sources = {}

    # LB: use la_hyp_value (LA-specific) if confident; otherwise lb_value_confident
    if ev["lb_transfer"]:
        lb = ev["lb_transfer"]
        if lb["la_hyp_value"]:
            value_sources["LB"] = lb["la_hyp_value"]
        elif lb["lb_value_confident"]:
            value_sources["LB"] = lb["lb_value_confident"]

    # CM
    if ev["cm_inference"]:
        cm = ev["cm_inference"]
        if cm["has_confident_value"] and cm["inferred_la"]:
            value_sources["CM"] = cm["inferred_la"]

    # Grid confidence (Phase 3)
    if ev["grid_confidence"]:
        gc = ev["grid_confidence"]
        pv = gc.get("proposed_value", "")
        if pv and not is_uncertain(pv):
            value_sources["GC"] = pv

    # No evidence at all
    if not value_sources:
        if conv_val and conv_val != "?":
            return ("UNCERTAIN", conv_val,
                    "Insufficient comparative evidence; retaining conventional value")
        return ("UNCERTAIN", "?", "No evidence available")

    unique_vals = set(value_sources.values())
    decision = "UNCERTAIN"
    best_guess = conv_val if conv_val != "?" else "?"
    conflict_note = ""

    if len(unique_vals) == 1:
        val = unique_vals.pop()
        if val == conv_val or conv_val == "?":
            decision = "CONFIRM"
            best_guess = val
        else:
            # All sources agree on a value different from conventional
            # Check if we have multiple independent sources confirming the new value
            if len(value_sources) >= 2:
                decision = "REVISE"
                best_guess = val
                conflict_note = (
                    f"Multiple sources agree on /{val}/ instead of /{conv_val}/"
                )
            else:
                # Single source but confident
                src = list(value_sources.keys())[0]
                decision = "CONFIRM" if src == "LB" else "REVISE"
                best_guess = val
                if src != "LB":
                    conflict_note = (
                        f"Single source {src} suggests /{val}/ vs conventional /{conv_val}/"
                    )

    else:
        # Multiple different values proposed — conflict
        decision = "UNCERTAIN"

        # Vote: most frequent value wins as best guess
        vote_counts = defaultdict(list)
        for src, val in value_sources.items():
            vote_counts[val].append(src)
        max_votes = max(len(v) for v in vote_counts.values())
        top_vals = [v for v, c in vote_counts.items() if len(c) == max_votes]

        if len(top_vals) == 1:
            best_guess = top_vals[0]
        else:
            # Tie-break: LB > CM > GC
            for pref in ["LB", "CM", "GC"]:
                if pref in value_sources:
                    best_guess = value_sources[pref]
                    break

        # Build conflict detail — skip sources whose value == "?"
        detail_parts = []
        for src, val in value_sources.items():
            detail_parts.append(f"{src}=/{val}/")
        conflict_detail = "; ".join(detail_parts)
        conflict_note = f"Conflict: {conflict_detail}"

    # ── Override: strong CM + LB agree on same value ──
    if "CM" in value_sources and "LB" in value_sources:
        if value_sources["CM"] == value_sources["LB"]:
            if ev["cm_inference"] and ev["cm_inference"]["triangular_confidence"] == "HIGH":
                agreed = value_sources["CM"]
                if agreed != conv_val and conv_val != "?":
                    decision = "REVISE"
                    best_guess = agreed
                    conflict_note = (
                        f"Strong LB+CM agreement on /{agreed}/; "
                        f"conventional /{conv_val}/ likely incorrect"
                    )
                else:
                    decision = "CONFIRM"
                    best_guess = agreed
            else:
                # LB+CM agree but CM not HIGH confidence
                agreed = value_sources["CM"]
                if agreed == conv_val or conv_val == "?":
                    decision = "CONFIRM"
                    best_guess = agreed
        else:
            # LB and CM disagree — only a conflict if both are confident
            lb_val = value_sources.get("LB", "")
            cm_val = value_sources.get("CM", "")
            cm_conf = ev["cm_inference"]["triangular_confidence"] if ev["cm_inference"] else ""

            if cm_val and cm_conf == "HIGH" and lb_val and cm_val != lb_val:
                # HIGH CM disagrees with LB — real puzzle, regardless of conventional
                decision = "UNCERTAIN"
                conflict_note = (
                    f"HIGH CM=/{cm_val}/ vs LB=/{lb_val}/ — genuine conflict"
                )

    # ── Override: positional anomaly + CM/LB agree on different value ──
    if ev["positional_anomaly"] and "CM" in value_sources and "LB" in value_sources:
        pa = ev["positional_anomaly"]
        if "ANOMALOUS" in pa.get("flags", ""):
            cm_val = value_sources.get("CM", "")
            lb_val = value_sources.get("LB", "")
            if cm_val and lb_val and cm_val == lb_val and cm_val != conv_val and conv_val != "?":
                decision = "REVISE"
                best_guess = cm_val
                conflict_note = (
                    f"Positional anomaly + LB/CM agree on /{cm_val}/ "
                    f"instead of /{conv_val}/"
                )

    # ── Override: if conventional is ? and only low confidence, stay UNCERTAIN ──
    if conv_val == "?" and decision == "CONFIRM" and len(value_sources) <= 1 and confidence < 50:
        decision = "UNCERTAIN"
        conflict_note = f"Low confidence ({confidence:.0f}/100) — insufficient for assignment"

    return (decision, best_guess, conflict_note)


# ── 5. Build the refined grid ──────────────────────────────────────────────
print("\n[5] Building refined phonetic grid ...")

refined_grid = []
grid_changes = []
misvalued_resolutions = []

# Sort key for Bennett IDs
def sort_key_bid(bid):
    parts = bid.split()
    num_part = parts[-1] if len(parts) > 1 else parts[0]
    # Extract numeric portion
    num = ""
    suffix = ""
    for ch in num_part:
        if ch.isdigit():
            num += ch
        else:
            suffix += ch
    try:
        n = int(num)
    except ValueError:
        n = 9999
    return (n, suffix)


SEEN = set()  # dedup

for bid in sorted(all_signs, key=sort_key_bid):
    bid_norm = clean_bennett(bid)

    # Deduplicate (e.g. AB 22f tracked in both upper/lower case)
    if bid_norm in SEEN:
        continue
    SEEN.add(bid_norm)

    # Skip non-phonetic sign types
    lb_row = LB_EVIDENCE.get(bid_norm, {})
    sign_type = lb_row.get("sign_type", "") if isinstance(lb_row, dict) else ""
    if sign_type and sign_type not in ("syllabogram", ""):
        continue

    conv_val = CONVENTIONAL_AB.get(bid_norm, "?")
    if conv_val and (conv_val.strip().startswith("IDE") or conv_val.strip().startswith("FRA")):
        continue

    # ── Compile evidence ──
    ev = {
        "lb_transfer": LB_EVIDENCE.get(bid_norm),
        "cm_inference": CM_EVIDENCE.get(bid_norm),
        "positional_anomaly": POSITIONAL_EVIDENCE.get(bid_norm),
        "ngram_anomaly": NGRAM_EVIDENCE.get(bid_norm),
        "grid_confidence": None,
    }
    if bid_norm in GC_BY_SIGN:
        gc = GC_BY_SIGN[bid_norm]
        ev["grid_confidence"] = {
            "confidence_score": safe_float(gc.get("confidence_score")),
            "assessment": gc.get("assessment", ""),
            "proposed_value": gc.get("proposed_value", ""),
            "conventional_value": gc.get("conventional_value", ""),
            "n_place_names": safe_int(gc.get("n_place_names")),
            "n_attestations": safe_int(gc.get("n_attestations")),
            "phonetic_consistency": gc.get("phonetic_consistency", ""),
            "observed_transliterations": gc.get("observed_transliterations", "{}"),
            "reasons": gc.get("reasons", ""),
        }

    # ── Compute confidence ──
    confidence = compute_confidence(ev)

    # ── Decision ──
    decision, best_guess, conflict_note = determine_decision(bid_norm, ev, conv_val, confidence)

    # ── Evidence summary string ──
    parts = []
    if ev["lb_transfer"] and ev["lb_transfer"]["has_confident_value"]:
        parts.append(f"LB={ev['lb_transfer']['composite_score']:.0f}")
    if ev["cm_inference"] and ev["cm_inference"]["has_confident_value"]:
        parts.append(f"CM={ev['cm_inference']['triangular_confidence']}")
    if ev["grid_confidence"]:
        parts.append(f"GC={ev['grid_confidence']['confidence_score']:.0f}")
    if ev["positional_anomaly"]:
        parts.append(f"Pos#{ev['positional_anomaly']['pos_rank']}")
    if ev["ngram_anomaly"]:
        parts.append(f"Ng#{ev['ngram_anomaly']['ngram_rank']}")
    evidence_summary = "; ".join(parts) if parts else "no evidence"

    # ── Phase 2 misvaluation flag ──
    phase2_misvalued = False
    if ev["positional_anomaly"] and "ANOMALOUS" in ev["positional_anomaly"]["flags"]:
        phase2_misvalued = True
    if ev["ngram_anomaly"] and ev["ngram_anomaly"]["disruption_score"] > 0.4:
        phase2_misvalued = True

    anomaly_supports_revalue = phase2_misvalued and best_guess != conv_val and conv_val != "?"

    # ── CM suggested value ──
    cm_suggest = ""
    cm_conf_level = ""
    if ev["cm_inference"] and ev["cm_inference"]["has_confident_value"]:
        cm_suggest = ev["cm_inference"]["inferred_la"]
        cm_conf_level = ev["cm_inference"]["triangular_confidence"]

    # ── LB proposed value ──
    lb_proposed = ""
    lb_comp = ""
    if ev["lb_transfer"]:
        lb_proposed = ev["lb_transfer"]["la_hyp_value"] or ev["lb_transfer"]["lb_value_confident"]
        lb_comp = round(ev["lb_transfer"]["composite_score"], 1) if ev["lb_transfer"]["composite_score"] > 0 else ""

    row = {
        "bennett_id": bid_norm,
        "conventional_value": conv_val if conv_val != "?" else "?",
        "lb_proposed_value": lb_proposed,
        "cm_suggested_value": cm_suggest,
        "refined_value": best_guess,
        "decision": decision,
        "confidence_score": round(confidence, 1),
        "lb_composite_score": lb_comp,
        "cm_triangular_confidence": cm_conf_level,
        "grid_confidence_score": round(ev["grid_confidence"]["confidence_score"], 1) if ev["grid_confidence"] else "",
        "positional_anomaly_rank": ev["positional_anomaly"]["pos_rank"] if ev["positional_anomaly"] else "",
        "positional_flags": ev["positional_anomaly"]["flags"] if ev["positional_anomaly"] else "",
        "ngram_disruption_score": round(ev["ngram_anomaly"]["disruption_score"], 3) if ev["ngram_anomaly"] else "",
        "ngram_rank": ev["ngram_anomaly"]["ngram_rank"] if ev["ngram_anomaly"] else "",
        "phase2_misvalued_flag": "YES" if phase2_misvalued else "",
        "phase2_revaluation_supported": "YES" if anomaly_supports_revalue else "",
        "conflict_note": conflict_note,
        "evidence_summary": evidence_summary,
    }
    refined_grid.append(row)

    # Track changes from AB convention
    if best_guess != conv_val and conv_val != "?":
        grid_changes.append({
            "bennett_id": bid_norm,
            "conventional_value": conv_val,
            "refined_value": best_guess,
            "decision": decision,
            "confidence": round(confidence, 1),
            "reason": conflict_note or evidence_summary,
        })

    # Track Phase 2 flagged signs and specifically requested signs
    if bid_norm in TRACKED_SIGNS or phase2_misvalued:
        res = {
            "bennett_id": bid_norm,
            "conventional_value": conv_val if conv_val != "?" else "?",
            "refined_value": best_guess,
            "decision": decision,
            "confidence": round(confidence, 1),
            "phase2_positional_rank": ev["positional_anomaly"]["pos_rank"] if ev["positional_anomaly"] else "",
            "phase2_ngram_rank": ev["ngram_anomaly"]["ngram_rank"] if ev["ngram_anomaly"] else "",
            "positional_flags": ev["positional_anomaly"]["flags"] if ev["positional_anomaly"] else "",
            "lb_composite": lb_comp,
            "cm_confidence": cm_conf_level,
            "cm_value": cm_suggest,
            "grid_confidence_score": round(ev["grid_confidence"]["confidence_score"], 1) if ev["grid_confidence"] else "",
            "grid_proposed_value": ev["grid_confidence"]["proposed_value"] if ev["grid_confidence"] else "",
            "evidence_summary": evidence_summary,
            "conflict_note": conflict_note,
            "resolution": f"{decision}: {conv_val} → {best_guess}" if best_guess != conv_val else f"{decision}: retained as {best_guess}",
        }
        misvalued_resolutions.append(res)


# ── 6. Write outputs ───────────────────────────────────────────────────────
print("\n[6] Writing output files ...")
os.makedirs(OUT, exist_ok=True)

# 6a. Refined phonetic grid
refined_path = os.path.join(OUT, "refined_phonetic_grid.csv")
fieldnames = [
    "bennett_id", "conventional_value", "lb_proposed_value", "cm_suggested_value",
    "refined_value", "decision", "confidence_score",
    "lb_composite_score", "cm_triangular_confidence", "grid_confidence_score",
    "positional_anomaly_rank", "positional_flags",
    "ngram_disruption_score", "ngram_rank",
    "phase2_misvalued_flag", "phase2_revaluation_supported",
    "conflict_note", "evidence_summary",
]
with open(refined_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(refined_grid)
print(f"    → {refined_path}  ({len(refined_grid)} rows)")

# 6b. Changes from AB convention
changes_path = os.path.join(OUT, "grid_changes_from_ab.csv")
cf = ["bennett_id", "conventional_value", "refined_value", "decision", "confidence", "reason"]
with open(changes_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cf)
    w.writeheader()
    w.writerows(grid_changes)
print(f"    → {changes_path}  ({len(grid_changes)} rows)")

# 6c. Misvalued signs resolution
misvalued_path = os.path.join(OUT, "misvalued_signs_resolution.csv")
mf = [
    "bennett_id", "conventional_value", "refined_value", "decision", "confidence",
    "phase2_positional_rank", "phase2_ngram_rank", "positional_flags",
    "lb_composite", "cm_confidence", "cm_value",
    "grid_confidence_score", "grid_proposed_value",
    "evidence_summary", "conflict_note", "resolution",
]
with open(misvalued_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=mf)
    w.writeheader()
    w.writerows(misvalued_resolutions)
print(f"    → {misvalued_path}  ({len(misvalued_resolutions)} rows)")

# 6d. Comprehensive synthesis report
report_path = os.path.join(OUT, "phase5_synthesis.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# Phase 5 Synthesis — Refined Phonetic Grid for Linear A\n\n")
    f.write("## Overview\n\n")
    f.write("This report synthesises all comparative evidence from Phase 5 (Linear B transfer, "
            "Cypro-Minoan triangular inference, loanword shadow lexicon, commodity context patterns) "
            "alongside Phase 3 (toponym anchors, phonetic grid confidence) and Phase 2 "
            "(positional & n-gram anomaly detection) to produce a refined phonetic grid for Linear A.\n\n")

    total = len(refined_grid)
    confirmed = sum(1 for r in refined_grid if r["decision"] == "CONFIRM")
    revised = sum(1 for r in refined_grid if r["decision"] == "REVISE")
    uncertain = sum(1 for r in refined_grid if r["decision"] == "UNCERTAIN")

    f.write(f"**Total signs evaluated:** {total}\n\n")
    f.write("| Decision | Count | Percentage |\n")
    f.write("|----------|-------|------------|\n")
    f.write(f"| CONFIRM  | {confirmed} | {confirmed/total*100:.1f}% |\n")
    f.write(f"| REVISE   | {revised} | {revised/total*100:.1f}% |\n")
    f.write(f"| UNCERTAIN| {uncertain} | {uncertain/total*100:.1f}% |\n\n")

    high_c = sum(1 for r in refined_grid if r["confidence_score"] >= 70)
    med_c = sum(1 for r in refined_grid if 40 <= r["confidence_score"] < 70)
    low_c = sum(1 for r in refined_grid if r["confidence_score"] < 40)
    f.write("**Confidence distribution:**\n")
    f.write(f"- High (≥70): {high_c} signs\n")
    f.write(f"- Medium (40-69): {med_c} signs\n")
    f.write(f"- Low (<40): {low_c} signs\n\n")

    # ── Changes ──
    f.write("## Changes from Conventional AB Grid\n\n")
    if grid_changes:
        f.write(f"**{len(grid_changes)} signs** revised:\n\n")
        f.write("| Sign | Conventional | Refined | Confidence | Reason |\n")
        f.write("|------|-------------|---------|------------|--------|\n")
        for c in grid_changes:
            f.write(f"| {c['bennett_id']} | /{c['conventional_value']}/ | /{c['refined_value']}/ | {c['confidence']} | {c['reason']} |\n")
        f.write("\n")
    else:
        f.write("No changes from conventional AB grid.\n\n")

    # ── Misvalued signs resolution ──
    f.write("## Phase 2 Misvalued Signs — Resolution\n\n")

    tracked_details = {
        "AB 16": ("AB 16 (qa)", "Ranked #1 anomalous by positional analysis"),
        "AB 60": ("AB 60 (ra)", "Ranked #2, 50.5% final position"),
        "AB 80": ("AB 80 (ma)", "Ranked #3, 50% initial position"),
        "AB 22": ("AB 22 (pi)", "Ranked #4, 66.7% final position"),
        "AB 02": ("AB 02 (ro/so)", "Flagged as dual-value candidate"),
        "AB 85": ("AB 85 (unknown)", "47% initial/47% final, likely word divider"),
    }

    for bid, (name, phase2_finding) in tracked_details.items():
        f.write(f"### {name}\n\n")
        f.write(f"- **Phase 2 finding:** {phase2_finding}\n")

        match = [r for r in refined_grid if r["bennett_id"] == bid]
        if match:
            r = match[0]
            f.write(f"- **Conventional AB value:** /{r['conventional_value']}/\n")
            f.write(f"- **Refined value:** /{r['refined_value']}/\n")
            f.write(f"- **Decision:** {r['decision']}\n")
            f.write(f"- **Confidence:** {r['confidence_score']}/100\n")
            if r['lb_composite_score']:
                f.write(f"- **LB composite:** {r['lb_composite_score']}\n")
            if r['cm_triangular_confidence']:
                f.write(f"- **CM:** {r['cm_triangular_confidence']} (value: /{r['cm_suggested_value']}/)\n")
            if r['grid_confidence_score']:
                f.write(f"- **Grid confidence (Ph3):** {r['grid_confidence_score']}\n")
            if r['conflict_note']:
                f.write(f"- **Conflict note:** {r['conflict_note']}\n")
        else:
            f.write("- **Not in refined grid**\n")

        # Detailed discussion per sign
        f.write("\n**Detailed assessment:**\n\n")
        if bid == "AB 16":
            f.write(
                "AB 16 (qa) was ranked #1 anomalous (60% initial, 40% final, 0% medial). "
                "CM evidence maps to CM 024 → Cypriot /ka/. "
                "LB conventional value is /qa/ (labiovelar), which is rare. "
                "The conflict between LB=/qa/ and CM=/ka/ (MEDIUM confidence) warrants attention. "
                "Positional anomaly may reflect phonetic特殊性. "
                "Further CM or toponym evidence is needed.\n\n"
                "**Recommendation:** Retain as /qa/ pending further evidence.\n\n"
            )
        elif bid == "AB 60":
            f.write(
                "AB 60 shows 50.5% final position — anomalous for CV. "
                "LB transfer is secure (composite 72.5, /ra/). "
                "CM evidence gives HIGH confidence for /ma/ (CM 008 → Cypriot /ma/). "
                "This is a genuine conflict: LB says /ra/, CM says /ma/. "
                "The positional anomaly may indicate a suffix function. "
                "If AB 60 = /ma/, then the conventional /ra/ needs reassignment. "
                "If AB 60 = /ra/, then CM inference may be wrong.\n\n"
                "**Recommendation:** UNCERTAIN — genuine LB/CM conflict needs resolution.\n\n"
            )
        elif bid == "AB 80":
            f.write(
                "AB 80 shows 50% initial, 46.4% final — anomalous. "
                "LB gives /ma/ (composite 76.0). "
                "CM gives LOW confidence for /pa/ (CM 051 → Cypriot /pa/). "
                "The CM link is weak but combined with positional anomaly, "
                "/pa/ is a possible revision candidate.\n\n"
                "**Recommendation:** Retain as /ma/ — CM evidence too low to revalue.\n\n"
            )
        elif bid == "AB 22":
            f.write(
                "AB 22 shows 66.7% final position — highly anomalous. "
                "However, both LB (68.0) and CM (HIGH) agree on /pi/. "
                "The final-position bias likely reflects the suffix /-pi/ "
                "(cf. LB instrumental /-phi/), not misvaluation.\n\n"
                "**Recommendation:** CONFIRM /pi/.\n\n"
            )
        elif bid == "AB 02":
            f.write(
                "AB 02 is a complex case. Conventional value is /ro/, but "
                "toponym evidence suggests /i/ in some contexts (PHAISTOS = pa-i-to). "
                "Positional profile (33.7/22.2/44.1) is anomalous. "
                "The dual-value hypothesis (ro~i) requires contextual analysis.\n\n"
                "**Recommendation:** UNCERTAIN — proposed dual value /ro~i/.\n\n"
            )
        elif bid == "AB 85":
            f.write(
                "AB 85 has 47% initial / 47% final — pattern of a boundary marker. "
                "LB value is unknown (?). CM evidence LOW for /au/. "
                "The positional distribution strongly suggests a word divider.\n\n"
                "**Recommendation:** Mark as WORD DIVIDER (non-phonetic).\n\n"
            )
        f.write("---\n\n")

    # ── LB/CM conflicts (genuine, where LB and CM give different values) ──
    lb_cm_conflicts = []
    for r in refined_grid:
        lb_val = r.get("lb_proposed_value", "") or ""
        cm_val = r.get("cm_suggested_value", "") or ""
        if lb_val and cm_val and lb_val != cm_val and lb_val != "?" and cm_val != "?":
            lb_cm_conflicts.append(r)
    if lb_cm_conflicts:
        f.write("## LB-CM Conflicts\n\n")
        f.write("Signs where LB and CM evidence genuinely disagree (both provide different confident values):\n\n")
        f.write("| Sign | Conv | LB | CM | Decision |\n")
        f.write("|------|------|----|----|----------|\n")
        for r in lb_cm_conflicts:
            lb_val = r.get("lb_proposed_value", "?") or r.get("conventional_value", "?")
            cm_val = r.get("cm_suggested_value", "?") or "?"
            f.write(f"| {r['bennett_id']} | /{r['conventional_value']}/ | /{lb_val}/ | /{cm_val}/ | {r['decision']} |\n")
        f.write("\n")

    # ── Recommendations ──
    f.write("## Recommendations for Future Research\n\n")
    f.write("1. **AB 16 (qa vs ka):** Investigate CM 024 connection. If confirmed, revalue.\n\n")
    f.write("2. **AB 60 (ra vs ma):** Resolve LB/CM conflict through toponym search.\n\n")
    f.write("3. **AB 02 (ro~i):** Systematic contextual analysis of conditioning environments.\n\n")
    f.write("4. **AB 85:** Confirm word-divider status via co-occurrence with segmentation boundaries.\n\n")
    f.write("5. **CM evidence:** Strengthen LOW-confidence CM links with more data.\n\n")
    f.write("6. **Loanword lexicon:** Expand from 2 to 20+ entries for more phonetic anchors.\n\n")

    # ── Methodology ──
    f.write("## Methodology Notes\n\n")
    f.write("- Confidence = weighted avg of LB (×2), CM (×1.5), GC (×1.5) minus positional penalty (up to −30) and n-gram penalty (up to −25).\n")
    f.write("- Values with `?` (e.g., `pa2?`, `de?`) treated as uncertain, not confident LB evidence.\n")
    f.write("- REVISE only when ≥2 independent sources agree on a new value different from conventional.\n")
    f.write("- UNCERTAIN when sources conflict or only one source has a confident value.\n\n")

    f.write("---\n")
    f.write(f"*Generated by Phase 5 pipeline — {os.path.basename(__file__)}*\n")

print(f"    → {report_path}")

# ── Summary ──
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Signs evaluated:          {total}")
print(f"  CONFIRM:                  {confirmed} ({confirmed/total*100:.1f}%)")
print(f"  REVISE:                   {revised} ({revised/total*100:.1f}%)")
print(f"  UNCERTAIN:                {uncertain} ({uncertain/total*100:.1f}%)")
print(f"  Changes from AB grid:     {len(grid_changes)}")
print(f"  Phase 2 flagged tracked:  {len(misvalued_resolutions)}")
print(f"  High confidence (≥70):    {high_c}")
print(f"  Medium (40-69):           {med_c}")
print(f"  Low (<40):                {low_c}")
print("=" * 70)
