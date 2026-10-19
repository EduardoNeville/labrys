"""ARCHIVED — WRONG TURN. Do not run, import, or extend.

Optimizes the Ventris grammatical scorer, which the oracle measured at 0.00×
chance (0/160) and which the exhaustive weight sweep failed to rescue
(0 of 1,771 vectors recover one value). `method_closure.md`: no optimizer can
help an objective with no gradient. It also defaults to the legacy 138-sign
grid. See ../../README.md and ../../../CODE_AUDIT.md.

Original docstring follows.

GPU-accelerated MCMC for Ventris grid completion.

Runs 1,024 parallel Markov Chain Monte Carlo chains on GPU, exploring
grid completions for the boundary-flexible cluster (12 most constrained
UNCERTAIN signs). Features:
  - Parallel chain initialization and mutation
  - GPU-batched grammatical scoring
  - Simulated annealing with temperature schedule
  - Per-sign consensus extraction from converged chains
  - Iterative tightening: accept converged values, re-run
"""

from __future__ import annotations

import csv
import logging
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch

from pipeline.ventris.gpu_scoring import (
    GPUCorpusCache,
    batch_score_completions,
    phoneme_to_idx,
    phoneme_idx_to_series,
    phoneme_idx_to_vowel,
    _NUM_PHONEMES,
    CONS_SERIES,
    VOWEL_COLS,
)

logger = logging.getLogger(__name__)

__all__ = ["VentrisMCMC", "run_mcmc_decipher"]


