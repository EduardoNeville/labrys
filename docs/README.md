# Linear A Unified Data Schema

This directory contains a comprehensive **dual-format schema** for Linear A inscriptions.

## Architecture

The schema has two representations that are losslessly interconvertible:

| Format | File | Purpose |
|--------|------|---------|
| **Main Documentation** | `unified-linear-a-schema.md` | Full specification with field definitions, tiers, and usage |
| **TEI ODD** | `tei-odd/linear-a-odd.xml` | Custom XML schema extending TEI P5 / EpiDoc |
| **JSON-LD Context** | `json-schema/linear-a-jsonld-context.json` | Linked-data context for JSON-LD |
| **JSON Schema** | `json-schema/linear-a-jsonld-schema.json` | Validates JSON-LD instances |
| **Controlled Vocabularies** | `controlled-vocabularies/*.rdf` | SKOS concept schemes for all coded fields |

## Example Files

| File | Description | Tiers Covered |
|------|-------------|---------------|
| `examples/ht-1-full-tei.xml` | HT 1 encoded in TEI-XML | 1 (metadata), 2 (signs), 3 (hand), 4 (lines), 7 (facsimile) |
| `examples/ht-1-jsonld.json` | HT 1 encoded in JSON-LD | All 7 tiers |
| `examples/kh-1-paleographic.json` | KH 1 with rich paleographic detail | 1–4, 6–7 (paleographic focus) |

## The 7 Tiers

1. **Text-Level Metadata** — GORILA ID, site, date, material, object type, preservation, location, publication
2. **Sign-Level Annotation** — Bennett ID, Unicode, bounding box, transliteration, confidence
3. **Paleographic Tier** — Scribal hand, shape class, ligatures, erasures, corrections, ductus
4. **Structural Tier** — Lines, sides, ruling, word boundaries, lacunae
5. **Semantic Tier** — Logograms, fractions, numerals, commodities
6. **Relational Tier** — Cross-references to Linear B, Cypro-Minoan, Cretan Hieroglyphic, Eteocretan
7. **Image Tier** — IIIF URLs, MSI bands, licenses, credits

## Quick Start

**Minimal JSON-LD (6 required fields):**

```json
{
  "@context": "https://schema.lineara.org/context/linear-a-v1.jsonld",
  "@type": "linearA:Inscription",
  "gorilaId": "HT 1",
  "findspot": { "site": "Hagia Triada" },
  "date": { "minoanPeriod": "LM IB" },
  "material": "clay",
  "objectType": "page-shaped tablet",
  "preservation": { "state": "nearly complete" },
  "publication": { "citation": "GORILA 1, pp. 10–15" },
  "signs": [
    {
      "sequence": 1,
      "bennettId": "AB 02",
      "unicode": "U+10602",
      "signType": "syllabogram"
    }
  ]
}
```

**Validate with:**

```bash
# Using ajv (Node.js)
ajv validate -s json-schema/linear-a-jsonld-schema.json -d examples/ht-1-jsonld.json

# Using Python's jsonschema
python3 -c "
import json, jsonschema
with open('json-schema/linear-a-jsonld-schema.json') as f:
    schema = json.load(f)
with open('examples/ht-1-jsonld.json') as f:
    data = json.load(f)
jsonschema.validate(instance=data, schema=schema)
print('Valid!')
"
```

## Crosswalk to Existing Resources

| Existing Resource | Mapping |
|------------------|---------|
| SigLA (document ID) | → `gorilaId` |
| SigLA (sign coordinates) | → `signs[].boundingBox` |
| SigLA (variant IDs) | → `signs[].siglaVariantId` |
| lineara.xyz (inscription) | → `gorilaId` + `signs[]` |
| lineara.xyz (transcription) | → `signs[].transliteration` |
| lineara.xyz (photoUrl) | → `images[].iiifServiceUrl` (transformed) |
| Winterstein TEI (g element) | → `signs[]` via `@bennett` ↔ `bennettId` |
| GORILA print (page/plate) | → `publication.citation` |
| CMS / iDAI seal objects | → `relations.relatedInscriptions` |
| Unicode Aegean Block | → `signs[].unicode` |
