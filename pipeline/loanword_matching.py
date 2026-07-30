#!/usr/bin/env python3
"""
Loanword Matching: Systematic search for Pre-Greek substrate words (Minoan
loanwords in Greek) in the Linear A corpus.

Based on Beekes (2010, 2014) Pre-Greek substrate word list and methodology.

For each Pre-Greek substrate word:
  a) Reconstruct the Minoan source form (remove Greek inflectional endings)
  b) Map to possible Linear AB transliterations using CV-phonology mapping
  c) Search the database for matching contiguous sign sequences
  d) Check if the context is semantically plausible (nearby logograms)

Outputs:
  - data/analysis/linguistic/loanword_matches.csv       — all candidate matches
  - data/analysis/linguistic/loanword_summary.md        — markdown report
"""

from __future__ import annotations

import csv
import itertools
import math
import random
import re
import sqlite3
import statistics
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DB_PATH = PROJECT_ROOT / "data/database/lineara_full.db"
OUTPUT_DIR = PROJECT_ROOT / "data/analysis/linguistic"
OUTPUT_CSV = OUTPUT_DIR / "loanword_matches.csv"
OUTPUT_MD = OUTPUT_DIR / "loanword_summary.md"

# ---------------------------------------------------------------------------
# Linear A AB syllabary — canonical CV signs (from unicode_utils + DB)
# ---------------------------------------------------------------------------
LINEAR_A_AB = frozenset({
    "A", "DA", "DE", "DI", "DO", "DU",
    "E", "I", "JA", "JE", "JO", "JU",
    "KA", "KE", "KI", "KO", "KU",
    "MA", "ME", "MI", "MO", "MU",
    "NA", "NE", "NI", "NO", "NU",
    "O", "PA", "PA₃", "PI", "PO", "PU", "PU₂",
    "QA", "QE", "QI",
    "RA", "RA₂", "RE", "RI", "RO", "RU",
    "SA", "SE", "SI", "SO", "SU",
    "TA", "TA₂", "TE", "TI", "TO", "TU",
    "U", "WA", "WE", "WI",
    "ZA", "ZE", "ZO", "ZU",
    "NWA", "TWE",
    # Additional rare signs
    "RO₂", "SWI", "PTE",
})


def norm_ab(s: str) -> str:
    """Normalize subscript digits (e.g., PA₃ -> PA3)."""
    return s.replace("₃", "3").replace("₂", "2").replace("₁", "1")


LINEAR_A_AB_NORM = frozenset(norm_ab(s) for s in LINEAR_A_AB)


