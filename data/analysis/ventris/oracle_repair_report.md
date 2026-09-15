# Oracle repair report — all defects fixed, sandbox re-run

**Date:** 2026-09-15 · Follows `oracle_retrace_findings.md` and `lb_sandbox_findings.md`.

Challenge was: 0/160 recovery on a deciphered script with perfect anchors must be a bug.
It was — **six** of them. All are fixed and the sandbox re-run. The 0.00× survives the
repairs, and now for a reason that is measured rather than assumed.

---

## Defects found and fixed

| # | Where | Defect | Effect | Status |
|---|---|---|---|---|
| 1 | `pipeline/lb_oracle.py` (mine) | passed the 15 *unnamed* signs as the detector's `uncertain` set; `triple_detection.py:375` keeps only triples with ≥2 UNCERTAIN members → collapsed the link graph to 101 triples in which 3 signs had a valued partner | Kober channel dead (constant score) | fixed: pass all observed signs → 60,155 triples, 76 linked signs |
| 2 | `complete.py:oracle_test` | chance baseline derived from `get_candidates(b)` with the **full** anchor set, so a hidden sign's own value tightened its own candidate list | inflated chance (LB 0.0683, LA 0.0841) | fixed: per-trial effective anchors → LB 0.0208, LA 0.0373 |
| 3 | `complete.py:_load_kober` | added every triple pair to *both* C- and V-graphs, deleting the consonant/vowel distinction that is Kober's method | constraints become one undifferentiated clique | fixed: consume the file's actual semantics (s1↔s2, s1↔s3 → C; s2↔s3, s1↔s3 → V) |
| 4 | `complete.py:CONS_SERIES_MAP` | **18 of 74 Linear B values missing**, incl. `no`, `po`, `pe` (1,707 / 1,132 / 1,050 occurrences) plus `qo, a2, a3, au, dwe, dwo, nwa, pu2, pte, ra2, ra3, ro2, ta2, twe, two` | those signs never earned a series vote; the Kober term skipped them (`if series == "?" ... continue`) | fixed: map completed (57 → 75 entries) |
| 5 | `complete.py:vowel_of` | returned `"?"` for every subscripted value (`ra2, ro2, ta2, pu2, a2, a3, …`) | those signs skipped in vowel constraints and Kober scoring | fixed: strip subscript digits (incl. Unicode ₀–₉) before reading the vowel |
| 6 | my measurement scripts | majority baseline was computed over a Counter that contained the junk label `"?"`, so the majority "class" was *unmapped*, and predicting it scored ~0% | inflated every ratio I reported (the bogus "6.4× / 8.4×") | fixed: majority computed over real labels only; unmapped targets excluded and counted |

Defects 4 and 5 are code-path-shared with Linear A — `CONS_SERIES_MAP` feeds the shipped
`kober_score` and candidate generation for both languages — but the **measured Linear A
impact is nil**: the LA grid has 52 distinct values, none of which is subscripted and none of
which falls in the 18 missing map entries, and the LA oracle returns identical results with
the legacy and fixed maps (0.0000 vs chance 0.0373 both ways). These two defects affected
Linear B, where `no`/`po`/`pe` are frequent real signs.

## Post-repair measurements

### The oracle, end to end (all fixes in place)

| corpus | recovery | chance | lift |
|---|---|---|---|
| Linear B (best case: real Greek, 73 perfect anchors, 40k signs) | 0.0000 | 0.0208 | **0.00×** |
| Linear A (default grid, fixed machinery) | 0.0000 | 0.0373 | **0.00×** |

### An independent, from-scratch per-sign instrument

`pipeline/repaired_instrument.py` scores each hidden sign on its own: profile-cosine against
the context profile of each candidate-bearing anchor sign, plus weighted series and vowel
votes. No global scalar, no greedy search, no shared machinery with the shipped scorer.

