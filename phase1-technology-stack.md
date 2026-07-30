# Phase 1 — Encoding & Tooling Requirements

**Project:** Labrys — Digital Epigraphy for Linear A  
**Phase:** 1 — Foundation (Encoding, Infrastructure, Annotations)  
**Version:** 1.0.0  
**Date:** 2026-07-31  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [TEI Publisher — Collaborative Corpus Editing](#2-tei-publisher--collaborative-corpus-editing)
3. [IIIF Image Server](#3-iiif-image-server)
4. [Label Studio / eScriptorium — Sign-Level Annotation](#4-label-studio--escriptorium)
5. [Script Encoding Initiative — Unicode & Fonts](#5-script-encoding-initiative--unicode--fonts)
6. [Python Data Pipeline](#6-python-data-pipeline)
7. [Version Control & Data Release](#7-version-control--data-release)
8. [Computational Infrastructure](#8-computational-infrastructure)
9. [Complete Technology Stack Summary](#9-complete-technology-stack-summary)
10. [Quickstart: Bootstrap Phase 1](#10-quickstart-bootstrap-phase-1)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│                                                                  │
│  TEI XML                   JSON-LD                 RDF/SKOS     │
│  (Canonical archive)       (Web API)               (Vocabs)     │
│       │                        │                       │        │
│       ▼                        ▼                       ▼        │
│  ┌─────────┐            ┌────────────┐         ┌──────────────┐ │
│  │ TEI     │ ◄────────► │ Python     │ ◄─────► │ PostgreSQL   │ │
│  │ Publisher│   XSLT    │ Pipeline   │         │ (metadata)   │ │
│  └─────────┘            └────────────┘         └──────────────┘ │
│       │                        │                       │        │
│       ▼                        ▼                       ▼        │
│  ┌─────────┐            ┌────────────┐         ┌──────────────┐ │
│  │ Git     │            │ Cantaloupe │         │ eScriptorium │ │
│  │ (TEI)   │            │ IIIF       │         │ Annotation   │ │
│  └─────────┘            └────────────┘         └──────────────┘ │
│       │                        │                       │        │
│       ▼                        ▼                       ▼        │
│  Git LFS                  Tiled images              SVG bboxes  │
│  (TEI corpus)             (JPEG2000/TIFF)           (PAGE XML)  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                   ┌─────────────────────┐
                   │  GitHub / Zenodo    │
                   │  DOI Release        │
                   └─────────────────────┘
```

### Design Principles

| Principle | Application |
|-----------|-------------|
| **TEI as source of truth** | TEI-XML (via EpiDoc ODD) is the canonical archival format. JSON-LD is derived via XSLT for web use. |
| **IIIF-first imaging** | All images served via IIIF Image API 2.1/3.0. No direct file URLs. |
| **Open-world annotation** | Annotations in Label Studio / eScriptorium are stored as PAGE XML → linked to TEI via `@xml:id`. |
| **Git LFS for binaries** | All image derivatives, trained models, and large binaries stored in Git LFS. |
| **Python middle layer** | All data transformation, validation, and analysis in Python 3.12+. |
| **Containerized services** | All services (TEI Publisher, Cantaloupe, eScriptorium) deployed via Docker. |

---

## 2. TEI Publisher — Collaborative Corpus Editing

### 2.1 What & Why

TEI Publisher (v8.x) is an open-source platform built on top of **eXist-db** that provides a web-based environment for editing, managing, and publishing TEI XML documents. For the Labrys corpus:

- Collaborative multi-user editing of TEI Linear A inscriptions
- Built-in ODD validation against `linear-a-odd.xml`
- REST API for programmatic access (Python pipeline can push/pull)
- TEI → HTML5 / PDF / EPUB publication out of the box
- Version history per-document (leveraging eXist-db's built-in versioning)

### 2.2 Requirements

| Requirement | Specification |
|-------------|---------------|
| **Platform** | TEI Publisher v8.3+ (current stable: 8.3.1 as of 2026-Q1) |
| **Runtime** | Tomcat 10 + eXist-db 6.x (bundled in TEI Publisher distribution) |
| **Java** | OpenJDK 21 LTS |
| **DB Backend** | eXist-db native XML database (built-in) |
| **RAM** | Minimum 8 GB (16 GB recommended for ~2K TEI documents) |
| **CPU** | 4+ cores |
| **Storage** | 20 GB for corpus + eXist-db indexing |
| **Network** | Port 8080 (Tomcat), 8443 (HTTPS) |

### 2.3 Setup Guide

```bash
#!/usr/bin/env bash
# ========================================================
# TEI Publisher + eXist-db — Labrys Setup
# ========================================================

# 1. Prerequisites
sudo apt update && sudo apt install -y openjdk-21-jdk git curl
java -version  # → OpenJDK 21

# 2. Download TEI Publisher
RELEASE="8.3.1"
wget "https://github.com/eeditiones/tei-publisher-app/releases/download/v${RELEASE}/tei-publisher-${RELEASE}.war"
# Or use Docker (recommended):
# docker pull existdb/tei-publisher:${RELEASE}

# 3. Docker deployment (production)
mkdir -p /srv/labrys/{exist-data,tei-corpus,logs}
docker network create labrys-net

docker run -d \
  --name tei-publisher \
  --network labrys-net \
  -p 8080:8080 \
  -v /srv/labrys/exist-data:/exist-data \
  -v /srv/labrys/tei-corpus:/tei-corpus \
  -v /srv/labrys/logs:/logs \
  -e "JAVA_OPTS=-Xmx8g -Dexist.home=/exist-data" \
  existdb/tei-publisher:${RELEASE}

# 4. Deploy custom ODD
# Copy linear-a-odd.xml to the ODD collection:
curl -X PUT \
  -H "Content-Type: application/xml" \
  --data-binary @docs/tei-odd/linear-a-odd.xml \
  "http://localhost:8080/exist/rest/db/apps/tei-publisher/odd/linear-a.odd"

# 5. Deploy controlled vocabularies
for f in docs/controlled-vocabularies/*.rdf; do
  curl -X PUT \
    -H "Content-Type: application/rdf+xml" \
    --data-binary "@$f" \
    "http://localhost:8080/exist/rest/db/apps/tei-publisher/vocab/$(basename $f)"
done

# 6. Ingest initial TEI corpus
# via REST API or TEI Publisher web UI

echo "TEI Publisher running at http://localhost:8080/tei-publisher"
```

### 2.4 Customizations Needed for Linear A

| Customization | Implementation | Status |
|---------------|---------------|--------|
| **ODD registration** | Register `linear-a-odd.xml` as a schema in TEI Publisher | **Done** (file exists) |
| **Custom HTML output** | Create ODD `html` transformation for Linear A sign rendering (Unicode + transliteration side-by-side) | Needs development |
| **Vocabulary widget** | Configure autocomplete from SKOS RDF files for site, period, material fields | Needs development |
| **Sign browser** | Custom app component to browse/unified sign inventory with Unicode rendering | Needs development |
| **User roles** | Define `editor` (can edit TEI), `reviewer` (can annotate/comment), `admin` (can publish) | Needs development |
| **IIIF image integration** | Link TEI `<graphic>` elements to IIIF manifests via Mirador viewer | Needs development |
| **OAI-PMH endpoint** | Enable TEI Publisher's OAI-PMH for metadata harvesting | Easy config |

### 2.5 TEI Corpus Organization

```
/srv/labrys/tei-corpus/
├── index.xml                    # Corpus manifest (list of all inscriptions)
├── ht/                          # Hagia Triada
│   ├── HT_001.xml
│   ├── HT_002.xml
│   └── ...
├── kh/                          # Khania
│   ├── KH_001.xml
│   └── ...
├── za/                          # Zakros
├── kn/                          # Knossos
├── ph/                          # Phaistos
├── ma/                          # Mallia
├── ar/                          # Arkhanes
├── other-sites/                 # Smaller findspots
├── controlled-vocabularies/     # SKOS RDF files
└── odd/                         # ODD schema
    └── linear-a-odd.xml
```

---

## 3. IIIF Image Server

### 3.1 Choice: Cantaloupe

**Recommended:** Cantaloupe v5.1+ (latest stable: 5.1.1 as of 2026-Q2)

| Criteria | Cantaloupe | IIIF-Presentation-API | Why Cantaloupe wins |
|----------|-----------|----------------------|---------------------|
| **Image API compliance** | IIF Image API 2.1/3.0 | Presentation API only | Need Image API for tile serving |
| **Format support** | TIFF, JPEG2000, PNG, JPEG | N/A (manifest server) | Need TIFF/JP2 archival masters |
| **Storage backends** | Filesystem, S3, Azure, etc. | N/A | Flexible |
| **Caching** | Built-in derivative cache | N/A | Essential for performance |
| **Python client** | `iiif` library via requests | N/A | Pipeline integration |
| **Docker image** | Official (`cantaloupe/cantaloupe`) | Not standalone | Easy deploy |
| **Metadata embedding** | XMP/IPTC extraction | Via manifest only | TEI ↔ image linking |

**Complementary:** A IIIF Presentation API server (or use TEI Publisher's built-in manifest generation) alongside Cantaloupe.

### 3.2 Storage Requirements

| Item | Count | Resolution | Format | Per File | Total |
|------|-------|-----------|--------|----------|-------|
| High-res photos | ~1,500 | 600 DPI (~6000×8000 px) | TIFF (LZW) | ~150–350 MB | **~250–500 GB** |
| JP2 derivatives | ~1,500 | same | JPEG2000 (lossless) | ~80–200 MB | **~120–300 GB** |
| IIIF cache (tiles) | ~1,500 | tiled at 512px | JPEG (90%) | ~30–100 MB | **~50–150 GB** |
| Drawings/facsimiles | ~1,500 | variable | TIFF/PNG | ~10–50 MB | **~15–75 GB** |
| MSI bands (×5) | ~7,500 | same as hi-res | TIFF | ~150–350 MB | **~1–2 TB** |
| **Total (photos only)** | | | | | **~400–850 GB** |
| **Total (+ MSI bands)** | | | | | **~1.5–3 TB** |

**Recommendation:** Start with **2 TB** SSD storage for primary + derivatives cache. Use Git LFS only for a representative subset (see §7).

### 3.3 Setup Guide

```bash
# ========================================================
# Cantaloupe IIIF Image Server — Labrys Setup
# ========================================================

# Docker deployment (recommended)
docker run -d \
  --name cantaloupe \
  --network labrys-net \
  -p 8182:8182 \
  -v /srv/labrys/images:/images \
  -v /srv/labrys/cantaloupe-cache:/var/cache/cantaloupe \
  -v /srv/labrys/cantaloupe-config:/etc/cantaloupe \
  -e "CANTALOUPE_CONFIG=/etc/cantaloupe/cantaloupe.properties" \
  cantaloupe/cantaloupe:5.1

# Configuration file: /srv/labrys/cantaloupe-config/cantaloupe.properties
cat > /srv/labrys/cantaloupe-config/cantaloupe.properties << 'CONF'
# Cantaloupe Configuration for Labrys

# Server
http.port = 8182
http.enabled = true
https.enabled = false
https.port = 8183

# Source — Filesystem
FilesystemSource.BasicLookupStrategy.path_prefix = /images
FilesystemSource.Binding = BasicLookupStrategy

# Caching
cache.server = FilesystemCache
cache.server.path = /var/cache/cantaloupe
cache.server.ttl_seconds = 2592000  # 30 days
cache.derivative.enabled = true
cache.derivative.path = /var/cache/cantaloupe/derivatives

# Processors — TIFF with JPEG2000 fallback
processor.jp2 = openjpeg
processor.tif = jai
processor.ImageIO.disable = true

# IIIF API versions
iiif.1.enabled = false
iiif.2.enabled = true
iiif.3.enabled = true

# Metadata
metadata.preserve = false
metadata.respect_rotation = true

# Logging
log.application.level = info
log.access.enabled = true

# Cors (for web apps)
cors.enabled = true
cors.allow_origin = ["*"]
CONF

# Test the server
curl "http://localhost:8182/iiif/2/HT_001.tif/info.json"
```

### 3.4 Metadata Linking to TEI Corpus

The linking between images and TEI inscriptions follows this model:

```
┌────────────────────────────────────────────────────┐
│              IIIF Manifest (auto-generated)         │
│  {                                                   │
│    "@id": "https://iiif.labrys.org/HT_001/manifest",│
│    "label": "HT 1 — Hagia Triada libation table",   │
│    "within": "https://data.labrys.org/HT_1",         │
│    "sequences": [{                                   │
│      "canvases": [{                                  │
│        "images": [{                                  │
│          "resource": {                               │
│            "@id": "https://iiif.labrys.org/"         │
│                     "images/HT_001.tif",            │
│            "service": {                              │
│              "@id": "https://iiif.labrys.org/"       │
│                       "iiif/2/HT_001.tif"           │
│            }                                         │
│          },                                          │
│          "on": "https://iiif.labrys.org/"            │
│               "HT_001/canvas/p1"                    │
│        }]                                            │
│      }]                                              │
│    }]                                                │
│  }                                                   │
└──────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────┐
│              TEI XML (in TEI Publisher)              │
│  <graphic url="https://iiif.labrys.org/iiif/2/      │
│              HT_001.tif/full/full/0/default.jpg"     │
│           mimeType="image/jpeg"                      │
│           width="6000" height="8000">                │
│    <desc>HT 1 recto — visible light photograph</desc>│
│    <licence target="https://creativecommons.org/     │
│                     licenses/by-nc-sa/4.0/"/>        │
│  </graphic>                                          │
└──────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────┐
│         eScriptorium Annotation (PAGE XML)          │
│  <Object id="r1_AB02" type="Sign">                 │
│    <Coords points="100,50 150,50 150,90 100,90"/>   │
│    <Labels>                                         │
│      <Label value="AB 02"/>                         │
│      <Label value="ro"/>                            │
│    </Labels>                                        │
│  </Object>                                          │
└──────────────────────────────────────────────────────┘
```

### 3.5 Image Naming Convention

```
{site_code}_{sequence}.{format}
HT_001.tif          → Hagia Triada, inscription #1, archival TIFF
HT_001_msi_ir.tif   → HT 1, multispectral infrared band
HT_001_msi_uv.tif   → HT 1, multispectral ultraviolet band
HT_001_msi_raking.tif → HT 1, raking light
HT_001_drawing.png  → HT 1, facsimile drawing
KH_001.tif          → Khania, inscription #1
ZA_Zb_3.tif         → Zakros, inscription ZA Zb 3
```

### 3.6 IIIF Presentation Manifest Generation

Use a Python script (part of the data pipeline) to auto-generate IIIF Presentation 3.0 manifests from TEI `<graphic>` elements:

```python
# Simplified example — part of pipeline/iiif_manifest_builder.py
def generate_manifest(tei_xml: str, base_url: str) -> dict:
    from lxml import etree
    root = etree.fromstring(tei_xml.encode())
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    
    gorila_id = root.find(".//tei:idno[@type='GORILA']", ns).text
    images = root.findall(".//tei:graphic", ns)
    
    manifest = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": f"{base_url}/manifest/{gorila_id.replace(' ', '_')}",
        "type": "Manifest",
        "label": {"en": [f"{gorila_id} — Linear A inscription"]},
        "items": []
    }
    
    for i, img in enumerate(images):
        img_url = img.get("url")
        canvas = {
            "id": f"{manifest['id']}/canvas/p{i+1}",
            "type": "Canvas",
            "width": int(img.get("width", 0)),
            "height": int(img.get("height", 0)),
            "items": [{
                "type": "AnnotationPage",
                "items": [{
                    "type": "Annotation",
                    "motivation": "painting",
                    "body": {
                        "type": "Image",
                        "id": img_url,
                        "format": img.get("mimeType", "image/jpeg"),
                        "service": [{
                            "id": img_url.rsplit("/full/", 1)[0],
                            "type": "ImageService3",
                            "profile": "level2"
                        }]
                    }
                }]
            }]
        }
        manifest["items"].append(canvas)
    
    return manifest
```

---

## 4. Label Studio / eScriptorium — Sign-Level Annotation

### 4.1 Choice: eScriptorium

**Recommended:** eScriptorium v0.13+ (latest: 0.14.x as of 2026)

| Criteria | eScriptorium | Label Studio |
|----------|-------------|--------------|
| **Primary use case** | OCR/HTR for historical scripts | General-purpose annotation |
| **Built-in HTR engine** | Kraken (+ Calamari, TF) | None (plugin) |
| **PAGE XML output** | Native | Not supported |
| **TEI integration** | Strong (via PAGE → TEI XSLT) | Weak (export to JSON/CSV) |
| **Bounding boxes** | Native polygon/bbox | Native |
| **Multi-spectral support** | Via image layers | Limited |
| **Self-hosted Docker** | Official image | Official image |
| **Crowd/team annotation** | Built-in user management | Built-in |
| **Script-specific training** | Kraken models for any script | Requires custom plugin |
| **Open source license** | AGPL v3 | Apache 2.0 |

**Why eScriptorium wins for this project:** Linear A needs OCR/HTR training for sign classification. eScriptorium's Kraken engine can be trained on Linear A signs from scratch. Label Studio would require significant custom plugin development to achieve the same.

### 4.2 Setup Guide

```bash
# ========================================================
# eScriptorium — Labrys Setup
# ========================================================

# Docker Compose deployment
mkdir -p /srv/labrys/escriptorium/{data,models,media}

cat > /srv/labrys/escriptorium/docker-compose.yml << 'DOCKER'
version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: escriptorium
      POSTGRES_USER: escriptorium
      POSTGRES_PASSWORD: labrys_linear_a_2026
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  app:
    image: scripta/escriptorium:0.14  # or build from https://gitlab.com/scripta/escriptorium
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
      - ./models:/app/models
    environment:
      DATABASE_URL: postgres://escriptorium:labrys_linear_a_2026@db/escriptorium
      CELERY_BROKER_URL: redis://redis:6379/0
      SECRET_KEY: labrys_secret_key_change_in_production
      DEBUG: "0"
    restart: unless-stopped

  celery:
    image: scripta/escriptorium:0.14
    command: celery -A escriptorium worker -l info -c 2
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media
      - ./models:/app/models
    environment:
      DATABASE_URL: postgres://escriptorium:labrys_linear_a_2026@db/escriptorium
      CELERY_BROKER_URL: redis://redis:6379/0
    restart: unless-stopped
DOCKER

cd /srv/labrys/escriptorium
docker compose up -d

# Access at http://localhost:8000
# Default admin: create on first login

# 3. Import IIIF images into eScriptorium
# Via eScriptorium UI: Documents → Import → IIIF URL
# URL format: https://iiif.labrys.org/iiif/2/HT_001.tif/info.json
```

### 4.3 Annotation Workflow

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│ 1. Import IIIF   │────►│ 2. Draw bounding  │────►│ 3. Assign sign   │
│    image         │     │    boxes per sign │     │    labels (AB #) │
│    (TIFF @ 600   │     │    (polygon or    │     │    + translit.   │
│     dpi)         │     │     rectangle)    │     │    + confidence  │
└──────────────────┘     └───────────────────┘     └──────────────────┘
                                                           │
                                                           ▼
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│ 6. Export PAGE   │◄────│ 5. Train Kraken   │◄────│ 4. Review &      │
│    XML + ALTO    │     │    HTR model for  │     │    correct       │
│    → TEI import  │     │    Linear A sign  │     │    (inter-rater) │
│    via XSLT      │     │    classification │     │                  │
└──────────────────┘     └───────────────────┘     └──────────────────┘
```

### 4.4 Label Schema for Linear A

```json
{
  "labels": [
    {"value": "AB 01", "type": "syllabogram", "unicode": "U+10601", "translit": "da"},
    {"value": "AB 02", "type": "syllabogram", "unicode": "U+10602", "translit": "ro"},
    {"value": "AB 03", "type": "syllabogram", "unicode": "U+10603", "translit": "pa"},
    {"value": "AB 04", "type": "syllabogram", "unicode": "U+10604", "translit": "te"},
    {"value": "AB 05", "type": "syllabogram", "unicode": "U+10605", "translit": "ti"},
    {"value": "AB 06", "type": "syllabogram", "unicode": "U+10606", "translit": "na"},
    {"value": "AB 07", "type": "syllabogram", "unicode": "U+10607", "translit": "di"},
    {"value": "AB 08", "type": "syllabogram", "unicode": "U+10608", "translit": "a"},
    {"value": "AB 09", "type": "syllabogram", "unicode": "U+10609", "translit": "se"},
    {"value": "AB 10", "type": "syllabogram", "unicode": "U+1060A", "translit": "u"},
    {"value": "AB 11", "type": "syllabogram", "unicode": "U+1060B", "translit": "si"},
    // ... all ~80 syllabograms + ~120 logograms/fractions
    {"value": "A 338", "type": "logogram", "unicode": "U+1065C", "translit": "GRAIN"},
    {"value": "A 303", "type": "logogram", "unicode": "U+1064D", "translit": "OLEUM"},
    // Word dividers, lacunae markers, damage markers
    {"value": "__word_divider__", "type": "structural"},
    {"value": "__lacuna__", "type": "structural"},
    {"value": "__damage__", "type": "structural"},
    {"value": "__line_break__", "type": "structural"}
  ]
}
```

The full label list should be generated from the controlled vocabularies + GORILA sign inventory. A Python script (`pipeline/generate_label_set.py`) can scrape from:

- **SigLA** `database.js` — all sign variants
- **Unicode Aegean block** — all assigned characters (U+10600–U+10767)
- **GORILA** sign list — AB and A numbers

### 4.5 Export Pipeline: PAGE XML → TEI

eScriptorium exports PAGE XML. Convert to TEI via XSLT:

```bash
# transformation/escriptorium_page2tei.xsl
# Convert PAGE XML bounding boxes + labels → TEI <g> elements with @bennett and <zone>

#!/bin/bash
for page in exports/*.xml; do
  base=$(basename "$page" .xml)
  java -jar /usr/local/bin/saxon-he-12.jar \
    -s:"$page" \
    -xsl:transformations/page2tei.xsl \
    -o:"tei/${base}.xml"
done
```

### 4.6 Kraken HTR Training for Linear A

Once ~200 inscriptions are annotated with sign-level bounding boxes, train an initial HTR model:

```bash
# Inside eScriptorium container or local Kraken installation
pip install kraken

# 1. Convert PAGE XML to line-level ground truth
ketos train \
  -i part/1 \
  --device cuda:0 \
  --load ./linear_a_model \
  --output ./linear_a_model \
  --preload \
  --batch 16 \
  --normalization minmax \
  --augment \
  -f page \
  data/*.xml

# 2. Model specifics
# - Input: line images (from IIIF tiles)
# - Output: character sequence (Unicode Linear A chars)
# - Architecture: VGSL (standard for Kraken)
# - After ~20 epochs on ~5000 line images → test CER < 10%
```

**Note:** Full HTR training belongs in Phase 2 (ML). Phase 1 focuses on setting up the annotation infrastructure and manually annotating a gold-standard set of ~50 inscriptions.

---

## 5. Script Encoding Initiative — Unicode & Fonts

### 5.1 Unicode Status

| Block | Range | Assigned | Free | Status |
|-------|-------|----------|------|--------|
| Linear A (Aegean Numbers subset) | U+10600–U+1077F | 341/384 | 43 | Assigned in Unicode 7.0 (2014), latest additions in Unicode 17.0 (2025) |

**Current gaps (as of Unicode 17.0):**

1. **Complex ligatures** — Some GORILA-identified ligatures (e.g., overlapping fractions with logograms) are not individually encoded. The convention is to represent them as sequences of existing characters.
2. **Variant glyphs** — Scribal variants (e.g., AB 28 with flattened top vs. rounded top) are not separately encoded — they are stylistic, not orthographic.
3. **New signs** — If new excavations (Phaistos, Knossos) yield previously unattested signs, a new Unicode proposal would be needed.

### 5.2 Unicode Proposal Process (if needed)

| Step | Action | Timeline | Responsible |
|------|--------|----------|-------------|
| 1 | Identify a sign not in Unicode Aegean block | Ongoing during Phase 1 encoding | Project epigraphers |
| 2 | Document: 10+ attestations, images, GORILA reference, proposed code point | 2 weeks | Project + Script Encoding Initiative (SEI) |
| 3 | Submit to Unicode Technical Committee (UTC) via SEI | 3 months before UTC meeting | SEI liaison |
| 4 | UTC review + vote | Next UTC meeting (typically quarterly) | UTC |
| 5 | Encoding in a future Unicode version | ~12–18 months after acceptance | Unicode Consortium |

**Unicode proposal template:** https://www.unicode.org/policies/proposal.html

**Contact:** Deborah Anderson (UC Berkeley, Script Encoding Initiative) — `dwanders@berkeley.edu`

### 5.3 Font Development

#### Recommendation: Noto Sans Linear A (Google)

| Font | Coverage | License | Quality | Recommendation |
|------|---------|---------|---------|---------------|
| **Noto Sans Linear A** | 337/341 signs | SIL OFL 1.1 | Excellent (designed by Google) | **Primary font** |
| **Aegean** (George Douros) | ~340/341 signs | Freeware (public domain-like) | Very good | **Fallback/comparison** |
| LA.ttf (CTAN) | ~280 signs | LPPL | Adequate | Not recommended for production |
| Symbola | ~300 signs | Freeware | Good | Not actively maintained |

#### Required Updates to Noto Sans Linear A

| Update | Priority | Description |
|--------|----------|-------------|
| **Missing 4 signs** from Unicode 15–17 additions | **High** | Signs A 315, A 316, A 317, A 318 (or whatever the latest additions are) |
| **Ligature support** | **Medium** | Opentype `liga` / `dlig` for common ligatures (e.g., A 301+AB 02) |
| **Scribal variant glyphs** as OpenType `ss01`–`ss10` | **Low** | Stylistic sets for regional variants (HT vs KH forms) |
| **Bold/Italic weights** | **Low** | Currently only Regular weight |

#### How to Contribute to Noto Sans Linear A

```bash
# 1. Get the source
git clone https://github.com/googlefonts/noto-fonts.git
cd noto-fonts/src/NotoSansLinearA

# 2. The font is built from Glyphs source or UFO
# Install fontmake or use Glyphs app

# 3. Add missing glyphs
# Open NotoSansLinearA.glyphs (or .ufo)
# Add new glyphs at the correct Unicode positions
# Design matching the existing style (linear, consistent stroke width)

# 4. Build
fontmake -g NotoSansLinearA.glyphs -o ttf --output-dir fonts/

# 5. Submit PR to googlefonts/noto-fonts

# Alternative: Submit via GitHub issues requesting Google's font team add them
```

#### Fallback: Build an Aegean-derived font for internal use

```bash
# If Noto updates are slow, build a patched Aegean with additional ligatures
# Using fonttools:
pip install fonttools

python3 << 'PY'
from fontTools.ttLib import TTFont
font = TTFont("Aegean.otf")

# Add a new ligature OpenType substitution
# (Simplified — real implementation needs careful table manipulation)
import copy
gsub = font["GSUB"]
# ... add ligature lookup for custom sequences

font.save("Aegean-Labrys.otf")
print("Patched font saved.")
PY
```

### 5.4 Font Testing & Rendering

Test rendering across browsers, applications, and OS:

```bash
# Test with Python Pillow
python3 -c "
from PIL import Image, ImageFont, ImageDraw
img = Image.new('RGB', (800, 200), 'white')
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('NotoSansLinearA-Regular.ttf', 48)
text = chr(0x10602) + chr(0x1061A) + chr(0x1065C)  # 𐘂𐘚𐙜
draw.text((10, 50), text, font=font, fill='black')
img.save('test_rendering.png')
print('Rendering saved to test_rendering.png')
"

# Test with matplotlib
python3 -c "
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
font = fm.FontProperties(fname='NotoSansLinearA-Regular.ttf', size=48)
fig, ax = plt.subplots()
ax.text(0.5, 0.5, chr(0x10602) + chr(0x1061A) + chr(0x1065C),
        fontproperties=font, ha='center', va='center')
fig.savefig('test_matplotlib.png')
"
```

### 5.5 Server-Side Rendering for TEI Publisher

TEI Publisher needs fonts installed on the server for SVG/PDF rendering:

```bash
# Install Noto Sans Linear A system-wide
sudo mkdir -p /usr/share/fonts/opentype/noto
sudo cp NotoSansLinearA-Regular.ttf /usr/share/fonts/opentype/noto/
sudo fc-cache -fv
# Verify
fc-list | grep -i "linear a"
```

---

## 6. Python Data Pipeline

### 6.1 Libraries & Versions

| Library | Version | Purpose | Why This Version |
|---------|---------|---------|-----------------|
| **Python** | 3.12+ | Runtime | LTS, 5+ year support window |
| **lxml** | 5.3.x | TEI XML parsing/validation | Fastest XML parser for Python; full XSLT 1.0 support |
| **pillow** | 11.x | Image processing (PIL fork) | Active development; supports TIFF, JP2, EXIF |
| **opencv-python** | 4.10.x | Advanced image processing, MSI band alignment | Standard for computer vision tasks |
| **rdflib** | 7.1.x | SKOS RDF vocabulary loading | Full RDF 1.1 support |
| **saxonche** (Python) | 12.x | XSLT 3.0 / XPath 3.1 | TEI ↔ JSON-LD transformation (XSLT 3.0 needed for JSON output) |
| **orjson** | 3.10+ | Fast JSON (de)serialization | 3–5× faster than stdlib json |
| **jsonschema** | 4.23 | JSON-LD validation against schema | Reference implementation |
| **sqlite3** (stdlib) or **psycopg2** | stdlib / 2.9.x | Database | SQLite for dev; PostgreSQL for production |
| **networkx** | 3.4 | Graph analysis of sign co-occurrence | Sign network analysis (Phase 2) |
| **requests** | 2.32.x | HTTP for IIIF / REST APIs | De facto standard |
| **tqdm** | 4.67 | Progress bars for batch processing | UI polish |
| **pydantic** | 2.9.x | Data validation & settings management | Type-safe config |
| **typer** | 0.15+ | CLI tooling | Modern CLI builder |
| **httpx** | 0.28+ | Async HTTP for bulk IIIF manifest fetching | Async parallel downloads |

### 6.2 Pipeline Structure

```
pipeline/
├── pyproject.toml               # Project metadata, dependencies
├── README.md
├── config/
│   ├── settings.yaml             # Paths, credentials, versions
│   └── sign_inventory.yaml       # AB/A number → Unicode mapping
├── data/
│   ├── tei/                      # TEI XML corpus (cloned from Git)
│   ├── images/                   # IIIF image references (not files)
│   ├── pages/                    # PAGE XML from eScriptorium
│   └── exports/                  # JSON-LD exports
├── labrys/
│   ├── __init__.py
│   ├── tei/
│   │   ├── parser.py             # lxml-based TEI parser
│   │   ├── validator.py          # ODD-validate TEI files
│   │   ├── transformer.py        # TEI ↔ JSON-LD via XSLT
│   │   └── stats.py              # Corpus statistics
│   ├── iiif/
│   │   ├── manifest_builder.py   # Generate IIIF manifests from TEI
│   │   ├── image_client.py       # Download IIIF tiles for ML
│   │   └── metadata.py           # Extract XMP/IPTC from images
│   ├── annotation/
│   │   ├── page_importer.py      # Import eScriptorium PAGE XML
│   │   ├── label_schema.py       # Manage annotation labels
│   │   └── converter.py          # PAGE → TEI sign annotations
│   ├── unicode/
│   │   ├── inventory.py          # Sign inventory from Unicode block
│   │   ├── collation.py          # Unicode ↔ SigLA ↔ GORILA mapping
│   │   └── proposal_checker.py   # Check if sign needs Unicode proposal
│   ├── pipeline/
│   │   ├── ingest.py             # Full ingestion: TEI → validate → export
│   │   ├── validate_all.py       # Validate entire corpus
│   │   └── export.py             # Export to JSON-LD / CSV / RDF
│   └── analysis/
│       ├── sign_frequencies.py   # Sign frequency analysis
│       ├── co_occurrence.py      # Build NetworkX graph
│       └── network_viz.py        # Graph visualization output
├── transformations/
│   ├── tei2jsonld.xsl            # TEI XML → JSON-LD (XSLT 3.0)
│   ├── jsonld2tei.xsl            # JSON-LD → TEI (reverse)
│   ├── page2tei.xsl              # PAGE XML → TEI sign annotations
│   └── tei2iiif.xsl              # TEI → IIIF manifest skeleton
├── scripts/
│   ├── bootstrap.sh              # Full setup script
│   ├── ingest_all.py             # Run: labrys pipeline ingest ...
│   ├── export_doi.py             # Prepare Zenodo submission
│   └── validate_unicode.py       # Check all TEI files use correct Unicode
└── tests/
    ├── test_tei_parser.py
    ├── test_iiif_manifest.py
    └── test_unicode_inventory.py
```

### 6.3 Key Pipeline Functions

#### TEI Parsing (lxml)

```python
# labrys/tei/parser.py
from lxml import etree
from pathlib import Path
from typing import Optional, List, Dict

TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}

class TEIParser:
    """Parse Linear A TEI inscriptions."""
    
    def __init__(self):
        self.parser = etree.XMLParser(
            dtd_validation=False,  # ODD validation done separately
            recover=True,
            huge_tree=True
        )
    
    def parse(self, path: Path) -> etree._Element:
        return etree.parse(str(path), self.parser).getroot()
    
    def get_gorila_id(self, root: etree._Element) -> str:
        el = root.find(".//tei:idno[@type='GORILA']", NSMAP)
        return el.text if el is not None else ""
    
    def get_signs(self, root: etree._Element) -> List[Dict]:
        """Extract sign annotations from TEI."""
        signs = []
        for i, g in enumerate(root.findall(".//tei:g", NSMAP), 1):
            sign = {
                "sequence": i,
                "bennett_id": g.get("bennett", ""),
                "sign_type": g.get("signType", ""),
                "transliteration": self._get_translit(g),
                "unicode": g.get("ref", "").split("#")[-1] if g.get("ref") else "",
                "confidence": float(g.get("confidence", 1.0)),
            }
            signs.append(sign)
        return signs
    
    def _get_translit(self, el: etree._Element) -> str:
        seg = el.find("tei:seg[@type='translit']", NSMAP)
        return seg.text if seg is not None and seg.text else ""
```

#### TEI → JSON-LD Transformation (XSLT 3.0 with Saxon)

```python
# labrys/tei/transformer.py
from saxonche import PySaxonProcessor

class TEItoJSONLD:
    def __init__(self, xslt_path: str):
        with PySaxonProcessor(license=False) as proc:
            self.xslt_exec = proc.new_xslt30_processor()
            with open(xslt_path) as f:
                self.executable = self.xslt_exec.compile_stylesheet(
                    stylesheet_text=f.read()
                )
    
    def transform(self, tei_xml: str) -> str:
        result = self.executable.transform_to_string(source_text=tei_xml)
        return result
```

### 6.4 Database Schema (PostgreSQL)

```sql
-- Phase 1 schema: Inscriptions table (core)
CREATE TABLE inscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gorila_id       VARCHAR(20) NOT NULL UNIQUE,
    site            VARCHAR(50) NOT NULL,
    site_code       VARCHAR(4) NOT NULL,
    minoan_period   VARCHAR(20),
    material        VARCHAR(30),
    object_type     VARCHAR(40),
    preservation    VARCHAR(30),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    tei_xml         XML,         -- Canonical TEI stored XML
    json_ld         JSONB,       -- Derived JSON-LD (materialized for performance)
    valid           BOOLEAN DEFAULT FALSE,  -- Schema-validated flag
);

-- Signs table (Tier 2)
CREATE TABLE signs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inscription_id  UUID REFERENCES inscriptions(id) ON DELETE CASCADE,
    sequence        INTEGER NOT NULL,
    bennett_id      VARCHAR(10) NOT NULL,
    unicode         VARCHAR(8),
    character       TEXT,
    transliteration VARCHAR(10),
    sign_type       VARCHAR(20),
    confidence      REAL DEFAULT 1.0,
    x               REAL,  -- bounding box left (relative 0–1)
    y               REAL,  -- bounding box top
    width           REAL,
    height          REAL,
    bbox_unit       VARCHAR(10) DEFAULT 'mm',
    UNIQUE(inscription_id, sequence)
);

-- Images table (Tier 7)
CREATE TABLE images (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inscription_id  UUID REFERENCES inscriptions(id) ON DELETE CASCADE,
    filename        VARCHAR(100) NOT NULL,
    iiif_url        TEXT NOT NULL,
    iiif_manifest   TEXT,
    image_type      VARCHAR(30),
    msi_band        VARCHAR(20),
    width           INTEGER,
    height          INTEGER,
    license         TEXT,
    credit          TEXT,
    is_primary      BOOLEAN DEFAULT FALSE,
    UNIQUE(inscription_id, filename)
);

-- Controlled vocabularies (from SKOS RDF)
CREATE TABLE vocabularies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme          VARCHAR(50) NOT NULL,  -- 'sites', 'periods', etc.
    concept_id      VARCHAR(50) NOT NULL,
    label           VARCHAR(100) NOT NULL,
    definition      TEXT,
    UNIQUE(scheme, concept_id)
);

-- Indexes
CREATE INDEX idx_inscriptions_site ON inscriptions(site);
CREATE INDEX idx_inscriptions_period ON inscriptions(minoan_period);
CREATE INDEX idx_signs_bennett ON signs(bennett_id);
CREATE INDEX idx_signs_inscription ON signs(inscription_id);
CREATE INDEX idx_images_inscription ON images(inscription_id);
CREATE INDEX idx_vocab_scheme ON vocabularies(scheme);
```

### 6.5 Dependency Installation

```bash
# pip install
pip install "lxml>=5.3" "pillow>=11" "opencv-python>=4.10" \
  "rdflib>=7.1" "orjson>=3.10" "jsonschema>=4.23" \
  "networkx>=3.4" "requests>=2.32" "pydantic>=2.9" \
  "typer>=0.15" "httpx>=0.28" "tqdm>=4.67"

# Saxon/C for XSLT 3.0 (separate install)
# From https://www.saxonica.com/download/c.xml
# Or via pip (SaxonCHE has a Python wheel)
pip install saxonche

# For production database
pip install psycopg2-binary
```

---

## 7. Version Control & Data Release

### 7.1 Git LFS Configuration

```bash
# ========================================================
# Git LFS — Labrys Setup
# ========================================================

# Install Git LFS
sudo apt install git-lfs
git lfs install

# Clone the repo with LFS support
git clone git@github.com:labrys-epigraphy/linear-a-corpus.git
cd linear-a-corpus

# Set up LFS tracking
git lfs track "*.tif"
git lfs track "*.tiff"
git lfs track "*.jp2"
git lfs track "*.png"    # large facsimiles only
git lfs track "*.h5"     # ML model files (Phase 2)
git lfs track "*.pth"    # PyTorch checkpoints
git lfs track "*.onnx"

# Track small files normally (no LFS)
git lfs untrack "*.xml"
git lfs untrack "*.json"
git lfs untrack "*.yaml"
git lfs untrack "*.py"
git lfs untrack "*.xsl"

# Verify
git lfs ls-files --all
```

**Important:** GitHub's LFS quota is 1 GB free, 100 GB for Pro. For ~500 GB of images, use:

| Option | Cost | Storage | Bandwidth (monthly) |
|--------|------|---------|---------------------|
| **GitHub Pro** | $4/user/mo | 100 GB LFS | 100 GB |
| **GitHub Team + LFS** | $4/user + $5/50GB | 100 GB + extra | 100 GB |
| **Self-hosted LFS server** | Server cost | Unlimited | Unlimited |
| **Dataset separate from code** | Free | No LFS needed | — |

**Recommendation:** Store code + TEI XML + small JSON in GitHub repo. Store images in a **Zenodo dataset** (free, unlimited, DOI-assigning). Use a `.gitmodules` or a `datasets.txt` manifest so the pipeline knows where to find remote images.

### 7.2 Repository Structure

```
linear-a-corpus/
├── .gitattributes                # LFS rules
├── README.md
├── LICENSE                       # CC-BY 4.0
├── pyproject.toml                # Python package
├── requirements.txt
├── docs/                         # Schema, examples, documentation
│   ├── unified-linear-a-schema.md
│   ├── tei-odd/
│   ├── json-schema/
│   ├── controlled-vocabularies/
│   └── examples/
├── corpus/                       # TEI-XML inscriptions
│   ├── index.xml
│   ├── ht/                       # By site (GORILA code)
│   │   ├── HT_001.xml
│   │   └── ...
│   ├── kh/
│   └── ...
├── pipeline/                     # Python pipeline (see §6)
├── transformations/              # XSLT stylesheets
├── annotations/                  # PAGE XML from eScriptorium
│   └── page/
├── models/                       # Kraken/ML models (if small enough)
│   └── linear-a-v1.mlmodel
├── datasets.txt                  # Manifest linking GORILA ID → image source
└── .zenodo.json                  # Zenodo metadata config
```

### 7.3 Data Release Workflow with Zenodo/DOI

```
┌─────────────────┐
│  Git Tag:        │
│  v1.0.0-beta     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  GitHub Release                     │
│  • Creates tag                      │
│  • Archives repository (code + TEI) │
│  • Triggers Zenodo (via GitHub     │
│    + Zenodo integration)           │
└────────┬────────┬──────────────────┘
         │        │
         ▼        ▼
┌──────────────────┐  ┌──────────────────────────┐
│  Zenodo Dataset 1│  │  Zenodo Dataset 2        │
│  "Labrys TEI     │  │  "Labrys Images — HT"    │
│   Corpus v1.0"  │  │   (subset for Phase 1)   │
├──────────────────┤  ├──────────────────────────┤
│  DOI: 10.5281/   │  │  DOI: 10.5281/zenodo.xxx │
│  zenodo.xxxxx    │  │                          │
│  Content:      │  │  Content: ~500 TIFF images│
│  • corpus/*.xml  │  │  of HT inscriptions      │
│  • docs/         │  │  + IIIF tiles            │
│  • pipeline/     │  │                          │
│  • README, LICENSE│  │  License: CC-BY-NC-SA 4.0│
└──────────────────┘  └──────────────────────────┘
```

### 7.4 Automated Release Script

```bash
#!/usr/bin/env bash
# scripts/release.sh — Create a new Zenodo release

set -euo pipefail

VERSION="${1:-}"  # e.g., v1.0.0-beta
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.0-beta"
    exit 1
fi

# 1. Validate corpus
python3 pipeline/scripts/validate_all.py corpus/
echo "✓ Corpus validated."

# 2. Export JSON-LD for all inscriptions
python3 pipeline/scripts/export_all.py \
    --input corpus/ \
    --output exports/json-ld/
echo "✓ JSON-LD exports done."

# 3. Update zenodo.json metadata
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" .zenodo.json

# 4. Git tag
git add -A
git commit -m "Release $VERSION"
git tag -a "$VERSION" -m "Labyrus TEI corpus release $VERSION"
git push origin main --tags

# 5. GitHub → Zenodo auto-trigger
echo "✓ Pushed tags. Zenodo will auto-archive if integration is active."
echo "  → Check: https://zenodo.org/account/settings/github/"
```

### 7.5 `.zenodo.json` (Zenodo metadata config)

```json
{
  "title": "Labrys — Linear A Digital Epigraphy Corpus",
  "description": "TEI-XML encoded corpus of Linear A inscriptions following the Labrys unified schema. Includes all 7 tiers of annotation for ~1,500 inscriptions from the GORILA corpus.",
  "creators": [
    {
      "name": "Labrys Epigraphy Project",
      "affiliation": "Labrys Digital Epigraphy",
      "orcid": ""
    }
  ],
  "keywords": [
    "Linear A", "Minoan", "epigraphy", "TEI", "undeciphered script",
    "Aegean scripts", "digital humanities"
  ],
  "license": {
    "id": "CC-BY-4.0"
  },
  "upload_type": "dataset",
  "access_right": "open",
  "prereserve_doi": true,
  "version": "1.0.0-beta",
  "publication_date": "2026-08-01"
}
```

---

## 8. Computational Infrastructure

### 8.1 Storage Estimates

| Component | Size | Growth | Notes |
|-----------|------|--------|-------|
| **TEI XML corpus** | ~1.5 MB | ~2 MB final | ~1,500 files, avg ~1 KB each |
| **JSON-LD exports** | ~3 MB | ~10 MB | 4–5× TEI size due to JSON verbosity |
| **Python pipeline** | ~5 MB | ~10 MB | Code, configs, scripts |
| **SKOS RDF vocabularies** | ~50 KB | ~100 KB | 12 files, tiny |
| **eScriptorium PAGE XML** | ~15 MB | ~50 MB | Bounding box annotations + labels |
| **PostgreSQL database** | ~2 GB | ~5 GB | With indexes on ~500K signs |
| **Image derivatives** | ~100 GB | ~500 GB | IIIF cache + thumbnails |
| **Kraken ML model** | ~500 MB | ~2 GB | Saved model + training checkpoints |
| **Docker images** | ~5 GB | ~8 GB | Cantaloupe, eXist, TEI Publisher, eScriptorium, PostgreSQL |
| **Source images (TIFF)** | ~400 GB | ~1.5 TB | Master archival copies (on NAS/object store) |
| **IIIF tile cache** | ~50 GB | ~200 GB | Generated on demand, persists for ~30 days |
| **Backups** | ~200 GB | ~800 GB | Weekly snapshots of DB + corpus |
| **Total active storage** | **~560 GB** | **~2.2 TB** | Without MSI bands |
| **Total with MSI bands (5×)** | **~1.5 TB** | **~4.5 TB** | With all multispectral data |

### 8.2 Server Sizing

| Environment | CPU | RAM | Storage | GPU | Monthly Cost (Cloud) | Notes |
|-------------|-----|-----|---------|-----|---------------------|-------|
| **Dev / Single-user** | 4 vCPU | 16 GB | 500 GB SSD | None | ~$50–80 | TEI Publisher + eScriptorium + DB on one box |
| **Production (Phase 1)** | 8 vCPU | 32 GB | 2 TB NVMe | None (yet) | ~$150–250 | All services, no ML training |
| **Production (Phase 2 ML)** | 16 vCPU | 64 GB | 4 TB NVMe | 1× RTX 4090 (24 GB) or A10G | ~$500–800 | For HTR training + inference |
| **On-prem (recommended)** | 16-core Xeon | 64 GB | 4 TB SSD + 8 TB HDD NAS | 1× RTX 4090 | ~$6,000 (one-time) | Best value for academic project |

### 8.3 Deployment Options

#### Option A: Single Ubuntu Server (Phase 1 — recommended)

```
Services on one machine:
├── Docker containers:
│   ├── tei-publisher (port 8080)
│   ├── cantaloupe (port 8182)
│   ├── escriptorium (port 8000)
│   └── postgresql (port 5432)
├── Python pipeline (cron or manual)
├── Nginx reverse proxy (port 80/443)
└── Let's Encrypt SSL
```

#### Option B: Kubernetes Cluster (Phase 2+)

```
Services in K8s:
├── Namespace: labrys
│   ├── deployment/tei-publisher
│   ├── deployment/cantaloupe
│   ├── deployment/escriptorium
│   ├── statefulset/postgresql
│   ├── deployment/redis
│   ├── job/pipeline-export (cron)
│   └── ingress/nginx
├── Persistent volumes:
│   ├── pvc/images (NFS or S3)
│   ├── pvc/tei-corpus (RWO)
│   └── pvc/postgres (RWO)
└── GPU node pool for ML training
```

### 8.4 Network Architecture

```
Internet ─► Nginx (443 SSL) ─┬──► TEI Publisher (8080)
                              ├──► Cantaloupe IIIF (8182)
                              ├──► eScriptorium (8000)
                              └──► API gateway (Phase 2)
                                      │
                                      ▼
                                 Python Pipeline
                                      │
                                      ▼
                                PostgreSQL (5432, internal)
```

### 8.5 Backup Strategy

```bash
# Daily
pg_dump -U labrys -d linear_a > /backups/db/$(date +%Y%m%d).sql  # ~200 MB compressed
rsync -avz /srv/labrys/tei-corpus/ /backups/tei/                  # ~2 MB
rsync -avz /srv/labrys/images/ /backups/images/       # ~10 GB (changes only)

# Weekly
tar czf /backups/full/$(date +%Y%W).tar.gz \
  /srv/labrys/tei-corpus/ \
  /srv/labrys/escriptorium/data/ \
  /srv/labrys/configs/

# Monthly — snapshot to cold storage (Wasabi/Glacier)
aws s3 sync /backups/full/ s3://labrys-backups/monthly/
```

---

## 9. Complete Technology Stack Summary

### 9.1 Core Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Operating System** | Ubuntu Server / Debian | 24.04 LTS / 12 | Stable base |
| **Container runtime** | Docker + Compose | 27.x + 2.30 | Service isolation |
| **Reverse proxy** | Nginx + Let's Encrypt | 1.26 | TLS termination |
| **Database** | PostgreSQL | 16 | Structured metadata |
| **XML database** | eXist-db (via TEI Publisher) | 6.x | Native XML storage |
| **Caching** | Redis | 7 | Celery + session cache |

### 9.2 Application Stack

| Component | Technology | Version | Licensing |
|-----------|-----------|---------|-----------|
| **TEI editor & CMS** | TEI Publisher | 8.3+ | AGPL v3 |
| **IIIF Image Server** | Cantaloupe | 5.1+ | MIT |
| **Annotation tool** | eScriptorium (Kraken) | 0.14+ | AGPL v3 |
| **Schema language** | TEI ODD (EpiDoc) | P5 4.11+ | CC-BY |
| **Data interchange** | JSON-LD + JSON Schema | 2020-12 | CC-BY |
| **Controlled vocabularies** | SKOS RDF | W3C Rec | CC-BY |

### 9.3 Python Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Python | 3.12+ | Runtime |
| lxml | 5.3.x | TEI parsing |
| saxonche | 12.x | XSLT 3.0 |
| pillow | 11.x | Image processing |
| opencv-python | 4.10.x | MSI alignment, CV |
| rdflib | 7.1.x | SKOS loading |
| orjson | 3.10+ | Fast JSON |
| jsonschema | 4.23 | Validation |
| networkx | 3.4 | Graph analysis |
| psycopg2 | 2.9.x | PostgreSQL |
| httpx | 0.28+ | Async IIIF client |
| pydantic | 2.9.x | Config management |
| typer | 0.15+ | CLI |

### 9.4 Font Stack

| Font | Version | Coverage | License | Use |
|------|---------|----------|---------|-----|
| **Noto Sans Linear A** | 2.005+ | 337/341 | SIL OFL 1.1 | Web UI, documents, rendering |
| **Aegean** (fallback) | 12+ | 340/341 | Freeware | Font fallback, comparison |
| **Noto Sans** | latest | Widespread | SIL OFL 1.1 | UI text, labels (not script) |

### 9.5 Git & Data Management

| Tool | Version | Purpose |
|------|---------|---------|
| Git | 2.45+ | Version control |
| Git LFS | 3.5+ | Binary tracking |
| Zenodo | — | DOI assignment, release |
| GitHub Actions | — | CI/CD, release automation |

### 9.6 Networking & Security

| Component | Technology |
|-----------|-----------|
| TLS | Let's Encrypt (Certbot) |
| Firewall | UFW + iptables |
| WAF | Nginx ModSecurity (optional) |
| Monitoring | Prometheus + Grafana (Phase 2) |
| Log aggregation | Loki / ELK (Phase 2) |

---

## 10. Quickstart: Bootstrap Phase 1

### Prerequisites

```bash
# Hardware (minimum)
# - 4 CPU cores
# - 16 GB RAM
# - 500 GB free disk (SSD recommended)
# - Ubuntu 24.04 LTS or Debian 12

# Install base tools
sudo apt update && sudo apt install -y \
  curl wget git git-lfs docker.io docker-compose-v2 \
  openjdk-21-jdk python3.12 python3.12-venv \
  nginx certbot

# Start Docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for group change
```

### Bootstrap Script

```bash
#!/usr/bin/env bash
# ========================================================
# Phase 1 — Full Bootstrap
# ========================================================

set -euo pipefail

echo "=== Labrys Phase 1 Bootstrap ==="

# 1. Clone the corpus repo
git clone git@github.com:labrys-epigraphy/linear-a-corpus.git
cd linear-a-corpus
git lfs install

# 2. Set up Python environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install saxonche  # XSLT 3.0

# 3. Set up Docker services
echo "→ Starting TEI Publisher..."
docker compose -f docker/tei-publisher.yml up -d

echo "→ Starting Cantaloupe..."
docker compose -f docker/cantaloupe.yml up -d

echo "→ Starting eScriptorium..."
docker compose -f docker/escriptorium.yml up -d

echo "→ Starting PostgreSQL..."
docker compose -f docker/postgres.yml up -d

# 4. Deploy ODD schema to TEI Publisher
curl -X PUT \
  -H "Content-Type: application/xml" \
  --data-binary @docs/tei-odd/linear-a-odd.xml \
  "http://localhost:8080/exist/rest/db/apps/tei-publisher/odd/linear-a.odd"

# 5. Ingest controlled vocabularies
python3 pipeline/scripts/ingest_vocabularies.py \
  --rdf docs/controlled-vocabularies/ \
  --db postgresql://localhost:5432/linear_a

# 6. Ingest sample TEI corpus
python3 pipeline/scripts/ingest_all.py \
  --input corpus/ht/ \
  --db postgresql://localhost:5432/linear_a \
  --validate

# 7. Generate IIIF manifest for HT subset
python3 pipeline/scripts/generate_manifests.py \
  --input corpus/ht/ \
  --base-url https://iiif.labrys.org \
  --output exports/iiif-manifests/

# 8. Export JSON-LD
python3 pipeline/scripts/export_all.py \
  --input corpus/ \
  --output exports/json-ld/ \
  --format jsonld

# 9. Run validation
python3 pipeline/scripts/validate_all.py corpus/

echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "TEI Publisher:     http://localhost:8080/tei-publisher"
echo "Cantaloupe IIIF:   http://localhost:8182/iiif/2"
echo "eScriptorium:      http://localhost:8000"
echo "PostgreSQL:         localhost:5432"
echo ""
echo "Log in with admin user created on first visit."
```

### Service URLs

| Service | URL | Default Credentials |
|---------|-----|--------------------|
| TEI Publisher | `http://localhost:8080/tei-publisher` | Create on first login |
| eXist-db admin | `http://localhost:8080/exist` | admin / (set in compose) |
| Cantaloupe | `http://localhost:8182/iiif/2` | No auth |
| eScriptorium | `http://localhost:8000` | Create on first login |
| PostgreSQL | `localhost:5432` | labrys / labrys_linear_a_2026 |

### Post-Bootstrap Validation Checklist

- [ ] TEI Publisher loads and all sample inscriptions render
- [ ] Cantaloupe returns `info.json` for test images
- [ ] IIIF manifests are valid JSON (validate with `iiif.io/api/presentation/validator`)
- [ ] eScriptorium can import IIIF images and draw bounding boxes
- [ ] PAGE XML exports from eScriptorium convert to TEI correctly
- [ ] Python pipeline validates all TEI files against ODD
- [ ] JSON-LD round-trips (TEI → JSON-LD → TEI) without data loss
- [ ] Git LFS tracking is active and test images pushed correctly
- [ ] Zenodo integration is configured for GitHub repository
- [ ] PostgreSQL schema matches the data model (all 7 tiers)
- [ ] Unicode Linear A signs render in TEI Publisher output
- [ ] SKOS vocabularies are loaded and usable in TEI Publisher forms

---

## Appendix A: References

- **TEI Publisher**: https://teipublisher.com/
- **eXist-db**: https://exist-db.org/
- **Cantaloupe IIIF**: https://cantaloupe-project.github.io/
- **IIIF Presentation API 3.0**: https://iiif.io/api/presentation/3.0/
- **eScriptorium**: https://gitlab.com/scripta/escriptorium
- **Kraken OCR**: https://github.com/mittagessen/kraken
- **Noto Sans Linear A**: https://fonts.google.com/noto/specimen/Noto+Sans+Linear+A
- **Aegean Font**: https://users.teilar.gr/~g1951d/
- **Unicode Aegean Block**: https://www.unicode.org/charts/PDF/U10600.pdf
- **Script Encoding Initiative**: https://linguistics.berkeley.edu/sei/
- **SigLA Database**: https://sigla.phis.me/
- **TEI P5 Guidelines**: https://tei-c.org/release/doc/tei-p5-doc/
- **EpiDoc**: https://epidoc.stoa.org/
- **Saxon/C HE (Python)**: https://www.saxonica.com/download/c.xml
- **Zenodo**: https://zenodo.org/
- **Labrys Docs**: `docs/` in this repository
