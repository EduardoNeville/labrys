# LB Sandbox Result — Condition (a): NO SIGNAL (0.00×)

**Date:** 2026-09-15 · **Pre-registered gate:** lift > 1.5× (pass) / 0.5–1.5 (inconclusive) / ≤0.5 (no signal) — committed in `ventris_report.md` *before* the run.

## The measurement

> **RETRACTED / SUPERSEDED (2026-09-15, later the same day).** The counts below are
> reproducible, but the *interpretation* was wrong. A full retrace
> (`data/analysis/ventris/oracle_retrace_findings.md`) found three bugs — one in this
> sandbox's Kober generation, two in the pipeline (`oracle_test` chance baseline,
> `_load_kober` discarding the C/V distinction). The 0.00× is a valid measurement of a
> **broken instrument**, not evidence that the corpus lacks signal. See the retrace for the
> corrected reading.

| Quantity | Value |
|---|---|
| Corpus | 4,794 LB inscriptions, 40,038 sign tokens (deduped from 7,370 source rows) |
| Anchors | 73 CONFIRM (Unicode Linear B standard), 15 UNCERTAIN (LB signs with no accepted reading) |
| Sign tokens coverage | 100.0% (gate > 95%) |
| Unique signs | 88 (75 named + 13 numbered-but-unnamed) |
| Oracle | 8 trials × 20 hidden = 160 scores |
| **Recovery** | **0.0000** vs chance 0.0193 → **lift 0.00×** (chance after fixing the baseline bug; it was 0.0683 with the buggy leaky baseline) |
| Signs recovered | none (after leak fix; see below) |

The pipeline scored a *deciphered script* — real Greek, perfect anchors, 4× the Linear A corpus — and recovered **zero** hidden phonetic values. **But the instrument is broken:** the Kober constraint channel was dead (my sandbox passed a 15-sign uncertain set into a filter that needs a *large* one, collapsing the link graph to 3 anchors), the candidate space stayed at 39–70 values per sign, and no aggregator ever produces a unique argmax. See the retrace before drawing any conclusion about Linear A from this.

## First result was a leak (important for the Linear A baseline too)

Initial run showed recovery 8.75% vs chance 6.83% (1.28×), from exactly two signs: **AB 01 (da)** and **AB 28 (i)**. Both appear in the hardcoded anchor words `pa-i-to` / `i-da`. `get_candidates()` restricted candidates using the **full** `self.confirmed` rather than the oracle's effective anchor set (`confirmed_override`), so a *hidden* sign was still anchor-constrained to its own true value. The "gate on membership in `self.confirmed`" guard in `complete.py` was wrong: hidden signs remain in `self.confirmed` during the oracle.

Fixed: `get_candidates(bid, confirmed=None)` now takes the effective anchor set; `_greedy_restore` passes `confirmed_override` through (change is behavior-neutral for the non-oracle path).

**Consequence for Linear A:** the historical 0.6× chance baseline was measured by leaky machinery. Re-running the original configuration (default grid + `lineara_full.db`) with the leak fixed gives **0.00× for Linear A as well**. The Phase 10c conclusion (no signal, no optimizer can help) is unchanged — now stronger: exactly zero of 160.

## Caveats (honest)

1. **Greedy restoration, not exhaustive search.** `_greedy_restore` is coordinate ascent from the first candidate. A zero recovery rate means the *scorer* cannot distinguish correct values during greedy search — which is the oracle's designed question — but a beam search over a flat objective is not ruled out by this run. Per the repo's own philosophy (§10c), the objective is tested before the optimizer is built; this run fails on the objective.
2. **Parsing is new.** The 88-sign inventory and top frequencies (ro, jo, a, ko, to, ke, e, wo, pa, ra…) match the known Linear B distribution, so the parse is not scrambled; but a parser error that specifically degraded co-occurrence structure would weaken the scorer's only channel. The 100% token coverage and the distributional sanity check bound this risk.
3. **Kober triples:** 101 strict triples on LB vs 11,845 on LA — the LB candidate sets (chance 6.8% ≈ tighter than LA's 8.4%) still never pinned a hidden sign to a single value. The link graph constrains; it does not identify.
4. **LB is the best case.** This was the condition with maximum anchors, correct values, real Greek phonotactics, and editor-supplied word division. Any weaker condition (Linear A's hypothesized anchors, agglutinative profile) can only do equal or worse. Condition (b) — substituting the Minoan morphological profile — is **not informative at 0.00× and is deferred**: there is no signal left to decompose.

## What the sandbox buys

- **Method verdict:** the Ventris endgame scorer family is at zero signal even with ground truth. Published as a negative, this closes a genre of unfalsifiable Linear A "method wins" papers.
- **LA baseline corrected:** 0.6× → 0.00×, independently.
- **A real bug found:** the oracle's anchor leak would have invalidated any future LA "positive" built on the same scorer.

## Artifacts

| File | Content |
|---|---|
| `languages/linear-b/data/raw/tablets.csv` | source corpus (InsiderPhD, 7,370 rows) |
| `languages/linear-b/translit_to_signid.csv` | 75-entry translit→AB-ID table (Unicode primary, `la_mapping` cross-check) |
| `languages/linear-b/answer_key.csv` | 73 CONFIRM + 15 UNCERTAIN — the only file with LB values |
| `languages/linear-b/data/database/linear-b.db` | anonymized corpus (transliteration NULL everywhere) |
| `languages/linear-b/data/analysis/kober/` | LB triples / frame links |
| `languages/linear-b/data/analysis/ventris/ventris_report.md` | pre-registration + verdict |
| `languages/linear-b/data/analysis/lb_grid_vs_unicode_mismatches.csv` | repo grid audit (below) |
| `languages/linear-b/config.yaml` | per-language config |

## Supplementary finding: `la_lb_mapping.csv` grid audit

Repo's LA↔LB grid vs the Unicode Linear B standard:
- **71/117 rows:** `lb_unicode`/`lb_char` point at a *different* sign (systematic offset — the glyph column was generated arithmetically; AB 78's `lb_char` lands on an unassigned codepoint).
- **11 rows:** `lb_value` disagrees with the standard value for that number. 6 are hard conflicts (Unicode names the sign): **AB 11** (repo `si`, std `po`), **AB 21** (`mi` vs `qi`), **AB 29** (`pu` vs `pu2`), **AB 33** (`ra` vs `ra3`), **AB 42** (`ke` vs `wo`), **AB 66** (`ta` vs `ta2`). The other 5 (AB 18/19/22/35/79) have no Unicode name to check against.
- The LA-side columns drift too (AB 21→AB22M, AB 42→AB49, AB 78→AB131B in Unicode names), while AB 01/02 are correct — same position-vs-number class of bug Phase 11 fixed in `unicode_utils.py`.

**Impact:** the `lb_value` column feeds the LB-transfer portion of the LA "CONFIRMED" grid. At minimum 6 rows and the whole glyph column need a row-by-row audit before any further LA claim cites this file. This does **not** affect the sandbox (which used Unicode as primary) — but it does affect Phase 2/5 outputs.