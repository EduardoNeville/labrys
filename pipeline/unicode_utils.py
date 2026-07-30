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
    # ---- Syllabograms (AB shared + A-only) ----
    ("AB 01", "U+10600", "𐘀", "da", "syllabogram"),
    ("AB 02", "U+10601", "𐘁", "ro", "syllabogram"),
    ("AB 03", "U+10602", "𐘂", "pa", "syllabogram"),
    ("AB 04", "U+10603", "𐘃", "te", "syllabogram"),
    ("AB 05", "U+10604", "𐘄", "to", "syllabogram"),
    ("AB 06", "U+10605", "𐘅", "na", "syllabogram"),
    ("AB 07", "U+10606", "𐘆", "di", "syllabogram"),
    ("AB 08", "U+10607", "𐘇", "a", "syllabogram"),
    ("AB 09", "U+10608", "𐘈", "se", "syllabogram"),
    ("AB 10", "U+10609", "𐘉", "u", "syllabogram"),
    ("AB 11", "U+1060A", "𐘊", "si", "syllabogram"),
    ("AB 12", "U+1060B", "𐘋", "so", "syllabogram"),
    ("AB 13", "U+1060C", "𐘌", "me", "syllabogram"),
    ("AB 14", "U+1060D", "𐘍", "do", "syllabogram"),
    ("AB 15", "U+1060E", "𐘎", "mo", "syllabogram"),
    ("AB 16", "U+1060F", "𐘏", "qa", "syllabogram"),
    ("AB 17", "U+10610", "𐘐", "za", "syllabogram"),
    ("AB 18", "U+10611", "𐘑", "zo", "syllabogram"),
    ("AB 19", "U+10612", "𐘒", "?,zo?", "syllabogram"),
    ("AB 20", "U+10613", "𐘓", "zo?", "syllabogram"),
    ("AB 21", "U+10614", "𐘔", "mi", "syllabogram"),
    ("AB 21f", "U+10615", "𐘕", "mi?", "syllabogram"),
    ("AB 22", "U+10616", "𐘖", "pi", "syllabogram"),
    ("AB 22f", "U+10617", "𐘗", "pi?", "syllabogram"),
    ("AB 23", "U+10618", "𐘘", "mu", "syllabogram"),
    ("AB 24", "U+10619", "𐘙", "ne", "syllabogram"),
    ("AB 26", "U+1061A", "𐘚", "ru", "syllabogram"),
    ("AB 27", "U+1061B", "𐘛", "re", "syllabogram"),
    ("AB 28", "U+1061C", "𐘜", "i", "syllabogram"),
    ("AB 29", "U+1061D", "𐘝", "pu", "syllabogram"),
    ("AB 30", "U+1061E", "𐘞", "ni", "syllabogram"),
    ("AB 31", "U+1061F", "𐘟", "sa", "syllabogram"),
    ("AB 32", "U+10620", "𐘠", "?", "syllabogram"),
    ("AB 33", "U+10621", "𐘡", "ra?", "syllabogram"),
    ("AB 34", "U+10622", "𐘢", "?,pa2?", "syllabogram"),
    ("AB 35", "U+10623", "𐘣", "ti", "syllabogram"),
    ("AB 36", "U+10624", "𐘤", "jo", "syllabogram"),
    ("AB 37", "U+10625", "𐘥", "?", "syllabogram"),
    ("AB 38", "U+10626", "𐘦", "e", "syllabogram"),
    ("AB 39", "U+10627", "𐘧", "?,pi?", "syllabogram"),
    ("AB 40", "U+10628", "𐘨", "wi", "syllabogram"),
    ("AB 41", "U+10629", "𐘩", "si?", "syllabogram"),
    ("AB 42", "U+1062A", "𐘪", "ke?", "syllabogram"),
    ("AB 43", "U+1062B", "𐘫", "ai?", "syllabogram"),
    ("AB 44", "U+1062C", "𐘬", "?", "syllabogram"),
    ("AB 45", "U+1062D", "𐘭", "?,de?", "syllabogram"),
    ("AB 46", "U+1062E", "𐘮", "?,je?", "syllabogram"),
    ("AB 47", "U+1062F", "𐘯", "?", "syllabogram"),
    ("AB 48", "U+10630", "𐘰", "?,nwa?", "syllabogram"),
    ("AB 49", "U+10631", "𐘱", "?", "syllabogram"),
    ("AB 50", "U+10632", "𐘲", "pu?", "syllabogram"),
    ("AB 51", "U+10633", "𐘳", "du?", "syllabogram"),
    ("AB 52", "U+10634", "𐘴", "?", "syllabogram"),
    ("AB 53", "U+10635", "𐘵", "ri", "syllabogram"),
    ("AB 54", "U+10636", "𐘶", "wa", "syllabogram"),
    ("AB 55", "U+10637", "𐘷", "nu", "syllabogram"),
    ("AB 56", "U+10638", "𐘸", "?", "syllabogram"),
    ("AB 57", "U+10639", "𐘹", "ja", "syllabogram"),
    ("AB 58", "U+1063A", "𐘺", "?", "syllabogram"),
    ("AB 59", "U+1063B", "𐘻", "?", "syllabogram"),
    ("AB 60", "U+1063C", "𐘼", "ra", "syllabogram"),
    ("AB 61", "U+1063D", "𐘽", "?", "syllabogram"),
    ("AB 62", "U+1063E", "𐘾", "?,pte?", "syllabogram"),
    ("AB 63", "U+1063F", "𐘿", "?", "syllabogram"),
    ("AB 64", "U+10640", "𐙀", "?,swi?", "syllabogram"),
    ("AB 65", "U+10641", "𐙁", "ju?", "syllabogram"),
    ("AB 66", "U+10642", "𐙂", "ta?", "syllabogram"),
    ("AB 67", "U+10643", "𐙃", "ki", "syllabogram"),
    ("AB 68", "U+10644", "𐙄", "ro2?", "syllabogram"),
    ("AB 69", "U+10645", "𐙅", "tu", "syllabogram"),
    ("AB 70", "U+10646", "𐙆", "?,ko?", "syllabogram"),
    ("AB 71", "U+10647", "𐙇", "?", "syllabogram"),
    ("AB 72", "U+10648", "𐙈", "?", "syllabogram"),
    ("AB 73", "U+10649", "𐙉", "?", "syllabogram"),
    ("AB 74", "U+1064A", "𐙊", "ze?", "syllabogram"),
    ("AB 75", "U+1064B", "𐙋", "?", "syllabogram"),
    ("AB 76", "U+1064C", "𐙌", "ra2?", "syllabogram"),
    ("AB 77", "U+1064D", "𐙍", "ka", "syllabogram"),
    ("AB 78", "U+1064E", "𐙎", "qe", "syllabogram"),
    ("AB 79", "U+1064F", "𐙏", "zo?", "syllabogram"),
    ("AB 80", "U+10650", "𐙐", "ma", "syllabogram"),
    ("AB 81", "U+10651", "𐙑", "ku", "syllabogram"),
    ("AB 82", "U+10652", "𐙒", "?", "syllabogram"),
    ("AB 83", "U+10653", "𐙓", "?", "syllabogram"),
    ("AB 84", "U+10654", "𐙔", "?", "syllabogram"),
    ("AB 85", "U+10655", "𐙕", "?", "syllabogram"),
    ("AB 86", "U+10656", "𐙖", "?", "syllabogram"),
    ("AB 87", "U+10657", "𐙗", "?", "syllabogram"),
    ("AB 88", "U+10658", "𐙘", "?", "syllabogram"),
    ("AB 89", "U+10659", "𐙙", "?", "syllabogram"),
    ("AB 90", "U+1065A", "𐙚", "?", "syllabogram"),
    ("AB 91", "U+1065B", "𐙛", "?", "syllabogram"),
    ("AB 92", "U+1065C", "𐙜", "?", "syllabogram"),
    ("AB 93", "U+1065D", "𐙝", "?", "syllabogram"),
    ("AB 94", "U+1065E", "𐙞", "?", "syllabogram"),
    ("AB 95", "U+1065F", "𐙟", "?", "syllabogram"),
    ("AB 96", "U+10660", "𐙠", "?", "syllabogram"),
    ("AB 97", "U+10661", "𐙡", "?", "syllabogram"),
    ("AB 98", "U+10662", "𐙢", "?", "syllabogram"),
    ("AB 99", "U+10663", "𐙣", "?", "syllabogram"),
    ("AB 100", "U+10664", "𐙤", "?", "syllabogram"),
    ("AB 101", "U+10665", "𐙥", "?", "syllabogram"),
    ("AB 102", "U+10666", "𐙦", "?", "syllabogram"),
    ("AB 103", "U+10667", "𐙧", "?", "syllabogram"),
    ("AB 104", "U+10668", "𐙨", "?", "syllabogram"),
    ("AB 105", "U+10669", "𐙩", "?", "syllabogram"),
    ("AB 106", "U+1066A", "𐙪", "?", "syllabogram"),
    ("AB 107", "U+1066B", "𐙫", "?", "syllabogram"),
    ("AB 108", "U+1066C", "𐙬", "?", "syllabogram"),
    ("AB 109", "U+1066D", "𐙭", "?", "syllabogram"),
    ("AB 110", "U+1066E", "𐙮", "?", "syllabogram"),
    ("AB 111", "U+1066F", "𐙯", "?", "syllabogram"),
    ("AB 112", "U+10670", "𐙰", "?", "syllabogram"),
    ("AB 113", "U+10671", "𐙱", "?", "syllabogram"),
    ("AB 114", "U+10672", "𐙲", "?", "syllabogram"),
    ("AB 115", "U+10673", "𐙳", "?", "syllabogram"),
    ("AB 116", "U+10674", "𐙴", "?", "syllabogram"),
    ("AB 117", "U+10675", "𐙵", "?", "syllabogram"),
    ("AB 118", "U+10676", "𐙶", "?", "syllabogram"),
    ("AB 119", "U+10677", "𐙷", "?", "syllabogram"),
    ("AB 120", "U+10678", "𐙸", "?", "syllabogram"),
    ("AB 121", "U+10679", "𐙹", "?", "syllabogram"),
    ("AB 122", "U+1067A", "𐙺", "?", "syllabogram"),
    ("AB 123", "U+1067B", "𐙻", "?", "syllabogram"),
    ("AB 124", "U+1067C", "𐙼", "?", "syllabogram"),
    ("AB 125", "U+1067D", "𐙽", "?", "syllabogram"),
    ("AB 126", "U+1067E", "𐙾", "?", "syllabogram"),
    ("AB 127", "U+1067F", "𐙿", "?", "syllabogram"),
    ("AB 128", "U+10680", "𐚀", "?", "syllabogram"),
    ("AB 129", "U+10681", "𐚁", "?", "syllabogram"),
    ("AB 130", "U+10682", "𐚂", "?", "syllabogram"),
    ("AB 131", "U+10683", "𐚃", "?", "syllabogram"),
    ("AB 132", "U+10684", "𐚄", "?", "syllabogram"),
    ("AB 133", "U+10685", "𐚅", "?", "syllabogram"),
    ("AB 134", "U+10686", "𐚆", "?", "syllabogram"),
    ("AB 135", "U+10687", "𐚇", "?", "syllabogram"),
    ("AB 136", "U+10688", "𐚈", "?", "syllabogram"),
    ("AB 137", "U+10689", "𐚉", "?", "syllabogram"),

    # ---- Logograms / Ideograms ----
    ("A 301", "U+1068A", "𐚊", "siliqua?", "logogram"),
    ("A 302", "U+1068B", "𐚋", "[sheep?]", "logogram"),
    ("A 303", "U+1068C", "𐚌", "[cattle?]", "logogram"),
    ("A 304", "U+1068D", "𐚍", "[vessel?]", "logogram"),
    ("A 305", "U+1068E", "𐚎", "[fig?]", "logogram"),
    ("A 306", "U+1068F", "𐚏", "[?]", "logogram"),
    ("A 307", "U+10690", "𐚐", "[?]", "logogram"),
    ("A 308", "U+10691", "𐚑", "[wheat?]", "logogram"),
    ("A 309", "U+10692", "𐚒", "[barley?]", "logogram"),
    ("A 310", "U+10693", "𐚓", "[wine?]", "logogram"),
    ("A 311", "U+10694", "𐚔", "[oil?]", "logogram"),
    ("A 312", "U+10695", "𐚕", "[?]", "logogram"),
    ("A 313", "U+10696", "𐚖", "[?]", "logogram"),
    ("A 314", "U+10697", "𐚗", "[?]", "logogram"),
    ("A 315", "U+10698", "𐚘", "[?]", "logogram"),
    ("A 316", "U+10699", "𐚙", "[?]", "logogram"),
    ("A 317", "U+1069A", "𐚚", "[?]", "logogram"),
    ("A 318", "U+1069B", "𐚛", "[?]", "logogram"),
    ("A 319", "U+1069C", "𐚜", "[?]", "logogram"),
    ("A 320", "U+1069D", "𐚝", "[?]", "logogram"),
    ("A 321", "U+1069E", "𐚞", "[?]", "logogram"),
    ("A 322", "U+1069F", "𐚟", "[?]", "logogram"),
    ("A 323", "U+106A0", "𐚠", "[?]", "logogram"),
    ("A 324", "U+106A1", "𐚡", "[?]", "logogram"),
    ("A 325", "U+106A2", "𐚢", "[?]", "logogram"),
    ("A 326", "U+106A3", "𐚣", "[?]", "logogram"),
    ("A 327", "U+106A4", "𐚤", "[?]", "logogram"),
    ("A 328", "U+106A5", "𐚥", "[?]", "logogram"),
    ("A 329", "U+106A6", "𐚦", "[?]", "logogram"),
    ("A 330", "U+106A7", "𐚧", "[?]", "logogram"),
    ("A 331", "U+106A8", "𐚨", "[?]", "logogram"),
    ("A 332", "U+106A9", "𐚩", "[?]", "logogram"),
    ("A 333", "U+106AA", "𐚪", "[?]", "logogram"),
    ("A 334", "U+106AB", "𐚫", "[?]", "logogram"),
    ("A 335", "U+106AC", "𐚬", "[?]", "logogram"),
    ("A 336", "U+106AD", "𐚭", "[?]", "logogram"),
    ("A 337", "U+106AE", "𐚮", "[?]", "logogram"),
    ("A 338", "U+106AF", "𐚯", "[wheat]", "logogram"),
    ("A 339", "U+106B0", "𐚰", "[?]", "logogram"),
    ("A 340", "U+106B1", "𐚱", "[?]", "logogram"),
    ("A 341", "U+106B2", "𐚲", "[?]", "logogram"),
    ("A 342", "U+106B3", "𐚳", "[?]", "logogram"),
    ("A 343", "U+106B4", "𐚴", "[?]", "logogram"),
    ("A 344", "U+106B5", "𐚵", "[?]", "logogram"),
    ("A 345", "U+106B6", "𐚶", "[?]", "logogram"),
    ("A 346", "U+106B7", "𐚷", "[?]", "logogram"),
    ("A 347", "U+106B8", "𐚸", "[?]", "logogram"),
    ("A 348", "U+106B9", "𐚹", "[?]", "logogram"),
    ("A 349", "U+106BA", "𐚺", "[?]", "logogram"),
    ("A 350", "U+106BB", "𐚻", "[?]", "logogram"),
    ("A 351", "U+106BC", "𐚼", "[?]", "logogram"),
    ("A 352", "U+106BD", "𐚽", "[?]", "logogram"),
    ("A 353", "U+106BE", "𐚾", "[?]", "logogram"),
    ("A 354", "U+106BF", "𐚿", "[?]", "logogram"),
    ("A 355", "U+106C0", "𐛀", "[?]", "logogram"),
    ("A 356", "U+106C1", "𐛁", "[?]", "logogram"),
    ("A 357", "U+106C2", "𐛂", "[?]", "logogram"),
    ("A 358", "U+106C3", "𐛃", "[?]", "logogram"),
    ("A 359", "U+106C4", "𐛄", "[?]", "logogram"),
    ("A 360", "U+106C5", "𐛅", "[?]", "logogram"),
    ("A 361", "U+106C6", "𐛆", "[?]", "logogram"),
    ("A 362", "U+106C7", "𐛇", "[?]", "logogram"),
    ("A 363", "U+106C8", "𐛈", "[?]", "logogram"),
    ("A 364", "U+106C9", "𐛉", "[?]", "logogram"),
    ("A 365", "U+106CA", "𐛊", "[?]", "logogram"),
    ("A 366", "U+106CB", "𐛋", "[?]", "logogram"),
    ("A 367", "U+106CC", "𐛌", "[?]", "logogram"),
    ("A 368", "U+106CD", "𐛍", "[?]", "logogram"),
    ("A 369", "U+106CE", "𐛎", "[?]", "logogram"),
    ("A 370", "U+106CF", "𐛏", "[?]", "logogram"),
    ("A 371", "U+106D0", "𐛐", "[?]", "logogram"),
    ("A 372", "U+106D1", "𐛑", "[?]", "logogram"),
    ("A 373", "U+106D2", "𐛒", "[?]", "logogram"),
    ("A 374", "U+106D3", "𐛓", "[?]", "logogram"),
    ("A 375", "U+106D4", "𐛔", "[?]", "logogram"),
    ("A 376", "U+106D5", "𐛕", "[?]", "logogram"),
    ("A 377", "U+106D6", "𐛖", "[?]", "logogram"),
    ("A 378", "U+106D7", "𐛗", "[?]", "logogram"),
    ("A 379", "U+106D8", "𐛘", "[?]", "logogram"),
    ("A 380", "U+106D9", "𐛙", "[?]", "logogram"),
    ("A 381", "U+106DA", "𐛚", "[?]", "logogram"),
    ("A 382", "U+106DB", "𐛛", "[?]", "logogram"),
    ("A 383", "U+106DC", "𐛜", "[?]", "logogram"),
    ("A 384", "U+106DD", "𐛝", "[?]", "logogram"),
    ("A 385", "U+106DE", "𐛞", "[?]", "logogram"),
    ("A 386", "U+106DF", "𐛟", "[?]", "logogram"),
    ("A 387", "U+106E0", "𐛠", "[?]", "logogram"),
    ("A 388", "U+106E1", "𐛡", "[?]", "logogram"),
    ("A 389", "U+106E2", "𐛢", "[?]", "logogram"),
    ("A 390", "U+106E3", "𐛣", "[?]", "logogram"),
    ("A 391", "U+106E4", "𐛤", "[?]", "logogram"),
    ("A 392", "U+106E5", "𐛥", "[?]", "logogram"),
    ("A 393", "U+106E6", "𐛦", "[?]", "logogram"),
    ("A 394", "U+106E7", "𐛧", "[?]", "logogram"),
    ("A 395", "U+106E8", "𐛨", "[?]", "logogram"),
    ("A 396", "U+106E9", "𐛩", "[?]", "logogram"),
    ("A 397", "U+106EA", "𐛪", "[?]", "logogram"),
    ("A 398", "U+106EB", "𐛫", "[?]", "logogram"),
    ("A 399", "U+106EC", "𐛬", "[?]", "logogram"),
    ("A 400", "U+106ED", "𐛭", "[?]", "logogram"),
    ("A 401", "U+106EE", "𐛮", "[?]", "logogram"),
    ("A 402", "U+106EF", "𐛯", "[?]", "logogram"),

    # ---- Fractions ----
    ("A 701", "U+106F0", "𐛰", "J (1/2?)", "fraction"),
    ("A 702", "U+106F1", "𐛱", "K (1/4?)", "fraction"),
    ("A 703", "U+106F2", "𐛲", "L (1/3?)", "fraction"),
    ("A 704", "U+106F3", "𐛳", "M (2/3?)", "fraction"),
    ("A 705", "U+106F4", "𐛴", "N (3/4?)", "fraction"),
    ("A 706", "U+106F5", "𐛵", "O (1/6?)", "fraction"),
    ("A 707", "U+106F6", "𐛶", "P (5/6?)", "fraction"),
    ("A 708", "U+106F7", "𐛷", "Q (1/8?)", "fraction"),
    ("A 709", "U+106F8", "𐛸", "R (3/8?)", "fraction"),
    ("A 710", "U+106F9", "𐛹", "S (5/8?)", "fraction"),
    ("A 711", "U+106FA", "𐛺", "T (7/8?)", "fraction"),
    ("A 712", "U+106FB", "𐛻", "U (1/10?)", "fraction"),
    ("A 713", "U+106FC", "𐛼", "V (3/10?)", "fraction"),
    ("A 714", "U+106FD", "𐛽", "W (7/10?)", "fraction"),
    ("A 715", "U+106FE", "𐛾", "X (9/10?)", "fraction"),
    ("A 716", "U+106FF", "𐛿", "Y (1/5?)", "fraction"),
    ("A 717", "U+10700", "𐜀", "Z (2/5?)", "fraction"),
    ("A 718", "U+10701", "𐜁", "AA (4/5?)", "fraction"),
    ("A 719", "U+10702", "𐜂", "BB (1/16?)", "fraction"),
    ("A 720", "U+10703", "𐜃", "CC (3/16?)", "fraction"),
    ("A 721", "U+10704", "𐜄", "DD (5/16?)", "fraction"),
    ("A 722", "U+10705", "𐜅", "EE (7/16?)", "fraction"),
    ("A 723", "U+10706", "𐜆", "??", "fraction"),
    ("A 724", "U+10707", "𐜇", "??", "fraction"),
    ("A 725", "U+10708", "𐜈", "??", "fraction"),
    ("A 726", "U+10709", "𐜉", "??", "fraction"),
    ("A 727", "U+1070A", "𐜊", "??", "fraction"),
    ("A 728", "U+1070B", "𐜋", "??", "fraction"),
    ("A 729", "U+1070C", "𐜌", "??", "fraction"),
    ("A 730", "U+1070D", "𐜍", "??", "fraction"),

    # ---- Numerals ----
    ("NUM 1",  "U+1070E", "𐜎", "1", "numeral"),
    ("NUM 10", "U+1070F", "𐜏", "10", "numeral"),
    ("NUM 100","U+10710", "𐜐", "100", "numeral"),
    ("NUM 1000","U+10711", "𐜑", "1000", "numeral"),
    ("NUM 10000","U+10712","𐜒", "10000", "numeral"),

    # ---- Metrical signs ----
    ("MET A", "U+10713", "𐜓", "weigh A", "metrical"),
    ("MET B", "U+10714", "𐜔", "weigh B", "metrical"),
    ("MET C", "U+10715", "𐜕", "weigh C", "metrical"),
    ("MET D", "U+10716", "𐜖", "weigh D", "metrical"),
    ("MET E", "U+10717", "𐜗", "weigh E", "metrical"),
    ("MET F", "U+10718", "𐜘", "weigh F", "metrical"),
    ("MET G", "U+10719", "𐜙", "weigh G", "metrical"),
    ("MET H", "U+1071A", "𐜚", "weigh H", "metrical"),
    ("MET I", "U+1071B", "𐜛", "weigh I", "metrical"),
    ("MET J", "U+1071C", "𐜜", "weigh J", "metrical"),

    # ---- Additional signs ----
    ("A 500", "U+1071D", "𐜝", "[?]", "logogram"),
    ("A 501", "U+1071E", "𐜞", "[?]", "logogram"),
    ("A 502", "U+1071F", "𐜟", "[?]", "logogram"),
    ("A 503", "U+10720", "𐜠", "[?]", "logogram"),
    ("A 504", "U+10721", "𐜡", "[?]", "logogram"),
    ("A 505", "U+10722", "𐜢", "[?]", "logogram"),
    ("A 506", "U+10723", "𐜣", "[?]", "logogram"),
    ("A 507", "U+10724", "𐜤", "[?]", "logogram"),
    ("A 508", "U+10725", "𐜥", "[?]", "logogram"),
    ("A 509", "U+10726", "𐜦", "[?]", "logogram"),
    ("A 510", "U+10727", "𐜧", "[?]", "logogram"),

    # ---- Ligatures / composite signs ----
    ("A LB", "U+10728", "𐜨", "ligature", "ligature"),
    ("A 604", "U+10729", "𐜩", "ligature", "ligature"),
    ("A 606", "U+1072A", "𐜪", "ligature", "ligature"),
    ("A 608", "U+1072B", "𐜫", "ligature", "ligature"),
    ("A 609", "U+1072C", "𐜬", "ligature", "ligature"),
    ("A 611", "U+1072D", "𐜭", "ligature", "ligature"),
    ("A 612", "U+1072E", "𐜮", "ligature", "ligature"),
    ("A 613", "U+1072F", "𐜯", "ligature", "ligature"),
    ("A 614", "U+10730", "𐜰", "ligature", "ligature"),
    ("A 615", "U+10731", "𐜱", "ligature", "ligature"),
    ("A 616", "U+10732", "𐜲", "ligature", "ligature"),
    ("A 617", "U+10733", "𐜳", "ligature", "ligature"),
    ("A 618", "U+10734", "𐜴", "ligature", "ligature"),
    ("A 619", "U+10735", "𐜵", "ligature", "ligature"),
    ("A 620", "U+10736", "𐜶", "ligature", "ligature"),

    # ---- Spare / unfilled code points (U+10737–U+1075F) ----
    # U+10737–U+10747: additional complex signs
    ("A 621", "U+1073C", "𐜼", "?", "ligature"),
    ("A 622", "U+1073D", "𐜽", "?", "ligature"),
    ("A 623", "U+1073E", "𐜾", "?", "ligature"),
    ("A 624", "U+1073F", "𐜿", "?", "ligature"),

    # ---- Vase shapes (U+10740–U+1075F) ----
    ("VASE 1",  "U+10740", "𐝀", "vase", "logogram"),
    ("VASE 2",  "U+10741", "𐝁", "vase", "logogram"),
    ("VASE 3",  "U+10742", "𐝂", "vase", "logogram"),
    ("VASE 4",  "U+10743", "𐝃", "vase", "logogram"),
    ("VASE 5",  "U+10744", "𐝄", "vase", "logogram"),
    ("VASE 6",  "U+10745", "𐝅", "vase", "logogram"),
    ("VASE 7",  "U+10746", "𐝆", "vase", "logogram"),
    ("VASE 8",  "U+10747", "𐝇", "vase", "logogram"),
    ("VASE 9",  "U+10748", "𐝈", "vase", "logogram"),
    ("VASE 10", "U+10749", "𐝉", "vase", "logogram"),
    ("VASE 11", "U+1074A", "𐝊", "vase", "logogram"),
    ("VASE 12", "U+1074B", "𐝋", "vase", "logogram"),
    ("VASE 13", "U+1074C", "𐝌", "vase", "logogram"),

    # ---- Further logograms / special signs ----
    ("A 560", "U+1074D", "𐝍", "[?]", "logogram"),
    ("A 561", "U+1074E", "𐝎", "[?]", "logogram"),
    ("A 562", "U+1074F", "𐝏", "[?]", "logogram"),
    ("A 563", "U+10750", "𐝐", "[?]", "logogram"),
    ("A 564", "U+10751", "𐝑", "[?]", "logogram"),
    ("A 565", "U+10752", "𐝒", "[?]", "logogram"),
    ("A 566", "U+10753", "𐝓", "[?]", "logogram"),
    ("A 567", "U+10754", "𐝔", "[?]", "logogram"),
    ("A 568", "U+10755", "𐝕", "[?]", "logogram"),

    # ---- Adjuncts ----
    ("ADJ 001", "U+10757", "𐝗", "adjunct", "adjunct"),
    ("ADJ 002", "U+10758", "𐝘", "adjunct", "adjunct"),
    ("ADJ 003", "U+10759", "𐝙", "adjunct", "adjunct"),
    ("ADJ 004", "U+1075A", "𐝚", "adjunct", "adjunct"),
    ("ADJ 005", "U+1075B", "𐝛", "adjunct", "adjunct"),
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
