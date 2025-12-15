# signals/helpers/weekly_pivot_update.py

import numpy as np
import pandas as pd

from signals.trendline_maker.treat_extrema import (
    smooth_series,
    find_local_extrema_trend_aware,
    snap_extrema,
    merge_extrema,
)


def snap_to_real_extreme(y_raw, idx, window=5, mode="high"):
    lo = max(0, idx - window)
    hi = min(len(y_raw), idx + window + 1)

    if mode == "high":
        local_idx = np.argmax(y_raw[lo:hi])
    else:
        local_idx = np.argmin(y_raw[lo:hi])

    return lo + local_idx


def weekly_pivot_update(
    data: pd.DataFrame,
    start_idx,
    end_idx,
    price_col: str = "D_Close",
    cluster_bar_distance: int = 8,
    snap_window: int = 5,
) -> pd.DataFrame:
    """
    Recompute pivots ONLY for the segment [start_idx : end_idx].
    Smooth extrema define timing, raw price extrema define level.
    """

    segment = data.loc[start_idx:end_idx].copy()
    y_raw = segment[price_col].values
    x = np.arange(len(y_raw))

    # ---- 1) Smooth series ----
    y_s2, y_s5, y_s20 = smooth_series(y_raw)

    data.loc[start_idx:end_idx, "smooth_s2"] = y_s2
    data.loc[start_idx:end_idx, "smooth_s5"] = y_s5
    data.loc[start_idx:end_idx, "smooth_s20"] = y_s20

    # ---- 2) Extrema detection on smooth curves ----
    lows2_raw, highs2_raw, _, _ = find_local_extrema_trend_aware(y_s2)
    lows5, highs5, _, _ = find_local_extrema_trend_aware(y_s5)

    # ---- 3) Snap σ2 → σ5 ----
    lows_cluster, lows_overridden = snap_extrema(lows2_raw, lows5, cluster_bar_distance)
    highs_cluster, highs_overridden = snap_extrema(
        highs2_raw, highs5, cluster_bar_distance
    )

    # ---- 4) Remaining σ2 extrema ----
    lows_remaining = sorted(set(lows2_raw) - set(lows_overridden))
    highs_remaining = sorted(set(highs2_raw) - set(highs_overridden))

    # ---- 5) Merge ----
    lows_merged = merge_extrema(lows_cluster, lows_remaining)
    highs_merged = merge_extrema(highs_cluster, highs_remaining)

    # ---- 6) Clear pivot columns ----
    data.loc[start_idx:end_idx, "pivot_resistance_price"] = np.nan
    data.loc[start_idx:end_idx, "pivot_support_price"] = np.nan

    # ---- 7) Insert snapped pivots (REAL price extrema) ----
    for idx in highs_merged:
        if 0 <= idx < len(segment):
            snapped_idx = snap_to_real_extreme(
                y_raw, idx, window=snap_window, mode="high"
            )
            real_ts = segment.index[snapped_idx]
            data.at[real_ts, "pivot_resistance_price"] = y_raw[snapped_idx]

    for idx in lows_merged:
        if 0 <= idx < len(segment):
            snapped_idx = snap_to_real_extreme(
                y_raw, idx, window=snap_window, mode="low"
            )
            real_ts = segment.index[snapped_idx]
            data.at[real_ts, "pivot_support_price"] = y_raw[snapped_idx]

    return data
