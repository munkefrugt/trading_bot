# signals/BB_recent_squeeze.py
import pandas as pd
import config
from .helpers.day_to_week import day_to_week

def BB_recent_squeeze(
    data: pd.DataFrame,
    i: int,
    lookback_weeks: int = 100,
    squeeze_pct: float = 0.20,
    expansion_factor: float = 1.10,
    tight_weeks: int = 16,   # about 4 months
) -> bool:
    """
    Pure WEEKLY Bollinger Squeeze Logic.
    Writes ONLY into config.weekly_bb (weekly space).

    Stores inside weekly_bb:
      BB_squeeze_start
      BB_squeeze_end
      BB_tight_channel
      BB_post_squeeze_expansion
      BB_has_squeezed
      BB_squeeze_length_weeks
      BB_squeeze_start_time
      BB_squeeze_end_time
    """

    # Map daily index -> weekly index
    w_pos = day_to_week(data, i)
    w = getattr(config, "weekly_bb", None)

    if w_pos is None or w is None or w_pos < lookback_weeks:
        return False

    req = ["W_BB_Middle_20", "W_BB_Upper_20", "W_BB_Lower_20"]
    if not all(col in w.columns for col in req):
        return False

    mid = w["W_BB_Middle_20"]
    up  = w["W_BB_Upper_20"]
    low = w["W_BB_Lower_20"]

    width = (up - low) / mid

    # recent slice (last X weeks)
    recent = width.iloc[w_pos - lookback_weeks : w_pos]

    # define squeeze threshold
    squeeze_threshold = recent.quantile(squeeze_pct)

    # --- Detect squeeze existence ---
    recent_min = recent.min()
    if recent_min > squeeze_threshold:
        return False

    # ===========================
    # SQUEEZE START (weekly)
    # ===========================
    squeeze_start_w = recent.idxmin()

    # mark start
    w.at[squeeze_start_w, "BB_squeeze_start"] = True
    w.at[squeeze_start_w, "BB_has_squeezed"] = True
    w.at[squeeze_start_w, "BB_squeeze_start_time"] = w.index[squeeze_start_w]

    # ===========================
    # TIGHT CHANNEL (weekly)
    # ===========================
    if len(recent) >= tight_weeks:
        tight_zone = recent.iloc[-tight_weeks:]
        tight_th = tight_zone.quantile(squeeze_pct)

        # weeks in the tight zone
        tight_weeks_list = [idx for idx, val in tight_zone.items() if val < tight_th]

        for idx in tight_weeks_list:
            w.at[idx, "BB_tight_channel"] = True

        # squeeze length in weeks
        w.at[squeeze_start_w, "BB_squeeze_length_weeks"] = len(tight_weeks_list)

    # ===========================
    # EXPANSION (weekly)
    # ===========================
    current_width = width.iloc[w_pos]
    if current_width <= recent_min * expansion_factor:
        return False

    # expansion hits: store at current week
    w.at[w_pos, "BB_squeeze_end"] = True
    w.at[w_pos, "BB_post_squeeze_expansion"] = True
    w.at[w_pos, "BB_squeeze_end_time"] = w.index[w_pos]

    try:
        ts = pd.to_datetime(w.index[w_pos]).date()
        print(f"🌀 Weekly BB POST-SQUEEZE expansion detected at {ts}")
    except Exception:
        pass

    return True
