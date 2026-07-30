#!/usr/bin/env python3
"""
morphology_scan.py — Systematic morphological analysis of the Linear A corpus.

Performs:
  1. Load consensus word-segmented corpus
  2. Extract unique words
  3. Morphological paradigm scan (suffix/prefix alternations)
  4. Agglutination analysis (word length distribution, recurring building blocks)
  5. Reduplication scan (CV-CV- patterns)
  6. Commodity-adjacent text analysis (pre-/post-modifier word order)
  7. Output CSV and Markdown summary
"""

import csv
import os
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "analysis", "segmentation", "segmented_texts_consensus.csv"
)

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "analysis", "linguistic"
)
OUT_PARADIGMS = os.path.join(OUT_DIR, "morphology_paradigms.csv")
OUT_WORD_LEN   = os.path.join(OUT_DIR, "word_length_distribution.csv")
OUT_REDUP      = os.path.join(OUT_DIR, "reduplication_patterns.csv")
OUT_SUMMARY    = os.path.join(OUT_DIR, "morphology_summary.md")

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Unicode ranges for Linear A / Aegean scripts
# ---------------------------------------------------------------------------
WORD_DIVIDER = '\U00010101'   # 𐄁

SYLLABOGRAM_START = 0x10600
SYLLABOGRAM_END   = 0x106FF

LOGOGRAM_START    = 0x10700
LOGOGRAM_END      = 0x1077F

NUMERAL_START     = 0x10100
NUMERAL_END       = 0x1013F


def is_syllabogram(ch: str) -> bool:
    return SYLLABOGRAM_START <= ord(ch) <= SYLLABOGRAM_END

def is_logogram(ch: str) -> bool:
    return LOGOGRAM_START <= ord(ch) <= LOGOGRAM_END

def is_numeral(ch: str) -> bool:
    return NUMERAL_START <= ord(ch) <= NUMERAL_END

def is_sign(ch: str) -> bool:
    return is_syllabogram(ch) or is_logogram(ch) or is_numeral(ch)

def is_phonetic(ch: str) -> bool:
    """True if ch is a syllabogram (phonetic sign)."""
    return is_syllabogram(ch)

def is_valid_word(word: str) -> bool:
    return any(is_syllabogram(c) or is_logogram(c) for c in word)

def sign_sequence(word: str) -> str:
    """Return only syllabograms and logograms (strip numerals, punctuation)."""
    return ''.join(c for c in word if is_syllabogram(c) or is_logogram(c))

def phonetic_sequence(word: str) -> str:
    """Return only syllabograms (phonetic signs, strip logograms and numerals)."""
    return ''.join(c for c in word if is_syllabogram(c))

def sign_length(word: str) -> int:
    return sum(1 for c in word if is_syllabogram(c) or is_logogram(c))

def phonetic_length(word: str) -> int:
    return sum(1 for c in word if is_syllabogram(c))


# ---------------------------------------------------------------------------
# 1. Load corpus
# ---------------------------------------------------------------------------
def load_consensus_corpus(path: str):
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            confidence = float(row['confidence'])
            if confidence <= 0:
                continue
            text = row['segmented_text']
            words = extract_words(text)
            records.append({
                'gorila_id': row['gorila_id'],
                'inscription_id': row['inscription_id'],
                'num_signs': int(row['num_signs']),
                'num_words': int(row['num_words']),
                'words': words,
                'raw_text': text,
            })
    return records


def extract_words(text: str):
    parts = text.split(WORD_DIVIDER)
    words = []
    for p in parts:
        p = p.strip()
        p = p.replace(' | ', '')
        p = p.replace('|', '')
        p = p.strip()
        if p and is_valid_word(p):
            words.append(p)
    return words


def build_vocab(records):
    vocab = Counter()
    for rec in records:
        for w in rec['words']:
            if is_valid_word(w):
                vocab[w] += 1
    return vocab


