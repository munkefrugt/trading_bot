#signals/trendline_crossings.py
import pandas as pd
import numpy as np
from .helpers.trendline import build_trend_channel_for_segment
from .helpers.trendline_eval import trendline_eval


def trendline_crossings(data: pd.DataFrame, i: int) -> bool:
    """
    Builds or updates a trend channel based on the most recent consolidation start,
    then checks for breakout conditions.
    """

    # --- Find last True in W_SenB_Consol_Start_Price before index i ---
    seg_start_time = None
    if "W_SenB_Consol_Start_Price" in data.columns:
        true_indices = data.index[data["W_SenB_Consol_Start_Price"] == True]
        true_indices = true_indices[true_indices <= data.index[i]]
        if len(true_indices) > 0:
            seg_start_time = true_indices[-1]

    if seg_start_time is None:
        return False

    # --- Build or extend the trend channel ---
    data, D_Close_smooth_breakout = build_trend_channel_for_segment(data, i)

    # --- Evaluate number of crossings ---
    crossings = trendline_eval(
        data,
        start_ts=seg_start_time,
        end_ts=data.index[i]
    )

    # --- Breakout condition ---
    if crossings > 2 and D_Close_smooth_breakout:
        print(f"breakout (from {seg_start_time.date()})")
        return True

    return False

