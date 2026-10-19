#!/usr/bin/env python3
"""
Egyptian Bridge Search: Match Egyptian trade vocabulary consonant-class
skeletons against Linear A sign consonant-class sequences in the corpus.

Approach:
  1. Map each Egyptian consonant → consonant class (P/T/K/S/N/R/W/V)
  2. Map each LA syllabogram → its consonant class based on phonetic value
  3. Search for consonant-class sequences as substrings
  4. When a consonant-class match is found, verify the specific sign values
     are compatible (within the same consonant class)
  5. Filter for >=3-sign matches
  6. Flag commodity-adjacent contexts

Key insight: Egyptian vowels are unwritten. By matching consonant classes
rather than specific CV signs, we avoid false negatives from vowel mismatch
while keeping specificity at the consonant-feature level.

Outputs:
  - data/analysis/egyptian_bridge/match_results.csv
  - data/analysis/egyptian_bridge/egyptian_report.md
"""

from __future__ import annotations

import csv
import sqlite3
import re
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
DB_PATH = PROJECT_ROOT / "data/database/lineara_full.db"
OUTPUT_DIR = PROJECT_ROOT / "data/analysis/egyptian_bridge"
VOCAB_CSV = OUTPUT_DIR / "egyptian_vocabulary.csv"
MATCH_CSV = OUTPUT_DIR / "match_results.csv"
REPORT_MD = OUTPUT_DIR / "egyptian_report.md"

EXPANDED_GRID = PROJECT_ROOT / "data/analysis/bootstrapping/expanded_grid.csv"

# ---------------------------------------------------------------------------
# Consonant class mapping
# ---------------------------------------------------------------------------

# Egyptian consonant → consonant class
EGYPTIAN_CLASS: Dict[str, str] = {
    "p": "P", "b": "P", "f": "P",
    "t": "T", "d": "T", "T": "T", "D": "T",
    "k": "K", "g": "K", "X": "K", "Q": "K",
    "s": "S", "z": "S", "S": "S",
    "m": "N", "n": "N",
    "r": "R", "l": "R",
    "w": "W",
    "j": "W",    # yod → glide class
    "H": "G",    # pharyngeal → glottal class (G)
    "h": "G",
}

# LA CV sign → consonant class based on the onset consonant
# Vowel-only signs → V (vowel class)
# Unknown consonants → ? (any)
def la_sign_to_class(sign: str) -> str:
    """Map a Linear A transliteration (lowercase, e.g., 'pa', 'da', 'a') to consonant class.

    Classes: P=labial, T=dental, K=velar, S=sibilant, R=liquid, N=nasal, W=glide, V=vowel.
    Nasals (m, n) are separated from stops to match Egyptian N-class."""
    if not sign:
        return "?"
    s = sign.lower().strip()
    # Vowel-only signs
    if s in ("a", "e", "i", "o", "u"):
        return "V"
    # Glides (W-series, J-series)
    if s[0] == "w":
        return "W"
    if s[0] == "j":
        return "W"
    # Nasals (m, n) — separate class
    if s[0] == "m":
        return "N"
    if s[0] == "n":
        return "N"
    # Labial stops (p, b, q)
    if s[0] in ("p", "b", "q"):
        return "P"
    # Dental stops (t, d, th)
    if s[0] in ("t", "d"):
        return "T"
    # Velar stops (k, g)
    if s[0] in ("k", "g"):
        return "K"
    # Sibilants (s, z)
    if s[0] in ("s", "z"):
        return "S"
    # Liquids (r, l)
    if s[0] in ("r", "l"):
        return "R"
    # Unknown
    return "?"


