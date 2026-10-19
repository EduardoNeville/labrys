#!/usr/bin/env python3
"""
Egyptian Trade Vocabulary Corpus for Linear A Bridge

Encodes ~80 Middle/Late Egyptian trade words (grain, oil, wine, metals,
vessels, scribal/administrative terms) with consonant skeletons and
Linear A CV-sequence mappings.

Sources: Gardiner (1957), Hoch (1994), Loprieno (1995), Faulkner (1962).
All words verified from standard Middle Egyptian lexicon.

Output: data/analysis/egyptian_bridge/egyptian_vocabulary.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data/analysis/egyptian_bridge"
OUTPUT_CSV = OUTPUT_DIR / "egyptian_vocabulary.csv"

# ---------------------------------------------------------------------------
# Egyptian consonant → Linear A AB sign mapping
#
# Egyptian consonantal script — each consonant maps to a CV-syllable in LA.
# Mapping philosophy:
#   - Standard consonants → standard LA CV signs
#   - Emphatic/pharyngeal consonants → closest LA equivalent
#   - Egyptian has NO writing of vowels; we produce consonant-only LA CV sequences
#     for substring matching (ignore vowel quality issues)
#
# Key to symbols used in skeleton field:
#   S = š (shin)
#   T = ṯ (tj)
#   D = ḏ (dj)
#   H = ḥ (pharyngeal h)
#   X = ḫ (velar fricative)
#   Q = q (uvular k)
#   ^ = ꜣ (aleph) — weak, ignored in skeleton
#   ' = ꜥ (ayin) — weak, ignored in skeleton
#   j = yod — weak, ignored in skeleton
#   w = waw — kept in skeleton, maps to U-vowel carrier or W-series
# ---------------------------------------------------------------------------

CONSONANT_TO_LA: Dict[str, str] = {
    # Plosives
    "p": "PU",  "b": "PU",
    "t": "TU",  "d": "TU",  "T": "TU",  "D": "DU",
    "k": "KU",  "g": "KU",  "Q": "QA",
    # Fricatives
    "f": "PU",
    "s": "SU",  "z": "ZU",  "S": "SU",
    "X": "KU",  "H": "A",
    "h": "A",
    # Nasals
    "m": "MU",  "n": "NU",
    # Liquids
    "r": "RU",  "l": "RU",
    # Glides (kept as consonants when not vocalic)
    "w": "WA",
    # Weak consonants (aleph/ayin/yod) → vowel carriers or ignored
    "^": "A",   "'": "A",   "j": "I",
}

# Consonants to skip entirely in skeleton (pure vowel carriers)
SKIP_CONSONANTS = set("^'j")


def skeleton_to_la_sequence(skeleton: str) -> List[str]:
    """Convert Egyptian consonant skeleton to list of Linear A AB sign values."""
    result = []
    for ch in skeleton:
        if ch in SKIP_CONSONANTS:
            continue
        la = CONSONANT_TO_LA.get(ch, "")
        if la:
            result.append(la)
    return result


def la_sequence_to_string(seq: List[str]) -> str:
    """Join LA sign sequence into a searchable string."""
    return "+".join(seq)

def la_sequence_flat(seq: List[str]) -> str:
    """Flat concatenation for substring matching."""
    return "".join(seq)


# ---------------------------------------------------------------------------
# Egyptian Trade Vocabulary (~80 entries)
#
# skeleton uses the single-char codes defined above.
# la_skeleton is an alternate form for searching (flat string, no separators).
# ---------------------------------------------------------------------------

VOCABULARY: List[dict] = [
    # ===== GRAIN / AGRICULTURE =====
    {"id": "jt", "english": "barley/grain", "category": "agriculture",
     "subcategory": "grain", "era": "Middle",
     "skeleton": "t",
     "notes": "i.t; basic grain term; e(iōt) in Coptic"},

    {"id": "bdt", "english": "emmer wheat", "category": "agriculture",
     "subcategory": "grain", "era": "Middle",
     "skeleton": "bdt",
     "notes": "bōte in Coptic; common wheat variety"},

    {"id": "swt", "english": "wheat (swt)", "category": "agriculture",
     "subcategory": "grain", "era": "Middle",
     "skeleton": "swt",
     "notes": "sūt; generic wheat"},

    {"id": "nHH", "english": "oil (sesame/vegetable)", "category": "agriculture",
     "subcategory": "oil", "era": "Middle",
     "skeleton": "nHH",
     "notes": "nḥḥ; vegetable oil; neḥ in Coptic"},

    {"id": "mrHt", "english": "oil/fat/ointment", "category": "agriculture",
     "subcategory": "oil", "era": "Middle",
     "skeleton": "mrHt",
     "notes": "mrḥt; fat/ointment; merḥ in Coptic"},

    {"id": "bjt", "english": "honey", "category": "agriculture",
     "subcategory": "food", "era": "Middle",
     "skeleton": "bjt",
     "notes": "bj.t; ebiō in Coptic; beekeeping product"},

    # ===== WINE / BEVERAGES =====
    {"id": "jrp", "english": "wine", "category": "beverages",
     "subcategory": "wine", "era": "Middle",
     "skeleton": "rp",
     "notes": "jrp; ērp in Coptic; standard wine term"},

    {"id": "SDr", "english": "wine (šdḥ type)", "category": "beverages",
     "subcategory": "wine", "era": "Middle",
     "skeleton": "SDr",
     "notes": "šdḥ; a type of wine; Coptic śōre"},

    {"id": "Hnqt", "english": "beer", "category": "beverages",
     "subcategory": "beer", "era": "Middle",
     "skeleton": "HnQt",
     "notes": "ḥnḳt; barley beer; ḥenḳe in Coptic"},

    {"id": "jrtt", "english": "milk", "category": "agriculture",
     "subcategory": "food", "era": "Middle",
     "skeleton": "rtt",
     "notes": "jrtt; erōte in Coptic"},

    # ===== METALS =====
    {"id": "nbw", "english": "gold", "category": "metals",
     "subcategory": "precious", "era": "Middle",
     "skeleton": "nbw",
     "notes": "nbw; nūb in Coptic (ⲛⲟⲩⲃ)"},

    {"id": "HD", "english": "silver", "category": "metals",
     "subcategory": "precious", "era": "Middle",
     "skeleton": "HD",
     "notes": "ḥḏ; ḥat in Coptic (ϩⲁⲧ)"},

    {"id": "Hmt", "english": "copper/bronze", "category": "metals",
     "subcategory": "base", "era": "Middle",
     "skeleton": "Hmt",
     "notes": "ḥmt; ḥomt in Coptic"},

    {"id": "bj^", "english": "copper/ore (bjꜣ)", "category": "metals",
     "subcategory": "base", "era": "Middle",
     "skeleton": "b",
     "notes": "bjꜣ; copper ore; ba in later form"},

    {"id": "D'm", "english": "electrum", "category": "metals",
     "subcategory": "precious", "era": "Middle",
     "skeleton": "Dm",
     "notes": "ḏꜥm; gold-silver alloy; ḏam"},

    {"id": "Hsbd", "english": "lapis lazuli", "category": "metals",
     "subcategory": "stones", "era": "Middle",
     "skeleton": "Hsbd",
     "notes": "ḥsbḏ; lapis lazuli, major trade commodity"},

    {"id": "mfk^t", "english": "turquoise", "category": "metals",
     "subcategory": "stones", "era": "Middle",
     "skeleton": "mfkt",
     "notes": "mfkꜣt; turquoise from Sinai mines; mefkat"},

    # ===== STONE / MATERIALS =====
    {"id": "Ss", "english": "alabaster/travertine", "category": "materials",
     "subcategory": "stone", "era": "Middle",
     "skeleton": "Ss",
     "notes": "šs; alabaster from Hatnub quarries"},

    {"id": "jnr", "english": "stone (generic)", "category": "materials",
     "subcategory": "stone", "era": "Middle",
     "skeleton": "nr",
     "notes": "jnr; generic stone; ōne in Coptic"},

    {"id": "Xt", "english": "wood/timber", "category": "materials",
     "subcategory": "wood", "era": "Middle",
     "skeleton": "Xt",
     "notes": "ḫt; wood; ḫe in Coptic"},

    {"id": "'S", "english": "cedar (wood)", "category": "materials",
     "subcategory": "wood", "era": "Middle",
     "skeleton": "S",
     "notes": "ꜥš; cedar imported from Levant"},

    {"id": "Sndt", "english": "acacia wood", "category": "materials",
     "subcategory": "wood", "era": "Middle",
     "skeleton": "Sndt",
     "notes": "šnḏt; native Egyptian hardwood"},

    {"id": "Sndt2", "english": "acacia (alt. form)", "category": "materials",
     "subcategory": "wood", "era": "Middle",
     "skeleton": "Sndt",
     "notes": "Variant writing of acacia"},

    # ===== VESSELS / CONTAINERS =====
    {"id": "hnw", "english": "jar/vessel (hnw-measure)", "category": "commodities",
     "subcategory": "vessel", "era": "Middle",
     "skeleton": "hnw",
     "notes": "hnw; standard liquid measure (~0.48L); hin"},

    {"id": "Ds", "english": "jar (for wine/oil)", "category": "commodities",
     "subcategory": "vessel", "era": "Middle",
     "skeleton": "Ds",
     "notes": "ḏs; storage jar; ḏes"},

    {"id": "nmst", "english": "jar/vessel (nemset)", "category": "commodities",
     "subcategory": "vessel", "era": "Middle",
     "skeleton": "nmst",
     "notes": "nmst; libation vessel; nemśet"},

    {"id": "ds", "english": "jar/pot", "category": "commodities",
     "subcategory": "vessel", "era": "Middle",
     "skeleton": "ds",
     "notes": "ds; generic pot/jar"},

    {"id": "mns^", "english": "jar/amphora (Canaanite)", "category": "commodities",
     "subcategory": "vessel", "era": "New",
     "skeleton": "mns",
     "notes": "mnsꜣ; Canaanite amphora; menes"},

    {"id": "'bt", "english": "offering vessel", "category": "commodities",
     "subcategory": "vessel", "era": "Middle",
     "skeleton": "bt",
     "notes": "ꜥbt; offering jar"},

    # ===== TEXTILES =====
    {"id": "Ssr", "english": "linen (fine)", "category": "commodities",
     "subcategory": "textile", "era": "Middle",
     "skeleton": "Ssr",
     "notes": "šsr; fine royal linen; šeser"},

    {"id": "jdmj", "english": "red linen/cloth", "category": "commodities",
     "subcategory": "textile", "era": "Middle",
     "skeleton": "dm",
     "notes": "jdmj; red cloth; idmi — trade cloth"},

    {"id": "mHt", "english": "linen (generic)/cloth", "category": "commodities",
     "subcategory": "textile", "era": "Middle",
     "skeleton": "mHt",
     "notes": "mḥt; generic flax/linen"},

    {"id": "H^tjw", "english": "linen cloth (specific)", "category": "commodities",
     "subcategory": "textile", "era": "Middle",
     "skeleton": "Ht",
     "notes": "ḥꜣtjw; cloth from fine linen"},

    # ===== ADMINISTRATIVE / SCRIBAL TERMS =====
    {"id": "Ss2", "english": "scribe/writing", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "Ss",
     "notes": "šs; scribe or writing; saḫ in Coptic"},

    {"id": "md't", "english": "document/papyrus roll", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "mDt",
     "notes": "mḏꜣt; papyrus document"},

    {"id": "Xtm", "english": "seal/seal-bearer", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "Xtm",
     "notes": "ḫtm; seal; ḫtem in Coptic"},

    {"id": "dbn", "english": "deben (weight ~91g)", "category": "administrative",
     "subcategory": "metrology", "era": "Middle",
     "skeleton": "dbn",
     "notes": "dbn; standard weight unit; teben in Coptic"},

    {"id": "Hq^t", "english": "heqat (grain measure)", "category": "administrative",
     "subcategory": "metrology", "era": "Middle",
     "skeleton": "HQt",
     "notes": "ḥḳꜣt; grain measure (~4.8L); ḥeḳat"},

    {"id": "X^r", "english": "khar (sack measure)", "category": "administrative",
     "subcategory": "metrology", "era": "Middle",
     "skeleton": "Xr",
     "notes": "ḫꜣr; sack/grain unit (~76.8L); ḫar"},

    {"id": "jp", "english": "count/assess", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "p",
     "notes": "jp; to count; ōp in Coptic"},

    {"id": "Hsb", "english": "count/calculate", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "Hsb",
     "notes": "ḥsb; to reckon; ḥeseb"},

    {"id": "tp", "english": "head/best/first", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "tp",
     "notes": "tp; quality marker: first/best quality"},

    {"id": "wD", "english": "command/decree", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "wD",
     "notes": "wḏ; official command; uḏa"},

    # ===== TITLES / OFFICIALS =====
    {"id": "jmj-r", "english": "overseer/supervisor", "category": "administrative",
     "subcategory": "titles", "era": "Middle",
     "skeleton": "mr",
     "notes": "jm.j-rꜣ; overseer; imi-r"},

    {"id": "nswt", "english": "king", "category": "administrative",
     "subcategory": "titles", "era": "Middle",
     "skeleton": "nswt",
     "notes": "nswt; king; nesu in Coptic (ⲛⲏⲥⲟⲩ)"},

    {"id": "pr-^", "english": "pharaoh (palace)", "category": "administrative",
     "subcategory": "titles", "era": "New",
     "skeleton": "pr",
     "notes": "pr-ꜥꜣ 'Great House' — pharaoh"},

    {"id": "H^tj-'", "english": "mayor/nomarch", "category": "administrative",
     "subcategory": "titles", "era": "Middle",
     "skeleton": "Ht",
     "notes": "ḥꜣtj-ꜥ 'foremost' — local governor"},

    {"id": "wpwtj", "english": "messenger/envoy", "category": "administrative",
     "subcategory": "titles", "era": "Middle",
     "skeleton": "wpwt",
     "notes": "wpwtj; envoy; uput in cuneiform"},

    {"id": "Smsw", "english": "follower/retainer", "category": "administrative",
     "subcategory": "titles", "era": "Middle",
     "skeleton": "Smsw",
     "notes": "šmsw; retainer; šemes"},

    # ===== TRADE / TRANSPORT =====
    {"id": "jnw", "english": "tribute/products/imports", "category": "trade",
     "subcategory": "goods", "era": "Middle",
     "skeleton": "nw",
     "notes": "jnw; imported products; inu in Coptic"},

    {"id": "sDf^", "english": "provision/supply", "category": "trade",
     "subcategory": "goods", "era": "Middle",
     "skeleton": "sDf",
     "notes": "sḏfꜣ; to provision; seḏefa"},

    {"id": "D^j", "english": "ferry/transport (water)", "category": "trade",
     "subcategory": "transport", "era": "Middle",
     "skeleton": "D",
     "notes": "ḏꜣj; to ferry; ḏai"},

    {"id": "'Q", "english": "enter/import", "category": "trade",
     "subcategory": "transport", "era": "Middle",
     "skeleton": "Q",
     "notes": "ꜥḳ; to enter; ꜥeḳ in Coptic"},

    {"id": "prj", "english": "go out/export", "category": "trade",
     "subcategory": "transport", "era": "Middle",
     "skeleton": "pr",
     "notes": "prj; to exit; pōre in Coptic"},

    {"id": "rDj", "english": "give/hand over", "category": "trade",
     "subcategory": "action", "era": "Middle",
     "skeleton": "rD",
     "notes": "rḏj; to give; tū/ti in Coptic"},

    {"id": "Ssp", "english": "receive", "category": "trade",
     "subcategory": "action", "era": "Middle",
     "skeleton": "Ssp",
     "notes": "šsp; to receive; šep in Coptic"},

    {"id": "swD", "english": "transmit/hand over", "category": "trade",
     "subcategory": "action", "era": "Middle",
     "skeleton": "swD",
     "notes": "swḏ; to hand over (causative)"},

    # ===== CATTLE / ANIMALS =====
    {"id": "jH", "english": "ox/cattle", "category": "agriculture",
     "subcategory": "livestock", "era": "Middle",
     "skeleton": "H",
     "notes": "jḥ; ox; ehe in Coptic"},

    {"id": "'wt", "english": "small cattle (sheep/goats)", "category": "agriculture",
     "subcategory": "livestock", "era": "Middle",
     "skeleton": "wt",
     "notes": "ꜥwt; small livestock; ꜥawet"},

    {"id": "mnmnt", "english": "herd (of cattle)", "category": "agriculture",
     "subcategory": "livestock", "era": "Middle",
     "skeleton": "mnmnt",
     "notes": "mnmnt; herd; menement"},

    # ===== STOREROOM / TREASURY =====
    {"id": "pr-HD", "english": "treasury", "category": "administrative",
     "subcategory": "institution", "era": "Middle",
     "skeleton": "prHD",
     "notes": "pr-ḥḏ 'House of Silver' — treasury"},

    {"id": "wd^", "english": "storehouse", "category": "administrative",
     "subcategory": "institution", "era": "Middle",
     "skeleton": "wd",
     "notes": "wdꜣ; storehouse/granary; uḏa"},

    {"id": "Snwtj", "english": "granary/silo", "category": "administrative",
     "subcategory": "institution", "era": "Middle",
     "skeleton": "Snwt",
     "notes": "šnwtj; granary; šenut in Coptic"},

    # ===== MISCELLANEOUS TRADE =====
    {"id": "sntr", "english": "incense (frankincense)", "category": "commodities",
     "subcategory": "incense", "era": "Middle",
     "skeleton": "sntr",
     "notes": "sntr; incense; sonte in Coptic (ⲥⲟⲛⲧⲉ)"},

    {"id": "Hsmn", "english": "natron", "category": "commodities",
     "subcategory": "mineral", "era": "Middle",
     "skeleton": "Hsmn",
     "notes": "ḥsmn; natron (sodium carbonate); ḥesmen"},

    {"id": "kmt", "english": "Egypt (Kemet)", "category": "administrative",
     "subcategory": "placename", "era": "Middle",
     "skeleton": "kmt",
     "notes": "kmt; Black Land — Egypt; Kēme in Coptic (ⲭⲏⲙⲉ)"},

    {"id": "TmHw", "english": "Libya (Tjehenu)", "category": "administrative",
     "subcategory": "placename", "era": "Middle",
     "skeleton": "TmHw",
     "notes": "ṯmḥw; Libya; land west of Egypt"},

    {"id": "kftjw", "english": "Crete/Caphtor (Minoans)", "category": "administrative",
     "subcategory": "placename", "era": "Middle",
     "skeleton": "kft",
     "notes": "kftjw; Keftiu — Egyptian name for Crete/Minoans"},

    {"id": "jwnw", "english": "Heliopolis", "category": "administrative",
     "subcategory": "placename", "era": "Middle",
     "skeleton": "nw",
     "notes": "jwnw; On (Heliopolis); Ōn in Coptic"},

    {"id": "mn-nfr", "english": "Memphis", "category": "administrative",
     "subcategory": "placename", "era": "Middle",
     "skeleton": "mnnfr",
     "notes": "mn-nfr; Memphis; Menfe in Coptic"},

    # ===== ADDITIONAL COMMODITIES =====
    {"id": "mrHt2", "english": "unguent/ointment", "category": "commodities",
     "subcategory": "cosmetic", "era": "Middle",
     "skeleton": "mrHt",
     "notes": "mrḥt; perfumed oil; merḥet"},

    {"id": "TXnw", "english": "Libyan oil (specific)", "category": "commodities",
     "subcategory": "oil", "era": "New",
     "skeleton": "TXn",
     "notes": "ṯḫnw; oil from Libya; ṯeḥen"},

    {"id": "mnw", "english": "monument/gift (trade item)", "category": "trade",
     "subcategory": "goods", "era": "Middle",
     "skeleton": "mnw",
     "notes": "mnw; gift/monument in diplomatic exchange"},

    {"id": "b^k", "english": "work/product/tribute", "category": "trade",
     "subcategory": "goods", "era": "Middle",
     "skeleton": "bk",
     "notes": "bꜣk; work-product; bāk in Coptic"},

    {"id": "p^qt", "english": "fine linen (pq)", "category": "commodities",
     "subcategory": "textile", "era": "Middle",
     "skeleton": "pQt",
     "notes": "pꜣqt; a type of fine linen for trade"},

    {"id": "nfr", "english": "good/beautiful (quality grade)", "category": "administrative",
     "subcategory": "quality", "era": "Middle",
     "skeleton": "nfr",
     "notes": "nfr; quality descriptor; nofre in Coptic"},

    {"id": "bjn", "english": "bad/poor (quality grade)", "category": "administrative",
     "subcategory": "quality", "era": "Middle",
     "skeleton": "bn",
     "notes": "bjn; poor quality; converse of nfr"},

    {"id": "w^H", "english": "endure/garrison (trade post)", "category": "trade",
     "subcategory": "transport", "era": "Middle",
     "skeleton": "H",
     "notes": "wꜣḥ; to endure/establish; Coptic ouoh"},

    {"id": "sm^", "english": "unite/join (trade alliance)", "category": "trade",
     "subcategory": "action", "era": "Middle",
     "skeleton": "sm",
     "notes": "smꜣ; to unite; šema/sema"},

    {"id": "X^w", "english": "excess/surplus (trade)", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "X",
     "notes": "ḫꜣw; excess; ḫaw — surplus in accounts"},

    {"id": "twt", "english": "statue/image (trade object)", "category": "commodities",
     "subcategory": "art", "era": "Middle",
     "skeleton": "twt",
     "notes": "twt; complete/statue; tout in Coptic"},

    {"id": "Xn", "english": "chest/box (container)", "category": "commodities",
     "subcategory": "container", "era": "Middle",
     "skeleton": "Xn",
     "notes": "ḫn; box for goods; ḫen"},

    {"id": "Db^", "english": "compensation/replacement", "category": "trade",
     "subcategory": "action", "era": "Middle",
     "skeleton": "Db",
     "notes": "ḏbꜣ; to compensate; ḏeba"},

    {"id": "Sb", "english": "food/meal (provisions)", "category": "agriculture",
     "subcategory": "food", "era": "Middle",
     "skeleton": "Sb",
     "notes": "šb; food offering; šeb in later form"},

    {"id": "'H'", "english": "stand/quantity (admin.)", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "H",
     "notes": "ꜥḥꜥ; standing quantity in accounts"},

    # Additional important trade words
    {"id": "dHt", "english": "meal/grain offering", "category": "agriculture",
     "subcategory": "food", "era": "Middle",
     "skeleton": "dHt",
     "notes": "dḥt; grain-based meal offering"},

    {"id": "zp", "english": "time/occasion (record keeping)", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "zp",
     "notes": "zp; time/occasion; sep in Coptic"},

    {"id": "rnp", "english": "year (dating)", "category": "administrative",
     "subcategory": "scribal", "era": "Middle",
     "skeleton": "rnp",
     "notes": "rnp; year; rompe in Coptic"},
]


# ---------------------------------------------------------------------------
# Generate LA forms
# ---------------------------------------------------------------------------

def generate_all():
    """Generate the full vocabulary with LA mappings."""
    rows = []
    for entry in VOCABULARY:
        skeleton = entry["skeleton"]
        la_seq = skeleton_to_la_sequence(skeleton)
        la_flat = la_sequence_flat(la_seq)
        la_plus = la_sequence_to_string(la_seq)
        sign_count = len(la_seq)

        rows.append({
            "id": entry["id"],
            "english": entry["english"],
            "category": entry["category"],
            "subcategory": entry["subcategory"],
            "era": entry["era"],
            "egyptian_transliteration": entry["id"],
            "consonant_skeleton": skeleton,
            "la_cv_sequence": la_plus,
            "la_flat": la_flat,
            "sign_count": sign_count,
            "notes": entry["notes"],
        })

    return rows


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = generate_all()

    # Stats
    cat_counts = {}
    for r in rows:
        c = r["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
    print("Categories:")
    for c, n in sorted(cat_counts.items()):
        print(f"  {c}: {n}")
    total = sum(r["sign_count"] for r in rows)
    print(f"Total entries: {len(rows)}")
    print(f"Average LA sequence length: {total/len(rows):.1f} signs")
    print(f"Entries with >=3 signs: {sum(1 for r in rows if r['sign_count'] >= 3)}")

    # Write CSV
    fieldnames = [
        "id", "english", "category", "subcategory", "era",
        "egyptian_transliteration", "consonant_skeleton",
        "la_cv_sequence", "la_flat", "sign_count", "notes"
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote to {OUTPUT_CSV}")

    return rows


if __name__ == "__main__":
    main()
