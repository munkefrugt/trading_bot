# signals/trendline_crossings.py
import pandas as pd
import numpy as np

from signals.helpers.segments import get_segment_bounds
from .helpers.weekly_pivot_update import weekly_pivot_update
from .helpers.trendline import build_trend_channel_for_segment
from .helpers.trendline_eval import trendline_eval


def trendline_crossings(data: pd.DataFrame, i: int) -> bool:
    """
    Builds or updates a trend channel for the active consolidation segment,
    updates pivots every 7 days, and checks breakout conditions.
    """

    # ---- Determine segment boundaries ----
    start_idx, end_idx = get_segment_bounds(data, i)
    if start_idx is None:
        return False

    # ---- Update pivots only every 7th day (segment start → current i) ----
    if i > 0 and i % 7 == 0:
        end_ts = data.index[i]  # convert i → timestamp
        data = weekly_pivot_update(data, start_idx, end_ts)

    # ---- Build trend channel for segment start → segment-end ----
    data, is_smooth_breakout = build_trend_channel_for_segment(
        data, start_idx=start_idx, end_idx=end_idx, i=i
    )

    # ---- Count crossings from segment start → current row ----
    crossings = trendline_eval(data, start_ts=start_idx, end_ts=data.index[i])

    # ---- Breakout condition ----
    if crossings > 2 and is_smooth_breakout:
        print(f"breakout (from {start_idx.date()})")
        return True

    return False
