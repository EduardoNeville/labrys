# Experiment protocol

Binding rules for any measurement in this repo. Each one exists because ignoring it cost
real time — the failures are named so nobody has to relearn them. Full narrative:
`data/analysis/ventris/oracle_repair_report.md`.

Run `uv run python pipeline/guards.py` before trusting any analysis output.

---

## 1. Pre-register the gate, in the output file, before running

Write the pass threshold, the trial count and the interpretation rule into the result file
*before* the first number is produced. Never adjust a threshold after seeing results.

*Precedent:* the Linear B sandbox gate (`lift > 1.5×`) was committed in
`languages/linear-b/data/analysis/ventris/ventris_report.md` before the run. The one
threshold that did change (the parser's unique-sign bound) was corrected before any oracle
run, and the correction is documented in the code that enforces it.

## 2. Every measurement gets a null control

Two baselines, not one:

- **uniform chance** (`1/|candidates|`), and
- **majority class** (predict the most frequent label) — because a channel that only ever
  predicts the common class carries no per-sign information.

For partner/link sets, a **permutation control** (random sets of the same size, drawn from the
same category) is mandatory.

*Precedent:* the "Kober identifies the series, 6.4×" claim was an artifact of a majority
baseline polluted by the junk label `"?"`. With a clean baseline the same channel read 1.03×.
Under a permutation control the paradigm-alternation channel was *beaten by its own control*.

## 3. Attribute every diff — never assume it

When an output changes after a code change, measure *why*: reconstruct the pre-change output
(`git show HEAD:<path>`) and compare field by field. Ask of each change: fix, or drift?

*Precedent:* four regenerated products differ from their committed versions; a column-wise
comparison proved they were **drift** (inputs moved on), not caused by the defect fixes. The
clincher: a profile file newer than the artefact derived from it.

## 4. One canonical implementation per concept

Duplicated logic is a defect class, not a convenience. If two modules need the same function,
one imports it from the other.

*Precedent:* `vowel_of` existed in four places and the four copies had drifted; all now
delegate to `pipeline/phonetics.py`, and a guard fails if a second definition appears.

## 5. Leak audit on every oracle path

Before trusting any recovery/accuracy number, prove the answer is unreachable:

- from the data tables (`SELECT DISTINCT transliteration` → all NULL), and
- from every scoring channel at run time.

*Precedent:* two leaks, in opposite directions. Anchor words constrained hidden signs to
their own true values (inflating recovery: 0.00 → 1.28×). The chance baseline used the full
anchor set (inflating chance by 2.3×, making the method look worse than the machinery
warranted).

## 6. Write the kill criteria first

State, before running, what result would make you abandon the approach. A negative result is
only useful if it was possible to get one.

*Precedent:* conditions (a)–(c) and the closure document state explicitly which outcome ends
the method search. Without that, four failed operationalizations would each have been
"promising, needs tuning".

## 7. Never let a plausible number outrun its control

A number with the right shape is the most dangerous artefact in this repo. Every headline
figure must be reproducible from a script in `pipeline/` with its control in the same run.

*Precedent:* 1.28×, the "1.8× Kober signal", "6.4× series identification" — all had the right
shape, all were artifacts of a defect or a bad baseline.

---

## Checklist for a new claim

1. Gate written down first, threshold and interpretation included.
2. Control(s) computed in the same run, same data, same candidate space.
3. Leak audit passes on the path used.
4. Diff attribution done if any input or output moved.
5. Result recorded in `data/analysis/ventris/verification_audit.md`; retractions are
   first-class entries, not silent edits.
6. `uv run python pipeline/guards.py` green.