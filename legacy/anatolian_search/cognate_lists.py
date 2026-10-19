#!/usr/bin/env python3
"""
Anatolian Cognate Lists — Luwian (Cuneiform + Hieroglyphic) and Lycian vocabulary.

Encodes:
  - Common nouns (agriculture, trade goods, kinship, body parts, numbers 1-10)
  - Verb roots
  - Grammatical suffixes / particles
  - Toponym-related vocabulary
  - Phoneme-to-Linear-A-AB mapping specific to Anatolian languages

Sources:
  - Melchert, H.C. (1993) *Cuneiform Luvian Lexicon*
  - Melchert, H.C. (2004) *A Dictionary of the Lycian Language*
  - Kloekhorst, A. (2008) *Etymological Dictionary of the Hittite Inherited Lexicon*
  - Payne, A. (2010) *Hieroglyphic Luwian* (2nd ed.)
  - Yakubovich, I. (2010) *Sociolinguistics of the Luvian Language*
  - Neumann, G. (2007) *Glossar des Lykischen*
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional

# =============================================================================
# Phoneme → Linear A AB sign mapping (Anatolian-specific)
#
# Anatolian languages (Luwian, Lycian) have:
#   - 4 vowels: a, i, u, e (no /o/ — aligns with Tyrsenian pattern!)
#   - Voiceless stops: p, t, k, kʷ (labiovelar)
#   - No phonemic voiced stops (no /b, d, g/ distinction)
#   - Fricatives: s, š (=/ʃ/), ḫ (=/ħ/ or /x/)
#   - Sonorants: m, n, l, r, w, y
#   - Lycian additionally has nasalized vowels (ẽ, ã, ũ)
#
# The Linear A AB syllabary has CV structure. We map Anatolian forms via:
#   C + V → AB_CV  (direct)
#   C + C → C(V) approximation (insert default vowel or drop)
#   ḫ → often drops / maps to vowel
#   š → maps to S-series (SA, SE, SI, SO, SU)
# =============================================================================

# Canonical AB signs (capitalized, no subscripts for matching)
AB_SIGNS: Dict[str, Dict[str, str]] = {
    # Consonant + vowel
    "p":  {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "b":  {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "t":  {"a": "TA", "e": "TE", "i": "TI", "o": "TO", "u": "TU", "default": "TU"},
    "d":  {"a": "DA", "e": "DE", "i": "DI", "o": "DO", "u": "DU", "default": "DU"},
    "k":  {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "g":  {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "kʷ": {"a": "QA", "e": "QE", "i": "QI", "o": "QO", "u": "QU", "default": "QU"},
    "kw": {"a": "QA", "e": "QE", "i": "QI", "o": "QO", "u": "QU", "default": "QU"},
    "q":  {"a": "QA", "e": "QE", "i": "QI", "o": "QO", "u": "QU", "default": "QU"},
    "s":  {"a": "SA", "e": "SE", "i": "SI", "o": "SO", "u": "SU", "default": "SU"},
    "š":  {"a": "SA", "e": "SE", "i": "SI", "o": "SO", "u": "SU", "default": "SU"},
    "z":  {"a": "ZA", "e": "ZE", "i": "ZI", "o": "ZO", "u": "ZU", "default": "ZU"},
    "m":  {"a": "MA", "e": "ME", "i": "MI", "o": "MO", "u": "MU", "default": "MU"},
    "n":  {"a": "NA", "e": "NE", "i": "NI", "o": "NO", "u": "NU", "default": "NU"},
    "l":  {"a": "LA", "e": "LE", "i": "LI", "o": "LO", "u": "LU", "default": "LU"},
    "r":  {"a": "RA", "e": "RE", "i": "RI", "o": "RO", "u": "RU", "default": "RU"},
    "w":  {"a": "WA", "e": "WE", "i": "WI", "o": "WO", "u": "WU", "default": "WA"},
    "y":  {"a": "JA", "e": "JE", "i": "JI", "o": "JO", "u": "JU", "default": "JA"},
    "j":  {"a": "JA", "e": "JE", "i": "JI", "o": "JO", "u": "JU", "default": "JA"},
    "x":  {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    # ḫ (laryngeal) — typically drops, or maps to vowel
    "ħ":  {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": "A"},
    "ḫ":  {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": "A"},
    "h":  {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": ""},
    # Vowel-only signs
    "a":  {"": "A"},
    "e":  {"": "E"},
    "i":  {"": "I"},
    "o":  {"": "O"},
    "u":  {"": "U"},
}

# Lycian-specific: nasalized vowels map to regular vowels
LYCIAN_VOWEL_MAP: Dict[str, str] = {
    "ã": "a", "ẽ": "e", "ĩ": "i", "ũ": "u", "õ": "o",
    "â": "a", "ê": "e", "î": "i", "û": "u", "ô": "o",
    "ā": "a", "ē": "e", "ī": "i", "ū": "u", "ō": "o",
}

# =============================================================================
# Phoneme string → Linear A AB sequence converter
# =============================================================================

def phoneme_to_ab(phoneme_str: str, language: str = "luwian") -> Tuple[str, str]:
    """
    Convert a phoneme string to its Linear A AB approximation.
    Returns (ab_sequence, method) where method describes the conversion strategy.

    Handles:
      - CV, V, VC sequences
      - Consonant clusters via vowel insertion
      - Laryngeal (ḫ/ħ) → vowel or drop
      - Lycian nasalized vowels → regular vowels
    """
    # Clean up: remove stress marks, normalize
    s = phoneme_str.lower().strip().rstrip("-")
    if language == "lycian":
        # Normalize nasalized/long vowels
        for k, v in LYCIAN_VOWEL_MAP.items():
            s = s.replace(k, v)

    ab_parts: List[str] = []
    i = 0
    n = len(s)

    # Extended mapping: consonant clusters
    consonant = ""

    while i < n:
        ch = s[i]

        # Skip unknown chars
        if ch not in "abcdeéfghijklmnopqrstuvwxyzšħḫʷθðṣṭḍŋ'" and ch not in "āēīōūãẽĩũâêîôû":
            i += 1
            continue

        # Check for digraph kʷ / kw
        if ch == "k" and i + 1 < n and s[i + 1] in ("ʷ", "w"):
            consonant = "kʷ"
            i += 2
        elif ch == "g" and i + 1 < n and s[i + 1] in ("ʷ", "w"):
            consonant = "kʷ"
            i += 2
        elif ch in "ptkbdgqszmnlrwjyxšħḫ":
            consonant = ch
            i += 1
        elif ch in "aeiou":
            # Vowel without consonant — vowel-only sign
            vowel_map = AB_SIGNS.get(ch, {})
            ab_parts.append(vowel_map.get("", ch.upper()))
            i += 1
        else:
            # Not a recognized consonant or vowel
            i += 1
            continue

        # After getting a consonant, look for following vowel
        if consonant:
            if i < n and s[i] in "aeiouāēīōūãẽĩũ":
                vowel = s[i]
                # Normalize long/nasalized vowels
                if vowel in "āēīōūãẽĩũâêîôû":
                    vowel = LYCIAN_VOWEL_MAP.get(vowel, vowel)
                cons_map = AB_SIGNS.get(consonant, {})
                ab_parts.append(cons_map.get(vowel, cons_map.get("default", consonant.upper() + vowel.upper())))
                i += 1
            else:
                # Consonant with no following vowel — use default vowel or drop
                if consonant in "ħḫh":
                    # Laryngeal: drop it
                    pass
                elif consonant in "nmrl":
                    # Sonorant coda — append with default vowel
                    cons_map = AB_SIGNS.get(consonant, {})
                    ab_parts.append(cons_map.get("default", consonant.upper() + "U"))
                else:
                    # Stop coda — drop or use default
                    cons_map = AB_SIGNS.get(consonant, {})
                    default = cons_map.get("default", "")
                    if default:
                        ab_parts.append(default)
            consonant = ""

    result = "".join(ab_parts) if ab_parts else s.upper()
    return result, "direct"


def word_to_ab_sequence(word: str, language: str = "luwian") -> str:
    """Convenience: convert a full word to AB sequence."""
    seq, _ = phoneme_to_ab(word, language)
    return seq


# =============================================================================
# Luwian Vocabulary (Cuneiform Luwian, attested ~1600-1200 BCE)
# =============================================================================

LUWIAN_NOUNS: Dict[str, List[Tuple[str, str, str]]] = {
    "kinship": [
        ("atta-", "ATTA", "father"),
        ("anna-", "ANA", "mother"),
        ("tuwa/tra-", "TUWATARA", "daughter"),
        ("ḫašša-", "ASA", "grandchild, descendant"),
        ("nāna-", "NANA", "brother (?)"),
        ("warwala-", "WAWA", "seed, offspring"),
        ("zida-", "ZITA", "man, male"),
        ("lala-", "LALA", "tongue, speech"),
    ],
    "body_parts": [
        ("ḫant-", "ATA", "front, face"),
        ("iššari-", "ISARI", "hand"),
        ("pata-", "PATA", "foot"),
        ("ḫašta-", "ASATA", "bone"),
        ("ēšḫar-", "ESARA", "blood"),
        ("tawa-", "TAWA", "eye"),
        ("tummanti-", "TUMATI", "ear"),
        ("lāla-", "LALA", "tongue"),
        ("šārḫuwant-", "SARUWATA", "belly, internal organ"),
        ("gant-", "KATA", "tooth"),  # Hittite/Luwian
    ],
    "agriculture_trade": [
        ("wār-", "WARA", "water"),
        ("immara-", "IMARA", "field, open country"),
        ("parna-", "PARANA", "house"),
        ("tapar-", "TAPARA", "to rule, govern"),
        ("ura-", "URA", "great, large"),
        ("kup-", "KUPA", "to plan, devise"),
        ("tarkummā-", "TARAKUMA", "to translate, interpret"),
        ("uwan(i)-", "UWANI", "wine (?)"),
        ("marmarra-", "MARAMARA", "a type of vessel"),
        ("zuppari-", "SUPARI", "torch"),
        ("taluppi-", "TALUPI", "lump of clay/metal"),
    ],
    "nature": [
        ("tār-", "TARA", "tree/wood"),
        ("wār-", "WARA", "water"),
        ("ḫari-", "ARI", "mountain"),
        ("nepiš-", "NEPISA", "sky, heaven"),
        ("temi-", "TEMI", "forest"),
        ("aruna-", "ARUNA", "sea"),
        ("ḫēw-", "EWA", "rain"),
        ("šiwat-", "SIWATA", "sun/day"),
        ("arma-", "ARAMA", "moon"),
        ("ḫašt-", "ASATA", "star, bone (dual meaning)"),
    ],
    "deities_divine": [
        ("tarḫunt-", "TARATA", "storm-god (Tarḫunt)"),
        ("arinniti-", "ARINITI", "Sun-goddess of Arinna"),
        ("šanta-", "SANATA", "god Šanta"),
        ("kubaba-", "KUPAPA", "goddess Kubaba"),
        ("runtiya-", "RUTIJA", "stag-god Runtiya"),
    ],
    "social_political": [
        ("ḫantawati-", "ATAWATI", "king"),
        ("tapariyalli-", "TAPARIJARI", "governor"),
        ("tarkummā-", "TARAKUMA", "translator"),
        ("ziti-", "SITI", "man, citizen"),
    ],
}

LUWIAN_VERBS: List[Tuple[str, str, str]] = [
    ("ā-", "A", "to make, do"),
    ("ēš-", "ESA", "to be"),
    ("au-", "AU", "to see"),
    ("ed-", "ETA", "to eat"),
    ("ēku-", "EKU", "to drink"),
    ("ī-", "I", "to go"),
    ("piya-", "PIJA", "to give"),
    ("walā-", "WALA", "to die"),
    ("kuen-", "KUNA", "to kill, strike"),
    ("tā-", "TA", "to take"),
    ("ēppa-", "EPA", "to seize, take"),
    ("malli-", "MALI", "to grind"),
    ("išta-", "ISATA", "to hear"),
    ("malā-", "MALA", "to think"),
    ("tūwa-", "TUWA", "to put, place"),
    ("tuwā-", "TUWA", "to look at"),
    ("pā-", "PA", "to give, grant"),
]

LUWIAN_NUMBERS: List[Tuple[str, str, str]] = [
    ("ā-", "A", "one"),
    ("tuw(a)-", "TUWA", "two"),
    ("tarri-", "TARI", "three"),
    ("māwa-", "MAWA", "four"),
    ("pānkʷ-", "PAKU", "five"),
    # 6-10 are less well attested in Luwian but can be reconstructed
    ("*daw(a)-", "TAWA", "six (reconstructed)"),
    ("*šaptam-", "SAPATA", "seven (reconstructed)"),
    ("*ašta-", "ASATA", "eight (reconstructed)"),
]

LUWIAN_SUFFIXES: List[Tuple[str, str, str, str]] = [
    # (suffix, ab_form, function, notes)
    ("-aš", "ASA", "genitive singular", "Very common case suffix"),
    ("-an", "ANA", "accusative singular common", "Core case marker"),
    ("-ati/-anti", "ATI", "3pl present / ablative-instrumental", "Plural marker"),
    ("-a", "A", "dative singular", "Dative case"),
    ("-ti", "TI", "3sg present", "Core verbal ending"),
    ("-nt-", "NTA", "participle", "Anatolian diagnostic feature"),
    ("-šša-", "SASA", "iterative/durative", "Verbal suffix, also in toponyms"),
    ("-ḫa", "A", "conjunction 'and'", "Enclitic conjunction"),
    ("-tari", "TARI", "middle voice 3sg", "Mediopassive marker"),
    ("-una", "UNA", "infinitive", "Infinitive marker"),
    ("-war", "WARA", "verbal noun", "Gerundive/verbal noun"),
    ("-alli-", "ALI", "agentive", "Forms agent nouns"),
    ("-izza-", "IZA", "causative", "Causative verb suffix"),
    ("-ašša-", "ASASA", "genitival adjective", "Very important for toponyms: -assos/-assa"),
    ("-anda-", "ANATA", "gerundive/place", "Very important for toponyms: -anda"),
    ("-wanza-", "WANAZA", "participle", "Luwian participle"),
    ("-mi-", "MI", "my (1sg possessive)", "Possessive enclitic"),
    ("-ti-", "TI", "your (2sg possessive)", "Possessive enclitic"),
    ("-ši-", "SI", "his/her (3sg possessive)", "Possessive enclitic"),
]

# =============================================================================
# Lycian Vocabulary (attested ~500-300 BCE, SW Anatolia)
# =============================================================================

LYCIAN_NOUNS: Dict[str, List[Tuple[str, str, str]]] = {
    "kinship": [
        ("tede-", "TETE", "father"),
        ("ẽni-", "ENI", "mother"),
        ("lada-", "LATA", "wife, woman"),
        ("tideime-", "TITEME", "son, child"),
        ("kbatra-", "KAPATARA", "daughter"),
        ("xñtawa-", "KATAWA", "king"),
        ("xñtawati-", "KATAWATI", "queen, kingship"),
    ],
    "body_parts": [
        ("tawa-", "TAWA", "eye"),
        ("pata-", "PATA", "foot"),
        ("lala-", "LALA", "tongue"),
        ("izre-", "ISARE", "hand"),  # cognate with Luwian iššari-
    ],
    "agriculture_trade": [
        ("prñna-", "PARANA", "house, building"),  # cognate with Luwian parna-
        ("wedri-", "WETARI", "city, settlement"),
        ("arina-", "ARINA", "spring, water source"),
        ("pddẽ-", "PATE", "place"),
        ("xupa-", "KUPA", "tomb"),
        ("tese-", "TESE", "oath, agreement"),
    ],
    "nature": [
        ("arina-", "ARINA", "spring, source"),
        ("maha(na)-", "MAANA", "god, divine"),
        ("natr-", "NATARA", "reeds"),
        ("tura-", "TURA", "land, earth"),
    ],
}

LYCIAN_VERBS: List[Tuple[str, str, str]] = [
    ("ta-", "TA", "to give, place, put"),
    ("ēti-", "ETI", "to carry, bring"),
    ("prñnawa-", "PARANAWA", "to build"),
    ("esa-", "ESA", "to sit, be seated"),
    ("tuwete-", "TUWETE", "erected (a monument)"),
    ("adi-", "ATI", "made, did"),
    ("awa-", "AWA", "to dedicate"),
    ("hri-", "ARI", "to present"),
]

LYCIAN_NUMBERS: List[Tuple[str, str, str]] = [
    ("tbi-", "TAPI", "one (numeral '1')"),
    ("kbi-", "KAPI", "two (numeral '2')"),
    ("tri-", "TARI", "three"),
    # 4-10 not securely attested
]

LYCIAN_SUFFIXES: List[Tuple[str, str, str, str]] = [
    ("-ehi", "EI", "genitive adjective", "Very common suffix"),
    ("-ẽ", "E", "accusative", "Accusative case"),
    ("-ti", "TI", "3sg verbal ending", "Verbal person marker"),
    ("-te", "TE", "3pl verbal ending", "Plural verbal"),
    ("-mi", "MI", "1sg present", "First person"),
    ("-ije-", "IJE", "passive", "Passive marker"),
    ("-asa-", "ASA", "genitival adjective", "Cognate with Luwian -ašša-; -ss- pattern"),
    ("-ãta-", "ATA", "gerundive", "Gerundive/place suffix; -nd- pattern"),
    ("-na-", "NA", "adjectivizer", "Forms adjectives"),
    ("-t-", "TA", "participle", "Participle marker"),
]

# =============================================================================
# Anatolian Toponym Lexicon (Bronze Age Aegean/Anatolian shared)
# =============================================================================

ANATOLIAN_TOPONYMS: List[Tuple[str, str, str, str]] = [
    # (name, ab_form, location, notes)
    ("Millawanda", "MILAWANATA", "Miletus", "Hittite name for Miletus; Linear A found there"),
    ("Apasa", "APASA", "Ephesus", "Arzawan capital"),
    ("Wilusa", "WILUSA", "Troy/Ilion", "Hittite name for Wilusa/Troy"),
    ("Tarḫuntašša", "TARATASASA", "S-Central Anatolia", "Luwian city; -ašša suffix"),
    ("Arinna", "ARINA", "Hittite heartland", "Sun-goddess city"),
    ("Ḫattuša", "ATUSA", "Boğazköy", "Hittite capital"),
    ("Karkiša", "KARAKISA", "Caria (?)", "Western Anatolian land"),
    ("Lukkā", "LUKA", "Lycia (?)", "SW Anatolian land; possibly Lycian homeland"),
    ("Aḫḫiyawa", "AIJAWA", "Aegean/Mycenaean", "Hittite name for Achaean/Aegean kingdom"),
    ("Parnassa", "PARANASA", "Parnassos?", "-ss- toponym; cf. Luwian parna- 'house'"),
    ("Zippašla", "SIPASALA", "W Anatolia", "Land in Arzawa confederacy"),
    ("Iyalanda", "IJALANATA", "Alinda (?)", "-nd- suffix toponym"),
]

# =============================================================================
# Aggregated word list for searching
# =============================================================================

def compile_word_list(language: str = "luwian") -> List[Tuple[str, str, str, str]]:
    """
    Compile a flat list of (phonemic_form, ab_form, meaning, category) for a language.
    """
    words: List[Tuple[str, str, str, str]] = []

    if language == "luwian":
        noun_dict = LUWIAN_NOUNS
        verbs = LUWIAN_VERBS
        numbers = LUWIAN_NUMBERS
        suffixes = LUWIAN_SUFFIXES
        lang_tag = "luwian"
    elif language == "lycian":
        noun_dict = LYCIAN_NOUNS
        verbs = LYCIAN_VERBS
        numbers = LYCIAN_NUMBERS
        suffixes = LYCIAN_SUFFIXES
        lang_tag = "lycian"
    else:
        return words

    for category, items in noun_dict.items():
        for phon, ab, meaning in items:
            words.append((phon, ab, meaning, f"{lang_tag}_{category}"))

    for phon, ab, meaning in verbs:
        words.append((phon, ab, meaning, f"{lang_tag}_verb"))

    for phon, ab, meaning in numbers:
        words.append((phon, ab, meaning, f"{lang_tag}_number"))

    for phon, ab, function, notes in suffixes:
        words.append((phon, ab, f"{function} [{notes}]", f"{lang_tag}_suffix"))

    return words


def compile_toponym_list() -> List[Tuple[str, str, str, str]]:
    """Return Anatolian toponyms with AB forms."""
    result = []
    for name, ab, location, notes in ANATOLIAN_TOPONYMS:
        result.append((name, ab, location, notes))
    return result


def compile_all_words() -> List[Tuple[str, str, str, str, str]]:
    """
    Compile all Anatolian words with language tag.
    Returns list of (phonemic, ab, meaning, category, language).
    """
    all_words = []
    for lang in ["luwian", "lycian"]:
        for phon, ab, meaning, cat in compile_word_list(lang):
            all_words.append((phon, ab, meaning, cat, lang))
    return all_words


def compile_suffix_inventory() -> Dict[str, List[Tuple[str, str, str, str]]]:
    """
    Compile suffix inventories for morphology comparison.
    Returns dict with language keys and list of (suffix, ab, function, notes).
    """
    return {
        "luwian": LUWIAN_SUFFIXES,
        "lycian": LYCIAN_SUFFIXES,
    }