# ═══════════════════════════════════════════════════════════════════════════════
# candidate loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_candidates(
    grid_path: str = "data/analysis/bootstrapping/expanded_grid.csv",
    freq_path: str = "data/analysis/frequency_constraints/constrained_candidates.csv",
    cluster_filter: Optional[List[str]] = None,
) -> Tuple[Dict[str, torch.Tensor], List[str], Dict[str, str]]:
    """Load candidate phoneme values for target UNCERTAIN signs.

    Returns:
        sign_to_candidates: sign → (K,) tensor of phoneme indices
        target_signs: ordered list of target signs
        current_values: sign → current conventional value
    """
    # Load grid
    grid = {}
    with open(grid_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            grid[row["bennett_id"]] = row

    # Load frequency constraints
    freq = defaultdict(lambda: {"series": set(), "vowels": set()})
    with open(freq_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row.get("bennett_id", "").strip()
            if row.get("plausible", "").strip().lower() != "true":
                continue
            series = row.get("consonant_class", "").strip()
            vowel = row.get("vowel", "").strip()
            if series and vowel:
                freq[bid]["series"].add(series)
                freq[bid]["vowels"].add(vowel)

    # Identify target signs: UNCERTAIN, with frequency constraints
    target_signs = []
    current_values = {}
    for bid, g in grid.items():
        dec = g.get("decision", "UNCERTAIN").strip()
        val = g.get("refined_value", g.get("conventional_value", "?"))
        if dec == "UNCERTAIN" or (val == "?"):
            # Only include signs with frequency constraints
            if bid in freq and freq[bid]["series"] and freq[bid]["vowels"]:
                if cluster_filter is None or bid in cluster_filter:
                    target_signs.append(bid)
                    current_values[bid] = val

    # Sort for deterministic ordering
    target_signs = sorted(target_signs)

    # Build candidate lists
    sign_to_candidates = {}
    for bid in target_signs:
        series_set = freq[bid]["series"]
        vowel_set = freq[bid]["vowels"]
        candidates = []

        for v in vowel_set:
            if "VOWEL" in series_set:
                candidates.append(phoneme_to_idx(v))
            if "LABIAL" in series_set:
                for c in "pm":
                    candidates.append(phoneme_to_idx(f"{c}{v}"))
            if "DENTAL" in series_set:
                for c in "tdn":
                    candidates.append(phoneme_to_idx(f"{c}{v}"))
            if "VELAR" in series_set:
                for c in "kq":
                    candidates.append(phoneme_to_idx(f"{c}{v}"))
            if "SIBILANT" in series_set:
                for c in "sz":
                    candidates.append(phoneme_to_idx(f"{c}{v}"))
            if "LIQUID" in series_set:
                for c in "rl":
                    candidates.append(phoneme_to_idx(f"{c}{v}"))
            if "PALATAL" in series_set:
                candidates.append(phoneme_to_idx(f"j{v}"))
            if "SEMIVOWEL" in series_set:
                candidates.append(phoneme_to_idx(f"w{v}"))

        if not candidates:
            # Fallback: all CV values
            for v in "aeiou":
                candidates.append(phoneme_to_idx(v))
                for c in "ptkmnslrzwjhqg":
                    candidates.append(phoneme_to_idx(f"{c}{v}"))

        candidates = sorted(set(candidates))
        sign_to_candidates[bid] = torch.tensor(candidates, dtype=torch.long)

    logger.info("Loaded %d target signs with candidates (avg %.1f/sign)",
                 len(target_signs),
                 sum(len(c) for c in sign_to_candidates.values()) / max(len(target_signs), 1))

    return sign_to_candidates, target_signs, current_values


# ═══════════════════════════════════════════════════════════════════════════════
# MCMC engine
# ═══════════════════════════════════════════════════════════════════════════════

class VentrisMCMC:
    """GPU-accelerated MCMC grid search.

    Runs B parallel chains, each maintaining a completion of S target signs.
    At each step, propose a random mutation, score the mutated completion
    on GPU, accept/reject via Metropolis-Hastings with annealing.
    """

    def __init__(
        self,
        db_path: str = "data/database/lineara_full.db",
        expanded_grid_path: str = "data/analysis/bootstrapping/expanded_grid.csv",
        freq_path: str = "data/analysis/frequency_constraints/constrained_candidates.csv",
        cluster_signs: Optional[List[str]] = None,
        num_chains: int = 1024,
        device: str = "cuda",
    ) -> None:
        self.device = device if torch.cuda.is_available() else "cpu"
        logger.info("VentrisMCMC on %s with %d chains", self.device, num_chains)

        self.num_chains = num_chains

        # Load candidates
        self.sign_to_candidates, self.target_signs, self.current_values = load_candidates(
            grid_path=expanded_grid_path,
            freq_path=freq_path,
            cluster_filter=cluster_signs,
        )
        self.S = len(self.target_signs)

        # Build GPU corpus cache
        self.cache = GPUCorpusCache(
            db_path=db_path,
            expanded_grid_path=expanded_grid_path,
            device=self.device,
        )
        self.baseline_entropy = self.cache.get_baseline_bigram_entropy()
        logger.info("Baseline bigram entropy: %.4f bits", self.baseline_entropy)

        # Max candidates per sign (for tensor padding)
        self.max_cands = max(len(c) for c in self.sign_to_candidates.values())
        logger.info("Max candidates per sign: %d", self.max_cands)

        # Initialize chains: random candidate indices
        # (num_chains, S) — each entry is an index into that sign's candidate list
        self.chains = torch.zeros(num_chains, self.S, dtype=torch.long, device=self.device)
        for i, bid in enumerate(self.target_signs):
            n = len(self.sign_to_candidates[bid])
            self.chains[:, i] = torch.randint(0, n, (num_chains,), device=self.device)

        # Current scores
        self.morph_scores = torch.zeros(num_chains, device=self.device)
        self.ent_scores = torch.zeros(num_chains, device=self.device)
        self.pref_scores = torch.zeros(num_chains, device=self.device)
        self.total_scores = torch.zeros(num_chains, device=self.device)

        # Score initial state
        self._score_all()

        # Tracking
        self.acceptance_history: List[float] = []
        self.best_score: float = float(self.total_scores.max().item())
        self.best_chain: int = int(self.total_scores.argmax().item())

    def _score_all(self) -> None:
        """Score all chains on GPU."""
        m, e, p = batch_score_completions(
            self.cache,
            self.sign_to_candidates,
            self.target_signs,
            self.chains,
            self.baseline_entropy,
            device=self.device,
        )
        self.morph_scores = m
        self.ent_scores = e
        self.pref_scores = p
        self.total_scores = 0.50 * m + 0.30 * e + 0.20 * p

    def step(
        self,
        temperature: float = 1.0,
        mutation_prob: float = 0.1,
    ) -> float:
        """One MCMC step: propose mutations, score, accept/reject.

        Returns acceptance rate.
        """
        B = self.num_chains
        S = self.S

        # Propose: for each chain, pick 1 random sign to mutate
        # Create mutated chains
        mut_chains = self.chains.clone()
        sign_to_mutate = torch.randint(0, S, (B,), device=self.device)

        for i in range(B):
            s = sign_to_mutate[i].item()
            n_cands = len(self.sign_to_candidates[self.target_signs[s]])
            if n_cands > 1:
                # Pick a different candidate
                current = mut_chains[i, s].item()
                new_val = random.randrange(n_cands)
                while new_val == current and n_cands > 1:
                    new_val = random.randrange(n_cands)
                mut_chains[i, s] = new_val

        # Score mutated chains
        m_mut, e_mut, p_mut = batch_score_completions(
            self.cache,
            self.sign_to_candidates,
            self.target_signs,
            mut_chains,
            self.baseline_entropy,
            device=self.device,
        )
        total_mut = 0.50 * m_mut + 0.30 * e_mut + 0.20 * p_mut

        # Metropolis-Hastings acceptance
        delta = total_mut - self.total_scores
        accept = False

        if temperature <= 0:
            accept_prob = (delta > 0).float()
        else:
            # Accept if better, or with exp(delta/T) if worse
            accept_prob = torch.where(
                delta > 0,
                torch.ones_like(delta),
                torch.exp(delta / temperature),
            )
            accept_prob = torch.clamp(accept_prob, 0.0, 1.0)

        rand_vals = torch.rand(B, device=self.device)
        accepted = rand_vals < accept_prob

        # Apply accepted mutations
        self.chains[accepted] = mut_chains[accepted]
        self.morph_scores[accepted] = m_mut[accepted]
        self.ent_scores[accepted] = e_mut[accepted]
        self.pref_scores[accepted] = p_mut[accepted]
        self.total_scores[accepted] = total_mut[accepted]

        acc_rate = float(accepted.float().mean().item())
        self.acceptance_history.append(acc_rate)

        # Track best
        current_best = float(self.total_scores.max().item())
        if current_best > self.best_score:
            self.best_score = current_best
            self.best_chain = int(self.total_scores.argmax().item())

        return acc_rate

    def run(
        self,
        iterations: int = 100000,
        initial_temp: float = 0.5,
        final_temp: float = 0.01,
        report_interval: int = 10000,
    ) -> Dict[str, Any]:
        """Run MCMC with annealing schedule.

        Returns consensus dict for each target sign.
        """
        logger.info("Starting MCMC: %d chains × %d iterations", self.num_chains, iterations)

        for it in range(iterations):
            # Annealing: linearly decrease temperature
            progress = it / max(iterations - 1, 1)
            temp = initial_temp * (1.0 - progress) + final_temp * progress

            acc_rate = self.step(temperature=temp)

            if (it + 1) % report_interval == 0:
                logger.info(
                    "Iter %d/%d: temp=%.4f accept=%.3f best=%.4f",
                    it + 1, iterations, temp, acc_rate, self.best_score,
                )

        # Extract per-sign consensus from final state
        consensus = self.get_consensus()

        logger.info("MCMC complete. Best score: %.4f", self.best_score)
        for bid in sorted(consensus.keys()):
            top_val, top_pct = consensus[bid]
            if top_pct >= 0.60:
                logger.info("  %s → %s (%.0f%% agreement)", bid, top_val, top_pct * 100)

        return consensus

    def get_consensus(self) -> Dict[str, Tuple[str, float]]:
        """Extract per-sign consensus from converged chain states.

        Returns {bennett_id: (most_common_phoneme_value, fraction_agreement)}
        """
        consensus = {}
        for i, bid in enumerate(self.target_signs):
            cands = self.sign_to_candidates[bid]
            chain_vals = self.chains[:, i]  # (B,)
            # Convert candidate indices → phoneme indices
            phoneme_indices = cands[chain_vals.cpu().long()]  # (B,)
            # Count
            counts: dict = {}
            for p in phoneme_indices.tolist():
                counts[p] = counts.get(p, 0) + 1
            # Get top
            top = max(counts, key=counts.get)
            top_pct = counts[top] / self.num_chains
            # Convert phoneme index back to value string
            from pipeline.ventris.gpu_scoring import _ALL_VALUES
            top_val = _ALL_VALUES[top] if top < len(_ALL_VALUES) else "?"
            consensus[bid] = (top_val, top_pct)

        return consensus

    def get_chain_states(self) -> Dict[str, Dict[str, float]]:
        """Return full distribution for each target sign."""
        distributions = {}
        for i, bid in enumerate(self.target_signs):
            cands = self.sign_to_candidates[bid]
            chain_vals = self.chains[:, i]
            phoneme_indices = cands[chain_vals.cpu().long()]
            counts: dict = {}
            from pipeline.ventris.gpu_scoring import _ALL_VALUES
            for p in phoneme_indices.tolist():
                val = _ALL_VALUES[p] if p < len(_ALL_VALUES) else "?"
                counts[val] = counts.get(val, 0) + 1
            # Convert to fractions
            distributions[bid] = {v: c / self.num_chains for v, c in counts.items()}
        return distributions


# ═══════════════════════════════════════════════════════════════════════════════
# iterative tightening harness
# ═══════════════════════════════════════════════════════════════════════════════

def run_mcmc_decipher(
    db_path: str = "data/database/lineara_full.db",
    expanded_grid_path: str = "data/analysis/bootstrapping/expanded_grid.csv",
    freq_path: str = "data/analysis/frequency_constraints/constrained_candidates.csv",
    output_dir: str = "data/analysis/ventris",
    cluster_signs: Optional[List[str]] = None,
    num_chains: int = 1024,
    iterations: int = 100000,
    agreement_threshold: float = 0.70,
    max_tightening_rounds: int = 5,
) -> Dict[str, Any]:
    """Run MCMC with iterative tightening.

    Each round:
    1. Run MCMC on current target signs
    2. Accept signs with >= agreement_threshold consensus
    3. Add accepted values to the cache mapping
    4. Re-run with reduced target set

    Returns summary dict.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    accepted_all: Dict[str, str] = {}
    round_results: List[Dict] = []

    # Copy cluster filter
    current_targets = cluster_signs.copy() if cluster_signs else None

    for round_num in range(max_tightening_rounds):
        logger.info("=" * 60)
        logger.info("TIGHTENING ROUND %d — %d target signs",
                     round_num + 1, len(current_targets) if current_targets else 0)

        # Run MCMC
        mcmc = VentrisMCMC(
            db_path=db_path,
            expanded_grid_path=expanded_grid_path,
            freq_path=freq_path,
            cluster_signs=current_targets,
            num_chains=num_chains,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )

        consensus = mcmc.run(iterations=iterations)
        distributions = mcmc.get_chain_states()

        # Accept high-agreement signs
        newly_accepted = {}
        for bid, (val, agreement) in consensus.items():
            if agreement >= agreement_threshold and bid not in accepted_all:
                newly_accepted[bid] = val
                accepted_all[bid] = val
                logger.info("ACCEPTED %s → /%s/ (%.1f%% agreement)",
                            bid, val, agreement * 100)

        # Record round results
        round_info = {
            "round": round_num + 1,
            "target_signs": len(mcmc.target_signs),
            "best_score": mcmc.best_score,
            "newly_accepted": len(newly_accepted),
            "total_accepted": len(accepted_all),
            "accepted_signs": newly_accepted,
        }
        round_results.append(round_info)

        # Update target list: remove accepted signs
        if current_targets:
            current_targets = [s for s in current_targets if s not in accepted_all]

        if not newly_accepted:
            logger.info("No new acceptances — convergence at round %d", round_num + 1)
            break

        if not current_targets:
            logger.info("All target signs resolved!")
            break

    # Write outputs
    # 1. Accepted signs
    acc_path = out / "mcmc_accepted_signs.csv"
    with open(acc_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bennett_id", "resolved_value", "source"])
        for bid, val in sorted(accepted_all.items()):
            writer.writerow([bid, val, "MCMC_iterative_tightening"])

    # 2. Per-sign distributions (last round)
    dist_path = out / "mcmc_distributions.csv"
    with open(dist_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bennett_id", "candidate_value", "chain_fraction"])
        for bid, dist in sorted(distributions.items()):
            for val, frac in sorted(dist.items(), key=lambda x: x[1], reverse=True)[:5]:
                writer.writerow([bid, val, f"{frac:.4f}"])

    # 3. Report
    report_lines = [
        "# Phase 10c — GPU-Accelerated MCMC Ventris Endgame",
        "",
        f"**Chains:** {num_chains}",
        f"**Iterations per round:** {iterations}",
        f"**Tightening rounds:** {len(round_results)}",
        f"**Total signs accepted:** {len(accepted_all)}",
        f"**Agreement threshold:** {agreement_threshold:.0%}",
        f"**Device:** {'cuda (GPU)' if torch.cuda.is_available() else 'cpu'}",
        "",
        "## Accepted Signs",
        "",
    ]
    for bid, val in sorted(accepted_all.items()):
        report_lines.append(f"- **{bid}** → `/{val}/`")

    report_lines += [
        "",
        "## Per-Round Results",
        "",
    ]
    for r in round_results:
        report_lines.append(
            f"- Round {r['round']}: {r['target_signs']} targets, "
            f"best score {r['best_score']:.4f}, "
            f"accepted {r['newly_accepted']} new signs "
            f"({', '.join(r['accepted_signs'].keys()) if r['accepted_signs'] else 'none'})"
        )

    report_lines += [
        "",
        "## Remaining High-Value Targets",
        "",
    ]
    if current_targets:
        for bid in sorted(current_targets):
            report_lines.append(f"- **{bid}**: below {agreement_threshold:.0%} agreement threshold")
    else:
        report_lines.append("- All target signs resolved!")

    report_lines += [
        "",
        "## Limitations",
        "",
        "- MCMC convergence is not guaranteed with 80 UNCERTAIN signs and sparse scoring signal",
        "- Morphology and prefix scores are heuristic — they favor plausible completions, not necessarily correct ones",
        "- The GPU scoring function samples bigram pairs (50 per batch) for speed — denser sampling would improve accuracy",
        "- AB 60 has no word-final context (alone on 46/47 inscriptions) — can't be resolved by morphology score",
        "- Frequency constraints are coarse (8 series × 5 vowels) — cannot distinguish /ta/ from /da/ or /na/",
        "",
        "---",
        "",
        "*Phase 10c — GPU-Accelerated MCMC. The method works but the scoring heuristics need stronger morphological signal for convergence on more than the most constrained cluster.*",
    ]

    report_path = out / "mcmc_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info("Phase 10c complete: %s accepted, report: %s",
                 len(accepted_all), report_path)

    return {
        "accepted_signs": accepted_all,
        "num_rounds": len(round_results),
        "total_accepted": len(accepted_all),
        "round_results": round_results,
        "output_dir": str(out),
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Default: boundary-flexible cluster
    BOUNDARY_FLEXIBLE = [
        "AB 01", "AB 02", "AB 47", "AB 60", "AB 62",
        "AB 65", "AB 66", "AB 80", "AB 85", "AB 87",
        "AB 113", "AB 130",
    ]

    summary = run_mcmc_decipher(
        cluster_signs=BOUNDARY_FLEXIBLE,
        num_chains=1024,
        iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 100000,
    )
    print()
    print("=" * 60)
    print("  GPU MCMC RESULTS")
    print("=" * 60)
    print(f"  Signs accepted: {len(summary['accepted_signs'])}")
    for bid, val in sorted(summary['accepted_signs'].items()):
        print(f"    {bid} → /{val}/")
