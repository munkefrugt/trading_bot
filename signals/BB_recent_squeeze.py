# signals/BB_recent_squeeze.py

import pandas as pd
import config
from .helpers.day_to_week import day_to_week

def BB_recent_squeeze(
    data: pd.DataFrame,
    i: int,
    lookback_weeks: int = 150,
    bubble_quantile: float = 0.75,
    calm_min_weeks: int = 8,
    calm_mean_frac: float = 0.7,
) -> bool:
    """
    Detect whether we are currently in (or just emerging from)
    a calm volatility zone that followed a previous Bollinger 'bubble'.

    IMPORTANT:
        - Does NOT wait for the weekly expansion candle.
        - Returns TRUE once calm zone exists (meta-condition for trendline breakouts).
        - Expansion is still logged for informational/plotting use, but
          NOT REQUIRED for returning True.

    Writes to weekly_bb:
      BB_squeeze_start
      BB_tight_channel
      BB_has_squeezed
      BB_squeeze_start_time
      BB_squeeze_length_weeks
      BB_bubble_start_time
      BB_bubble_end_time
      BB_bubble_peak_time
      (OPTIONAL) BB_post_squeeze_expansion if expansion later appears
    """

    w_pos = day_to_week(data, i)
    w = getattr(config, "weekly_bb", None)

    if w_pos is None or w is None:
        return False

    if w_pos < calm_min_weeks + 3:
        return False

    req = ["W_BB_Middle_20", "W_BB_Upper_20", "W_BB_Lower_20"]
    if not all(col in w.columns for col in req):
        return False

    mid = w["W_BB_Middle_20"]
    up  = w["W_BB_Upper_20"]
    low = w["W_BB_Lower_20"]

    width = (up - low) / mid

    # ---------------------- WINDOW ----------------------
    start_pos = max(0, w_pos - lookback_weeks)
    window = width.iloc[start_pos : w_pos + 1]

    if len(window) < calm_min_weeks + 3:
        return False

    bubble_th = window.quantile(bubble_quantile)

    # ---------------------- FIND BUBBLE PEAK ----------------------
    bubble_pos = None
    for pos in range(start_pos + 1, w_pos - 1):
        w_here = width.iloc[pos]
        if w_here >= bubble_th:
            w_prev = width.iloc[pos - 1]
            w_next = width.iloc[pos + 1]
            if w_here >= w_prev and w_here >= w_next:
                bubble_pos = pos  # last bubble peak

    if bubble_pos is None:
        return False

    bubble_label = w.index[bubble_pos]
    bubble_width = width.iloc[bubble_pos]

    # ---------------------- FIND BUBBLE START & END ----------------------
    bubble_start_pos = bubble_pos
    for pos in range(bubble_pos - 1, start_pos - 1, -1):
        if width.iloc[pos] < bubble_th:
            break
        bubble_start_pos = pos

    bubble_end_pos = bubble_pos
    for pos in range(bubble_pos + 1, w_pos + 1):
        if width.iloc[pos] < bubble_th:
            break
        bubble_end_pos = pos

    bubble_start_label = w.index[bubble_start_pos]
    bubble_end_label   = w.index[bubble_end_pos]

    # ---------------------- CALM ZONE ----------------------
    calm_start = bubble_end_pos
    calm_end = w_pos

    if calm_end - calm_start < calm_min_weeks:
        return False

    calm_slice = width.iloc[calm_start:calm_end]
    if calm_slice.empty:
        return False

    calm_mean = calm_slice.mean()

    # calm must be significantly narrower than bubble
    if calm_mean >= bubble_width * calm_mean_frac:
        return False

    # ---------------------- MARK CALM ZONE ----------------------
    squeeze_start_label = calm_slice.idxmin()

    w.loc[squeeze_start_label, "BB_squeeze_start"] = True
    w.loc[squeeze_start_label, "BB_has_squeezed"] = True
    w.loc[squeeze_start_label, "BB_squeeze_start_time"] = pd.Timestamp(squeeze_start_label)
    w.loc[squeeze_start_label, "BB_squeeze_length_weeks"] = len(calm_slice)

    # mark calm zone flags
    for lbl in calm_slice.index:
        w.loc[lbl, "BB_tight_channel"] = True

    # bubble metadata (for plotting / inspection)
    w.loc[bubble_start_label, "BB_bubble_start_time"] = pd.Timestamp(bubble_start_label)
    w.loc[bubble_label,       "BB_bubble_peak_time"]  = pd.Timestamp(bubble_label)
    w.loc[bubble_end_label,   "BB_bubble_end_time"]   = pd.Timestamp(bubble_end_label)

    # ---------------------- DEBUG PRINTS ----------------------
    try:
        print("\n=== BB calm-zone DEBUG ===")
        print(f"Bubble threshold      : {bubble_th:.4f}")
        print(f"Bubble START          : {bubble_start_label.date()}")
        print(f"Bubble PEAK           : {bubble_label.date()} (width={bubble_width:.4f})")
        print(f"Bubble END            : {bubble_end_label.date()}")
        print(f"Calm zone             : {calm_slice.index[0].date()} → {calm_slice.index[-1].date()}")
        print(f"Calm mean width       : {calm_mean:.4f}")
        print(f"Calm zone length      : {len(calm_slice)} weeks")
        print("CALM detected → returning TRUE.")
    except:
        pass

    # ❗ IMPORTANT: Return True because calm zone exists
    return True
