# An audit of every positive this project has produced, and the one that survived

**Date:** 2026-10-01 · **Scope:** the Linear A project's positive claims, 2026-08 … 2026-10-01 ·
**Companion files:** `EXPERIMENT_PROTOCOL.md` (the rules), `data/analysis/ventris/verification_audit.md`
(the case records), `METHOD_CLOSURE_PAPER.md` (the Linear B test bed).

---

## 1. Why this note exists

This project has produced **thirteen** positive results. Twelve of them died on inspection. One
survived, and it is the least quantitative of the thirteen.

That ratio is not a failure of effort — it is the project's actual output. Every retraction came
from a null that was matched to the claim *after* the claim was made, and the failure modes are few
enough to name, which makes them avoidable in a way that "be careful" never is. This note collects
them as a taxonomy with the cases attached, then states the decision procedure that follows.

The useful framing is not "we were wrong thirteen times". It is: **a positive is a hypothesis about
a null.** Each of these died because the null was not the one the claim implicitly assumed.

---

## 2. The five ways a positive died here

### Mode 1 — the null was measured on a contaminated population

| case | what was claimed | what killed it |
| anchor-word leak | 1.28× oracle lift (LB sandbox) | hidden signs were still constrained to their own true values by hardcoded anchor words (`pa-i-to`, `i-da`). With the leak fixed: **0.00×** |
| Kober channel 6.4–8.4× | the frame channel identifies consonant series | "chance" was computed over a label set polluted by an unmapped-value sentinel, so the majority class was a **junk label** predicted at ~0% accuracy. Clean majority baseline: **1.03×** |
| Linear A oracle 0.6× | a weak but real signal | measured by leaky machinery; re-run with the leak fixed: **0.00×** |

The lesson is the one the paper's §5 states: *uniform chance is the wrong null for a channel that
can only emit the common class.* Every one of these three was a baseline problem wearing the costume
of a signal.

### Mode 2 — the null did not share the measurement's unit, membership, or selection

| case | the mismatch |
| commodity enrichment (retracted 2026-10-01 in cross-site test, see Mode 4) | the hypergeometric ran over **adjacent slots** from ±3-sign windows. Windows overlap inside a text and span most of a short tablet, so the effective sample is **documents**: at document level the same claim is stronger (p 1.16e-04 → **2.69e-11**), and the original number was diluted by a unit that does not exist |
| my own first permutation control (2026-10-01) | its "truth" was drawn **from the candidate list**, so it had 100% membership while the real truth is a candidate only ~40–54% of the time. The null was solving an easier problem than the measurement, and its 0.25–0.52× "win" was partly that asymmetry |
| the weight-simplex sweep (2026-10-01) | a *maximum* over 1,771 vectors needs a permuted maximum as its null, not 1/|C|: the identical search on a permuted truth reaches 2.8%, so "best of 1,771" is a number that outruns its evidence by construction |
| `in_argmax` labelled "top-1" | `aggregator_bakeoff.py`'s "67 / 47 / 59 / 100%" figures are **ties allowed** — they are argmax-set size. Three reproduce as that; the kober channel's 100% does not (8.9%) |

Three distinct properties to match: **unit** (what is one observation?), **membership** (could the
answer have been present at all?), **selection** (was this case chosen by an earlier test on the same
data?). A null that differs on any of them is measuring something else.

### Mode 3 — the pool was one archive pretending to be a corpus

| case | the confound |
| `i-da` toponym | the four sanctuary matches are all `Za`-series libation texts, a genre that is 33.7% at peak sanctuaries against 2.3% for the corpus. Stratifying by genre moved p from 0.00086 to **0.38** |
| `pa-i-to` (Phaistos) | 3 distinct matches of 78 at Phaistos against 3.3 expected — a truncation artifact, not a match |
| A 301 "entry-opening marker" | 229 of 231 occurrences are initial at **Haghia Triada Portico 11 and Room 13** (99.1%), and 9 of 43 (20.9%) everywhere else. `229` is both the index-0 count and the Portico count because they are the *same occurrences* |
| AB 85 "word divider" | the 508-occurrence "never medial" profile belonged to the **logogram A 301**; AB 85 itself has 8 occurrences and is medial-dominant |

**The corpus property that explains this mode**, and which nobody had written down:
Haghia Triada *Portico 11 and Room 13* is **863 of 1,719 inscriptions (50.2%)** of the whole Linear A
corpus, with its own tablet format. Half the corpus is one room, so a pooled positional or
distributional statistic is mostly a statistic about that room. Stratification must reach **room**
level, not site level: two rooms of the same site disagree about A 301 (Portico 229/231 initial,
Villa Magazine 0/3).

### Mode 4 — the claim was never tested on data it had not already seen

