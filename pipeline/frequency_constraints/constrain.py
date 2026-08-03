#!/usr/bin/env python3
"""
constrain.py — Use frequency distributions + Kober grid links to eliminate
impossible phoneme classes for each UNCERTAIN sign.

Inputs:
  - data/analysis/frequency_constraints/frequency_profile.csv
  - data/analysis/bootstrapping/expanded_grid.csv
  - data/analysis/kober/grid_series.csv
  - data/analysis/kober/triple_patterns.csv
  - data/database/lineara_full.db (for frequency lookup)

Outputs:
  - data/analysis/frequency_constraints/constrained_candidates.csv
  - data/analysis/frequency_constraints/frequency_report.md

Method:
  1. For each UNCERTAIN sign, get its observed corpus frequency.
  2. For each consonant class and vowel row, check if frequency is within
     the expected envelope (mean ± 2σ, or IQR-based outlier bounds).
  3. Cross-reference with Kober grid series: same-series CONFIRMED signs
     constrain either consonant or vowel (not both).
  4. Cross-reference with Kober triples: shared preceding/following contexts
     with CONFIRMED signs constrain the phonetic space.
  5. Eliminate phoneme classes whose frequency envelope excludes the
     observed frequency.
"""

import csv
import logging
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "database" / "lineara_full.db"
GRID_PATH = PROJECT_ROOT / "data" / "analysis" / "bootstrapping" / "expanded_grid.csv"
PROFILE_PATH = PROJECT_ROOT / "data" / "analysis" / "frequency_constraints" / "frequency_profile.csv"
SERIES_PATH = PROJECT_ROOT / "data" / "analysis" / "kober" / "grid_series.csv"
TRIPLES_PATH = PROJECT_ROOT / "data" / "analysis" / "kober" / "triple_patterns.csv"
OUT_DIR = PROJECT_ROOT / "data" / "analysis" / "frequency_constraints"
CANDIDATES_PATH = OUT_DIR / "constrained_candidates.csv"
REPORT_PATH = OUT_DIR / "frequency_report.md"

CONSONANT_CLASSES: dict[str, set[str]] = {
    "DENTAL": {"t", "d", "n"},
    "LABIAL": {"p", "m"},
    "VELAR":  {"k"},
    "SIBILANT": {"s", "z"},
    "LIQUID": {"r", "l"},
    "PALATAL": {"j"},
    "SEMIVOWEL": {"w"},
    "VOWEL": {""},
}

VOWELS: list[str] = ["a", "e", "i", "o", "u"]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_freqs() -> dict[str, int]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT bennett_id, COUNT(*) AS freq FROM signs "
        "WHERE sign_type = 'syllabogram' AND bennett_id != '' "
        "GROUP BY bennett_id"
    )
    return {r["bennett_id"]: r["freq"] for r in c.fetchall()}


def load_grid() -> list[dict]:
    with open(GRID_PATH, newline="") as f:
        return list(csv.DictReader(f))


def load_profile() -> dict[str, dict]:
    """Load frequency_profile.csv, keyed by profile_label."""
    profile: dict[str, dict] = {}
    with open(PROFILE_PATH, newline="") as f:
        for r in csv.DictReader(f):
            profile[r["profile_label"]] = r
    return profile


def load_series() -> dict[str, list[str]]:
    """Load grid_series.csv -> {series_label: [bennett_id, ...]}"""
    series: dict[str, list[str]] = defaultdict(list)
    with open(SERIES_PATH, newline="") as f:
        for r in csv.DictReader(f):
            series[r["series_label"]].append(r["bennett_id"])
    return dict(series)


def load_triples() -> list[dict]:
    with open(TRIPLES_PATH, newline="") as f:
        return list(csv.DictReader(f))


def parse_cv(refined_value: str) -> tuple[str | None, str | None]:
    if not refined_value or refined_value.strip() in ("?", ""):
        return None, None
    val = refined_value.strip().lower()
    if val in ("a", "e", "i", "o", "u"):
        return "", val
    consonant = val[0]
    rest = val[1:]
    if len(val) >= 3 and val[:2] in (
        "kh", "th", "ph", "ts", "dz", "kw", "gw", "tw", "dw", "sw", "qw",
    ):
        consonant = val[:2]
        rest = val[2:]
    for i, ch in enumerate(rest):
        if ch in "aeiou":
            if i > 0:
                consonant += rest[:i]
            return consonant, rest[i:]
    return consonant, ""