# ---------------------------------------------------------------------------
# 3. Morphological paradigm scan
# ---------------------------------------------------------------------------
def scan_paradigms(vocab, records):
    """
    Identify candidate morphological paradigms by comparing words
    for shared roots with varying affixes.

    We look at:
    a) Suffixation: wordA = root + X, wordB = root + Y  (X,Y ∈ {1,2}-sign endings)
    b) Prefixation: wordA = X + root, wordB = Y + root  (X,Y ∈ {1,2}-sign starts)

    Uses the full sign sequence (syllabograms + logograms included) for matching.
    Only considers words with at least 3 phonetic signs.
    """
    paradigms = []

    # Build list of words with their phonetic and full sign sequences
    entries = []
    for w, c in vocab.items():
        if not is_valid_word(w):
            continue
        ph = phonetic_sequence(w)   # syllabograms only
        full = sign_sequence(w)     # syllabograms + logograms
        if len(ph) < 3:
            continue
        entries.append((w, c, ph, full))

    # Pre-build text index for context lookup
    word_texts = defaultdict(set)
    for rec in records:
        for w in rec['words']:
            if is_valid_word(w):
                word_texts[w].add(rec['gorila_id'])

    # ---------------------------------------------------------------
    # Suffix scan: words sharing a prefix (root) with different endings
    # ---------------------------------------------------------------
    suffix_groups = defaultdict(list)  # (root_phonetic, suffix_len) -> [(word, freq, alt_suffix, full_seq)]
    for w, c, ph, full in entries:
        phlen = len(ph)
        # Last 1 sign varies
        root1 = ph[:-1]
        suffix_groups[(root1, 1, 'suffix')].append((w, c, ph[-1], full, ph))
        # Last 2 signs vary
        if phlen >= 4:
            root2 = ph[:-2]
            suffix_groups[(root2, 2, 'suffix')].append((w, c, ph[-2:], full, ph))

    # ---------------------------------------------------------------
    # Prefix scan: words sharing a suffix (root) with different starts
    # ---------------------------------------------------------------
    prefix_groups = defaultdict(list)
    for w, c, ph, full in entries:
        phlen = len(ph)
        # First 1 sign varies
        root1 = ph[1:]
        prefix_groups[(root1, 1, 'prefix')].append((w, c, ph[0], full, ph))
        # First 2 signs vary
        if phlen >= 4:
            root2 = ph[2:]
            prefix_groups[(root2, 2, 'prefix')].append((w, c, ph[:2], full, ph))

    # ---------------------------------------------------------------
    # Process all groups
    # ---------------------------------------------------------------
    all_groups = list(suffix_groups.items()) + list(prefix_groups.items())

    for (root, alen, atype), members in all_groups:
        alt_seqs = set(m[2] for m in members)
        if len(alt_seqs) < 2:
            continue

        # Build variant info
        variant_info = []
        for m in members:
            w, c, alt_seq, full_s, ph_s = m
            variant_info.append({
                'word': w,
                'alternating_sequence': alt_seq,
                'phonetic_sequence': ph_s,
                'full_signs': full_s,
                'frequency': c,
                'texts': '; '.join(sorted(word_texts.get(w, set()))),
                'num_texts': len(word_texts.get(w, set())),
            })

        total_att = sum(v['frequency'] for v in variant_info)

        all_texts = set()
        for v in variant_info:
            for t in v['texts'].split('; '):
                if t:
                    all_texts.add(t)

        paradigm = {
            'shared_root': root,
            'alternation_type': atype,
            'alternation_length': alen,
            'num_variants': len(variant_info),
            'total_attestations': total_att,
            'alternating_sequences': ', '.join(sorted(alt_seqs)),
            'variants': variant_info,
            'text_contexts': '; '.join(sorted(all_texts)),
            'num_text_contexts': len(all_texts),
        }
        paradigms.append(paradigm)

    # Deduplicate
    seen = set()
    unique = []
    for p in paradigms:
        key = (p['shared_root'], p['alternation_type'], p['alternation_length'])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    # Sort: by total_attestations desc, then by num_variants desc
    unique.sort(key=lambda p: (-p['total_attestations'], -p['num_variants']))
    return unique


