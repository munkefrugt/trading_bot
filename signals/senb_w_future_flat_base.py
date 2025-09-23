# signals/senb_w_future_flat_base.py
from .helpers.day_to_week import day_to_week
import config
import pandas as pd

def senb_w_future_flat_base(data: pd.DataFrame, i: int) -> bool:
    w_pos = day_to_week(data, i)
    if w_pos is None or w_pos < 8:
        return False

    w = config.ichimoku_weekly
    series = w["W_Senkou_span_B_future"]

    # start of rise after a perfectly flat 8-week base
    prev_val = series.iloc[w_pos - 1]
    curr_val = series.iloc[w_pos]
    if pd.isna(prev_val) or pd.isna(curr_val) or not (curr_val > prev_val):
        return False

    seg = series.iloc[w_pos - 8 : w_pos]  # 8 values: [w_pos-8, ..., w_pos-1]
    if len(seg) != 8 or seg.isna().any() or seg.nunique() != 1:
        return False

    base_val = float(seg.iloc[-1])  # flat base value (the week just before the rise)

    # mark at Senkou future (26 weeks ahead on the daily index)
    future_index = i + (26 * 7)
    if future_index < len(data):
        future_date = data.index[future_index]
        data.at[future_date, "W_SenB_Future_flat_to_up_point"] = True

        # store sparse anchor one week BEFORE the future point (aligns with base week)
        anchor_index = future_index - 7
        if 0 <= anchor_index < len(data):
            anchor_date = data.index[anchor_index]
            data.at[anchor_date, "W_SenB_base_val"] = base_val

    return True