| case | the replication |
| commodity sign↔class enrichment (the project's last surviving positive) | selected on all sites, then re-tested on the same documents. Selecting on Haghia Triada and testing on **Khania** replicates **2 of 67 pairs — and both are logogram↔own-class tautologies** (A 303↔LIVESTOCK, A 301↔PERSONNEL). Every *syllabogram* association fails (AB 30 p=0.044, AB 81 p=0.27, AB 31 p=0.42). My pre-registered prediction — "the three strongest replicate" — was **wrong** |

The design detail that makes this test worth running: the selection set contains its own **positive
control**. A logogram must co-occur with the class that defines it, and those pairs replicate as they
must — so the pipeline is demonstrably sensitive to a real association across sites while every
inferred one fails. Without that control, "2 of 67 replicated" is ambiguous.

### Mode 5 — a plausible number outran this specific control

| case | the tell |
| AB 82↔LIVESTOCK (Bonferroni, 70×) | both co-occurrences come from **one inscription (PH10)**, and the "commodity" came from a HIDE ligature encoding — circular |
| fraction values | 16 of 29 entries are derived by complement-fitting, and the file is then cited as its own evidence |
| §4.4 paradigm A "9/9 correct" | its own permutation control reaches 73.8%, because same-series partner vowels cluster. Reported at n=9; on the day of writing, the same shape recurred at n=6 (Thera 5/6 against a 21.4% control) |
| "78 anchors" | a transcription count, cited as a property of the corpus |
| Tyrsenian "best structural fit" | best WALS profile, **0** Swadesh matches at p=1.0 — a structural resemblance claimed with no lexical support |
| "diachronic prior" | positional behaviour is not conserved across periods (AB 49: 67% → 7%) |

Two of these are the project's own author's, and two are mine from the last week. That is the point:
the modes are not a critique of earlier work, they are the shape of the trap.

---

## 3. The one that lived

**The libation formula.** Recorded as "structurally real but phonetically inert", and it is the only
positive claim that survives every test this note describes:

- **counts reproduce exactly** — `ja-sa-sa-ra-me` 9, `u-na-ka-na-si` 6, `si-ru-te` 7, opening
  A-TA-I-*301-WA-JA 11 (matched over sign rows with a non-null Bennett id; naive matching over the raw
  sequence silently drops divider and lacuna rows)
- **position**: the opening is at index 0 in **11 of 11**
- **order**: in all **9** texts carrying two or more of the five formula words, they appear in the
  documented slot order — 9 of 9, no exceptions
- **it travels**: **5 sites** (Iouktas, Platanos, Psykhro, Troullos, Palaikastro) for the fixed
  five-sign sequence, so unlike the commodity associations it is not one archive's convention

What it does **not** give: translations (the source's tentative readings), phonetic values (Linear B
transfer), or any new value. It is a structural anchor and a promising sub-corpus, not a decipherment.

**And the one negative that survived everything**: distributional methods are closed on the Linear B
test bed. Not because eight aggregators failed, but because **none of 1,771 weight vectors over the
four channels recovers even one hidden value** — and zero again when the answer is guaranteed to be in
the candidate list. Stratified by findspot, all four operationalizations in the closure paper hold
(§4.1: 0.46× / 0.45× / 0.00× against a pooled 0.23×; §4.2: exact 0.0% in every stratum).

The pattern across both corpora: **what generalises is formula and genre; what does not is
distribution.** That conclusion was reached independently on Linear A (replication) and Linear B
(weight-simplex sweep), which is the most credible thing this project has.

---

## 4. The decision procedure that follows

Ordered by how often its absence caused one of the cases above.

1. **Pre-register the gate and the prediction, before the run** — including the prediction you expect
   to fail. Record the failure. (My wrong prediction is in the record; the alternative is not knowing
   whether a test could have failed.)
2. **Compute the null in the same run, on the same draws.** A null from a previous run, another
   corpus, or a different sample is not a null.
3. **Match the null on three properties:** unit (documents, not overlapping windows), membership
   (could the answer have been present?), and selection (was this chosen by an earlier test on the
   same data?). For a maximum over N tries, permute the objective and take its maximum.
4. **Report the input size next to every number.** The most interesting-looking figure in this
   week's audit (1.31×, INCONCLUSIVE) came from a script scoring an **empty corpus**; it was caught
   only because the inscription count printed beside it was 0.
5. **Attribute every hit.** Which sign, which draw, and was it a unique result or a tie resolved by
   list order? The one Linear B value ever "recovered" after eight repairs was a tie.
6. **Stratify by archive down to room level, and report across strata.** A pooled figure answers a
   question about the largest room. Two rooms of one site can disagree.
7. **Replicate on held-out data *and* a held-out stratum**, with a positive control that must pass.
   Both are needed: this week's claim passed 20,000 site-stratified permutations and failed the
   cross-site test.
8. **Prefer the exhaustive search to the example** when the cache makes it free. Eight hand-picked
   aggregators said "the ones we tried failed"; 1,771 vectors said "the space fails".
9. **Name metrics so they cannot be confused.** Ties-allowed rank-1 is not unique identification,
   and a class is not a value.
10. **Write the negatives down with the same care as the positives.** The audit trail is this
    project's most substantial output; the negatives are what make the surviving claim credible.

---

## 5. What this cost, and what it bought

Thirteen positives: twelve retracted, one (the libation formula's structure) intact, one negative
about method (distribution is closed) that is now stronger than any of the retracted positives ever
were. Two instruments came out of the exercise and are reusable: `archive_stratification.py` (per
archive, for any sign) and the `stratify_*_by_findspot.py` pair (per stratum, for the oracle and the
instrument, with per-stratum Kober graphs so constraints cannot leak across sites).

The honest summary for anyone planning to build on this corpus: **the corpus cannot be talked into
giving up values, and the reason is now measured rather than argued.** Whatever produces a
decipherment will be evidence from outside it — a bilingual, an independent script side, or a longer
non-administrative text — and the apparatus that will judge that evidence is the one this note
documents.
