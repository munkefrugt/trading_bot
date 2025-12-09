import numpy as np
import pandas as pd
from .get_data import fetch_btc_data
from .trendline_pipeline import fit_trendlines_hybrid
from .plot_trendlines import plot_clean_extrema_with_trendlines


def run_trendline_debug():
    df = fetch_btc_data().copy()
    df = df.rename(columns=str)

    # Better: slice by date
    start_year = 1
    years = 2
    start = df.index.min() + pd.DateOffset(years=start_year)
    end = start + pd.DateOffset(years=years)

    df_new = df.loc[start:end].copy()
    if df_new.empty:
        print("⚠ Slice was empty — adjust years/segment")
        return

    x = df_new.index.to_numpy()
    y = df_new["Close"].values

    (
        support,
        resistance,
        lows_remaining,
        highs_remaining,
        lows_cluster,
        highs_cluster,
        y_s2,
        y_s5,
        y_s15,
        y_s25,
        y_s50,
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
    ) = fit_trendlines_hybrid(y, cluster_bar_distance=10)

    plot_clean_extrema_with_trendlines(
        x,
        y,
        y_s2,
        y_s5,
        y_s15,
        y_s25,
        y_s50,
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
