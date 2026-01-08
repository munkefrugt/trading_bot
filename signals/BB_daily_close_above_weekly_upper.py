# signals/BB_daily_close_above_weekly_upper.py

import pandas as pd
import config
from .helpers.day_to_week import day_to_week


def BB_daily_close_above_weekly_upper(data: pd.DataFrame, i: int, seq):
    # print("BB UPPER CALLED", data.index[i].date())
    w_pos = day_to_week(data, i)
    w = getattr(config, "weekly_bb", None)
    daily_close = data["D_Close"].iloc[i]
    last_weekly_upper = w["W_BB_Upper_20"].iloc[w_pos - 1]
    # 2024-10-29
    if data.index[i].date() == pd.Timestamp("2023-10-24").date():
        print("2023-10-24")
        print(daily_close)
        print(last_weekly_upper)

    if data.index[i].date() == pd.Timestamp("2024-10-29").date():
        print("2024-10-29")
        print(daily_close)
        print(last_weekly_upper)

    return daily_close > last_weekly_upper
