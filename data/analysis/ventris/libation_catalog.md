# Libation Formula Catalog (Corrected Corpus) — Reference Document

**Generated** by `pipeline/libation_catalog.py` from `data/database/lineara_full.db`.
Do not hand-edit: `pipeline/guards.py` re-derives this file and fails on any drift.

**Convention.** One token per sign row, in reading order. `|` = word divider / break. `?` = sign with no conventional value recorded in the DB. Tokens are the DB's `transliteration` column, lowercased — i.e. the Linear B transfer reading, not a Minoan reading.

## Formula words (whole corpus, not just the vessel sites)

| Slot | Signs | Occurrences | Inscriptions |
|------|-------|-------------|--------------|
| opening (a-ta-i-*301-wa-ja) | `AB 08 AB 59 AB 28 A 301 AB 54 AB 57` | 11 | IOZa2, IOZa3, IOZa7, KOZa1, PKZa12, SYZa1, SYZa2, SYZa3, SYZa4, SYZa8, TLZa1 |
| ja-sa-sa-ra-me | `AB 57 AB 31 AB 31 AB 60 AB 13` | 9 | IOZa12, IOZa16, IOZa2@10, IOZa6@15, IOZa9, PKZa27, PLZf1@8, PSZa2@10, TLZa1@10 |
| u-na-ka-na-si | `AB 10 AB 06 AB 77 AB 06 AB 41` | 6 | IOZa2@15, IOZa9@5, KOZa1@15, PKZa27@5, PKZa8@16, SYZa2@11 |
| i-pi-na-ma | `AB 28 AB 39 AB 06 AB 80` | 6 | APZa2@2, IOZa15, IOZa2@20, KOZa1@20, TLZa1@19, VRYZa1 |
| si-ru-te | `AB 41 AB 26 AB 04` | 7 | IOZa14, IOZa15@4, IOZa2@24, KOZa1@24, SYZa3@10, TLZa1@23, VRYZa1@4 |

