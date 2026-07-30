#!/usr/bin/env python3
"""
Ingest lineara.xyz inscriptions.json + supplement.json into the Labrys pipeline.
Handles the list-of-[id, data] format and merges supplement data.
"""
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.models import (
    Inscription, Findspot, SignInstance, DateInfo, Dimensions,
    ImageResource, SignSemantics,
)
from pipeline.database import LinearADatabase
from pipeline.unicode_utils import validate_mapping, lookup_sign

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Known site → period mapping (from SigLA/lineara.xyz context field)
PERIOD_MAP = {
    "LMIB": "LM IB",
    "LMIA": "LM IA",
    "LMII": "LM II",
    "LMIII": "LM III",
    "MMII": "MM II",
    "MMIII": "MM III",
    "MMIII/LMIA": "MM III/LM IA",
    "MMIII-LMIA": "MM III/LM IA",
    "": "Uncertain",
}

# Support/object-type mapping
SUPPORT_MAP = {
    "Tablet": "tablet (page-shaped)",
    "Tablet (page-shaped)": "tablet (page-shaped)",
    "Tablet (palm-leaf)": "tablet (palm-leaf)",
    "Tablet (long-and-thin)": "tablet (long-and-thin)",
    "Roundel": "roundel",
    "Libation table": "libation table",
    "Sealing": "sealing",
    "Seal": "seal",
    "Pottery": "pottery vessel",
    "Fresco": "fresco",
    "Metal object": "metal object",
    "Bone label": "bone label",
    "Ivory plaque": "ivory plaque",
    "Stone vessel": "stone vessel",
    "Vase": "pottery vessel",
    "Pin": "metal object",
    "Weight": "metal object",
}


def guess_material_from_support(support: str) -> Optional[str]:
    """Guess material from object type."""
    if not support:
        return None
    s = support.lower()
    if "tablet" in s or "roundel" in s or "sealing" in s:
        return "clay"
    if "stone" in s or "libation" in s:
        return "stone"
    if "metal" in s:
        return "metal"
    if "bone" in s:
        return "bone"
    if "ivory" in s:
        return "ivory"
    if "fresco" in s:
        return "fresco/plaster"
    if "pottery" in s or "vase" in s or "vessel" in s:
        return "pottery/ceramic"
    return None


def parse_words_to_signs(words_list, translit_words=None):
    """
    Convert the 'words' list (Unicode strings) and optional
    'transliteratedWords' into SignInstance objects.
    Each word is a string of characters; word dividers are separate entries.
    """
    signs = []
    seq = 0
    word_boundaries = []
    current_word_start = 0
    word_idx = 0

    if translit_words is None:
        translit_words = []

    # Build a per-character transliteration map from transliteratedWords
    # transliteratedWords is a list like ["QE-RA₂-U", "|", "\n", "KI-RO", ...]
    char_translit = {}  # index in words flat list -> transliteration
    char_idx_flat = 0
    for tw in translit_words:
        if tw in ("|", "\n", ""):
            # These are separators/dividers
            char_translit[char_idx_flat] = tw if tw in ("|", "\n") else None
            char_idx_flat += 1
            continue
        # Split transliteration by space or hyphen
        parts = re.split(r'[-\s]+', tw)
        for p in parts:
            char_translit[char_idx_flat] = p
            char_idx_flat += 1

    current_word = []
    flat_idx = 0

    for word_str in words_list:
        if word_str in ("|", "\n"):
            # Word divider
            if word_str == "|":
                signs.append(SignInstance(
                    sequence=seq,
                    bennettId="WORD_DIV",
                    signType="word divider",
                    character=word_str,
                    transliteration="|",
                ))
                seq += 1
            # \n indicates line break — skip
            if current_word and len(current_word) > 0:
                word_boundaries.append(current_word.copy())
                current_word = []
            flat_idx += 1
            continue

        # Process each character in the word
        for ch in word_str:
            # Look up the character in unicode mapping
            lookup = lookup_sign(unicode_ref=ch) or {}
            bennett_id = lookup.get("bennettId", "")
            translit = char_translit.get(flat_idx, lookup.get("transliteration", ch))
            
            signs.append(SignInstance(
                sequence=seq,
                bennettId=bennett_id,
                unicode=lookup.get("unicode"),
                character=ch,
                transliteration=translit,
                signType=lookup.get("signType", "syllabogram"),
            ))
            current_word.append(seq)
            seq += 1
            flat_idx += 1

        # End of word
        if current_word:
            word_boundaries.append(current_word.copy())
            current_word = []

    return signs, word_boundaries


