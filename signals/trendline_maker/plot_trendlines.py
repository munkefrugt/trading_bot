# trendline_maker/plot_trendlines.py

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates


def plot_clean_extrema_with_trendlines(
    x_num,  # numeric index (0,1,2,...)
    x_dates,  # datetime index for plotting
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
    """
    Clean plot function using:
      x_num   -> numeric axis for math (trendlines, regressions)
      x_dates -> datetime axis for visual plotting
    """

    plt.figure(figsize=(15, 6))

    # ============================================
    # RAW PRICE + SMOOTH LINES
    # ============================================
    plt.plot(x_dates, y_raw, alpha=0.3, label="Close", linewidth=1)
    plt.plot(x_dates, y_s2, label="σ2", linewidth=2)
    plt.plot(x_dates, y_s5, label="σ5", linewidth=2, alpha=0.7)

    # ============================================
    # REGRESSION LINES (use numeric x for math)
    # ============================================
    plt.plot(x_dates, m2 * x_num + b2, color="blue", linestyle="-", linewidth=1.5)
    plt.plot(x_dates, m5 * x_num + b5, color="purple", linestyle=":", linewidth=1.5)

    # ============================================
    # EXTREMA (remaining)
    # ============================================
    plt.scatter(
        x_dates[lows_remaining],
        y_s2[lows_remaining],
        s=70,
        color="green",
        marker="v",
        label="Lows (remaining)",
    )

    plt.scatter(
        x_dates[highs_remaining],
        y_s2[highs_remaining],
        s=70,
        color="red",
        marker="^",
        label="Highs (remaining)",
    )

    # ============================================
    # EXTREMA (clusters)
    # ============================================
    plt.scatter(
        x_dates[lows_cluster],
        y_s2[lows_cluster],
        s=300,
        color="green",
        alpha=0.25,
        edgecolor="black",
        label="Low cluster",
    )

    plt.scatter(
        x_dates[highs_cluster],
        y_s2[highs_cluster],
        s=300,
        color="red",
        alpha=0.25,
        edgecolor="black",
        label="High cluster",
    )

    # ============================================
    # SUPPORT / RESISTANCE LINES
    # ============================================
    if support:
        slope, intercept = support
        plt.plot(
            x_dates,
            slope * x_num + intercept,
            color="green",
            linestyle="--",
            linewidth=2,
            label="Support line",
        )

    if resistance:
        slope, intercept = resistance
        plt.plot(
            x_dates,
            slope * x_num + intercept,
            color="red",
            linestyle="--",
            linewidth=2,
            label="Resistance line",
        )

    # ============================================
    # PIVOTS
    # ============================================
    if support_pivots:
        a, b = support_pivots
        if a is not None:
            plt.scatter(
                x_dates[a],
                y_s2[a],
                color="lime",
                s=200,
                marker="X",
                label="Support pivots",
            )
        if b is not None:
            plt.scatter(x_dates[b], y_s2[b], color="lime", s=200, marker="X")

    if resistance_pivots:
        a, b = resistance_pivots
        if a is not None:
            plt.scatter(
                x_dates[a],
                y_s2[a],
                color="pink",
                s=200,
                marker="X",
                label="Resistance pivots",
            )
        if b is not None:
            plt.scatter(x_dates[b], y_s2[b], color="pink", s=200, marker="X")

    # ============================================
    # DATE FORMATTING
    # ============================================
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)

    # ============================================
    # FINISH
    # ============================================
    plt.title("Hybrid Trendline Detector (Clean Extrema + Trendlines)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
