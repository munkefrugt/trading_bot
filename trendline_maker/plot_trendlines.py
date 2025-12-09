# trendline_maker/plot_trendlines.py

import matplotlib.pyplot as plt


def plot_clean_extrema_with_trendlines(
    x,
    y_raw,
    y_s2,
    y_s5,
    lows_remaining,
    highs_remaining,
    lows_cluster,
    highs_cluster,
    support,
    resistance,
    m2,
    b2,
    m5,
    b5,
    support_pivots=None,
    resistance_pivots=None,
    support_reg=None,
    resistance_reg=None,
):
    plt.figure(figsize=(15, 6))

    plt.plot(x, y_raw, alpha=0.3, label="Close", linewidth=1)
    plt.plot(x, y_s2, label="σ2", linewidth=2)
    plt.plot(x, y_s5, label="σ5", linewidth=2, alpha=0.7)

    plt.plot(x, m2 * x + b2, color="blue", linestyle="-", linewidth=1.5)
    plt.plot(x, m5 * x + b5, color="purple", linestyle=":", linewidth=1.5)

    plt.scatter(lows_remaining, y_s2[lows_remaining], s=70, color="green", marker="v")
    plt.scatter(highs_remaining, y_s2[highs_remaining], s=70, color="red", marker="^")

    plt.scatter(
        lows_cluster,
        y_s2[lows_cluster],
        s=300,
        color="green",
        alpha=0.25,
        edgecolor="black",
    )
    plt.scatter(
        highs_cluster,
        y_s2[highs_cluster],
        s=300,
        color="red",
        alpha=0.25,
        edgecolor="black",
    )

    if support:
        slope, intercept = support
        plt.plot(x, slope * x + intercept, color="green", linestyle="--", linewidth=2)

    if resistance:
        slope, intercept = resistance
        plt.plot(x, slope * x + intercept, color="red", linestyle="--", linewidth=2)

    # mark pivots
    if support_pivots:
        a, b = support_pivots
        if a is not None:
            plt.scatter([a], [y_s2[a]], color="lime", s=200, marker="X")
        if b is not None:
            plt.scatter([b], [y_s2[b]], color="lime", s=200, marker="X")

    if resistance_pivots:
        a, b = resistance_pivots
        if a is not None:
            plt.scatter([a], [y_s2[a]], color="pink", s=200, marker="X")
        if b is not None:
            plt.scatter([b], [y_s2[b]], color="pink", s=200, marker="X")

    plt.grid(True)
    plt.tight_layout()
    plt.show()
