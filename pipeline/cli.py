#!/usr/bin/env python3
"""
CLI — Command-line interface for the Linear A Digitization Pipeline
====================================================================
Usage:
    pipeline --help
    pipeline unicode validate
    pipeline unicode generate-csv path/to/output.csv
    pipeline parse sigla path/to/database.js
    pipeline parse tei path/to/corpus/dir
    pipeline db init path/to/database.db
    pipeline db import path/to/database.db [--sigla ...] [--tei ...]
    pipeline db query path/to/database.db [--site ...] [--period ...]
    pipeline db stats path/to/database.db
    pipeline cooccurrence path/to/database.db output/dir [--normalize jaccard|pmi|tscore]
    pipeline export jsonld path/to/database.db output/dir
    pipeline export tei-xml path/to/database.db output/dir
    pipeline export plaintext path/to/database.db output/path [--format ab|translit|unicode|mixed]
    pipeline run --sigla path/to/database.js --db path/to/database.db [--export output/dir]
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from . import __version__
from .unicode_utils import (
    BENNETT_TO_UNICODE, write_mapping_csv, validate_mapping,
    lookup_sign, bennett_to_unicode, bennett_to_character,
    is_valid_bennett,
)
from .parser_sigla import parse_sigla_js, parse_sigla_json
from .parser_tei import parse_tei_corpus, parse_tei_xml
from .database import LinearADatabase
from .cooccurrence import CooccurrenceMatrix
from .exporters import (
    export_jsonld, export_jsonld_collection,
    export_tei_xml,
    export_plaintext,
)

logger = logging.getLogger("pipeline")


# ===================================================================
# Logging setup
# ===================================================================

def _setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ===================================================================
# CLI groups
# ===================================================================

@click.group()
@click.version_option(version=__version__, prog_name="labrys-pipeline")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def cli(verbose: bool):
    """Labrys Linear A Digitization Pipeline"""
    _setup_logging(verbose)


# -------------------------------------------------------------------
# unicode
# -------------------------------------------------------------------

@cli.group()
def unicode():
    """Unicode mapping utilities for the Aegean block (U+10600–U+1077F)."""


@unicode.command("validate")
def unicode_validate():
    """Validate the built-in Bennett → Unicode mapping table."""
    errors = validate_mapping()
    if errors:
        click.echo(f"Found {len(errors)} error(s):")
        for e in errors:
            click.echo(f"  ✗ {e}")
        sys.exit(1)
    else:
        click.echo("✓ Mapping table is valid.")
        click.echo(f"  Total entries: {len(BENNETT_TO_UNICODE)}")
        # Show break-down
        from collections import Counter
        types = Counter(t[4] for t in BENNETT_TO_UNICODE)
        for st, cnt in types.most_common():
            click.echo(f"    {st}: {cnt}")


@unicode.command("generate-csv")
@click.argument("output", type=click.Path())
def unicode_csv(output: str):
    """Write the full mapping table to a CSV file."""
    count = write_mapping_csv(output)
    click.echo(f"✓ Wrote {count} mapping rows to {output}")


@unicode.command("lookup")
@click.option("--bennett", "-b", help="Bennett ID (e.g., 'AB 02' or 'A 338')")
@click.option("--unicode", "-u", "unicode_ref", help="Unicode hex (e.g., 'U+10600')")
def unicode_lookup(bennett: str, unicode_ref: str):
    """Look up a sign by Bennett ID or Unicode reference."""
    if not bennett and not unicode_ref:
        click.echo("Provide at least --bennett or --unicode.")
        sys.exit(1)
    result = lookup_sign(bennett_id=bennett, unicode_ref=unicode_ref)
    if result:
        click.echo("Sign found:")
        for k, v in result.items():
            click.echo(f"  {k}: {v}")
    else:
        click.echo("No matching sign found.")


# -------------------------------------------------------------------
# parse
# -------------------------------------------------------------------

@cli.group()
def parse():
    """Parse inscription data from various source formats."""


@parse.command("sigla")
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True,
              help="Input is already JSON, not JS")
@click.option("--limit", type=int, default=0, help="Max inscriptions to parse")
@click.option("--output", "-o", type=click.Path(), help="Save parsed data as JSON")
def parse_sigla(input_path: str, as_json: bool, limit: int, output: str):
    """Parse SigLA database.js (or JSON dump) file."""
    if as_json:
        results = parse_sigla_json(input_path)
    else:
        results = parse_sigla_js(input_path)

    if not results:
        click.echo("No inscriptions parsed.")
        sys.exit(1)

    click.echo(f"Parsed {len(results)} inscriptions from SigLA.")

    if limit > 0:
        results = dict(list(results.items())[:limit])

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.to_dict() for k, v in results.items()},
                f, indent=2, ensure_ascii=False,
            )
        click.echo(f"Saved parsed data to {output}")

    # Summary
    sites = set()
    total_signs = 0
    for ins in results.values():
        if ins.findspot:
            sites.add(ins.findspot.site)
        total_signs += len(ins.signs)
    click.echo(f"  Sites: {len(sites)}")
    click.echo(f"  Total signs: {total_signs}")


@parse.command("tei")
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Save parsed data as JSON")
def parse_tei(input_path: str, output: str):
    """Parse TEI-XML corpus (file or directory)."""
    input_path = Path(input_path)
    if input_path.is_file():
        ins = parse_tei_xml(str(input_path))
        results = {ins.gorilaId: ins} if ins else {}
    else:
        results = parse_tei_corpus(str(input_path))

    if not results:
        click.echo("No inscriptions parsed.")
        sys.exit(1)

    click.echo(f"Parsed {len(results)} inscriptions from TEI.")

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.to_dict() for k, v in results.items()},
                f, indent=2, ensure_ascii=False,
            )
        click.echo(f"Saved parsed data to {output}")

    total_signs = sum(len(ins.signs) for ins in results.values())
    click.echo(f"  Total signs: {total_signs}")


# -------------------------------------------------------------------
# db
# -------------------------------------------------------------------

@cli.group()
def db():
    """SQLite database operations."""


@db.command("init")
@click.argument("db_path", type=click.Path())
def db_init(db_path: str):
    """Create/initialize an empty database."""
    database = LinearADatabase(db_path)
    database.connect()
    database.close()
    click.echo(f"✓ Initialised database: {db_path}")


@db.command("import")
@click.argument("db_path", type=click.Path())
@click.option("--sigla", type=click.Path(exists=True), help="SigLA JS/JSON file")
@click.option("--sigla-json", is_flag=True, help="SigLA input is JSON not JS")
@click.option("--tei", type=click.Path(exists=True), help="TEI file/directory")
@click.option("--json", "json_path", type=click.Path(exists=True), help="JSON dump file")
@click.option("--commit-every", type=int, default=50, help="Commit every N records")
def db_import(db_path: str, sigla: str, sigla_json: bool,
              tei: str, json_path: str, commit_every: int):
    """Import inscriptions from various sources into the database."""
    database = LinearADatabase(db_path)
    database.connect()

    all_inscriptions = []
    count = 0

    if sigla:
        if sigla_json:
            parsed = parse_sigla_json(sigla)
        else:
            parsed = parse_sigla_js(sigla)
        click.echo(f"Parsed {len(parsed)} SigLA inscriptions.")
        all_inscriptions.extend(parsed.values())

    if tei:
        tei_path = Path(tei)
        if tei_path.is_file():
            ins = parse_tei_xml(str(tei_path))
            parsed_tei = {ins.gorilaId: ins} if ins else {}
        else:
            parsed_tei = parse_tei_corpus(str(tei_path))
        click.echo(f"Parsed {len(parsed_tei)} TEI inscriptions.")
        all_inscriptions.extend(parsed_tei.values())

    if json_path:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        from .models import Inscription as InsModel
        for key, val in data.items():
            try:
                ins = InsModel.from_dict(val)
                all_inscriptions.append(ins)
            except Exception as exc:
                logger.warning("Failed to parse from JSON: %s", exc)
        click.echo(f"Loaded {len(all_inscriptions)} from JSON dump (after dedup).")

    # Deduplicate by GORILA ID (last source wins)
    seen = {}
    for ins in all_inscriptions:
        if ins.gorilaId in seen:
            logger.warning("Duplicate GORILA ID %s from different sources; keeping last.", ins.gorilaId)
        seen[ins.gorilaId] = ins
    deduped = list(seen.values())

    click.echo(f"Importing {len(deduped)} unique inscriptions…")
    total_signs = 0
    for i, ins in enumerate(deduped):
        try:
            database.insert_inscription(ins)
            total_signs += len(ins.signs)
            count += 1
        except Exception as exc:
            logger.error("Failed to import %s: %s", ins.gorilaId, exc)
        if i > 0 and i % commit_every == 0:
            database.conn.commit()

    database.conn.commit()
    database.close()

    click.echo(f"✓ Imported {count} inscriptions with {total_signs} signs into {db_path}")


@db.command("query")
@click.argument("db_path", type=click.Path(exists=True))
@click.option("--site", help="Filter by findspot site")
@click.option("--period", help="Filter by Minoan period")
@click.option("--material", help="Filter by material")
@click.option("--object-type", "object_type", help="Filter by object type")
@click.option("--signs", help="Filter by sign sequence (space-separated Bennett IDs)")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def db_query(db_path: str, site: str, period: str, material: str,
             object_type: str, signs: str, limit: int, as_json: bool):
    """Query inscriptions in the database."""
    database = LinearADatabase(db_path)
    database.connect()

    results = database.search(
        site=site, period=period,
        material=material, object_type=object_type,
        sign_sequence=signs, limit=limit,
    )

    if not results:
        click.echo("No matching inscriptions found.")
        database.close()
        return

    if as_json:
        data = [ins.to_dict() for ins in results]
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        click.echo(f"Found {len(results)} inscription(s):")
        for ins in results:
            site_str = ins.findspot.site if ins.findspot else "?"
            period_str = ins.date.minoanPeriod if ins.date else "?"
            sign_count = len(ins.signs)
            click.echo(f"  {ins.gorilaId:12s} | {site_str:20s} | {period_str:12s} | {sign_count} signs")

    database.close()


@db.command("stats")
@click.argument("db_path", type=click.Path(exists=True))
def db_stats(db_path: str):
    """Show corpus statistics from the database."""
    database = LinearADatabase(db_path)
    database.connect()
    stats = database.stats()
    database.close()

    click.echo("Corpus Statistics:")
    for k, v in stats.items():
        if isinstance(v, dict):
            click.echo(f"  {k}:")
            for sk, sv in v.items():
                click.echo(f"    {sk}: {sv}")
        else:
            click.echo(f"  {k}: {v}")


# -------------------------------------------------------------------
# cooccurrence
# -------------------------------------------------------------------

@cli.command()
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--normalize", type=click.Choice(["jaccard", "pmi", "tscore"]),
              help="Normalization method")
@click.option("--min-frequency", type=int, default=2,
              help="Minimum sign frequency for inclusion")
@click.option("--context", type=click.Choice(["document", "line", "word"]),
              default="document", help="Co-occurrence context")
@click.option("--min-weight", type=float, default=0.0,
              help="Minimum edge weight for edge list")
def cooccurrence(db_path: str, output_dir: str, normalize: str,
                 min_frequency: int, context: str, min_weight: float):
    """Generate sign co-occurrence matrix from database."""
    database = LinearADatabase(db_path)
    database.connect()

    # Load all inscriptions
    rows = database.list_all()
    if not rows:
        click.echo("No inscriptions found in database.")
        database.close()
        return

    inscriptions = []
    for r in rows:
        ins = database.get_inscription(r["gorila_id"])
        if ins:
            inscriptions.append(ins)

    database.close()
    click.echo(f"Loaded {len(inscriptions)} inscriptions for co-occurrence analysis.")

    # Build matrix
    matrix = CooccurrenceMatrix(inscriptions, min_frequency=min_frequency, context=context)
    matrix.build()

    summary = matrix.summary()
    click.echo(f"Matrix: {summary['signs']} signs, "
               f"{summary['non_zero_pairs']} non-zero pairs, "
               f"density={summary['density']:.4f}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Write CSV matrix
    csv_path = str(output_path / f"cooccurrence_{summary['signs']}signs.csv")
    matrix.write_csv(csv_path, normalize=normalize)
    click.echo(f"Matrix CSV: {csv_path}")

    # Write edge list
    edge_path = str(output_path / f"edgelist_{summary['signs']}signs.csv")
    n_edges = matrix.write_edge_list(edge_path, normalize=normalize, min_weight=min_weight)
    click.echo(f"Edge list: {edge_path} ({n_edges} edges)")

    # Try NetworkX export
    try:
        G = matrix.to_networkx(normalize=normalize, min_weight=min_weight)
        gml_path = str(output_path / f"graph_{summary['signs']}signs.gml")
        nx.write_gml(G, gml_path)
        click.echo(f"NetworkX GML: {gml_path}")
    except (ImportError, Exception) as exc:
        click.echo(f"NetworkX export skipped: {exc}")


# -------------------------------------------------------------------
# export
# -------------------------------------------------------------------

@cli.group()
def export():
    """Export inscriptions to standard formats."""


@export.command("jsonld")
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--base-uri", default="https://data.lineara.org",
              help="Base URI for JSON-LD @id")
@click.option("--ids", help="Comma-separated list of GORILA IDs to export")
def export_jsonld_cmd(db_path: str, output_dir: str, base_uri: str, ids: str):
    """Export inscriptions as JSON-LD files + collection manifest."""
    database = LinearADatabase(db_path)
    database.connect()

    if ids:
        id_list = [i.strip() for i in ids.split(",")]
        inscriptions = []
        for gid in id_list:
            ins = database.get_inscription(gid)
            if ins:
                inscriptions.append(ins)
    else:
        rows = database.list_all()
        inscriptions = [database.get_inscription(r["gorila_id"]) for r in rows]
        inscriptions = [ins for ins in inscriptions if ins]

    database.close()

    if not inscriptions:
        click.echo("No inscriptions to export.")
        return

    # Individual exports
    for ins in inscriptions:
        export_jsonld(ins, output_dir, f"{base_uri}/inscription")

    # Collection manifest
    manifest_path = export_jsonld_collection(inscriptions, output_dir, base_uri)

    click.echo(f"Exported {len(inscriptions)} JSON-LD files to {output_dir}")
    click.echo(f"Collection manifest: {manifest_path}")


@export.command("tei-xml")
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--ids", help="Comma-separated list of GORILA IDs to export")
def export_tei_cmd(db_path: str, output_dir: str, ids: str):
    """Export inscriptions as TEI-XML files."""
    database = LinearADatabase(db_path)
    database.connect()

    if ids:
        id_list = [i.strip() for i in ids.split(",")]
        inscriptions = []
        for gid in id_list:
            ins = database.get_inscription(gid)
            if ins:
                inscriptions.append(ins)
    else:
        rows = database.list_all()
        inscriptions = [database.get_inscription(r["gorila_id"]) for r in rows]
        inscriptions = [ins for ins in inscriptions if ins]

    database.close()

    if not inscriptions:
        click.echo("No inscriptions to export.")
        return

    for ins in inscriptions:
        export_tei_xml(ins, output_dir)

    click.echo(f"Exported {len(inscriptions)} TEI-XML files to {output_dir}")


@export.command("plaintext")
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("output_path", type=click.Path())
@click.option("--format", "text_format",
              type=click.Choice(["ab", "translit", "unicode", "mixed"]),
              default="ab", help="Text format")
@click.option("--ids", help="Comma-separated list of GORILA IDs to export")
def export_plaintext_cmd(db_path: str, output_path: str, text_format: str, ids: str):
    """Export inscriptions as plain text transliterations."""
    database = LinearADatabase(db_path)
    database.connect()

    if ids:
        id_list = [i.strip() for i in ids.split(",")]
        inscriptions = []
        for gid in id_list:
            ins = database.get_inscription(gid)
            if ins:
                inscriptions.append(ins)
    else:
        rows = database.list_all()
        inscriptions = [database.get_inscription(r["gorila_id"]) for r in rows]
        inscriptions = [ins for ins in inscriptions if ins]

    database.close()

    if not inscriptions:
        click.echo("No inscriptions to export.")
        return

    export_plaintext(inscriptions, output_path, format=text_format)
    click.echo(f"Exported {len(inscriptions)} inscriptions to {output_path}")


# -------------------------------------------------------------------
# run (full pipeline)
# -------------------------------------------------------------------

@cli.command()
@click.option("--sigla", type=click.Path(exists=True), help="SigLA JS/JSON file")
@click.option("--tei", type=click.Path(exists=True), help="TEI file/directory")
@click.option("--db", "db_path", type=click.Path(), required=True,
              help="SQLite database path (will be created)")
@click.option("--export", "export_dir", type=click.Path(),
              help="Export directory (JSON-LD + TEI-XML + plain text)")
@click.option("--cooccurrence", "cooc_dir", type=click.Path(),
              help="Co-occurrence output directory")
@click.option("--mapping-csv", type=click.Path(),
              help="Write Bennett → Unicode mapping CSV")
@click.option("--min-freq", type=int, default=2,
              help="Min sign frequency for co-occurrence")
@click.option("--verbose", "-v", is_flag=True)
def run(sigla: str, tei: str, db_path: str,
        export_dir: str, cooc_dir: str,
        mapping_csv: str, min_freq: int, verbose: bool):
    """Run the full digitization pipeline (parse → db → export)."""
    _setup_logging(verbose)
    click.echo("╔══════════════════════════════════════════╗")
    click.echo("║  Labrys Linear A Digitization Pipeline  ║")
    click.echo("╚══════════════════════════════════════════╝")

    # 1. Unicode mapping validation
    click.echo("\n[1/5] Validating Unicode mapping…")
    errors = validate_mapping()
    if errors:
        click.echo(f"  ⚠ {len(errors)} mapping errors found:")
        for e in errors[:5]:
            click.echo(f"    {e}")
    else:
        click.echo("  ✓ Mapping valid")

    if mapping_csv:
        write_mapping_csv(mapping_csv)
        click.echo(f"  ✓ Mapping CSV written to {mapping_csv}")

    # 2. Parse sources
    all_inscriptions = []
    click.echo("\n[2/5] Parsing source data…")

    if sigla:
        click.echo(f"  Parsing SigLA: {sigla}")
        parsed = parse_sigla_js(sigla)
        all_inscriptions.extend(parsed.values())
        click.echo(f"  → {len(parsed)} inscriptions from SigLA")

    if tei:
        click.echo(f"  Parsing TEI: {tei}")
        tei_path = Path(tei)
        if tei_path.is_file():
            ins = parse_tei_xml(str(tei_path))
            parsed_tei = {ins.gorilaId: ins} if ins else {}
        else:
            parsed_tei = parse_tei_corpus(str(tei_path))
        all_inscriptions.extend(parsed_tei.values())
        click.echo(f"  → {len(parsed_tei)} inscriptions from TEI")

    if not all_inscriptions:
        click.echo("  ⚠ No source data provided. Use --sigla and/or --tei.")
        sys.exit(1)

    # Deduplicate
    seen = {}
    for ins in all_inscriptions:
        seen[ins.gorilaId] = ins
    deduped = list(seen.values())
    click.echo(f"  Total unique inscriptions: {len(deduped)}")

    # 3. Database import
    click.echo("\n[3/5] Importing into database…")
    database = LinearADatabase(db_path)
    database.connect()
    for i, ins in enumerate(deduped):
        try:
            database.insert_inscription(ins)
        except Exception as exc:
            logger.error("Failed to import %s: %s", ins.gorilaId, exc)
    database.conn.commit()

    stats = database.stats()
    click.echo(f"  ✓ {stats['inscriptions']} inscriptions, {stats['signs']} signs in database")
    click.echo(f"  ✓ {stats['sites']} sites, {stats['periods']} periods")

    # 4. Export
    if export_dir:
        click.echo(f"\n[4/5] Exporting to {export_dir}…")
        Path(export_dir).mkdir(parents=True, exist_ok=True)

        # JSON-LD
        jld_dir = str(Path(export_dir) / "jsonld")
        for ins in deduped:
            export_jsonld(ins, jld_dir)
        export_jsonld_collection(deduped, jld_dir)
        click.echo(f"  ✓ JSON-LD: {jld_dir}")

        # TEI-XML
        tei_dir = str(Path(export_dir) / "tei-xml")
        for ins in deduped:
            export_tei_xml(ins, tei_dir)
        click.echo(f"  ✓ TEI-XML: {tei_dir}")

        # Plain text
        txt_path = str(Path(export_dir) / "corpus_ab.txt")
        export_plaintext(deduped, txt_path, format="ab")
        click.echo(f"  ✓ Plain text: {txt_path}")

        txt_translit = str(Path(export_dir) / "corpus_translit.txt")
        export_plaintext(deduped, txt_translit, format="translit")
        click.echo(f"  ✓ Transliteration text: {txt_translit}")

    # 5. Co-occurrence
    if cooc_dir:
        click.echo(f"\n[5/5] Generating co-occurrence matrix in {cooc_dir}…")
        Path(cooc_dir).mkdir(parents=True, exist_ok=True)

        matrix = CooccurrenceMatrix(deduped, min_frequency=min_freq)
        matrix.build()
        summary = matrix.summary()
        click.echo(f"  Matrix: {summary['signs']} signs, "
                   f"{summary['non_zero_pairs']} pairs, "
                   f"density={summary['density']:.4f}")

        # Raw
        matrix.write_csv(str(Path(cooc_dir) / "matrix_raw.csv"))
        matrix.write_edge_list(str(Path(cooc_dir) / "edgelist_raw.csv"))

        # Jaccard
        matrix.write_csv(str(Path(cooc_dir) / "matrix_jaccard.csv"), normalize="jaccard")
        matrix.write_edge_list(str(Path(cooc_dir) / "edgelist_jaccard.csv"), normalize="jaccard", min_weight=0.0)

        # PMI
        matrix.write_csv(str(Path(cooc_dir) / "matrix_pmi.csv"), normalize="pmi")
        matrix.write_edge_list(str(Path(cooc_dir) / "edgelist_pmi.csv"), normalize="pmi", include_negatives=True)

        # NetworkX
        try:
            import networkx as nx
            for norm_name in ["raw", "jaccard", "pmi"]:
                G = matrix.to_networkx(normalize=norm_name if norm_name != "raw" else None)
                nx.write_gml(G, str(Path(cooc_dir) / f"graph_{norm_name}.gml"))
            click.echo("  ✓ NetworkX graphs saved")
        except ImportError:
            click.echo("  ⚠ NetworkX not available; GML export skipped")

    database.close()

    click.echo("\n✓ Pipeline complete!")
    click.echo(f"  Database: {db_path}")
    if export_dir:
        click.echo(f"  Exports: {export_dir}")
    if cooc_dir:
        click.echo(f"  Co-occurrence: {cooc_dir}")


# ===================================================================
# Entry point
# ===================================================================

def main():
    cli()


if __name__ == "__main__":
    main()