def classify_sign(c: str | None, v: str | None) -> tuple[str | None, str | None]:
    if c is None or v is None:
        return None, None
    for cls_label, consonants in CONSONANT_CLASSES.items():
        if c in consonants:
            return cls_label, v if v in VOWELS else None
    return None, None


# ---------------------------------------------------------------------------
# Frequency constraint logic
# ---------------------------------------------------------------------------

def within_envelope(freq: int, stats: dict, n_std: float = 2.0) -> tuple[bool, float]:
    """Check if freq falls within mean ± n_std * std of the profile stats.

    Returns (plausible, z_score). Higher z_score = further from mean.
    """
    mean_str = stats.get("mean")
    std_str = stats.get("std")
    if mean_str is None or std_str is None:
        return True, 0.0  # insufficient data → can't eliminate
    mean = float(mean_str)
    std = float(std_str)
    if std == 0:
        return abs(freq - mean) < 1, abs(freq - mean)
    z = abs(freq - mean) / std
    return z <= n_std, z


def within_iqr(freq: int, stats: dict, multiplier: float = 1.5) -> tuple[bool, float]:
    """Check if freq is within [p25 - 1.5*IQR, p75 + 1.5*IQR]."""
    p25_str = stats.get("p25")
    p75_str = stats.get("p75")
    if p25_str is None or p75_str is None:
        return True, 0.0
    p25 = float(p25_str)
    p75 = float(p75_str)
    iqr = p75 - p25
    lower = p25 - multiplier * iqr
    upper = p75 + multiplier * iqr
    # distance from nearest bound (negative = inside)
    if freq < lower:
        return False, (lower - freq) / max(iqr, 1)
    if freq > upper:
        return False, (freq - upper) / max(iqr, 1)
    return True, 0.0


def frequency_percentile(freq: int, stats: dict) -> float | None:
    """Approximate percentile of freq within the profile's distribution.

    Uses min/max/p50 for crude interpolation.
    """
    p50_str = stats.get("p50")
    min_str = stats.get("min")
    max_str = stats.get("max")
    if p50_str is None or min_str is None or max_str is None:
        return None
    p50 = float(p50_str)
    pmin = float(min_str)
    pmax = float(max_str)
    if pmax == pmin:
        return 50.0
    # Linear percentile between min/max, anchored at p50 = 0.5
    return (freq - pmin) / (pmax - pmin) * 100


# ---------------------------------------------------------------------------
# Kober grid constraint logic
# ---------------------------------------------------------------------------

def get_series_membership(bennett_id: str, series: dict[str, list[str]]) -> str | None:
    """Return which Kober series a sign belongs to."""
    for label, members in series.items():
        if bennett_id in members:
            return label
    return None


def get_series_partner_phonemes(
    bennett_id: str,
    series: dict[str, list[str]],
    grid: list[dict],
) -> tuple[set[str], set[str]]:
    """Return (shared_consonant_classes, shared_vowels) from CONFIRMED series partners.

    If all CONFIRMED partners share a consonant, that constrains the unknown.
    Likewise for vowels.
    """
    series_label = get_series_membership(bennett_id, series)
    if series_label is None:
        return set(), set()

    members = series[series_label]
    grid_map = {r["bennett_id"]: r for r in grid}

    partner_consonant_classes: set[str] = set()
    partner_vowels: set[str] = set()

    for member in members:
        if member == bennett_id:
            continue
        gm = grid_map.get(member)
        if gm is None or gm["decision"] != "CONFIRM":
            continue
        c, v = parse_cv(gm.get("refined_value", ""))
        cc, vv = classify_sign(c, v)
        if cc:
            if cc == "VOWEL":
                # Pure vowel sign - contributes to vowel constraint only
                pass  # vowel already captured
            partner_consonant_classes.add(cc)
        if vv:
            partner_vowels.add(vv)

    return partner_consonant_classes, partner_vowels


