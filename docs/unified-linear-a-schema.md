# Unified Data Schema for Linear A Inscriptions

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Author:** Agent 2 — Schema Design Task  
**License:** CC-BY 4.0  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Schema Layers](#2-schema-layers)
3. [Field Reference by Tier](#3-field-reference-by-tier)
4. [TEI ODD Customization](#4-tei-odd-customization)
5. [JSON-LD Context & JSON Schema](#5-json-ld-context--json-schema)
6. [Controlled Vocabularies](#6-controlled-vocabularies)
7. [Minimum Required vs Optional](#7-minimum-required-vs-optional)
8. [Examples](#8-examples)
9. [Crosswalk: TEI ↔ JSON-LD ↔ SigLA ↔ lineara.xyz](#9-crosswalk)
10. [References](#10-references)

---

## 1. Architecture Overview

This schema defines a **dual-format** representation for Linear A inscriptions:

- **TEI-XML** (via a custom ODD derived from TEI EpiDoc) — the canonical "source of truth" for long-term archival
- **JSON-LD** (via JSON Schema) — for web APIs, data exchange, and integration with the IIIF Presentation API

The schema is organised into **seven tiers** mirroring the task specification:

| Tier | Name | Domain |
|------|------|--------|
| 1 | Text-Level Metadata | Inscription identity, provenance, dating |
| 2 | Sign-Level Annotation | Individual sign instances with IDs & positioning |
| 3 | Paleographic Tier | Hands, ductus, shape variants, corrections |
| 4 | Structural Tier | Lines, sides, rulings, word boundaries |
| 5 | Semantic Tier | Logograms, fractions, numerals, commodities |
| 6 | Relational Tier | Cross-references to other writing systems |
| 7 | Image Tier | IIIF URLs, copyright, multi-spectral bands |

### Guiding Principles

1. **Separation of Concerns**: Each tier is independently usable. A museum catalogue may only need Tier 1 + Tier 7; a paleographer needs Tier 2 + Tier 3.
2. **Open World Assumption**: Absence of a field does not imply absence of the property — it is simply unknown.
3. **Unicode-First**: All Linear A characters are represented as Unicode Aegean Block code points (U+10600–U+1077F). Transliteration strings accompany the Unicode for human readability.
4. **IIIF Compatibility**: Image references follow the IIIF Presentation API 3.0.
5. **Round-Trippable**: TEI ↔ JSON-LD conversion should be lossless for all documented fields.

---

## 2. Schema Layers

```
┌─────────────────────────────────────────────┐
│              JSON-LD (Web API)              │
│  Compact, linked-data ready, IIIF-friendly  │
├─────────────────────────────────────────────┤
│                   ▲ ▼                        │
│           XSLT / custom mapping             │
│                   ▲ ▼                        │
├─────────────────────────────────────────────┤
│           TEI-XML (EpiDoc ODD)              │
│  Canonical archival format, rich markup     │
├─────────────────────────────────────────────┤
│                   ▲ ▼                        │
│           Controlled Vocabularies           │
│  SKOS concept schemes for all coded fields  │
└─────────────────────────────────────────────┘
```

---

## 3. Field Reference by Tier

### 3.1 Tier 1 — Text-Level Metadata

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| Inscription ID (GORILA) | `//teiHeader/fileDesc/titleStmt/idno[@type="GORILA"]` | `gorilaId` | string (pattern: `[A-Z]{2,4} \d+`) | **MUST** |
| GORILA Volume/Page | `//teiHeader/fileDesc/biblStruct/monogr/biblScope[@unit="vol"]` | `gorilaVolume` | integer | optional |
| Alternative IDs | `//teiHeader/fileDesc/titleStmt/idno[@type="alternative"]` | `alternativeIds` | string[] | optional |
| Findspot Site | `//sourceDesc/origPlace[@type="findspot"]/placeName` | `findspot.site` | string (from CV) | **MUST** |
| Findspot Coordinates (lat/lon) | `//sourceDesc/origPlace/geo` | `findspot.coordinates` | `{"lat": number, "lon": number}` | optional |
| Findspot Specific Context (room, trench) | `//sourceDesc/origPlace/desc` | `findspot.context` | string | optional |
| Date — Minoan Period | `//profileDesc/creation/date[@type="minoanPeriod"]/@period` | `date.minoanPeriod` | string (from CV) | **MUST** |
| Date — Calendar (BCE range) | `//profileDesc/creation/date[@type="bceRange"]` | `date.bceRange` | `{"from": int, "to": int}` | optional |
| Date — Notes | `//profileDesc/creation/date/desc` | `date.notes` | string | optional |
| Material | `//physDesc/objectDesc/supportDesc/support/material` | `material` | string (from CV) | **MUST** |
| Object Type | `//physDesc/objectDesc/objectType` | `objectType` | string (from CV) | **MUST** |
| Preservation Status | `//physDesc/condition/@state` | `preservation.state` | string (from CV) | **MUST** |
| Preservation Description | `//physDesc/condition/p` | `preservation.description` | string | optional |
| Dimensions (height, width, depth, diameter, unit) | `//physDesc/objectDesc/dimensions` | `dimensions` | object | optional |
| Current Location / Institution | `//msIdentifier/institution` | `currentLocation.institution` | string | optional |
| Current Location / Collection | `//msIdentifier/collection` | `currentLocation.collection` | string | optional |
| Current Location / Inventory Number | `//msIdentifier/idno` | `currentLocation.inventoryNumber` | string | optional |
| Primary Publication Reference | `//teiHeader/fileDesc/biblStruct/monogr` | `publication` | object | **MUST** |
| Secondary Bibliography | `//teiHeader/fileDesc/biblList` | `bibliography` | object[] | optional |

### 3.2 Tier 2 — Sign-Level Annotation

*Per individual sign occurrence on the inscription.*

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| Sign Sequence Number | `//text/body/ab/g[@n]` | `signs[].sequence` | integer | **MUST** |
| Sign ID (Bennett AB number) | `@type="bennett"` on `<g>` | `signs[].bennettId` | string (pattern: `(AB|A)\s?\d{2,3}`) | **MUST** |
| Unicode Code Point | `@ref` on `<g>` pointing to Uni. Aegean | `signs[].unicode` | string (U+106xx) | **MUST** (except uncertain signs) |
| Unicode Character | (implied by ref) | `signs[].character` | string (literal) | optional |
| Visual Variant ID (SigLA) | `@ana` pointing to `#sigla-*` | `signs[].siglaVariantId` | URI | optional |
| Bounding Box on Image | `<surface>/<zone>` | `signs[].boundingBox` | object (see JSON Schema) | optional |
| Transliteration Character | `<g><seg type="translit">` | `signs[].transliteration` | string | optional |
| Confidence in Sign Identification | `<certainty @degree>` | `signs[].confidence` | float [0..1] | optional |
| Sign Type (syllabogram / logogram / fraction / numeral / adjunct) | `@ana` pointing to sign type CV | `signs[].signType` | string (from CV) | **MUST** |
| Is Ligature Component? | `<g type="ligatureComponent">` | `signs[].isLigatureComponent` | boolean | optional |

### 3.3 Tier 3 — Paleographic Tier

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| Scribal Hand ID | `//profileDesc/handNote[@xml:id]` | `paleography.scribalHandId` | string | optional |
| Scribal Hand Certainty | `<handNote/@certainty>` | `paleography.scribalHandCertainty` | float [0..1] | optional |
| Sign Shape Classification | `<g @rend>` with reference to shape taxonomy | `signs[].shapeClass` | string (from CV) | optional |
| Ligature Composition | `<g type="ligature"><g>` nested | `signs[].ligatureOf` | string[] (Bennett IDs) | optional |
| Erasure Mark | `<del type="erasure">` | `signs[].erasure` | boolean | optional |
| Correction/Overwriting | `<add type="correction">` above `<del>` | `signs[].correction` | `{"original": string, "correctedTo": string}` | optional |
| Ductus Characteristics | `<handNote/desc>` | `paleography.ductusNotes` | string | optional |
| Ink/Incising Method | `<physDesc/scriptDesc/scriptNote>` | `paleography.writingMethod` | string (from CV) | optional |

### 3.4 Tier 4 — Structural Tier

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| Line Number | `<lb @n>` | `structure.lines[].number` | integer/string | **MUST** |
| Tablet Side | `<div type="side">` | `structure.side` | "recto" / "verso" / "edge" | optional |
| Ruling Lines | `<lineGroup type="ruling">` | `structure.lines[].ruling` | boolean | optional |
| Word Boundary | `<g/>` followed by `<space/>` or `<pc>` | `structure.words[].boundary` | integer (sign seq index) | **MUST** |
| Punctuation / Word Divider | `<pc type="wordDivider">` | `structure.wordDividers[]` | integer[] | optional |
| Line Continuation | `<cb/>` or explicit notation | `structure.lines[].continuesFrom` | ref | optional |
| Damage Span | `<damage/>` | `structure.lines[].damaged` | boolean | optional |
| Lacuna | `<gap/>` | `structure.lacunae[]` | `{"signs": int, "position": int}` | optional |

### 3.5 Tier 5 — Semantic Tier

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| Logogram Designation | `<g type="logogram">` | `signs[].semantics.logogramOf` | string (from CV) | conditional |
| Fraction Value | `<g type="fraction">` with numeric value | `signs[].semantics.fractionValue` | string (e.g., "1/2", "1/3") | conditional |
| Numeral Value (integer) | `<num value="">` | `signs[].semantics.numericValue` | integer | conditional |
| Commodity Classification | `<g type="logogram">` with `@ana` = commodity CV | `signs[].semantics.commodity` | string (from CV) | conditional |
| Quantity Unit | `<measure unit="">` | `signs[].semantics.unit` | string | optional |
| Metrological Value | `<measure commodity="">` | `signs[].semantics.metrologicalValue` | string | optional |

### 3.6 Tier 6 — Relational Tier

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| Linear B DMic Sign Number | `@corresp` pointing to DMic entry | `relations.linearB[].dmicId` | string | optional |
| Linear B Phonetic Value | `@sameAs` or `@equiv` | `relations.linearB[].phoneticValue` | string | optional |
| Cypro-Minoan Sign Parallel | `@corresp` pointing to CM entry | `relations.cyproMinoan[].signId` | string | optional |
| Cretan Hieroglyphic Parallel | `@corresp` pointing to CH entry | `relations.cretanHiero[].signId` | string | optional |
| Eteocretan Connection | `@corresp` pointing to Eteocretan text | `relations.eteocretan[].textId` | string | optional |
| Scholarly Disagreement | `<note type="debate">` | `relations.scholarlyNotes[]` | string | optional |
| Related Inscriptions | `//teiHeader/xenoData/relatedInscriptions` | `relations.relatedInscriptions[]` | string[] (GORILA IDs) | optional |

### 3.7 Tier 7 — Image Tier

| Field | TEI Path | JSON-LD Key | Type | Required |
|-------|----------|-------------|------|----------|
| IIIF Image Service URL | `<graphic url="...">` with `@mimeType="application/ld+json"` | `images[].iiifServiceUrl` | URI | optional |
| IIIF Manifest URL | `<ref type="iiif-manifest">` | `images[].iiifManifestUrl` | URI | optional |
| Photograph Credit | `<graphic/desc>` or `<bibl>` | `images[].credit` | string | optional |
| Copyright / License | `<licence>` on graphic | `images[].license` | URI | **MUST** if image present |
| Image Type (photo / drawing / MSI band / 3D) | `<graphic/@rend>` | `images[].type` | string (from CV) | **MUST** if image present |
| Multi-Spectral Image Band | `<graphic/@n="msi-${band}">` | `images[].msiBand` | string | optional |
| Image Width/Height | `<graphic/@width>` / `@height` | `images[].width` / `images[].height` | integer | optional |

---

## 4. TEI ODD Customization

*See `tei-odd/linear-a-odd.xml` for the full ODD file.*

The ODD customizes TEI P5 / EpiDoc for Linear A-specific content. Key customizations:

### 4.1 New Elements (via `<elementSpec>`)

- `<inscriptionType>` — wrapper for object type + material
- `<signInstance>` — single sign occurrence (extends `<g>`)
- `<ligature>` — explicit ligature composition
- `<wordDivider>` — explicit punctuation marker
- `<msiBand>` — multi-spectral image band reference

### 4.2 New Attributes (via `<attDef>`)

| Attribute | Applies To | Values |
|-----------|-----------|--------|
| `@bennett` | `<g>` | Pattern: `(AB|A)\s?\d{2,3}` |
| `@signType` | `<g>` | `syllabogram`, `logogram`, `fraction`, `numeral`, `adjunct`, `ligature` |
| `@siglaVariant` | `<g>` | URI pointing to SigLA variant |
| `@confidence` | `<g>` / `<certainty>` | float [0..1] |
| `@minoanPeriod` | `<date>` | Token list for Minoan periods |
| `@gorilaRef` | `<idno>` | The GORILA ID string |

### 4.3 Controlled Vocabulary Integration

All controlled vocabularies are expressed as TEI `<taxonomy>` elements within the ODD `<classSpec>` or via `<encodingDesc>` referencing external SKOS concept schemes.

### 4.4 Minimum Structure (Required)

```xml
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Linear A Inscription</title>
        <idno type="GORILA">HT 1</idno>
      </titleStmt>
      <sourceDesc>
        <origPlace type="findspot">
          <placeName>Hagia Triada</placeName>
        </origPlace>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <creation>
        <date type="minoanPeriod" period="LM IB"/>
      </creation>
      <langUsage><language ident="emn">Minoan</language></langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
      <ab>
        <!-- sign instances -->
      </ab>
    </body>
  </text>
</TEI>
```

---

## 5. JSON-LD Context & JSON Schema

*See `json-schema/linear-a-jsonld-schema.json` for the full JSON Schema.*

### 5.1 @context Design

The JSON-LD context resolves to a namespace like:

```json
{
  "@context": {
    "la": "https://schema.lineara.org/ns/",
    "iiif": "http://iiif.io/api/presentation/3/context.json",
    "dcterms": "http://purl.org/dc/terms/",
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
    "gorilaId": "la:gorilaId",
    "signs": {"@id": "la:signs", "@container": "@list"},
    "images": {"@id": "la:images", "@container": "@list"},
    "bennettId": "la:bennettId",
    "unicode": "la:unicodeCodePoint"
  }
}
```

### 5.2 Primary JSON-LD Types

- `linearA:Inscription` — the root document type
- `linearA:SignInstance` — individual sign on the inscription
- `linearA:ImageResource` — photographic/imaging resource
- `linearA:ScribalHand` — hand identification

### 5.3 Example JSON-LD Skeleton

```json
{
  "@context": "https://schema.lineara.org/context/linear-a-v1.jsonld",
  "@type": "linearA:Inscription",
  "gorilaId": "HT 1",
  "findspot": { "site": "Hagia Triada", "coordinates": {"lat": 35.0589, "lon": 24.7894} },
  "date": { "minoanPeriod": "LM IB", "bceRange": {"from": -1500, "to": -1450} },
  "material": "clay",
  "objectType": "tablet",
  "preservation": { "state": "incomplete" },
  "signs": [ /* ... */ ],
  "structure": { "lines": [], "side": "recto" },
  "images": [ /* ... */ ]
}
```

---

## 6. Controlled Vocabularies

*See `controlled-vocabularies/` for SKOS/RDF concept schemes.*

Below is a summary of each controlled vocabulary. Each entry shows:
- **Vocabulary name** and **CV ID** (for `@ana` / `skos:inScheme` references)
- **Concept list** (values)
- **Usage context** (which field/tier)

### 6.1 Site Names (`cv:sites`)

```
Hagia Triada, Khania, Knossos, Zakros, Phaistos, Mallia, Tylissos,
Arkhanes, Palaikastro, Petras, Gournia, Mochlos, Pseira, Kato Syme,
Akrotiri (Thera), Kea (Ayia Irini), Milos (Phylakopi), Cythera,
Samothrace, Troy, Apodoulou, Sklavokampos, Nirou Chani, Archanes,
Epano Zakros, Prassa, Syme, Kydonia, Amnissos, Poros
```

### 6.2 Minoan Periods (`cv:periods`)

```
MM II, MM III, MM III/LM IA, LM IA, LM IB, LM II, LM IIIA1, LM IIIA2,
LM IIIB, Mixed, Uncertain
```

(With correspondence to absolute BCE dates via `skos:scopeNote`)

### 6.3 Materials (`cv:materials`)

```
clay, stone (limestone, sandstone, marble, steatite, serpentine),
metal (gold, silver, bronze, lead), ivory, bone, fresco/plaster,
pottery/ceramic, glass, wood (rare)
```

### 6.4 Object Types (`cv:objectTypes`)

```
tablet (page-shaped, palm-leaf, long-and-thin, roundel), 
libation table (offering table, altar), sealing (flat-based, 
nodule, prism), roundel, seal (lentoid, amygdaloid, cylinder, signet ring),
pottery vessel (pithos, jar, cup, bowl, rhyton), fresco (wall painting,
dipinto), metal object (axe, blade, vessel, ring), bone label,
ivory plaque, stone vessel
```

### 6.5 Preservation States (`cv:preservationStates`)

```
complete, nearly complete, incomplete, fragmentary, severely damaged,
eroded, reconstructed
```

### 6.6 Sign Types (`cv:signTypes`)

```
syllabogram, logogram (ideogram), fraction (simple, compound), 
numeral (unit, tens, hundreds, thousands), adjunct, ligature, 
word divider, punctuation, uncertain
```

### 6.7 Commodity Categories (`cv:commodities`)

```
grain (wheat, barley), figs, olives, olive oil, wine, grapes,
livestock (sheep, goat, cow, pig, horse), wool, cloth/textile,
bronze, copper, tin, gold, silver, spice, perfume, dye (purple),
honey, wax, resin, timber, unspecified, religious/dedicatory
```

### 6.8 Scribal Hands (`cv:scribalHands`)

Open vocabulary (extensible). Known named hands:

```
HT Hand 1, HT Hand 2, HT Hand 3 (Palaima 1988),
KH Hand A, KH Hand B (Hallager & Vlasaki 2000),
ZA Hand 1, ZA Hand 2, MA Hand 1, PH Hand 1
```

### 6.9 Image Types (`cv:imageTypes`)

```
photograph (visible light), drawing (facsimile), MSI (multispectral),
infrared, ultraviolet, raking light, RTI (reflectance transformation),
3D model (photogrammetry, structured light), X-ray, CT scan
```

### 6.10 Shape Classifications (`cv:shapeClasses`)

```
standard, cursive, formal, monumental, incised (careful), 
incised (casual), painted, variant_a, variant_b, ligatured,
simplified, archaizing
```

### 6.11 Writing Methods (`cv:writingMethods`)

```
incised (pre-firing), incised (post-firing), painted (dipinto),
stamped, carved, impressed
```

### 6.12 Confidence Levels (`cv:confidenceLevels`)

```
1.00 (certain), 0.80–0.99 (high), 0.50–0.79 (medium), 
0.20–0.49 (low), 0.00–0.19 (speculative)
```

---

## 7. Minimum Required vs Optional

### 7.1 Minimum Viable Record (Tier 1 only)

```json
{
  "gorilaId": "HT 1",
  "findspot": { "site": "Hagia Triada" },
  "date": { "minoanPeriod": "LM IB" },
  "material": "clay",
  "objectType": "tablet",
  "preservation": { "state": "incomplete" },
  "publication": { "citation": "GORILA 1, pp. 10–15" }
}
```

### 7.2 Comprehensive Record (all tiers)

Includes all fields listed in Section 3. A fully annotated inscription with sign-level, paleographic, structural, semantic, relational, and image data.

### 7.3 Conditional Requirements

| Condition | Required Fields |
|-----------|----------------|
| If `signType` is `"logogram"` | `semantics.logogramOf` AND `semantics.commodity` (if commodity) |
| If `signType` is `"fraction"` | `semantics.fractionValue` |
| If `signType` is `"numeral"` | `semantics.numericValue` |
| If `signType` is `"ligature"` | `signs[].ligatureOf` |
| If any image is present | `images[].license` and `images[].type` |
| If `preservation.state` is `"incomplete"` or `"fragmentary"` | `structure.lacunae` describing gaps |

### 7.4 Field Status Summary

| Status | Count | Notes |
|--------|-------|-------|
| **MUST** (minimum viable) | 7+ | gorilaId, findspot.site, date.minoanPeriod, material, objectType, preservation.state, publication, signs (≥1) |
| **SHOULD** | 15 | dimensions, signs[].bennettId, signs[].unicode, signs[].signType, structure.lines[], structure.words[], currentLocation, bibliography |
| **MAY** | 25+ | All remaining fields in tiers 2–7 |

---

## 8. Examples

### 8.1 Minimal TEI-XML (HT 1 — Hagia Triada tablet)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="linear-a-odd.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Linear A Inscription HT 1</title>
        <idno type="GORILA">HT 1</idno>
        <idno type="alternative">GORILA 1.1</idno>
      </titleStmt>
      <sourceDesc>
        <origPlace type="findspot">
          <placeName ref="https://vocab.lineara.org/site/HT">Hagia Triada</placeName>
          <geo>35.0589 24.7894</geo>
        </origPlace>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <creation>
        <date type="minoanPeriod" period="LM IB">
          <desc>Late Minoan IB (ca. 1500–1450 BCE)</desc>
        </date>
      </creation>
      <langUsage>
        <language ident="emn">Minoan (Eteocretan)</language>
      </langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
      <ab n="1">
        <lb n="1"/>
        <g ref="https://unicode.org/charts/PDF/U10600.pdf#U+10602" bennett="AB 02" signType="syllabogram"><seg type="translit">ro</seg></g>
        <g ref="https://unicode.org/charts/PDF/U10600.pdf#U+1061A" bennett="AB 26" signType="syllabogram"><seg type="translit">ru</seg></g>
        <space unit="chars" quantity="1"/>
        <g ref="https://unicode.org/charts/PDF/U10600.pdf#U+1065C" bennett="A 338" signType="logogram"><seg type="translit">[wheat]</seg></g>
        <num value="12"/>
      </ab>
    </body>
  </text>
</TEI>
```

### 8.2 JSON-LD (corresponding to the TEI above)

```json
{
  "@context": "https://schema.lineara.org/context/linear-a-v1.jsonld",
  "@id": "https://data.lineara.org/inscription/HT_1",
  "@type": "linearA:Inscription",
  "gorilaId": "HT 1",
  "alternativeIds": ["GORILA 1.1"],
  "findspot": {
    "site": "Hagia Triada",
    "coordinates": { "lat": 35.0589, "lon": 24.7894 }
  },
  "date": {
    "minoanPeriod": "LM IB",
    "bceRange": { "from": -1500, "to": -1450 },
    "notes": "Late Minoan IB destruction horizon"
  },
  "material": "clay",
  "objectType": "tablet",
  "preservation": {
    "state": "nearly complete",
    "description": "Left edge chipped, surface worn on lines 4-5"
  },
  "dimensions": {
    "height": 85,
    "width": 120,
    "depth": 15,
    "unit": "mm"
  },
  "currentLocation": {
    "institution": "Heraklion Archaeological Museum",
    "collection": "Minoan Collection",
    "inventoryNumber": "HM 1234"
  },
  "publication": {
    "citation": "GORILA 1, pp. 10-15, pl. II-III",
    "doi": "10.1234/gorila.v1"
  },
  "bibliography": [
    {
      "citation": "Palaima, T.G. (1988). The Scribes of Pylos.",
      "pages": "45-48"
    }
  ],
  "signs": [
    {
      "sequence": 1,
      "bennettId": "AB 02",
      "unicode": "U+10602",
      "character": "𐘂",
      "transliteration": "ro",
      "confidence": 1.0,
      "signType": "syllabogram",
      "boundingBox": { "x": 10, "y": 5, "width": 8, "height": 12, "unit": "mm" }
    },
    {
      "sequence": 2,
      "bennettId": "AB 26",
      "unicode": "U+1061A",
      "character": "𐘚",
      "transliteration": "ru",
      "confidence": 0.95,
      "signType": "syllabogram"
    },
    {
      "sequence": 3,
      "bennettId": "A 338",
      "unicode": "U+1065C",
      "character": "𐙜",
      "signType": "logogram",
      "semantics": {
        "logogramOf": "wheat",
        "commodity": "grain",
        "numericValue": 12
      }
    }
  ],
  "structure": {
    "side": "recto",
    "lines": [
      { "number": 1, "signs": [1, 2, 3], "ruling": false }
    ],
    "wordDividers": [{"afterSignSequence": 2}],
    "words": [
      { "signSequences": [1, 2] },
      { "signSequences": [3] }
    ]
  },
  "language": "emn",
  "relations": {
    "linearB": [
      { "dmicId": "DMic 02", "phoneticValue": "ro" }
    ]
  },
  "images": [
    {
      "iiifServiceUrl": "https://iiif.heraklion-museum.gr/iiif/2/HM_1234",
      "iiifManifestUrl": "https://iiif.heraklion-museum.gr/iiif/HM_1234/manifest",
      "credit": "Heraklion Archaeological Museum / EFA",
      "license": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
      "type": "photograph",
      "width": 4000,
      "height": 3000
    }
  ]
}
```

### 8.3 Sign-Level with Paleographic Detail

```json
{
  "@context": "https://schema.lineara.org/context/linear-a-v1.jsonld",
  "@id": "https://data.lineara.org/inscription/KH_1",
  "gorilaId": "KH 1",
  "findspot": { "site": "Khania" },
  "date": { "minoanPeriod": "LM IB" },
  "material": "clay",
  "objectType": "tablet",
  "preservation": { "state": "fragmentary" },
  "paleography": {
    "scribalHandId": "https://data.lineara.org/hand/KH_A",
    "scribalHandCertainty": 0.85,
    "ductusNotes": "Rapid cursive hand, signs ligatured. AB 28 (i) shows distinctive flattened top.",
    "writingMethod": "incised (pre-firing)"
  },
  "signs": [
    {
      "sequence": 1,
      "bennettId": "AB 28",
      "unicode": "U+1061C",
      "transliteration": "i",
      "confidence": 0.70,
      "signType": "syllabogram",
      "siglaVariantId": "https://sigla.phis.me/variant/AB28_v2",
      "shapeClass": "variant_b",
      "erasure": false,
      "boundingBox": {
        "x": 45,
        "y": 22,
        "width": 6,
        "height": 9,
        "unit": "mm"
      }
    },
    {
      "sequence": 2,
      "bennettId": "AB 13",
      "unicode": "U+1060D",
      "transliteration": "me",
      "confidence": 0.60,
      "signType": "syllabogram",
      "siglaVariantId": "https://sigla.phis.me/variant/AB13_v1",
      "shapeClass": "standard",
      "erasure": true,
      "correction": {
        "original": "AB 13 (me)",
        "correctedTo": "AB 27 (re)"
      },
      "boundingBox": {
        "x": 52,
        "y": 21,
        "width": 7,
        "height": 10,
        "unit": "mm"
      }
    }
  ],
  "images": [
    {
      "iiifServiceUrl": "https://iiif.khaniamuseum.gr/iiif/2/KH_1",
      "type": "msi",
      "msiBand": "infrared",
      "license": "https://creativecommons.org/licenses/by/4.0/"
    }
  ]
}
```

---

## 9. Crosswalk: TEI ↔ JSON-LD ↔ SigLA ↔ lineara.xyz

| Domain | TEI-EpiDoc | JSON-LD | SigLA (JS object) | lineara.xyz (JSON) |
|--------|-----------|---------|--------------------|--------------------|
| Inscription ID | `//titleStmt/idno[@type="GORILA"]` | `gorilaId` | `document.id` | `._id` |
| Site | `//origPlace/placeName` | `findspot.site` | `document.site` | `.findSpot` |
| Period | `//creation/date/@period` | `date.minoanPeriod` | — | — |
| Text | `<ab>` content + `<lb/>` | `signs[].transliteration` | `document.wordViews[].signs[].transliteration` | `.transcription` |
| Sign transliteration | `<g><seg type="translit">` | `signs[].transliteration` | `word.signs[].transliteration` | (in .transcription) |
| Sign bounding box | `<surface><zone>` | `signs[].boundingBox` | `sign.coords` | — |
| Image URL | `<graphic @url>` | `images[].iiifServiceUrl` | `document.documentImgUrl` | `.photoUrl` |
| Word view | `<w>` or `<space/>` seg | `structure.words[]` | `document.wordViews[]` | — |
| Side | `<div type="side">` | `structure.side` | `document.face` | — |
| Hand | `<handNote>` | `paleography.scribalHandId` | — | — |

**Lossiness**: The TEI ↔ JSON-LD mapping is designed to be lossless. The mappings from SigLA and lineara.xyz involve information loss because those datasets lack paleographic and relational tiers.

---

## 10. Files

| File | Purpose |
|------|---------|
| `tei-odd/linear-a-odd.xml` | Full TEI ODD customization for Linear A inscriptions |
| `json-schema/linear-a-jsonld-schema.json` | JSON Schema v2020-12 for JSON-LD validation |
| `json-schema/linear-a-jsonld-context.json` | JSON-LD @context file |
| `controlled-vocabularies/sites.rdf` | SKOS concept scheme for findspot sites |
| `controlled-vocabularies/periods.rdf` | SKOS concept scheme for Minoan periods |
| `controlled-vocabularies/materials.rdf` | SKOS concept scheme for materials |
| `controlled-vocabularies/object-types.rdf` | SKOS concept scheme for object types |
| `controlled-vocabularies/preservation-states.rdf` | SKOS concept scheme for preservation states |
| `controlled-vocabularies/sign-types.rdf` | SKOS concept scheme for sign types |
| `controlled-vocabularies/commodities.rdf` | SKOS concept scheme for commodities |
| `controlled-vocabularies/image-types.rdf` | SKOS concept scheme for image types |
| `controlled-vocabularies/shape-classes.rdf` | SKOS concept scheme for palaeographic shape classes |
| `controlled-vocabularies/writing-methods.rdf` | SKOS concept scheme for writing methods |
| `controlled-vocabularies/scribal-hands.rdf` | SKOS concept scheme for scribal hand IDs |
| `examples/ht-1-full-tei.xml` | Complete TEI-XML example for HT 1 |
| `examples/ht-1-jsonld.json` | Complete JSON-LD example for HT 1 |
| `examples/kh-1-paleographic.json` | JSON-LD with paleographic detail for KH 1 |

---

## 10. References

- Godart, L. & Olivier, J.-P. (1976–1985). *Recueil des inscriptions en Linéaire A* (GORILA). 5 vols. École Française d'Athènes.
- Salgarella, E. & Castellan, S. (2021–2026). *SigLA: The Signs of Linear A: a Palaeographical Database*. https://sigla.phis.me/
- Winterstein, G. et al. (2015). "A Digital Corpus for Linear A." *ACL Workshop on Corpus-based Research in the Humanities*.
- Bennett, E.L. (1964). "The Linear B Sign List." *Mycenaean Studies*.
- Palaima, T.G. (1988). *The Scribes of Pylos*. Edizioni dell'Ateneo.
- Hallager, E. & Vlasaki, M. (2000). *The Linear A Inscriptions from Khania*. Creta Antica.
- TEI Consortium (2025). *TEI P5: Guidelines for Electronic Text Encoding and Interchange*. https://tei-c.org/release/doc/tei-p5-doc/
- EpiDoc Collaborative (2025). *EpiDoc Guidelines*. https://epidoc.stoa.org/
- IIIF Consortium (2020). *IIIF Presentation API 3.0*. https://iiif.io/api/presentation/3.0/
