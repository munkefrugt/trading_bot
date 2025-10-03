#helpers/trendline_crossings.py
import pandas as pd
import numpy as np
from .helpers.trendline import build_trend_channel_for_segment
from .helpers.trendline_eval import trendline_eval


SLOPE_COL = "W_Senkou_span_B_slope_pct"
SLOPE_ABS_THRESHOLD = 2.0  # %

def find_start_of_consolidation(data: pd.DataFrame, i: int):
    """
    Walk backward from i until |W_Senkou_span_B_slope_pct| > threshold.
    Mark that bar as consolidation start and set an anchor ≈ 26 calendar weeks earlier
    (snap to nearest available bar at/before that time).
    Returns (start_ts, anchor_ts_or_None) or (None, None) if not found.
    """
    if i <= 0 or i >= len(data) or SLOPE_COL not in data.columns:
        return None

    j = i
    while j > 0:
        slope = data.at[data.index[j], SLOPE_COL]
        if pd.notna(slope) and abs(slope) > SLOPE_ABS_THRESHOLD:
            time_senb_rise = data.index[j]
            data.loc[time_senb_rise, "W_SenB_Consol_Start_SenB"] = True

            # 26 calendar weeks earlier → snap to nearest available bar at/before that time
            anchor_time_target = time_senb_rise - pd.Timedelta(weeks=26)
            idx = data.index.get_indexer([anchor_time_target], method="pad")
            if idx.size and idx[0] != -1:
                seg_start_time = data.index[idx[0]]
                data.loc[seg_start_time, "W_SenB_Consol_Start_Price"] = True
                return seg_start_time
            return None
        j -= 1

    return None


def trendline_crossings(data: pd.DataFrame, i: int) -> bool:
    seg_start_time = find_start_of_consolidation(data, i)
    # keep building channel if channel arent done. 
    data, D_Close_smooth_breakout = build_trend_channel_for_segment(data, i)    
    crossings = trendline_eval(
        data,   
        start_ts=seg_start_time,
        end_ts=data.index[i])

    print("crossings")
    print(crossings)

    if crossings > 2 and D_Close_smooth_breakout:
        return True 
    
    return False
