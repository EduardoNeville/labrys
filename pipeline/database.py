"""
SQLite Database Module for Linear A Inscriptions
=================================================
Provides a full relational schema matching the Unified Data Schema,
with methods to insert, query, and export inscription data.

Schema tables:
  - inscriptions       — Tier 1: text-level metadata
  - signs              — Tier 2: sign-level annotation
  - sign_semantics     — Tier 5: semantic annotations (logograms, fractions, numerals)
  - lines              — Tier 4: line structure
  - words              — Tier 4: word boundaries
  - images             — Tier 7: image resources
  - bibliography       — Tier 1: bibliography entries
  - relations_linear_b — Tier 6: Linear B relations
  - findspots          — normalized findspot table
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Any

from .models import (
    Inscription, SignInstance, Findspot, DateInfo, Dimensions,
    CurrentLocation, Preservation, Publication, BibliographyEntry,
    Line, WordBoundary, Structure, ImageResource, SignSemantics,
    Relations, LinearBRelation, Coordinates, Lacuna, Paleography,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS findspots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    site        TEXT NOT NULL UNIQUE,
    latitude    REAL,
    longitude   REAL,
    context     TEXT
);

CREATE TABLE IF NOT EXISTS inscriptions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    gorila_id       TEXT NOT NULL UNIQUE,
    alternative_ids TEXT,               -- JSON array
    findspot_id     INTEGER REFERENCES findspots(id),
    minoan_period   TEXT,
    bce_from        INTEGER,
    bce_to          INTEGER,
    date_notes      TEXT,
    material        TEXT,
    object_type     TEXT,
    preservation_state     TEXT,
    preservation_description TEXT,
    dim_height      REAL,
    dim_width       REAL,
    dim_depth       REAL,
    dim_diameter    REAL,
    dim_unit        TEXT DEFAULT 'mm',
    institution     TEXT,
    collection      TEXT,
    inventory_no    TEXT,
    publication_citation TEXT,
    publication_doi TEXT,
    source          TEXT,
    raw_data        TEXT,               -- JSON blob for audit
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS signs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    sequence            INTEGER NOT NULL,
    bennett_id          TEXT,
    unicode             TEXT,
    character           TEXT,
    transliteration     TEXT,
    confidence          REAL,
    sign_type           TEXT DEFAULT 'syllabogram',
    sigla_variant_id    TEXT,
    bbox_x              REAL,
    bbox_y              REAL,
    bbox_w              REAL,
    bbox_h              REAL,
    bbox_unit           TEXT DEFAULT 'mm',
    shape_class         TEXT,
    is_ligature_component INTEGER DEFAULT 0,
    ligature_of         TEXT,           -- JSON array of Bennett IDs
    erasure             INTEGER DEFAULT 0,
    correction_original TEXT,
    correction_corrected TEXT,
    UNIQUE(inscription_id, sequence)
);

CREATE TABLE IF NOT EXISTS sign_semantics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sign_id             INTEGER NOT NULL REFERENCES signs(id) ON DELETE CASCADE,
    logogram_of         TEXT,
    commodity           TEXT,
    fraction_value      TEXT,
    numeric_value       INTEGER,
    unit                TEXT,
    metrological_value  TEXT,
    UNIQUE(sign_id)
);

CREATE TABLE IF NOT EXISTS lines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    line_number         TEXT NOT NULL,
    side                TEXT,
    ruling              INTEGER DEFAULT 0,
    damaged             INTEGER DEFAULT 0,
    continues_from      TEXT,
    UNIQUE(inscription_id, line_number)
);

CREATE TABLE IF NOT EXISTS words (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    word_index          INTEGER NOT NULL,
    sign_sequences      TEXT,           -- JSON array of sequence numbers
    UNIQUE(inscription_id, word_index)
);

CREATE TABLE IF NOT EXISTS word_dividers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    after_sequence      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lacunae (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    num_signs           INTEGER,
    position            INTEGER
);

CREATE TABLE IF NOT EXISTS images (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    iiif_service_url    TEXT,
    iiif_manifest_url   TEXT,
    credit              TEXT,
    license             TEXT,
    image_type          TEXT DEFAULT 'photograph',
    msi_band            TEXT,
    width               INTEGER,
    height              INTEGER
);

CREATE TABLE IF NOT EXISTS bibliography (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    citation            TEXT NOT NULL,
    pages               TEXT
);

CREATE TABLE IF NOT EXISTS relations_linear_b (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inscription_id      INTEGER NOT NULL REFERENCES inscriptions(id) ON DELETE CASCADE,
    dmic_id             TEXT,
    phonetic_value      TEXT
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS inscriptions_fts USING fts5(
    gorila_id,
    material,
    object_type,
    content='inscriptions',
    content_rowid='id'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_signs_inscription ON signs(inscription_id);
CREATE INDEX IF NOT EXISTS idx_signs_bennett ON signs(bennett_id);
CREATE INDEX IF NOT EXISTS idx_signs_unicode ON signs(unicode);
CREATE INDEX IF NOT EXISTS idx_signs_type ON signs(sign_type);
CREATE INDEX IF NOT EXISTS idx_inscriptions_findspot ON inscriptions(findspot_id);
CREATE INDEX IF NOT EXISTS idx_inscriptions_period ON inscriptions(minoan_period);
CREATE INDEX IF NOT EXISTS idx_inscriptions_material ON inscriptions(material);
CREATE INDEX IF NOT EXISTS idx_inscriptions_object_type ON inscriptions(object_type);
"""