def parse_lineara_inscription(entry_id: str, entry_data: dict, supplement: dict) -> Optional[Inscription]:
    """
    Convert a lineara.xyz inscription entry (from the list-of-pairs) to an Inscription.
    Merges supplement data if available.
    """
    try:
        name = entry_data.get("name", entry_id)
        # Merge supplement
        supp = supplement.get(name, {})

        # --- Findspot / Site ---
        site = entry_data.get("site", "")
        findspot_str = entry_data.get("findspot", "")
        # Combine site and findspot
        full_site = site
        if findspot_str and findspot_str != site:
            full_site = f"{site} - {findspot_str}" if site else findspot_str

        findspot = Findspot(site=full_site or site or "Unknown") if (site or findspot_str) else None

        # --- Date / Period ---
        context = entry_data.get("context", "")
        period = PERIOD_MAP.get(context, context if context else "Uncertain")
        date_info = DateInfo(minoanPeriod=period)

        # --- Material & Object Type ---
        support = entry_data.get("support", "")
        object_type = SUPPORT_MAP.get(support, support or None)
        material = guess_material_from_support(support)

        # --- Dimensions (from supplement) ---
        dims = None
        dim_raw = supp.get("dimensions", {}) or {}
        if isinstance(dim_raw, dict) and dim_raw:
            def _clean_dim(val):
                if not val:
                    return None
                s = str(val).strip()
                s = re.sub(r'[\[\]()<>+]', '', s)
                s = re.sub(r'(\d+\.)\s+(\d)', r'\1\2', s)
                m = re.match(r'(-?\d+\.?\d*)', s)
                if m:
                    return float(m.group(1))
                try:
                    return float(s)
                except ValueError:
                    return None
            h = _clean_dim(dim_raw.get("height"))
            l = _clean_dim(dim_raw.get("length"))
            w = _clean_dim(dim_raw.get("width"))
            t = _clean_dim(dim_raw.get("thickness"))
            dims = Dimensions(
                height=h,
                width=l or w,
                depth=t,
                unit="mm" if "mm" in dim_raw.get("unit", "").lower() else "cm",
            )

        # --- Images ---
        images = []
        for img_url in entry_data.get("images", []):
            images.append(ImageResource(
                iiifServiceUrl=img_url,
                credit=entry_data.get("imageRights", ""),
                license=entry_data.get("imageRightsURL", ""),
            ))

        # --- Signs from words/transliteratedWords ---
        words = entry_data.get("words", [])
        translit_words = entry_data.get("transliteratedWords", [])
        signs, word_boundaries = parse_words_to_signs(words, translit_words)

        # --- Create Inscription ---
        alt_ids = entry_data.get("names", [])
        if name in alt_ids:
            alt_ids.remove(name)

        inscription = Inscription(
            gorilaId=name,
            alternativeIds=alt_ids,
            findspot=findspot,
            date=date_info,
            material=material,
            objectType=object_type,
            dimensions=dims,
            signs=signs,
            images=images,
            source="lineara.xyz",
            raw_data=entry_data,
        )
        return inscription

    except Exception as exc:
        logger.warning("Failed to parse %s: %s", entry_id, exc)
        import traceback
        traceback.print_exc()
        return None


def load_inscriptions_json(path: str) -> list:
    """Load the lineara.xyz inscriptions.json (list-of-pairs format)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Convert dict to list-of-pairs
        return [[k, v] for k, v in data.items()]
    else:
        raise ValueError(f"Unexpected data format: {type(data)}")


def load_supplement(path: str) -> dict:
    """Load supplement.json into a dict keyed by name."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {entry.get("name", f"UNKNOWN_{i}"): entry for i, entry in enumerate(data)}
    return data


# ===================================================================
# Main
# ===================================================================

