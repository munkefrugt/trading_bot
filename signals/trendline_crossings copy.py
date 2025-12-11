# signals/trendline_crossings.py
import pandas as pd
import numpy as np
from .helpers.trendline import build_trend_channel_for_segment
from .helpers.trendline_eval import trendline_eval
from .helpers.weekly_pivot_update import weekly_pivot_update
from signals.helpers.segments import get_segment_bounds


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

    # run this function every 7th calender day.
    # find pivots and add to df.
    # if a line exists and a resitance_pivot is above the line
    # (y = mx+b)
    #   resistance_line_m , resistance_line_b= get_resistance_pivot_line()

    # TODO make the pivots works and get tehm plotet.maybe start with the gausian smooth plot
    if i > 0 and i % 7 == 0:
        data = weekly_pivot_update(data)

    # --- Build the old trend channel ---
    data, D_Close_smooth_breakout = build_trend_channel_for_segment(data, i)

    # --- Evaluate number of crossings ---
    crossings = trendline_eval(data, start_ts=seg_start_time, end_ts=data.index[i])

    # --- Breakout condition ---
    if crossings > 2 and D_Close_smooth_breakout:
        print(f"breakout (from {seg_start_time.date()})")
        return True

    return False
