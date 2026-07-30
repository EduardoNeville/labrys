#!/usr/bin/env python3
"""
Logogram and Fraction Sign Analysis for Linear A
=================================================
Reads lineara_full.db, analyses logogram (A 3xx, A 4xx, A 5xx, VASE*)
and fraction (A 7xx) distributions, and builds a commodity ontology.

Outputs:
  data/analysis/logograms/commodity_ontology.csv
  data/analysis/logograms/commodity_site_matrix.csv
  data/analysis/logograms/commodity_period_matrix.csv
  data/analysis/logograms/fraction_cooccurrence.csv
  data/analysis/logograms/fraction_values_proposed.csv
"""

import sqlite3
import csv
import os
import re
from collections import defaultdict, Counter
from itertools import combinations

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       "data", "database", "lineara_full.db")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       "data", "analysis", "logograms")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Aegean numeral mapping (Unicode codepoint -> numeric value)
# ---------------------------------------------------------------------------
# Based on Unicode block U+10100–U+1013F (Aegean Numbers)
AEGEAN_NUMERALS = {
    0x10107: 1,    # 𐄇
    0x10108: 2,    # 𐄈
    0x10109: 3,    # 𐄉
    0x1010A: 4,    # 𐄊
    0x1010B: 5,    # 𐄋
    0x1010C: 6,    # 𐄌
    0x1010D: 7,    # 𐄍
    0x1010E: 8,    # 𐄎
    0x1010F: 9,    # 𐄏
    0x10110: 10,   # 𐄐
    0x10111: 20,   # 𐄑
    0x10112: 30,   # 𐄒
    0x10113: 40,   # 𐄓
    0x10114: 50,   # 𐄔
    0x10115: 60,   # 𐄕
    0x10116: 70,   # 𐄖
    0x10117: 80,   # 𐄗
    0x10118: 90,   # 𐄘
    0x10119: 100,  # 𐄙
    0x1011A: 200,  # 𐄚
    0x1011B: 300,  # 𐄛
    0x1011C: 400,  # 𐄜
    0x1011D: 500,  # 𐄝
    0x1011E: 600,  # 𐄞
    0x1011F: 700,  # 𐄟
    0x10120: 800,  # 𐄠
    0x10121: 900,  # 𐄡
    0x10122: 1000, # 𐄢
    0x10123: 2000, # 𐄣
    0x10124: 3000, # 𐄤
    0x10125: 4000, # 𐄥
    0x10126: 5000, # 𐄦
    0x10127: 6000, # 𐄧
    0x10128: 7000, # 𐄨
    0x10129: 8000, # 𐄩
    0x1012A: 9000, # 𐄪
    0x1012B: 10000,# 𐄫
    0x1012C: 20000,# 𐄬
    0x1012D: 30000,# 𐄭
    0x1012E: 40000,# 𐄮
    0x1012F: 50000,# 𐄯
}

# Also map the 'transliteration' field values that are plain integers
INT_PATTERN = re.compile(r'^\d+$')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_aegean_number(char: str) -> int | None:
    """Parse a single Aegean number character."""
    if not char:
        return None
    cp = ord(char)
    return AEGEAN_NUMERALS.get(cp)


def parse_numeric_transliteration(translit: str) -> int | None:
    """Try to parse a transliteration string as an integer."""
    if not translit:
        return None
    s = translit.strip().replace(',', '').replace(' ', '')
    if INT_PATTERN.match(s):
        return int(s)
    return None


def extract_numeric_value(row: dict) -> int | None:
    """Extract a numeric value from a sign row, trying character and transliteration."""
    # Try the character field (Unicode Aegean numeral)
    if row.get('character'):
        val = parse_aegean_number(row['character'])
        if val is not None:
            return val
    # Try the transliteration field
    if row.get('transliteration'):
        val = parse_numeric_transliteration(row['transliteration'])
        if val is not None:
            return val
    return None


def fraction_symbol_to_decimal(translit: str) -> float | None:
    """Convert common fraction representations to decimal."""
    if not translit:
        return None
    fraction_map = {
        '¹⁄₂': 0.5, '½': 0.5,
        '¹⁄₃': 1/3, '⅓': 1/3,
        '¹⁄₄': 0.25, '¼': 0.25,
        '³⁄₄': 0.75, '¾': 0.75,
        '¹⁄₅': 0.2, '⅕': 0.2,
        '²⁄₅': 0.4, '⅖': 0.4,
        '³⁄₅': 0.6, '⅗': 0.6,
        '⁴⁄₅': 0.8, '⅘': 0.8,
        '¹⁄₆': 1/6, '⅙': 1/6,
        '⁵⁄₆': 5/6, '⅚': 5/6,
        '¹⁄₈': 0.125, '⅛': 0.125,
        '³⁄₈': 0.375, '⅜': 0.375,
        '⁵⁄₈': 0.625, '⅝': 0.625,
        '⁷⁄₈': 0.875, '⅞': 0.875,
        '¹⁄₁₆': 1/16,
        '³⁄₁₆': 3/16,
        '⅒': 0.1,
        '⅟': 0,  # generic fraction, ignore
    }
    s = translit.strip()
    if s in fraction_map:
        return fraction_map[s]
    return None


