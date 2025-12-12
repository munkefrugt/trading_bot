# signals/trendline_crossings.py

import numpy as np
import pandas as pd

from signals.helpers.segments import get_segment_bounds
from signals.helpers.weekly_pivot_update import weekly_pivot_update
from signals.helpers.pivot_line_builder import build_pivot_trendlines
from .helpers.trendline import build_trend_channel_for_segment
from .helpers.trendline_eval import trendline_eval


def trendline_crossings(data: pd.DataFrame, i: int) -> bool:
    """
    Uses weekly pivots and pivot-based trendlines to detect breakout conditions.
    Steps:
      1) Determine consolidation segment (start_idx → end_idx)
      2) Every 7th day: update pivots for (start_idx → i)
      3) Build pivot trendlines from pivots
      4) Build trend channel for (start_idx → end_idx)
      5) Evaluate crossings and detect breakout
    """

    # ----------------------------------------------------------
    # 1) Consolidation segment boundaries
    # ----------------------------------------------------------
    start_idx, end_idx = get_segment_bounds(
        data, i, start_offset_days=20, end_offset_days=1
    )
    if start_idx is None:
        return False

    # timestamp of current i
    end_ts = data.index[i]

    # ----------------------------------------------------------
    # 2) Weekly pivot update (runs every 7 days)
    # ----------------------------------------------------------
    if i > 0 and i % 7 == 0:
        data = weekly_pivot_update(data, start_idx, end_ts)

        # ------------------------------------------------------
        # 3) Build pivot support/resistance trendlines
        # ------------------------------------------------------
        segment = data.loc[start_idx:end_ts]
        y_segment = segment["D_Close"].values

        pivot_lows_ts = segment.index[segment["pivot_support_price"].notna()].tolist()
        pivot_highs_ts = segment.index[
            segment["pivot_resistance_price"].notna()
        ].tolist()

        pivot_lows = [segment.index.get_loc(ts) for ts in pivot_lows_ts]
        pivot_highs = [segment.index.get_loc(ts) for ts in pivot_highs_ts]

        support_line, resistance_line = build_pivot_trendlines(
            y_segment, pivot_lows, pivot_highs
        )

        seg_len = len(segment)
        x = np.arange(seg_len)

        # clear old values in segment
        data.loc[start_idx:end_ts, ["pivot_support_line", "pivot_resistance_line"]] = (
            np.nan
        )

        # Write support line
        if support_line is not None:
            m, b = support_line
            data.loc[start_idx:end_ts, "pivot_support_line"] = m * x + b

        # Write resistance line
        if resistance_line is not None:
            m, b = resistance_line
            data.loc[start_idx:end_ts, "pivot_resistance_line"] = m * x + b

    # ----------------------------------------------------------
    # 4) Build trend channel for main consolidation window
    # ----------------------------------------------------------
    data, smooth_breakout = build_trend_channel_for_segment(
        data, start_idx=start_idx, end_idx=end_idx, i=i
    )

    # ----------------------------------------------------------
    # 5) Evaluate number of crossings within segment
    # ----------------------------------------------------------
    crossings = trendline_eval(data, start_ts=start_idx, end_ts=end_ts)

    # ----------------------------------------------------------
    # Breakout condition
    # ----------------------------------------------------------
    if crossings > 2 and smooth_breakout:
        print(f"breakout (from {start_idx.date()})")
        return True

    return False
