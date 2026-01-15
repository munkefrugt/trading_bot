# signals/BB_cross_paired_with_trendline_cross.py

import pandas as pd
import config
from signals.helpers.day_to_week import day_to_week


def BB_cross_paired_with_trendline_cross(
    data: pd.DataFrame,
    i: int,
    seq,
    max_pair_days: int = 60,
) -> bool:
    """
    Detect WEEKLY Bollinger Band upper break and pair it with
    a recent DAILY pivot / trendline breakout.

    Logic:
    - Detect WEEKLY CLOSE > WEEKLY BB upper
    - Store weekly BB break event (timestamp + values)
    - Pair with last pivot break if within `max_pair_days`

    Design:
    - Weekly BB evaluated on weekly close only
    - Daily pivot break provides timing
    - Event-based, no lookbacks
    - No mutation of `data`
    """

    # --------------------------------------------------
    # 1) Weekly context
    # --------------------------------------------------
    w_pos = day_to_week(data, i)

    weekly_data = getattr(config, "weekly_data", None)
    weekly_bb = getattr(config, "weekly_bb", None)

    if (
        weekly_data is None
        or weekly_bb is None
        or w_pos is None
        or w_pos < 0
        or w_pos >= len(weekly_data)
    ):
        return False

    weekly_close = weekly_data["W_Close"].iloc[w_pos]
    weekly_upper = weekly_bb["W_BB_Upper_20"].iloc[w_pos]
    weekly_ts = weekly_data.index[w_pos]

    # --------------------------------------------------
    # 2) Detect WEEKLY BB upper CROSS (event)
    # --------------------------------------------------
    bb_weekly_cross = weekly_close > weekly_upper

    if bb_weekly_cross and "bb_weekly_break_ts" not in seq.helpers:
        seq.helpers["bb_weekly_break_ts"] = weekly_ts
        seq.helpers["bb_weekly_break_close"] = weekly_close
        seq.helpers["bb_weekly_break_upper"] = weekly_upper

        print(
            f"📊 WEEKLY BB BREAK | "
            f"week={weekly_ts.date()} | "
            f"W_Close={weekly_close:.2f} | "
            f"W_BB_Upper={weekly_upper:.2f} | "
            f"Δ={weekly_close - weekly_upper:.2f} | "
            f"seq={seq.id}"
        )

    # --------------------------------------------------
    # 3) Pair with DAILY pivot / trendline break
    # --------------------------------------------------
    pivot_ts = seq.helpers.get("pivot_break_ts")
    bb_ts = seq.helpers.get("bb_weekly_break_ts")

    if pivot_ts is None or bb_ts is None:
        return False

    days_after_pivot = (bb_ts - pivot_ts).days

    if 0 < days_after_pivot <= max_pair_days:
        seq.helpers["bb_pivot_pair_days"] = days_after_pivot

        seq.helpers["bb_pivot_pair_ts"] = bb_ts

        print(
            f"🔗 WEEKLY BB ↔ PIVOT PAIRED | "
            f"pivot={pivot_ts.date()} | "
            f"bb_week={bb_ts.date()} | "
            f"W_Close={seq.helpers.get('bb_weekly_break_close'):.2f} | "
            f"W_BB_Upper={seq.helpers.get('bb_weekly_break_upper'):.2f} | "
            f"Δ={seq.helpers.get('bb_weekly_break_close') - seq.helpers.get('bb_weekly_break_upper'):.2f} | "
            f"Δ_days={days_after_pivot} | "
            f"seq={seq.id}"
        )

        return True

    return False
