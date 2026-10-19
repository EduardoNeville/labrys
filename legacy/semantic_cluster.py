#!/usr/bin/env python3
"""
Semantic Clustering of Commodity-Adjacent Syllabogram Sequences
=================================================================
Cluster logogram-adjacent syllabogram sequences, rank distinctive sequences
per commodity, and check if distinctive sequences contain UNCERTAIN signs
as candidates for commodity-name phonemes.

Reads: data/analysis/commodity_decoding/logogram_contexts.csv
       data/analysis/ml/uncertain_predictions.csv
Writes: data/analysis/commodity_decoding/commodity_report.md

Key questions:
  - Are there syllabogram sequences that uniquely identify a commodity class?
  - Do any distinctive sequences contain UNCERTAIN signs, giving semantic constraints?
  - Do ML predictions for those signs produce plausible readings?
  - Can we reconstruct proto-words for common trade goods?
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict, Counter
from itertools import combinations
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTEXT_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "commodity_decoding", "logogram_contexts.csv"
)
OUT_DIR = os.path.join(BASE_DIR, "data", "analysis", "commodity_decoding")
os.makedirs(OUT_DIR, exist_ok=True)

ML_PREDICTIONS_PATH = os.path.join(
    BASE_DIR, "data", "analysis", "ml", "uncertain_predictions.csv"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_ml_predictions() -> dict[str, dict]:
    """Load ML predictions for UNCERTAIN signs."""
    ml_map: dict[str, dict] = {}
    if os.path.exists(ML_PREDICTIONS_PATH):
        with open(ML_PREDICTIONS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_map[row["bennett_id"]] = row
    return ml_map


def _bennett_to_ml_value(bid: str, ml_map: dict) -> Optional[str]:
    """Get the ML-predicted transliteration for a Bennett ID."""
    if bid in ml_map:
        return ml_map[bid].get("predicted_refined_value", "")
    return None


def _has_ml_prediction(bid: str, ml_map: dict) -> bool:
    """Check if an ML prediction exists for this Bennett ID."""
    val = _bennett_to_ml_value(bid, ml_map)
    return bool(val and val != "?" and val != "")


# ---------------------------------------------------------------------------
# Sequence extraction from context rows
# ---------------------------------------------------------------------------


def extract_sequences(context_rows: list[dict]) -> dict[str, list[list[tuple]]]:
    """Extract syllabogram sequences adjacent to each commodity logogram.

    Returns dict[commodity_class -> list of sequences, where each sequence
    is a list of (position, bennett_id, transliteration) tuples.
    Positions: 'b3','b2','b1' (before) and 'a1','a2','a3' (after).
    """
    seqs: dict[str, list[list[tuple]]] = defaultdict(list)

    for row in context_rows:
        comm = row.get("commodity_class", "")
        if not comm:
            continue

        # Build the signed sequence around the logogram
        seq = []
        for pos in ["before_-3", "before_-2", "before_-1",
                     "after_1", "after_2", "after_3"]:
            bennett = row.get(f"{pos}_bennett", "") or ""
            translit = row.get(f"{pos}_translit", "") or ""
            stype = row.get(f"{pos}_type", "") or ""
            if stype == "syllabogram" and bennett and bennett.startswith("AB "):
                seq.append((pos, bennett, translit))

        # Filter out sequences that are just empty transliterations
        valid = [s for s in seq if s[2] and s[2].strip()]
        if valid:
            seqs[comm].append(valid)

    return seqs


# ---------------------------------------------------------------------------
# N-gram profiling per commodity
# ---------------------------------------------------------------------------


def build_ngram_profiles(
    seqs: dict[str, list[list[tuple]]],
    n: int = 2,
) -> dict[str, dict]:
    """Build n-gram frequency profiles per commodity class.

    Returns dict[commodity -> {
        'ngrams': Counter of (translit1, translit2, ...) tuples,
        'ngrams_bennett': Counter of (bennett1, bennett2, ...) tuples,
        'total_ngrams': int,
        'total_sequences': int,
    }]
    """
    profiles: dict[str, dict] = {}

    for comm, sequences in seqs.items():
        ngram_counter = Counter()
        bennett_counter = Counter()
        total_ngrams = 0

        for seq in sequences:
            translits = [s[2] for s in seq if s[2]]
            bennetts = [s[1] for s in seq if s[1]]
            for i in range(len(translits) - n + 1):
                ng = tuple(translits[i : i + n])
                ngram_counter[ng] += 1
                total_ngrams += 1
            for i in range(len(bennetts) - n + 1):
                bg = tuple(bennetts[i : i + n])
                bennett_counter[bg] += 1

        profiles[comm] = {
            "ngrams": ngram_counter,
            "ngrams_bennett": bennett_counter,
            "total_ngrams": total_ngrams,
            "total_sequences": len(sequences),
        }

    return profiles


# ---------------------------------------------------------------------------
# Distinctiveness scoring
# ---------------------------------------------------------------------------


def score_distinctiveness(
    profiles: dict[str, dict],
) -> dict[str, list[tuple]]:
    """Score how distinctive each n-gram is for its commodity class.

    For each n-gram in commodity C:
       distinctiveness = (freq_in_C / total_in_C) / (freq_in_others / total_in_others)

    Returns dict[commodity -> list of (ngram, score, freq_in_C, freq_in_others)].
    """
    all_commodities = list(profiles.keys())
    results: dict[str, list[tuple]] = defaultdict(list)

    for comm in all_commodities:
        prof = profiles[comm]
        my_ngrams = prof["ngrams"]
        my_total = prof["total_ngrams"]

        if my_total == 0:
            continue

        # Aggregate other commodities
        other_ngrams: Counter = Counter()
        other_total = 0
        for other_comm in all_commodities:
            if other_comm == comm:
                continue
            other_ngrams.update(profiles[other_comm]["ngrams"])
            other_total += profiles[other_comm]["total_ngrams"]

        # Score each n-gram
        scored = []
        for ng, cnt in my_ngrams.most_common():
            my_freq = cnt / my_total if my_total > 0 else 0
            other_cnt = other_ngrams.get(ng, 0)
            other_freq = other_cnt / other_total if other_total > 0 else 0

            # Distinctiveness ratio (with Laplace smoothing)
            if other_freq < 1e-10:
                score = float("inf")
            else:
                score = my_freq / other_freq

            scored.append((ng, score, cnt, other_cnt))

        scored.sort(key=lambda x: -x[1])
        results[comm] = scored

    return results


# ---------------------------------------------------------------------------
# UNCERTAIN sign analysis
# ---------------------------------------------------------------------------


def analyze_uncertain_signs(
    profiles: dict[str, dict],
    distinctiveness: dict[str, list[tuple]],
    ml_map: dict[str, dict],
    top_n: int = 10,
) -> dict[str, dict]:
    """Analyze whether distinctive sequences contain UNCERTAIN signs.

    For each distinctive n-gram (transliteration bigram/trigram), we look up
    the matching Bennett-ID n-grams and check only those specific Bennett IDs
    for UNCERTAIN/ML-prediction status.

    Returns dict[commodity -> {
        'distinctive_with_uncertain': list of (ngram, score, uncertain_signs),
        'candidate_proto_words': list of {sequence, ml_reading, notes},
    }]
    """
    results: dict[str, dict] = {}

    for comm, scored in distinctiveness.items():
        prof = profiles[comm]
        bennett_ngrams = prof["ngrams_bennett"]

        distinctive_uncertain: list[tuple] = []
        candidate_words: list[dict] = []
        seen_candidates: set[str] = set()

        top_ngrams = scored[:top_n]

        for ng, score, cnt, other_cnt in top_ngrams:
            # Filter out junk sequences (empty transliterations, numerals,
            # fractions, or punctuation-like tokens masquerading as n-grams)
            ng_strs = [str(x).strip() for x in ng]
            if any(not s or s in ("", "?", "-", "≈", "—") for s in ng_strs):
                continue
            # Skip if any token is clearly not a syllabogram (numbers, fractions, etc.)
            if any(
                s.startswith("[") or "⁄" in s or s.isdigit()
                for s in ng_strs
            ):
                continue

            # Now find matching Bennett n-grams: we need Bennett bigrams where
            # the transliteration values of those Bennetts would match this n-gram.
            # Build a mapping: transliteration -> set of bennett_ids that could produce it
            translit_to_bennett: dict[str, set[str]] = defaultdict(set)
            for bid, info in ml_map.items():
                val = info.get("predicted_refined_value", "").strip()
                if val:
                    translit_to_bennett[val].add(bid)

            # For each position in the n-gram, find Bennett IDs that match
            position_candidates: list[set[str]] = []
            for t in ng_strs:
                cands: set[str] = set()
                # Add exact matches from ML predictions
                if t in translit_to_bennett:
                    cands.update(translit_to_bennett[t])
                position_candidates.append(cands)

            # Find Bennett IDs that are both (a) in the matching Bennett n-gram
            # and (b) are UNCERTAIN (have ML predictions)
            uncertain_in_ng: list[str] = []

            for bg in bennett_ngrams:
                if len(bg) != len(ng_strs):
                    continue
                # Check if ANY Bennett in this bg matches our transliteration
                # and is UNCERTAIN
                for bid in bg:
                    if _has_ml_prediction(bid, ml_map):
                        # Check if this bid could produce this transliteration
                        ml_val = _bennett_to_ml_value(bid, ml_map) or ""
                        if ml_val and ml_val in ng_strs:
                            if bid not in uncertain_in_ng:
                                uncertain_in_ng.append(bid)

            if uncertain_in_ng:
                ml_reading = "-".join(ng_strs)

                if ml_reading not in seen_candidates:
                    seen_candidates.add(ml_reading)
                    candidate_words.append({
                        "sequence": "-".join(ng_strs),
                        "ml_reading": ml_reading,
                        "uncertain_signs": "; ".join(sorted(uncertain_in_ng)),
                        "distinctiveness_score": f"{score:.3f}",
                        "ngram_count": cnt,
                    })

                distinctive_uncertain.append(
                    (ng, score, uncertain_in_ng)
                )

        results[comm] = {
            "distinctive_with_uncertain": distinctive_uncertain,
            "candidate_proto_words": candidate_words,
        }

    return results


# ---------------------------------------------------------------------------
# Proto-word reconstruction
# ---------------------------------------------------------------------------


def reconstruct_proto_words(
    profiles: dict[str, dict],
    distinctiveness: dict[str, list[tuple]],
    ml_map: dict[str, dict],
) -> list[dict]:
    """Attempt to reconstruct plausible proto-words for key trade goods.

    Uses the distinctive n-grams (from score_distinctiveness) as the primary input,
    cross-referencing with known Mediterranean trade vocabulary.

    Returns list of proto-word hypotheses.
    """
    hypotheses: list[dict] = []

    TRADE_REFERENCE = {
        "WINE": [
            ("wo-no", "Mycenaean *woinos"),
            ("wi-ja", "Hittite wiyana-"),
            ("wi-ne", "Mycenaean *woinos alt."),
        ],
        "OLIVE_OIL": [
            ("e-ra-wa", "Mycenaean *elaiwon"),
            ("e-ra-wo", "Mycenaean *elaiwo gen."),
            ("a-re-pa", "Mycenaean *aleiphar"),
            ("e-re-pa", "cf. *elaiwa?"),
        ],
        "GRAIN": [
            ("si-to", "Mycenaean *sitos"),
            ("ki-ri", "Mycenaean *kri barley"),
        ],
        "CLOTH": [
            ("pa-wo", "Mycenaean *pharwos"),
            ("te-pa", "Mycenaean *tepa?"),
        ],
        "VESSELS": [
            ("di-pa", "Mycenaean *dipas cup"),
            ("a-ke", "Mycenaean *aggeion"),
        ],
        "LIVESTOCK": [
            ("qe-ra", "cf. Mycenaean *qera? goat?"),
        ],
    }

    # Build reverse map: ml_predicted_value -> set(bennett_ids)
    ml_value_to_bids: dict[str, set[str]] = defaultdict(set)
    for bid, info in ml_map.items():
        val = info.get("predicted_refined_value", "").strip().lower()
        if val and val != "?":
            ml_value_to_bids[val].add(bid)

    seen: set[str] = set()

    for comm, scored in distinctiveness.items():
        if not scored:
            continue

        refs = TRADE_REFERENCE.get(comm, [])
        # Look at top 8 most distinctive n-grams
        for ng, score, cnt, other_cnt in scored[:8]:
            # Filter junk
            ng_strs = [str(x).strip().lower() for x in ng]
            if len(ng_strs) < 2:
                continue
            if any(not s or s in ("", "?", "-", "≈", "—") for s in ng_strs):
                continue
            if any(
                c in s for c in "⁄¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉"
                for s in ng_strs
            ):
                continue

            reading = "-".join(ng_strs)
            if reading in seen:
                continue
            seen.add(reading)

            # Check which signs in this sequence are UNCERTAIN
            uncertain_bids: list[str] = []
            for t in ng_strs:
                if t in ml_value_to_bids:
                    uncertain_bids.extend(sorted(ml_value_to_bids[t]))

            # Cross-reference with trade vocabulary
            matches: list[str] = []
            for ref_seq, ref_note in refs:
                ref_sylls = ref_seq.split("-")
                if len(ref_sylls) == len(ng_strs):
                    overlap = sum(
                        1 for r, p in zip(ref_sylls, ng_strs)
                        if r[:2] == p[:2]
                    )
                    if overlap >= len(ref_sylls) * 0.5:
                        matches.append(f"{ref_seq} ({ref_note})")

            if uncertain_bids and cnt >= 1:
                hypotheses.append({
                    "commodity": comm,
                    "sequence": reading,
                    "ngram_count": cnt,
                    "distinctiveness_ratio": f"{score:.2f}",
                    "uncertain_signs_involved": "; ".join(sorted(set(uncertain_bids))),
                    "trade_word_matches": "; ".join(matches) if matches else "none",
                    "assessment": (
                        "Plausible trade-word candidate"
                        if matches
                        else ("Highly distinctive — possible commodity term"
                              if score > 5.0 else "Novel sequence — no known cognates")
                    ),
                })

    return hypotheses


# ---------------------------------------------------------------------------
# Build the report
# ---------------------------------------------------------------------------


def build_report(
    profiles: dict[str, dict],
    distinctiveness: dict[str, list[tuple]],
    uncertain_analysis: dict[str, dict],
    proto_words: list[dict],
    commodity_seqs: dict[str, list[list[tuple]]],
) -> str:
    """Build the commodity_decoding report as markdown."""

    lines = []
    lines.append("# Commodity-Semantic Decoding Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        "This report analyzes syllabogram sequences adjacent to Linear A "
        "commodity logograms (WINE, GRAIN, OLIVE OIL, VESSELS, etc.) to identify "
        "candidate commodity-name phonemes. The approach is constrained semantic "
        "decoding — we know what many logograms *mean* and we look at what "
        "syllabograms consistently surround them."
    )
    lines.append("")
    lines.append("## Data Summary")
    lines.append("")
    lines.append("| Commodity Class | Occurrences | Distinct Logograms | Adjacent Sylls |")
    lines.append("|---|---|---|---|")
    for comm in sorted(profiles.keys(), key=lambda c: -profiles[c]["total_sequences"]):
        prof = profiles[comm]
        total_syll = sum(prof["ngrams"].values())
        lines.append(
            f"| {comm} | {prof['total_sequences']} | "
            f"{len(set(bid for bg in prof['ngrams_bennett'] for bid in bg))} | "
            f"{total_syll} |"
        )
    lines.append("")

    # --- Distinctive n-grams per commodity ---
    lines.append("## Distinctive Syllabogram Sequences per Commodity")
    lines.append("")
    lines.append(
        "For each commodity class, the most distinctive adjacent bigrams/trigrams "
        "are ranked by *distinctiveness ratio*: how much more common they are near "
        "this commodity vs. all others."
    )
    lines.append("")

    for comm in sorted(profiles.keys(), key=lambda c: -profiles[c]["total_sequences"]):
        scored = distinctiveness.get(comm, [])
        if not scored:
            lines.append(f"### {comm}")
            lines.append("")
            lines.append("No distinctive sequences found.")
            lines.append("")
            continue

        lines.append(f"### {comm}")
        lines.append("")
        lines.append("| Rank | Sequence | Freq (this comm) | Freq (others) | Ratio |")
        lines.append("|---|---|---|---|---|")

        for rank, (ng, score, cnt, other_cnt) in enumerate(scored[:15], 1):
            seq_str = "-".join(str(x) for x in ng)
            ratio_str = f"{score:.2f}" if score != float("inf") else "∞"
            lines.append(f"| {rank} | {seq_str} | {cnt} | {other_cnt} | {ratio_str} |")
        lines.append("")

    # --- UNCERTAIN signs in distinctive sequences ---
    lines.append("## UNCERTAIN Signs in Distinctive Sequences")
    lines.append("")
    lines.append(
        "Distinctive sequences that contain UNCERTAIN signs (those with ML predictions "
        "from Phase 4) are prime candidates for commodity-name phonemes. If a sign's "
        "ML-predicted value produces a reading that matches known Mediterranean trade "
        "vocabulary, that strengthens both the ML prediction and the semantic decoding."
    )
    lines.append("")

    for comm in sorted(profiles.keys(), key=lambda c: -profiles[c]["total_sequences"]):
        ua = uncertain_analysis.get(comm, {})
        cands = ua.get("candidate_proto_words", [])
        if not cands:
            lines.append(f"### {comm}")
            lines.append("")
            lines.append("No distinctive sequences with UNCERTAIN signs.")
            lines.append("")
            continue

        lines.append(f"### {comm}")
        lines.append("")
        lines.append(
            "| Sequence | ML Reading | UNCERTAIN Signs | Score | Count |"
        )
        lines.append("|---|---|---|---|---|")
        for cw in cands:
            lines.append(
                f"| {cw['sequence']} | {cw['ml_reading']} | "
                f"{cw['uncertain_signs']} | {cw['distinctiveness_score']} | "
                f"{cw['ngram_count']} |"
            )
        lines.append("")

    # --- Proto-word hypotheses ---
    lines.append("## Proto-Word Hypotheses")
    lines.append("")
    lines.append(
        "Using ML-predicted values for UNCERTAIN signs plus conventional AB values "
        "for CONFIRM signs, we can assemble candidate readings for sequences that "
        "are distinctive to specific commodities. These are cross-referenced with "
        "known Mediterranean trade vocabulary (Mycenaean, pre-Greek, Hittite, etc.)."
    )
    lines.append("")
    lines.append("**⚠️ CAUTION**: These are HYPOTHESES, not decipherment claims. "
                "Linear A remains undeciphered after 70+ years of effort. "
                "These readings are constrained semantic guesses, not confirmed values.")
    lines.append("")

    if proto_words:
        lines.append(
            "| Commodity | Sequence | Count | UNCERTAIN Signs | "
            "Trade Word Matches | Assessment |"
        )
        lines.append("|---|---|---|---|---|---|")
        for hw in proto_words[:30]:
            lines.append(
                f"| {hw['commodity']} | {hw['sequence']} | {hw['ngram_count']} | "
                f"{hw['uncertain_signs_involved']} | "
                f"{hw['trade_word_matches']} | {hw['assessment']} |"
            )
    else:
        lines.append("No proto-word hypotheses generated.")
    lines.append("")

    # --- Overall assessment ---
    lines.append("## Overall Assessment")
    lines.append("")

    # Count how many commodities have distinctive sequences
    commodities_with_distinctive = sum(
        1 for comm, scored in distinctiveness.items()
        if scored and scored[0][1] > 2.0
    )
    total_commodities = len(profiles)
    lines.append(
        f"- **{commodities_with_distinctive}/{total_commodities}** commodity classes "
        "have at least one syllabogram sequence with distinctiveness ratio > 2.0"
    )

    total_uncertain_candidates = sum(
        len(ua.get("candidate_proto_words", []))
        for ua in uncertain_analysis.values()
    )
    lines.append(
        f"- **{total_uncertain_candidates}** candidate sequences contain "
        "UNCERTAIN signs that could be constrained by commodity semantics"
    )

    proto_word_count = len(proto_words)
    proto_with_matches = sum(1 for hw in proto_words if hw["trade_word_matches"] != "none")
    lines.append(
        f"- **{proto_with_matches}/{proto_word_count}** proto-word hypotheses "
        "have plausible Mediterranean trade vocabulary matches"
    )

    lines.append("")
    lines.append("### Key Observations")
    lines.append("")

    # Find the strongest signals
    strongest = sorted(
        [(comm, scored[0]) for comm, scored in distinctiveness.items() if scored],
        key=lambda x: -x[1][1],
    )[:5]
    for comm, (ng, score, cnt, other_cnt) in strongest:
        if score == float("inf"):
            lines.append(
                f"- **{comm}**: Sequence `{'-'.join(str(x) for x in ng)}` is "
                f"*only* found near this commodity (distinctiveness = ∞)"
            )
        else:
            lines.append(
                f"- **{comm}**: Sequence `{'-'.join(str(x) for x in ng)}` is "
                f"{score:.1f}× more common near this commodity"
            )

    lines.append("")
    lines.append("### Key Limitations")
    lines.append("")
    lines.append(
        "- The Linear A corpus is small (~11K signs), so statistical distinctiveness "
        "is fragile — a single new tablet could change rankings."
    )
    lines.append(
        "- ML predictions for UNCERTAIN signs are probabilistic (confidence typically "
        "5–50%), and our proto-word readings compound this uncertainty multiplicatively."
    )
    lines.append(
        "- Adjacent syllabograms may encode quantities, transaction verbs, or "
        "administrative formulas rather than commodity names — our current approach "
        "cannot distinguish these."
    )
    lines.append(
        "- The three most common syllabograms near most commodities are measurement "
        "formulas / transaction terms, not commodity names."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("Semantic Clustering — Phase 2b")
    print("=" * 60)

    # Load context data
    if not os.path.exists(CONTEXT_PATH):
        print(f"ERROR: {CONTEXT_PATH} not found. Run context_extract.py first.")
        return

    context_rows: list[dict] = []
    with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        context_rows = list(reader)
    print(f"Loaded {len(context_rows)} context windows from logogram_contexts.csv")

    # Load ML predictions
    ml_map = load_ml_predictions()
    print(f"Loaded {len(ml_map)} ML predictions for UNCERTAIN signs.")

    # Extract syllabogram sequences by commodity
    commodity_seqs = extract_sequences(context_rows)
    print(f"\nExtracted sequences for {len(commodity_seqs)} commodity classes:")
    for comm, seqs in sorted(commodity_seqs.items(),
                              key=lambda x: -len(x[1])):
        print(f"  {comm}: {len(seqs)} sequences")

    # Build bigram profiles
    profiles_2 = build_ngram_profiles(commodity_seqs, n=2)
    profiles_3 = build_ngram_profiles(commodity_seqs, n=3)

    # We'll use bigram profiles as the primary analysis (larger sample)
    profiles = profiles_2
    # But also consider trigram info where available
    for comm in profiles_2:
        if comm in profiles_3:
            # Merge trigram n-grams into bigram profiles as additional evidence
            profiles[comm]["ngrams"].update(profiles_3[comm]["ngrams"])
            profiles[comm]["ngrams_bennett"].update(profiles_3[comm]["ngrams_bennett"])
            profiles[comm]["total_ngrams"] += profiles_3[comm]["total_ngrams"]

    # Score distinctiveness
    distinctiveness = score_distinctiveness(profiles)
    print("\nDistinctiveness scores computed.")

    # Analyze UNCERTAIN signs
    uncertain_analysis = analyze_uncertain_signs(
        profiles, distinctiveness, ml_map
    )
    print("UNCERTAIN sign analysis complete.")

    # Reconstruct proto-words
    proto_words = reconstruct_proto_words(
        profiles, distinctiveness, ml_map
    )
    print(f"Generated {len(proto_words)} proto-word hypotheses.")

    # Build and write report
    report = build_report(
        profiles, distinctiveness, uncertain_analysis,
        proto_words, commodity_seqs,
    )
    report_path = os.path.join(OUT_DIR, "commodity_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nWrote report to {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for comm, scored in sorted(distinctiveness.items(),
                                key=lambda x: -x[1][0][1] if x[1] else 0):
        if not scored:
            print(f"\n{comm}: no distinctive sequences found")
            continue

        top3 = scored[:3]
        print(f"\n{comm} (top 3 distinctive sequences):")
        for ng, score, cnt, other_cnt in top3:
            seq_str = "-".join(str(x) for x in ng)
            urt = uncertain_analysis.get(comm, {}).get(
                "candidate_proto_words", []
            )
            urt_note = ""
            for cw in urt:
                if cw["sequence"] == seq_str:
                    urt_note = f" [UNCERTAIN: {cw['uncertain_signs']}]"
                    break
            print(f"  {seq_str:30s}  ratio={score:>8.2f}  "
                  f"n_comm={cnt:>3d}  n_other={other_cnt:>3d}{urt_note}")

    print("\nDone!")


if __name__ == "__main__":
    main()
