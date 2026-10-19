# Archive — code that must not be run or extended

This directory holds code whose **premise was falsified** or which was a **wrong turn**.
It is kept, not deleted, for two reasons: the audit trail, and so the mistake is visible
rather than quietly removable.

Nothing here is importable from `pipeline/`. Nothing here should be imported, cited as a
result, or used to produce a new number. Each file carries a header saying which claim it
rested on and what replaced it. The authoritative audit is `../CODE_AUDIT.md`.

**The rule:** a retraction moves the code here *and* records the retraction in
`data/analysis/ventris/verification_audit.md`. An archive entry without an audit entry is
just a deleted file with a story.

---

## `retracted/` — the premise was falsified

| file | was | why it is here |
| `diachronic.py` | Phase 11 Avenue 6: MM-attested signs are 2× more likely CONFIRMED (p=0.0003) | The corpus correction moved it to **p=0.1748, 1.1×** — no effect. A time-based prior on a corpus that is 76% one destruction horizon was never identifiable. |
| `diachronic_prior.py` | Avenue 6b: apply that prior to the grid | Depends entirely on `diachronic.py`; same falsification. |
| `libation_segmentation.py` | Avenue 7b: segment the libation formula into words, with `AB 85` in slot A | The `AB 85` in the formula is the **retracted attribution**: those 508 occurrences belong to the logogram **A 301**. The real formula was re-derived from the corrected corpus in `data/analysis/ventris/libation_recovered.md`, which is canonical. |

## `wrong_turns/gpu/` — search over an objective with no signal

| file | what it did |
| `gpu_scoring.py` | Batched the Ventris grammatical scorer on GPU |
| `gpu_mcmc.py` | Ran 1,024 parallel MCMC chains over grid completions |

Both are competent code. Both optimize a scorer that the oracle measured at **0.00× chance**
(0/160), and the exhaustive weight sweep showed **0 of 1,771 weight vectors recover a value**.
`method_closure.md` states the conclusion these files ignored: *"No optimizer (beam,
annealing, Optuna) can help an objective with no gradient."* Faster search over a flat surface
is not a research programme. They also default to the legacy 138-sign grid.

**The lesson is the useful part:** "this would be fast on a GPU" is not evidence that the
thing being optimized is real. Check the gate first (`pipeline/guards.py`, oracle lift), then
optimize.

## `wrong_turns/hardware/` — not research

`gpu-fixup.sh` and `gpu-stress-test.py` are machine operations for a Tesla P40 (PCIe ASPM,
thermals, sustained matmul). They belong to an environment setup, not to a corpus project,
and they were never imported by anything. Kept here only so the removal is explicit.

## `agent_scratch/` — subagent working files

`JOURNAL.md`, `MEMORY.md`, `REPORT.md`, `TODO.md` were the scratch trail of a single
subagent task (the Egyptian bridge). Their durable content is already in
`data/analysis/egyptian_bridge/egyptian_report.md` and
`data/analysis/synthesis/phase_summary_10_11.md`. They sat at the repository root and read
like project documentation, which is exactly the failure mode this archive prevents: **a
working file must not be mistaken for a finding.** The Egyptian bridge itself is a concluded
negative (312 consonant-class matches, null-model ratios 1.6–6.4× — consistent with chance).