def get_triple_partner_constraints(
    bennett_id: str,
    triples: list[dict],
    grid: list[dict],
) -> dict:
    """From Kober triples, collect constraints from CONFIRMED partners.

    If AB X, AB Y, AB Z form a triple (shared following+preceding context),
    and we know X's vowel, that constrains Y and Z to share either consonant
    OR vowel with X. We collect the shared context patterns.

    Returns deduplicated partner sets (unique confirmed partners, not total
    triple rows).
    """
    grid_map = {r["bennett_id"]: r for r in grid}

    unique_partners: set[str] = set()  # unique bennett_ids of confirmed partners
    num_triples = 0

    for t in triples:
        s1, s2, s3 = t["sign_1"], t["sign_2"], t["sign_3"]
        if bennett_id not in (s1, s2, s3):
            continue
        num_triples += 1

        for s in (s1, s2, s3):
            if s == bennett_id:
                continue
            gm = grid_map.get(s)
            if gm is None or gm["decision"] != "CONFIRM":
                continue
            c, v = parse_cv(gm.get("refined_value", ""))
            cc, vv = classify_sign(c, v)
            if cc is not None and vv is not None:
                unique_partners.add(s)

    # Collect shared consonant classes and vowels from unique partners
    linked_cc: set[str] = set()
    linked_v: set[str] = set()
    for s in unique_partners:
        gm = grid_map[s]
        c, v = parse_cv(gm.get("refined_value", ""))
        cc, vv = classify_sign(c, v)
        if cc:
            linked_cc.add(cc)
        if vv:
            linked_v.add(vv)

    return {
        "linked_cc": linked_cc,
        "linked_v": linked_v,
        "num_triples": num_triples,
        "num_confirmed_partners": len(unique_partners),
    }


# ---------------------------------------------------------------------------
# Main constraint logic
# ---------------------------------------------------------------------------

