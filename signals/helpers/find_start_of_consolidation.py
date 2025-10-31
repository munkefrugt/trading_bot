import pandas as pd

SLOPE_COL = "W_Senkou_span_B_slope_pct"
SLOPE_ABS_THRESHOLD = 2.0  # %

def find_start_of_consolidation(data: pd.DataFrame, i: int):
    """
    Walk backward from i until |W_Senkou_span_B_slope_pct| > threshold.
    Marks that bar as the consolidation start and also tags a price anchor
    about 26 weeks earlier (if available).
    Returns the timestamp of the start, or None if not found.
    """
    if i <= 0 or i >= len(data) or SLOPE_COL not in data.columns:
        return None

    j = i
    while j > 0:
        slope = data.at[data.index[j], SLOPE_COL]
        if pd.notna(slope) and abs(slope) > SLOPE_ABS_THRESHOLD:
            start_ts = data.index[j]
            data.loc[start_ts, "W_SenB_Consol_Start_SenB"] = True

            # 26 calendar weeks earlier → snap to nearest available bar at/before that time
            anchor_target = start_ts - pd.Timedelta(weeks=26)
            idx = data.index.get_indexer([anchor_target], method="pad")
            if idx.size and idx[0] != -1:
                anchor_ts = data.index[idx[0]]
                data.loc[anchor_ts, "W_SenB_Consol_Start_Price"] = True

            return start_ts
        j -= 1

    return None
