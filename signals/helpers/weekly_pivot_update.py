# signals/helpers/pivot_update.py

import numpy as np
import pandas as pd

from signals.trendline_maker.treat_extrema import (
    smooth_series,
    find_local_extrema_trend_aware,
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
    snap_window: int = 5,
) -> pd.DataFrame:
    """
    Recompute pivots ONLY for the segment [start_idx : end_idx].
    Pivots are detected from σ5-smoothed price ONLY.
    Timing from smooth curve, level from real price.
    """

    segment = data.loc[start_idx:end_idx].copy()
    y_raw = segment[price_col].values

    # ----------------------------------------------------------
    # 1) Smooth series
    # ----------------------------------------------------------
    y_s2, y_s5, y_s10, y_s20 = smooth_series(y_raw)

    data.loc[start_idx:end_idx, "smooth_s2"] = y_s2
    data.loc[start_idx:end_idx, "smooth_s5"] = y_s5
    data.loc[start_idx:end_idx, "smooth_s10"] = y_s10

    data.loc[start_idx:end_idx, "smooth_s20"] = y_s20

    # ----------------------------------------------------------
    # 2) σ5 extrema detection ONLY
    # ----------------------------------------------------------
    lows5, highs5, _, _ = find_local_extrema_trend_aware(y_s5)

    # ----------------------------------------------------------
    # 3) Clear pivot columns
    # ----------------------------------------------------------
    data.loc[start_idx:end_idx, "pivot_resistance_price"] = np.nan
    data.loc[start_idx:end_idx, "pivot_support_price"] = np.nan

    # ----------------------------------------------------------
    # 4) Insert snapped σ5 pivots (REAL price levels)
    # ----------------------------------------------------------
    for idx in highs5:
        if 0 <= idx < len(segment):
            snapped_idx = snap_to_real_extreme(
                y_raw, idx, window=snap_window, mode="high"
            )
            real_ts = segment.index[snapped_idx]
            data.at[real_ts, "pivot_resistance_price"] = y_raw[snapped_idx]

    for idx in lows5:
        if 0 <= idx < len(segment):
            snapped_idx = snap_to_real_extreme(
                y_raw, idx, window=snap_window, mode="low"
            )
            real_ts = segment.index[snapped_idx]
            data.at[real_ts, "pivot_support_price"] = y_raw[snapped_idx]

    return data
