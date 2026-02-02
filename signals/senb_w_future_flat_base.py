# signals/senb_w_future_flat_base.py
from .helpers.day_to_week import day_to_week
from .helpers.cloud_future_check import future_week_sena_above_senb
import config
import pandas as pd


def senb_w_future_flat_base(data: pd.DataFrame, i: int, seq) -> bool:
    if not future_week_sena_above_senb(data, i):
        return False

    w_pos = day_to_week(data, i)
    if w_pos is None or w_pos < 8:
        return False

    w = config.ichimoku_weekly
    series = w["W_Senkou_span_B_future"]

    # start of rise after a perfectly flat 8-week base
    # prev_val = series.iloc[w_pos - 1]
    # curr_val = series.iloc[w_pos]
    # if pd.isna(prev_val) or pd.isna(curr_val) or not (curr_val > prev_val):
    #     return False

    seg = series.iloc[w_pos - 8 : w_pos]  # 8 values: [w_pos-8, ..., w_pos-1]
    if len(seg) != 8 or seg.isna().any() or seg.nunique() != 1:
        return False

    base_val = float(seg.iloc[-1])  # flat base value (week just before the rise)

    # --- Calendar-based marking on daily index ---
    current_ts = data.index[i]

    # Future point ~26 calendar weeks ahead; snap to next available bar (backfill)
    future_ts = current_ts + pd.Timedelta(weeks=26)
    future_idx = data.index.get_indexer([future_ts], method="backfill")
    if future_idx.size and future_idx[0] != -1 and future_idx[0] < len(data):
        future_loc = future_idx[0]
        data.at[data.index[future_loc], "W_SenB_Future_flat_to_up_point"] = True

        # Sparse anchor ~1 calendar week BEFORE future point; snap to prev available bar (pad)
        anchor_ts = future_ts - pd.Timedelta(weeks=1)
        anchor_idx = data.index.get_indexer([anchor_ts], method="pad")
        if anchor_idx.size and anchor_idx[0] != -1 and 0 <= anchor_idx[0] < len(data):
            data.at[data.index[anchor_idx[0]], "W_SenB_base_val"] = base_val

    print("found flat base")
    return True
