# Method closure: four operationalizations of the Kober/Ventris method, all measured empty

**Date:** 2026-09-15 · **Best-case corpus throughout:** Linear B — deciphered, real Greek,
73 correct anchors, 40,038 sign tokens, editor-supplied word division, 4× Linear A's size.

This document closes the question "can the project's core method recover phonetic values
from a syllabary corpus?" on the easiest instance available. Every measurement carries a
null control; every ratio is against the right baseline (uniform chance *and* majority
class), per `oracle_repair_report.md` and the Phase 12 audit addendum.

## The four operationalizations, and what each measures

| # | Operationalization | Measurement | Result |
|---|---|---|---|
| 1 | **Shipped scorer end to end** (`complete.py`, hide-N-recover) | oracle recovery vs chance | **0.00×** (0/160), chance 0.0208 |
| 2 | **From-scratch per-sign instrument** (profile-cosine + weighted votes; no shared code) | exact value / series / vowel vs majority | exact **0.00×**; series 1.03×; vowel 1.00× |
| 3 | **Frame sharing** — signs sharing a following or preceding sign (Kober's recorded relation) | agreement of consonant / vowel vs chance, ~55k pairs per relation | 0.87× / 0.98× (following), 0.92× / 0.96× (preceding) — **at or below chance** |
| 4 | **Paradigm-slot alternation** — (A) identical left *and* right neighbour, ≥2 slots; (B) strict minimal pairs, word types differing in exactly one position | partners share the series; eliminative vowel complement | (A) series **13.9%** vs 27.4% majority; complement unique 12.5% vs control 19.4% — **beaten by its own control**<br>(B) series **14.3%**; complement unique 19.4% vs control 18.5%, correct 78.6% vs control 80.0% — **identical to control** |

Operationalization 4 is the one Ventris actually used, and the strictest form of it: a sign
alternating with `da/de/di/do` in the same slot should be `du`. It is indistinguishable from
random partner sets drawn from the sign's own series.

## Why the single apparent positive is not one

Operationalization 4(A) produced 9/9 correct vowel complements. That number is:

- on **9 signs** (12.5% of signs with partners) — the uniqueness rate is *lower* than the
  control's 19.4%, so the eliminative step fires less often than chance;
- matched or beaten by the permutation control, which gets 73.8–80.0% correct by accident,
  because same-series partner vowels cluster.

Under operationalization 4(B) the signal and the control converge to the same numbers.

## Verdict

**No operationalization of the frame/paradigm relation recovers phonetic values from a
deciphered syllabary corpus, and none exceeds majority-class prediction for the consonant
series or the vowel.** The corpus's evidence channels are not merely weak — they are
indistinguishable from random with respect to phonetic identity.

Two consequences, kept separate:

1. **About the project's methods:** the Ventris-endgame family (frame links → series,
  weighted votes → vowels, corpus-level plausibility scoring, greedy/coordinate search) is
  closed. Continuing to build within it is not a research programme, it is a bug hunt.
2. **About Linear A:** nothing here says Linear A *cannot* be deciphered, and nothing here
  measures Minoan. It says the information needed is not present in the Linear A corpus plus
  Linear B transfer — which is what the oracle's flat profile has been saying since Phase
  10c, now measured properly and on the best case.

## What would falsify this closure

Written down so the closure can be attacked rather than believed:

- A corpus with **semantic** anchors (a bilingual, or LA↔CM correspondence with known
  values): operationalizations 1–4 all reduce to *distributional* evidence, which is exactly
  what failed. Meaning-bearing anchors are a different evidence class and untested here.
- A **longer or non-administrative** text: all four tests use administrative lists, where
  word-slots vary lexically rather than paradigmatically. The `KN Zg 57/58` scepter (119
  signs, ritual) is the first such text; the probe's test B should be re-run on it.
- **Cross-script anchoring**: if CM or Eteocretan yields values, the chains in
  `MULTI_LANGUAGE_DECYPHR_PLAN.md` become testable, and the sandbox is the acceptance test.

## Reusable assets (do not rebuild)

| Asset | Path |
|---|---|
| LB corpus + anonymized DB | `languages/linear-b/` |
| Answer key (the only file with LB values) | `languages/linear-b/answer_key.csv` |
| Oracle + leak guard | `pipeline/lb_oracle.py`, `pipeline/lb_ingest.py:assert_no_leak` |
| Failure attribution harness | `pipeline/oracle_diagnose.py`, `pipeline/aggregator_bakeoff.py` |
| Independent instrument + baselines | `pipeline/repaired_instrument.py` |
| Channel tests | `pipeline/frame_link_test.py`, `pipeline/paradigm_slot_probe.py` |
| Canonical phonetic logic + selfcheck | `pipeline/phonetics.py` |