"""
Exporters — Convert Inscription objects to standard formats
============================================================
Supports:
  - JSON-LD (one file per text + collection manifest)
  - TEI-XML (one file per text, following the Unified Data Schema)
  - Plain text (AB transliteration strings, one per line)
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .models import Inscription, SignInstance, Line, Structure, Findspot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSON-LD constants
# ---------------------------------------------------------------------------

JSONLD_CONTEXT = {
    "@context": {
        "la": "https://schema.lineara.org/ns/",
        "iiif": "http://iiif.io/api/presentation/3/context.json",
        "dcterms": "http://purl.org/dc/terms/",
        "schema": "https://schema.org/",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "gorilaId": {"@id": "la:gorilaId"},
        "signs": {"@id": "la:signs", "@container": "@list"},
        "images": {"@id": "la:images", "@container": "@list"},
        "bennettId": "la:bennettId",
        "unicode": "la:unicodeCodePoint",
        "transliteration": "la:transliteration",
        "findspot": "la:findspot",
        "site": "la:site",
        "coordinates": "la:coordinates",
        "date": "la:date",
        "minoanPeriod": "la:minoanPeriod",
        "material": "la:material",
        "objectType": "la:objectType",
        "preservation": "la:preservation",
        "structure": "la:structure",
    }
}


# ---------------------------------------------------------------------------
# JSON-LD Exporter
# ---------------------------------------------------------------------------

def export_jsonld(inscription: Inscription,
                  output_dir: str,
                  base_uri: str = "https://data.lineara.org/inscription") -> str:
    """
    Export a single inscription as a JSON-LD file.

    Args:
        inscription: the Inscription object
        output_dir: directory to write the file
        base_uri: base URI for @id generation

    Returns:
        Path to the written file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_id = _sanitize_id(inscription.gorilaId)
    filename = f"{safe_id}.jsonld"
    filepath = output_dir / filename

    doc = _build_jsonld(inscription, base_uri)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    logger.info("Exported JSON-LD: %s", filepath)
    return str(filepath)


