"""
Unicode Utilities for Linear A (Aegean Block U+10600–U+1077F)
=============================================================
Provides the canonical mapping between Bennett AB / A numbers and
Unicode code points, plus lookup / validation helpers.
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical Bennett → Unicode mapping
#
# Sources:
#   - Unicode 17.0 Aegean block (U+10600–U+1077F)
#   - GORILA / Bennett AB numbering convention
#   - SigLA sign inventory
#
# Format: (bennett_id, unicode_hex, character, transliteration, sign_type)
# ---------------------------------------------------------------------------

BENNETT_TO_UNICODE: list[tuple[str, str, str, str, str]] = [
    # Corrected mapping (Unicode standard, unicode.org names list)
    # Rebuilt 2026-08-13: fixed 144 systematic codepoint-offset errors
    ("AB 01", "U+10600", "𐘀", "", "syllabogram"),
    ("AB 02", "U+10601", "𐘁", "", "syllabogram"),
    ("AB 03", "U+10602", "𐘂", "", "syllabogram"),
    ("AB 04", "U+10603", "𐘃", "", "syllabogram"),
    ("AB 05", "U+10604", "𐘄", "", "syllabogram"),
    ("AB 06", "U+10605", "𐘅", "", "syllabogram"),
    ("AB 07", "U+10606", "𐘆", "", "syllabogram"),
    ("AB 08", "U+10607", "𐘇", "", "syllabogram"),
    ("AB 09", "U+10608", "𐘈", "", "syllabogram"),
    ("AB 10", "U+10609", "𐘉", "", "syllabogram"),
    ("AB 11", "U+1060A", "𐘊", "", "syllabogram"),
    ("AB 13", "U+1060B", "𐘋", "", "syllabogram"),
    ("AB 16", "U+1060C", "𐘌", "", "syllabogram"),
    ("AB 17", "U+1060D", "𐘍", "", "syllabogram"),
    ("AB 20", "U+1060E", "𐘎", "", "syllabogram"),
    ("AB 21", "U+1060F", "𐘏", "", "syllabogram"),
    ("AB 21f", "U+10610", "𐘐", "", "syllabogram"),
    ("AB 21m", "U+10611", "𐘑", "", "syllabogram"),
    ("AB 22", "U+10612", "𐘒", "", "syllabogram"),
    ("AB 22f", "U+10613", "𐘓", "", "syllabogram"),
    ("AB 22m", "U+10614", "𐘔", "", "syllabogram"),
    ("AB 23", "U+10615", "𐘕", "", "syllabogram"),
    ("AB 23m", "U+10616", "𐘖", "", "syllabogram"),
    ("AB 24", "U+10617", "𐘗", "", "syllabogram"),
    ("AB 26", "U+10618", "𐘘", "", "syllabogram"),
    ("AB 27", "U+10619", "𐘙", "", "syllabogram"),
    ("AB 28", "U+1061A", "𐘚", "", "syllabogram"),
    ("A 028B", "U+1061B", "𐘛", "", "syllabogram"),
    ("AB 29", "U+1061C", "𐘜", "", "syllabogram"),
    ("AB 30", "U+1061D", "𐘝", "", "syllabogram"),
    ("AB 31", "U+1061E", "𐘞", "", "syllabogram"),
    ("AB 34", "U+1061F", "𐘟", "", "syllabogram"),
    ("AB 37", "U+10620", "𐘠", "", "syllabogram"),
    ("AB 38", "U+10621", "𐘡", "", "syllabogram"),
    ("AB 39", "U+10622", "𐘢", "", "syllabogram"),
    ("AB 40", "U+10623", "𐘣", "", "syllabogram"),
    ("AB 41", "U+10624", "𐘤", "", "syllabogram"),
    ("AB 44", "U+10625", "𐘥", "", "syllabogram"),
    ("AB 45", "U+10626", "𐘦", "", "syllabogram"),
    ("AB 46", "U+10627", "𐘧", "", "syllabogram"),
    ("AB 47", "U+10628", "𐘨", "", "syllabogram"),
    ("AB 48", "U+10629", "𐘩", "", "syllabogram"),
    ("AB 49", "U+1062A", "𐘪", "", "syllabogram"),
    ("AB 50", "U+1062B", "𐘫", "", "syllabogram"),
    ("AB 51", "U+1062C", "𐘬", "", "syllabogram"),
    ("AB 53", "U+1062D", "𐘭", "", "syllabogram"),
    ("AB 54", "U+1062E", "𐘮", "", "syllabogram"),
    ("AB 55", "U+1062F", "𐘯", "", "syllabogram"),
    ("AB 56", "U+10630", "𐘰", "", "syllabogram"),
    ("AB 57", "U+10631", "𐘱", "", "syllabogram"),
    ("AB 58", "U+10632", "𐘲", "", "syllabogram"),
    ("AB 59", "U+10633", "𐘳", "", "syllabogram"),
    ("AB 60", "U+10634", "𐘴", "", "syllabogram"),
    ("AB 61", "U+10635", "𐘵", "", "syllabogram"),
    ("AB 65", "U+10636", "𐘶", "", "syllabogram"),
    ("AB 66", "U+10637", "𐘷", "", "syllabogram"),
    ("AB 67", "U+10638", "𐘸", "", "syllabogram"),
    ("AB 69", "U+10639", "𐘹", "", "syllabogram"),
    ("AB 70", "U+1063A", "𐘺", "", "syllabogram"),
    ("AB 73", "U+1063B", "𐘻", "", "syllabogram"),
    ("AB 74", "U+1063C", "𐘼", "", "syllabogram"),
    ("AB 76", "U+1063D", "𐘽", "", "syllabogram"),
    ("AB 77", "U+1063E", "𐘾", "", "syllabogram"),
    ("AB 78", "U+1063F", "𐘿", "", "syllabogram"),
    ("AB 79", "U+10640", "𐙀", "", "syllabogram"),
    ("AB 80", "U+10641", "𐙁", "", "syllabogram"),
    ("AB 81", "U+10642", "𐙂", "", "syllabogram"),
    ("AB 82", "U+10643", "𐙃", "", "syllabogram"),
    ("AB 85", "U+10644", "𐙄", "", "syllabogram"),
    ("AB 86", "U+10645", "𐙅", "", "syllabogram"),
    ("AB 87", "U+10646", "𐙆", "", "syllabogram"),
    ("A 100-102", "U+10647", "𐙇", "", "logogram"),
    ("AB 118", "U+10648", "𐙈", "", "syllabogram"),
    ("AB 120", "U+10649", "𐙉", "", "syllabogram"),
    ("A 120B", "U+1064A", "𐙊", "", "logogram"),
    ("AB 122", "U+1064B", "𐙋", "", "syllabogram"),
    ("AB 123", "U+1064C", "𐙌", "", "syllabogram"),
    ("AB 131A", "U+1064D", "𐙍", "", "syllabogram"),
    ("AB 131B", "U+1064E", "𐙎", "", "syllabogram"),
    ("A 131C", "U+1064F", "𐙏", "", "logogram"),
    ("AB 164", "U+10650", "𐙐", "", "syllabogram"),
    ("AB 171", "U+10651", "𐙑", "", "syllabogram"),
    ("AB 180", "U+10652", "𐙒", "", "syllabogram"),
    ("AB 188", "U+10653", "𐙓", "", "syllabogram"),
    ("AB 191", "U+10654", "𐙔", "", "syllabogram"),
    ("A 301", "U+10655", "𐙕", "", "logogram"),
    ("A 302", "U+10656", "𐙖", "", "logogram"),
    ("A 303", "U+10657", "𐙗", "", "logogram"),
    ("A 304", "U+10658", "𐙘", "", "logogram"),
    ("A 305", "U+10659", "𐙙", "", "logogram"),
    ("A 306", "U+1065A", "𐙚", "", "logogram"),
    ("A 307", "U+1065B", "𐙛", "", "logogram"),
    ("A 308", "U+1065C", "𐙜", "", "logogram"),
    ("A 309A", "U+1065D", "𐙝", "", "logogram"),
    ("A 309B", "U+1065E", "𐙞", "", "logogram"),
    ("A 309C", "U+1065F", "𐙟", "", "logogram"),
    ("A 310", "U+10660", "𐙠", "", "logogram"),
    ("A 311", "U+10661", "𐙡", "", "logogram"),
    ("A 312", "U+10662", "𐙢", "", "logogram"),
    ("A 313A", "U+10663", "𐙣", "", "logogram"),
    ("A 313B", "U+10664", "𐙤", "", "logogram"),
    ("A 313C", "U+10665", "𐙥", "", "logogram"),
    ("A 314", "U+10666", "𐙦", "", "logogram"),
    ("A 315", "U+10667", "𐙧", "", "logogram"),
    ("A 316", "U+10668", "𐙨", "", "logogram"),
    ("A 317", "U+10669", "𐙩", "", "logogram"),
    ("A 318", "U+1066A", "𐙪", "", "logogram"),
    ("A 319", "U+1066B", "𐙫", "", "logogram"),
    ("A 320", "U+1066C", "𐙬", "", "logogram"),
    ("A 321", "U+1066D", "𐙭", "", "logogram"),
    ("A 322", "U+1066E", "𐙮", "", "logogram"),
    ("A 323", "U+1066F", "𐙯", "", "logogram"),
    ("A 324", "U+10670", "𐙰", "", "logogram"),
    ("A 325", "U+10671", "𐙱", "", "logogram"),
    ("A 326", "U+10672", "𐙲", "", "logogram"),
    ("A 327", "U+10673", "𐙳", "", "logogram"),
    ("A 328", "U+10674", "𐙴", "", "logogram"),
    ("A 329", "U+10675", "𐙵", "", "logogram"),
    ("A 330", "U+10676", "𐙶", "", "logogram"),
    ("A 331", "U+10677", "𐙷", "", "logogram"),
    ("A 332", "U+10678", "𐙸", "", "logogram"),
    ("A 333", "U+10679", "𐙹", "", "logogram"),
    ("A 334", "U+1067A", "𐙺", "", "logogram"),
    ("A 335", "U+1067B", "𐙻", "", "logogram"),
    ("A 336", "U+1067C", "𐙼", "", "logogram"),
    ("A 337", "U+1067D", "𐙽", "", "logogram"),
    ("A 338", "U+1067E", "𐙾", "", "logogram"),
    ("A 339", "U+1067F", "𐙿", "", "logogram"),
    ("A 340", "U+10680", "𐚀", "", "logogram"),
    ("A 341", "U+10681", "𐚁", "", "logogram"),
    ("A 342", "U+10682", "𐚂", "", "logogram"),
    ("A 343", "U+10683", "𐚃", "", "logogram"),
    ("A 344", "U+10684", "𐚄", "", "logogram"),
    ("A 345", "U+10685", "𐚅", "", "logogram"),
    ("A 346", "U+10686", "𐚆", "", "logogram"),
    ("A 347", "U+10687", "𐚇", "", "logogram"),
    ("A 348", "U+10688", "𐚈", "", "logogram"),
    ("A 349", "U+10689", "𐚉", "", "logogram"),
    ("A 350", "U+1068A", "𐚊", "", "logogram"),
    ("A 351", "U+1068B", "𐚋", "", "logogram"),
    ("A 352", "U+1068C", "𐚌", "", "logogram"),
    ("A 353", "U+1068D", "𐚍", "", "logogram"),
    ("A 354", "U+1068E", "𐚎", "", "logogram"),
    ("A 355", "U+1068F", "𐚏", "", "logogram"),
    ("A 356", "U+10690", "𐚐", "", "logogram"),
    ("A 357", "U+10691", "𐚑", "", "logogram"),
    ("A 358", "U+10692", "𐚒", "", "logogram"),
    ("A 359", "U+10693", "𐚓", "", "logogram"),
    ("A 360", "U+10694", "𐚔", "", "logogram"),
    ("A 361", "U+10695", "𐚕", "", "logogram"),
    ("A 362", "U+10696", "𐚖", "", "logogram"),
    ("A 363", "U+10697", "𐚗", "", "logogram"),
    ("A 364", "U+10698", "𐚘", "", "logogram"),
    ("A 365", "U+10699", "𐚙", "", "logogram"),
    ("A 366", "U+1069A", "𐚚", "", "logogram"),
    ("A 367", "U+1069B", "𐚛", "", "logogram"),
    ("A 368", "U+1069C", "𐚜", "", "logogram"),
    ("A 369", "U+1069D", "𐚝", "", "logogram"),
    ("A 370", "U+1069E", "𐚞", "", "logogram"),
    ("A 371", "U+1069F", "𐚟", "", "logogram"),
]

# ---------------------------------------------------------------------------
# Derived lookup structures
# ---------------------------------------------------------------------------

_BENNETT_TO_UNICODE_MAP: dict[str, tuple[str, str, str, str]] = {}
_UNICODE_TO_BENNETT_MAP: dict[str, str] = {}
_BENNETT_PATTERN = re.compile(r"^(AB|A|NUM|MET|VASE|ADJ)\s?(\d{1,5}|[A-Z])$", re.IGNORECASE)

for _ben, _uni, _char, _trans, _stype in BENNETT_TO_UNICODE:
    _BENNETT_TO_UNICODE_MAP[_ben] = (_uni, _char, _trans, _stype)
    _UNICODE_TO_BENNETT_MAP[_uni] = _ben
    _UNICODE_TO_BENNETT_MAP[_char] = _ben


def normalize_bennett(bennett_id: str) -> str:
    """Normalize a Bennett ID to a canonical form (e.g., 'ab 01' → 'AB 01')."""
    m = _BENNETT_PATTERN.match(bennett_id.strip())
    if m:
        prefix = m.group(1).upper()
        num = m.group(2)
        return f"{prefix} {num}"
    # Handle already-canonical
    upper = bennett_id.strip().upper()
    if upper in _BENNETT_TO_UNICODE_MAP:
        return upper
    return bennett_id.strip()


def bennett_to_unicode(bennett_id: str) -> Optional[str]:
    """Return the Unicode hex string (e.g., 'U+10600') for a Bennett ID."""
    norm = normalize_bennett(bennett_id)
    result = _BENNETT_TO_UNICODE_MAP.get(norm)
    return result[0] if result else None


def bennett_to_character(bennett_id: str) -> Optional[str]:
    """Return the Unicode character for a Bennett ID."""
    norm = normalize_bennett(bennett_id)
    result = _BENNETT_TO_UNICODE_MAP.get(norm)
    return result[1] if result else None


def bennett_to_transliteration(bennett_id: str) -> Optional[str]:
    """Return the conventional transliteration for a Bennett ID."""
    norm = normalize_bennett(bennett_id)
    result = _BENNETT_TO_UNICODE_MAP.get(norm)
    return result[2] if result else None


def bennett_to_type(bennett_id: str) -> Optional[str]:
    """Return the sign type for a Bennett ID."""
    norm = normalize_bennett(bennett_id)
    result = _BENNETT_TO_UNICODE_MAP.get(norm)
    return result[3] if result else None


def unicode_to_bennett(unicode_ref: str) -> Optional[str]:
    """
    Map a Unicode code point (hex string like 'U+10600' or literal char) back
    to a canonical Bennett ID.
    """
    return _UNICODE_TO_BENNETT_MAP.get(unicode_ref)


def lookup_sign(bennett_id: Optional[str] = None,
                 unicode_ref: Optional[str] = None) -> Optional[dict]:
    """
    Look up a sign by either Bennett ID or Unicode reference.
    Returns a dict with 'bennettId', 'unicode', 'character',
    'transliteration', 'signType' or None.
    """
    if bennett_id:
        norm = normalize_bennett(bennett_id)
        result = _BENNETT_TO_UNICODE_MAP.get(norm)
        if result:
            return {
                "bennettId": norm,
                "unicode": result[0],
                "character": result[1],
                "transliteration": result[2],
                "signType": result[3],
            }
    if unicode_ref:
        ben = unicode_to_bennett(unicode_ref)
        if ben:
            return lookup_sign(bennett_id=ben)
    return None


def is_valid_bennett(bennett_id: str) -> bool:
    """Check if a Bennett ID exists in the mapping."""
    return normalize_bennett(bennett_id) in _BENNETT_TO_UNICODE_MAP


def is_valid_unicode(unicode_ref: str) -> bool:
    """Check if a Unicode reference maps to a known sign."""
    if unicode_ref in _UNICODE_TO_BENNETT_MAP:
        return True
    # Also check character literal
    return unicode_ref in _UNICODE_TO_BENNETT_MAP


def all_bennett_ids() -> list[str]:
    """Return all known Bennett IDs in canonical order."""
    return [t[0] for t in BENNETT_TO_UNICODE]


def write_mapping_csv(output_path: str) -> int:
    """
    Write the full Bennett → Unicode mapping as a CSV file.
    Returns the number of rows written.
    """
    fieldnames = ["bennettId", "unicode", "character", "transliteration", "signType"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ben, uni, char, trans, stype in BENNETT_TO_UNICODE:
            writer.writerow({
                "bennettId": ben,
                "unicode": uni,
                "character": char,
                "transliteration": trans,
                "signType": stype,
            })
    count = len(BENNETT_TO_UNICODE)
    logger.info("Wrote %d mapping rows to %s", count, output_path)
    return count


def validate_mapping() -> list[str]:
    """
    Run integrity checks on the mapping table.
    Returns a list of error messages (empty = clean).
    """
    errors = []
    seen_bennett = set()
    seen_unicode = set()
    for ben, uni, char, trans, stype in BENNETT_TO_UNICODE:
        # Check for duplicate Bennett IDs
        if ben in seen_bennett:
            errors.append(f"Duplicate Bennett ID: {ben}")
        seen_bennett.add(ben)
        # Check for duplicate Unicode hex
        if uni in seen_unicode:
            errors.append(f"Duplicate Unicode: {uni}")
        seen_unicode.add(uni)
        # Validate Unicode hex format
        if not re.match(r"^U\+10[67][0-9A-Fa-f]{2}$", uni):
            errors.append(f"Invalid Unicode hex: {uni} for {ben}")
        # Check character matches hex
        expected_char = chr(int(uni[2:], 16))
        if char != expected_char:
            errors.append(f"Character mismatch for {uni}: got {char!r}, expected {expected_char!r}")
    logger.info("Validation complete: %d errors", len(errors))
    return errors


# ---------------------------------------------------------------------------
# Quick CLI for mapping generation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    errors = validate_mapping()
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
    else:
        print("Mapping validation: PASSED")
    write_mapping_csv("bennett_to_unicode.csv")
