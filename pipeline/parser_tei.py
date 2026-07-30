"""
TEI-XML Parser — Parse Linear A inscriptions from TEI/EpiDoc XML
================================================================
Handles the Winterstein et al. (2015) TEI corpus format,
as well as any TEI files conforming to the Unified Data Schema.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional, Any

from .models import (
    Inscription, Findspot, SignInstance, Line, Structure,
    BoundingBox, ImageResource, DateInfo, Preservation,
    Publication, Dimensions, CurrentLocation, Coordinates,
    SignSemantics, WordBoundary, Lacuna, Relations,
    LinearBRelation, Paleography, BibliographyEntry,
)
from .unicode_utils import lookup_sign, normalize_bennett

logger = logging.getLogger(__name__)

# Optional lxml import
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False
    import xml.etree.ElementTree as ET
    logger.warning("lxml not available; falling back to ElementTree")


def _get_xml_parser():
    """Return appropriate XML parser."""
    if HAS_LXML:
        return etree
    return ET


def _xpath(el, expr: str, namespaces: Optional[dict] = None) -> list:
    """XPath helper that works with both lxml and ElementTree."""
    if namespaces is None:
        namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    if HAS_LXML:
        return el.xpath(expr, namespaces=namespaces)
    # ElementTree: use the namespace-prefixed expression directly
    # ET.findall() supports prefix:local notation when ns map is provided
    try:
        results = el.findall(expr, namespaces)
        if results:
            return results
    except Exception:
        pass
    # Fallback: try without namespace prefix
    simplified = expr.replace("tei:", "")
    if simplified.startswith("//"):
        simplified = "." + simplified
    results = el.findall(simplified, namespaces)
    return results if results else []


def _xpath_one(el, expr: str, namespaces: Optional[dict] = None):
    """Get first element matching XPath, or None."""
    results = _xpath(el, expr, namespaces)
    return results[0] if results else None


def _text(el) -> str:
    """Get text content of an element, stripped."""
    if el is None:
        return ""
    if hasattr(el, "text") and el.text:
        return el.text.strip()
    # lxml case
    return (el.text or "").strip()


def _attr(el, attr: str, default: Any = None) -> Any:
    """Get attribute value from an element."""
    if el is None:
        return default
    return el.get(attr, default)


def _bool_attr(el, attr: str) -> Optional[bool]:
    val = _attr(el, attr)
    if val is None:
        return None
    return val.lower() in ("true", "1", "yes")


NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def parse_tei_xml(xml_path: str) -> Optional[Inscription]:
    """Parse a single TEI-XML file into an Inscription instance."""
    path = Path(xml_path)
    if not path.exists():
        logger.error("TEI file not found: %s", xml_path)
        return None

    logger.info("Parsing TEI file: %s", xml_path)
    et = _get_xml_parser()
    try:
        tree = et.parse(str(path))
        root = tree.getroot()
    except Exception as exc:
        logger.error("XML parse error in %s: %s", xml_path, exc)
        return None

    # Decide namespace
    tag = root.tag
    ns_match = re.match(r"\{([^}]+)\}", tag)
    ns = {"tei": ns_match.group(1)} if ns_match else {"tei": "http://www.tei-c.org/ns/1.0"}

    return _parse_tei_element(root, ns, source=str(path))


def parse_tei_corpus(corpus_dir: str) -> dict[str, Inscription]:
    """
    Parse a directory of TEI-XML files.

    Files can be:
      - Individual inscription XML files (e.g., HT_1.xml)
      - A single corpus file containing multiple <TEI> elements
      - A <teiCorpus> container
    """
    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        logger.error("Corpus directory not found: %s", corpus_dir)
        return {}

    results: dict[str, Inscription] = {}

    if corpus_path.is_file():
        files = [corpus_path]
    else:
        files = sorted(corpus_path.glob("**/*.xml"))

    for xml_file in files:
        if xml_file.name.startswith("."):
            continue
        try:
            inscription = parse_tei_xml(str(xml_file))
            if inscription:
                gorila = inscription.gorilaId
                if gorila in results:
                    logger.warning("Duplicate GORILA ID %s from %s; overwriting.", gorila, xml_file)
                results[inscription.gorilaId] = inscription
        except Exception as exc:
            logger.warning("Failed to parse %s: %s", xml_file, exc)

    logger.info("Parsed %d inscriptions from TEI corpus in %s", len(results), corpus_dir)
    return results


def _parse_tei_element(root, ns: dict, source: str = "") -> Optional[Inscription]:
    """Parse a <TEI> element into an Inscription."""
    try:
        # --- GORILA ID ---
        gorila_id = ""
        idno_els = _xpath(root, ".//tei:idno[@type='GORILA']", ns)
        if idno_els:
            gorila_id = _text(idno_els[0])
        if not gorila_id:
            # Try alternative ID patterns
            idno_els = _xpath(root, ".//tei:idno", ns)
            for idno in idno_els:
                val = _text(idno)
                if re.match(r"^(HT|KH|ZA|KN|PH|MA|TY|AR|PE|PK|GO|SY|MI|AK|AP|PR|SI|VR|CR|DA|SK)\s?\d", val, re.I):
                    gorila_id = val
                    break
        if not gorila_id:
            logger.warning("No GORILA ID found in %s", source)
            gorila_id = Path(source).stem if source else "unknown"

        # --- Alternative IDs ---
        alt_ids = []
        alt_els = _xpath(root, ".//tei:idno[@type='alternative']", ns)
        for ae in alt_els:
            alt_ids.append(_text(ae))

        # --- Findspot ---
        findspot = None
        place_el = _xpath_one(root, ".//tei:origPlace[@type='findspot']/tei:placeName", ns)
        site = _text(place_el) if place_el is not None else ""
        geo_el = _xpath_one(root, ".//tei:origPlace/tei:geo", ns)
        coords = None
        if geo_el is not None and _text(geo_el):
            try:
                parts = _text(geo_el).split()
                if len(parts) >= 2:
                    coords = Coordinates(lat=float(parts[0]), lon=float(parts[1]))
            except (ValueError, IndexError):
                pass
        context_el = _xpath_one(root, ".//tei:origPlace/tei:desc", ns)
        context = _text(context_el) if context_el is not None else None
        if site:
            findspot = Findspot(site=site, coordinates=coords, context=context)

        # --- Date ---
        date_info = None
        date_el = _xpath_one(root, ".//tei:date[@type='minoanPeriod']", ns)
        if date_el is not None:
            period = _attr(date_el, "period", "")
            date_info = DateInfo(minoanPeriod=period)
            # BCE range
            bce_el = _xpath_one(root, ".//tei:date[@type='bceRange']", ns)
            if bce_el is not None:
                date_info.bceRange = {
                    "from": _attr(bce_el, "notBefore", type(None)),
                    "to": _attr(bce_el, "notAfter", type(None)),
                }
            desc_el = _xpath_one(root, ".//tei:date/tei:desc", ns)
            if desc_el is not None:
                date_info.notes = _text(desc_el)

        # --- Material ---
        material_el = _xpath_one(root, ".//tei:support/tei:material", ns)
        material = _text(material_el) if material_el is not None else None
        if not material:
            material_el = _xpath_one(root, ".//tei:material", ns)
            material = _text(material_el) if material_el is not None else None

        # --- Object type ---
        obj_type_el = _xpath_one(root, ".//tei:objectType", ns)
        obj_type = _text(obj_type_el) if obj_type_el is not None else None

        # --- Preservation ---
        preservation = None
        cond_el = _xpath_one(root, ".//tei:condition", ns)
        if cond_el is not None:
            state = _attr(cond_el, "state", "incomplete")
            desc = _text(cond_el)
            preservation = Preservation(state=state, description=desc or None)

        # --- Dimensions ---
        dimensions = None
        dim_el = _xpath_one(root, ".//tei:dimensions", ns)
        if dim_el is not None:
            dimensions = Dimensions(
                height=_num_attr(dim_el, "height"),
                width=_num_attr(dim_el, "width"),
                depth=_num_attr(dim_el, "depth"),
                unit=_attr(dim_el, "unit", "mm"),
            )

        # --- Current Location ---
        loc = None
        inst_el = _xpath_one(root, ".//tei:institution", ns)
        coll_el = _xpath_one(root, ".//tei:collection", ns)
        inv_el = _xpath_one(root, ".//tei:idno[@type='inventory']", ns)
        if inst_el is not None or inv_el is not None:
            loc = CurrentLocation(
                institution=_text(inst_el) if inst_el is not None else None,
                collection=_text(coll_el) if coll_el is not None else None,
                inventoryNumber=_text(inv_el) if inv_el is not None else None,
            )

        # --- Publication ---
        pub = None
        bibl_el = _xpath_one(root, ".//tei:biblStruct/tei:monogr", ns)
        if bibl_el is not None:
            # Try to construct a citation string
            author = _text(_xpath_one(bibl_el, ".//tei:author", ns))
            title = _text(_xpath_one(bibl_el, ".//tei:title", ns))
            imprint = _text(_xpath_one(bibl_el, ".//tei:imprint", ns))
            citation = f"{author} ({title}) {imprint}" if author else title or _text(bibl_el)
            pub = Publication(citation=citation.strip())

        # --- Bibliography ---
        biblio = []
        bibl_els = _xpath(root, ".//tei:listBibl/tei:bibl", ns)
        for be in bibl_els:
            biblio.append(BibliographyEntry(citation=_text(be)))

        # --- Signs ---
        signs = _parse_tei_signs(root, ns)

        # --- Structure ---
        structure = _parse_tei_structure(root, ns, signs)

        # --- Paleography ---
        paleo = _parse_tei_paleography(root, ns)

        # --- Images ---
        images = _parse_tei_images(root, ns)

        # --- Relations ---
        relations = None
        corresp_els = _xpath(root, ".//tei:relation", ns) or _xpath(root, ".//tei:link", ns)
        if corresp_els:
            relations = Relations()

        inscription = Inscription(
            gorilaId=gorila_id,
            alternativeIds=alt_ids,
            findspot=findspot,
            date=date_info,
            material=material,
            objectType=obj_type,
            preservation=preservation,
            dimensions=dimensions,
            currentLocation=loc,
            publication=pub,
            bibliography=biblio,
            signs=signs,
            structure=structure,
            paleography=paleo,
            images=images,
            relations=relations,
            source="tei",
        )
        return inscription

    except Exception as exc:
        logger.error("Error parsing TEI from %s: %s", source, exc, exc_info=True)
        return None


def _parse_tei_signs(root, ns: dict) -> list[SignInstance]:
    """Extract sign instances from TEI <g> elements."""
    signs: list[SignInstance] = []
    g_els = _xpath(root, ".//tei:g", ns)

    # If no <g> elements, try <seg type="sign">
    if not g_els:
        g_els = _xpath(root, ".//tei:seg[@type='sign']", ns)

    for idx, g in enumerate(g_els, start=1):
        # Bennett ID
        bennett = _attr(g, "bennett") or _attr(g, "n") or ""
        if not bennett:
            # Try to get from ana attribute
            ana = _attr(g, "ana", "")
            m = re.search(r"(?:AB|A)\s?\d{2,4}", ana)
            if m:
                bennett = m.group(0)

        if bennett:
            bennett = normalize_bennett(bennett)

        # Unicode ref
        unicode_ref = _attr(g, "ref", "")
        if unicode_ref and unicode_ref.startswith("#"):
            # Internal reference; skip
            unicode_ref = ""

        # Transliteration
        trans_el = _xpath_one(g, "./tei:seg[@type='translit']", ns)
        transliteration = _text(trans_el) if trans_el is not None else _attr(g, "translit", "")

        # Sign type
        sign_type = _attr(g, "signType", "")
        if not sign_type:
            ana = _attr(g, "ana", "")
            if "syllabogram" in ana:
                sign_type = "syllabogram"
            elif "logogram" in ana:
                sign_type = "logogram"
            elif "fraction" in ana:
                sign_type = "fraction"
            elif "numeral" in ana:
                sign_type = "numeral"
            else:
                sign_type = "syllabogram"

        # Numeric value (for numerals)
        num_val = None
        num_attr = _attr(g, "value", "")
        if num_attr:
            try:
                num_val = int(num_attr)
            except ValueError:
                pass

        semantics = None
        if sign_type == "logogram" or num_val is not None:
            semantics = SignSemantics(
                logogramOf=_attr(g, "logogramOf"),
                fractionValue=_attr(g, "fractionValue"),
                numericValue=num_val,
                commodity=_attr(g, "commodity"),
            )

        # Bounding box from zone
        bbox = None
        zone = _xpath_one(g, "./tei:zone", ns)
        if zone is not None:
            bbox = BoundingBox(
                x=float(_attr(zone, "l", 0)),
                y=float(_attr(zone, "t", 0)),
                width=float(_attr(zone, "r", 0)) - float(_attr(zone, "l", 0)),
                height=float(_attr(zone, "b", 0)) - float(_attr(zone, "t", 0)),
            )

        # Fill from lookup if available
        lookup = lookup_sign(bennett_id=bennett) if bennett else None

        sign = SignInstance(
            sequence=idx,
            bennettId=bennett or "",
            unicode=unicode_ref or (lookup.get("unicode") if lookup else None),
            character=lookup.get("character") if lookup else None,
            transliteration=transliteration or (lookup.get("transliteration") if lookup else None),
            confidence=_num_attr(g, "confidence"),
            signType=sign_type,
            boundingBox=bbox,
            semantics=semantics,
            isLigatureComponent=_attr(g, "type", "") == "ligatureComponent",
        )
        signs.append(sign)

    return signs


def _parse_tei_structure(root, ns: dict, signs: list[SignInstance]) -> Optional[Structure]:
    """Extract structural information from TEI."""
    # Lines from <lb> elements
    lines: list[Line] = []
    lb_els = _xpath(root, ".//tei:lb", ns)
    for lb in lb_els:
        n = _attr(lb, "n", str(len(lines) + 1))
        lines.append(Line(number=n))

    # Side from <div type="side">
    side_el = _xpath_one(root, ".//tei:div[@type='side']", ns)
    side = _attr(side_el, "n", "") if side_el is not None else None

    # Word boundaries from <space/> and <pc type="wordDivider">
    word_dividers: list[int] = []
    pc_els = _xpath(root, ".//tei:pc[@type='wordDivider']", ns)
    # This is approximate; we'd need sign indices

    if not lines and not side:
        return None

    return Structure(
        side=side,
        lines=lines,
        wordDividers=word_dividers,
    )


def _parse_tei_paleography(root, ns: dict) -> Optional[Paleography]:
    """Extract paleographic information."""
    hand_el = _xpath_one(root, ".//tei:handNote", ns)
    if hand_el is None:
        return None

    return Paleography(
        scribalHandId=_attr(hand_el, "xml:id"),
        scribalHandCertainty=_num_attr(hand_el, "certainty"),
        ductusNotes=_text(_xpath_one(hand_el, ".//tei:desc", ns)) or None,
        writingMethod=_attr(hand_el, "method"),
    )


def _parse_tei_images(root, ns: dict) -> list[ImageResource]:
    """Extract image references."""
    images: list[ImageResource] = []
    graphic_els = _xpath(root, ".//tei:graphic", ns)
    for g in graphic_els:
        images.append(ImageResource(
            iiifServiceUrl=_attr(g, "url"),
            width=_num_attr(g, "width"),
            height=_num_attr(g, "height"),
            type=_attr(g, "rend", "photograph"),
        ))
    return images


def _num_attr(el, attr: str, default=None):
    """Get a numeric attribute value."""
    val = el.get(attr)
    if val is None:
        return default
    try:
        return float(val) if "." in val else int(val)
    except (ValueError, TypeError):
        return default