# ---------------------------------------------------------------------------
# 4. Agglutination analysis
# ---------------------------------------------------------------------------
def analyze_agglutination(vocab, records):
    """
    Compute word length distribution and recurring building blocks.
    Computes both total-sign and phonetic-only lengths.
    """
    # Length in total signs (syllabograms + logograms)
    len_total_types = Counter()
    len_total_tokens = Counter()
    # Length in phonetic signs only (syllabograms)
    len_phon_types = Counter()
    len_phon_tokens = Counter()

    building_blocks = Counter()
    long_words = []

    for word, freq in vocab.items():
        if not is_valid_word(word):
            continue
        s_total = sign_sequence(word)
        s_phon = phonetic_sequence(word)
        slen_total = len(s_total)
        slen_phon = len(s_phon)

        len_total_types[slen_total] += 1
        len_total_tokens[slen_total] += freq
        len_phon_types[slen_phon] += 1
        len_phon_tokens[slen_phon] += freq

        if slen_total >= 5:
            long_words.append((word, freq, slen_total, slen_phon, s_total, s_phon))

        # Extract recurring substrings of length 2-3 (phonetic only)
        if slen_phon >= 3:
            for i in range(0, slen_phon - 1):
                sub2 = s_phon[i:i+2]
                if len(sub2) == 2:
                    building_blocks[sub2] += freq
            for i in range(0, slen_phon - 2):
                sub3 = s_phon[i:i+3]
                building_blocks[sub3] += freq

    # Compute stats
    total_types_total = sum(len_total_types.values())
    total_tokens_total = sum(len_total_tokens.values())
    total_types_phon = sum(len_phon_types.values())
    total_tokens_phon = sum(len_phon_tokens.values())

    mean_total_type = (sum(s * c for s, c in len_total_types.items()) / total_types_total
                       if total_types_total else 0)
    mean_total_token = (sum(s * c for s, c in len_total_tokens.items()) / total_tokens_total
                        if total_tokens_total else 0)
    mean_phon_type = (sum(s * c for s, c in len_phon_types.items()) / total_types_phon
                      if total_types_phon else 0)
    mean_phon_token = (sum(s * c for s, c in len_phon_tokens.items()) / total_tokens_phon
                       if total_tokens_phon else 0)

    return {
        'len_total_types': len_total_types,
        'len_total_tokens': len_total_tokens,
        'len_phon_types': len_phon_types,
        'len_phon_tokens': len_phon_tokens,
        'total_types_total': total_types_total,
        'total_tokens_total': total_tokens_total,
        'total_types_phon': total_types_phon,
        'total_tokens_phon': total_tokens_phon,
        'mean_total_type': round(mean_total_type, 4),
        'mean_total_token': round(mean_total_token, 4),
        'mean_phon_type': round(mean_phon_type, 4),
        'mean_phon_token': round(mean_phon_token, 4),
        'long_words': sorted(long_words, key=lambda x: -x[1])[:30],
        'building_blocks': building_blocks.most_common(40),
    }


# ---------------------------------------------------------------------------
# 5. Reduplication scan
# ---------------------------------------------------------------------------
def scan_reduplication(vocab):
    """
    Identify potential reduplication patterns in the phonetic sequences.
    """
    redup_patterns = defaultdict(list)

    for word, freq in vocab.items():
        if not is_valid_word(word):
            continue
        s = phonetic_sequence(word)
        slen = len(s)
        if slen < 2:
            continue

        # Pattern 1: First two signs are identical (C1V1-C1V1-...)
        if slen >= 4 and s[0:2] == s[2:4]:
            redup_patterns['initial_disyllabic_redup'].append((word, freq, s))

        # Pattern 2: First sign immediately repeated (C1-C1-...)
        if slen >= 3 and s[0] == s[1]:
            redup_patterns['initial_sign_reduplication'].append((word, freq, s))

        # Pattern 3: Adjacent CV-CV reduplication (a-sa-sa / sa-sa-...)
        if slen >= 4:
            for i in range(0, slen - 2):
                if s[i+1:i+3] == s[i+2:i+4] and len(s[i+1:i+3]) == 2:
                    redup_patterns['adjacent_cv_cv'].append((word, freq, s))
                    break

        # Pattern 4: Internal disyllabic reduplication (non-adjacent)
        if slen >= 5:
            for i in range(slen - 3):
                for j in range(i + 2, slen - 1):
                    if s[i:i+2] == s[j:j+2] and j - i >= 2:
                        redup_patterns['internal_disyllabic_redup'].append(
                            (word, freq, s)
                        )
                        break
                else:
                    continue
                break

        # Pattern 5: First sign repeated later in word
        if slen >= 4:
            first = s[0]
            if first in s[2:]:
                redup_patterns['initial_sign_repeated'].append((word, freq, s))

        # Pattern 6: Chiastic pattern AB...BA
        if slen >= 4:
            if s[:2] == s[-2:][::-1]:
                redup_patterns['chiastic_ab_ba'].append((word, freq, s))

    return redup_patterns