def constrain_sign(
    bennett_id: str,
    freq: int,
    profile: dict[str, dict],
    series: dict[str, list[str]],
    triples: list[dict],
    grid: list[dict],
) -> dict:
    """For one sign, evaluate all consonant_class × vowel candidates."""

    # Get series partner info
    series_cc, series_v = get_series_partner_phonemes(bennett_id, series, grid)

    # Get triple partner info
    triple_constraints = get_triple_partner_constraints(bennett_id, triples, grid)

    results: dict[str, list[dict]] = {"candidates": [], "eliminated": []}

    # All possible consonant classes
    all_cc = list(CONSONANT_CLASSES.keys())
    all_v = list(VOWELS)

    total_candidates = 0
    eliminated = 0

    for cc in all_cc:
        # Get frequency envelope for this consonant class
        cc_stats = profile.get(cc)
        if cc_stats is None:
            continue

        # Check consonant class frequency plausibility
        cc_plausible_iqr, cc_dist_iqr = within_iqr(freq, cc_stats)
        cc_plausible_std, cc_z = within_envelope(freq, cc_stats, 2.0)

        for v in all_v:
            total_candidates += 1
            reasons_to_keep: list[str] = []
            reasons_to_eliminate: list[str] = []

            # --- Frequency checks ---
            # CV slot frequency
            cv_key = f"{cc}_{v}"
            cv_stats = profile.get(cv_key)
            cv_plausible = True
            cv_dist = 0.0
            if cv_stats:
                cv_plausible, cv_dist = within_envelope(freq, cv_stats, 2.0)
                if not cv_plausible:
                    reasons_to_eliminate.append(
                        f"frequency {freq} outside {cc}/{v} envelope "
                        f"(mean={cv_stats.get('mean')}, std={cv_stats.get('std')})"
                    )

            # Consonant class frequency check (only if CV slot check can't decide)
            if cv_stats is None and not cc_plausible_iqr:
                reasons_to_eliminate.append(
                    f"frequency {freq} outside {cc} IQR envelope "
                    f"(p50={cc_stats.get('p50')}, IQR="
                    f"[{cc_stats.get('p25')}-{cc_stats.get('p75')}])"
                )

            # Vowel row frequency check
            v_stats = profile.get(f"{v} ({_vowel_name(v)})")
            if v_stats:
                v_plausible, v_z = within_envelope(freq, v_stats, 2.0)
                if not v_plausible and freq > 200:
                    reasons_to_eliminate.append(
                        f"frequency {freq} unusually high for {v}-row "
                        f"(mean={v_stats.get('mean')}, std={v_stats.get('std')})"
                    )

            # --- Kober series checks ---
            series_label = get_series_membership(bennett_id, series)
            if series_label:
                if series_cc and cc not in series_cc:
                    # Not in same consonant class as partners
                    # BUT: series can share vowel instead of consonant
                    # Don't eliminate yet unless vowel also doesn't match
                    if series_v and v not in series_v:
                        reasons_to_eliminate.append(
                            f"Kober series '{series_label}': "
                            f"neither consonant ({cc} not in {series_cc}) "
                            f"nor vowel ({v} not in {series_v}) "
                            f"matches series partners"
                        )
                    else:
                        reasons_to_keep.append(
                            f"Kober series '{series_label}': "
                            f"vowel {v} matches series partners {series_v}"
                        )
                elif series_v and v in series_v and cc not in series_cc:
                    reasons_to_keep.append(
                        f"Kober series '{series_label}': vowel {v} matches"
                    )
                elif series_cc and cc in series_cc and series_v and v not in series_v:
                    reasons_to_keep.append(
                        f"Kober series '{series_label}': consonant {cc} matches"
                    )

            # --- Kober triple checks ---
            if triple_constraints["linked_cc"] and cc in triple_constraints["linked_cc"]:
                reasons_to_keep.append(
                    f"Kober triples: consonant class {cc} matches "
                    f"{triple_constraints['num_confirmed_partners']} confirmed partners"
                )
            if triple_constraints["linked_v"] and v in triple_constraints["linked_v"]:
                reasons_to_keep.append(
                    f"Kober triples: vowel {v} matches confirmed partners"
                )

            # --- Decision ---
            # Decision hierarchy:
            # 1. Strong frequency contradiction → eliminated UNLESS Kober rescue
            #    (consonant AND vowel both match)
            # 2. Kober contradiction (neither C nor V matches series) → eliminated
            # 3. Weak frequency + no Kober support → eliminated

            freq_contradiction = (
                (cv_stats is not None and not cv_plausible)
                or (cv_stats is None and not cc_plausible_iqr and freq > 10)
            )
            kober_contradiction = (
                series_cc and series_v
                and cc not in series_cc and v not in series_v
            )
            kober_rescue = (
                (series_cc and cc in series_cc)
                or (series_v and v in series_v)
                or (triple_constraints["linked_cc"] and cc in triple_constraints["linked_cc"])
                or (triple_constraints["linked_v"] and v in triple_constraints["linked_v"])
            )
            low_freq_class = cc in {"SIBILANT", "SEMIVOWEL"}

            # Decision logic:
            if kober_contradiction:
                is_eliminated = True
            elif freq_contradiction and not kober_rescue:
                is_eliminated = True
            elif low_freq_class and freq > 200:
                # Very high frequency can't be a rare class
                is_eliminated = True
                reasons_to_eliminate.append(
                    f"frequency {freq} incompatible with low-frequency class {cc}"
                )
            elif freq_contradiction and kober_rescue:
                # Frequency says no but Kober says yes — keep as plausible
                # with a note
                is_eliminated = False
                reasons_to_keep.append(
                    f"Kober rescue: frequency contradiction overridden by series/triple link"
                )
            else:
                is_eliminated = False

            entry = {
                "bennett_id": bennett_id,
                "frequency": freq,
                "consonant_class": cc,
                "vowel": v,
                "plausible": not is_eliminated,
                "series": series_label or "",
                "reasons": "; ".join(reasons_to_keep if not is_eliminated
                                     else reasons_to_eliminate),
                "elimination_reasons": "; ".join(reasons_to_eliminate),
                "supporting_reasons": "; ".join(reasons_to_keep),
            }

            if is_eliminated:
                eliminated += 1
                results["eliminated"].append(entry)
            else:
                results["candidates"].append(entry)

    return results


