# signals/helpers/weekly_pivot_update.py
import numpy as np
import pandas as pd

from signals.trendline_maker.treat_extrema import (
    smooth_series,
    find_local_extrema_trend_aware,
    snap_extrema,
    merge_extrema,
)


def weekly_pivot_update(
    data: pd.DataFrame,
    start_idx,
    end_idx,
    price_col: str = "D_Close",
    cluster_bar_distance: int = 8,
) -> pd.DataFrame:
    """
    Recompute pivots ONLY for the segment [start_idx : end_idx].
    Uses Gaussian smooths σ2/σ5 and same extrema logic as trendline_maker.
    """

    segment = data.loc[start_idx:end_idx].copy()
    y_raw = segment[price_col].values
    x = np.arange(len(y_raw))

    # ---- 1) Smooth series ----
    y_s2, y_s5, y_s20 = smooth_series(y_raw)

    # store smooth curves for plotting/debug
    data.loc[start_idx:end_idx, "smooth_s2"] = y_s2
    data.loc[start_idx:end_idx, "smooth_s5"] = y_s5
    data.loc[start_idx:end_idx, "smooth_s20"] = y_s20

    # ---- 2) Extrema detection ----
    lows2_raw, highs2_raw, _, _ = find_local_extrema_trend_aware(y_s2)
    lows5, highs5, _, _ = find_local_extrema_trend_aware(y_s5)

    # ---- 3) Snap σ2 → σ5 ----
    lows_cluster, lows_overridden = snap_extrema(lows2_raw, lows5, cluster_bar_distance)
    highs_cluster, highs_overridden = snap_extrema(
        highs2_raw, highs5, cluster_bar_distance
    )

    # ---- 4) Remaining σ2 extrema not overridden ----
    lows_remaining = sorted(set(lows2_raw) - set(lows_overridden))
    highs_remaining = sorted(set(highs2_raw) - set(highs_overridden))

    # ---- 5) Merge snapped + remaining ----
    lows_merged = merge_extrema(lows_cluster, lows_remaining)
    highs_merged = merge_extrema(highs_cluster, highs_remaining)

    # ---- 6) Clear pivot columns only for segment ----
    data.loc[start_idx:end_idx, "pivot_resistance_price"] = np.nan
    data.loc[start_idx:end_idx, "pivot_support_price"] = np.nan

    # ---- 7) Insert new pivots ----
    for idx in highs_merged:
        if 0 <= idx < len(segment):
            real_idx = segment.index[idx]
            data.at[real_idx, "pivot_resistance_price"] = y_raw[idx]

    for idx in lows_merged:
        if 0 <= idx < len(segment):
            real_idx = segment.index[idx]
            data.at[real_idx, "pivot_support_price"] = y_raw[idx]

    return data