# ---------------------------------------------------------------------------
# 6. Commodity-adjacent text analysis
# ---------------------------------------------------------------------------
def analyze_commodity_context(records):
    pre_modifiers = Counter()
    post_modifiers = Counter()
    logogram_sequences = []

    for rec in records:
        words = rec['words']
        if not words:
            continue
        for i, w in enumerate(words):
            if not any(is_logogram(c) for c in w):
                continue
            # Preceding word
            if i > 0:
                prev = words[i-1]
                if is_valid_word(prev) and not any(is_logogram(c) for c in prev):
                    pre_modifiers[prev] += 1
                    logogram_sequences.append({
                        'text_id': rec['gorila_id'],
                        'logogram': w,
                        'pre_modifier': prev,
                        'post_modifier': '',
                    })
            # Following word
            if i < len(words) - 1:
                nxt = words[i+1]
                if is_valid_word(nxt) and not any(is_logogram(c) for c in nxt):
                    post_modifiers[nxt] += 1
                    logogram_sequences.append({
                        'text_id': rec['gorila_id'],
                        'logogram': w,
                        'pre_modifier': '',
                        'post_modifier': nxt,
                    })

    return {
        'pre_modifiers': pre_modifiers,
        'post_modifiers': post_modifiers,
        'total_pre': sum(pre_modifiers.values()),
        'total_post': sum(post_modifiers.values()),
        'sequences': logogram_sequences,
    }


# ---------------------------------------------------------------------------
# 7. Output
# ---------------------------------------------------------------------------
def write_paradigms_csv(paradigms, path):
    """Write candidate morphological paradigms to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'shared_root', 'alternation_type', 'alternation_length',
            'num_variants', 'total_attestations', 'alternating_sequences',
            'num_text_contexts', 'text_contexts',
            'variant_words', 'variant_frequencies', 'variant_alternating_seqs',
            'variant_phonetic', 'variant_texts'
        ])
        for p in paradigms:
            vwords = '; '.join(v['word'] for v in p['variants'])
            vfreqs = '; '.join(str(v['frequency']) for v in p['variants'])
            valtseq = '; '.join(v['alternating_sequence'] for v in p['variants'])
            vphon = '; '.join(v['phonetic_sequence'] for v in p['variants'])
            vtexts = '; '.join(v['texts'] for v in p['variants'])
            writer.writerow([
                p['shared_root'],
                p['alternation_type'],
                p['alternation_length'],
                p['num_variants'],
                p['total_attestations'],
                p['alternating_sequences'],
                p['num_text_contexts'],
                p['text_contexts'],
                vwords,
                vfreqs,
                valtseq,
                vphon,
                vtexts,
            ])


def write_word_length_csv(stats, path):
    """Write word length distribution to CSV (total signs + phonetic only)."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'word_length', 'measure',
            'num_types', 'num_tokens', 'type_pct', 'token_pct'
        ])
        # Total sign lengths
        for slen in sorted(stats['len_total_types'].keys()):
            types = stats['len_total_types'][slen]
            tokens = stats['len_total_tokens'].get(slen, 0)
            writer.writerow([
                slen, 'total_signs',
                types, tokens,
                round(types / stats['total_types_total'] * 100, 2) if stats['total_types_total'] else 0,
                round(tokens / stats['total_tokens_total'] * 100, 2) if stats['total_tokens_total'] else 0,
            ])
        # Phonetic-only lengths
        for slen in sorted(stats['len_phon_types'].keys()):
            types = stats['len_phon_types'][slen]
            tokens = stats['len_phon_tokens'].get(slen, 0)
            writer.writerow([
                slen, 'phonetic_only',
                types, tokens,
                round(types / stats['total_types_phon'] * 100, 2) if stats['total_types_phon'] else 0,
                round(tokens / stats['total_tokens_phon'] * 100, 2) if stats['total_tokens_phon'] else 0,
            ])


