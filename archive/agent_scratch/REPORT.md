# REPORT.md — Egyptian Bridge Marshal

## Task

Create `pipeline/egyptian_bridge/` with corpus.py (Egyptian trade vocabulary) and search.py (consonant-class substring search against Linear A corpus), exploring whether Egyptian trade vocabulary appears as Linear A sign sequences in commodity-appropriate administrative contexts.

## Methodology

### Vocabulary (corpus.py)

88 Middle Egyptian trade/commerce terms were encoded with:
- **Standard Egyptological transliteration** (Gardiner/Faulkner conventions)
- **Single-char consonant skeleton** (T=ṯ, D=ḏ, S=š, H=ḥ, X=ḫ, Q=ḳ)
- **Weak consonants stripped** (ꜣ, ꜥ, j, w → vowel carriers, ignored in skeleton)
- **Categories**: agriculture, beverages, commodities, materials, metals, trade, administrative

Source: Gardiner (1957), Hoch (1994), Loprieno (1995), Faulkner (1962) — well-attested Middle/Late Egyptian trade vocabulary including grain, oil, wine, metal, textile, vessel, scribal, and metrological terms.

### Search (search.py)

**Consonant-class matching approach:**

1. Map each Egyptian consonant → **consonant class**:
   - P: p, b, f, q (labial)
   - T: t, d, ṯ, ḏ (dental)
   - K: k, g, ḫ, ḳ (velar)
   - S: s, z, š (sibilant)
   - N: m, n (nasal)
   - R: r, l (liquid)
   - W: w, j (glide)
   - G: ḥ, h (glottal/pharyngeal)

2. Map each LA syllabogram → consonant class by onset:
   - pa, ba, ma, qa → P; ta, da, na → T; ka, ga → K
   - sa, za → S; ra, la → R; wa, ja → W; a, e, i, o, u → V

3. Search for Egyptian consonant-class skeletons as contiguous substrings in the LA corpus class strings.

4. **Two sources**: conventional AB values AND Phase 8 expanded grid values.

5. **Filter**: ≥3 consecutive consonant classes (signs).

6. **Context**: commodity logogram (GRA, OLE, VIN, AROM, CYP, etc.) within ±3 sign positions.

### Scoring

| Factor | Weight |
|--------|--------|
| Sign count | 15/sign, max 60 |
| Commodity context | +20 |
| Expanded source | +5 |
| Trade/commodity category | +10 |
| Agriculture/metals/materials | +5 |

### Null Model

Per-inscription character shuffling (200 permutations each) to estimate expected matches under random ordering while preserving per-text length distributions.

## Results

### Summary Statistics

| Metric | Value |
|--------|-------|
| Egyptian words encoded | 88 |
| Words with ≥3-sign skeletons | 46 |
| Corpus inscriptions searched | 1,220 |
| Valid syllabogram tokens | 4,232 |
| Total consonant-class matches | 312 |
| Unique Egyptian words matched | 25 |
| Unique inscriptions matched | 151 |
| Matches with commodity context | 40 |
| Egyptian words with commodity context | 16 |

### Top Matches

| Score | Egyptian | English | Class | Inscription | LA Match | Commodities |
|-------|----------|---------|-------|-------------|----------|-------------|
| 90 | sntr | incense | SNTR | HT96a | si+mi+ta+ru | AROM, GRA |
| 80 | SDr | wine (šdḥ) | STR | ZA11a | so+ta+ra | VIN |
| 80 | SDr | wine (šdḥ) | STR | ZA15a | za+do+re | VIN |
| 80 | Ssr | fine linen | SSR | HT27b | sa+sa+re | GRA, VIN |
| 80 | mns^ | Canaanite jar | NNS | HT128a | mu+nu+se | GRA |
| 75 | bdt | emmer wheat | PTT | HT9a | pa+de+tu | — |
| 75 | Ssr | fine linen | SSR | HT18 | se+sa+ra | GRA |
| 75 | Ssr | fine linen | SSR | HT27b | sa+sa+re | GRA, VIN |

### Null-Model Ratios

| Egyptian Word | Class | Observed | Expected (shuffled) | Ratio |
|---------------|-------|----------|---------------------|-------|
| Ssr | SSR | 30 | 9.1 | 3.3x |
| md't | NTT | 39 | 12.6 | 3.1x |
| mnw | NNW | 20 | 3.1 | 6.4x |
| kftjw | KPT | 17 | 5.8 | 2.9x |
| SDr | STR | 17 | 8.7 | 2.0x |
| kmt | KNT | 20 | 10.5 | 1.9x |
| jrtt | RTT | 21 | 12.8 | 1.6x |

