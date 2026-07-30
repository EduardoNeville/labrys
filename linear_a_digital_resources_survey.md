# Survey of Digital Resources for Linear A

**Date:** 2026-07-30  
**Task:** Agent 1 — Comprehensive resource survey

---

## 1. SigLA — The Signs of Linear A Database

| Property | Detail |
|----------|--------|
| **URL** | https://sigla.phis.me/ |
| **Format** | Interactive web app; data shipped as client-side JavaScript (~2.5MB database.js) |
| **License** | CC BY-NC-SA 4.0 (dataset and drawings) |
| **Coverage** | All tablets from GORILA: Arkhanes, Khania, Mallia, Phaistos, Knossos, Tylissos, Zakros, Hagia Triada (HT 1-133+). Continuously expanding. |
| **Last updated** | Ongoing (beta; last visible news: January 2021). Actively maintained. |
| **Machine-readable?** | ⚠️ Partially. No JSON/XML/CSV export. Data is embedded in minified JS but extractable. |
| **API?** | ❌ No documented REST API. All queries are client-side against the bundled JS database. |
| **Download?** | ❌ No bulk download link. Must scrape `database.js`. |
| **Contact** | Ester Salgarella (es636@cam.ac.uk), Simon Castellan (simon@phis.me) |

**What it offers:** Interactive paleographical database with sign attestation highlighting on tablet images, word views, complex search, map view. The most polished interactive Linear A resource.

---

## 2. Winterstein et al. 2015 — Linear A Digital Corpus (XML/TEI-EpiDoc)

| Property | Detail |
|----------|--------|
| **URL (paper)** | https://aclanthology.org/W15-3715/ |
| **URL (data)** | http://hdl.handle.net/10220/40744 (NTU repository) — currently behind AWS WAF CAPTCHA |
| **Format** | XML / TEI-EpiDoc (Epigraphic Doc) |
| **License** | Paper: ACL (likely CC-BY). Dataset license unclear. |
| **Coverage** | 1,427 Linear A documents (7,362–7,396 signs) — 75.5% of GORILA corpus |
| **Last updated** | 2015 (frozen) |
| **Machine-readable?** | ✅ Yes — well-structured XML/TEI. Unicode Linear A characters used. |
| **Downloadable?** | ⚠️ Theoretically yes, but the NTU repository currently requires solving a CAPTCHA (AWS WAF). |

**What it offers:** The first and most complete TEI-EpiDoc corpus of Linear A. Converts Younger's transcriptions to Unicode. Proper XML structure with Leiden-style epigraphic markup. **However, the actual dataset may no longer be easily accessible.**

---

## 3. GORILA — Digitization Status

| Property | Detail |
|----------|--------|
| **Reference** | Louis Godart & Jean-Pierre Olivier, *Recueil des inscriptions en Linéaire A* (5 vols, 1976–1985) |
| **Total documents** | ≈1,427 |
| **Fully digitized** | ~75% via Younger's transcriptions, SigLA, lineara.xyz, Winterstein corpus |
| **Still print-only** | ~25% — fragmentary texts, lesser-known documents not yet transcribed digitally |
| **Images** | GORILA photos/facsimiles used in SigLA and lineara.xyz under © École Française d'Athènes |

**Status:** There is no single open-access digitization of the complete GORILA corpus. What exists are overlapping partial digitizations in different formats.

---

## 4. Unicode Aegean Block (U+10600–U+1077F)

| Property | Detail |
|----------|--------|
| **URL** | https://www.unicode.org/charts/PDF/U10600.pdf |
| **Assigned characters** | 341 of 384 code points |
| **Unicode version** | 7.0 (June 2014); latest chart: Unicode 17.0 (2025) |
| **Font support** | Noto Sans Linear A (Google, SIL OFL), Aegean (George Douros), CTAN lineara package |
| **Coverage gaps** | 43 unassigned code points. Not all fonts cover all 341 characters. Some complex ligatures may not render. |

---

## 5. John G. Younger's Online Resources

| Property | Detail |
|----------|--------|
| **URL (archive)** | https://web.archive.org/web/20231222205430/http://www.people.ku.edu/~jyounger/LinearA/ |
| **Original URL** | http://people.ku.edu/~jyounger/LinearA/ — **currently offline** (DNS NXDOMAIN) |
| **Format** | Plain HTML pages, JPEG sign charts |
| **Coverage** | 1,077 transcriptions (75.5% of GORILA), lexicon, sign lists, palaeographic charts, grammar notes |
| **Last updated** | July 3, 2023 |
| **Machine-readable?** | ❌ No. All data in HTML tables. Must be scraped. |
| **License** | Not explicitly stated (freely accessible) |

**What it offers:** The foundational digital Linear A resource. Includes HT texts, other site texts, religious texts, lexicon (forward & reverse), phonetic grids, ideogram charts, palaeographic charts. **Only accessible via Wayback Machine.**

---

## 6. GitHub Repositories & Open Datasets