def export_jsonld_collection(inscriptions: list[Inscription],
                              output_dir: str,
                              base_uri: str = "https://data.lineara.org") -> str:
    """
    Export a JSON-LD collection manifest containing all inscriptions.

    Args:
        inscriptions: list of Inscription objects
        output_dir: directory to write the manifest
        base_uri: base URI

    Returns:
        Path to the manifest file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "collection.jsonld"

    # Also export individual files
    for ins in inscriptions:
        export_jsonld(ins, str(output_dir), f"{base_uri}/inscription")

    members = []
    for ins in inscriptions:
        safe_id = _sanitize_id(ins.gorilaId)
        members.append({
            "@type": "linearA:Inscription",
            "@id": f"{base_uri}/inscription/{safe_id}",
            "gorilaId": ins.gorilaId,
            "title": f"Linear A Inscription {ins.gorilaId}",
        })

    manifest = {
        "@context": [
            JSONLD_CONTEXT["@context"],
            {"@base": base_uri},
        ],
        "@id": f"{base_uri}/collection",
        "@type": "linearA:Collection",
        "title": "Labrys Linear A Corpus",
        "description": f"Collection of {len(inscriptions)} Linear A inscriptions "
                       f"exported from the Labrys pipeline on {datetime.utcnow().isoformat()}Z.",
        "totalItems": len(inscriptions),
        "members": members,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info("Exported JSON-LD collection manifest: %s", manifest_path)
    return str(manifest_path)


def _build_jsonld(ins: Inscription, base_uri: str) -> dict:
    """Build the JSON-LD representation of an inscription."""
    safe_id = _sanitize_id(ins.gorilaId)

    doc = {
        "@context": JSONLD_CONTEXT["@context"],
        "@id": f"{base_uri}/{safe_id}",
        "@type": "linearA:Inscription",
        "gorilaId": ins.gorilaId,
    }

    # Alternative IDs
    if ins.alternativeIds:
        doc["alternativeIds"] = ins.alternativeIds

    # Findspot
    if ins.findspot:
        fs = {
            "site": ins.findspot.site,
        }
        if ins.findspot.coordinates:
            fs["coordinates"] = {
                "lat": ins.findspot.coordinates.lat,
                "lon": ins.findspot.coordinates.lon,
            }
        if ins.findspot.context:
            fs["context"] = ins.findspot.context
        doc["findspot"] = fs

    # Date
    if ins.date:
        d = {"minoanPeriod": ins.date.minoanPeriod}
        if ins.date.bceRange:
            d["bceRange"] = ins.date.bceRange
        if ins.date.notes:
            d["notes"] = ins.date.notes
        doc["date"] = d

    # Material, object type
    if ins.material:
        doc["material"] = ins.material
    if ins.objectType:
        doc["objectType"] = ins.objectType

    # Preservation
    if ins.preservation:
        doc["preservation"] = {
            "state": ins.preservation.state,
        }
        if ins.preservation.description:
            doc["preservation"]["description"] = ins.preservation.description

    # Dimensions
    if ins.dimensions:
        dims = {"unit": ins.dimensions.unit}
        for attr in ("height", "width", "depth", "diameter"):
            val = getattr(ins.dimensions, attr, None)
            if val is not None:
                dims[attr] = val
        doc["dimensions"] = dims

    # Current location
    if ins.currentLocation:
        loc = {}
        for attr in ("institution", "collection", "inventoryNumber"):
            val = getattr(ins.currentLocation, attr, None)
            if val:
                loc[attr] = val
        if loc:
            doc["currentLocation"] = loc

    # Publication
    if ins.publication:
        pub = {"citation": ins.publication.citation}
        if ins.publication.doi:
            pub["doi"] = ins.publication.doi
        doc["publication"] = pub

    # Bibliography
    if ins.bibliography:
        doc["bibliography"] = [
            {"citation": be.citation, "pages": be.pages}
            for be in ins.bibliography if be.citation
        ]

    # Signs
    if ins.signs:
        doc["signs"] = [_sign_to_jsonld(s) for s in ins.signs]

    # Structure
    if ins.structure:
        doc["structure"] = _structure_to_jsonld(ins.structure)

    # Paleography
    if ins.paleography:
        paleo = {}
        for attr in ("scribalHandId", "scribalHandCertainty", "ductusNotes", "writingMethod"):
            val = getattr(ins.paleography, attr, None)
            if val is not None:
                paleo[attr] = val
        if paleo:
            doc["paleography"] = paleo

    # Relations
    if ins.relations:
        rels = {}
        if ins.relations.linearB:
            rels["linearB"] = [
                {"dmicId": lb.dmicId, "phoneticValue": lb.phoneticValue}
                for lb in ins.relations.linearB
            ]
        if rels:
            doc["relations"] = rels

    # Images
    if ins.images:
        doc["images"] = [
            {
                "iiifServiceUrl": img.iiifServiceUrl,
                "iiifManifestUrl": img.iiifManifestUrl,
                "credit": img.credit,
                "license": img.license,
                "type": img.type,
                "msiBand": img.msiBand,
                "width": img.width,
                "height": img.height,
            }
            for img in ins.images
        ]

    # Source tracking
    if ins.source:
        doc["source"] = ins.source

    return doc


def _sign_to_jsonld(s: SignInstance) -> dict:
    """Convert a SignInstance to JSON-LD representation."""
    obj = {
        "sequence": s.sequence,
        "bennettId": s.bennettId,
    }
    if s.unicode:
        obj["unicode"] = s.unicode
    if s.character:
        obj["character"] = s.character
    if s.transliteration:
        obj["transliteration"] = s.transliteration
    if s.confidence is not None:
        obj["confidence"] = s.confidence
    if s.signType:
        obj["signType"] = s.signType
    if s.siglaVariantId:
        obj["siglaVariantId"] = s.siglaVariantId
    if s.boundingBox:
        bb = s.boundingBox
        obj["boundingBox"] = {
            "x": bb.x, "y": bb.y,
            "width": bb.width, "height": bb.height,
            "unit": bb.unit,
        }
    if s.shapeClass:
        obj["shapeClass"] = s.shapeClass
    if s.isLigatureComponent:
        obj["isLigatureComponent"] = True
    if s.ligatureOf:
        obj["ligatureOf"] = s.ligatureOf
    if s.erasure:
        obj["erasure"] = True
    if s.correction:
        obj["correction"] = {
            "original": s.correction.original,
            "correctedTo": s.correction.correctedTo,
        }
    if s.semantics:
        sem = {}
        if s.semantics.logogramOf:
            sem["logogramOf"] = s.semantics.logogramOf
        if s.semantics.commodity:
            sem["commodity"] = s.semantics.commodity
        if s.semantics.fractionValue:
            sem["fractionValue"] = s.semantics.fractionValue
        if s.semantics.numericValue is not None:
            sem["numericValue"] = s.semantics.numericValue
        if s.semantics.unit:
            sem["unit"] = s.semantics.unit
        if sem:
            obj["semantics"] = sem
    return obj


def _structure_to_jsonld(st: Structure) -> dict:
    """Convert Structure to JSON-LD."""
    obj = {}
    if st.side:
        obj["side"] = st.side
    if st.lines:
        obj["lines"] = [
            {
                "number": l.number,
                "ruling": l.ruling,
                "damaged": l.damaged,
            }
            for l in st.lines
        ]
    if st.words:
        obj["words"] = [
            {"signSequences": w.signSequences}
            for w in st.words
        ]
    if st.wordDividers:
        obj["wordDividers"] = st.wordDividers
    if st.lacunae:
        obj["lacunae"] = [
            {"signs": l.signs, "position": l.position}
            for l in st.lacunae
        ]
    return obj


# ---------------------------------------------------------------------------
# TEI-XML Exporter
# ---------------------------------------------------------------------------

def export_tei_xml(inscription: Inscription,
                   output_dir: str,
                   schema_location: str = "linear-a-odd.rng") -> str:
    """
    Export a single inscription as TEI-XML conforming to the schema.

    Args:
        inscription: the Inscription object
        output_dir: directory to write the file
        schema_location: RELAX NG schema file for ODD validation

    Returns:
        Path to the written file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_id = _sanitize_id(inscription.gorilaId)
    filename = f"{safe_id}.xml"
    filepath = output_dir / filename

    xml = _build_tei_xml(inscription, schema_location)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml)

    logger.info("Exported TEI-XML: %s", filepath)
    return str(filepath)


