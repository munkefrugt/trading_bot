# signals/BB_recent_squeeze.py
import pandas as pd
import config
from .helpers.day_to_week import day_to_week

def BB_recent_squeeze(data: pd.DataFrame, i: int) -> bool:
    """
    Detects a Bollinger Band squeeze (low volatility period)
    on the weekly timeframe using config.weekly_bb.

    Uses columns:
      - W_BB_Middle_20
      - W_BB_Upper_20
      - W_BB_Lower_20

    Prints when a squeeze is detected.
    """
    w_pos = day_to_week(data, i)
    if w_pos is None or w_pos < 100:
        return False

    w = getattr(config, "weekly_bb", None)
    if w is None:
        return False

    required = ["W_BB_Middle_20", "W_BB_Upper_20", "W_BB_Lower_20"]
    if not all(col in w.columns for col in required):
        return False

    middle = w["W_BB_Middle_20"]
    upper = w["W_BB_Upper_20"]
    lower = w["W_BB_Lower_20"]

    # Relative width of the Bollinger Bands
    width = (upper - lower) / middle

    # Compare current width to the last 100 weeks
    recent = width.iloc[w_pos - 100:w_pos]
    squeeze_threshold = recent.quantile(0.2)

    is_squeezed = width.iloc[w_pos] < squeeze_threshold

    if is_squeezed:
        try:
            squeeze_time = pd.to_datetime(w.index[w_pos]).date()
            print(f"🌀 Weekly BB squeeze detected at {squeeze_time}")
        except Exception:
            pass
        return True

    return False
