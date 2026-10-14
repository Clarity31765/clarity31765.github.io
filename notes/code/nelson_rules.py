"""
Nelson Rules checker for an Individuals (I) control chart.

Reads a CSV of sequential measurements, estimates the center line and sigma,
applies all eight Nelson rules (Lloyd S. Nelson, 1984), and writes:
  - a table of violations (CSV)
  - a control chart with flagged points (PNG)

Usage:
    python nelson_rules.py data/sample_qc.csv --column value
    python nelson_rules.py data/sample_qc.csv --column value --baseline 25
    python nelson_rules.py data/sample_qc.csv --column value --mean 10.0 --sigma 0.2

Sigma for an Individuals chart is estimated as  MR-bar / 1.128  (d2 for n = 2)
from the baseline points, unless --mean and --sigma are given.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

D2_N2 = 1.128  # bias-correction constant for moving range of 2 points

RULE_TEXT = {
    1: "1 point beyond 3 sigma",
    2: "9 points in a row on the same side of the center line",
    3: "6 points in a row steadily increasing or decreasing",
    4: "14 points in a row alternating up and down",
    5: "2 of 3 points beyond 2 sigma, same side",
    6: "4 of 5 points beyond 1 sigma, same side",
    7: "15 points in a row within 1 sigma (either side)",
    8: "8 points in a row beyond 1 sigma, on both sides",
}


@dataclass
class Violation:
    rule: int
    end_index: int          # index of the point that completes the pattern
    points: list[int]       # all points that make up the pattern


def estimate_limits(x: np.ndarray) -> tuple[float, float]:
    """Center line and sigma for an Individuals chart (MR-bar / d2)."""
    mean = float(np.mean(x))
    mr_bar = float(np.mean(np.abs(np.diff(x))))
    return mean, mr_bar / D2_N2


def check(x: np.ndarray, mean: float, sigma: float) -> list[Violation]:
    z = (np.asarray(x, dtype=float) - mean) / sigma
    n = len(z)
    side = np.sign(z)                    # +1 above, -1 below, 0 on the line
    d = np.sign(np.diff(z))              # direction between points
    out: list[Violation] = []

    def add(rule, end, pts):
        out.append(Violation(rule, end, list(pts)))

    for i in range(n):
        # Rule 1: one point beyond 3 sigma
        if abs(z[i]) > 3:
            add(1, i, [i])

        # Rule 2: 9 in a row on the same side
        if i >= 8:
            w = side[i - 8:i + 1]
            if np.all(w > 0) or np.all(w < 0):
                add(2, i, range(i - 8, i + 1))

        # Rule 3: 6 points in a row steadily increasing or decreasing
        # (6 points = 5 differences in the same direction)
        if i >= 5:
            w = d[i - 5:i]
            if np.all(w > 0) or np.all(w < 0):
                add(3, i, range(i - 5, i + 1))

        # Rule 4: 14 points alternating up and down (13 differences)
        if i >= 13:
            w = d[i - 13:i]
            if np.all(w != 0) and np.all(w[1:] * w[:-1] < 0):
                add(4, i, range(i - 13, i + 1))

        # Rule 5: 2 of 3 beyond 2 sigma, same side
        if i >= 2:
            w = z[i - 2:i + 1]
            for s in (1, -1):
                hits = [i - 2 + k for k in range(3) if s * w[k] > 2]
                if len(hits) >= 2:
                    add(5, i, hits)
                    break

        # Rule 6: 4 of 5 beyond 1 sigma, same side
        if i >= 4:
            w = z[i - 4:i + 1]
            for s in (1, -1):
                hits = [i - 4 + k for k in range(5) if s * w[k] > 1]
                if len(hits) >= 4:
                    add(6, i, hits)
                    break

        # Rule 7: 15 in a row within 1 sigma
        if i >= 14:
            w = z[i - 14:i + 1]
            if np.all(np.abs(w) < 1):
                add(7, i, range(i - 14, i + 1))

        # Rule 8: 8 in a row beyond 1 sigma, with points on both sides
        if i >= 7:
            w = z[i - 7:i + 1]
            if np.all(np.abs(w) > 1) and np.any(w > 0) and np.any(w < 0):
                add(8, i, range(i - 7, i + 1))

    return out


def first_hits(violations: list[Violation]) -> list[Violation]:
    """Keep only the first point of each continuous run, so one pattern is
    reported once instead of once per extra point."""
    kept, last_end = [], {}
    for v in sorted(violations, key=lambda v: (v.rule, v.end_index)):
        if last_end.get(v.rule) == v.end_index - 1:
            last_end[v.rule] = v.end_index
            continue
        kept.append(v)
        last_end[v.rule] = v.end_index
    return sorted(kept, key=lambda v: (v.end_index, v.rule))


def plot(x, mean, sigma, violations, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    idx = np.arange(1, len(x) + 1)
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)

    for k, ls, a in ((3, "-", 0.9), (2, "--", 0.6), (1, ":", 0.5)):
        for s in (1, -1):
            ax.axhline(mean + s * k * sigma, color="#B42318" if k == 3 else "#8A8F98",
                       ls=ls, lw=1, alpha=a)
        ax.text(len(x) + 2.2, mean + k * sigma, f"+{k}σ", va="center", fontsize=8, color="#555")
        ax.text(len(x) + 2.2, mean - k * sigma, f"-{k}σ", va="center", fontsize=8, color="#555")
    ax.axhline(mean, color="#0E5A63", lw=1.2)
    ax.text(len(x) + 2.2, mean, "CL", va="center", fontsize=8, color="#0E5A63")

    ax.plot(idx, x, color="#0E5A63", lw=1, marker="o", ms=3.5, zorder=2)

    flagged = {}
    for v in violations:
        flagged.setdefault(v.end_index, set()).add(v.rule)
    for i, rules in flagged.items():
        ax.plot(idx[i], x[i], "o", ms=8, mfc="none", mec="#F08A24", mew=1.8, zorder=3)
        ax.annotate(",".join(f"R{r}" for r in sorted(rules)), (idx[i], x[i]),
                    xytext=(0, 9), textcoords="offset points", ha="center",
                    fontsize=7.5, color="#B54708")

    ax.set_title(title, fontsize=11, loc="left")
    ax.set_xlabel("Sample #")
    ax.set_ylabel("Value")
    ax.set_xlim(0, len(x) + 5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="Apply the 8 Nelson rules to an Individuals chart.")
    p.add_argument("csv")
    p.add_argument("--column", default="value")
    p.add_argument("--baseline", type=int, default=None,
                   help="use only the first N points to estimate mean and sigma")
    p.add_argument("--mean", type=float, default=None)
    p.add_argument("--sigma", type=float, default=None)
    p.add_argument("--out", default="output")
    a = p.parse_args()

    x = pd.read_csv(a.csv)[a.column].to_numpy(dtype=float)
    if a.mean is not None and a.sigma is not None:
        mean, sigma = a.mean, a.sigma
        src = "given"
    else:
        base = x[: a.baseline] if a.baseline else x
        mean, sigma = estimate_limits(base)
        src = f"MR-bar/1.128 from first {len(base)} points"

    v = first_hits(check(x, mean, sigma))

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = [{"sample": i.end_index + 1, "rule": i.rule, "description": RULE_TEXT[i.rule],
             "pattern_samples": f"{i.points[0] + 1}-{i.points[-1] + 1}"} for i in v]
    pd.DataFrame(rows, columns=["sample", "rule", "description", "pattern_samples"]) \
        .to_csv(out / "violations.csv", index=False)
    plot(x, mean, sigma, v, f"Individuals chart with Nelson rules  (CL={mean:.3f}, σ={sigma:.3f}, {src})",
         out / "control_chart.png")

    print(f"Center line = {mean:.4f}, sigma = {sigma:.4f} ({src})")
    print(f"{len(v)} pattern(s) found")
    for r in rows:
        print(f"  sample {r['sample']:>3}  Rule {r['rule']}: {r['description']}  [{r['pattern_samples']}]")


if __name__ == "__main__":
    main()
