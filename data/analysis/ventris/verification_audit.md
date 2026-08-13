# Phase 11 Verification — Claims Audit

**Purpose:** Verify every finding before synthesis. This audit caught TWO
compromised claims (Avenue 1 AB 85, Avenue 2 AB 82) — both were circular
artifacts of corpus encoding, not independent discoveries.

---

## Claim 1 — Oracle: "scorer has no signal" ✅ CONFIRMED

- **Re-verified:** With the strengthened 4-term scorer (Kober, cross-entropy,
  anchors), hidden confirmed signs still rank the true value 45th/70, excluded,
  and 37th/70 — argmax never right.
- **Robust:** Held across 4 scorer versions, 8-trials × 20-hidden oracle,
  and per-sign isolation. The leakage fix and A+B+C strengthening changed
  nothing (0.11× → 0.59×, still below chance).
- **Note:** the two signs "recovered" (AB 28, AB 01) have 1 candidate each —
  trivial.

## Claim 2 — Avenue 1: "AB 85 is the word divider" ❌ COMPROMISED

- **What I claimed:** AB 85 flagged as #1 positional anomaly (med=0.06, 508 occ)
  → independently confirms word-divider hypothesis.
- **What verification found:**
  - AB 85's transliteration is `*301` (258 occ) / `*306` (2 occ) — **logogram
    numbers**, not syllabogram values.
  - The `word_dividers` table is **empty** — no word-divider records exist.
  - AB 85's grid status is `CONFIRM` with value `?` and confidence 25/100 —
    the "confirmation" is low-confidence, possibly a bootstrapping artifact.
  - The positional anomaly (never medial) is real but its interpretation as
    "word divider" is NOT independently established — it could equally be a
    frequently-standalone logogram/ligature.
- **Verdict:** The positional *fact* (never medial) stands. The *interpretation*
  (word divider) is unsupported — circular or ambiguous. Must be downgraded.

## Claim 3 — Avenue 2: "AB 82 ↔ LIVESTOCK (Bonferroni, 70×)" ❌ COMPROMISED

- **What I claimed:** AB 82 significantly enriched in LIVESTOCK contexts
  (p=0.0002, 70× fold) — the project's strongest lead.
- **What verification found:**
  - Both LIVESTOCK co-occurrences come from the **same inscription (PH10)**,
    where AB 82 appears as `HIDE+[?]` — a **livestock ligature** (hide/skin).
  - AB 82's transliteration is `HIDE+[?]` in 3 of 11 occurrences — the
    commodity pipeline classified those rows as LIVESTOCK.
  - So AB 82's "enrichment" is **baked into the data encoding**: it IS a HIDE
    ligature inside livestock entries. The test rediscovered the encoding.
- **Verdict:** Circular — the association is real in the data but not an
  independent discovery. Must be retracted as a "discovery"; reframed as
  "AB 82 co-occurs with HIDE ligatures in livestock entries" (a data fact,
  not an insight).

## Claim 4 — Avenue 3: "all cryptanalysis signals are frequency artifacts" ✅ CONFIRMED

- **Re-verified:** Zipf alpha identical under token shuffle (1.502 both).
  Bigram reduction 26.7% real vs 18.1% shuffled — ~7pp real, weak.
  Kober V-link cohesion circular (V-links = shared context).
- **Robust:** Null controls (shuffle) are the correct methodology; the
  conclusions hold.

## Claim 5 — Avenue 4: "graph isomorphism untestable + no phonetic correlation" ✅ CONFIRMED

- **Re-verified:** No LB corpus sequences in repo. Community structure
  degenerate (337/345 in one component). Top-degree signs are numerals.
- **Robust:** The 55%-vs-59% correlation comparison was crude but the
  conclusion (centrality ≠ phonetic signal) holds — top-10 syllabogram
  values are phonetically incoherent.

---

## Summary

| Claim | Status |
|-------|--------|
| Oracle: scorer has no signal | ✅ Confirmed |
| Avenue 1: AB 85 word divider | ❌ **Compromised** (positional fact real, interpretation unsupported) |
| Avenue 2: AB 82↔LIVESTOCK | ❌ **Compromised** (circular — HIDE ligature encoding) |
| Avenue 3: signals are artifacts | ✅ Confirmed |
| Avenue 4: untestable + no signal | ✅ Confirmed |

**Bottom line for synthesis:** The only claims that survive verification are
the NEGATIVE ones (oracle, Avenue 3, Avenue 4). The two POSITIVE findings
(Avenue 1 word divider, Avenue 2 livestock) were both artifacts of corpus
encoding. The honest synthesis must present the project's outcome as: **all
computational avenues exhausted; no phonetic or semantic discovery survives
verification; the corpus is below the noise floor; new data is the only path.**