def main():
    # Paths
    base = Path(__file__).resolve().parent
    raw_dir = base / "data" / "raw" / "sigla"
    inscriptions_path = raw_dir / "inscriptions.json"
    supplement_path = raw_dir / "supplement.json"
    db_dir = base / "data" / "database"
    db_path = db_dir / "lineara_full.db"

    # Create directories
    db_dir.mkdir(parents=True, exist_ok=True)

    # Step 0: Validate Unicode mapping
    print("=" * 60)
    print("STEP 0: Unicode Mapping Validation")
    print("=" * 60)
    errors = validate_mapping()
    if errors:
        print(f"  ✗ {len(errors)} error(s) found:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  ✓ Mapping table is valid.")
    print(f"  Total mapping entries: {len(validate_mapping.__code__.co_consts)}")  # wonky
    # Count from the module directly
    from pipeline.unicode_utils import BENNETT_TO_UNICODE
    print(f"  Total mapping entries: {len(BENNETT_TO_UNICODE)}")
    print()

    # Step 1: Load data
    print("=" * 60)
    print("STEP 1: Loading lineara.xyz data")
    print("=" * 60)
    
    raw_entries = load_inscriptions_json(str(inscriptions_path))
    supp_data = load_supplement(str(supplement_path))
    print(f"  Loaded {len(raw_entries)} inscription entries from inscriptions.json")
    print(f"  Loaded {len(supp_data)} supplement entries from supplement.json")
    print()

    # Step 2: Parse all entries
    print("=" * 60)
    print("STEP 2: Parsing inscriptions")
    print("=" * 60)
    
    inscriptions = []
    failed = 0
    for entry in raw_entries:
        if isinstance(entry, list) and len(entry) >= 2:
            entry_id = str(entry[0])
            entry_data = entry[1]
        elif isinstance(entry, dict):
            entry_id = entry.get("name", entry.get("gorilaId", "UNKNOWN"))
            entry_data = entry
        else:
            failed += 1
            continue

        ins = parse_lineara_inscription(entry_id, entry_data, supp_data)
        if ins:
            inscriptions.append(ins)
        else:
            failed += 1

    print(f"  Parsed: {len(inscriptions)} inscriptions")
    print(f"  Failed: {failed}")
    
    total_signs = sum(len(ins.signs) for ins in inscriptions)
    print(f"  Total signs across all inscriptions: {total_signs}")
    print()

    # Step 3: Create database and import
    print("=" * 60)
    print("STEP 3: Database Import")
    print("=" * 60)
    
    # Remove old database if exists
    if db_path.exists():
        db_path.unlink()
        print(f"  Removed existing database: {db_path}")

    database = LinearADatabase(str(db_path))
    database.connect()
    print(f"  Created database: {db_path}")

    imported = 0
    for i, ins in enumerate(inscriptions):
        try:
            database.insert_inscription(ins)
            imported += 1
        except Exception as exc:
            logger.error("Failed to import %s: %s", ins.gorilaId, exc)
        if (i + 1) % 200 == 0:
            database.conn.commit()
            print(f"  Progress: {i+1}/{len(inscriptions)}")

    database.conn.commit()
    database.close()
    print(f"  Imported: {imported} inscriptions into database")
    print()

    # Step 4: Stats
    print("=" * 60)
    print("STEP 4: Corpus Statistics")
    print("=" * 60)
    
    database = LinearADatabase(str(db_path))
    database.connect()
    stats = database.stats()
    database.close()

    # Get additional stats via direct SQL
    database = LinearADatabase(str(db_path))
    database.connect()
    conn = database.conn
    
    # Unique signs (bennett_id)
    cur = conn.execute("SELECT COUNT(DISTINCT bennett_id) FROM signs WHERE bennett_id != '' AND bennett_id IS NOT NULL")
    unique_signs = cur.fetchone()[0]
    
    # Sites
    cur = conn.execute("SELECT COUNT(DISTINCT site) FROM findspots")
    sites = cur.fetchone()[0]
    
    # Periods
    cur = conn.execute("SELECT DISTINCT minoan_period FROM inscriptions WHERE minoan_period != '' AND minoan_period IS NOT NULL")
    periods_list = [r[0] for r in cur.fetchall()]
    
    # Materials
    cur = conn.execute("SELECT DISTINCT material FROM inscriptions WHERE material != '' AND material IS NOT NULL")
    materials_list = [r[0] for r in cur.fetchall()]
    
    # Object types
    cur = conn.execute("SELECT DISTINCT object_type FROM inscriptions WHERE object_type != '' AND object_type IS NOT NULL")
    object_types_list = [r[0] for r in cur.fetchall()]
    
    # Material distribution
    cur = conn.execute("SELECT material, COUNT(*) FROM inscriptions WHERE material != '' AND material IS NOT NULL GROUP BY material ORDER BY COUNT(*) DESC")
    material_dist = dict(cur.fetchall())
    
    # Object type distribution
    cur = conn.execute("SELECT object_type, COUNT(*) FROM inscriptions WHERE object_type != '' AND object_type IS NOT NULL GROUP BY object_type ORDER BY COUNT(*) DESC")
    object_type_dist = dict(cur.fetchall())
    
    # Period distribution
    cur = conn.execute("SELECT minoan_period, COUNT(*) FROM inscriptions WHERE minoan_period != '' AND minoan_period IS NOT NULL GROUP BY minoan_period ORDER BY COUNT(*) DESC")
    period_dist = dict(cur.fetchall())
    
    # Site distribution (top 20)
    cur = conn.execute("SELECT f.site, COUNT(*) as cnt FROM inscriptions i JOIN findspots f ON i.findspot_id = f.id GROUP BY f.site ORDER BY cnt DESC LIMIT 20")
    site_dist = list(cur.fetchall())
    
    # Sign type distribution
    cur = conn.execute("SELECT sign_type, COUNT(*) FROM signs GROUP BY sign_type ORDER BY COUNT(*) DESC")
    sign_type_dist = dict(cur.fetchall())
    
    # Top signs
    cur = conn.execute("SELECT bennett_id, COUNT(*) as cnt FROM signs WHERE bennett_id != '' AND bennett_id IS NOT NULL GROUP BY bennett_id ORDER BY cnt DESC LIMIT 20")
    top_signs = list(cur.fetchall())
    
    database.close()

    # Print stats
    print(f"  Total inscriptions: {stats.get('inscriptions', len(inscriptions))}")
    print(f"  Total signs: {stats.get('signs', total_signs)}")
    print(f"  Unique signs (Bennett IDs): {unique_signs}")
    print(f"  Sites: {sites}")
    print(f"  Periods: {len(periods_list)}")
    print(f"  Materials: {len(materials_list)}")
    print(f"  Object types: {len(object_types_list)}")
    print()
    
    if 'date_range' in stats:
        print(f"  Date range: {stats['date_range']}")
    
    print(f"\n  Period distribution:")
    for p, c in period_dist.items():
        print(f"    {p}: {c}")
    
    print(f"\n  Material distribution:")
    for m, c in material_dist.items():
        print(f"    {m}: {c}")
    
    print(f"\n  Object type distribution:")
    for ot, c in object_type_dist.items():
        print(f"    {ot}: {c}")
    
    print(f"\n  Top 10 sites:")
    for site, cnt in site_dist[:10]:
        print(f"    {site}: {cnt}")
    
    print(f"\n  Sign type distribution:")
    for st, cnt in sign_type_dist.items():
        print(f"    {st}: {cnt}")
    
    print(f"\n  Top 15 signs:")
    for bid, cnt in top_signs[:15]:
        print(f"    {bid}: {cnt}")
    
    print()

    # Step 5: Additional stats - inscriptions with no signs
    database = LinearADatabase(str(db_path))
    database.connect()
    conn = database.conn
    cur = conn.execute("SELECT COUNT(*) FROM inscriptions i WHERE (SELECT COUNT(*) FROM signs s WHERE s.inscription_id = i.id) = 0")
    empty = cur.fetchone()[0]
    cur = conn.execute("SELECT gorila_id FROM inscriptions i WHERE (SELECT COUNT(*) FROM signs s WHERE s.inscription_id = i.id) = 0 LIMIT 10")
    empty_ids = [r[0] for r in cur.fetchall()]
    database.close()
    
    if empty > 0:
        print(f"  Inscriptions with no signs: {empty}")
        if empty_ids:
            print(f"    Examples: {', '.join(empty_ids[:10])}")
    print()

    # Step 6: Write summary report
    print("=" * 60)
    print("STEP 5: Writing Summary Report")
    print("=" * 60)
    
    report_path = base / "phase2_corpus_ingestion.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Phase 2 — Corpus Ingestion Report\n\n")
        f.write(f"**Date:** $(date +%Y-%m-%d)\n\n")
        f.write("## 1. Data Sources\n\n")
        f.write("| Source | File | Records |\n")
        f.write("|--------|------|--------|\n")
        f.write(f"| lineara.xyz | `inscriptions.json` | {len(raw_entries)} entries |\n")
        f.write(f"| lineara.xyz | `supplement.json` | {len(supp_data)} entries |\n")
        f.write("\n")
        
        f.write("## 2. Unicode Mapping Validation\n\n")
        if not errors:
            f.write("✅ **PASSED** — No errors in Bennett→Unicode mapping table.\n")
        else:
            f.write(f"⚠️ **{len(errors)} error(s) found**\n\n")
            for e in errors:
                f.write(f"- {e}\n")
        f.write(f"\nTotal mapping entries: {len(BENNETT_TO_UNICODE)}\n\n")
        
        f.write("## 3. Parsing Results\n\n")
        f.write(f"- Total JSON entries processed: {len(raw_entries)}\n")
        f.write(f"- Successfully parsed: **{len(inscriptions)}**\n")
        f.write(f"- Failed: **{failed}**\n")
        f.write(f"- Total sign instances extracted: **{total_signs}**\n")
        f.write(f"- Inscriptions with no signs: **{empty}**\n")
        if empty_ids:
            f.write(f"  - Examples: {', '.join(empty_ids[:10])}\n")
        f.write("\n")
        
        f.write("## 4. Database Ingestion\n\n")
        f.write(f"- Database: `data/database/lineara_full.db`\n")
        f.write(f"- Records imported: **{imported}**\n")
        f.write(f"- Database schema: 12 tables (inscriptions, signs, sign_semantics, lines, words, word_dividers, lacunae, images, bibliography, relations_linear_b, findspots, inscriptions_fts)\n")
        f.write("\n")
        
        f.write("## 5. Corpus Statistics\n\n")
        f.write("### Overview\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total inscriptions | {stats.get('inscriptions', len(inscriptions))} |\n")
        f.write(f"| Total signs | {stats.get('signs', total_signs)} |\n")
        f.write(f"| Unique signs (Bennett IDs) | {unique_signs} |\n")
        f.write(f"| Sites | {sites} |\n")
        f.write(f"| Periods | {len(periods_list)} |\n")
        f.write(f"| Material types | {len(materials_list)} |\n")
        f.write(f"| Object types | {len(object_types_list)} |\n")
        if 'date_range' in stats:
            f.write(f"| Date range | {stats['date_range']['from']} – {stats['date_range']['to']} BCE |\n")
        f.write("\n")
        
        f.write("### Period Distribution\n\n")
        f.write("| Period | Count |\n")
        f.write("|--------|-------|\n")
        for p, c in sorted(period_dist.items(), key=lambda x: -x[1]):
            f.write(f"| {p} | {c} |\n")
        f.write("\n")
        
        f.write("### Material Distribution\n\n")
        f.write("| Material | Count |\n")
        f.write("|----------|-------|\n")
        for m, c in sorted(material_dist.items(), key=lambda x: -x[1]):
            f.write(f"| {m} | {c} |\n")
        f.write("\n")
        
        f.write("### Object Type Distribution\n\n")
        f.write("| Object Type | Count |\n")
        f.write("|-------------|-------|\n")
        for ot, c in sorted(object_type_dist.items(), key=lambda x: -x[1]):
            f.write(f"| {ot} | {c} |\n")
        f.write("\n")
        
        f.write("### Sign Type Distribution\n\n")
        f.write("| Sign Type | Count |\n")
        f.write("|-----------|-------|\n")
        for st, cnt in sorted(sign_type_dist.items(), key=lambda x: -x[1]):
            f.write(f"| {st} | {cnt} |\n")
        f.write("\n")
        
        f.write("### Top 10 Sites\n\n")
        f.write("| Site | Inscriptions |\n")
        f.write("|------|-------------|\n")
        for site, cnt in site_dist[:10]:
            f.write(f"| {site} | {cnt} |\n")
        f.write("\n")
        
        f.write("### Top 15 Signs (by frequency)\n\n")
        f.write("| Bennett ID | Count |\n")
        f.write("|------------|-------|\n")
        for bid, cnt in top_signs[:15]:
            f.write(f"| {bid} | {cnt} |\n")
        f.write("\n")
        
        f.write("## 6. Unicode Validation Details\n\n")
        f.write("The built-in `BENNETT_TO_UNICODE` mapping table contains ")
        f.write(f"{len(BENNETT_TO_UNICODE)} entries covering:\n\n")
        
        # Count by type
        from collections import Counter
        types = Counter(t[4] for t in BENNETT_TO_UNICODE)
        for st, cnt in types.most_common():
            f.write(f"- **{st}**: {cnt} entries\n")
        f.write("\n")
        f.write("The validation checks:\n")
        f.write("- No duplicate Bennett IDs\n")
        f.write("- No duplicate Unicode code points\n")
        f.write("- Valid Unicode hex format (`U+10600`–`U+1077F`)\n")
        f.write("- Character literal matches code point\n")
        f.write("\n")
        
        f.write("---\n")
        f.write("*Report generated by Labrys pipeline ingestion script.*\n")
    
    print(f"  Report written to: {report_path}")
    print()
    print("=" * 60)
    print("DONE — All tasks complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