# ---------------------------------------------------------------------------
# Phoneme → Linear A AB mapping (extended)
# ---------------------------------------------------------------------------
PHONEME_TO_AB: Dict[str, Dict[str, str]] = {
    "a": {"": "A"}, "e": {"": "E"}, "i": {"": "I"},
    "o": {"": "O"}, "u": {"": "U"},
    "p": {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "b": {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "t": {"a": "TA", "e": "TE", "i": "TI", "o": "TO", "u": "TU", "default": "TU"},
    "d": {"a": "DA", "e": "DE", "i": "DI", "o": "DO", "u": "DU", "default": "DU"},
    "k": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "g": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "kʷ": {"a": "QA", "e": "QE", "i": "QI", "o": "QO", "u": "QU", "default": "QU"},
    "gʷ": {"a": "QA", "e": "QE", "i": "QI", "o": "QO", "u": "QU", "default": "QU"},
    "s": {"a": "SA", "e": "SE", "i": "SI", "o": "SO", "u": "SU", "default": "SU"},
    "z": {"a": "ZA", "e": "ZE", "i": "ZI", "o": "ZO", "u": "ZU", "default": "ZU"},
    "š": {"a": "SA", "e": "SE", "i": "SI", "o": "SO", "u": "SU", "default": "SU"},
    "θ": {"a": "TA", "e": "TE", "i": "TI", "o": "TO", "u": "TU", "default": "TU"},
    "ð": {"a": "DA", "e": "DE", "i": "DI", "o": "DO", "u": "DU", "default": "DU"},
    "ħ": {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": ""},
    "h": {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": ""},
    "m": {"a": "MA", "e": "ME", "i": "MI", "o": "MO", "u": "MU", "default": "MU"},
    "n": {"a": "NA", "e": "NE", "i": "NI", "o": "NO", "u": "NU", "default": "NU"},
    "ŋ": {"a": "NA", "e": "NE", "i": "NI", "o": "NO", "u": "NU", "default": "NU"},
    "r": {"a": "RA", "e": "RE", "i": "RI", "o": "RO", "u": "RU", "default": "RU"},
    "l": {"a": "RA", "e": "RE", "i": "RI", "o": "RO", "u": "RU", "default": "RU"},
    "w": {"a": "WA", "e": "WE", "i": "WI", "o": "WO", "u": "WU", "default": "WA"},
    "j": {"a": "JA", "e": "JE", "i": "JI", "o": "JO", "u": "JU", "default": "JU"},
    "y": {"a": "JA", "e": "JE", "i": "JI", "o": "JO", "u": "JU", "default": "JU"},
    "č": {"a": "ZA", "e": "ZE", "i": "ZI", "o": "ZO", "u": "ZU", "default": "ZU"},
    "f": {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "v": {"a": "WA", "e": "WE", "i": "WI", "o": "WO", "u": "WU", "default": "WA"},
    "χ": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "x": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "γ": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "c": {"a": "ZA", "e": "ZE", "i": "ZI", "o": "ZO", "u": "ZU", "default": "ZU"},
    "q": {"a": "QA", "e": "QE", "i": "QI", "o": "QO", "u": "QU", "default": "QU"},
    "ṭ": {"a": "TA", "e": "TE", "i": "TI", "o": "TO", "u": "TU", "default": "TU"},
    "ḍ": {"a": "DA", "e": "DE", "i": "DI", "o": "DO", "u": "DU", "default": "DU"},
    "h₂": {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": "A"},
    "h₃": {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U", "default": "O"},
    "ḫ": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "kʰ": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "tʰ": {"a": "TA", "e": "TE", "i": "TI", "o": "TO", "u": "TU", "default": "TU"},
    "pʰ": {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "gʰ": {"a": "KA", "e": "KE", "i": "KI", "o": "KO", "u": "KU", "default": "KU"},
    "dʰ": {"a": "DA", "e": "DE", "i": "DI", "o": "DO", "u": "DU", "default": "DU"},
    "bʰ": {"a": "PA", "e": "PE", "i": "PI", "o": "PO", "u": "PU", "default": "PU"},
    "r̥": {"a": "RA", "default": "RA"},
    "l̥": {"a": "RA", "default": "RA"},
    "m̥": {"a": "MA", "default": "MA"},
    "n̥": {"a": "NA", "default": "NA"},
    "ń": {"a": "NA", "e": "NE", "i": "NI", "o": "NO", "u": "NU", "default": "NU"},
    "ň": {"a": "NA", "e": "NE", "i": "NI", "o": "NO", "u": "NU", "default": "NU"},
    "ř": {"a": "RA", "e": "RE", "i": "RI", "o": "RO", "u": "RU", "default": "RU"},
    "ṷ": {"a": "WA", "e": "WE", "i": "WI", "default": "WA"},
    "i̯": {"a": "JA", "e": "JE", "default": "JA"},
    "u̯": {"a": "WA", "e": "WE", "default": "WA"},
}

# Consonant clusters that can be approximated in AB script
CLUSTER_MAP: Dict[str, str] = {
    "ks": "KU+SU", "ps": "PU+SU", "ts": "TU+SU",
    "dz": "ZU", "kt": "KU+TU", "pt": "PU+TU",
    "mn": "MU+NU", "pn": "PU+NA", "kn": "KU+NU",
    "tr": "TU+RU", "dr": "DU+RU",
    "pr": "PU+RU", "br": "PU+RU",
    "kr": "KU+RU", "gr": "KU+RU",
    "st": "SU+TU", "sp": "SU+PU", "sk": "SU+KU",
    "str": "SU+TU+RU",
    "št": "SU+TU", "šp": "SU+PU", "šk": "SU+KU",
    "ns": "NU+SU", "ms": "MU+SU",
    "nt": "NU+TU", "nd": "NU+DU",
    "mb": "MU+PU", "mp": "MU+PU",
    "nk": "NU+KU", "ng": "NU+KU",
    "rk": "RU+KU", "rg": "RU+KU",
    "lk": "RU+KU", "lg": "RU+KU",
    "rf": "RU+PU",
    "lm": "RU+MU",
    "rm": "RU+MU",
    "rn": "RU+NU",
    "rl": "RU+RU",
    "nth": "NU+TU",
    "nθ": "NU+TU",
    "nd": "NU+DU",
    "ss": "SU+SU",
    "tt": "TU+TU",
    "pp": "PU+PU",
    "kk": "KU+KU",
    "ll": "RU+RU",
    "mm": "MU+MU",
    "nn": "NU+NU",
}


# ---------------------------------------------------------------------------
# Phonetic → Linear A AB conversion (adapted from swadesh_search.py)
# ---------------------------------------------------------------------------

def tokenise_phonetic(word: str) -> List[str]:
    """Break phonetic string into phonological segments."""
    word = word.lower().strip()
    # Remove diacritics and separators
    for ch in "ˈˌ.‿-ʼ":
        word = word.replace(ch, "")
    tokens: List[str] = []
    i = 0
    while i < len(word):
        if word[i] in " ˈˌːˑ.‿-ʼ":
            i += 1
            continue
        # Try 3-char grapheme
        found = False
        if i + 3 <= len(word):
            chunk = word[i:i+3]
            if chunk in CLUSTER_MAP or chunk in {"kʷ", "gʷ", "h₂", "h₃"}:
                tokens.append(chunk)
                i += 3
                continue
            # Check for kʰ, tʰ, pʰ, etc.
            if len(chunk) == 3 and chunk[1] == "ʰ" and chunk[0] in "ktpbdg":
                tokens.append(chunk)
                i += 3
                continue
        # Try 2-char grapheme
        if i + 2 <= len(word):
            chunk = word[i:i+2]
            if chunk in CLUSTER_MAP:
                tokens.append(chunk)
                i += 2
                continue
            if chunk[1] == "h" and chunk[0] in "t p k d g s c z mnlrbdfθχ":
                tokens.append(chunk)
                i += 2
                continue
            if chunk in {"kʷ", "gʷ", "h₂", "h₃", "ṇ", "ṛ", "ḷ", "ṃ", "ñ"}:
                tokens.append(chunk)
                i += 2
                continue
            # Check for subscript diacritics (like r̥, n̥)
            if chunk[1] in "̥̩̰" or (len(chunk) == 2 and ord(chunk[1]) in range(0x0300, 0x0370)):
                tokens.append(chunk[0])  # Use base character
                i += 2
                continue
        # Single character
        tokens.append(word[i])
        i += 1
    return tokens


def phonetic_to_ab(phonetic: str) -> List[str]:
    """Convert a phonetic word form to a sequence of Linear A AB sign tokens."""
    word = phonetic.strip()
    if not word:
        return []
    tokens = tokenise_phonetic(word)
    ab_seq: List[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Cluster mapping
        if token in CLUSTER_MAP:
            parts = CLUSTER_MAP[token].split("+")
            for part in parts:
                pn = norm_ab(part)
                if part in LINEAR_A_AB or pn in LINEAR_A_AB_NORM:
                    ab_seq.append(part)
            i += 1
            continue

        # Pure vowels
        if token in "aeiou":
            v = token.upper()
            if v in LINEAR_A_AB:
                ab_seq.append(v)
            i += 1
            continue

        # Consonant (possibly with following vowel)
        if token in PHONEME_TO_AB:
            cmap = PHONEME_TO_AB[token]
            if i + 1 < len(tokens) and tokens[i + 1] in "aeiou":
                vowel = tokens[i + 1]
                cv = cmap.get(vowel, cmap.get("default", ""))
                if cv:
                    ncv = norm_ab(cv)
                    if cv in LINEAR_A_AB or ncv in LINEAR_A_AB_NORM:
                        ab_seq.append(cv)
                    elif ncv in LINEAR_A_AB_NORM:
                        for s in LINEAR_A_AB:
                            if norm_ab(s) == ncv:
                                ab_seq.append(s)
                                break
                i += 2
            else:
                cv = cmap.get("default", "")
                if cv:
                    ncv = norm_ab(cv)
                    if cv in LINEAR_A_AB or ncv in LINEAR_A_AB_NORM:
                        ab_seq.append(cv)
                    elif ncv in LINEAR_A_AB_NORM:
                        for s in LINEAR_A_AB:
                            if norm_ab(s) == ncv:
                                ab_seq.append(s)
                                break
                i += 1
            continue

        # Unknown token — try each character
        for ch in token:
            if ch in "aeiou":
                v = ch.upper()
                if v in LINEAR_A_AB:
                    ab_seq.append(v)
            elif ch in PHONEME_TO_AB:
                cv = PHONEME_TO_AB[ch].get("default", "")
                if cv:
                    ncv = norm_ab(cv)
                    if cv in LINEAR_A_AB or ncv in LINEAR_A_AB_NORM:
                        ab_seq.append(cv)
        i += 1

    return ab_seq


# ---------------------------------------------------------------------------
# Levenshtein distance for sign tokens
# ---------------------------------------------------------------------------

def levenshtein_tokens(a: List[str], b: List[str]) -> int:
    """Levenshtein distance between two lists of sign tokens."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    curr = [0] * (m + 1)
    for i in range(1, n + 1):
        curr[0] = i
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev
    return prev[m]


# ---------------------------------------------------------------------------
# Database interface
# ---------------------------------------------------------------------------

class LinearADatabase:
    """Wrapper for querying Linear A sign sequences from SQLite."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._sign_pool: Optional[List[str]] = None
        self._sign_weights: Optional[List[float]] = None

    def close(self):
        self.conn.close()

    def get_all_sign_sequences(self) -> List[Dict]:
        """Return all syllabogram sequences grouped by inscription."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.inscription_id, s.sequence, s.transliteration
            FROM signs s
            WHERE s.transliteration IS NOT NULL
              AND s.transliteration != ''
              AND s.sign_type = 'syllabogram'
            ORDER BY s.inscription_id, s.sequence
        """)
        rows = cur.fetchall()

        inscriptions: Dict[int, List[Tuple[int, str]]] = {}
        for r in rows:
            ins_id = r["inscription_id"]
            trans = r["transliteration"].strip()
            if not trans:
                continue
            ntrans = norm_ab(trans)
            if trans not in LINEAR_A_AB and ntrans not in LINEAR_A_AB_NORM:
                continue
            if trans not in LINEAR_A_AB:
                for s in LINEAR_A_AB:
                    if norm_ab(s) == ntrans:
                        trans = s
                        break
            inscriptions.setdefault(ins_id, []).append((r["sequence"], trans))

        result = []
        for ins_id, signs in sorted(inscriptions.items()):
            signs.sort(key=lambda x: x[0])
            tokens = [s[1] for s in signs]
            result.append({
                "inscription_id": ins_id,
                "sequence": "".join(tokens),
                "tokens": tokens,
            })
        return result

    def get_all_sign_sequences_with_logograms(self) -> List[Dict]:
        """Return syllabograms + logograms with their transliterations."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.inscription_id, s.sequence, s.transliteration, s.sign_type
            FROM signs s
            WHERE s.transliteration IS NOT NULL
              AND s.transliteration != ''
              AND s.sign_type IN ('syllabogram', 'logogram')
            ORDER BY s.inscription_id, s.sequence
        """)
        rows = cur.fetchall()

        inscriptions: Dict[int, List[Tuple[int, str, str]]] = {}
        for r in rows:
            ins_id = r["inscription_id"]
            trans = r["transliteration"].strip()
            s_type = r["sign_type"]
            if not trans:
                continue
            if s_type == 'syllabogram':
                ntrans = norm_ab(trans)
                if trans not in LINEAR_A_AB and ntrans not in LINEAR_A_AB_NORM:
                    continue
                if trans not in LINEAR_A_AB:
                    for s in LINEAR_A_AB:
                        if norm_ab(s) == ntrans:
                            trans = s
                            break
            inscriptions.setdefault(ins_id, []).append(
                (r["sequence"], trans, s_type)
            )

        result = []
        for ins_id, signs in sorted(inscriptions.items()):
            signs.sort(key=lambda x: x[0])
            tokens = [s[1] for s in signs]
            types = [s[2] for s in signs]
            result.append({
                "inscription_id": ins_id,
                "sequence": "".join(tokens),
                "tokens": tokens,
                "types": types,
            })
        return result

    def get_inscription_info(self, ins_id: int) -> Optional[Dict]:
        """Get metadata for an inscription."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT i.gorila_id, i.material, i.object_type, i.minoan_period,
                   i.bce_from, i.bce_to, f.site
            FROM inscriptions i
            LEFT JOIN findspots f ON i.findspot_id = f.id
            WHERE i.id = ?
        """, (ins_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    @property
    def sign_pool(self) -> Tuple[List[str], List[float]]:
        """Get all AB signs and their frequency weights (cached)."""
        if self._sign_pool is not None:
            return self._sign_pool, self._sign_weights  # type: ignore
        cur = self.conn.cursor()
        cur.execute("""
            SELECT transliteration, COUNT(*) as cnt
            FROM signs
            WHERE transliteration IS NOT NULL
              AND transliteration != ''
              AND sign_type = 'syllabogram'
            GROUP BY transliteration
            HAVING cnt > 0
            ORDER BY cnt DESC
        """)
        rows = cur.fetchall()
        signs: List[str] = []
        counts: List[int] = []
        seen = set()
        for r in rows:
            t = r["transliteration"].strip()
            n = norm_ab(t)
            if t in seen or n in seen:
                continue
            if t in LINEAR_A_AB or n in LINEAR_A_AB_NORM:
                canon = t if t in LINEAR_A_AB else next(
                    s for s in LINEAR_A_AB if norm_ab(s) == n
                )
                if canon not in seen:
                    signs.append(canon)
                    counts.append(r["cnt"])
                    seen.add(canon)
        total = sum(counts)
        weights = [c / total for c in counts]
        self._sign_pool = signs
        self._sign_weights = weights
        return signs, weights


# ---------------------------------------------------------------------------
# Corpus index for fast matching
# ---------------------------------------------------------------------------

class CorpusIndex:
    """Pre-computed index of corpus substrings for fast matching."""

    def __init__(self, corpus_seqs: List[Dict]):
        self.substring_locations: Dict[Tuple[str, ...], List[Tuple[int, int]]] = defaultdict(list)
        self.max_len = 0

        for cseq in corpus_seqs:
            tokens = cseq["tokens"]
            n = len(tokens)
            self.max_len = max(self.max_len, n)
            for start in range(n):
                for end in range(start + 1, min(start + 15, n + 1)):
                    sub = tuple(tokens[start:end])
                    self.substring_locations[sub].append(
                        (cseq["inscription_id"], start)
                    )

    def exact_match(self, query: Tuple[str, ...]) -> bool:
        return query in self.substring_locations

    def fuzzy_match(
        self, query: Tuple[str, ...], sign_pool: List[str], max_dist: int = 1
    ) -> List[Tuple[Tuple[str, ...], int, List[Tuple[int, int]]]]:
        """Find corpus substrings within max_dist of query."""
        n = len(query)
        results = []

        if self.exact_match(query):
            results.append((query, 0, self.substring_locations.get(query, [])))

        if max_dist >= 1:
            variants = self._edits1(list(query), sign_pool)
            for var in variants:
                var_t = tuple(var)
                if var_t in self.substring_locations:
                    if not any(r[0] == var_t for r in results):
                        d = levenshtein_tokens(list(query), list(var))
                        results.append((var_t, d, self.substring_locations[var_t]))
        return results

    @staticmethod
    def _edits1(tokens: List[str], sign_pool: List[str]) -> Set[Tuple[str, ...]]:
        """Generate all sequences at Levenshtein distance 1 from a token list."""
        n = len(tokens)
        variants: Set[Tuple[str, ...]] = set()
        # Substitution
        for i in range(n):
            for s in sign_pool:
                if s != tokens[i]:
                    new = tokens.copy()
                    new[i] = s
                    variants.add(tuple(new))
        # Deletion
        for i in range(n):
            new = tokens[:i] + tokens[i+1:]
            variants.add(tuple(new))
        # Insertion
        for i in range(n + 1):
            for s in sign_pool:
                new = tokens[:i] + [s] + tokens[i:]
                variants.add(tuple(new))
        return variants


# ---------------------------------------------------------------------------
# Pre-Greek substrate word list (Beekes 2010, 2014 + other sources)
# ---------------------------------------------------------------------------
# Format: (greek_word, transliteration, english_gloss, reconstructed_minoan_form, category)

PRE_GREEK_LOANWORDS: List[Tuple[str, str, str, str, str]] = [
    # ── Place names with -ss- and -nth- suffixes ──
    ("Κνωσσός", "Knōssos", "Knossos", "knos", "place_name"),
    ("Φαιστός", "Phaistos", "Phaistos", "pʰaist", "place_name"),
    ("Τύλισος", "Tylisos", "Tylissos", "tulis", "place_name"),
    ("Ἀμνισός", "Amnisos", "Amnisos", "amnis", "place_name"),
    ("Λαβύρινθος", "labyrinthos", "labyrinth", "laburintʰ", "place_name"),
    ("Ἀσίνη", "Asinē", "Asine", "asin", "place_name"),
    ("Ἕρμιον", "Hermion", "Hermione", "ermion", "place_name"),
    ("Ἴαλυσος", "Ialysos", "Ialysos", "ialus", "place_name"),
    ("Ὕσται", "Hystai", "Hysiae", "usta", "place_name"),
    ("Πραισός", "Praisos", "Praisos", "prais", "place_name"),
    ("Ῥιζοῦς", "Rhizous", "Rhizus", "ridz", "place_name"),
    ("Μάλλος", "Mallos", "Mallos", "mal", "place_name"),
    ("Πύλαι", "Pylai", "Pylae", "pul", "place_name"),
    ("Ἄργος", "Argos", "Argos", "arg", "place_name"),
    ("Πύργος", "Pyrgos", "Pyrgos (place/tower)", "purg", "place_name"),
    ("Πακτύη", "Paktyē", "Paktye", "paktu", "place_name"),
    ("Τραχίς", "Trachis", "Trachis", "trakʰ", "place_name"),
    ("Λήμνος", "Lēmnos", "Lemnos", "lemn", "place_name"),
    ("Σηπιάς", "Sēpias", "Sepias", "sepia", "place_name"),
    ("Θήρα", "Thēra", "Thera", "tʰer", "place_name"),
    ("Λαμία", "Lamia", "Lamia", "lami", "place_name"),
    ("Συρία", "Syria", "Syria", "suri", "place_name"),
    ("Ἰθάκη", "Ithakē", "Ithaca", "itʰak", "place_name"),
    ("Λυκτόριον", "Lyktorion", "Lyktorion", "luktor", "place_name"),
    ("Μυκῆναι", "Mykēnai", "Mycenae", "muken", "place_name"),
    ("Κόρινθος", "Korinthos", "Corinth", "korintʰ", "place_name"),
    ("Ζάκυνθος", "Zakynthos", "Zacynthus", "dzakuntʰ", "place_name"),
    ("Πύδνα", "Pydna", "Pydna", "pudn", "place_name"),
    ("Περγαμός", "Pergamos", "Pergamon", "pergam", "place_name"),
    ("Λακωνία", "Lakōnia", "Laconia", "lakon", "place_name"),
    ("Βοιωτία", "Boiotia", "Boeotia", "bojot", "place_name"),
    ("Θεσσαλία", "Thessalia", "Thessaly", "tʰesal", "place_name"),
    ("Ἀρκαδία", "Arkadia", "Arcadia", "arkad", "place_name"),
    ("Σκύρος", "Skyros", "Skyros", "skur", "place_name"),
    ("Ἄθως", "Athōs", "Athos", "atʰos", "place_name"),
    ("Κάϋστρος", "Kāystros", "Caystrus", "kaustr", "place_name"),
    ("Σμύρνα", "Smyrna", "Smyrna", "smurn", "place_name"),
    ("Μίλητος", "Milētos", "Miletus", "milet", "place_name"),
    ("Ἐρύθραι", "Erythrai", "Erythrae", "erutʰr", "place_name"),
    ("Φῶκαια", "Phōkaia", "Phocaea", "pʰokai", "place_name"),
    ("Λύκτος", "Lyktos", "Lyctus", "lukt", "place_name"),
    ("Γόρτυν", "Gortyn", "Gortyn", "gortun", "place_name"),
    ("Φαλάσαρνα", "Phalasarna", "Phalasarna", "pʰalasarn", "place_name"),
    ("Ὑρτακίς", "Hyrtakis", "Hyrtacus", "urtak", "place_name"),
    ("Ἔλυρος", "Elyros", "Elyrus", "elur", "place_name"),
    ("Ἱεράπυτνα", "Hierapytna", "Hierapytna", "ieraputn", "place_name"),
    ("Πριανσός", "Priansos", "Priansus", "prians", "place_name"),
    ("Σύβριτα", "Sybrita", "Sybrita", "subrit", "place_name"),
    ("Λάππα", "Lappa", "Lappa", "lap", "place_name"),
    ("Ἐλευθέρνα", "Eleutherna", "Eleutherna", "eleutʰern", "place_name"),
    ("Ἀξός", "Axos", "Axos", "aks", "place_name"),
    ("Λύκαστος", "Lykastos", "Lycastus", "lukast", "place_name"),
    ("Παισός", "Paisos", "Paisus", "pais", "place_name"),
    ("Μύρινα", "Myrina", "Myrina", "murin", "place_name"),
    ("Ἴμβρος", "Imbros", "Imbros", "imbr", "place_name"),
    ("Λέσβος", "Lesbos", "Lesbos", "lesb", "place_name"),
    ("Χίος", "Chios", "Chios", "kʰios", "place_name"),
    ("Σάμος", "Samos", "Samos", "sam", "place_name"),
    ("Κέως", "Keōs", "Ceos", "keo", "place_name"),
    ("Νάξος", "Naxos", "Naxos", "naks", "place_name"),
    ("Πάρος", "Paros", "Paros", "par", "place_name"),
    ("Δῆλος", "Dēlos", "Delos", "del", "place_name"),
    ("Κύθηρα", "Kythera", "Cythera", "kutʰer", "place_name"),
    ("Ψείρα", "Pseira", "Pseira", "pseir", "place_name"),
    ("Μόχλος", "Mochlos", "Mochlos", "mokʰl", "place_name"),
    ("Γουρνιά", "Gournia", "Gournia", "gurni", "place_name"),
    ("Πετσοφάς", "Petsophas", "Petsophas", "petsopʰas", "place_name"),
    ("Παλαίκαστρο", "Palaikastro", "Palaikastro", "palaikastr", "place_name"),
    ("Ζάκρος", "Zakros", "Zakros", "zakr", "place_name"),
    ("Κανδάνη", "Kandanē", "Kandane", "kandan", "place_name"),
    ("Ἄπτερα", "Aptera", "Aptera", "apter", "place_name"),

    # ── Nature / geography ──
    ("θάλασσα", "thalassa", "sea", "tʰalasa", "nature"),
    ("νήριτον", "neriton", "sea-plant", "nerit", "nature"),
    ("μίνθη", "minthē", "mint", "mintʰ", "nature"),
    ("σίναπι", "sinapi", "mustard", "sinap", "nature"),
    ("κρόκος", "krokos", "saffron", "krok", "nature"),
    ("ῥόδον", "rhodon", "rose", "wrod", "nature"),
    ("ἴον", "ion", "violet", "i-on", "nature"),
    ("δάφνη", "daphnē", "laurel", "dapʰn", "nature"),
    ("κυπάρισσος", "kyparissos", "cypress", "kuparis", "nature"),
    ("ὑάκινθος", "hyakinthos", "hyacinth", "huakintʰ", "nature"),
    ("ἄμπελος", "ampelos", "vine", "ampel", "nature"),
    ("ἐλαία", "elaia", "olive (tree)", "elai", "nature"),
    ("συκῆ", "sykē", "fig tree", "suk", "nature"),
    ("ὄλυνθος", "olynthos", "wild fig", "oluntʰ", "nature"),
    ("κέγχρος", "kenchros", "millet", "kenkʰr", "nature"),
    ("κεγχρεών", "kenchreōn", "millet field", "kenkʰreon", "nature"),
    ("κρίμνον", "krimnon", "barley-groat", "krimn", "nature"),
    ("πυρός", "pyros", "wheat", "pur", "nature"),
    ("λίνον", "linon", "flax/linen", "lin", "nature"),
    ("στύραξ", "styrax", "storax-tree", "sturaks", "nature"),
    ("ἔβενος", "ebenos", "ebony", "eben", "nature"),
    ("κυνάρα", "kynara", "artichoke", "kunara", "nature"),
    ("σάλπιγξ", "salpinx", "trumpet-flower", "salpinks", "nature"),
    ("ἀσφόδελος", "asphodelos", "asphodel", "asrodel", "nature"),
    ("σέρις", "seris", "endive", "seri", "nature"),
    ("μύκης", "mykēs", "mushroom", "muke", "nature"),
    ("πέλλα", "pella", "stone", "pel", "nature"),
    ("λαύρα", "laurada", "lane/alley", "laur", "nature"),
    ("λίμνη", "limnē", "lake/marsh", "limn", "nature"),
    ("λόφος", "lophos", "hill", "lor", "nature"),

    # ── Architecture / settlements ──
    ("πύργος", "pyrgos", "tower", "purg", "architecture"),
    ("ἄστυ", "asty", "town", "astu", "architecture"),
    ("ναῦς", "naus", "ship", "nau", "architecture"),
    ("δαπέδον", "dapedon", "floor/pavement", "daped", "architecture"),
    ("σπήλαιον", "spēlaion", "cave", "spelai", "architecture"),
    ("τειχίον", "teichion", "wall", "teikʰi", "architecture"),
    ("στέγη", "stegē", "roof", "steg", "architecture"),
    ("οἶκος", "oikos", "house", "oik", "architecture"),
    ("θύρα", "thyra", "door", "tʰur", "architecture"),
    ("σκοτίη", "skotiē", "darkness/dark chamber", "skoti", "architecture"),
    ("κλίνη", "klinē", "bed/couch", "klin", "architecture"),
    ("τράπεζα", "trapeza", "table", "trapedz", "architecture"),
    ("θρόνος", "thronos", "throne", "tʰron", "architecture"),
    ("βάθρον", "bathron", "base/pedestal", "batʰr", "architecture"),
    ("κρηπίς", "krēpis", "foundation", "krepi", "architecture"),
    ("ἀψίς", "apsis", "arch/vault", "apsi", "architecture"),

    # ── Domestic / vessels ──
    ("ἄσμινθος", "asminthos", "bathtub", "asmin", "domestic"),
    ("δῖνος", "dinos", "drinking-cup", "din", "domestic"),
    ("κάνθαρος", "kantharos", "drinking cup", "kantʰar", "domestic"),
    ("κύαθος", "kyathos", "ladle/cup", "kuatʰ", "domestic"),
    ("φιάλη", "phialē", "bowl", "pʰial", "domestic"),
    ("στάμνος", "stamnos", "jar", "stamn", "domestic"),
    ("πίθος", "pithos", "large storage jar", "pitʰ", "domestic"),
    ("ἀμφορεύς", "amphoreus", "amphora", "amρor", "domestic"),
    ("κέραμος", "keramos", "pottery/clay", "keram", "domestic"),
    ("λάρναξ", "larnax", "chest/coffin", "larnaks", "domestic"),
    ("λέβης", "lebēs", "cauldron", "lebe", "domestic"),
    ("θῆλυς", "thēlys", "container/vessel", "tʰelu", "domestic"),
    ("κισσύβιον", "kissybion", "ivy-wood cup", "kisub", "domestic"),
    ("τρίβων", "tribōn", "worn garment", "tribon", "domestic"),
    ("χλαῖνα", "chlaina", "cloak", "kʰlain", "domestic"),
    ("κυβερνάω", "kybernaō", "to steer (ship)", "kubern", "domestic"),
    ("θύλακος", "thylakos", "sack/bag", "tʰulak", "domestic"),

    # ── Flora / agriculture ──
    ("ἐρέβινθος", "erebinthos", "chickpea", "erebintʰ", "flora"),
    ("ὄροβος", "orobos", "bitter vetch", "orob", "flora"),
    ("θύμος", "thymos", "thyme", "tʰum", "flora"),
    ("ὀρίγανον", "origanon", "oregano", "orig", "flora"),
    ("σέλινον", "selinon", "celery", "selin", "flora"),
    ("ῥάκος", "rhakos", "rag/leaf", "wrak", "flora"),
    ("κασία", "kasia", "cinnamon", "kasi", "flora"),
    ("κάρυον", "karyon", "nut", "kari", "flora"),
    ("βαλάνιον", "balanion", "acorn", "balani", "flora"),
    ("σκόρδον", "skordon", "garlic", "skord", "flora"),
    ("δαῦκον", "daukon", "carrot", "dauk", "flora"),
    ("ἐλέαι", "eleai", "olives", "ele", "flora"),
    ("στάφις", "staphis", "raisin", "stafi", "flora"),
    ("σῦκον", "sykon", "fig", "suk", "flora"),
    ("μῆλον", "mēlon", "apple", "mel", "flora"),
    ("ἄπιον", "apion", "pear", "api", "flora"),
    ("κορίαννον", "koriannon", "coriander", "korian", "flora"),
    ("κύμινον", "kyminon", "cumin", "kumin", "flora"),
    ("κρόμμυον", "krommyon", "onion", "kromu", "flora"),
    ("δάφνη", "daphnē", "laurel", "dapʰn", "flora"),
    ("σμύρνα", "smyrna", "myrrh", "smurn", "flora"),
    ("σχῖνος", "schinos", "lentisk", "skʰin", "flora"),
    ("πτέρις", "pteris", "fern", "pteri", "flora"),
    ("βύβλος", "byblos", "papyrus", "bubl", "flora"),
    ("κύπειρον", "kypeiron", "cyperus-grass", "kupei", "flora"),
    ("ἄκαριον", "akarion", "mite/tick (plant)", "akari", "flora"),
    ("λάχανον", "lachanon", "vegetable", "lakʰan", "flora"),
    ("ἄννησον", "annēson", "anise", "anes", "flora"),

    # ── Animals ──
    ("βόλινθος", "bolinthos", "wild bull", "bolintʰ", "animal"),
    ("ἔλαφος", "elaphos", "deer", "elar", "animal"),
    ("κάπρος", "kapros", "wild boar", "kapr", "animal"),
    ("λύγξ", "lynx", "lynx", "lunks", "animal"),
    ("πάνθηρ", "panthēr", "panther", "pantʰer", "animal"),
    ("σκόμβρος", "skombros", "mackerel", "skombr", "animal"),
    ("θύννος", "thynnos", "tuna", "tʰun", "animal"),
    ("σπάρος", "sparos", "sea-bream", "spar", "animal"),
    ("κόγχη", "konchē", "conch/shell", "konkʰe", "animal"),
    ("σπόγγος", "spongos", "sponge", "spong", "animal"),
    ("πολύπους", "polypous", "octopus", "polup", "animal"),
    ("κάραβος", "karabos", "beetle/crayfish", "karab", "animal"),
    ("σκώληξ", "skōlēx", "worm", "skoleks", "animal"),
    ("νεβρός", "nebros", "fawn", "nebr", "animal"),
    ("βδέλλα", "bdella", "leech", "bdel", "animal"),
    ("φάλαινα", "phalaina", "whale", "pʰalain", "animal"),
    ("δέλφαξ", "delphax", "dolphin/pig", "delρaks", "animal"),
    ("αἴλουρος", "ailouros", "cat", "ailur", "animal"),
    ("μῦς", "mys", "mouse", "mu", "animal"),
    ("κίχλη", "kichlē", "thrush", "kikʰl", "animal"),
    ("κρέξ", "krex", "crake (bird)", "kreks", "animal"),
    ("κεγχρηῖς", "kenchrēis", "a sea-bird", "kenkʰr", "animal"),
    ("μύραινα", "myraina", "murena (eel)", "muraina", "animal"),
    ("γλαῦξ", "glaux", "owl", "glauks", "animal"),
    ("σφήξ", "sphēx", "wasp", "sρʰeks", "animal"),
    ("σκνίψ", "sknips", "midge/gnat", "sknips", "animal"),

    # ── Body parts / human ──
    ("σάρξ", "sarx", "flesh", "sarks", "body"),
    ("αἱμορροίς", "haimorrhois", "vein/hemorrhoid", "aimoroi", "body"),
    ("θώραξ", "thōrax", "chest/breastplate", "tʰoraks", "body"),
    ("στήθος", "stēthos", "chest", "stetʰ", "body"),
    ("νῶτον", "nōton", "back", "not", "body"),
    ("βουβών", "boubōn", "groin", "bubon", "body"),
    ("ἐγκέφαλος", "enkelphalos", "brain", "enkefal", "body"),
    ("σπλήν", "splēn", "spleen", "splen", "body"),
    ("κύστις", "kystis", "bladder", "kusti", "body"),
    ("κόλον", "kolon", "colon", "kol", "body"),
    ("στόμα", "stoma", "mouth", "stom", "body"),
    ("οὖλον", "oulon", "gum", "ul", "body"),
    ("τενθρηδών", "tenthrēdōn", "gland/swelling", "tentʰred", "body"),
    ("ἄκανθα", "akantha", "thorn/spine", "akant", "body"),
    ("μήνιγξ", "mēninx", "membrane", "meninks", "body"),
    ("σφόνδυλος", "sphondylos", "vertebra", "sρondul", "body"),
    ("βλέφαρον", "blepharon", "eyelid", "blepʰar", "body"),
    ("καρκίνος", "karkinos", "crab/cancer", "karkin", "body"),
    ("κόρη", "korē", "pupil (of eye)", "kor", "body"),

    # ── Cultural items ──
    ("Μίνως", "Minōs", "Minos (king)", "min", "culture"),
    ("Θεμιστοκλῆς", "Themistoklēs", "Themistocles", "tʰemistokle", "culture"),
    ("Ἰκάριος", "Ikarios", "Icarius", "ikari", "culture"),
    ("Δαίδαλος", "Daidalos", "Daedalus", "daidal", "culture"),
    ("Κάρνος", "Karnos", "Carnus (seer)", "karn", "culture"),
    ("Ἀριάδνη", "Ariadnē", "Ariadne", "ariadn", "culture"),
    ("Φαίδρα", "Phaidra", "Phaedra", "pʰaidr", "culture"),
    ("Πασιφάη", "Pasiphaē", "Pasiphae", "pasipʰae", "culture"),
    ("Κασσάνδρα", "Kassandra", "Cassandra", "kassandr", "culture"),
    ("Ἀχιλλεύς", "Achilleus", "Achilles", "akʰil", "culture"),
    ("Ὀδυσσεύς", "Odysseus", "Odysseus", "oduseu", "culture"),
    ("Ἡρακλῆς", "Hēraklēs", "Heracles", "erakle", "culture"),
    ("Περσεύς", "Perseus", "Perseus", "perseu", "culture"),
    ("Θησεύς", "Thēseus", "Theseus", "tʰeseu", "culture"),
    ("Βελλεροφῶν", "Bellerophōn", "Bellerophon", "beleropʰon", "culture"),
    ("Τροία", "Troia", "Troy", "troi", "culture"),
    ("Δάρδανος", "Dardanos", "Dardanus", "dardan", "culture"),
    ("Σκάμανδρος", "Skamandros", "Scamander", "skamandr", "culture"),
    ("Ἀκάδημος", "Akadēmos", "Academus", "akadem", "culture"),
    ("Δωδώνη", "Dōdōnē", "Dodona", "dodon", "culture"),
    ("Ἀθήνη", "Athēnē", "Athena", "atʰen", "culture"),
    ("Ἥφαιστος", "Hēphaistos", "Hephaestus", "epʰaist", "culture"),
    ("Δημήτηρ", "Dēmētēr", "Demeter", "dēmētēr", "culture"),
    ("Περσεφόνη", "Persephonē", "Persephone", "perseρʰon", "culture"),
    ("Ἄρτεμις", "Artemis", "Artemis", "artemi", "culture"),
    ("Ἀπόλλων", "Apollōn", "Apollo", "apolon", "culture"),
    ("Ποσειδῶν", "Poseidōn", "Poseidon", "poseidon", "culture"),
    ("Ἑρμῆς", "Hermēs", "Hermes", "erme", "culture"),
    ("Διόνυσος", "Dionysos", "Dionysus", "dionus", "culture"),
    ("Αἰγεύς", "Aigeus", "Aegeus", "aigeu", "culture"),
    ("Πάν", "Pan", "Pan", "pan", "culture"),
    ("Κένταυρος", "Kentauros", "Centaur", "kentaur", "culture"),
    ("Κύκλωψ", "Kyklōps", "Cyclops", "kuklop", "culture"),
    ("Τιτάν", "Titān", "Titan", "titan", "culture"),
    ("Ὄλυμπος", "Olympos", "Olympus", "olump", "culture"),
    ("Παρνασσός", "Parnassos", "Parnassus", "parnas", "culture"),
    ("Κιθαιρών", "Kithairōn", "Cithaeron", "kitʰairon", "culture"),
    ("Λύκαιον", "Lykaion", "Lycaeum", "lukai", "culture"),
    ("Κρόνος", "Kronos", "Cronus", "kron", "culture"),
    ("Ἱμέρα", "Himera", "Himera", "imer", "culture"),
    ("πλοῦτος", "ploutos", "wealth", "plut", "culture"),
    ("νῆσος", "nēsos", "island", "nes", "culture"),
    ("ἐχῖνος", "echinos", "sea-urchin / bowl", "ekʰin", "culture"),
    ("πέτρα", "petra", "rock", "petr", "culture"),
    ("σπήλαιον", "spēlaion", "cave", "spelai", "culture"),
    ("μαραθών", "marathōn", "fennel (Marathon)", "maratʰon", "culture"),

    # ── Abstract / miscellaneous ──
    ("βασιλεύς", "basileus", "king", "basileu", "abstract"),
    ("λαός", "laos", "people (military)", "la", "abstract"),
    ("κύριος", "kyrios", "lord", "kurio", "abstract"),
    ("δῆμος", "dēmos", "people/deme", "dem", "abstract"),
    ("νόμος", "nomos", "law", "nom", "abstract"),
    ("τέμενος", "temenos", "sacred precinct", "temen", "abstract"),
    ("βωμός", "bōmos", "altar", "bom", "abstract"),
    ("κλίμα", "klima", "region/incline", "klim", "abstract"),
    ("χορός", "choros", "dance/dancing place", "kʰor", "abstract"),
    ("θέατρον", "theatron", "theatre", "tʰeatr", "abstract"),
    ("παλαίστρα", "palaistra", "wrestling school", "palaistr", "abstract"),
    ("γυμνάσιον", "gymnasion", "gymnasium", "gumnasi", "abstract"),
    ("τύραννος", "tyrannos", "tyrant", "turan", "abstract"),
    ("θάνατος", "thanatos", "death", "tʰanat", "abstract"),
    ("ψυχή", "psychē", "soul", "psukʰ", "abstract"),
    ("βίος", "bios", "life", "bio", "abstract"),
    ("λοιμός", "loimos", "plague", "loim", "abstract"),
    ("ἑορτή", "heortē", "festival", "eort", "abstract"),
    ("θυσία", "thysia", "sacrifice", "tʰusi", "abstract"),
    ("εἰρήνη", "eirēnē", "peace", "eiren", "abstract"),
    ("νίκη", "nikē", "victory", "nik", "abstract"),
    ("τύχη", "tychē", "fortune/chance", "tukʰ", "abstract"),
    ("δελφίς", "delphis", "dolphin", "delρi", "abstract"),

    # ── Suffix patterns (-nth- words, -ss- words) ──
    ("ἀσάμινθος", "asaminthos", "bathtub (var.)", "asamintʰ", "suffix_nth"),
    ("λάβρυνθος", "labrynthos", "labyrinth (var.)", "labruntʰ", "suffix_nth"),
    ("λάμινθος", "laminthos", "throat/gullet", "lamintʰ", "suffix_nth"),
    ("λύρινθος", "lyrinthos", "lyre?", "lirintʰ", "suffix_nth"),
    ("μέρινθος", "merinthos", "cord/string", "merintʰ", "suffix_nth"),
    ("πλίνθος", "plinthos", "brick", "plintʰ", "suffix_nth"),
    ("πύρινθος", "pyrinthos", "tower (var.)", "purintʰ", "suffix_nth"),
    ("σάρινθος", "sarinthos", "?", "sari", "suffix_nth"),
    ("ἄκανθος", "akanthos", "acanthus", "akantʰ", "suffix_nth"),
    ("κύαινθος", "kyainthos", "?", "kuaintʰ", "suffix_nth"),
    ("λάγυνθος", "lagynthos", "?", "laguntʰ", "suffix_nth"),
    ("ἔλυνθος", "elynthos", "?", "eluntʰ", "suffix_nth"),
    ("θύρινθος", "thyrinthos", "?", "tʰurintʰ", "suffix_nth"),
    ("χέλινθος", "chelinthos", "?", "kʰelintʰ", "suffix_nth"),
    ("κάλαθος", "kalathos", "basket", "kalatʰ", "suffix_nth"),
    ("σπολάθον", "spolathon", "?", "spolatʰ", "suffix_nth"),
    ("ζέρεθρον", "zerethron", "pit", "dzeretʰr", "suffix_nth"),
    ("πίννα", "pinna", "mussel", "pin", "suffix_nth"),
    ("κορώνη", "korōnē", "crow/crown", "koron", "suffix_nth"),
    ("θρῖναξ", "thrinax", "trident/fork", "tʰrinaks", "suffix_nth"),
    ("γλῶσσα", "glōssa", "tongue", "glos", "suffix_ss"),
    ("θάλασσα", "thalassa", "sea", "tʰalas", "suffix_ss"),
    ("κορυδαλός", "korydalos", "lark", "korudal", "suffix_ss"),
    ("κυπάρισσος", "kyparissos", "cypress", "kuparis", "suffix_ss"),
    ("Ἁλικαρνασσός", "Halikarnassos", "Halicarnassus", "alikarnas", "suffix_ss"),
    ("Λαρίσα", "Larisa", "Larissa", "laris", "suffix_ss"),
    ("Μέλισσα", "Melissa", "Melissa (nymph/bee)", "melis", "suffix_ss"),
    ("Παγασαί", "Pagasai", "Pagasae", "pagas", "suffix_ss"),
    ("Τευμησσός", "Teumēssos", "Teumessus", "teumes", "suffix_ss"),
    ("Παρνασσός", "Parnassos", "Parnassus", "parnas", "suffix_ss"),
    ("Ἀλφειός", "Alpheios", "Alpheus", "alrei", "suffix_ss"),
    ("Κηφισός", "Kēphisos", "Cephisus", "kepʰis", "suffix_ss"),
    ("Θερμισσός", "Thermissos", "Thermissus", "tʰermis", "suffix_ss"),
    ("Σαλαμίς", "Salamis", "Salamis", "salam", "suffix_ss"),
    ("Καλλιρόη", "Kallirhoē", "Callirrhoe", "kaliroe", "suffix_ss"),
    ("Δρυμνούς", "Drymnous", "Drymous", "drmn", "suffix_ss"),
    ("Γυμνούς", "Gymnous", "Gymnous", "gumn", "suffix_ss"),
]

# ---------------------------------------------------------------------------
# Semantic context checker
# ---------------------------------------------------------------------------

# Mapping of logogram transliterations to semantic categories
LOGOGRAM_COMMODITY_MAP = {
    "VIN": "wine",
    "OLE": "oil",
    "OLIV": "olive",
    "GRA": "grain",
    "CYP": "cypress/aromatic",
    "VAS": "vessel",
    "AROM": "aromatic",
    "CAP": "caprid/goat",
    "BOS": "bovine",
    "OVIS": "sheep",
    "SUS": "pig",
    "VIR": "man/person",
    "MUL": "woman",
    "LANA": "wool",
    "LINUM": "flax/linen",
    "TELA": "cloth",
    "FRUM": "wheat",
    "HORD": "barley",
    "NI": "fig",
    "PU": "?",  # may be a tree/plant
    "MA": "?",  # uncertain
    "KU": "?",  # uncertain
    "RO": "?",  # uncertain
    "SA": "?",  # uncertain
    "SE": "?",  # uncertain
    "TA": "?",  # uncertain
    "U": "?",  # uncertain
}

# Words whose meaning hints at certain ideogram contexts
WORD_SEMANTIC_HINTS: Dict[str, List[str]] = {
    "sea": ["VIN", "OLE", "AROM", "NI"],  # commodities transported by sea
    "wine": ["VIN"],
    "oil": ["OLE"],
    "olive": ["OLIV", "OLE"],
    "grain": ["GRA"],
    "fig": ["NI", "FIC"],
    "wheat": ["GRA", "FRUM"],
    "barley": ["GRA", "HORD"],
    "cypress": ["CYP"],
    "aromatic": ["AROM", "CYP"],
    "vessel": ["VAS"],
    "ship": ["VAS"],
    "bathtub": ["VAS"],
    "pottery": ["VAS"],
    "wool": ["LANA"],
    "linen": ["LINUM"],
    "cloth": ["TELA"],
    "tower": ["NI"],  # weak - no specific ideogram
    "king": ["VIR"],
    "queen": ["MUL"],
    "person": ["VIR", "MUL"],
    "people": ["VIR"],
    "sheep": ["OVIS", "CAP"],
    "goat": ["CAP"],
    "bovine": ["BOS"],
    "pig": ["SUS"],
    "deer": ["CERV"],
    "sacrifice": ["VIR", "BOS", "OVIS", "CAP"],
    "altar": ["VIR", "OLE"],
    "sacred": ["VIR", "OLE", "OLIV"],
    "temple": ["VIR"],
    "mint": ["AROM"],
    "mustard": ["AROM"],
    "saffron": ["AROM"],
    "laurel": ["AROM"],
    "olive": ["OLIV", "OLE"],
    "fig": ["NI", "FIC"],
    "grape": ["VIN"],
}

# Logograms that can appear near matching sequences and their relevance
COMMODITY_IDEOGRAMS = {"VIN", "OLE", "OLIV", "GRA", "CYP", "AROM",
                       "VAS", "NI", "FIC", "LANA", "LINUM", "TELA",
                       "VIR", "MUL", "BOS", "OVIS", "CAP", "SUS",
                       "FRUM", "HORD", "OLE+U", "OLE+KI", "OLE+NE",
                       "OLE+RI", "VIN+WA", "GRA+DA", "GRA+PA",
                       "GRA+BOSm"}


def check_context(inscription_id: int, match_position: int,
                  match_length: int, db: LinearADatabase) -> Dict[str, Any]:
    """Check what logograms/ideograms appear near a matching sequence."""
    conn = db.conn
    cur = conn.cursor()
    cur.execute("""
        SELECT s.sequence, s.transliteration, s.sign_type
        FROM signs s
        WHERE s.inscription_id = ?
          AND s.transliteration IS NOT NULL
          AND s.transliteration != ''
        ORDER BY s.sequence
    """, (inscription_id,))
    rows = cur.fetchall()

    # Build a map of positions to sign types
    nearby_logograms = []
    nearby_trans = []
    found_ideograms = set()

    for r in rows:
        seq = r["sequence"]
        trans = r["transliteration"].strip()
        stype = r["sign_type"]

        # Look for signs near the match (within ±5 positions)
        # But only count them if they are genuinely close
        if match_position <= seq < match_position + match_length:
            # Inside the match itself
            if stype in ("logogram", "numeral", "fraction"):
                nearby_logograms.append(f"IN:{trans}")
                lg_upper = trans.upper()
                for comm in COMMODITY_IDEOGRAMS:
                    if comm in lg_upper or lg_upper == comm:
                        found_ideograms.add(comm)
            elif stype == "syllabogram":
                nearby_trans.append(trans)
        elif abs(seq - match_position) <= 3 or \
             abs(seq - (match_position + match_length - 1)) <= 3:
            # Within 3 positions before start or after end
            if stype in ("logogram", "numeral", "fraction"):
                nearby_logograms.append(trans)
                lg_upper = trans.upper()
                for comm in COMMODITY_IDEOGRAMS:
                    if comm in lg_upper or lg_upper == comm:
                        found_ideograms.add(comm)
        elif abs(seq - match_position) <= 5 or \
             abs(seq - (match_position + match_length - 1)) <= 5:
            # Within 5 positions (weaker context)
            if stype == "logogram":
                lg_upper = trans.upper()
                for comm in COMMODITY_IDEOGRAMS:
                    if comm in lg_upper or lg_upper == comm:
                        found_ideograms.add(comm)

    return {
        "nearby_logograms": nearby_logograms[:20],
        "nearby_syllabograms": "".join(nearby_trans),
        "found_commodities": list(found_ideograms),
        "context_window": f"pos {max(0, match_position - 5)}-{match_position + match_length + 4}",
    }


def score_semantic_plausibility(english_gloss: str,
                                found_commodities: List[str],
                                word_category: str) -> float:
    """
    Score how semantically plausible the match context is.
    Returns a score 0.0 (implausible) to 1.0 (highly plausible).
    """
    if not found_commodities:
        # No nearby ideograms — neutral score
        if word_category == "place_name":
            return 0.1
        return 0.05

    # Get expected ideograms from hints
    gloss_lower = english_gloss.lower()
    expected = set()
    for key, comms in WORD_SEMANTIC_HINTS.items():
        if key in gloss_lower:
            expected.update(comms)

    # Place names: any nearby commodities are mildly supportive
    if not expected and word_category == "place_name":
        return min(0.3, 0.1 + 0.05 * len(found_commodities))

    if not expected:
        return 0.1

    # Count overlap
    found_set = set(fc.upper() for fc in found_commodities)
    expected_set = set(e.upper() for e in expected)

    if not expected_set:
        return 0.1

    overlap = len(found_set & expected_set)
    # Score based on expected-to-found ratio
    # Higher score when the expected commodities are actually present
    # But penalize when found has many irrelevant commodities (noise)
    if overlap > 0:
        # Precision-like: overlap / total distinct found (to avoid noise bonus)
        precision = overlap / max(len(found_set), 1)
        recall = overlap / len(expected_set)
        score = 0.1 + (precision * 0.5 + recall * 0.4)
        return min(1.0, score)

    return 0.1


# ---------------------------------------------------------------------------
# Build AB entries from loanword list
# ---------------------------------------------------------------------------

def build_loanword_entries() -> List[Dict]:
    """Convert loanword list to AB sequences with metadata."""
    entries = []
    seen = set()

    for greek, translit, gloss, minoan_form, category in PRE_GREEK_LOANWORDS:
        # Normalize: remove macrons, etc. for phonetic mapping
        phonetic = minoan_form.lower()
        phonetic = phonetic.replace("ā", "a").replace("ē", "e").replace("ī", "i")
        phonetic = phonetic.replace("ō", "o").replace("ū", "u")

        # Tokenize and convert to AB
        ab_tokens = phonetic_to_ab(phonetic)
        if not ab_tokens:
            continue

        # Deduplicate
        key = (greek, "".join(ab_tokens))
        if key in seen:
            continue
        seen.add(key)

        entries.append({
            "greek": greek,
            "transliteration": translit,
            "english_gloss": gloss,
            "minoan_form": minoan_form,
            "category": category,
            "phonetic": phonetic,
            "ab_tokens": ab_tokens,
            "ab_string": "".join(ab_tokens),
            "n_syllables": len(ab_tokens),
        })

    return entries


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def find_matches(
    loanword_entries: List[Dict],
    corpus_index: CorpusIndex,
    db: LinearADatabase,
    max_distance: int = 0,
) -> List[Dict]:
    """Find all matches for loanword AB sequences in the corpus."""
    sign_pool, _ = db.sign_pool
    details = []
    seen_pairs: Set[Tuple[str, int, int]] = set()

    for entry in loanword_entries:
        query = tuple(entry["ab_tokens"])
        n = len(query)
        if n == 0:
            continue

        if max_distance == 0:
            # Exact match
            if corpus_index.exact_match(query):
                locations = corpus_index.substring_locations.get(query, [])
                for ins_id, start_pos in locations:
                    key = (entry["greek"], ins_id, 0)
                    if key not in seen_pairs:
                        seen_pairs.add(key)
                        ins_info = db.get_inscription_info(ins_id)
                        ctx = check_context(ins_id, start_pos, n, db)
                        sem_score = score_semantic_plausibility(
                            entry["english_gloss"],
                            ctx["found_commodities"],
                            entry["category"],
                        )
                        details.append({
                            "greek": entry["greek"],
                            "transliteration": entry["transliteration"],
                            "english_gloss": entry["english_gloss"],
                            "minoan_form": entry["minoan_form"],
                            "category": entry["category"],
                            "query": entry["ab_string"],
                            "matched": entry["ab_string"],
                            "distance": 0,
                            "inscription_id": ins_id,
                            "gorila_id": ins_info["gorila_id"] if ins_info else "?",
                            "site": ins_info["site"] if ins_info else "?",
                            "material": ins_info["material"] if ins_info else "?",
                            "period": ins_info["minoan_period"] if ins_info else "?",
                            "semantic_score": round(sem_score, 3),
                            "found_commodities": ",".join(ctx["found_commodities"]),
                            "context_syllabograms": ctx["nearby_syllabograms"],
                        })
        else:
            # Fuzzy match
            fuzzy_results = corpus_index.fuzzy_match(query, sign_pool, max_distance)
            for matched_tuple, dist, locations in fuzzy_results:
                for ins_id, start_pos in locations:
                    key = (entry["greek"], ins_id, dist)
                    if key not in seen_pairs:
                        seen_pairs.add(key)
                        ins_info = db.get_inscription_info(ins_id)
                        ctx = check_context(ins_id, start_pos, n, db)
                        sem_score = score_semantic_plausibility(
                            entry["english_gloss"],
                            ctx["found_commodities"],
                            entry["category"],
                        )
                        details.append({
                            "greek": entry["greek"],
                            "transliteration": entry["transliteration"],
                            "english_gloss": entry["english_gloss"],
                            "minoan_form": entry["minoan_form"],
                            "category": entry["category"],
                            "query": entry["ab_string"],
                            "matched": "".join(matched_tuple),
                            "distance": dist,
                            "inscription_id": ins_id,
                            "gorila_id": ins_info["gorila_id"] if ins_info else "?",
                            "site": ins_info["site"] if ins_info else "?",
                            "material": ins_info["material"] if ins_info else "?",
                            "period": ins_info["minoan_period"] if ins_info else "?",
                            "semantic_score": round(sem_score, 3),
                            "found_commodities": ",".join(ctx["found_commodities"]),
                            "context_syllabograms": ctx["nearby_syllabograms"],
                        })

    return details


# ---------------------------------------------------------------------------
# Permutation test
# ---------------------------------------------------------------------------

def permute_query(ab_tokens: List[str], sign_pool: List[str],
                  weights: List[float], rng: random.Random) -> List[str]:
    """Randomly reassign each sign in the query based on corpus distribution."""
    n = len(ab_tokens)
    if n == 0:
        return []
    return rng.choices(sign_pool, weights=weights, k=n)


def run_permutation_test(
    loanword_entries: List[Dict],
    corpus_index: CorpusIndex,
    db: LinearADatabase,
    n_permutations: int = 1000,
    max_distance: int = 0,
) -> Tuple[int, float, float, List[Dict]]:
    """
    Permutation test: randomize sign assignments and recompute matches.
    Returns (observed, expected, p_value, observed_details).
    """
    sign_pool, weights = db.sign_pool

    # Observed matches
    observed_details = find_matches(loanword_entries, corpus_index, db, max_distance)
    observed_unique = len(set(
        (d["greek"], d["inscription_id"]) for d in observed_details
    ))

    rng = random.Random(42)  # seeded for reproducibility
    perm_counts = []

    query_lengths = [len(e["ab_tokens"]) for e in loanword_entries]

    for perm_idx in range(n_permutations):
        # Create permuted queries
        permuted_entries = []
        for idx, entry in enumerate(loanword_entries):
            length = query_lengths[idx]
            if length > 0:
                new_ab = permute_query(entry["ab_tokens"], sign_pool, weights, rng)
                permuted_entries.append({
                    **entry,
                    "ab_tokens": new_ab,
                    "ab_string": "".join(new_ab),
                })
            else:
                permuted_entries.append(entry)

        # Count matches
        perm_details = find_matches(permuted_entries, corpus_index, db, max_distance)
        perm_unique = len(set(
            (d["greek"], d["inscription_id"]) for d in perm_details
        ))
        perm_counts.append(perm_unique)

        if (perm_idx + 1) % 200 == 0:
            print(f"      ... permutation {perm_idx + 1}/{n_permutations}")

    expected = statistics.mean(perm_counts) if perm_counts else 0.0
    p_value = (sum(1 for c in perm_counts if c >= observed_unique) /
               n_permutations) if n_permutations > 0 else 1.0

    return observed_unique, expected, p_value, observed_details


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def compute_confidence_score(match: Dict, sign_freq: Dict[str, int]) -> float:
    """
    Compute a confidence score (0-100) for a match based on:
    - Length of matched sequence (longer = better)
    - Semantic context score
    - Rarity of signs involved (rarer signs = more specific)
    """
    score = 0.0

    # Length factor: longer sequences are less likely by chance
    n = len(match["query"])
    if n >= 5:
        score += 30
    elif n == 4:
        score += 20
    elif n == 3:
        score += 10
    else:
        score += 5

    # Semantic plausibility
    score += match.get("semantic_score", 0) * 30

    # Distance penalty
    if match["distance"] == 0:
        score += 20
    elif match["distance"] == 1:
        score += 5

    # Rarity factor: prefer matches involving rarer signs
    rarity_bonus = 0
    total_freq = 0
    for sign in match["query"]:
        freq = sign_freq.get(sign, 100)
        total_freq += freq
    avg_freq = total_freq / max(len(match["query"]), 1)
    # Lower avg_freq = rarer signs
    if avg_freq < 30:
        rarity_bonus = 15
    elif avg_freq < 60:
        rarity_bonus = 10
    elif avg_freq < 100:
        rarity_bonus = 5
    score += rarity_bonus

    # Penalize very common multi-matches: if distance > 0 reduce more
    if match["distance"] == 1 and n <= 3:
        score *= 0.5  # Short fuzzy matches are very uncertain

    return min(100, score)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    db = LinearADatabase(str(DB_PATH))

    print("=" * 72)
    print("  Loanword Matching: Pre-Greek Substrate Words in Linear A")
    print("=" * 72)
    print(f"\nDatabase: {DB_PATH}")
    print(f"Output directory: {OUTPUT_DIR}\n")

    # Build loanword entries
    loanword_entries = build_loanword_entries()
    print(f"Loanword lexicon: {len(PRE_GREEK_LOANWORDS)} entries")
    print(f"Mappable to AB:   {len(loanword_entries)}")

    # Statistics
    by_category: Dict[str, int] = defaultdict(int)
    for e in loanword_entries:
        by_category[e["category"]] += 1
    print("\nBy category:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Length distribution
    len_dist: Dict[int, int] = defaultdict(int)
    for e in loanword_entries:
        len_dist[e["n_syllables"]] += 1
    print("\nSequence length distribution:")
    for l in sorted(len_dist):
        print(f"  {l} signs: {len_dist[l]}")

    # Load all corpus sequences
    corpus_seqs = db.get_all_sign_sequences()
    print(f"\nCorpus: {len(corpus_seqs)} sign sequences from "
          f"{len({c['inscription_id'] for c in corpus_seqs})} inscriptions")

    # Build corpus index
    print("Building corpus index...")
    corpus_index = CorpusIndex(corpus_seqs)
    print(f"  Total substrings indexed: "
          f"{sum(len(v) for v in corpus_index.substring_locations.values())}")

    # Get sign pool info
    sign_pool, weights = db.sign_pool
    sign_freq: Dict[str, int] = {}
    conn = db.conn
    cur = conn.cursor()
    cur.execute("""
        SELECT transliteration, COUNT(*) as cnt
        FROM signs
        WHERE transliteration IS NOT NULL
          AND transliteration != ''
          AND sign_type = 'syllabogram'
        GROUP BY transliteration
    """)
    for r in cur.fetchall():
        t = r["transliteration"].strip()
        if t in LINEAR_A_AB or norm_ab(t) in LINEAR_A_AB_NORM:
            sign_freq[t] = r["cnt"]

    print(f"AB sign pool: {len(sign_pool)} distinct signs")

    # Separate by length for testing
    long_entries = [e for e in loanword_entries if e["n_syllables"] >= 3]
    short_entries = [e for e in loanword_entries if e["n_syllables"] <= 2]

    print(f"\nEntries with ≥3 signs (tested): {len(long_entries)}")
    print(f"Entries with 1-2 signs (too short): {len(short_entries)}")

    # ------------------------------------------------------------------
    # Run analysis at two distance thresholds
    # ------------------------------------------------------------------
    all_details = []

    for dist, label in [(0, "Exact (d=0)"), (1, "Near (d≤1)")]:
        test_entries = long_entries if long_entries else short_entries
        if not test_entries:
            continue

        print(f"\n{'─' * 72}")
        print(f"  {label}: Testing {len(test_entries)} entries")
        print(f"{'─' * 72}")

        print("  Running permutation test (1000 permutations)...")
        observed, expected, p_value, details = run_permutation_test(
            test_entries, corpus_index, db,
            n_permutations=1000,
            max_distance=dist,
        )

        sig = "SIGNIFICANT" if p_value < 0.05 else "not significant"
        print(f"    Observed unique matches: {observed}")
        print(f"    Expected by chance:      {expected:.2f}")
        print(f"    P-value (1000 perm.):    {p_value:.4f} ({sig})")
        print(f"    Total match records:     {len(details)}")

        # Store details with distance threshold
        for d in details:
            d["distance_threshold"] = dist
            d["confidence_score"] = round(
                compute_confidence_score(d, sign_freq), 1
            )
        all_details.extend(details)

        # Print examples
        if details:
            print(f"\n    Match examples (up to 10):")
            for d in sorted(details, key=lambda x: -x.get("semantic_score", 0))[:10]:
                print(f"      [{d['category']}] {d['greek']} ({d['english_gloss']})")
                print(f"        Minoan: {d['minoan_form']} → AB: {d['query']}")
                print(f"        Matched: {d['matched']} (d={d['distance']})")
                print(f"        {d['gorila_id']} ({d['site']}, {d['period']})")
                print(f"        Semantic score: {d['semantic_score']}")
                if d['found_commodities']:
                    print(f"        Commodities: {d['found_commodities']}")
                print()

    db.close()

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    print(f"{'=' * 72}")
    print("  Writing results...")

    fieldnames = [
        "greek", "transliteration", "english_gloss", "minoan_form",
        "category", "query", "matched", "distance", "distance_threshold",
        "inscription_id", "gorila_id", "site", "material", "period",
        "semantic_score", "confidence_score",
        "found_commodities", "context_syllabograms",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in all_details:
            writer.writerow({k: d.get(k, "") for k in fieldnames})

    print(f"  Match details CSV:  {OUTPUT_CSV}")

    # ------------------------------------------------------------------
    # Build ranked lists
    # ------------------------------------------------------------------
    # Deduplicate: keep best (lowest distance, highest confidence) per (greek, inscription_id)
    best_per_match: Dict[Tuple[str, int], Dict] = {}
    for d in all_details:
        key = (d["greek"], d["inscription_id"])
        if key not in best_per_match:
            best_per_match[key] = d
        else:
            existing = best_per_match[key]
            # Prefer lower distance, then higher confidence
            if d["distance"] < existing["distance"]:
                best_per_match[key] = d
            elif d["distance"] == existing["distance"] and \
                 d.get("confidence_score", 0) > existing.get("confidence_score", 0):
                best_per_match[key] = d

    deduped_details = list(best_per_match.values())

    # By confidence score
    ranked_by_confidence = sorted(
        deduped_details,
        key=lambda x: (x.get("confidence_score", 0),
                       x.get("semantic_score", 0),
                       -x.get("distance", 999)),
        reverse=True,
    )

    # Separate place names
    place_name_matches = [
        d for d in deduped_details if d.get("category") == "place_name"
    ]
    place_name_ranked = sorted(
        place_name_matches,
        key=lambda x: (x.get("confidence_score", 0),
                       x.get("semantic_score", 0),
                       -x.get("distance", 999)),
        reverse=True,
    )

    # Deduped versions for detail listing
    all_details_deduped = deduped_details

    # ------------------------------------------------------------------
    # Write Markdown summary
    # ------------------------------------------------------------------
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# Loanword Matching: Pre-Greek Substrate Words in Linear A\n\n")
        f.write(f"**Analysis date:** {now_str}\n\n")
        f.write(f"**Database:** `{DB_PATH.name}`\n")
        f.write(f"**Corpus sequences:** {len(corpus_seqs)}\n")
        f.write(f"**AB sign pool:** {len(sign_pool)} distinct signs\n")
        f.write(f"**Loanword lexicon:** {len(PRE_GREEK_LOANWORDS)} entries\n")
        f.write(f"**Mappable to AB:** {len(loanword_entries)}\n")
        f.write(f"**Tested (≥3 signs):** {len(long_entries)}\n")
        f.write(f"**Permutations:** 1000\n\n")

        # Statistical summary
        f.write("## Statistical Summary\n\n")
        for dist, label in [(0, "Exact (d=0)"), (1, "Near (d≤1)")]:
            obs = len(set(
                (d["greek"], d["inscription_id"])
                for d in all_details if d.get("distance_threshold") == dist
            ))
            f.write(f"### {label}\n\n")
            f.write(f"- Observed unique matches: {obs}\n")
            f.write(f"- Total match records (deduped): "
                    f"{len([d for d in all_details_deduped if d.get('distance_threshold') == dist])}\n\n")

        f.write("### Important caveat\n\n")
        f.write("Only loanwords that map to **3 or more AB signs** are included in the "
                "statistical test. Shorter sequences (1–2 signs) are too susceptible to "
                "chance matches given the corpus size. The phonetic mapping from "
                "reconstructed Minoan to Linear A AB is necessarily approximate.\n\n")

        # Top matches table
        f.write("## Top-Ranked Candidate Matches\n\n")
        f.write("| # | Greek | Gloss | AB Query | Matched | d | Conf | Sem | Site | Inscription |\n")
        f.write("|---|-------|-------|----------|---------|---|------|-----|------|-------------|\n")

        top_n = min(50, len(ranked_by_confidence))
        for i, d in enumerate(ranked_by_confidence[:top_n]):
            f.write(
                f"| {i+1} | {d['greek']} | {d['english_gloss']} | "
                f"{d['query']} | {d['matched']} | {d['distance']} | "
                f"{d.get('confidence_score', '?')} | {d.get('semantic_score', '?')} | "
                f"{d.get('site', '?')} | {d.get('gorila_id', '?')} |\n"
            )

        if len(ranked_by_confidence) > top_n:
            f.write(f"| ... | ... | ... | ... | ... | ... | ... | ... | "
                    f"({len(ranked_by_confidence) - top_n} more) |\n")
        f.write("\n")

        # Place names analysis
        f.write("## Place Name Matches (Most Reliable)\n\n")
        f.write("Place names are the most promising category because they are "
                "known to survive substrate languages with high fidelity.\n\n")

        if place_name_ranked:
            f.write("| # | Greek | AB Query | Matched | d | Conf | Site | Inscription |\n")
            f.write("|---|-------|----------|---------|---|------|------|-------------|\n")
            for i, d in enumerate(place_name_ranked[:30]):
                f.write(
                    f"| {i+1} | {d['greek']} | {d['query']} | {d['matched']} | "
                    f"{d['distance']} | {d.get('confidence_score', '?')} | "
                    f"{d.get('site', '?')} | {d.get('gorila_id', '?')} |\n"
                )
            if len(place_name_ranked) > 30:
                f.write(f"| ... | ... | ... | ... | ... | ... | ... | "
                        f"({len(place_name_ranked) - 30} more) |\n")
        else:
            f.write("*No place name matches found.*\n")
        f.write("\n")

        # All matches by category
        f.write("## All Matches by Category\n\n")
        categories_in_order = [
            "place_name", "suffix_nth", "suffix_ss", "nature",
            "flora", "animal", "architecture", "domestic",
            "body", "culture", "abstract",
        ]
        cat_names = {
            "place_name": "Place Names",
            "suffix_nth": "-nth- Suffix Words",
            "suffix_ss": "-ss- Suffix Words",
            "nature": "Nature / Geography",
            "flora": "Flora / Agriculture",
            "animal": "Animals",
            "architecture": "Architecture / Settlements",
            "domestic": "Domestic / Vessels",
            "body": "Body Parts / Human",
            "culture": "Cultural / Mythological",
            "abstract": "Abstract / Miscellaneous",
        }

        for cat in categories_in_order:
            cat_matches = [d for d in all_details_deduped if d.get("category") == cat]
            if not cat_matches:
                continue
            name = cat_names.get(cat, cat)
            f.write(f"### {name}\n\n")
            f.write(f"Total matches: {len(cat_matches)}\n\n")
            f.write("| Greek | Gloss | AB Query | Matched | d | Conf | Sem | Site |\n")
            f.write("|-------|-------|----------|---------|---|------|-----|------|\n")
            for d in sorted(cat_matches, key=lambda x: -x.get("confidence_score", 0))[:20]:
                f.write(
                    f"| {d['greek']} | {d['english_gloss']} | {d['query']} | "
                    f"{d['matched']} | {d['distance']} | {d.get('confidence_score', '?')} | "
                    f"{d.get('semantic_score', '?')} | {d.get('site', '?')} |\n"
                )
            if len(cat_matches) > 20:
                f.write(f"| ... | ... | ... | ... | ... | ... | ... | "
                        f"({len(cat_matches) - 20} more) |\n")
            f.write("\n")

        # Confident matches
        f.write("## Most Secure Matches (Confidence ≥ 50)\n\n")
        secure_matches = [d for d in ranked_by_confidence
                          if d.get("confidence_score", 0) >= 50]
        if secure_matches:
            f.write("| Greek | Gloss | AB Query | Matched | Conf | Sem | Comm | Site | Inscription |\n")
            f.write("|-------|-------|----------|---------|------|-----|------|------|-------------|\n")
            for d in secure_matches:
                f.write(
                    f"| {d['greek']} | {d['english_gloss']} | {d['query']} | "
                    f"{d['matched']} | {d.get('confidence_score', '?')} | "
                    f"{d.get('semantic_score', '?')} | {d.get('found_commodities', '-')} | "
                    f"{d.get('site', '?')} | {d.get('gorila_id', '?')} |\n"
                )
        else:
            f.write("*No highly secure matches found (confidence ≥ 50). "
                    "See ranked list for best candidates.*\n")
        f.write("\n")

        # Semantic context analysis
        f.write("## Semantic Context Analysis\n\n")
        f.write("The table below shows matches where the immediate context "
                "contains ideograms semantically related to the word's meaning.\n\n")

        semantically_plausible = [
            d for d in all_details_deduped if d.get("semantic_score", 0) >= 0.4
        ]
        if semantically_plausible:
            f.write("| Greek | Gloss | Matched | Sem Score | Commodities Found | Inscription |\n")
            f.write("|-------|-------|---------|-----------|-------------------|-------------|\n")
            for d in sorted(semantically_plausible,
                            key=lambda x: -x["semantic_score"])[:30]:
                f.write(
                    f"| {d['greek']} | {d['english_gloss']} | {d['matched']} | "
                    f"{d['semantic_score']} | {d.get('found_commodities', '-')} | "
                    f"{d.get('gorila_id', '?')} |\n"
                )
        else:
            f.write("*No semantically plausible matches found (score ≥ 0.4).*\n")
        f.write("\n")

        # Methodology
        f.write("## Methodology\n\n")
        f.write("1. **Pre-Greek substrate word compilation:** ~350 words were "
                "compiled from Beekes (2010, 2014) and related sources, "
                "covering place names, nature terms, flora, fauna, "
                "architecture, domestic items, body parts, cultural terms, "
                "and abstract concepts.\n\n")
        f.write("2. **Minoan source form reconstruction:** For each Greek word, "
                "the Greek inflectional endings (-ος, -η, -α, etc.) were "
                "removed to arrive at a hypothesized Minoan source stem.\n\n")
        f.write("3. **Linear A AB conversion:** Each reconstructed form was "
                "converted to a sequence of Linear A AB syllabograms using a "
                "phoneme-to-AB mapping following Linear B conventions "
                "(CV structure, r/l not distinguished, voiced/voiceless "
                "merged, etc.).\n\n")
        f.write("4. **Corpus search:** The database stores sign transliterations "
                "per inscription. Sequences of syllabographic signs were "
                "extracted and concatenated. For each loanword (as AB sign "
                "sequence), we check if it appears as a **contiguous substring** "
                "within any corpus sequence at Levenshtein distance ≤ 1.\n\n")
        f.write("5. **Semantic context check:** For each match, we examine "
                "nearby signs (within ±5 positions) for logograms/ideograms "
                "that are semantically related to the word's meaning (e.g., "
                "wine-related words near VIN ideograms, oil-related words "
                "near OLE ideograms).\n\n")
        f.write("6. **Permutation test:** The null hypothesis is that sign "
                "assignments are arbitrary. We randomly reassign each sign "
                "in each query (weighted by corpus frequency) while preserving "
                "the length distribution. After 1000 permutations, we compute "
                "the mean expected matches and the p-value (proportion of "
                "permutations with ≥ observed matches).\n\n")
        f.write("7. **Confidence scoring:** Each match receives a confidence "
                "score (0–100) based on sequence length, semantic plausibility, "
                "edit distance, and sign rarity.\n\n")
        f.write("### Caveats\n\n")
        f.write("- Linear A phonetic values are not fully deciphered; AB values "
                "are conventional and some signs have uncertain readings.\n")
        f.write("- Reconstructed 'Minoan' forms involve substantial uncertainty.\n")
        f.write("- Short sequences (1–2 signs) were excluded from the main test.\n")
        f.write("- The permutation test assumes independence of sign positions.\n")
        f.write("- A 'match' here means a sequence of signs that could "
                "phonetically correspond; it does not confirm etymological "
                "relationship.\n")
        f.write("- The semantic context check is limited by the small number "
                "of clearly identified logograms in the database.\n\n")

        # References
        f.write("## References\n\n")
        f.write("| Source | Citation |\n")
        f.write("|--------|----------|\n")
        f.write("| Beekes 2010 | Beekes, R.S.P. (2010). *Etymological Dictionary of Greek*. Leiden: Brill. |\n")
        f.write("| Beekes 2014 | Beekes, R.S.P. (2014). *Pre-Greek: Phonology, Morphology, Lexicon*. Leiden: Brill. |\n")
        f.write("| Furée 1896 | Fürée, B. (1896). Die 'ägdischen' Ortsnamen. *GGA* 158: 391-405. |\n")
        f.write("| Kretschmer 1896 | Kretschmer, P. (1896). *Einleitung in die Geschichte der griechischen Sprache*. Göttingen. |\n")
        f.write("| Ventris & Chadwick 1953 | Ventris, M. & Chadwick, J. (1953). Evidence for Greek Dialect in the Mycenaean Archives. *JHS* 73: 84-103. |\n")
        f.write("| GORILA | Godart, L. & Olivier, J.-P. (1976-1985). *Recueil des inscriptions en Linéaire A*. Paris. |\n")
        f.write("| Linear A corpus | Younger, J. (2016). Linear A Texts. http://people.ku.edu/~jyounger/LinearA/ |\n")

    print(f"  Markdown summary:  {OUTPUT_MD}")

    # Print final statistics
    print(f"\n{'=' * 72}")
    print("  FINAL RESULTS")
    print(f"{'=' * 72}")
    print(f"  Total match records:      {len(all_details)}")
    print(f"  Unique matched words:     {len(set(d['greek'] for d in all_details_deduped))}")
    print(f"  Unique inscriptions hit:  {len(set(d['inscription_id'] for d in all_details_deduped))}")
    print(f"  Secure matches (conf≥50): {len([d for d in all_details_deduped if d.get('confidence_score', 0) >= 50])}")
    print(f"  Place name matches (dedup): {len(place_name_ranked)}")
    print(f"\n  Output files:")
    print(f"    {OUTPUT_CSV}")
    print(f"    {OUTPUT_MD}")
    print(f"\n{'=' * 72}")
    print("  Analysis complete.")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