The opening occurs **11** times, at position 0 in **11** of them. It is the only slot whose pattern includes the logogram `A 301` — a syllabogram-only transcription of this slot is a transcription error (see `libation_recovered.md`'s corrections note).

**Slot order.** In the 9 texts carrying two or more formula slots, the slots appear in the documented order in **9 of 9**.

## Other recurring elements

| Element | Signs | Occurrences | Inscriptions |
|---------|-------|-------------|--------------|
| di-ki-te-te (Palaikastro deity root) | `AB 07 AB 67 AB 04 AB 04` | 3 | PKZa11@7, PKZa15@1, PKZa8@4 |
| ja-di-ki-tu | `AB 57 AB 07 AB 67 AB 69` | 1 | IOZa2@6 |
| di-ki-tu-ja | `AB 07 AB 67 AB 69 AB 57` | 1 | IOZa2@7 |
| i-da (Mt. Ida) | `AB 28 AB 01` | 13 | ARZf1, ARZf2, CRZg4, IOZa11@8, KOZa1@12, NEZa1, PH6@12, PKZa17, PKZa18@1, PKZa9@4, SYZa1@6, ZA21b |

## Full sequences — the vessel sites

### Iouktas (IOZa)

- **IOZa11** (10 signs): `na | da da | ? u ti nu i na i da | ? ? ? ? |`
- **IOZa12** (7 signs): `| | ja sa sa ra me | i ti |`  — ja-sa-sa-ra-me
- **IOZa13** (2 signs): `| ma i ? |`
- **IOZa14** (5 signs): `si ru te | i di ? |`  — si-ru-te
- **IOZa15** (7 signs): `i pi na ma | si ru te | ?`  — i-pi-na-ma, si-ru-te
- **IOZa16** (11 signs): `arom | ja sa sa ra ? | u na ru ka na si ? ?`  — ja-sa-sa-ra-me
- **IOZa2** (35 signs): `a ta i *301 wa ja | ja di ki tu | ja sa sa ra me | u na ka na si | i pi na ma | ? si ru te ta na ra te u ti nu | i | ? | ? | |`  — opening (a-ta-i-*301-wa-ja), ja-sa-sa-ra-me, u-na-ka-na-si, i-pi-na-ma, si-ru-te
- **IOZa3** (7 signs): `| a ta i *301 wa ja | au |`  — opening (a-ta-i-*301-wa-ja)
- **IOZa4** (2 signs): `*301 wa ? |`
- **IOZa5** (8 signs): `i ja re di ja | i ja pa ? |`
- **IOZa6** (20 signs): `ta na i *301 u ti nu | i na ta i zu di si ka | ja sa sa ra me |`  — ja-sa-sa-ra-me
- **IOZa7** (9 signs): `a ta i *301 wa ja | ja ti *321 |`  — opening (a-ta-i-*301-wa-ja)
- **IOZa8** (6 signs): `a na ti *301 wa ja ? |`
- **IOZa9** (10 signs): `ja sa sa ra me ? u na ka na si ? ?`  — ja-sa-sa-ra-me, u-na-ka-na-si
- **IOZa<1>** (3 signs): `a je sa`

### Kophinas (KOZa)

- **KOZa1** (27 signs): `a ta i *301 wa ja tu ru sa | du *314 re | i da a | u na ka na si | i pi na ma | si ru te`  — opening (a-ta-i-*301-wa-ja), u-na-ka-na-si, i-pi-na-ma, si-ru-te

### Palaikastro (PKZa)

- **PKZa10** (7 signs): `si | i pi na mi na | si ? |`
- **PKZa11** (42 signs): `a ta i *301 wa e | a di ki te te | ? re | pi te ri | a ko a ne | a ? sa ra me | u na ru ka na ti | ? i na mi na si ru | | | i na ja pa qa ? ? ? ?`
- **PKZa12** (29 signs): `a ta i *301 wa ja | a di ki te ? ? | | ra me ne u na ru ka ja si a pa du pa ja ja pa qa ? ? ? ? ? ? | | ? | ? ? ?`  — opening (a-ta-i-*301-wa-ja)
- **PKZa14** (6 signs): `tu me ? | ja sa sa ? |`
- **PKZa15** (8 signs): `ja di ki te te du pu₂ re ? |`
- **PKZa16** (5 signs): `to sa | pu₂ ? ja ? |`
- **PKZa17** (2 signs): `i da | | |`
- **PKZa18** (5 signs): `te | i da | ja ja ? |`
- **PKZa20** (3 signs): `u na ka ? |`
- **PKZa27** (10 signs): `ja sa sa ra me u na ka na si`  — ja-sa-sa-ra-me, u-na-ka-na-si
- **PKZa28** (2 signs): `pu₂ re | *418+l2 𐜶 |`
- **PKZa4** (4 signs): `a sa sa ra |`
- **PKZa8** (23 signs): `nu | pa₃ e | ja di ki te te *307 pu₂ re | tu me i ? sa u na ka na si ? i pi ? ? |`  — u-na-ka-na-si
- **PKZa9** (7 signs): `| ja u pa ma i da | di | | ? |`

### Arkalochori (ARKH) — no formula slots

- **ARKH1a** (17 signs): `ta pi | ? ? ki | | ? ra ? ? a su *118 ne 2 ¹⁄₂ ? a pa mi ki sa ne ? ? | | ? ? ? ? |`
- **ARKH1b** (5 signs): `a ? re 3 ? pa₃ ? ? — ? 8 — | ? 𐄎`
- **ARKH2** (23 signs): `si da te ku ra *131b 5 a si da to i 12 ? *301 se de *21f *118 6 ? su pu wa 4 ? mi ? | |`
- **ARKH3a** (11 signs): `ka ne gra ? ¹⁄₅ oliv 3 ? *131b 2 2 ? *317 ? | ki nu 13 te 2 ? *317 2 ? *312 ? ku 3 ? 𐄈 ? 𐄈 | | ? 𐄉`
- **ARKH3b** (7 signs): `ja pi gra 6 ? pi gra 1 ? ole ? | 2 ? 4 vin 1 ? 𐄊 | ? 𐄇 |`
- **ARKH4a** (14 signs): `| ni ta ? ta re 5 ? a | 4 ? de su | *47 5 ? pi ti ne a ? | ? ? ? ? | |`
- **ARKH4b** (12 signs): `| | re 10 ? ? de 10 ? i *47 ? a ki ro 3 za si zu 3 | ? ? | | 𐄉 |`
- **ARKH5** (10 signs): `a du ni ta na 41 ? 7 a da gra 40 ? *131b 6 ? ? | ? | |`
- **ARKH6** (6 signs): `da na tu | ku ? ri ? | | |`
- **ARKH7** (1 signs): `| — *308 ¹⁄₅ |`
- **ARKHZc8** (3 signs): `*306 ta je`
- **ARKHZf9** (9 signs): `ja ki si ki nu | mi da ma ra₂ |`

### Prassa (PRZa)

- **PRZa1** (13 signs): `ta na su te ke ? to i ja ? sa sa *802 me ?`

### Syme (SYZa)

- **SYZa1** (10 signs): `a ta i *301 wa ja | i da mi | ja ? |`  — opening (a-ta-i-*301-wa-ja)
- **SYZa10** (4 signs): `qa sa ra ku`
- **SYZa11** (2 signs): `| ro qa |`
- **SYZa12** (1 signs): `| a |`
- **SYZa2** (19 signs): `a ta i *301 wa ja | ja su ma tu oliv 1 u na ka na si ole a ja`  — opening (a-ta-i-*301-wa-ja), u-na-ka-na-si
- **SYZa3** (13 signs): `a ta i *301 wa ja se ka na si si ru te ? ?`  — opening (a-ta-i-*301-wa-ja), si-ru-te
- **SYZa4** (13 signs): `a ta i *301 wa ja | ja i nwa za | pa₃ ni wi`  — opening (a-ta-i-*301-wa-ja)
- **SYZa5** (5 signs): `mi ja | ja wa pa₃ ? |`
- **SYZa6** (4 signs): `da se ra te`
- **SYZa8** (8 signs): `a ta i *301 wa ja | ja ja ? |`  — opening (a-ta-i-*301-wa-ja)
- **SYZa9** (5 signs): `ja pa ra ja se`

### Psykhro (PSZa)

- **PSZa2** (15 signs): `re i ke ? na i *301 ti | 𐄌 ja ti | ja sa sa ra me | ? ? |`  — ja-sa-sa-ra-me

### Platanos (PLZf)

- **PLZf1** (22 signs): `ta | wi te ja mu | u qe ti | ja sa sa ra me | ta nu ni ki na | ni nu ni | | | i | ? | |`  — ja-sa-sa-ra-me

## Reading notes

- Formula slots were found by sign-ID pattern across the whole corpus; the vessel-site sequences above are the genre's texts, and some formula carriers are not vessels (the counts in the table are corpus-wide).
- `A 301` is a **logogram**, not a syllabogram: it stands inside the opening (`a-ta-i-*301-wa-ja`) and its 500-odd occurrences were once mis-attributed to the syllabogram AB 85 (`verification_audit.md`, Phase 12 addendum).
- Word dividers are rendered as `|` rather than omitted, so the token count of a line is the sign count of the inscription — the property the hand-written version could not guarantee.
- i-pi-na-ma rests on AB 39, whose value is `pi?` (uncertain) in `la_lb_mapping.csv`; the sign *sequence* is what the corpus supports.
