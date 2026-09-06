#!/usr/bin/env python3
"""Export a compact quality/latency figure from the audited report, without rerunning models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    import matplotlib  # type: ignore[import-not-found]

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore[import-not-found]

    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("figure output must be fresh")
    report = json.loads(args.report.read_text())
    conditions = report["conditions"]
    labels = [row["model"] for row in conditions]
    colors = ["#2563eb", "#059669", "#c2410c"][: len(labels)]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    x = list(range(len(labels)))
    success = [row["strict_success_rate"] * 100 for row in conditions]
    axes[0].bar(x, success, color=colors, width=0.55)
    for i, row in enumerate(conditions):
        low, high = row["success_ci95_cluster_bootstrap"]
        axes[0].vlines(i, low * 100, high * 100, color="#111827", linewidth=1.2)
        axes[0].text(i, min(102, high * 100 + 3), f"{int(row['successes'])}/21", ha="center")
    axes[0].set_ylim(0, 110)
    axes[0].set_ylabel("Strict Dev success (%)")
    axes[0].set_title("Quality: 95% group-bootstrap interval")
    samples = [[row["task_seconds"] for row in c["rows"]] for c in conditions]
    axes[1].boxplot(samples, positions=x, widths=0.45, showfliers=False)
    for i, values in enumerate(samples):
        # Deterministic offsets disclose all tasks without random display jitter.
        offsets = [i + ((j % 7) - 3) * 0.025 for j in range(len(values))]
        axes[1].scatter(offsets, values, color=colors[i], alpha=0.65, s=16)
    axes[1].set_ylabel("End-to-end seconds/task")
    axes[1].set_title("Latency: all 21 tasks, including failures")
    for ax in axes:
        ax.set_xticks(x, labels)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    fig.suptitle("clean_v1.1 Dev pilot — not held-out Test results", fontsize=12)
    args.output.mkdir(parents=True)
    fig.savefig(args.output / "quality_latency.png", dpi=250)
    fig.savefig(args.output / "quality_latency.pdf")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
