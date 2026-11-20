"""Analyze matched ACT and Diffusion trials in the original evaluation order."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta, binomtest
from sequentialized_barnard_tests import Decision, Hypothesis, MirroredStepTest


POLICIES = ("ACT", "Diffusion")


def read_trials(path, budget):
    required = {"policy", "episode_id", "configuration_id", "success", "partial_score", "recorded_time_s"}
    records = {policy: {} for policy in POLICIES}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        for row in reader:
            policy = row["policy"]
            episode = int(row["episode_id"])
            layout = row["configuration_id"].strip()
            if policy not in records or episode in records[policy] or not layout:
                raise ValueError(f"Unexpected policy, duplicate episode, or empty layout: {policy} {episode}.")
            success = row["success"]
            time_s = float(row["recorded_time_s"])
            progress = float(row["partial_score"])
            if success not in ("0", "1") or not np.isfinite(time_s) or time_s < 0 or not 0 <= progress <= 1:
                raise ValueError(f"Invalid outcome, time, or partial score: {policy} {episode}.")
            records[policy][episode] = (layout, int(success), time_s, progress)

    order = range(1, budget + 1)
    if any(set(episodes) != set(order) for episodes in records.values()):
        raise ValueError(f"Expected episodes 1 through {budget} for both policies.")
    act_layouts, diffusion_layouts = ([records[policy][i][0] for i in order] for policy in POLICIES)
    if act_layouts != diffusion_layouts or len(set(act_layouts)) != budget:
        raise ValueError("Episode order must have unique, matched configuration IDs.")

    outcomes = [tuple(records[policy][i][1] for policy in POLICIES) for i in order]
    return outcomes, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--n-max", type=int, default=25, help="Predeclared budget per policy")
    parser.add_argument("--out", type=Path, default=Path("step_results"))
    args = parser.parse_args()
    if args.n_max < 25:
        parser.error("The assignment requires at least 25 trials per policy.")
    try:
        trials, records = read_trials(args.manifest, args.n_max)
    except (ValueError, OSError) as error:
        parser.error(str(error))

    test = MirroredStepTest(alternative=Hypothesis.P0LessThanP1, n_max=args.n_max,
                            alpha=0.10, inference_mode="ranking", random_seed=42)
    winner = None
    decision_line = f"Inconclusive after {len(trials)} trials per policy."
    for trial, (act, diffusion) in enumerate(trials, 1):
        decision = test.step(act, diffusion).decision
        if decision != Decision.FailToDecide:
            winner = {Decision.AcceptAlternative: "Diffusion", Decision.AcceptNull: "ACT"}[decision]
            decision_line = f"First STEP decision: {winner} favored after {trial} trials per policy."
            break

    lines = [decision_line, f"n_max={args.n_max}, alpha_pair=0.10, linear risk budget, ranking, seed=42",
             "Official STEP commit 3ae1623906f82fe472a352ed4a6b8e4a712f1f3d"]
    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    probability = np.linspace(0, 1, 501)
    for index, (name, outcomes) in enumerate(zip(POLICIES, zip(*trials))):
        successes, n = sum(outcomes), len(outcomes)
        interval = binomtest(successes, n).proportion_ci(confidence_level=0.90, method="wilson")
        lines.append(f"{name}: {successes} successes, {n-successes} failures, "
                     f"{successes/n:.1%} (90% Wilson CI {interval.low:.1%} to {interval.high:.1%})")
        successful_times = [time_s for _, result, time_s, _ in records[name].values() if result]
        if successful_times:
            q1, median, q3 = np.percentile(successful_times, [25, 50, 75])
            lines.append(f"  Successful trials: median {median:g} s, Q1–Q3 {q1:g}–{q3:g} s")
        mean_progress = np.mean([progress for _, _, _, progress in records[name].values()])
        lines.append(f"  Mean partial score: {mean_progress:.2f}")
        density = beta.pdf(probability, successes + 1, n - successes + 1)
        width = 0.35 * density / density.max()
        ax.fill_betweenx(probability, index-width, index+width, color=["#366f90", "#bf7645"][index])
        ax.text(index, 1.03, "a" if winner in (None, name) else "b", ha="center")
    ax.set(xticks=[0, 1], xticklabels=["ACT", "Diffusion"], xlim=(-0.6, 1.6),
           ylim=(0, 1.1), yticks=np.linspace(0, 1, 6), ylabel="Success probability")
    fig.tight_layout()
    args.out.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out / "posterior_violin.png", dpi=220)
    summary = "\n".join(lines) + "\n"
    (args.out / "summary.txt").write_text(summary, encoding="utf-8")
    print(summary, end="")


if __name__ == "__main__":
    main()