| metric | instrument | majority baseline | ratio |
|---|---|---|---|
| LB — consonant series | 23.1% | 22.5% | **1.03×** |
| LB — vowel | 16.9% | 16.9% | **1.00×** |
| LB — exact value | **0.0%** | — | chance 1.9% → **0.00×** |
| LA — consonant series | 25.0% | 24.4% | 1.03× |
| LA — vowel | 15.0% | 15.0% | 1.00× |
| LA — exact value | 0.6% | — | chance 4.2% → **0.15×** |

The rebuilt instrument performs **at the majority-class baseline**. It is not an
implementation failure: it is a measurement of how much per-sign information the evidence
carries.

### The pairwise premise, tested directly (LB corpus, all values known)

Does sharing a frame sign predict agreement of consonant or vowel?

| relation | agreement | chance | ratio |
|---|---|---|---|
| share FOLLOWING sign → same consonant | 0.131 | 0.150 | 0.87× |
| share FOLLOWING sign → same vowel | 0.201 | 0.206 | 0.98× |
| share PRECEDING sign → same consonant | 0.137 | 0.150 | 0.92× |
| share PRECEDING sign → same vowel | 0.197 | 0.206 | 0.96× |

The frame-link relation is **empty at the pairwise level** on the best-case corpus, n ≈ 55k
pairs per relation. Whatever weak aggregate signal appeared earlier was a frequency artifact
of majority-class prediction.

## Verdict

**The zero is real, and it is not a bug.** After repairing six defects — including one that
had disabled the constraint stage entirely, one that had deleted the method's central
distinction, and two that had silently excluded 18 of 74 signs — the method still recovers
nothing, and an independently built per-sign instrument lands exactly on the majority
baseline for both the consonant series and the vowel.

The corrected statement about the method family:

> On Linear B — a deciphered script, real Greek, 73 correct anchors, 40,038 sign tokens, 4×
> the Linear A corpus, editor-supplied word division — the frame-link (Kober) relation
> carries no pairwise information, and no per-sign channel (series vote, vowel vote, context
> profile) exceeds majority-class prediction. Exact-value recovery is 0.00× chance. The same
> instrument on Linear A gives 0.15× with a 0.6% hit rate against a 4.2% baseline.

**What this does and does not say.** It says the *Ventris-endgame operationalisation* — frame
links for series, weighted votes for vowels, corpus-level plausibility scoring — cannot
recover phonetic values, and that this is now established on the easiest possible instance
rather than inferred from Linear A's difficulty. It does **not** say Kober's insight is
wrong in principle: what is falsified is this operationalisation of it, on this corpus. A
fair test of the idea itself would need a different operationalisation (e.g. paradigm-slot
alignment rather than frame co-occurrence).

## Consequence for the project

- Phase 10c's "no signal, no optimizer can help" **stands** — and is now measured with
  correct semantics, complete constants and clean baselines, on the best case.
- The historical 0.6× is retired (leak-contaminated); the LA figure is 0.00× against a
  0.0373 chance baseline.
- The Linear A 44/138 phonetic grid, the refined grid, and any claim resting on the shipped
  scorer's constraints should be re-derived before further use, because defects 4–5 changed
  which signs could participate in those constraints at all.
- `verification_audit.md` needs entries for defects 2–5.

## Artifacts

| File | Role |
|---|---|
| `pipeline/oracle_diagnose.py` | failure attribution: round-trip, candidate inclusion, per-term rank, stronger search |
| `pipeline/aggregator_bakeoff.py` | aggregator comparison on a frozen component cache |
| `pipeline/frame_link_test.py` | frame-link channel measurement vs chance |
| `pipeline/repaired_instrument.py` | from-scratch per-sign instrument + majority baselines |
| `pipeline/local_vowel_test.py`, `pipeline/vowel_recovery_test.py`, `pipeline/series_filtered_oracle.py` | vowel-recovery probes (superseded, kept for the audit trail) |