### Category Distribution

| Category | Matches |
|----------|---------|
| administrative | 104 |
| commodities | 87 |
| agriculture | 46 |
| trade | 40 |
| beverages | 17 |
| materials | 10 |
| metals | 8 |

## Analysis

### Key Question

> Do 3–5 Egyptian trade words appear as LA sign sequences in commodity-appropriate contexts?

**Yes — 16 Egyptian trade words have consonant-class matches with nearby commodity logograms.** The most credible are:

1. **sntr (incense/frankincense)** — 4-class match (SNTR → S-N-T-R) on HT96a, adjacent to AROM (aromatics) AND GRA (grain) logograms. Frankincense was a major trade commodity and its Egyptian name (sntr, Coptic ⲥⲟⲛⲧⲉ) is well-attested.

2. **SDr (wine type)** — 3-class match (STR → S-T-R) on ZA11a and ZA15a, both with VIN (wine) logograms nearby. Contextually appropriate.

3. **Ssr (fine linen)** — 3-class match (SSR → S-S-R) on multiple texts including HT27b and HT18, with GRA and VIN nearby. Linen was a major Egyptian export.

### Honest Assessment

**The matches exist but are consistent with chance.** The null-model ratios of 1.6x–6.4x show some words (SSR, NNW) are above chance, but:

1. **3-consonant-class matches are extremely common.** With only 8 classes and 4,232 positions, a 3-class sequence like T-T-K appears ~10 times by chance.

2. **Administrative vocabulary dominates results.** "Document" (md't), "year" (rnp), "Egypt" (kmt), "overseer" (jmj-r) produce most matches, yet these are the least likely to appear as loanwords — they're basic administrative terms that every language has natively.

3. **The best matches are still ambiguous.** sntr → SI-MI-TA-RU could be coincidental. The class match (S-N-T-R) is only 4 signs long, and SI-MI-TA-RU is a common LA sequence.

4. **No directionality claim is possible.** Even if genuine, kftjw (Egyptian name for Crete) → K-P-T class match could be Minoan→Egyptian (Egyptian Keftiu = Minoan Kaphtor), not Egyptian→Minoan.

5. **Corpus genre bias.** The surviving LA corpus is administrative (tablets, sealings), not commercial correspondence. Trade vocabulary may simply not appear in this genre, regardless of whether loanwords existed in spoken Minoan.

### Why This Is Hard (Inherent Limitations)

| Limitation | Impact |
|------------|--------|
| Egyptian omits vowels | Can't distinguish ta/te/ti/to/tu — all collapse to T |
| LA values uncertain (~50% unconfirmed) | Most signs we search against are probabilistic |
| 4,232 tokens is tiny | A 3-class match has baseline probability of ~0.3% per position |
| No word boundaries in cuneiform-style texts | Substring matching finds embedded sequences in longer words |
| Consonant-class matching is broad | P/T/K/S/N/R/V/W = 8 classes, many random 3-class sequences exist |

## Deliverables

| File | Description |
|------|-------------|
| `pipeline/egyptian_bridge/__init__.py` | Module init |
| `pipeline/egyptian_bridge/corpus.py` | Egyptian vocabulary encoding |
| `pipeline/egyptian_bridge/search.py` | Consonant-class search engine |
| `data/analysis/egyptian_bridge/egyptian_vocabulary.csv` | 88 Egyptian trade terms |
| `data/analysis/egyptian_bridge/match_results.csv` | 312 match results |
| `data/analysis/egyptian_bridge/egyptian_report.md` | Full markdown report |

## Commands

```bash
# Generate vocabulary
uv run python pipeline/egyptian_bridge/corpus.py

# Run search
uv run python pipeline/egyptian_bridge/search.py
```

## Verdict

**This approach does not provide strong evidence for Egyptian loanwords in Linear A.** While 16 Egyptian trade words produce consonant-class matches near commodity logograms, the signal-to-noise ratio is too low to distinguish genuine borrowings from coincidence. A definitive answer would require:
- Better phonetic values for LA signs (reducing consonant-class granularity)
- Larger corpus (more texts = more statistical power)
- Multi-evidence convergence (phonological regularity + semantic fit + archaeological context)
- Word-boundary awareness (matching whole words, not substrings)

This negative finding is itself informative: if Egyptian loans are common in Linear A, they are well-hidden by the combination of LA's uncertain phonology and the corpus's small administrative focus.
