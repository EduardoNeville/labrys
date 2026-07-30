"""
Linear A Digitization Pipeline
===============================
A comprehensive Python toolkit for processing, storing, and exporting
Linear A inscriptions from multiple digital sources.

Modules:
    models       — Pydantic data models for inscriptions, signs, etc.
    unicode_utils — Bennett AB ↔ Unicode mapping and validation
    parser_sigla — Parsing of SigLA database.js dump
    parser_tei   — Parsing of TEI/XML corpora (Winterstein et al.)
    database     — SQLite storage with full schema
    cooccurrence — Sign co-occurrence matrix generation (Jaccard, PMI)
    exporters    — Export to JSON-LD, TEI-XML, plain text
    cli          — Click-based command-line interface
"""

__version__ = "1.0.0"
__author__ = "Labrys Project"
