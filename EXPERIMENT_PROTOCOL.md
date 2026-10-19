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

## 8. Retire code the way you retire a claim

Added 2026-10-19, after a code audit found retracted ideas still importable, ten modules still
reading a grid with 69 non-existent signs, and the project's most-cited artifact with no
generator. Full detail: `CODE_AUDIT.md`.

**8.1 A retraction is three actions, never one.**

1. move the code to `archive/` with a header naming the falsifying number;
2. fix every doc that cites its output — a banner, not a silent deletion, for historical files;
3. record it in `data/analysis/ventris/verification_audit.md`.

Deleting the file alone guarantees the idea returns, because the reasoning that produced it is
still plausible.

**8.2 Every canonical artifact gets a generator and a guard.** If a file cannot be re-derived
from committed inputs, it is a hand-copied number wearing a `.csv` extension. If it can be, the
check belongs in `pipeline/guards.py` so a hand-edit fails loudly.

**8.3 Every guard must pass on a fresh clone.** "Skipped — run `tools/bootstrap.sh`" is
acceptable; "FAILED because a gitignored file is absent" teaches people to ignore the suite.

**8.4 Freeze concluded avenues.** A negative result is a result. The only permitted change to a
RECORD module is a repaired import. Re-tuning one is how a retracted positive comes back.

**8.5 Name the instrument in every claim.** This repo currently contains three different
"confirmed sign" counts on two grids, one of which is 50% phantom signs. A count without its
instrument is not a number, it is a rumour.

**8.6 Purge phantoms at the source.** The purge was applied to one grid and not the other, so
five CONFIRM decisions survived on signs with no codepoint and zero occurrences. When a filter is
introduced, grep every derived file for the thing it filters.

**8.7 A dependency only unvalidated code needs is not a default dependency.** torch was a 2 GB
CUDA wheel behind code that has produced zero live conclusions; it is now the optional `ml` extra.

**8.8 Working files are not findings.** A subagent's `JOURNAL.md`/`MEMORY.md` at the repo root
read like project documentation. Scratch goes in `archive/agent_scratch/`, findings go in
`data/analysis/` **with a control**.

**8.9 When the audit and a summary disagree, the summary is wrong until proven otherwise.**

---

## Checklist for a new claim

1. Gate written down first, threshold and interpretation included.
2. Control(s) computed in the same run, same data, same candidate space.
3. Leak audit passes on the path used.
4. Diff attribution done if any input or output moved.
5. Result recorded in `data/analysis/ventris/verification_audit.md`; retractions are
   first-class entries, not silent edits.
6. `uv run python pipeline/guards.py` green (15/15, `tools/bootstrap.sh` on a fresh clone).
7. If the claim rests on a file, that file has a generator (§8.2) and the claim names the
   instrument it was measured on (§8.5).