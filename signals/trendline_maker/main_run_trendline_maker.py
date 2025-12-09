# main_run_trendline_maker.py
# Runs full trendline maker pipeline + candidate visualizer

import numpy as np
from datetime import datetime
from .get_data import load_csv_from_drive, load_yf
from .trendline_pipeline import fit_trendlines_hybrid
from .plot_trendlines import plot_clean_extrema_with_trendlines
from .plot_candidate_lines import plot_candidate_lines


def run_trendline_maker(cluster_distance=10):
    print("=== Running Trendline Maker Sandbox ===")

    symbol = "BTC-USD"
    segment_start = "2024-03-01"
    segment_end = "2024-10-15"  # datetime.today().strftime("%Y-%m-%d")

    df = load_yf(symbol, segment_start, segment_end)

    # --- DATE SLICE ---
    df_new = df.loc[segment_start:segment_end].copy()
    x = np.arange(len(df_new))  # numeric
    x_dates = df_new.index  # datetime
    y = df_new["Close"].values

    # -------------------------------------------------------
    # RUN HYBRID TRENDLINE LOGIC
    # -------------------------------------------------------
    (
        support,
        resistance,
        lows_remaining,
        highs_remaining,
        lows_cluster,
        highs_cluster,
        y_s2,
        y_s5,
        lows_merged,
        highs_merged,
        m2,
        b2,
        m5,
        b5,
        support_pivots,
        resistance_pivots,
        support_reg,
        resistance_reg,
        sup_candidate_lines,
        sup_valid_lines,
        sup_best_line,
        res_candidate_lines,
        res_valid_lines,
        res_best_line,
    ) = fit_trendlines_hybrid(y, cluster_bar_distance=cluster_distance)

    # -------------------------------------------------------
    # PLOT RESULT
    # -------------------------------------------------------
    print("\n=== Plotting final trendlines ===")
    plot_clean_extrema_with_trendlines(
        x,
        x_dates,  # datetime
        y,
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
        support_pivots=support_pivots,
        resistance_pivots=resistance_pivots,
        support_reg=support_reg,
        resistance_reg=resistance_reg,
    )

    return {
        "support": support,
        "resistance": resistance,
        "y_s2": y_s2,
        "y_s5": y_s5,
        "pivots_support": support_pivots,
        "pivots_resistance": resistance_pivots,
    }