# ---------------------------------------------------------------------------
# Database class
# ---------------------------------------------------------------------------

class LinearADatabase:
    """SQLite database wrapper for Linear A inscriptions."""

    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser().resolve())
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Open (or create) the database and ensure the schema exists."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
        logger.info("Connected to database: %s", self.db_path)
        return self.conn

    def _create_schema(self):
        """Execute the schema DDL."""
        if not self.conn:
            raise RuntimeError("Not connected. Call connect() first.")
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert_inscription(self, ins: Inscription) -> int:
        """
        Insert (or update) an Inscription and all its related data.
        Returns the database row ID.
        """
        if not self.conn:
            raise RuntimeError("Not connected.")

        cursor = self.conn.cursor()

        # --- Findspot ---
        findspot_id = None
        if ins.findspot and ins.findspot.site:
            cursor.execute(
                """INSERT OR IGNORE INTO findspots (site, latitude, longitude, context)
                   VALUES (?, ?, ?, ?)""",
                (ins.findspot.site,
                 ins.findspot.coordinates.lat if ins.findspot.coordinates else None,
                 ins.findspot.coordinates.lon if ins.findspot.coordinates else None,
                 ins.findspot.context),
            )
            cursor.execute("SELECT id FROM findspots WHERE site = ?", (ins.findspot.site,))
            row = cursor.fetchone()
            if row:
                findspot_id = row["id"]

        # --- Main inscription row ---
        alt_ids_json = json.dumps(ins.alternativeIds) if ins.alternativeIds else None
        bce_from = ins.date.bceRange.get("from") if ins.date and ins.date.bceRange else None
        bce_to = ins.date.bceRange.get("to") if ins.date and ins.date.bceRange else None

        cursor.execute(
            """INSERT OR REPLACE INTO inscriptions
               (gorila_id, alternative_ids, findspot_id,
                minoan_period, bce_from, bce_to, date_notes,
                material, object_type,
                preservation_state, preservation_description,
                dim_height, dim_width, dim_depth, dim_diameter, dim_unit,
                institution, collection, inventory_no,
                publication_citation, publication_doi,
                source, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ins.gorilaId,
                alt_ids_json,
                findspot_id,
                ins.date.minoanPeriod if ins.date else None,
                bce_from,
                bce_to,
                ins.date.notes if ins.date else None,
                ins.material,
                ins.objectType,
                ins.preservation.state if ins.preservation else None,
                ins.preservation.description if ins.preservation else None,
                ins.dimensions.height if ins.dimensions else None,
                ins.dimensions.width if ins.dimensions else None,
                ins.dimensions.depth if ins.dimensions else None,
                ins.dimensions.diameter if ins.dimensions else None,
                ins.dimensions.unit if ins.dimensions else "mm",
                ins.currentLocation.institution if ins.currentLocation else None,
                ins.currentLocation.collection if ins.currentLocation else None,
                ins.currentLocation.inventoryNumber if ins.currentLocation else None,
                ins.publication.citation if ins.publication else None,
                ins.publication.doi if ins.publication else None,
                ins.source,
                json.dumps(ins.raw_data) if ins.raw_data else None,
            ),
        )
        ins_db_id = cursor.lastrowid
        if ins_db_id is None:
            # If REPLACE happened, get existing ID
            cursor.execute("SELECT id FROM inscriptions WHERE gorila_id = ?", (ins.gorilaId,))
            row = cursor.fetchone()
            ins_db_id = row["id"] if row else None
            if ins_db_id is None:
                raise RuntimeError(f"Failed to get DB id for {ins.gorilaId}")

        # --- Signs ---
        self._delete_related(ins_db_id, "signs")
        for sign in ins.signs:
            sign_db_id = self._insert_sign(ins_db_id, sign)

        # --- Lines ---
        if ins.structure:
            self._delete_related(ins_db_id, "lines")
            for line in ins.structure.lines:
                cursor.execute(
                    """INSERT OR REPLACE INTO lines
                       (inscription_id, line_number, side, ruling, damaged, continues_from)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (ins_db_id, str(line.number), ins.structure.side,
                     1 if line.ruling else 0, 1 if line.damaged else 0,
                     line.continuesFrom),
                )

            # Words
            self._delete_related(ins_db_id, "words")
            for wi, wb in enumerate(ins.structure.words):
                cursor.execute(
                    "INSERT INTO words (inscription_id, word_index, sign_sequences) VALUES (?, ?, ?)",
                    (ins_db_id, wi, json.dumps(wb.signSequences)),
                )

            # Word dividers
            self._delete_related(ins_db_id, "word_dividers")
            for seq_idx in ins.structure.wordDividers:
                cursor.execute(
                    "INSERT INTO word_dividers (inscription_id, after_sequence) VALUES (?, ?)",
                    (ins_db_id, seq_idx),
                )

            # Lacunae
            self._delete_related(ins_db_id, "lacunae")
            for lac in ins.structure.lacunae:
                cursor.execute(
                    "INSERT INTO lacunae (inscription_id, num_signs, position) VALUES (?, ?, ?)",
                    (ins_db_id, lac.signs, lac.position),
                )

        # --- Images ---
        self._delete_related(ins_db_id, "images")
        for img in ins.images:
            cursor.execute(
                """INSERT INTO images
                   (inscription_id, iiif_service_url, iiif_manifest_url,
                    credit, license, image_type, msi_band, width, height)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ins_db_id, img.iiifServiceUrl, img.iiifManifestUrl,
                 img.credit, img.license, img.type, img.msiBand,
                 img.width, img.height),
            )

        # --- Bibliography ---
        self._delete_related(ins_db_id, "bibliography")
        for be in ins.bibliography:
            cursor.execute(
                "INSERT INTO bibliography (inscription_id, citation, pages) VALUES (?, ?, ?)",
                (ins_db_id, be.citation, be.pages),
            )

        # --- Relations ---
        if ins.relations:
            self._delete_related(ins_db_id, "relations_linear_b")
            for lb in ins.relations.linearB:
                cursor.execute(
                    "INSERT INTO relations_linear_b (inscription_id, dmic_id, phonetic_value) VALUES (?, ?, ?)",
                    (ins_db_id, lb.dmicId, lb.phoneticValue),
                )

        self.conn.commit()
        return ins_db_id

    def _insert_sign(self, ins_db_id: int, sign: SignInstance) -> int:
        """Insert a single sign record. Returns sign DB id."""
        cursor = self.conn.cursor()
        correction_orig = sign.correction.original if sign.correction else None
        correction_corr = sign.correction.correctedTo if sign.correction else None
        ligature_of_json = json.dumps(sign.ligatureOf) if sign.ligatureOf else None

        cursor.execute(
            """INSERT INTO signs
               (inscription_id, sequence, bennett_id, unicode, character,
                transliteration, confidence, sign_type, sigla_variant_id,
                bbox_x, bbox_y, bbox_w, bbox_h, bbox_unit,
                shape_class, is_ligature_component, ligature_of,
                erasure, correction_original, correction_corrected)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ins_db_id, sign.sequence, sign.bennettId, sign.unicode,
             sign.character, sign.transliteration, sign.confidence,
             sign.signType, sign.siglaVariantId,
             sign.boundingBox.x if sign.boundingBox else None,
             sign.boundingBox.y if sign.boundingBox else None,
             sign.boundingBox.width if sign.boundingBox else None,
             sign.boundingBox.height if sign.boundingBox else None,
             sign.boundingBox.unit if sign.boundingBox else "mm",
             sign.shapeClass,
             1 if sign.isLigatureComponent else 0,
             ligature_of_json,
             1 if sign.erasure else 0,
             correction_orig, correction_corr),
        )
        sign_db_id = cursor.lastrowid

        # Semantics
        if sign.semantics:
            cursor.execute(
                """INSERT OR REPLACE INTO sign_semantics
                   (sign_id, logogram_of, commodity, fraction_value, numeric_value, unit, metrological_value)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sign_db_id, sign.semantics.logogramOf, sign.semantics.commodity,
                 sign.semantics.fractionValue, sign.semantics.numericValue,
                 sign.semantics.unit, sign.semantics.metrologicalValue),
            )

        return sign_db_id

    def _delete_related(self, ins_db_id: int, table: str):
        """Delete all rows for an inscription from a related table."""
        if not self.conn:
            return
        col = "inscription_id"
        self.conn.execute(f"DELETE FROM {table} WHERE {col} = ?", (ins_db_id,))

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_inscription(self, gorila_id: str) -> Optional[Inscription]:
        """Retrieve a single inscription by GORILA ID."""
        if not self.conn:
            raise RuntimeError("Not connected.")
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, f.site, f.latitude, f.longitude, f.context as findspot_context
               FROM inscriptions i
               LEFT JOIN findspots f ON i.findspot_id = f.id
               WHERE i.gorila_id = ?""",
            (gorila_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_inscription(row)

    def search(self, site: Optional[str] = None,
               period: Optional[str] = None,
               material: Optional[str] = None,
               object_type: Optional[str] = None,
               sign_sequence: Optional[str] = None,
               limit: int = 100) -> list[Inscription]:
        """
        Search inscriptions by various criteria.
        sign_sequence is a space-separated list of Bennett IDs.
        """
        if not self.conn:
            raise RuntimeError("Not connected.")

        query = """SELECT DISTINCT i.*, f.site, f.latitude, f.longitude, f.context as findspot_context
                   FROM inscriptions i
                   LEFT JOIN findspots f ON i.findspot_id = f.id"""
        joins = []
        conditions = []
        params: list[Any] = []

        if site:
            conditions.append("f.site LIKE ?")
            params.append(f"%{site}%")

        if period:
            conditions.append("i.minoan_period = ?")
            params.append(period)

        if material:
            conditions.append("i.material LIKE ?")
            params.append(f"%{material}%")

        if object_type:
            conditions.append("i.object_type LIKE ?")
            params.append(f"%{object_type}%")

        if sign_sequence:
            bennett_ids = sign_sequence.strip().split()
            placeholders = ",".join("?" for _ in bennett_ids)
            joins.append("JOIN signs s2 ON i.id = s2.inscription_id")
            conditions.append(f"s2.bennett_id IN ({placeholders})")
            params.extend(bennett_ids)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # For sign sequence, also ensure ordering
        if sign_sequence:
            query += " GROUP BY i.id HAVING COUNT(DISTINCT s2.bennett_id) = ?"
            params.append(len(bennett_ids))

        query += " ORDER BY i.gorila_id LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [self._row_to_inscription(r) for r in rows]

    def list_all(self) -> list[dict]:
        """List all inscriptions (summary only)."""
        if not self.conn:
            raise RuntimeError("Not connected.")
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.id, i.gorila_id, f.site, i.minoan_period, i.material,
                      i.object_type, i.preservation_state,
                      (SELECT COUNT(*) FROM signs s WHERE s.inscription_id = i.id) as sign_count
               FROM inscriptions i
               LEFT JOIN findspots f ON i.findspot_id = f.id
               ORDER BY i.gorila_id"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_signs_for_inscription(self, ins_db_id: int) -> list[dict]:
        """Get all signs for an inscription."""
        if not self.conn:
            raise RuntimeError("Not connected.")
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT s.*, ss.logogram_of, ss.commodity, ss.fraction_value,
                      ss.numeric_value
               FROM signs s
               LEFT JOIN sign_semantics ss ON s.id = ss.sign_id
               WHERE s.inscription_id = ?
               ORDER BY s.sequence""",
            (ins_db_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return basic corpus statistics."""
        if not self.conn:
            raise RuntimeError("Not connected.")
        cursor = self.conn.cursor()

        stats = {}
        cursor.execute("SELECT COUNT(*) FROM inscriptions")
        stats["inscriptions"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM signs")
        stats["signs"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT bennett_id) FROM signs WHERE bennett_id != ''")
        stats["unique_signs"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT f.site) FROM inscriptions i JOIN findspots f ON i.findspot_id = f.id")
        stats["sites"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT minoan_period) FROM inscriptions WHERE minoan_period != ''")
        stats["periods"] = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(bce_from), MAX(bce_to) FROM inscriptions WHERE bce_from IS NOT NULL")
        row = cursor.fetchone()
        if row and row[0] is not None:
            stats["date_range"] = {"from": row[0], "to": row[1]}

        return stats

    # ------------------------------------------------------------------
    # Internal: row -> Inscription
    # ------------------------------------------------------------------

    def _row_to_inscription(self, row: sqlite3.Row) -> Inscription:
        """Convert a database row to an Inscription object."""
        rd = dict(row)

        findspot = None
        if rd.get("site"):
            coords = None
            if rd.get("latitude") is not None and rd.get("longitude") is not None:
                coords = Coordinates(lat=rd["latitude"], lon=rd["longitude"])
            findspot = Findspot(
                site=rd["site"],
                coordinates=coords,
                context=rd.get("findspot_context"),
            )

        date_info = None
        if rd.get("minoan_period"):
            date_info = DateInfo(
                minoanPeriod=rd["minoan_period"],
                bceRange={"from": rd["bce_from"], "to": rd["bce_to"]} if rd.get("bce_from") is not None else None,
                notes=rd.get("date_notes"),
            )

        dims = None
        if any(rd.get(k) for k in ("dim_height", "dim_width", "dim_depth", "dim_diameter")):
            dims = Dimensions(
                height=rd.get("dim_height"),
                width=rd.get("dim_width"),
                depth=rd.get("dim_depth"),
                diameter=rd.get("dim_diameter"),
                unit=rd.get("dim_unit", "mm"),
            )

        loc = None
        if rd.get("institution") or rd.get("inventory_no"):
            loc = CurrentLocation(
                institution=rd.get("institution"),
                collection=rd.get("collection"),
                inventoryNumber=rd.get("inventory_no"),
            )

        pres = None
        if rd.get("preservation_state"):
            pres = Preservation(
                state=rd["preservation_state"],
                description=rd.get("preservation_description"),
            )

        pub = None
        if rd.get("publication_citation"):
            pub = Publication(
                citation=rd["publication_citation"],
                doi=rd.get("publication_doi"),
            )

        # Signs
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT s.*, ss.logogram_of, ss.commodity, ss.fraction_value,
                      ss.numeric_value, ss.unit as sem_unit, ss.metrological_value
               FROM signs s
               LEFT JOIN sign_semantics ss ON s.id = ss.sign_id
               WHERE s.inscription_id = ?
               ORDER BY s.sequence""",
            (rd["id"],),
        )
        sign_rows = cursor.fetchall()
        signs = []
        for sr in sign_rows:
            sd = dict(sr)
            sem = None
            if sd.get("logogram_of") or sd.get("numeric_value") is not None:
                sem = SignSemantics(
                    logogramOf=sd.get("logogram_of"),
                    commodity=sd.get("commodity"),
                    fractionValue=sd.get("fraction_value"),
                    numericValue=sd.get("numeric_value"),
                    unit=sd.get("sem_unit"),
                    metrologicalValue=sd.get("metrological_value"),
                )
            bbox = None
            if sd.get("bbox_x") is not None:
                bbox = BoundingBox(
                    x=sd["bbox_x"], y=sd["bbox_y"],
                    width=sd["bbox_w"], height=sd["bbox_h"],
                    unit=sd.get("bbox_unit", "mm"),
                )
            signs.append(SignInstance(
                sequence=sd["sequence"],
                bennettId=sd.get("bennett_id") or "",
                unicode=sd.get("unicode"),
                character=sd.get("character"),
                transliteration=sd.get("transliteration"),
                confidence=sd.get("confidence"),
                signType=sd.get("sign_type", "syllabogram"),
                siglaVariantId=sd.get("sigla_variant_id"),
                boundingBox=bbox,
                shapeClass=sd.get("shape_class"),
                isLigatureComponent=bool(sd.get("is_ligature_component")),
                ligatureOf=json.loads(sd["ligature_of"]) if sd.get("ligature_of") else None,
                erasure=bool(sd.get("erasure")),
                semantics=sem,
            ))

        # Structure
        structure = None
        cursor.execute(
            "SELECT * FROM lines WHERE inscription_id = ? ORDER BY line_number",
            (rd["id"],),
        )
        line_rows = cursor.fetchall()
        if line_rows:
            lines = []
            for lr in line_rows:
                ld = dict(lr)
                lines.append(Line(
                    number=ld["line_number"],
                    ruling=bool(ld["ruling"]),
                    damaged=bool(ld["damaged"]),
                    continuesFrom=ld.get("continues_from"),
                ))
            structure = Structure(
                side=line_rows[0]["side"] if "side" in line_rows[0] else None,
                lines=lines,
            )

        # Images
        images = []
        cursor.execute("SELECT * FROM images WHERE inscription_id = ?", (rd["id"],))
        for ir in cursor.fetchall():
            imd = dict(ir)
            images.append(ImageResource(
                iiifServiceUrl=imd.get("iiif_service_url"),
                iiifManifestUrl=imd.get("iiif_manifest_url"),
                credit=imd.get("credit"),
                license=imd.get("license"),
                type=imd.get("image_type", "photograph"),
                msiBand=imd.get("msi_band"),
                width=imd.get("width"),
                height=imd.get("height"),
            ))

        # Bibliography
        biblio = []
        cursor.execute("SELECT * FROM bibliography WHERE inscription_id = ?", (rd["id"],))
        for br in cursor.fetchall():
            bd = dict(br)
            biblio.append(BibliographyEntry(citation=bd["citation"], pages=bd.get("pages")))

        alt_ids = []
        if rd.get("alternative_ids"):
            try:
                alt_ids = json.loads(rd["alternative_ids"])
            except (json.JSONDecodeError, TypeError):
                pass

        return Inscription(
            gorilaId=rd["gorila_id"],
            alternativeIds=alt_ids,
            findspot=findspot,
            date=date_info,
            material=rd.get("material"),
            objectType=rd.get("object_type"),
            preservation=pres,
            dimensions=dims,
            currentLocation=loc,
            publication=pub,
            bibliography=biblio,
            signs=signs,
            structure=structure,
            images=images,
            source=rd.get("source"),
        )
