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

---

## Audit of Prior Phases (2–9) Claims

Beyond my own findings, the synthesis will cite Phase 2–9 results. These were
audited against their source CSVs:

### P1. "77 CONFIRMED anchors" — ⚠️ PARTIALLY OVERSTATED
- 19 of 77 CONFIRMED signs have value `?` (confirmed as category, no value).
- 20/77 low-confidence (<50); only 17/77 ≥70.
- The Phase 5 refined grid confirms only 44 as CONFIRM — the two grids disagree
  by 33 signs. My oracle's "58 anchors" are the intersection of 77-minus-`?`
  minus 19, but ~20 of those are low-confidence.
- **Synthesis must say "~58 values, ~17 high-confidence" not "78 anchors".**

### P2. "17 high-confidence anchors" — ⚠️ 3 ARE DISPUTED
- AB 01 (da), AB 38 (e), AB 50 (pu) are high-confidence in bootstrap grid but
  downgraded to UNCERTAIN in the refined grid — the SAME LB/CM conflicts the
  MASTER_SYNTHESIS flags as unresolved (AB 01 da/ta, AB 38 e/pa).
- **Synthesis must not present these as settled.**

### P3. Toponyms (pa-i-to, i-da) — ✅ SOLID
- PHAISTOS: 95 matches at edit-distance 1 across ~75 inscriptions, 8+ sites.
- IDA: 20 matches, patterns I-DA (14) and I-TA (6) — robust to the da/ta
  conflict (both readings give the same place name).
- **These are the strongest lexical claims and they hold.**

### P4. "Tyrsenian is the best structural fit" — ❌ OVERSTATED
- AGENTS.md: "Tyrsenian ranks highest structurally (5/8 WALS, 62.5%)".
- Actual candidate_ranking.csv: Anatolian IE #1 (8), Hurro-Urartian #2 (8),
  Tyrsenian #3 (7) — ALL "INCONCLUSIVE (tentative)".
- WALS: no family clearly wins; Anatolian has 8 features at comparable
  confidence to Tyrsenian's 8.
- **Synthesis must say "no family distinguished; several weakly compatible;
  all inconclusive" — not "Tyrsenian best".**

### P5. "Agglutinative morphology" — ✅ SUPPORTED (weakly)
- 24 alternation paradigms exist, but with small attestations. The claim is
  reasonable but rests on limited data.

### P6. Misvalued signs (AB 16, AB 60, AB 80) — ✅ SUPPORTED
- Positional anomaly is real and reproducible (Avenue 1 table). The
  interpretation "misvalued" follows from the anomaly + LB/CM conflict.

---

## Consolidated Verdict for Synthesis

| Claim | Source | Status |
|-------|--------|--------|
| Oracle: no scorer signal | Phase 10c | ✅ Confirmed |
| Avenues 3/4 negative | Phase 11 | ✅ Confirmed |
| Avenue 1 AB 85 word divider | Phase 11 | ❌ Retracted |
| Avenue 2 AB 82↔LIVESTOCK | Phase 11 | ❌ Retracted |
| 77 CONFIRMED anchors | Phase 8 | ⚠️ Overstated (58 values, 17 high-conf) |
| Toponyms pa-i-to/i-da | Phase 3 | ✅ Solid |
| Tyrsenian best fit | Phase 3 | ❌ Overstated (no family distinguished) |
| Agglutinative morphology | Phase 3 | ✅ Supported (weak) |
| Misvalued signs | Phase 2/5 | ✅ Supported |

**The synthesis's honest case:** the solid results are the toponyms (real,
robust), the misvalued-sign flags (real), and the negative results (oracle +
avenues). The "best family fit" and "78 anchors" claims must be downgraded.