| Repository | Stars | Format | License | Notes |
|-----------|-------|--------|---------|-------|
| [mwenge/lineara.xyz](https://github.com/mwenge/lineara.xyz) | 38 | JSON (1,720 docs) | None (code) | **Best structured open dataset.** Web viz tool. |
| [ryanpavlicek/linearaworkbench](https://github.com/ryanpavlicek/linearaworkbench) | 3 | TSX/SPA | Apache-2.0 | 50 analysis modules. Uses lineara.xyz upstream. |
| [ryanpavlicek/pyaegean](https://github.com/ryanpavlicek/pyaegean) | 1 | Python lib | Apache-2.0 | NLP toolkit for Aegean scripts. |
| [sakamoto6000-png/linear-a-structural-analysis](https://github.com/sakamoto6000-png/linear-a-structural-analysis) | 2 | Python | MIT | Structural analysis, GORILA-based. |
| [elliottbolzan/Ariadne](https://github.com/elliottbolzan/Ariadne) | 1 | Python | None | PDF generation of GORILA corpus. |
| [deemkeen/linear-a-arithmetic](https://github.com/deemkeen/linear-a-arithmetic) | 0 | ? | — | Arithmetic hypothesis testing. |
| [TJRoch/proto-minoan-grammar-model](https://github.com/TJRoch/proto-minoan-grammar-model) | — | — | — | Grammar model from Linear A. |

**Key finding:** The `mwenge/lineara.xyz` JSON dataset is the most complete, structured, freely accessible corpus (1,720 entries, 52 sites). It has become the de-facto upstream data source for other tools (lineara.xyz website, linearaworkbench).

---

## 7. Minoan Language Research Group (Bologna) / INSCRIBE

| Property | Detail |
|----------|--------|
| **URL** | https://site.unibo.it/inscribe/en |
| **Project** | INSCRIBE — *Invention of Scripts and Their Beginnings* (ERC Consolidator Grant) |
| **Coverage** | Multi-script comparative (Linear A, Linear B, Cretan Hieroglyphic, Cypro-Minoan) |
| **Datasets** | ❌ No public datasets found |
| **Output** | Academic publications, books, conference presentations |

**Note:** The older URL `site.unibo.it/minoan-language-research-group` returns 404. The group appears to have been rebranded/absorbed into the INSCRIBE project.

---

## 8. Thesaurus of the Minoan Language (TML) Project

| Property | Detail |
|----------|--------|
| **URL** | ❌ No active website found |
| **Status** | Unknown — may have been a proposed project or a short-lived initiative. No digital presence found through searches of academic databases, GitHub, or web archives. |

**Note:** This project could not be located. It may refer to an earlier concept that was never implemented, or a small project with no public web presence.

---

## 9. Image Databases

| Resource | URL | Linear A Coverage |
|----------|-----|-------------------|
| **CMS** (Corpus der Minoischen und Mykenischen Siegel) | https://idai.world/ (moved from cms.mainz.org) | Seal stones with Linear A inscriptions. Image metadata via iDAI.objects SPA. |
| **iDAI.objects / Arachne** | https://arachne.dainst.org → https://idai.world/ | Archaeological object images including CMS seals. Anti-bot protection. |
| **MFA Boston** | https://collections.mfa.org/ | Linear A objects (votive double axe, etc.) with IIIF images. |
| **British Museum** | https://www.britishmuseum.org/collection | Linear A inscribed objects in collection. |
| **SigLA** | https://sigla.phis.me/ | GORILA facsimile images embedded in interactive viewer. |

**Machine-readable:** CMS/iDAI objects has a REST API but requires authentication. No dedicated IIIF manifest for Linear A was found.

---

## 10. IIIF Endpoints & API-Accessible Repositories

| Resource | IIIF/API | Notes |
|----------|----------|-------|
| iDAI.world (DAI) | API exists with auth | SPA, no public IIIF manifest for Linear A |
| British Museum | IIIF | Objects with Linear A inscriptions available as IIIF |
| MFA Boston | IIIF | Individual objects served as IIIF |
| Cambridge Digital Library | IIIF | Could host Linear A material but no dedicated collection found |
| École Française d'Athènes | No public IIIF | Holds GORILA copyright; images used under license |

**Finding:** No aggregated IIIF endpoint for Linear A inscriptions exists. Individual museum systems may serve IIIF images of objects bearing Linear A text, but there is no focused corpus-level IIIF collection.

---

## Summary Table

| # | Resource | Format | License | Coverage | Machine-Readable | Last Updated |
|---|----------|--------|---------|----------|-----------------|-------------|
| 1 | **SigLA** | Web app (JS) | CC BY-NC-SA 4.0 | All major sites, growing | ⚠️ (JS only) | Current |
| 2 | **Winterstein 2015** | XML/TEI-EpiDoc | Unclear | 1,427 docs (75.5%) | ✅ Yes | 2015 |
| 3 | **GORILA** | Print | © ÉFA | 1,427 docs | ❌ | 1985 |
| 4 | **Unicode Aegean** | Unicode standard | Free | 341 characters | ✅ Yes | 2025 |
| 5 | **Younger's site** | HTML | Free (?) | 1,077 docs | ❌ | 2023 (offline) |
| 6 | **lineara.xyz** | JSON | None | 1,720 entries | ✅ Yes | 2026 |
| 7 | **INSCRIBE (Bologna)** | Academic | Varied | Multi-script | ❌ | Current |
| 8 | **TML** | — | — | — | — | — |
| 9 | **CMS / iDAI** | Web + API | Academic | Seals w/ Linear A | ⚠️ | Current |
| 10 | **IIIF** | Various | Varied | Scattered | ⚠️ | Current |

**The key actionable dataset is `mwenge/lineara.xyz` (JSON, 1,720 entries, MIT-like). SigLA provides the best interactive exploration. Winterstein's TEI corpus is the most academically rigorous but may be inaccessible.**