def _vowel_name(v: str) -> str:
    names = {"a": "A-row", "e": "E-row", "i": "I-row", "o": "O-row", "u": "U-row"}
    return names.get(v, v)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    all_results: dict[str, dict],
    profile: dict,
    uncertain_signs: list[dict],
    freqs: dict[str, int],
) -> str:
    """Generate a Markdown report."""

    total_candidates = sum(
        len(r["candidates"]) + len(r["eliminated"])
        for r in all_results.values()
    )
    total_plausible = sum(len(r["candidates"]) for r in all_results.values())
    total_eliminated = sum(len(r["eliminated"]) for r in all_results.values())
    pct_eliminated = (total_eliminated / total_candidates * 100) if total_candidates else 0

    lines = [
        "# Frequency-Typology Grid Constraint Report",
        "",
        "## Summary",
        "",
        f"- **Target signs**: {len(all_results)} UNCERTAIN syllabograms",
        f"- **Total candidate CV slots evaluated**: {total_candidates}",
        f"- **Eliminated**: {total_eliminated} ({pct_eliminated:.1f}%)",
        f"- **Remaining plausible candidates**: {total_plausible}",
        "",
        "## Methodology",
        "",
        "1. **Frequency envelopes**: For each CONFIRMED consonant class and vowel row,",
        "   we compute mean ± 2σ frequency ranges. Any candidate whose observed",
        "   frequency falls outside this envelope is flagged.",
        "2. **Kober grid series**: Signs in the same Kober series share either",
        "   consonant or vowel. If an UNCERTAIN sign's series partners all share",
        "   a consonant class (or vowel), and the candidate matches neither,",
        "   it is eliminated.",
        "3. **Kober triples**: Three-sign patterns with shared preceding/following",
        "   context provide additional constraints from CONFIRMED partners.",
        "4. **Typological priors**: Very high-frequency signs (>200 occurrences)",
        "   cannot belong to typologically rare consonant classes (sibilants,",
        "   semivowels).",
        "",
        "## Elimination by Sign",
        "",
    ]

    # Sort signs by frequency (descending)
    sorted_signs = sorted(
        all_results.items(),
        key=lambda x: freqs.get(x[0], 0),
        reverse=True,
    )

    for bennett_id, results in sorted_signs:
        freq = freqs.get(bennett_id, 0)
        n_candidates = len(results["candidates"])
        n_eliminated = len(results["eliminated"])
        n_total = n_candidates + n_eliminated
        pct = (n_eliminated / n_total * 100) if n_total else 0

        # Get conventional/refined value
        grid_info = next((s for s in uncertain_signs if s["bennett_id"] == bennett_id), {})
        rv = grid_info.get("refined_value", "?")

        lines.append(f"### {bennett_id} (conventional: {rv}, freq: {freq})")
        lines.append(f"- Candidates eliminated: {n_eliminated}/{n_total} ({pct:.0f}%)")
        lines.append(f"- Plausible candidates: {n_candidates}")

        if results["candidates"]:
            lines.append("- **Best candidates**:")
            # Sort by supporting reasons (more reasons = stronger)
            sorted_candidates = sorted(
                results["candidates"],
                key=lambda x: len(x["supporting_reasons"]),
                reverse=True,
            )
            for c in sorted_candidates[:8]:
                sr = c["supporting_reasons"] or "(frequency alone)"
                lines.append(f"  - {c['consonant_class']}/{c['vowel']}: {sr}")

        if results["eliminated"]:
            lines.append("- **Notable eliminations**:")
            for e in results["eliminated"][:5]:
                lines.append(f"  - ✗ {e['consonant_class']}/{e['vowel']}: {e['elimination_reasons']}")

        lines.append("")

    # Per-class elimination stats
    lines.append("## Elimination by Consonant Class")
    lines.append("")
    elim_by_cc: dict[str, int] = defaultdict(int)
    cand_by_cc: dict[str, int] = defaultdict(int)
    for results in all_results.values():
        for e in results["eliminated"]:
            elim_by_cc[e["consonant_class"]] += 1
        for c in results["candidates"]:
            cand_by_cc[c["consonant_class"]] += 1

    for cc in sorted(CONSONANT_CLASSES.keys()):
        e_count = elim_by_cc.get(cc, 0)
        c_count = cand_by_cc.get(cc, 0)
        total = e_count + c_count
        pct = (e_count / total * 100) if total else 0
        lines.append(f"- **{cc}**: {e_count}/{total} eliminated ({pct:.0f}%)")

    lines.append("")
    lines.append("## Key Findings")
    lines.append("")

    # High-frequency signs
    high_freq = [(b, r) for b, r in all_results.items() if freqs.get(b, 0) > 100]
    lines.append("### High-Frequency UNCERTAIN Signs (>100 occurrences)")
    lines.append("")
    for b_id, results in sorted(high_freq, key=lambda x: freqs.get(x[0], 0), reverse=True):
        freq = freqs.get(b_id, 0)
        n_c = len(results["candidates"])
        lines.append(
            f"- **{b_id}** (freq={freq}): {n_c} candidates remain. "
            f"Must be a common phoneme class."
        )

    lines.append("")
    lines.append("### Zero-Frequency Signs")
    lines.append("")
    zero_freq = [(b, r) for b, r in all_results.items() if freqs.get(b, 0) == 0]
    for b_id, results in sorted(zero_freq):
        lines.append(
            f"- **{b_id}**: 0 occurrences. No frequency constraint possible "
            f"(all classes remain plausible)."
        )

    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append("- Frequency envelopes are based on 58 CONFIRMED signs — a small sample.")
    lines.append("- CV slot statistics are sparse; many slots have <2 CONFIRMED signs.")
    lines.append("- The Kober grid series classification into boundary-flexible,")
    lines.append("  medial-dominant, and neutral is based on positional analysis,")
    lines.append("  not phonetic certainty.")
    lines.append("- Frequency alone is a WEAK constraint compared to phonetic or")
    lines.append("  comparative evidence. Eliminations here should be treated as")
    lines.append("  suggestive, not definitive.")
    lines.append("- AB 62 (freq=285), AB 66 (freq=308), AB 85 (freq=274) are extreme")
    lines.append("  outliers even compared to common CONFIRMED signs. They may be")
    lines.append("  grammatical morphemes rather than content phonemes, which would")
    lines.append("  invalidate the frequency-class approach.")
    lines.append("- The task brief mentions AB 62 appearing 437 times, matching")
    lines.append("  triple_patterns.csv total_occ. Our DB count using")
    lines.append("  sign_type='syllabogram' gives 285. The triple_patterns column")
    lines.append("  counts at a coarser level. We use the DB count as authoritative.")
    lines.append("- The medial-dominant Kober series spans all consonant classes and")
    lines.append("  all vowels among its CONFIRMED members, providing zero class-level")
    lines.append("  constraint for its UNCERTAIN members (AB 49, AB 52, AB 56, etc).")
    lines.append("- For signs with zero corpus occurrences, no frequency constraint is")
    lines.append("  possible. Other evidence sources must carry the full burden.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Loading data...")
    freqs = load_freqs()
    grid = load_grid()
    profile = load_profile()
    series = load_series()
    triples = load_triples()

    # Target: all UNCERTAIN signs plus CONFIRMED-with-unknown-value
    uncertain_signs = [
        r for r in grid
        if r["decision"] == "UNCERTAIN"
        or (r["decision"] == "CONFIRM" and r["refined_value"] in ("?", "", None))
    ]
    log.info("Target signs: %d", len(uncertain_signs))

    all_results: dict[str, dict] = {}
    for s in uncertain_signs:
        b_id = s["bennett_id"]
        freq = freqs.get(b_id, 0)
        if freq == 0:
            log.info("%s: freq=0, skipping (no constraint possible)", b_id)
            # Still include for completeness but with all candidates plausible
            all_results[b_id] = {"candidates": [], "eliminated": []}
            for cc in CONSONANT_CLASSES:
                for v in VOWELS:
                    all_results[b_id]["candidates"].append({
                        "bennett_id": b_id,
                        "frequency": 0,
                        "consonant_class": cc,
                        "vowel": v,
                        "plausible": True,
                        "series": get_series_membership(b_id, series) or "",
                        "reasons": "zero frequency — no constraint",
                        "elimination_reasons": "",
                        "supporting_reasons": "",
                    })
            continue

        results = constrain_sign(b_id, freq, profile, series, triples, grid)
        all_results[b_id] = results
        n_c = len(results["candidates"])
        n_e = len(results["eliminated"])
        log.info("%s: freq=%d, %d candidates, %d eliminated", b_id, freq, n_c, n_e)

    # --- Write candidates CSV ---
    log.info("Writing %s...", CANDIDATES_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "bennett_id", "frequency", "consonant_class", "vowel",
        "plausible", "series", "reasons",
    ]
    with open(CANDIDATES_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for results in all_results.values():
            for c in results["candidates"]:
                writer.writerow(c)
            # Also write eliminated for transparency
            for e in results["eliminated"]:
                writer.writerow(e)

    # --- Write report ---
    log.info("Writing %s...", REPORT_PATH)
    report = generate_report(all_results, profile, uncertain_signs, freqs)
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    # --- Summary stats ---
    total_candidates = sum(
        len(r["candidates"]) + len(r["eliminated"]) for r in all_results.values()
    )
    total_plausible = sum(len(r["candidates"]) for r in all_results.values())
    total_eliminated = sum(len(r["eliminated"]) for r in all_results.values())
    pct = (total_eliminated / total_candidates * 100) if total_candidates else 0

    log.info("=== SUMMARY ===")
    log.info("Total candidates evaluated: %d", total_candidates)
    log.info("Eliminated: %d (%.1f%%)", total_eliminated, pct)
    log.info("Remaining: %d", total_plausible)
    log.info("Done.")


if __name__ == "__main__":
    main()