def write_reduplication_csv(redup_patterns, path):
    """Write reduplication inventory to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pattern_type', 'word', 'phonetic_sequence', 'frequency', 'description'])
        desc_map = {
            'initial_disyllabic_redup': 'First 2 signs repeated (C1V1-C1V1-...)',
            'initial_sign_reduplication': 'First sign immediately repeated (C1-C1-...)',
            'adjacent_cv_cv': 'Adjacent CV-CV reduplication (e.g., a-sa-sa)',
            'internal_disyllabic_redup': 'Internal disyllabic reduplication (non-adjacent)',
            'initial_sign_repeated': 'First sign repeated later in word',
            'chiastic_ab_ba': 'Chiastic pattern AB...BA',
        }
        for ptype, items in sorted(redup_patterns.items()):
            for item in items:
                word = item[0]
                freq = item[1]
                seq = item[2]
                desc = desc_map.get(ptype, ptype)
                writer.writerow([ptype, word, seq, freq, desc])


def write_summary_md(records, vocab, paradigms, agglutination,
                     redup_patterns, commodity, path):
    """Write comprehensive morphological summary as Markdown."""
    lines = []
    lines.append("# Morphological Analysis Summary — Linear A Corpus")
    lines.append("")
    lines.append(f"*Generated by `morphology_scan.py`*")
    lines.append("")
    lines.append("## Corpus Overview")
    lines.append("")
    lines.append(f"- Total texts with consensus word boundaries: **{len(records)}**")
    total_tokens = sum(vocab.values())
    lines.append(f"- Total word tokens: **{total_tokens}**")
    lines.append(f"- Unique word types: **{len(vocab)}**")
    lines.append(f"- Type–token ratio: **{len(vocab)/total_tokens:.3f}**")
    lines.append("")

    # ---- Agglutination ----
    lines.append("## Word Length Distribution (Agglutination Analysis)")
    lines.append("")
    lines.append("### Summary Statistics")
    lines.append("")
    lines.append("| Metric | Total Signs | Phonetic Signs Only |")
    lines.append("|--------|-------------|---------------------|")
    lines.append(f"| Mean word length (by type) | {agglutination['mean_total_type']} | {agglutination['mean_phon_type']} |")
    lines.append(f"| Mean word length (by token) | {agglutination['mean_total_token']} | {agglutination['mean_phon_token']} |")
    lines.append("")

    mean_phon = agglutination['mean_phon_token']
    if mean_phon > 3.0:
        agg_inference = (
            "**Agglutinative profile**: Mean phonetic word length >3.0 signs. "
            "This suggests the presence of agglutinative morphology (stacked affixes), "
            "consistent with languages like Turkish, Finnish, or Sumerian.")
    elif mean_phon > 2.0:
        agg_inference = (
            "**Intermediate profile**: Mean phonetic word length between 2–3 signs. "
            "Possible mildly agglutinative language with limited affixation.")
    else:
        agg_inference = (
            "**Isolating profile**: Mean phonetic word length <2.0 signs. "
            "Consistent with an isolating/analytic language where words tend to be "
            "monomorphemic, like Mandarin or Vietnamese.")

    lines.append(f"**Interpretation:** {agg_inference}")
    lines.append("")

    # Detailed table
    lines.append("### Length Distribution (Total Signs)")
    lines.append("")
    lines.append("| Length | Types | Tokens | Type % | Token % |")
    lines.append("|--------|-------|--------|--------|---------|")
    for slen in sorted(agglutination['len_total_types'].keys()):
        types = agglutination['len_total_types'][slen]
        tokens = agglutination['len_total_tokens'].get(slen, 0)
        t_pct = round(types / agglutination['total_types_total'] * 100, 2)
        tok_pct = round(tokens / agglutination['total_tokens_total'] * 100, 2)
        lines.append(f"| {slen} | {types} | {tokens} | {t_pct}% | {tok_pct}% |")
    lines.append("")

    lines.append("### Length Distribution (Phonetic Signs Only)")
    lines.append("")
    lines.append("| Length | Types | Tokens | Type % | Token % |")
    lines.append("|--------|-------|--------|--------|---------|")
    for slen in sorted(agglutination['len_phon_types'].keys()):
        types = agglutination['len_phon_types'][slen]
        tokens = agglutination['len_phon_tokens'].get(slen, 0)
        t_pct = round(types / agglutination['total_types_phon'] * 100, 2)
        tok_pct = round(tokens / agglutination['total_tokens_phon'] * 100, 2)
        lines.append(f"| {slen} | {types} | {tokens} | {t_pct}% | {tok_pct}% |")
    lines.append("")

    # Long words
    if agglutination['long_words']:
        lines.append("### Long Words (≥5 total signs, top 20 by frequency)")
        lines.append("")
        lines.append("| Word | Total Signs | Phon. Signs | Frequency | Phonetic Seq |")
        lines.append("|------|-------------|-------------|-----------|--------------|")
        for word, freq, slen_t, slen_p, seq_t, seq_p in agglutination['long_words'][:20]:
            lines.append(f"| `{word}` | {slen_t} | {slen_p} | {freq} | {seq_p} |")
        lines.append("")

    # Building blocks
    if agglutination['building_blocks']:
        lines.append("### Recurring Building Blocks (phonetic substrings)")
        lines.append("")
        lines.append("| Substring | Frequency |")
        lines.append("|-----------|-----------|")
        for sub, freq in agglutination['building_blocks'][:20]:
            lines.append(f"| `{sub}` | {freq} |")
        lines.append("")

    # ---- Paradigms ----
    lines.append("## Candidate Morphological Paradigms")
    lines.append("")
    lines.append(f"Total candidate paradigms identified: **{len(paradigms)}**")
    lines.append("")

    if paradigms:
        # Split by type
        suffix_pars = [p for p in paradigms if p['alternation_type'] == 'suffix']
        prefix_pars = [p for p in paradigms if p['alternation_type'] == 'prefix']

        lines.append(f"- Suffixation paradigms (words sharing a root, differing in endings): **{len(suffix_pars)}**")
        lines.append(f"- Prefixation paradigms (words sharing a root, differing in starts): **{len(prefix_pars)}**")
        lines.append("")

        # Top suffix paradigms
        if suffix_pars:
            lines.append("### Top Suffixation Paradigms (by attestations)")
            lines.append("")
            lines.append("| # | Root | Variants | Attest. | Alternating Suffixes |")
            lines.append("|---|------|----------|---------|---------------------|")
            for i, p in enumerate(suffix_pars[:20], 1):
                lines.append(f"| {i} | `{p['shared_root']}` | {p['num_variants']} | {p['total_attestations']} | `{p['alternating_sequences']}` |")
            lines.append("")

        # Top prefix paradigms
        if prefix_pars:
            lines.append("### Top Prefixation Paradigms (by attestations)")
            lines.append("")
            lines.append("| # | Root | Variants | Attest. | Alternating Prefixes |")
            lines.append("|---|------|----------|---------|----------------------|")
            for i, p in enumerate(prefix_pars[:20], 1):
                lines.append(f"| {i} | `{p['shared_root']}` | {p['num_variants']} | {p['total_attestations']} | `{p['alternating_sequences']}` |")
            lines.append("")
    else:
        lines.append("*(No clear paradigms identified.)*")
        lines.append("")

    # ---- Reduplication ----
    lines.append("## Reduplication Patterns")
    lines.append("")
    total_redup = sum(len(items) for items in redup_patterns.values())
    lines.append(f"Total reduplication candidates: **{total_redup}**")
    lines.append("")

    for ptype, items in sorted(redup_patterns.items()):
        label = ptype.replace('_', ' ').title()
        lines.append(f"### {label} ({len(items)} instances)")
        lines.append("")
        lines.append("| Word | Phonetic Seq | Frequency |")
        lines.append("|------|--------------|-----------|")
        for item in items[:15]:
            word = item[0]
            freq = item[1]
            seq = item[2]
            lines.append(f"| `{word}` | {seq} | {freq} |")
        if len(items) > 15:
            lines.append(f"| *... and {len(items) - 15} more* | | |")
        lines.append("")

    # ---- Commodity Analysis ----
    lines.append("## Commodity-Adjacent Text Analysis")
    lines.append("")
    lines.append("| Modifier Position | Total Occurrences |")
    lines.append("|-------------------|-------------------|")
    lines.append(f"| Pre-modifier (before logogram) | {commodity['total_pre']} |")
    lines.append(f"| Post-modifier (after logogram) | {commodity['total_post']} |")
    lines.append("")

    total_mod = commodity['total_pre'] + commodity['total_post']
    if total_mod > 0:
        pre_pct = commodity['total_pre'] / total_mod * 100
        lines.append(f"**Word order inference:** {pre_pct:.1f}% of modifiers appear **before** "
                     f"logograms, {100 - pre_pct:.1f}% **after**.")
        if pre_pct > 60:
            lines.append("This **modifier-noun** (head-final) tendency resembles Sumerian and "
                         "Turkish word order.")
        elif pre_pct < 40:
            lines.append("This **noun-modifier** (head-initial) tendency resembles Romance "
                         "languages or Hebrew.")
        else:
            lines.append("No strong word order preference is observed.")
    else:
        lines.append("*(No modifier-logogram adjacency found.)*")
    lines.append("")

    if commodity['pre_modifiers']:
        lines.append("### Top Pre-modifiers (before logograms)")
        lines.append("")
        lines.append("| Word | Frequency |")
        lines.append("|------|-----------|")
        for w, c in commodity['pre_modifiers'].most_common(10):
            lines.append(f"| `{w}` | {c} |")
        lines.append("")

    if commodity['post_modifiers']:
        lines.append("### Top Post-modifiers (after logograms)")
        lines.append("")
        lines.append("| Word | Frequency |")
        lines.append("|------|-----------|")
        for w, c in commodity['post_modifiers'].most_common(10):
            lines.append(f"| `{w}` | {c} |")
        lines.append("")

    # ---- Detailed Paradigm Examples ----
    if paradigms:
        lines.append("## Detailed Paradigm Examples")
        lines.append("")
        for p in paradigms[:15]:
            lines.append(f"### Root `{p['shared_root']}` — {p['alternation_type']} "
                         f"(affix len={p['alternation_length']})")
            lines.append("")
            lines.append(f"- Variants: {p['num_variants']}, Total attestations: {p['total_attestations']}")
            lines.append(f"- Alternating sequences: `{p['alternating_sequences']}`")
            lines.append(f"- Text contexts: {p['num_text_contexts']} texts")
            for v in p['variants']:
                lines.append(f"  - `{v['word']}` (phon: `{v['phonetic_sequence']}`, "
                             f"alt: `{v['alternating_sequence']}`, "
                             f"freq: {v['frequency']}, texts: {v['num_texts']})")
            lines.append("")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Wrote {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Linear A Morphological Scan")
    print("=" * 60)

    print("\n[1] Loading consensus corpus...")
    records = load_consensus_corpus(INPUT_CSV)
    print(f"  Loaded {len(records)} texts with consensus word boundaries.")
    total_tokens = sum(len(r['words']) for r in records)
    print(f"  Total word tokens: {total_tokens}")

    print("\n[2] Building vocabulary...")
    vocab = build_vocab(records)
    print(f"  Unique word types: {len(vocab)}")

    print("\n[3] Scanning for morphological paradigms...")
    paradigms = scan_paradigms(vocab, records)
    print(f"  Found {len(paradigms)} candidate paradigms.")
    suffix_pars = [p for p in paradigms if p['alternation_type'] == 'suffix']
    prefix_pars = [p for p in paradigms if p['alternation_type'] == 'prefix']
    print(f"    Suffixation: {len(suffix_pars)}, Prefixation: {len(prefix_pars)}")
    write_paradigms_csv(paradigms, OUT_PARADIGMS)
    print(f"  Wrote {OUT_PARADIGMS}")

    print("\n[4] Agglutination analysis...")
    agglutination = analyze_agglutination(vocab, records)
    print(f"  Mean total word length (token): {agglutination['mean_total_token']}")
    print(f"  Mean phonetic word length (token): {agglutination['mean_phon_token']}")
    write_word_length_csv(agglutination, OUT_WORD_LEN)
    print(f"  Wrote {OUT_WORD_LEN}")

    print("\n[5] Reduplication scan...")
    redup_patterns = scan_reduplication(vocab)
    total_redup = sum(len(items) for items in redup_patterns.values())
    print(f"  Found {total_redup} reduplication candidates across "
          f"{len(redup_patterns)} pattern types.")
    for ptype, items in sorted(redup_patterns.items()):
        print(f"    {ptype}: {len(items)}")
    write_reduplication_csv(redup_patterns, OUT_REDUP)
    print(f"  Wrote {OUT_REDUP}")

    print("\n[6] Commodity-adjacent text analysis...")
    commodity = analyze_commodity_context(records)
    print(f"  Pre-modifiers: {commodity['total_pre']}")
    print(f"  Post-modifiers: {commodity['total_post']}")

    print("\n[7] Writing summary report...")
    write_summary_md(records, vocab, paradigms, agglutination,
                     redup_patterns, commodity, OUT_SUMMARY)

    print("\n" + "=" * 60)
    print("Done! All outputs written to:")
    print(f"  {OUT_PARADIGMS}")
    print(f"  {OUT_WORD_LEN}")
    print(f"  {OUT_REDUP}")
    print(f"  {OUT_SUMMARY}")
    print("=" * 60)


if __name__ == '__main__':
    main()