def egyptian_skeleton_to_class(skeleton: str) -> str:
    """Convert Egyptian consonant skeleton to consonant class string."""
    result = []
    for ch in skeleton:
        cls = EGYPTIAN_CLASS.get(ch, "?")
        if cls != "?":
            result.append(cls)
    return "".join(result)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_vocabulary() -> List[dict]:
    rows = []
    with open(VOCAB_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["sign_count"] = int(row["sign_count"])
            rows.append(row)
    return rows


def load_expanded_grid() -> Dict[str, str]:
    mapping = {}
    with open(EXPANDED_GRID, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row["bennett_id"].strip()
            refined = row["refined_value"].strip().lower()
            if refined and refined != "?":
                mapping[bid] = refined
    return mapping


# ---------------------------------------------------------------------------
# Corpus building
# ---------------------------------------------------------------------------

COMMODITY_LOGOGRAMS = {
    "GRA", "OLE", "VIN", "OLIV", "AROM", "CAP", "CYP",
    "TELA", "GAL", "VS", "VIR", "L", "AU",
}

def norm_translit(tl: str) -> str:
    if not tl:
        return ""
    tl = tl.strip().lower()
    tl = re.sub(r'[₀₁₂₃₄₅₆₇₈₉₂₃]', '', tl)
    return tl


def is_valid_syll(tl: str) -> bool:
    """Check if a transliteration is a core LA syllabogram value."""
    if not tl:
        return False
    clean = re.sub(r'[₂₃₁₀]', '', tl.strip())
    if not re.match(r'^[A-Z]{1,3}$', clean):
        return False
    if clean in COMMODITY_LOGOGRAMS:
        return False
    if clean == "L":
        return False
    return True


def is_commodity_logogram(tl: str) -> bool:
    if not tl:
        return False
    tl_upper = tl.strip().upper()
    if tl_upper in COMMODITY_LOGOGRAMS:
        return True
    if "+" in tl_upper:
        parts = tl_upper.split("+")
        return any(p in COMMODITY_LOGOGRAMS for p in parts)
    return False


def build_corpus(expanded_map: Dict[str, str]) -> List[dict]:
    """Build corpus with both conventional and expanded sequences.
    Each sequence is a list of (sign_str, consonant_class) tuples."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get inscriptions
    c.execute("SELECT id, gorila_id FROM inscriptions")
    ins_info = {r["id"]: r["gorila_id"] for r in c.fetchall()}

    # Get all syllabogram signs
    c.execute("""
        SELECT s.inscription_id, s.sequence, s.bennett_id, s.transliteration,
               s.sign_type, i.gorila_id, f.site, i.material, i.minoan_period,
               i.object_type
        FROM signs s
        JOIN inscriptions i ON i.id = s.inscription_id
        LEFT JOIN findspots f ON f.id = i.findspot_id
        WHERE s.sign_type = 'syllabogram'
          AND s.transliteration IS NOT NULL
          AND s.transliteration != ''
          AND s.transliteration != '?'
        ORDER BY s.inscription_id, s.sequence
    """)

    # Group by inscription
    ins_data = defaultdict(list)
    for row in c.fetchall():
        ins_id = row["inscription_id"]
        ins_data[ins_id].append({
            "sequence": row["sequence"],
            "bennett_id": row["bennett_id"] or "",
            "transliteration": row["transliteration"],
            "norm": norm_translit(row["transliteration"]),
            "gorila_id": row["gorila_id"],
            "site": row["site"] or "",
            "material": row["material"] or "",
            "period": row["minoan_period"] or "",
            "object_type": row["object_type"] or "",
        })

    conn.close()

    corpus = []
    for ins_id, signs in ins_data.items():
        if not signs:
            continue

        info = signs[0]

        # Build conventional sequence
        conv_signs = []
        conv_classes = []
        expanded_signs = []
        expanded_classes = []

        for s in signs:
            tl = s["transliteration"]
            bid = s["bennett_id"]
            if is_valid_syll(tl):
                norm = norm_translit(tl)
                cls = la_sign_to_class(norm)
                conv_signs.append(norm)
                conv_classes.append(cls)

                # Expanded form
                if bid in expanded_map and expanded_map[bid] != "?":
                    exp_norm = expanded_map[bid].lower()
                    exp_cls = la_sign_to_class(exp_norm)
                    expanded_signs.append(exp_norm)
                    expanded_classes.append(exp_cls)
                else:
                    expanded_signs.append(norm)
                    expanded_classes.append(cls)

        if not conv_signs:
            continue

        # Track sequence numbers alongside valid syllabograms for commodity context lookup
        conv_sequences = []
        for s in signs:
            tl = s["transliteration"]
            if is_valid_syll(tl):
                conv_sequences.append(s["sequence"])

        corpus.append({
            "inscription_id": ins_id,
            "gorila_id": info["gorila_id"],
            "site": info["site"],
            "material": info["material"],
            "period": info["period"],
            "object_type": info["object_type"],
            "raw_signs": signs,
            "conventional_signs": conv_signs,
            "conventional_classes": conv_classes,
            "conventional_class_str": "".join(conv_classes),
            "conventional_sequences": conv_sequences,
            "expanded_signs": expanded_signs,
            "expanded_classes": expanded_classes,
            "expanded_class_str": "".join(expanded_classes),
        })

    return corpus


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def find_class_matches(eg_class_str: str, corpus_class_str: str) -> List[int]:
    """Find all start positions where eg_class_str appears as substring."""
    if not eg_class_str:
        return []
    pos = 0
    matches = []
    while True:
        idx = corpus_class_str.find(eg_class_str, pos)
        if idx == -1:
            break
        matches.append(idx)
        pos = idx + 1
    return matches


def find_commodity_context(raw_signs: List[dict],
                           match_start_seq: int, match_end_seq: int,
                           window: int = 3) -> List[str]:
    """Find commodity logograms near the matched sign positions.
    match_start_seq/end_seq are actual sequence numbers from the DB."""
    commodities = set()
    for s in raw_signs:
        seq = s["sequence"]
        if match_start_seq - window <= seq <= match_end_seq + window:
            tl = s["transliteration"]
            if is_commodity_logogram(tl):
                parts = tl.upper().split("+")
                for p in parts:
                    if p in COMMODITY_LOGOGRAMS:
                        commodities.add(p)
    return sorted(commodities)


def search(vocabulary: List[dict], corpus: List[dict],
           min_signs: int = 3) -> List[dict]:
    """Main search using consonant-class subsequences."""

    # Build Egyptian class strings
    eg_entries = []
    for v in vocabulary:
        if v["sign_count"] < min_signs:
            continue
        class_str = egyptian_skeleton_to_class(v["consonant_skeleton"])
        if len(class_str) >= min_signs:
            eg_entries.append({
                **v,
                "class_str": class_str,
            })

    print(f"Searching {len(eg_entries)} Egyptian words (>= {min_signs} signs)")
    print(f"Across {len(corpus)} inscriptions")

    results = []

    for eg in eg_entries:
        eg_class = eg["class_str"]

        for ins in corpus:
            # Search conventional
            conv_matches = find_class_matches(eg_class,
                                              ins["conventional_class_str"])
            for start_pos in conv_matches:
                end_pos = start_pos + len(eg_class) - 1

                # Verify: get the actual sign values at these positions
                matched_signs_conv = ins["conventional_signs"][start_pos:end_pos+1]
                matched_classes_conv = ins["conventional_classes"][start_pos:end_pos+1]

                # Map to actual DB sequence numbers via conventional_sequences list
                seq_list = ins.get("conventional_sequences", [])
                raw_start_seq = seq_list[start_pos] if start_pos < len(seq_list) else 0
                raw_end_seq = seq_list[end_pos] if end_pos < len(seq_list) else 0

                commodities = find_commodity_context(
                    ins["raw_signs"], raw_start_seq, raw_end_seq)

                results.append({
                    "egyptian_id": eg["id"],
                    "egyptian_english": eg["english"],
                    "egyptian_category": eg["category"],
                    "egyptian_subcategory": eg["subcategory"],
                    "egyptian_skeleton": eg["consonant_skeleton"],
                    "egyptian_class_str": eg_class,
                    "gorila_id": ins["gorila_id"],
                    "site": ins["site"],
                    "material": ins["material"],
                    "period": ins["period"],
                    "object_type": ins["object_type"],
                    "match_sign_start": start_pos,
                    "match_sign_end": end_pos,
                    "match_length": len(eg_class),
                    "matched_signs": "+".join(matched_signs_conv),
                    "matched_classes": "".join(matched_classes_conv),
                    "source": "conventional",
                    "commodities_nearby": ",".join(commodities),
                    "commodity_context": len(commodities) > 0,
                })

            # Search expanded
            if ins.get("expanded_class_str"):
                exp_matches = find_class_matches(eg_class,
                                                 ins["expanded_class_str"])
                for start_pos in exp_matches:
                    end_pos = start_pos + len(eg_class) - 1

                    matched_signs_exp = ins["expanded_signs"][start_pos:end_pos+1]
                    matched_classes_exp = ins["expanded_classes"][start_pos:end_pos+1]

                    seq_list = ins.get("conventional_sequences", [])
                    raw_start_seq = seq_list[start_pos] if start_pos < len(seq_list) else 0
                    raw_end_seq = seq_list[end_pos] if end_pos < len(seq_list) else 0

                    commodities = find_commodity_context(
                        ins["raw_signs"], raw_start_seq, raw_end_seq)

                    results.append({
                        "egyptian_id": eg["id"],
                        "egyptian_english": eg["english"],
                        "egyptian_category": eg["category"],
                        "egyptian_subcategory": eg["subcategory"],
                        "egyptian_skeleton": eg["consonant_skeleton"],
                        "egyptian_class_str": eg_class,
                        "gorila_id": ins["gorila_id"],
                        "site": ins["site"],
                        "material": ins["material"],
                        "period": ins["period"],
                        "object_type": ins["object_type"],
                        "match_sign_start": start_pos,
                        "match_sign_end": end_pos,
                        "match_length": len(eg_class),
                        "matched_signs": "+".join(matched_signs_exp),
                        "matched_classes": "".join(matched_classes_exp),
                        "source": "expanded",
                        "commodities_nearby": ",".join(commodities),
                        "commodity_context": len(commodities) > 0,
                    })

    return results


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_match(match: dict) -> float:
    score = 0.0
    sign_count = match["match_length"]
    score += min(sign_count * 15, 60)
    if match["commodity_context"]:
        score += 20
    if match["source"] == "expanded":
        score += 5
    cat = match["egyptian_category"]
    if cat in ("commodities", "trade"):
        score += 10
    elif cat in ("agriculture", "metals", "materials", "beverages"):
        score += 5
    return min(score, 100)


# ---------------------------------------------------------------------------
# Null model: expected random matches
# ---------------------------------------------------------------------------

def estimate_null_rate(corpus_class_str: str, eg_class_str: str,
                       n_permutations: int = 1000) -> float:
    """Estimate expected matches under random shuffling of corpus classes.
    Returns mean matches per permutation."""
    import random
    random.seed(42)
    chars = list(corpus_class_str)
    counts = []
    for _ in range(n_permutations):
        random.shuffle(chars)
        shuffled = "".join(chars)
        matches = find_class_matches(eg_class_str, shuffled)
        counts.append(len(matches))
    return sum(counts) / len(counts)


def estimate_null_rate_single(corpus_class_str: str, eg_class_str: str,
                               n_permutations: int = 200) -> float:
    """Estimate expected matches for a single inscription string.
    Returns mean matches per permutation for this one string."""
    import random
    random.seed(42)
    if len(corpus_class_str) < len(eg_class_str):
        return 0.0
    chars = list(corpus_class_str)
    counts = []
    for _ in range(n_permutations):
        random.shuffle(chars)
        shuffled = "".join(chars)
        matches = find_class_matches(eg_class_str, shuffled)
        counts.append(len(matches))
    return sum(counts) / len(counts)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def generate_report(results: List[dict], vocabulary: List[dict],
                    corpus: List[dict]) -> str:
    lines = []
    lines.append("# Egyptian Trade Vocabulary — Linear A Bridge Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    unique_eg = set(r["egyptian_id"] for r in results)
    unique_ins = set(r["gorila_id"] for r in results)
    commodity_matches = [r for r in results if r["commodity_context"]]

    # Category counts
    cat_counts = Counter(r["egyptian_category"] for r in results)

    # Corpus stats
    total_signs = sum(len(ins["conventional_signs"]) for ins in corpus)
    total_classes = sum(len(ins["conventional_classes"]) for ins in corpus)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Egyptian words searched**: {len(vocabulary)}")
    lines.append(f"- **Words with ≥3-sign skeletons**: {sum(1 for v in vocabulary if v['sign_count'] >= 3)}")
    lines.append(f"- **Corpus size**: {len(corpus)} inscriptions, {total_signs} syllabogram tokens")
    lines.append(f"- **Total consonant-class matches**: {len(results)}")
    lines.append(f"- **Unique Egyptian words matched**: {len(unique_eg)}")
    lines.append(f"- **Unique inscriptions matched**: {len(unique_ins)}")
    lines.append(f"- **Matches with commodity context**: {len(commodity_matches)}")
    lines.append(f"- **Method**: consonant-class subsequence matching (vowel-independent)")
    lines.append("")

    lines.append("## Key Question")
    lines.append("")
    lines.append("> Do 3–5 Egyptian trade words appear as LA sign sequences in commodity-appropriate contexts?")
    lines.append("")

    if commodity_matches:
        eg_with_ctx = set(r["egyptian_id"] for r in commodity_matches)
        lines.append(f"**Yes — {len(eg_with_ctx)} Egyptian trade words have consonant-class matches "
                     f"with nearby commodity logograms.**")
        lines.append(f"These are: {', '.join(sorted(eg_with_ctx))}")
    else:
        lines.append("**No — no Egyptian trade words had consonant-class matches adjacent "
                     "to commodity logograms at ≥3 signs.**")
    lines.append("")

    if unique_eg:
        lines.append(f"**{len(unique_eg)} Egyptian words produce consonant-class substring matches.**")
    lines.append("")

    # Category breakdown
    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Matches |")
    lines.append("|----------|---------|")
    for cat, cnt in cat_counts.most_common():
        lines.append(f"| {cat} | {cnt} |")
    lines.append("")

    # Top matches
    lines.append("## Top Matches (ranked by score)")
    lines.append("")
    lines.append("| Score | Egyptian Word | English | Category | Class Skel. | Inscription | Site | Signs | Sign Match | Commodity Context | Source |")
    lines.append("|-------|---------------|---------|----------|-------------|-------------|------|-------|------------|-------------------|--------|")

    for r in results:
        r["score"] = score_match(r)

    scored = sorted(results, key=lambda x: -x["score"])

    shown = set()
    for r in scored[:40]:
        key = (r["egyptian_id"], r["gorila_id"], r["match_sign_start"])
        if key in shown:
            continue
        shown.add(key)
        ctx = "YES" if r["commodity_context"] else "—"
        lines.append(
            f"| {r['score']:.0f} | {r['egyptian_id']} | {r['egyptian_english']} | "
            f"{r['egyptian_category']} | {r['egyptian_class_str']} | "
            f"{r['gorila_id']} | {r['site']} | "
            f"{r['match_length']} | {r['matched_signs']} | "
            f"{ctx} | {r['source']} |"
        )
    lines.append("")

    # Top Egyptian words
    by_word = defaultdict(list)
    for r in results:
        by_word[r["egyptian_id"]].append(r)

    lines.append("## Egyptian Words with Most Matches")
    lines.append("")
    lines.append("| Egyptian Word | English | Category | Skeleton | Class | Signs | Matches | Commodity Context |")
    lines.append("|---------------|---------|----------|----------|-------|-------|---------|-------------------|")

    word_stats = []
    for eg_id, matches in by_word.items():
        ctx_count = sum(1 for m in matches if m["commodity_context"])
        eg_entry = next((v for v in vocabulary if v["id"] == eg_id), None)
        class_str = egyptian_skeleton_to_class(eg_entry["consonant_skeleton"]) if eg_entry else ""
        word_stats.append({
            "id": eg_id,
            "english": eg_entry["english"] if eg_entry else eg_id,
            "category": eg_entry["category"] if eg_entry else "",
            "skeleton": eg_entry["consonant_skeleton"] if eg_entry else "",
            "class": class_str,
            "sign_count": eg_entry["sign_count"] if eg_entry else 0,
            "matches": len(matches),
            "ctx_matches": ctx_count,
        })

    word_stats.sort(key=lambda x: (-x["matches"], -x["sign_count"]))
    for ws in word_stats[:25]:
        lines.append(
            f"| {ws['id']} | {ws['english']} | {ws['category']} | "
            f"{ws['skeleton']} | {ws['class']} | {ws['sign_count']} | "
            f"{ws['matches']} | {ws['ctx_matches']} |"
        )
    lines.append("")

    # Null model estimation
    lines.append("## Statistical Assessment")
    lines.append("")
    lines.append("**Important:** Consonant-class matching at 3+ signs in a corpus of "
                 f"{total_classes} consonant-class tokens will produce "
                 "coincidental matches. Without a null model, we cannot distinguish "
                 "signal from noise.")
    lines.append("")

    # Estimate for a few key words
    lines.append("### Null-model estimates for key words")
    lines.append("")
    lines.append("| Egyptian Word | Class | Observed Matches | Expected (shuffled) | Ratio |")
    lines.append("|---------------|-------|-----------------|---------------------|-------|")

    # Sample a few words
    import random
    random.seed(42)
    # Concatenate corpus class strings with a separator to prevent cross-inscription matches
    sep = "|"
    all_class_strs = sep.join(ins["conventional_class_str"] for ins in corpus)
    
    sample_egs = word_stats[:8]
    for ws in sample_egs:
        eg_class = ws["class"]
        if len(eg_class) < 3:
            continue
        obs = ws["matches"]
        # Null model: shuffle chars WITHIN each inscription separately
        # to preserve per-text length distributions
        total_exp = 0.0
        for ins in corpus:
            cs = ins["conventional_class_str"]
            ins_exp = estimate_null_rate_single(cs, eg_class, n_permutations=200)
            total_exp += ins_exp
        ratio = obs / total_exp if total_exp > 0 else float("inf")
        lines.append(
            f"| {ws['id']} | {eg_class} | {obs} | {total_exp:.1f} | {ratio:.1f}x |"
        )
    lines.append("")

    # Caveats
    lines.append("## Critical Caveats")
    lines.append("")
    lines.append("1. **Consonant-class matching is broad.** We match at the level of")
    lines.append("   consonant features (labial, dental, velar, etc.), not specific phonemes.")
    lines.append("   This increases sensitivity but also false positives. A match between")
    lines.append("   Egyptian /nfr/ (N-P-R) and LA /na-pa-ra/ (N-P-R) could be coincidental.")
    lines.append("")
    lines.append("2. **No vowel information.** Egyptian writing omits vowels entirely, and")
    lines.append("   LA sign values are uncertain for most vowels. Our class-based matching")
    lines.append("   intentionally ignores vowels, which is appropriate for the evidence but")
    lines.append("   further reduces specificity.")
    lines.append("")
    lines.append("3. **Five consonant classes cover most LA signs.** P, T, K, S, N, R, W, V")
    lines.append("   means that random 3-class sequences are common. A 3-sign match has a")
    lines.append("   baseline probability of ~1/7³ = 1/343 for any given position under")
    lines.append("   uniform distribution (actual distribution is non-uniform).")
    lines.append("")
    lines.append("4. **No directionality claim.** Even genuine matches cannot distinguish")
    lines.append("   Egyptian→Minoan vs Minoan→Egyptian vs shared substrate borrowing.")
    lines.append("")
    lines.append("5. **This is a text search, not linguistic proof.** No phonological regularity,")
    lines.append("   semantic verification, or historical context has been applied.")
    lines.append("")

    # Honest assessment
    lines.append("## Honest Assessment")
    lines.append("")

    if commodity_matches:
        lines.append("Some Egyptian trade words have consonant-class matches near commodity")
        lines.append("logograms in the Linear A corpus. However:")
        lines.append("")
        lines.append("- Consonant-class matching at ≥3 signs is highly susceptible to coincidence")
        lines.append("- The null-model ratios (if near 1.0x) would indicate chance-level matching")
        lines.append("- Even if matches are above chance, this could reflect shared Afroasiatic")
        lines.append("  substrate rather than direct Egyptian→Minoan borrowing")
    else:
        lines.append("**No Egyptian trade words produced consonant-class matches adjacent to")
        lines.append("**commodity logograms at ≥3 signs.**")
        lines.append("")
        lines.append("This negative result has several possible explanations:")
        lines.append("")
        lines.append("1. **Egyptian loans don't exist in LA.** Minoan traders may have used")
        lines.append("   Egyptian terminology only orally, not in administrative texts.")
        lines.append("2. **Phonological adaptation was more extensive.** Egyptian words borrowed")
        lines.append("   into Minoan may have undergone consonant changes that break our class mapping.")
        lines.append("3. **Corpus bias.** Surviving LA texts are administrative (tablets, sealings),")
        lines.append("   not commercial. Trade vocabulary may not appear in this genre.")
        lines.append("4. **The 3-sign threshold is too high.** Many Egyptian trade terms have")
        lines.append("   2-consonant skeletons (e.g., jrp 'wine' → r-p, nbw 'gold' → n-b).")
        lines.append("   Lowering to 2 signs would produce many more matches but at the cost of")
        lines.append("   specificity (2-class matches are overwhelmingly noise).")

    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(f"- **Vocabulary**: {len(vocabulary)} Egyptian trade/commerce terms from Middle/Late Egyptian")
    lines.append(f"- **Corpus**: {len(corpus)} Linear A inscriptions, {total_signs} syllabogram tokens")
    lines.append("- **Mapping**: Egyptian consonant → consonant class (P/T/K/S/N/R/W/G)")
    lines.append("  LA syllabogram value → consonant class (based on phonetic onset)")
    lines.append("- **Search**: contiguous subsequence matching of consonant-class strings")
    lines.append("- **Filter**: ≥3 contiguous signs (consonant classes)")
    lines.append("- **Context**: commodity logogram (GRA, OLE, VIN, etc.) ±3 sign positions")
    lines.append("- **Dual-source**: conventional AB values AND Phase 8 expanded values searched")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Egyptian vocabulary...")
    vocabulary = load_vocabulary()
    print(f"  {len(vocabulary)} Egyptian terms loaded")

    print("Loading expanded grid...")
    expanded_map = load_expanded_grid()
    print(f"  {len(expanded_map)} expanded grid entries")

    print("Building Linear A corpus...")
    corpus = build_corpus(expanded_map)
    total_signs = sum(len(ins["conventional_signs"]) for ins in corpus)
    print(f"  {len(corpus)} inscriptions")
    print(f"  {total_signs} valid syllabogram tokens")

    # Show top class distribution
    all_classes = []
    for ins in corpus:
        all_classes.extend(ins["conventional_classes"])
    class_dist = Counter(all_classes)
    print(f"  Class distribution: {dict(class_dist.most_common())}")

    print("Searching...")
    results = search(vocabulary, corpus, min_signs=3)

    for r in results:
        r["score"] = score_match(r)

    results.sort(key=lambda r: r["score"], reverse=True)

    print(f"  {len(results)} matches found")
    commodity_matches = [r for r in results if r["commodity_context"]]
    print(f"  {len(commodity_matches)} with commodity context")

    # Write CSV
    fieldnames = [
        "egyptian_id", "egyptian_english", "egyptian_category",
        "egyptian_subcategory", "egyptian_skeleton", "egyptian_class_str",
        "gorila_id", "site", "material", "period", "object_type",
        "match_sign_start", "match_sign_end", "match_length",
        "matched_signs", "matched_classes",
        "source", "commodities_nearby", "commodity_context", "score",
    ]

    with open(MATCH_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    print(f"Results written to {MATCH_CSV}")

    # Generate report
    report = generate_report(results, vocabulary, corpus)

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written to {REPORT_MD}")

    unique_eg = set(r["egyptian_id"] for r in results)
    print(f"\n=== SUMMARY ===")
    print(f"Total matches: {len(results)}")
    print(f"Unique Egyptian words matched: {len(unique_eg)}")
    print(f"Matches with commodity context: {len(commodity_matches)}")
    print(f"Top 10 matches by score:")
    for r in results[:10]:
        ctx = f" [COMMODITY: {r['commodities_nearby']}]" if r["commodity_context"] else ""
        print(f"  {r['score']:.0f}: {r['egyptian_id']} ({r['egyptian_english']}) "
              f"→ {r['gorila_id']} ({r['site']}) class:{r['egyptian_class_str']} "
              f"→ LA:{r['matched_signs']} [{r['source']}]{ctx}")

    return results


if __name__ == "__main__":
    main()