def _build_tei_xml(ins: Inscription, schema_location: str) -> str:
    """Build the TEI-XML string for an inscription."""
    lines = []
    indent = "  "

    # XML declaration and ODD reference
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<?xml-model href="{schema_location}" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>')
    lines.append('<TEI xmlns="http://www.tei-c.org/ns/1.0">')

    # teiHeader
    lines.append(f"{indent}<teiHeader>")

    # fileDesc
    lines.append(f"{indent * 2}<fileDesc>")
    lines.append(f"{indent * 3}<titleStmt>")
    lines.append(f"{indent * 4}<title>Linear A Inscription {_xml_esc(ins.gorilaId)}</title>")
    lines.append(f"{indent * 4}<idno type=\"GORILA\">{_xml_esc(ins.gorilaId)}</idno>")
    for alt in ins.alternativeIds:
        lines.append(f"{indent * 4}<idno type=\"alternative\">{_xml_esc(alt)}</idno>")
    lines.append(f"{indent * 3}</titleStmt>")

    # sourceDesc (findspot)
    lines.append(f"{indent * 3}<sourceDesc>")
    if ins.findspot:
        lines.append(f"{indent * 4}<origPlace type=\"findspot\">")
        lines.append(f"{indent * 5}<placeName>{_xml_esc(ins.findspot.site)}</placeName>")
        if ins.findspot.coordinates:
            lat = ins.findspot.coordinates.lat
            lon = ins.findspot.coordinates.lon
            lines.append(f"{indent * 5}<geo>{lat} {lon}</geo>")
        if ins.findspot.context:
            lines.append(f"{indent * 5}<desc>{_xml_esc(ins.findspot.context)}</desc>")
        lines.append(f"{indent * 4}</origPlace>")
    lines.append(f"{indent * 3}</sourceDesc>")
    lines.append(f"{indent * 2}</fileDesc>")

    # profileDesc
    lines.append(f"{indent * 2}<profileDesc>")
    lines.append(f"{indent * 3}<creation>")
    if ins.date:
        period = ins.date.minoanPeriod or "Uncertain"
        lines.append(f"{indent * 4}<date type=\"minoanPeriod\" period=\"{_xml_esc(period)}\">")
        if ins.date.notes:
            lines.append(f"{indent * 5}<desc>{_xml_esc(ins.date.notes)}</desc>")
        lines.append(f"{indent * 4}</date>")
        if ins.date.bceRange:
            bce_from = ins.date.bceRange.get("from", "")
            bce_to = ins.date.bceRange.get("to", "")
            lines.append(f"{indent * 4}<date type=\"bceRange\" notBefore=\"{bce_from}\" notAfter=\"{bce_to}\"/>")
    else:
        lines.append(f"{indent * 4}<date type=\"minoanPeriod\" period=\"Uncertain\"/>")
    lines.append(f"{indent * 3}</creation>")
    lines.append(f"{indent * 3}<langUsage><language ident=\"emn\">Minoan</language></langUsage>")
    lines.append(f"{indent * 2}</profileDesc>")

    # physDesc (optional)
    has_phys = ins.material or ins.objectType or ins.dimensions or ins.preservation
    if has_phys:
        lines.append(f"{indent * 2}<physDesc>")
        if ins.material or ins.objectType:
            lines.append(f"{indent * 3}<objectDesc>")
            if ins.objectType:
                lines.append(f"{indent * 4}<objectType>{_xml_esc(ins.objectType)}</objectType>")
            if ins.material:
                lines.append(f"{indent * 4}<supportDesc><support><material>{_xml_esc(ins.material)}</material></support></supportDesc>")
            if ins.dimensions:
                d = ins.dimensions
                dim_str = f"unit=\"{_xml_esc(d.unit)}\""
                parts = []
                for attr in ("height", "width", "depth", "diameter"):
                    val = getattr(d, attr, None)
                    if val is not None:
                        parts.append(f"{attr}=\"{val}\"")
                if parts:
                    lines.append(f"{indent * 4}<dimensions {dim_str} {' '.join(parts)}/>")
            lines.append(f"{indent * 3}</objectDesc>")
        if ins.preservation:
            lines.append(f"{indent * 3}<condition state=\"{_xml_esc(ins.preservation.state)}\">")
            if ins.preservation.description:
                lines.append(f"{indent * 4}<p>{_xml_esc(ins.preservation.description)}</p>")
            lines.append(f"{indent * 3}</condition>")
        lines.append(f"{indent * 2}</physDesc>")

    # msIdentifier (current location)
    if ins.currentLocation and (ins.currentLocation.institution or ins.currentLocation.inventoryNumber):
        lines.append(f"{indent * 2}<msIdentifier>")
        if ins.currentLocation.institution:
            lines.append(f"{indent * 3}<institution>{_xml_esc(ins.currentLocation.institution)}</institution>")
        if ins.currentLocation.collection:
            lines.append(f"{indent * 3}<collection>{_xml_esc(ins.currentLocation.collection)}</collection>")
        if ins.currentLocation.inventoryNumber:
            lines.append(f"{indent * 3}<idno type=\"inventory\">{_xml_esc(ins.currentLocation.inventoryNumber)}</idno>")
        lines.append(f"{indent * 2}</msIdentifier>")

    lines.append(f"{indent}</teiHeader>")

    # text body
    lines.append(f"{indent}<text>")
    lines.append(f"{indent * 2}<body>")
    lines.append(f"{indent * 3}<ab n=\"1\">")

    # Render signs with line breaks
    current_line = 1
    if ins.structure and ins.structure.lines:
        line_map = {i + 1: l for i, l in enumerate(ins.structure.lines)}
    else:
        line_map = {}

    for i, sign in enumerate(ins.signs):
        # Check if we need a line break
        if line_map and i < len(line_map):
            line = line_map.get(i + 1)
            if line and line.number != current_line:
                lines.append(f"{indent * 4}<lb n=\"{line.number}\"/>")
                current_line = line.number

        attrs = ""
        if sign.bennettId:
            attrs += f' bennett="{_xml_esc(sign.bennettId)}"'
        if sign.unicode:
            attrs += f' ref="{_xml_esc(sign.unicode)}"'
        if sign.signType:
            attrs += f' signType="{_xml_esc(sign.signType)}"'
        if sign.confidence is not None:
            attrs += f' confidence="{sign.confidence}"'

        # Check for word divider (space)
        if ins.structure and sign.sequence in ins.structure.wordDividers:
            lines.append(f"{indent * 4}<space unit=\"chars\" quantity=\"1\"/>")

        # Numeral handling
        if sign.signType == "numeral" and sign.semantics and sign.semantics.numericValue is not None:
            lines.append(f"{indent * 4}<g{attrs}><num value=\"{sign.semantics.numericValue}\"/><seg type=\"translit\">{_xml_esc(sign.transliteration or str(sign.semantics.numericValue))}</seg></g>")
        else:
            trans = _xml_esc(sign.transliteration) if sign.transliteration else ""
            if trans:
                lines.append(f"{indent * 4}<g{attrs}><seg type=\"translit\">{trans}</seg></g>")
            else:
                lines.append(f"{indent * 4}<g{attrs}/>")

    lines.append(f"{indent * 3}</ab>")
    lines.append(f"{indent * 2}</body>")
    lines.append(f"{indent}</text>")
    lines.append("</TEI>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Plain Text Exporter
# ---------------------------------------------------------------------------

def export_plaintext(inscriptions: list[Inscription],
                     output_path: str,
                     format: str = "ab") -> str:
    """
    Export inscriptions as plain text.

    Args:
        inscriptions: list of Inscription objects
        output_path: destination file path
        format: 'ab' for Bennett IDs, 'translit' for transliteration,
                'unicode' for Unicode characters, 'mixed' for abbreviated

    Returns:
        Path to the written file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines_out = []
    for ins in inscriptions:
        if format == "ab":
            text = " ".join(s.bennettId for s in ins.signs if s.bennettId)
        elif format == "translit":
            text = " ".join(s.transliteration if s.transliteration else s.bennettId
                           for s in ins.signs)
        elif format == "unicode":
            text = " ".join(s.character if s.character else s.bennettId
                           for s in ins.signs)
        elif format == "mixed":
            parts = []
            for s in ins.signs:
                if s.character:
                    parts.append(s.character)
                elif s.transliteration:
                    parts.append(f"[{s.transliteration}]")
                else:
                    parts.append(s.bennettId)
            text = " ".join(parts)
        else:
            text = " ".join(s.bennettId for s in ins.signs if s.bennettId)

        lines_out.append(f"{ins.gorilaId}: {text}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")

    logger.info("Exported %d inscriptions as plain text to %s", len(inscriptions), output_path)
    return str(output_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_id(gorila_id: str) -> str:
    """Convert a GORILA ID like 'HT 1' to a safe filename like 'HT_1'."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", gorila_id.strip())


def _xml_esc(text: Any) -> str:
    """Escape text for XML content."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text