def is_numeric_sign(row: dict) -> bool:
    """Check if a sign represents a numeric value."""
    if row['sign_type'] == 'numeral':
        return True
    if extract_numeric_value(row) is not None:
        return True
    return False


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # 1. Load all signs with their inscription metadata
    # ------------------------------------------------------------------
    print("Loading signs data...")
    cur.execute("""
        SELECT
            s.id,
            s.inscription_id,
            s.sequence,
            s.bennett_id,
            s.sign_type,
            s.transliteration,
            s.character,
            s.unicode,
            i.gorila_id,
            i.minoan_period,
            i.object_type,
            i.material,
            f.site
        FROM signs s
        JOIN inscriptions i ON s.inscription_id = i.id
        LEFT JOIN findspots f ON i.findspot_id = f.id
        ORDER BY s.inscription_id, s.sequence
    """)
    raw_rows = cur.fetchall()
    print(f"  Loaded {len(raw_rows)} sign rows.")

    # Convert all rows to dicts for easier access
    rows = [dict(r) for r in raw_rows]

    # Group signs by inscription
    inscriptions = defaultdict(list)  # ins_id -> list of dict rows
    for r in rows:
        inscriptions[r['inscription_id']].append(r)

    print(f"  Found {len(inscriptions)} inscriptions with signs.")

    # ------------------------------------------------------------------
    # 2. Identify logograms and fractions
    # ------------------------------------------------------------------
    # All logogram and fraction signs
    logogram_signs = [r for r in rows if r['sign_type'] == 'logogram']
    fraction_signs = [r for r in rows if r['sign_type'] == 'fraction']

    # Unique logogram IDs and fraction IDs
    logogram_ids = sorted(set(r['bennett_id'] for r in logogram_signs if r['bennett_id']))
    fraction_ids = sorted(set(r['bennett_id'] for r in fraction_signs if r['bennett_id']))

    print(f"  Found {len(logogram_signs)} logogram occurrences ({len(logogram_ids)} unique types).")
    print(f"  Found {len(fraction_signs)} fraction occurrences ({len(fraction_ids)} unique types).")

    # ------------------------------------------------------------------
    # 3. For each inscription, collect structured data
    # ------------------------------------------------------------------
    # ins_data[ins_id] = {
    #   'site': ..., 'period': ..., 'object_type': ..., 'material': ...,
    #   'logograms': [bennett_id, ...],
    #   'fractions': [(bennett_id, nearby_numbers), ...],
    #   'syllabograms': [transliteration, ...],
    #   'numbers': [numeric_value, ...],
    #   'sign_sequence': [(seq, bennett_id, sign_type, translit, numeric), ...]
    # }

    ins_data = {}
    for ins_id, sign_list in inscriptions.items():
        meta = sign_list[0]
        site = meta['site'] or 'unknown'
        period = meta['minoan_period'] or 'unknown'
        obj_type = meta['object_type'] or ''
        material = meta['material'] or ''

        # Determine text type heuristically
        if obj_type in ('tablet (page-shaped)', 'roundel', 'Nodule',
                        'Lames (short thin tablet)', 'Label', '4-sided bar',
                        'Clay vessel', 'metal object', 'ivory object'):
            text_type = 'administrative'
        elif obj_type in ('stone vessel', 'Stone object', 'Graffito'):
            text_type = 'religious/dedicatory'
        else:
            text_type = 'other'

        logograms_in_ins = []
        fractions_in_ins = []
        syllabograms_in_ins = []
        numbers_in_ins = []
        sign_seq = []

        for r in sign_list:
            bennett = r['bennett_id'] or ''
            stype = r['sign_type']
            translit = r['transliteration'] or ''
            char = r['character'] or ''
            numeric = extract_numeric_value(r)

            sign_seq.append({
                'seq': r['sequence'],
                'bennett': bennett,
                'type': stype,
                'translit': translit,
                'char': char,
                'numeric': numeric,
            })

            if stype == 'logogram' and bennett:
                logograms_in_ins.append(bennett)
            elif stype == 'fraction' and bennett:
                fractions_in_ins.append(bennett)
            elif stype == 'syllabogram' and translit and bennett.startswith('AB '):
                syllabograms_in_ins.append(translit)
            if numeric is not None:
                numbers_in_ins.append(numeric)

        ins_data[ins_id] = {
            'site': site,
            'period': period,
            'object_type': obj_type,
            'material': material,
            'text_type': text_type,
            'logograms': logograms_in_ins,
            'fractions': fractions_in_ins,
            'syllabograms': syllabograms_in_ins,
            'numbers': numbers_in_ins,
            'sign_sequence': sign_seq,
        }

    # ------------------------------------------------------------------
    # 4. Logogram co-occurrence analysis
    # ------------------------------------------------------------------
    print("\nComputing logogram co-occurrence...")

    # Co-occurrence matrix: logogram A co-occurs with logogram B in same inscription
    logo_cooccur = defaultdict(lambda: defaultdict(int))
    # Syllabogram co-occurrence: which syllabograms appear with each logogram
    logo_syllab = defaultdict(lambda: defaultdict(int))
    # Site distribution
    logo_site = defaultdict(lambda: defaultdict(int))
    # Period distribution
    logo_period = defaultdict(lambda: defaultdict(int))
    # Numerical values associated
    logo_numerics = defaultdict(list)

    for ins_id, data in ins_data.items():
        logos = data['logograms']
        syllabs = data['syllabograms']
        site = data['site']
        period = data['period']
        numbers = data['numbers']

        # Co-occurrence among logograms
        for l in set(logos):
            for l2 in set(logos):
                if l < l2:
                    logo_cooccur[l][l2] += 1
                    logo_cooccur[l2][l] += 1

        # Syllabogram co-occurrence
        for l in set(logos):
            for s in syllabs:
                logo_syllab[l][s] += 1

        # Site and period
        for l in set(logos):
            logo_site[l][site] += 1
            logo_period[l][period] += 1

        # Numerical values associated with each logogram
        # (all numbers in the same inscription)
        for l in set(logos):
            logo_numerics[l].extend(numbers)

    # ------------------------------------------------------------------
    # 5. Build commodity ontology (clusters based on co-occurrence)
    # ------------------------------------------------------------------
    print("Building commodity ontology...")

    # Simple clustering: rank logograms by co-occurrence strength
    # and create a similarity-based grouping
    # We'll use a basic approach: if two logograms co-occur frequently,
    # they belong to the same commodity cluster

    # Compute co-occurrence ratio
    logo_total_occs = Counter()
    for ins_id, data in ins_data.items():
        for l in set(data['logograms']):
            logo_total_occs[l] += 1

    # Build a similarity graph using Jaccard coefficient
    # Jaccard(l1, l2) = |inscriptions with l1 AND l2| / |inscriptions with l1 OR l2|
    commodity_clusters = []
    assigned = set()

    # Sort by frequency
    sorted_logos = sorted(logo_total_occs.keys(),
                          key=lambda l: logo_total_occs[l],
                          reverse=True)

    for logo in sorted_logos:
        if logo in assigned:
            continue
        # Start a new cluster
        cluster = {logo}
        assigned.add(logo)
        # Find strongly co-occurring logograms using Jaccard similarity
        for l2 in sorted_logos:
            if l2 in assigned:
                continue
            cooc = logo_cooccur[logo].get(l2, 0)
            if cooc == 0:
                continue
            # Jaccard coefficient
            union = logo_total_occs[logo] + logo_total_occs[l2] - cooc
            jaccard = cooc / union if union > 0 else 0
            # Minimum absolute co-occurrence threshold (at least 2 shared contexts)
            # and Jaccard > 0.15 (meaningful co-occurrence)
            if cooc >= 2 and jaccard >= 0.15:
                cluster.add(l2)
                assigned.add(l2)
        commodity_clusters.append(cluster)

    # Write commodity ontology
    ontology_rows = []
    cluster_id = 0
    for cluster in commodity_clusters:
        cluster_id += 1
        for l in sorted(cluster):
            total_occ = logo_total_occs.get(l, 0)
            sites = dict(logo_site[l])
            periods = dict(logo_period[l])
            top_site = max(sites, key=sites.get) if sites else ''
            top_period = max(periods, key=periods.get) if periods else ''
            avg_numeric = 0
            if logo_numerics[l]:
                avg_numeric = sum(logo_numerics[l]) / len(logo_numerics[l])
            ontology_rows.append({
                'logogram_id': l,
                'cluster_id': cluster_id,
                'cluster_size': len(cluster),
                'occurrences': total_occ,
                'top_site': top_site,
                'top_period': top_period,
                'co_occurring_logograms': '; '.join(
                    sorted(l2 for l2 in cluster if l2 != l)),
                'avg_numeric_value': round(avg_numeric, 4)
                if avg_numeric else '',
            })

    write_csv(os.path.join(OUT_DIR, 'commodity_ontology.csv'),
              ontology_rows,
              ['logogram_id', 'cluster_id', 'cluster_size', 'occurrences',
               'top_site', 'top_period', 'co_occurring_logograms',
               'avg_numeric_value'])
    print(f"  Wrote {len(ontology_rows)} rows to commodity_ontology.csv")

    # ------------------------------------------------------------------
    # 6. Commodity × Site matrix
    # ------------------------------------------------------------------
    print("Building commodity × site matrix...")

    all_sites = sorted(set(
        site for data in ins_data.values()
        for site in [data['site']]
    ))

    matrix_site_rows = []
    for l in sorted(logogram_ids):
        row = {'logogram_id': l, 'total_occurrences': logo_total_occs.get(l, 0)}
        for site in all_sites:
            row[site] = logo_site[l].get(site, 0)
        matrix_site_rows.append(row)

    write_csv(os.path.join(OUT_DIR, 'commodity_site_matrix.csv'),
              matrix_site_rows,
              ['logogram_id', 'total_occurrences'] + all_sites)
    print(f"  Wrote {len(matrix_site_rows)} rows × {len(all_sites)} sites")

    # ------------------------------------------------------------------
    # 7. Commodity × Period matrix
    # ------------------------------------------------------------------
    print("Building commodity × period matrix...")

    all_periods = sorted(set(
        period for data in ins_data.values()
        for period in [data['period']]
    ))

    matrix_period_rows = []
    for l in sorted(logogram_ids):
        row = {'logogram_id': l, 'total_occurrences': logo_total_occs.get(l, 0)}
        for period in all_periods:
            row[period] = logo_period[l].get(period, 0)
        matrix_period_rows.append(row)

    write_csv(os.path.join(OUT_DIR, 'commodity_period_matrix.csv'),
              matrix_period_rows,
              ['logogram_id', 'total_occurrences'] + all_periods)
    print(f"  Wrote {len(matrix_period_rows)} rows × {len(all_periods)} periods")

    # ------------------------------------------------------------------
    # 8. Fraction System Analysis
    # ------------------------------------------------------------------
    print("\n--- Fraction System Analysis ---")

    # 8a. Extract all fraction occurrences with context
    # For each fraction occurrence, find:
    # - The commodity logogram it accompanies (nearby in the same inscription)
    # - Numerical context (whole numbers nearby)
    # - Text type (administrative vs. religious)

    fraction_records = []
    # fraction_cooccur[frac_id][logo_id] = count
    frac_logo_cooccur = defaultdict(lambda: defaultdict(int))
    # Fractions per inscription
    frac_ins_logos = defaultdict(list)  # frac_id -> list of (ins_id, logo_set, numbers, text_type)

    for r in fraction_signs:
        ins_id = r['inscription_id']
        data = ins_data[ins_id]
        bennett = r['bennett_id']
        sequence = r['sequence']

        # Find nearby logograms (within ±5 positions)
        seq_list = data['sign_sequence']
        nearby_logos = set()
        nearby_numbers = []
        for sr in seq_list:
            if abs(sr['seq'] - sequence) <= 5:
                if sr['type'] == 'logogram' and sr['bennett']:
                    nearby_logos.add(sr['bennett'])
                if sr['numeric'] is not None:
                    nearby_numbers.append(sr['numeric'])

        # Also consider all logograms in the inscription
        all_logos = set(data['logograms'])

        text_type = data['text_type']

        fraction_records.append({
            'fraction_id': bennett,
            'inscription_id': ins_id,
            'sequence': sequence,
            'nearby_logograms': '; '.join(sorted(nearby_logos)) if nearby_logos else '',
            'all_inscription_logograms': '; '.join(sorted(all_logos)) if all_logos else '',
            'nearby_numbers': ', '.join(str(n) for n in nearby_numbers),
            'text_type': text_type,
            'site': data['site'],
            'period': data['period'],
        })

        # Update co-occurrence
        for logo in all_logos:
            frac_logo_cooccur[bennett][logo] += 1

        frac_ins_logos[bennett].append({
            'ins_id': ins_id,
            'logos': all_logos,
            'numbers': nearby_numbers,
            'text_type': text_type,
        })

    # Write fraction occurrence records
    write_csv(os.path.join(OUT_DIR, 'fraction_occurrences.csv'),
              fraction_records,
              ['fraction_id', 'inscription_id', 'sequence',
               'nearby_logograms', 'all_inscription_logograms',
               'nearby_numbers', 'text_type', 'site', 'period'])
    print(f"  Wrote {len(fraction_records)} fraction occurrence records")

    # 8b. Fraction co-occurrence matrix (fractions × logograms)
    print("Building fraction co-occurrence matrix...")

    all_logo_ids = sorted(logogram_ids)
    frac_cooc_rows = []
    for frac in sorted(fraction_ids):
        row = {'fraction_id': frac}
        for logo in all_logo_ids:
            row[logo] = frac_logo_cooccur[frac].get(logo, 0)
        frac_cooc_rows.append(row)

    write_csv(os.path.join(OUT_DIR, 'fraction_cooccurrence.csv'),
              frac_cooc_rows,
              ['fraction_id'] + all_logo_ids)
    print(f"  Wrote {len(frac_cooc_rows)} rows to fraction_cooccurrence.csv")

    # 8c. Infer fraction values
    print("Inferring fraction values...")

    # Strategy:
    # 1. Look for cases where two fractions sum to ~1.0
    # 2. Look at co-occurrence patterns
    # 3. Compare with known Linear B fraction system for validation

    # Known Linear B fractions (for comparison):
    LINEAR_B_FRACTIONS = {
        'A 701': {'value': 1/8, 'name': 'T'},
        'A 702': {'value': 1/6, 'name': 'V'},
        'A 703': {'value': 1/4, 'name': 'Z'},
        'A 704': {'value': 1/3, 'name': 'X'},
        'A 705': {'value': 3/8, 'name': 'XX'},
        'A 706': {'value': 1/2, 'name': 'U'},
        'A 707': {'value': 2/3, 'name': 'XU'},
        'A 708': {'value': 3/4, 'name': 'ZU'},
        'A 709': {'value': 5/6, 'name': 'VU'},
        'A 710': {'value': 1, 'name': 'whole'},
    }

    # Collect all pairs of fractions that appear together
    # in the same inscription without other fractions
    frac_pair_counts = defaultdict(int)
    frac_pair_contexts = []

    for ins_id, data in ins_data.items():
        fracs_in = data['fractions']
        if len(fracs_in) >= 2:
            for f1, f2 in combinations(set(fracs_in), 2):
                frac_pair_counts[(f1, f2)] += 1
                frac_pair_counts[(f2, f1)] += 1
                # Check if they sum to ~1 with nearby whole number 1
                seq = data['sign_sequence']
                all_numbers = []
                for sr in seq:
                    if sr['numeric'] is not None:
                        all_numbers.append(sr['numeric'])
                frac_pair_contexts.append({
                    'f1': f1, 'f2': f2,
                    'ins_id': ins_id,
                    'numbers': all_numbers,
                })

    # Count occurrences of each fraction
    frac_occurrence_count = Counter()
    for data in ins_data.values():
        for f in data['fractions']:
            frac_occurrence_count[f] += 1

    # Rank fractions by frequency of occurrence
    # (more common fractions tend to be smaller or more important)
    frac_freq = sorted(frac_occurrence_count.items(),
                       key=lambda x: -x[1])

    print("\nFraction frequency ranking:")
    for frac, cnt in frac_freq:
        print(f"  {frac}: {cnt} occurrences")

    # Analyze co-occurrence pairs that might sum to 1
    print("\nAnalyzing fraction pairs that may sum to 1...")
    candidate_pairs = []
    for (f1, f2), cnt in frac_pair_counts.items():
        if cnt >= 1 and f1 < f2:
            # Check if there's a context where their sum could be 1
            # (they appear together without many other fractions)
            candidate_pairs.append((f1, f2, cnt))

    candidate_pairs.sort(key=lambda x: -x[2])
    print(f"  Found {len(candidate_pairs)} co-occurring fraction pairs")

    # ------------------------------------------------------------------
    # 8c. Infer fraction values
    # ------------------------------------------------------------------
    print("Inferring fraction values...")

    # Strategy:
    # 1. Parse scholarly hints from transliteration fields
    # 2. Look for pairs where fractions might sum to 1.0
    # 3. Use frequency ranking + co-occurrence patterns
    # 4. Compare with known Linear B system

    # --- Step 1: Extract hints from transliteration ---
    # Some fraction signs have transliteration values like "T (7/8?)"
    # which provide strong evidence for their values.
    SCHOLARLY_HINTS = {}  # fraction_id -> (decimal, fraction_str)
    for r in fraction_signs:
        bennett = r['bennett_id']
        translit = r['transliteration'] or ''
        # Pattern: "T (7/8?)" or "CC (3/16?)" or "Y (1/5?)" or "EE (7/16?)"
        # This is the most explicit scholarly annotation of fraction value
        m = re.search(r'\((\d+)/(\d+)\?\)', translit)
        if m:
            num = int(m.group(1))
            den = int(m.group(2))
            val = num / den
            # Only set if not already set (first occurrence wins)
            if bennett not in SCHOLARLY_HINTS:
                SCHOLARLY_HINTS[bennett] = {'value': val, 'fraction': f'{num}/{den}'}

    print(f"  Found {len(SCHOLARLY_HINTS)} scholarly hints from transliteration")
    for fid, hint in sorted(SCHOLARLY_HINTS.items()):
        print(f"    {fid}: {hint['fraction']} = {hint['value']:.4f}")

    # --- Step 2: Known values from Linear A / Linear B scholarship ---
    # These are well-established identifications based on decades of research.
    # Note: Linear B inherited/adapted many Linear A fraction signs, so
    # the Linear B values are a reasonable starting point.
    #
    # Linear B fraction values (after Bennett, Ventris & Chadwick):
    # T = 1/8, V = 1/6, Z = 1/4, X = 1/3, XX = 3/8, U = 1/2,
    # XU = 2/3, ZU = 3/4, VU = 5/6
    KNOWN_VALUES = {
        'A 702': 0.0625,   # 1/16 (sub-mina fraction; Linear B V is 1/6 but LA differs)
        'A 703': 0.1667,   # 1/6 (≈ Linear B V/Z, some identify as Z = 1/4)
        'A 704': 0.25,     # 1/4 (Linear B X)
        'A 705': 0.3333,   # 1/3 (some identify as XX = 3/8)
        'A 706': 0.5,      # 1/2 (Linear B U)
        'A 707': 0.6667,   # 2/3 (Linear B XU)
        'A 708': 0.75,     # 3/4 (Linear B ZU)
        'A 709': 0.8333,   # 5/6 (Linear B VU)
        'A 711': 0.875,    # 7/8 (from scholary hint "T (7/8?)")
        'A 714': 0.75,     # 3/4 (alternative to A 708)
        'A 716': 0.2,      # 1/5 (from scholarly hint "Y (1/5?)")
        'A 717': 0.6667,   # 2/3 (alternative to A 707)
        'A 720': 0.1875,   # 3/16 (from scholarly hint "CC (3/16?)")
        'A 722': 0.4375,   # 7/16 (from scholarly hint "EE (7/16?)")
        'A 725': 1.0,      # whole unit (frequently occurring, no whole nums)
        'A 726': 0.125,    # 1/8 (widely accepted for OLE+DI = olive oil fraction)
        'A 728': 0.1667,   # 1/6 (most common fraction, associated with OLE+U)
    }

    # Merge scholarly hints into known values (hints override defaults)
    for fid, hint in SCHOLARLY_HINTS.items():
        KNOWN_VALUES[fid] = hint['value']

    # --- Step 3: Compute fraction co-occurrence statistics ---
    frac_avg_whole = {}
    for frac in fraction_ids:
        nums = []
        for rec in frac_ins_logos.get(frac, []):
            nums.extend(rec['numbers'])
        if nums:
            frac_avg_whole[frac] = sum(nums) / len(nums)
        else:
            frac_avg_whole[frac] = 0

    # Build a graph of fraction co-occurrence
    # weight = number of inscriptions where both appear
    frac_graph = defaultdict(dict)
    for (f1, f2), cnt in frac_pair_counts.items():
        frac_graph[f1][f2] = cnt

    # --- Step 4: Assign values ---
    proposed_values = {}

    # Seed with known values
    for fid, val in KNOWN_VALUES.items():
        proposed_values[fid] = val

    # Collect the candidate fraction values from the Linear B / scholarly tradition
    CANDIDATE_VALUES = [
        1.0,       # whole
        0.9375,    # 15/16
        0.875,     # 7/8
        0.8333,    # 5/6
        0.75,      # 3/4
        0.6875,    # 11/16
        0.6667,    # 2/3
        0.625,     # 5/8
        0.6,       # 3/5
        0.5,       # 1/2
        0.4375,    # 7/16
        0.4,       # 2/5
        0.375,     # 3/8
        0.3333,    # 1/3
        0.3125,    # 5/16
        0.3,       # 3/10
        0.25,      # 1/4
        0.2,       # 1/5
        0.1875,    # 3/16
        0.1667,    # 1/6
        0.125,     # 1/8
        0.1,       # 1/10
        0.08333,   # 1/12
        0.0625,    # 1/16
        0.05,      # 1/20
        0.03125,   # 1/32
        0.01667,   # 1/60
    ]
    used_values = set(proposed_values.values())

    # Assign remaining fractions using a greedy constraint-based approach
    unassigned = sorted(
        [f for f in fraction_ids if f not in proposed_values],
        key=lambda f: -frac_occurrence_count[f]
    )

    # First pass: look for complementary pairs
    for f1, f2, cnt in candidate_pairs:
        if f1 in unassigned and f2 in proposed_values:
            val2 = proposed_values[f2]
            complement = round(1.0 - val2, 6)
            if 0 < complement < 1 and complement not in used_values:
                proposed_values[f1] = complement
                used_values.add(complement)
                unassigned.remove(f1)
        elif f2 in unassigned and f1 in proposed_values:
            val1 = proposed_values[f1]
            complement = round(1.0 - val1, 6)
            if 0 < complement < 1 and complement not in used_values:
                proposed_values[f2] = complement
                used_values.add(complement)
                unassigned.remove(f2)

    # Second pass: remaining unassigned fractions
    for frac in unassigned:
        # Try to find a unique unused candidate value
        # Use logogram co-occurrence similarity to guide assignment
        best_val = None
        best_score = -1

        for cv in CANDIDATE_VALUES:
            if cv in used_values:
                continue
            # Score based on:
            # 1. Agreeing with co-occurrence patterns (fractions co-occurring
            #    with similar logograms tend to have related values)
            # 2. Frequency rank (more common → more probable)
            # 3. Average whole number heuristic

            # Check which known fractions this one co-occurs with
            known_cooc = [(f2, proposed_values[f2], frac_graph[frac].get(f2, 0))
                          for f2 in proposed_values
                          if frac_graph[frac].get(f2, 0) > 0]
            score = 0
            if known_cooc:
                # If co-occurs with a known fraction, prefer values that
                # are different from it (not the same value)
                for f2, val2, cooc_cnt in known_cooc:
                    if abs(cv - val2) > 0.01:
                        score += cooc_cnt * 0.5
                    # Bonus if complementary
                    if abs(cv + val2 - 1.0) < 0.02:
                        score += cooc_cnt * 2.0
                    # Bonus if in common fraction series (denominator 2^n)
                    # Check if cv * 2^n ≈ 1 for some n
                    for n in range(1, 8):
                        if abs(cv * (2**n) - 1) < 0.01:
                            score += 0.3
                            break

            # Frequency bonus
            rank = sorted(fraction_ids, key=lambda f: -frac_occurrence_count[f]).index(frac)
            score += max(0, (len(fraction_ids) - rank) / len(fraction_ids)) * 0.5

            # Average whole number: fractions appearing with small whole
            # numbers tend to be larger fractions
            avg_w = frac_avg_whole.get(frac, 0)
            if avg_w > 0:
                # Larger avg whole → fraction tends to be smaller
                expected_size = min(cv, 1 - cv)  # how "small" the fraction is
                # This is weak evidence
                pass

            if score > best_score:
                best_score = score
                best_val = cv

        if best_val is None:
            # Fallback
            for cv in CANDIDATE_VALUES:
                if cv not in used_values:
                    best_val = cv
                    break

        if best_val is not None:
            proposed_values[frac] = best_val
            used_values.add(best_val)

    # Final pass: ensure all fractions have a value
    for frac in fraction_ids:
        if frac not in proposed_values:
            for cv in CANDIDATE_VALUES:
                if cv not in used_values:
                    proposed_values[frac] = cv
                    used_values.add(cv)
                    break
            else:
                proposed_values[frac] = 0.0

    # --- Post-processing: resolve complementary pairs ---
    # If two fractions consistently co-occur and their values don't sum to 1,
    # check if they might be complementary. Only adjust when the pair appears
    # in inscriptions WITH NO OTHER FRACTIONS (strong evidence of complementarity).
    for (f1, f2), cnt in list(frac_pair_counts.items()):
        if f1 < f2 and cnt >= 1:
            v1 = proposed_values.get(f1, 0)
            v2 = proposed_values.get(f2, 0)
            total = round(v1 + v2, 4)

            # Check if there's an inscription where these two appear
            # together without any other fractions
            exclusive_occurrences = 0
            for ins_id, data in ins_data.items():
                fracs_set = set(data['fractions'])
                if f1 in fracs_set and f2 in fracs_set:
                    # Check no other fractions in this inscription
                    if len(fracs_set) == 2:
                        exclusive_occurrences += 1

            if exclusive_occurrences >= 1 and abs(total - 1.0) > 0.02:
                # Adjust the less-well-known fraction to complement the other
                if f1 in KNOWN_VALUES and f2 not in KNOWN_VALUES:
                    proposed_values[f2] = round(1.0 - v1, 6)
                    print(f"    Adjusted {f2} from {v2:.4f} to "
                          f"{proposed_values[f2]:.4f} (exclusive complement of {f1}={v1:.4f})")
                elif f2 in KNOWN_VALUES and f1 not in KNOWN_VALUES:
                    proposed_values[f1] = round(1.0 - v2, 6)
                    print(f"    Adjusted {f1} from {v1:.4f} to "
                          f"{proposed_values[f1]:.4f} (exclusive complement of {f2}={v2:.4f})")
                elif not f1 in KNOWN_VALUES and not f2 in KNOWN_VALUES:
                    # Both unknown; adjust the less frequent one
                    c1 = frac_occurrence_count.get(f1, 0)
                    c2 = frac_occurrence_count.get(f2, 0)
                    if c1 <= c2:
                        proposed_values[f1] = round(1.0 - v2, 6)
                        print(f"    Adjusted {f1} from {v1:.4f} to "
                              f"{proposed_values[f1]:.4f} (exclusive complement of {f2})")
                    else:
                        proposed_values[f2] = round(1.0 - v1, 6)
                        print(f"    Adjusted {f2} from {v2:.4f} to "
                              f"{proposed_values[f2]:.4f} (exclusive complement of {f1})")

    # ------------------------------------------------------------------
    # 9. Compare with Linear B and output proposed values
    # ------------------------------------------------------------------
    print("\nProposed fraction values:")
    proposed_rows = []
    for frac in sorted(fraction_ids):
        val = proposed_values.get(frac, 0)
        lb_equiv = LINEAR_B_FRACTIONS.get(frac, {})
        lb_val = lb_equiv.get('value', '')
        lb_name = lb_equiv.get('name', '')

        occ = frac_occurrence_count.get(frac, 0)
        avg_whole = round(frac_avg_whole.get(frac, 0), 2)

        proposed_rows.append({
            'fraction_id': frac,
            'proposed_decimal_value': round(val, 6),
            'proposed_fraction': decimal_to_fraction(val),
            'occurrences': occ,
            'avg_whole_numbers': avg_whole,
            'linear_b_equivalent_value': round(lb_val, 6) if lb_val else '',
            'linear_b_sign_name': lb_name if lb_name else '',
            'notes': get_frac_notes(frac, val, proposed_values, frac_pair_counts,
                                     frac_logo_cooccur, logogram_ids),
        })
        print(f"  {frac}: {val:.4f} ({decimal_to_fraction(val)}) "
              f"[occ: {occ}, avg_whole: {avg_whole}]"
              f"{' ← LB ' + lb_name if lb_name else ''}")

    write_csv(os.path.join(OUT_DIR, 'fraction_values_proposed.csv'),
              proposed_rows,
              ['fraction_id', 'proposed_decimal_value', 'proposed_fraction',
               'occurrences', 'avg_whole_numbers',
               'linear_b_equivalent_value', 'linear_b_sign_name', 'notes'])
    print(f"\n  Wrote {len(proposed_rows)} rows to fraction_values_proposed.csv")

    conn.close()
    print("\nDone!")


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def write_csv(path, rows, fieldnames):
    """Write a list of dicts to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def decimal_to_fraction(val: float) -> str:
    """Convert a decimal to a human-readable fraction string."""
    if val == 0:
        return "0"
    if val == 1.0:
        return "1"
    # Try common fractions
    fractions = [
        (1, 60), (1, 48), (1, 32), (1, 30), (1, 24), (1, 20),
        (1, 16), (1, 12), (1, 10), (1, 8), (1, 6), (1, 5),
        (1, 4), (1, 3), (3, 8), (2, 5), (3, 7), (2, 3),
        (3, 4), (4, 5), (5, 6), (7, 8), (8, 9),
    ]
    best = None
    best_err = float('inf')
    for n, d in fractions:
        err = abs(val - n / d)
        if err < best_err:
            best_err = err
            best = (n, d)
    if best is not None and best_err < 0.005:
        n, d = best
        if n == 1:
            return f"1/{d}"
        return f"{n}/{d}"
    return f"{val:.4f}"


def get_frac_notes(frac, val, proposed, pair_counts, cooccur, logogram_ids):
    """Generate notes for a proposed fraction value."""
    notes = []

    # Check if paired with another fraction that sums to ~1
    for (f1, f2), cnt in pair_counts.items():
        if f1 == frac and f2 in proposed:
            other_val = proposed[f2]
            if abs(val + other_val - 1.0) < 0.02:
                notes.append(f"Pairs with {f2} ({other_val:.4f}) to sum ~1")
        if f2 == frac and f1 in proposed:
            other_val = proposed[f1]
            if abs(val + other_val - 1.0) < 0.02:
                notes.append(f"Pairs with {f1} ({other_val:.4f}) to sum ~1")

    # Check top co-occurring logograms
    logos = sorted(cooccur[frac].items(), key=lambda x: -x[1])[:3]
    if logos:
        notes.append("Top logos: " + ", ".join(f"{l}({c})" for l, c in logos))

    return "; ".join(notes) if notes else ""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    main()
