# signals/senb_w_future_slope_pct.py
from .helpers.day_to_week import day_to_week
import config
import pandas as pd

def senb_w_future_slope_pct(
    data: pd.DataFrame,
    i: int,
    min_slope_pct: float = 1.0,
) -> bool:
    w_pos = day_to_week(data, i)
    if w_pos is None:
        return False

    series = config.ichimoku_weekly["W_Senkou_span_B_slope_pct"]

    fut_w_pos = w_pos + 26  # check the weekly slope 26 weeks ahead
    if fut_w_pos >= len(series):
        return False

    val = series.iloc[fut_w_pos]
    if pd.isna(val) or val < min_slope_pct:
        return False

    # fire now
    data.at[data.index[i], "senb_w_future_slope_pct"] = True

    # mark the Senkou future point on the DAILY index using calendar time
    current_ts = data.index[i]
    future_ts = current_ts - pd.Timedelta(weeks=0) + pd.Timedelta(weeks=26)
    # snap to the next available bar (handles weekends/holidays)
    idx = data.index.get_indexer([future_ts], method="backfill")
    if idx.size and idx[0] != -1 and idx[0] < len(data):
        data.at[data.index[idx[0]], "W_SenB_Future_slope_ok_point"] = True

    print("senb_w_futu're_slope_pct found")
    return True
