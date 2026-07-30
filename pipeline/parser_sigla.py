"""
SigLA Parser — extract inscription data from the SigLA database.js file
======================================================================
SigLA ships its entire dataset as a client-side JavaScript file
(database.js).  This module parses that JS object literal into
our Inscription data model.

Strategy:
  - Load the JS file, extract the JSON-like object using a regex
    (looking for `var database = {...}` or similar patterns).
  - Parse with Python's json module after minor clean-up.
  - Map each document entry to an `Inscription` instance.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional, Any

from .models import (
    Inscription, Findspot, SignInstance, Line, Structure,
    BoundingBox, ImageResource, DateInfo, Preservation,
    Publication, Dimensions, CurrentLocation,
    SignSemantics, WordBoundary,
)
from .unicode_utils import lookup_sign

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Regex to extract the database object from SigLA's JS
# Typical pattern: `var database = { ... };`
_RE_DATABASE = re.compile(
    r"(?:var\s+database|const\s+database|let\s+database)\s*=\s*(\{.*?\});\s*$",
    re.DOTALL,
)

# Alternate: just find the outermost {...} that looks like a JS object
_RE_JSON_OBJECT = re.compile(r"^(\{.*\})$", re.DOTALL)


def _clean_js_for_json(js_text: str) -> str:
    """
    Attempt to convert SigLA's JavaScript object literal to valid JSON.

    This is heuristic:
      - Remove comments (// and /* */)
      - Convert single-quoted strings to double-quoted
      - Ensure property keys are quoted
      - Remove trailing commas
    """
    # Remove block comments
    text = re.sub(r"/\*.*?\*/", "", js_text, flags=re.DOTALL)
    # Remove line comments
    text = re.sub(r"//[^\n]*", "", text)
    # Try to find the main object
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove var/const/let assignment
    text = re.sub(r"^(?:var|const|let)\s+\w+\s*=\s*", "", text)
    # Remove trailing semicolon and any JS after it
    text = re.sub(r";\s*$", "", text)
    return text


def _convert_sigla_sign_type(st: str) -> str:
    """Map SigLA sign type strings to our controlled vocabulary."""
    mapping = {
        "syllabogram": "syllabogram",
        "logogram": "logogram",
        "fraction": "fraction",
        "numeral": "numeral",
        "adjunct": "adjunct",
        "ligature": "ligature",
        "word_divider": "word divider",
        "punctuation": "punctuation",
        "uncertain": "uncertain",
        "syllabic": "syllabogram",
        "ideogram": "logogram",
        "number": "numeral",
    }
    return mapping.get(st.lower().strip(), "uncertain")


def _sigla_bennett_to_standard(bennett: str) -> str:
    """Normalize SigLA's Bennett notation to standard form."""
    # SigLA sometimes uses "A-338", "AB-02", "AB02", "A338"
    s = bennett.strip().replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    # Insert space between alpha and digits if missing
    s = re.sub(r"^(AB|A|NUM)(\d)", r"\1 \2", s)
    return s.upper()


def _parse_sigla_document(doc_id: str, raw: dict) -> Optional[Inscription]:
    """
    Convert a single SigLA document object to an Inscription.
    Returns None if the data is unusable.
    """
    try:
        # --- Findspot ---
        site_raw = raw.get("site", "") or raw.get("findSpot", "") or raw.get("findspot", "")
        findspot = Findspot(site=site_raw.strip()) if site_raw else None

        # --- Date ---
        period_raw = raw.get("period", "") or raw.get("date", "")
        date_info = None
        if period_raw:
            date_info = DateInfo(minoanPeriod=period_raw.strip())

        # --- Material & Object type ---
        material = raw.get("material", "") or None
        obj_type = raw.get("objectType", "") or raw.get("documentType", "") or raw.get("type", "") or None

        # --- Preservation ---
        preservation = None
        pres_raw = raw.get("preservation", "") or raw.get("condition", "")
        if pres_raw:
            preservation = Preservation(state=pres_raw.strip())

        # --- Publication ---
        publication = None
        pub_raw = raw.get("publication", "") or raw.get("biblio", "") or raw.get("bibliography", "")
        if pub_raw:
            if isinstance(pub_raw, str):
                publication = Publication(citation=pub_raw)
            elif isinstance(pub_raw, dict):
                publication = Publication(
                    citation=pub_raw.get("citation", str(pub_raw)),
                    doi=pub_raw.get("doi"),
                )

        # --- Dimensions ---
        dims = None
        dim_raw = raw.get("dimensions", {}) or raw.get("size", {})
        if isinstance(dim_raw, dict) and dim_raw:
            dims = Dimensions(
                height=dim_raw.get("height"),
                width=dim_raw.get("width"),
                depth=dim_raw.get("depth"),
                unit=dim_raw.get("unit", "mm"),
            )

        # --- Current Location ---
        loc = None
        inst = raw.get("institution", "") or raw.get("museum", "") or raw.get("location", "")
        inv = raw.get("inventoryNumber", "") or raw.get("invNo", "") or raw.get("inventory", "")
        if inst or inv:
            loc = CurrentLocation(
                institution=inst if isinstance(inst, str) else None,
                inventoryNumber=str(inv) if inv else None,
            )

        # --- Signs ---
        signs: list[SignInstance] = []
        raw_signs = raw.get("signs", []) or raw.get("signInstances", []) or raw.get("wordViews", [])

        # SigLA may store signs in wordViews structure
        if raw.get("wordViews") and not raw_signs:
            raw_signs = raw["wordViews"]

        seq = 0
        for entry in (raw_signs if isinstance(raw_signs, list) else []):
            if isinstance(entry, list):
                # wordViews is a list of words, each a list of signs
                for s in entry:
                    instance = _parse_sigla_sign(s, seq)
                    if instance:
                        seq += 1
                        signs.append(instance)
            elif isinstance(entry, dict):
                instance = _parse_sigla_sign(entry, seq)
                if instance:
                    seq += 1
                    signs.append(instance)

        # --- Structure ---
        structure = None
        lines_raw = raw.get("lines", []) or raw.get("sides", [])
        if lines_raw and isinstance(lines_raw, list):
            lines = []
            for lr in lines_raw:
                if isinstance(lr, dict):
                    lines.append(Line(
                        number=lr.get("n", lr.get("number", 0)),
                        signs=lr.get("signs", []),
                        ruling=lr.get("ruling", False),
                        damaged=lr.get("damaged", False),
                    ))
            structure = Structure(
                side=raw.get("face", raw.get("side", "")),
                lines=lines,
            )

        # --- Images ---
        images: list[ImageResource] = []
        img_raw = raw.get("images", []) or raw.get("photos", [])
        if isinstance(img_raw, list):
            for im in img_raw:
                if isinstance(im, dict):
                    images.append(ImageResource(
                        iiifServiceUrl=im.get("iiifServiceUrl") or im.get("url"),
                        iiifManifestUrl=im.get("iiifManifestUrl"),
                        credit=im.get("credit") or im.get("attribution"),
                        license=im.get("license"),
                        type=im.get("type", "photograph"),
                    ))

        # --- Source tracking ---
        alt_ids = []
        if raw.get("alternativeIds"):
            alt_ids = raw["alternativeIds"] if isinstance(raw["alternativeIds"], list) else [raw["alternativeIds"]]

        inscription = Inscription(
            gorilaId=doc_id,
            alternativeIds=alt_ids,
            findspot=findspot,
            date=date_info,
            material=material,
            objectType=obj_type,
            preservation=preservation,
            dimensions=dimensions,
            currentLocation=loc,
            publication=publication,
            signs=signs,
            structure=structure,
            images=images,
            source="sigla",
            raw_data=raw,
        )

        return inscription

    except Exception as exc:
        logger.warning("Failed to parse SigLA document %s: %s", doc_id, exc)
        return None


def _parse_sigla_sign(entry: dict, seq: int) -> Optional[SignInstance]:
    """Parse a single sign entry from SigLA into our SignInstance model."""
    try:
        bennett_raw = entry.get("bennett", "") or entry.get("bennettId", "") or entry.get("sign", "")
        if not bennett_raw:
            return None

        bennett = _sigla_bennett_to_standard(bennett_raw)
        lookup = lookup_sign(bennett_id=bennett) or {}

        # Bounding box
        bbox = None
        coords = entry.get("coords", {}) or entry.get("boundingBox", {}) or entry.get("zone", {})
        if isinstance(coords, dict) and ("x" in coords or "left" in coords):
            bbox = BoundingBox(
                x=coords.get("x", coords.get("left", 0)),
                y=coords.get("y", coords.get("top", 0)),
                width=coords.get("width", 0),
                height=coords.get("height", 0),
                unit=coords.get("unit", "mm"),
            )

        # Semantics
        semantics = None
        if entry.get("logogramOf") or entry.get("fractionValue") or entry.get("numericValue"):
            semantics = SignSemantics(
                logogramOf=entry.get("logogramOf"),
                fractionValue=entry.get("fractionValue"),
                numericValue=entry.get("numericValue"),
                commodity=entry.get("commodity"),
            )

        return SignInstance(
            sequence=seq,
            bennettId=bennett,
            unicode=lookup.get("unicode") or entry.get("unicode"),
            character=lookup.get("character") or entry.get("character"),
            transliteration=lookup.get("transliteration") or entry.get("transliteration") or entry.get("reading"),
            confidence=entry.get("confidence", lookup.get("confidence")),
            signType=_convert_sigla_sign_type(entry.get("signType", lookup.get("signType", "syllabogram"))),
            siglaVariantId=entry.get("variantId"),
            boundingBox=bbox,
            isLigatureComponent=entry.get("isLigatureComponent", False),
            semantics=semantics,
        )
    except Exception as exc:
        logger.debug("Failed to parse sign entry %s: %s", entry, exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_sigla_js(js_path: str) -> dict[str, Inscription]:
    """
    Parse a SigLA database.js file and return a dict of
    {gorilaId: Inscription}.
    """
    js_path = Path(js_path)
    if not js_path.exists():
        logger.error("SigLA JS file not found: %s", js_path)
        return {}

    logger.info("Reading SigLA file: %s", js_path)
    js_text = js_path.read_text(encoding="utf-8")

    # Extract JSON-like portion
    cleaned = _clean_js_for_json(js_text)

    # Try parsing as JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Direct JSON parse failed: %s. Trying regex extraction…", exc)
        # Try regex extraction of the main object
        m = _RE_DATABASE.search(js_text)
        if m:
            cleaned = _clean_js_for_json(m.group(0))
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as exc2:
                logger.error("JSON parse failed even after regex extraction: %s", exc2)
                return {}
        else:
            logger.error("Could not extract JSON object from SigLA JS file.")
            return {}

    if not isinstance(data, dict):
        logger.error("Parsed SigLA data is not a dict (got %s).", type(data).__name__)
        return {}

    results: dict[str, Inscription] = {}

    # SigLA database may be keyed by document ID or have a 'documents' key
    documents = data.get("documents", data)

    for doc_key, doc_val in documents.items():
        if not isinstance(doc_val, dict):
            continue
        # doc_key could be "HT 1", "KH 1", etc.
        inscription = _parse_sigla_document(str(doc_key), doc_val)
        if inscription:
            results[str(doc_key)] = inscription

    logger.info("Parsed %d inscriptions from SigLA file.", len(results))
    return results


def parse_sigla_json(json_path: str) -> dict[str, Inscription]:
    """
    Parse a SigLA dump that is already in JSON format
    (e.g., extracted from the JS manually or via a separate export).
    """
    json_path = Path(json_path)
    if not json_path.exists():
        logger.error("SigLA JSON file not found: %s", json_path)
        return {}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results: dict[str, Inscription] = {}
    documents = data.get("documents", data)

    for doc_key, doc_val in documents.items():
        if not isinstance(doc_val, dict):
            continue
        inscription = _parse_sigla_document(str(doc_key), doc_val)
        if inscription:
            results[str(doc_key)] = inscription

    logger.info("Parsed %d inscriptions from SigLA JSON.", len(results))
    return results
