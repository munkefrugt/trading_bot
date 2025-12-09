# trendline_maker/plot_candidate_lines.py

import matplotlib.pyplot as plt
import numpy as np


def plot_candidate_lines(
    x,
    y,
    extrema,
    candidate_lines,
    valid_lines,
    best_line,
    pivot_A,
    pivot_B,
    m_reg,
    b_reg,
    title="Trendline Candidates",
):
    plt.figure(figsize=(16, 9))

    # Raw price
    plt.plot(x, y, color="black", alpha=0.5, label="Price")

    # Extrema
    plt.scatter(extrema, y[extrema], s=70, color="orange", label="Extrema")

    # Regression line
    plt.plot(x, m_reg * x + b_reg, color="blue", linewidth=2, label="Regression")

    # All candidate lines (gray)
    for slope, intercept in candidate_lines:
        plt.plot(x, slope * x + intercept, color="gray", alpha=0.10, linewidth=1)

    # Valid lines (green)
    for slope, intercept in valid_lines:
        plt.plot(x, slope * x + intercept, color="green", alpha=0.45, linewidth=2)

    # Best line (red)
    if best_line:
        slope, intercept = best_line
        plt.plot(x, slope * x + intercept, color="red", linewidth=3, label="BEST")

    # Mark pivots
    if pivot_A is not None:
        plt.scatter(
            [pivot_A], [y[pivot_A]], s=140, color="red", marker="x", label="Pivot A"
        )
    if pivot_B is not None:
        plt.scatter(
            [pivot_B], [y[pivot_B]], s=140, color="blue", marker="x", label="Pivot B"
        )

    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
