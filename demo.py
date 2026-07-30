#!/usr/bin/env python3
"""
Demo: End-to-end test of the Labrys Linear A Digitization Pipeline
===================================================================
Runs the full pipeline using the built-in sample corpus.

Usage:
    python demo.py [--db /tmp/labrys_demo.db] [--export /tmp/labrys_export] [--cooc /tmp/labrys_cooc]
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

# Add parent to path if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.sample_corpus import get_sample_inscriptions
from pipeline.unicode_utils import (
    validate_mapping, write_mapping_csv, lookup_sign,
    BENNETT_TO_UNICODE,
)
from pipeline.database import LinearADatabase
from pipeline.cooccurrence import CooccurrenceMatrix
from pipeline.exporters import (
    export_jsonld, export_jsonld_collection,
    export_tei_xml, export_plaintext,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demo")


def main():
    print("=" * 60)
    print("  Labrys Linear A Pipeline — Demo")
    print("=" * 60)

    # ---- Step 1: Unicode Mapping ----
    print("\n[1] Validating Unicode mapping...")
    errors = validate_mapping()
    if errors:
        print(f"  ✗ {len(errors)} errors found!")
        for e in errors[:5]:
            print(f"    {e}")
    else:
        print(f"  ✓ All {len(BENNETT_TO_UNICODE)} mapping entries valid.")

    # Show a few lookups
    for test_id in ["AB 02", "AB 28", "A 338", "NUM 1", "A 701"]:
        info = lookup_sign(bennett_id=test_id)
        if info:
            print(f"  {test_id:8s} → {info['unicode']} {info['character']}  ({info['transliteration']}) [{info['signType']}]")

    # Write mapping CSV
    mapping_csv = tempfile.mktemp(suffix="_bennett_unicode.csv")
    write_mapping_csv(mapping_csv)
    print(f"\n  ✓ Mapping CSV: {mapping_csv}")

    # ---- Step 2: Load sample corpus ----
    print("\n[2] Loading sample corpus...")
    inscriptions = get_sample_inscriptions()
    print(f"  ✓ Loaded {len(inscriptions)} inscriptions:")
    for ins in inscriptions:
        site = ins.findspot.site if ins.findspot else "?"
        period = ins.date.minoanPeriod if ins.date else "?"
        n_signs = len(ins.signs)
        translit = ins.transliteration_string()[:60]
        print(f"    {ins.gorilaId:8s} | {site:15s} | {period:12s} | {n_signs:2d} signs | {translit}...")

    # ---- Step 3: Database ----
    print("\n[3] Importing into SQLite database...")
    db_path = tempfile.mktemp(suffix="_labrys.db")
    db = LinearADatabase(db_path)
    db.connect()
    for ins in inscriptions:
        db.insert_inscription(ins)
    db.conn.commit()

    stats = db.stats()
    print(f"  ✓ Database: {db_path}")
    print(f"    Inscriptions: {stats['inscriptions']}")
    print(f"    Signs:        {stats['signs']}")
    print(f"    Unique signs: {stats['unique_signs']}")
    print(f"    Sites:        {stats['sites']}")
    print(f"    Periods:      {stats['periods']}")

    # Query examples
    print("\n  Query by site 'Hagia Triada':")
    ht_results = db.search(site="Hagia Triada")
    for r in ht_results[:3]:
        print(f"    {r.gorilaId} — {len(r.signs)} signs")

    print("\n  Query by period 'LM IB':")
    lb_results = db.search(period="LM IB")
    for r in lb_results[:3]:
        print(f"    {r.gorilaId} — {r.findspot.site if r.findspot else '?'}")

    db.close()

    # ---- Step 4: Co-occurrence matrix ----
    print("\n[4] Computing sign co-occurrence matrix...")
    matrix = CooccurrenceMatrix(inscriptions, min_frequency=1)
    matrix.build()
    summary = matrix.summary()
    print(f"  Matrix: {summary['signs']} signs, "
          f"{summary['non_zero_pairs']} non-zero pairs "
          f"(density={summary['density']:.3f})")

    # Show top co-occurrences
    print("\n  Top 10 co-occurring sign pairs (raw counts):")
    pairs = []
    for i in range(matrix.size):
        for j in range(i + 1, matrix.size):
            count = matrix.raw_matrix[i][j]
            if count > 0:
                pairs.append((count, matrix.index_sign[i], matrix.index_sign[j]))
    pairs.sort(reverse=True)
    for cnt, a, b in pairs[:10]:
        print(f"    {a:8s} ↔ {b:8s}  ({cnt} co-occurrences)")

    # Jaccard top pairs
    print("\n  Top 10 sign pairs by Jaccard similarity:")
    jac = matrix.jaccard_matrix()
    jac_pairs = []
    for i in range(matrix.size):
        for j in range(i + 1, matrix.size):
            sim = jac[i][j]
            if sim > 0:
                jac_pairs.append((sim, matrix.index_sign[i], matrix.index_sign[j]))
    jac_pairs.sort(reverse=True)
    for sim, a, b in jac_pairs[:10]:
        print(f"    {a:8s} ↔ {b:8s}  (J={sim:.3f})")

    # Write outputs
    cooc_dir = tempfile.mkdtemp(suffix="_cooc")
    matrix.write_csv(str(Path(cooc_dir) / "matrix_raw.csv"))
    matrix.write_csv(str(Path(cooc_dir) / "matrix_jaccard.csv"), normalize="jaccard")
    matrix.write_edge_list(str(Path(cooc_dir) / "edgelist_raw.csv"))
    matrix.write_edge_list(str(Path(cooc_dir) / "edgelist_jaccard.csv"), normalize="jaccard")
    print(f"\n  ✓ Co-occurrence outputs in {cooc_dir}")

    # NetworkX graph
    try:
        import networkx as nx
        G = matrix.to_networkx(normalize="jaccard", min_weight=0.0)
        gml_path = str(Path(cooc_dir) / "graph_jaccard.gml")
        nx.write_gml(G, gml_path)
        print(f"  ✓ NetworkX graph with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges → {gml_path}")
    except ImportError:
        print("  ⚠ NetworkX not available, skipping graph export")

    # ---- Step 5: Exports ----
    print("\n[5] Exporting to standard formats...")
    export_dir = tempfile.mkdtemp(suffix="_export")

    # JSON-LD
    jsonld_dir = str(Path(export_dir) / "jsonld")
    for ins in inscriptions:
        export_jsonld(ins, jsonld_dir)
    manifest = export_jsonld_collection(inscriptions, jsonld_dir)
    print(f"  ✓ JSON-LD: {jsonld_dir} ({len(inscriptions)} files + collection manifest)")

    # TEI-XML
    tei_dir = str(Path(export_dir) / "tei-xml")
    for ins in inscriptions:
        export_tei_xml(ins, tei_dir)
    print(f"  ✓ TEI-XML: {tei_dir} ({len(inscriptions)} files)")

    # Plain text
    txt_ab = str(Path(export_dir) / "corpus_ab.txt")
    export_plaintext(inscriptions, txt_ab, format="ab")
    txt_translit = str(Path(export_dir) / "corpus_translit.txt")
    export_plaintext(inscriptions, txt_translit, format="translit")
    txt_unicode = str(Path(export_dir) / "corpus_unicode.txt")
    export_plaintext(inscriptions, txt_unicode, format="unicode")
    print(f"  ✓ Plain text: {export_dir} (3 format variants)")

    # Show a TEI-XML sample
    tei_sample = Path(tei_dir) / "HT_1.xml"
    if tei_sample.exists():
        print(f"\n  Sample TEI-XML ({tei_sample}):")
        lines = tei_sample.read_text(encoding="utf-8").split("\n")
        for line in lines[:25]:
            print(f"    {line}")
        print("    ...")

    # Show a JSON-LD sample
    jsonld_sample = Path(jsonld_dir) / "HT_1.jsonld"
    if jsonld_sample.exists():
        with open(jsonld_sample, "r") as f:
            data = json.load(f)
        print(f"\n  Sample JSON-LD ({jsonld_sample}):")
        print(f"    @type: {data.get('@type')}")
        print(f"    gorilaId: {data.get('gorilaId')}")
        print(f"    findspot: {data.get('findspot', {}).get('site')}")
        print(f"    signs: {len(data.get('signs', []))} entries")

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
    print(f"  Database:    {db_path}")
    print(f"  Mapping CSV: {mapping_csv}")
    print(f"  Co-occurrence: {cooc_dir}")
    print(f"  Exports:     {export_dir}")
    print()
    print("  To inspect the database, run:")
    print(f"    python -m pipeline.cli db stats {db_path}")
    print(f"    python -m pipeline.cli db query {db_path} --site Hagia")
    print()
    print("  To re-run with real data:")
    print("    python -m pipeline.cli run --sigla /path/to/database.js --db corpus.db --export ./exports --cooccurrence ./cooc")
    print()


if __name__ == "__main__":
    main()
