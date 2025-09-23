# signals/senb_w_future_slope_pct.py
from .helpers.day_to_week import day_to_week
import config
import pandas as pd

def senb_w_future_slope_pct(
    data: pd.DataFrame,
    i: int,
    min_slope_pct: float = 1 
) -> bool:
    w_pos = day_to_week(data, i)
    if w_pos is None:
        return False

    series = config.ichimoku_weekly["W_Senkou_span_B_slope_pct"]
    if w_pos >= len(series):
        return False

    val = series.iloc[w_pos+26]
    if pd.isna(val) or val < min_slope_pct:
        return False

    # fire now
    data.at[data.index[i], "senb_w_future_slope_pct"] = True

    # mark the Senkou future point for plotting
    future_index = i + (26 * 7)
    if future_index < len(data):
        future_date = data.index[future_index]
        data.at[future_date, "W_SenB_Future_slope_ok_point"] = True

    return True
