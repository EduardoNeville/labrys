"""
Eteocretan ↔ Linear A Comparison Module
========================================
Systematic comparison of Eteocretan words against Linear A evidence.

Comparison axes:
    1. Direct word matching — Eteocretan words vs. known LA words, loanwords, toponyms
    2. Phonotactic profile — CV structure, consonant/vowel ratios
    3. Sign-to-phoneme mapping — Reverse-map Eteocretan phonemes to LA signs
    4. Recurring morpheme analysis — Identify repeated segments across texts
    5. Bilingual evidence — Greek-Eteocretan parallel text analysis
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter

from pipeline.eteocretan.corpus import (
    ALL_INSCRIPTIONS, ALL_WORDS, get_vocabulary, get_unique_et_words,
    EteocretanWord, EteocretanInscription,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known Linear A words with high-confidence meanings
# ---------------------------------------------------------------------------
KNOWN_LA_WORDS: dict[str, str] = {
    # From Phase 1-3 analysis; these are the ~15-20 high-confidence words
    "aro": "total (accounting term)",
    "kuro": "total (accounting term)",
    "kupari": "cypress? (plant)",
    "kumi": "cumin? (plant)",
    "mari": "wool? (commodity)",
    "sara": "flax? (commodity)",
    "mini": "mint? (plant)",
    "kane": "maybe: bronze? or a vessel?",
    "pato": "perhaps related to PHAISTOS? or a unit",
    "dare": "perhaps a commodity or measure",
    "repa": "perhaps a commodity",
    "sipu": "possibly a vessel (cf. kissybion?)",
    "ima": "perhaps grain? or measure",
    "itani": "perhaps a theonym or toponym element",
    "maikaru": "perhaps a personal name or toponym",
    "asasara": "perhaps a theonym (cf. ASASARA formula)",
    "aroto": "perhaps a commodity",
    "rate": "perhaps a measure",
    "tame": "perhaps delivery/allocation",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class WordMatch:
    """A single word comparison result."""
    et_word: str  # Eteocretan word (cleaned)
    la_form: str  # Linear A form matched
    match_type: str  # "known_la_word", "loanword", "toponym", "partial"
    distance: int  # edit distance (0 = exact)
    confidence: str  # HIGH/MEDIUM/LOW
    evidence: str  # explanation of match


@dataclass
class ComparisonResult:
    """Aggregate comparison results."""
    word_matches: list[WordMatch] = field(default_factory=list)
    phonotactic_summary: dict = field(default_factory=dict)
    recurring_words: dict = field(default_factory=dict)
    sign_mappings: list[dict] = field(default_factory=list)
    bilingual_analysis: dict = field(default_factory=dict)
    statistics: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Phonotactic analysis
# ---------------------------------------------------------------------------


def _tokenize_phonemes(word: str) -> list[str]:
    """Tokenize a cleaned word into approximate phoneme-like segments.

    Simple approach for Eteocretan (written in Greek alphabet, mostly
    phonemic): each character is a phoneme approximation, except:
      th, ph, kh are single phonemes
      double consonants treated as single segments
    """
    i = 0
    tokens = []
    digraphs = {"th", "ph", "kh", "ps", "ks"}
    while i < len(word):
        if i + 1 < len(word) and word[i:i+2] in digraphs:
            tokens.append(word[i:i+2])
            i += 2
        else:
            tokens.append(word[i])
            i += 1
    return tokens


def _is_vowel(ch: str) -> bool:
    """Check if a phoneme token is a vowel."""
    vowels = {"a", "e", "i", "o", "u", "ā", "ē", "ō", "ū", "y"}
    return ch.lower() in vowels


def _phoneme_to_cv(token: str) -> str:
    """Convert a phoneme token to C or V."""
    if _is_vowel(token):
        return "V"
    else:
        return "C"


def compute_phonotactic_profile(word: str) -> dict:
    """Compute phonotactic profile of a word.

    Returns: {cv_sequence, syllable_count, c_ratio, v_ratio,
              initial, final, has_cv, has_vc, is_cvcv}
    """
    tokens = _tokenize_phonemes(word)
    if not tokens:
        return {
            "cv_sequence": "",
            "token_count": 0,
            "c_count": 0, "v_count": 0,
            "c_ratio": 0.0, "v_ratio": 0.0,
            "initial": "", "final": "",
            "has_open_syllable": False,
            "is_mostly_cvcv": False,
        }

    cv_seq = "".join(_phoneme_to_cv(t) for t in tokens)
    c_count = sum(1 for t in tokens if not _is_vowel(t))
    v_count = sum(1 for t in tokens if _is_vowel(t))
    total = len(tokens)

    # Check for CV(CV)* pattern — typical of agglutinative languages
    # including Minoan: mostly CVCV with occasional CC
    cv_pairs = sum(1 for j in range(0, len(tokens)-1, 2)
                   if j+1 < len(tokens)
                   and not _is_vowel(tokens[j])
                   and _is_vowel(tokens[j+1]))
    is_cvcv = cv_pairs >= (len(tokens) // 2) * 0.7

    return {
        "cv_sequence": cv_seq,
        "token_count": total,
        "c_count": c_count,
        "v_count": v_count,
        "c_ratio": round(c_count / total, 3) if total else 0.0,
        "v_ratio": round(v_count / total, 3) if total else 0.0,
        "initial": tokens[0] if tokens else "",
        "final": tokens[-1] if tokens else "",
        "has_open_syllable": cv_seq.endswith("V") if cv_seq else False,
        "is_mostly_cvcv": is_cvcv,
    }


# ---------------------------------------------------------------------------
# Edit distance (Levenshtein)
# ---------------------------------------------------------------------------


def edit_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(
                curr[-1] + 1,          # insert
                prev[j] + 1,           # delete
                prev[j - 1] + cost,    # substitute
            ))
        prev = curr
    return prev[-1]


def _normalize_form(s: str) -> str:
    """Normalize a form for comparison: lowercase, remove diacritics approximate."""
    replacements = {
        "ā": "a", "ē": "e", "ō": "o", "ū": "u",
        "th": "t", "ph": "p", "kh": "k",
        "w": "u", "y": "i",
        "j": "i",
    }
    result = s.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


# ---------------------------------------------------------------------------
# Word matching
# ---------------------------------------------------------------------------


def match_against_known_la_words(et_word: str) -> list[WordMatch]:
    """Compare an Eteocretan word against known Linear A words."""
    matches = []
    norm_et = _normalize_form(et_word)

    for la_word, meaning in KNOWN_LA_WORDS.items():
        norm_la = _normalize_form(la_word)
        dist = edit_distance(norm_et, norm_la)
        max_len = max(len(norm_et), len(norm_la))

        if dist == 0:
            confidence = "HIGH"
        elif dist <= 1 and max_len >= 3:
            confidence = "MEDIUM"
        elif dist <= 2 and max_len >= 4:
            confidence = "LOW"
        else:
            continue

        matches.append(WordMatch(
            et_word=et_word,
            la_form=la_word,
            match_type="known_la_word",
            distance=dist,
            confidence=confidence,
            evidence=f"Known LA word: {la_word} = '{meaning}'. Edit distance {dist}.",
        ))

    return matches


def match_against_loanwords(et_word: str, loanword_data: list[dict]) -> list[WordMatch]:
    """Compare against loanword matches from loanword_matches.csv."""
    matches = []
    norm_et = _normalize_form(et_word)

    seen_forms = set()
    for row in loanword_data:
        la_matched = row.get("matched", "")
        if not la_matched or la_matched in seen_forms:
            continue
        seen_forms.add(la_matched)

        norm_la = _normalize_form(la_matched)
        dist = edit_distance(norm_et, norm_la)
        max_len = max(len(norm_et), len(norm_la))

        if dist <= 1 and max_len >= 3:
            confidence = "MEDIUM"
        elif dist <= 2 and max_len >= 4:
            confidence = "LOW"
        else:
            continue

        matches.append(WordMatch(
            et_word=et_word,
            la_form=la_matched,
            match_type="loanword",
            distance=dist,
            confidence=confidence,
            evidence=(
                f"Loanword match: LA {la_matched} matched to Gk {row.get('greek', '?')} "
                f"'{row.get('english_gloss', '?')}'. Edit distance {dist}."
            ),
        ))

    return matches


def match_against_toponyms(et_word: str, toponym_data: list[dict]) -> list[WordMatch]:
    """Compare against toponym anchors."""
    matches = []
    norm_et = _normalize_form(et_word)

    seen_forms = set()
    for row in toponym_data:
        matched = row.get("matched_string", "")
        if not matched or matched in seen_forms:
            continue
        seen_forms.add(matched)

        norm_la = _normalize_form(matched)
        dist = edit_distance(norm_et, norm_la)
        max_len = max(len(norm_et), len(norm_la))

        if dist == 0:
            confidence = "HIGH"
        elif dist <= 1 and max_len >= 3:
            confidence = "MEDIUM"
        elif dist <= 2 and max_len >= 4:
            confidence = "LOW"
        else:
            continue

        matches.append(WordMatch(
            et_word=et_word,
            la_form=matched,
            match_type="toponym",
            distance=dist,
            confidence=confidence,
            evidence=(
                f"Toponym match: {row.get('place_name', '?')} ({row.get('la_spelling', '?')}). "
                f"LA fragment: {matched}. Edit distance {dist}."
            ),
        ))

    return matches


# ---------------------------------------------------------------------------
# Bilingual analysis
# ---------------------------------------------------------------------------


def analyze_bilinguals() -> dict:
    """Analyze the Greek-Eteocretan bilingual inscriptions.

    PR 2 is the key bilingual text. The Greek portion says:
       "...sons dedicated to Zeus (Dāi)..."

    Eteocretan words that appear near the Greek text:
       onadesimet, epikles, phar, isal, set, et

    Questions:
    - Is "onadesimet" the Eteocretan word for "dedicated/offered"?
    - Is "epikles" borrowed from Greek epiklētos 'called upon'?
    - Is "phar" related to Greek pherō 'bear/bring/offer'?
    - Is "set/et" a verbal or grammatical ending?
    """
    pr2 = [ins for ins in ALL_INSCRIPTIONS if ins.id == "PR 2"][0]

    bilingual_words = []
    for w in pr2.words:
        bilingual_words.append({
            "word": w.cleaned,
            "text": w.text,
            "notes": w.notes or "",
        })

    # Recurring words across texts (potential formula)
    recurring = Counter()
    for w in ALL_WORDS:
        if not w.is_greek and len(w.cleaned) >= 2:
            recurring[w.cleaned] += 1

    repeated = {w: c for w, c in recurring.items() if c >= 2}

    analysis = {
        "bilingual_inscription": "PR 2",
        "greek_summary": pr2.greek_text_summary,
        "et_words_near_greek": bilingual_words,
        "key_observations": [
            "PR 2 is the only clear bilingual — Eteocretan text on same stone as Greek dedication",
            "onadesimet appears in DR 2, PR 1, and PR 2 — the most repeated word (3 occurrences)",
            "epikles appears in DR 2 and PR 2 — possibly a loanword from Greek epiklētos 'invoked'",
            "isal appears in DR 1, PR 2, and PR 3",
            "set/ete appears in DR 1, PR 1, and PR 2 — possible verbal or grammatical ending",
            "kalmit appears in DR 1 and PR 1 — possible noun or name",
            "The word 'phar' near the Greek dedication could relate to 'offering/bringing' (cf. Gk pherō)",
            "Short words 'et' and 'no' appear across many texts — likely grammatical particles",
        ],
        "recurring_non_greek_words": repeated,
        "potential_cognates": [
            {
                "et_word": "onadesimet",
                "hypothesis": (
                    "Most repeated Eteocretan word (3×). Appears in the bilingual PR 2 near "
                    "a Greek dedication. Possibly = 'dedicated/offered/established' or a "
                    "formulaic phrase. Structure: ona-de-si-met? Matches Minoan agglutinative pattern."
                ),
                "la_possible_roots": ["ona", "desi", "met"],
            },
            {
                "et_word": "epikles",
                "hypothesis": (
                    "Likely borrowed from Greek epiklēs/epiklētos 'called upon, invoked'. "
                    "If so, it confirms Greek contact influence on Eteocretan vocabulary. "
                    "But could also be coincidental — many languages have similar-looking religious terms."
                ),
                "la_possible_roots": ["epi", "kles"],
            },
            {
                "et_word": "phar",
                "hypothesis": (
                    "Near Greek dedication in PR 2. Could be Eteocretan 'offering/bringing' "
                    "term. Compare Greek pherō 'I bring'. If it's the Eteocretan equivalent "
                    "of Greek anethēkan 'dedicated', this is hugely significant. But only 4 letters."
                ),
                "la_possible_roots": ["par"],
            },
            {
                "et_word": "barze",
                "hypothesis": (
                    "Unique word in PR 5. Possibly a name or noun. The sequence 'bar+ze' "
                    "looks potentially Minoan — bar/par is a common LA root."
                ),
                "la_possible_roots": ["bar"],
            },
        ],
    }

    return analysis


# ---------------------------------------------------------------------------
# Sign mapping
# ---------------------------------------------------------------------------


def map_words_to_la_signs(
    et_words: list[str],
    refined_grid: dict[str, dict],
) -> list[dict]:
    """Attempt to reverse-map Eteocretan phoneme sequences to Linear A signs.

    For each Eteocretan word, try to find a plausible Linear A sign sequence
    using the refined phonetic grid. Since LA is mostly CV, we try to break
    Eteocretan words into CV segments and match each to LA signs.

    This is speculative — we're essentially asking: "If this Eteocretan word
    were written in Linear A, what signs would be used?"
    """
    # Build lookup: (C+V) → list of AB signs
    cv_lookup: dict[str, list[str]] = {}
    for bennett_id, info in refined_grid.items():
        value = info.get("refined_value", "")
        if not value or value == "?":
            continue
        # Try both refined and conventional
        for val in {value, info.get("conventional_value", "")}:
            if not val or len(val) > 2:
                continue
            val = val.strip("?")
            if not val:
                continue
            key = val.lower()
            if key not in cv_lookup:
                cv_lookup[key] = []
            cv_lookup[key].append(bennett_id)

    # Also build V-only and C-only lookups for standalone vowels and codas
    v_lookup: dict[str, list[str]] = {"a": [], "e": [], "i": [], "o": [], "u": []}
    for bennett_id, info in refined_grid.items():
        for v in ["a", "e", "i", "o", "u"]:
            vals = {
                info.get("refined_value", ""),
                info.get("conventional_value", ""),
            }
            for val in vals:
                if val and val.strip("?") == v:
                    v_lookup[v].append(bennett_id)

    results = []
    for word in et_words:
        word_lower = word.lower()
        tokens = _tokenize_phonemes(word_lower)
        if len(tokens) < 2:
            continue

        # Try to segment into CV pairs
        segments = []
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens) and not _is_vowel(tokens[i]) and _is_vowel(tokens[i+1]):
                segments.append(tokens[i] + tokens[i+1])
                i += 2
            elif _is_vowel(tokens[i]):
                segments.append(tokens[i])
                i += 1
            else:
                segments.append(tokens[i])
                i += 1

        # Map each segment
        mapped_segments = []
        all_mapped = True
        for seg in segments:
            candidates = cv_lookup.get(seg, [])
            if not candidates and len(seg) == 1:
                candidates = v_lookup.get(seg, [])
            if not candidates:
                all_mapped = False
                mapped_segments.append({"segment": seg, "candidates": ["?"]})
            else:
                mapped_segments.append({
                    "segment": seg,
                    "candidates": candidates[:5],
                })

        results.append({
            "et_word": word,
            "tokens": tokens,
            "segments": [s["segment"] for s in mapped_segments],
            "mapped_segments": mapped_segments,
            "fully_mapped": all_mapped,
        })

    return results


# ---------------------------------------------------------------------------
# Phonotactic comparison
# ---------------------------------------------------------------------------


def compare_phonotactics() -> dict:
    """Compare Eteocretan phonotactics against known Linear A phonotactics.

    Known Linear A profile (from Phase 1-3):
    - Predominantly CV (open syllables)
    - C/V ratio approximately 55-60% consonants, 40-45% vowels
    - Agglutinative suffix chains
    - Very few consonant clusters
    """
    et_words = get_unique_et_words()
    profiles = []

    for w in et_words:
        profile = compute_phonotactic_profile(w.cleaned)
        profile["word"] = w.cleaned
        profiles.append(profile)

    if not profiles:
        return {"error": "no words to analyze"}

    avg_c = sum(p["c_ratio"] for p in profiles) / len(profiles)
    avg_v = sum(p["v_ratio"] for p in profiles) / len(profiles)
    open_syl = sum(1 for p in profiles if p["has_open_syllable"]) / len(profiles)
    cvcv_ratio = sum(1 for p in profiles if p["is_mostly_cvcv"]) / len(profiles)

    # Initial/final tendencies
    initials = Counter(p["initial"] for p in profiles if p["initial"])
    finals = Counter(p["final"] for p in profiles if p["final"])

    return {
        "word_count": len(profiles),
        "avg_c_ratio": round(avg_c, 3),
        "avg_v_ratio": round(avg_v, 3),
        "open_syllable_ratio": round(open_syl, 3),
        "cvcv_pattern_ratio": round(cvcv_ratio, 3),
        "common_initials": initials.most_common(10),
        "common_finals": finals.most_common(10),
        "individual_profiles": profiles,
        "comparison_to_la": {
            "la_typical": "CV-dominant, 55-60% C, 40-45% V, open syllables, few clusters",
            "eteocretan_assessment": (
                f"ET: {avg_c:.1%} C / {avg_v:.1%} V, {open_syl:.0%} open-syllable-final, "
                f"{cvcv_ratio:.0%} CVCV pattern match"
            ),
            "compatible": (
                abs(avg_c - 0.58) < 0.15  # within 15% of expected LA C-ratio
            ),
        },
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_all_comparisons(
    data_dir: str = "data/analysis",
    output_dir: str = "data/analysis/eteocretan",
) -> ComparisonResult:
    """Run all Eteocretan ↔ Linear A comparisons and save output files.

    Returns a ComparisonResult with all findings.
    """
    os.makedirs(output_dir, exist_ok=True)

    result = ComparisonResult()

    # ── Load reference data ──
    loanword_path = os.path.join(data_dir, "linguistic", "loanword_matches.csv")
    toponym_path = os.path.join(data_dir, "linguistic", "toponym_anchors.csv")
    grid_path = os.path.join(data_dir, "comparative", "refined_phonetic_grid.csv")

    loanwords = []
    if os.path.exists(loanword_path):
        with open(loanword_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            loanwords = list(reader)
    logger.info(f"Loaded {len(loanwords)} loanword entries")

    toponyms = []
    if os.path.exists(toponym_path):
        with open(toponym_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            toponyms = list(reader)
    logger.info(f"Loaded {len(toponyms)} toponym entries")

    refined_grid = {}
    if os.path.exists(grid_path):
        with open(grid_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                refined_grid[row["bennett_id"]] = row
    logger.info(f"Loaded {len(refined_grid)} grid entries")

    # ── 1. Word matching ──
    et_vocab = get_vocabulary()
    logger.info(f"Comparing {len(et_vocab)} unique Eteocretan words...")

    all_matches: list[WordMatch] = []
    for word in et_vocab:
        all_matches.extend(match_against_known_la_words(word))
        all_matches.extend(match_against_loanwords(word, loanwords))
        all_matches.extend(match_against_toponyms(word, toponyms))

    # Deduplicate and sort
    seen = set()
    unique_matches = []
    for m in all_matches:
        key = (m.et_word, m.la_form, m.match_type)
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    unique_matches.sort(key=lambda m: m.distance)
    result.word_matches = unique_matches

    # ── 2. Phonotactics ──
    result.phonotactic_summary = compare_phonotactics()

    # ── 3. Recurring words ──
    recurring = Counter(
        w.cleaned for w in ALL_WORDS
        if not w.is_greek and len(w.cleaned) >= 2
    )
    result.recurring_words = {
        "total_et_tokens": sum(1 for w in ALL_WORDS if not w.is_greek),
        "unique_et_types": len(et_vocab),
        "type_token_ratio": round(len(et_vocab) / max(1, sum(1 for w in ALL_WORDS if not w.is_greek)), 3),
        "most_repeated": recurring.most_common(15),
    }

    # ── 4. Sign mapping ──
    result.sign_mappings = map_words_to_la_signs(et_vocab, refined_grid)

    # ── 5. Bilingual analysis ──
    result.bilingual_analysis = analyze_bilinguals()

    # ── 6. Statistics ──
    result.statistics = {
        "total_inscriptions": len(ALL_INSCRIPTIONS),
        "total_word_tokens": len(ALL_WORDS),
        "total_et_tokens": sum(1 for w in ALL_WORDS if not w.is_greek),
        "total_greek_tokens": sum(1 for w in ALL_WORDS if w.is_greek),
        "unique_et_types": len(et_vocab),
        "bilingual_texts": sum(1 for ins in ALL_INSCRIPTIONS if ins.is_bilingual),
        "total_matches_found": len(unique_matches),
        "high_conf_matches": sum(1 for m in unique_matches if m.confidence == "HIGH"),
        "medium_conf_matches": sum(1 for m in unique_matches if m.confidence == "MEDIUM"),
        "low_conf_matches": sum(1 for m in unique_matches if m.confidence == "LOW"),
        "fully_mapped_words": sum(1 for m in result.sign_mappings if m["fully_mapped"]),
        "phonotactics_compatible": result.phonotactic_summary.get("comparison_to_la", {}).get("compatible", False),
    }

    # ── Write output CSVs ──
    # Word matches
    matches_path = os.path.join(output_dir, "comparison_results.csv")
    with open(matches_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "et_word", "la_form", "match_type", "edit_distance",
            "confidence", "evidence"
        ])
        for m in unique_matches:
            writer.writerow([
                m.et_word, m.la_form, m.match_type,
                m.distance, m.confidence, m.evidence,
            ])
    logger.info(f"Comparison results written: {matches_path} ({len(unique_matches)} matches)")

    # Phonotactic profiles
    phono_path = os.path.join(output_dir, "phonotactic_profiles.csv")
    with open(phono_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "word", "cv_sequence", "token_count", "c_count", "v_count",
            "c_ratio", "v_ratio", "initial", "final",
            "has_open_syllable", "is_mostly_cvcv"
        ])
        for p in result.phonotactic_summary.get("individual_profiles", []):
            writer.writerow([
                p.get("word", ""), p.get("cv_sequence", ""),
                p.get("token_count", 0), p.get("c_count", 0), p.get("v_count", 0),
                p.get("c_ratio", 0), p.get("v_ratio", 0),
                p.get("initial", ""), p.get("final", ""),
                p.get("has_open_syllable", False), p.get("is_mostly_cvcv", False),
            ])
    logger.info(f"Phonotactic profiles written: {phono_path}")

    # Sign mappings
    signmap_path = os.path.join(output_dir, "sign_mappings.csv")
    with open(signmap_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["et_word", "tokens", "segments", "fully_mapped", "mapped_signs"])
        for m in result.sign_mappings:
            signs_flat = "; ".join(
                f"{s['segment']}→{','.join(s['candidates'][:3])}"
                for s in m["mapped_segments"]
            )
            writer.writerow([
                m["et_word"],
                "-".join(m["tokens"]),
                "-".join(m["segments"]),
                m["fully_mapped"],
                signs_flat,
            ])
    logger.info(f"Sign mappings written: {signmap_path}")

    return result
