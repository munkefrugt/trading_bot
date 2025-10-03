# signals/helpers/trendline.py
import numpy as np
import pandas as pd

def build_trend_channel_for_segment(
    data: pd.DataFrame,
    i: int,
    price_col: str = "D_Close",
    smooth_col: str = "D_Close_smooth",
    end_offset_days: int = 14,
    upper_q: float = 0.90,
    lower_q: float = 0.10,
    col_mid: str = "trendln_mid",
    col_top: str = "trendln_top",
    col_bot: str = "trendln_bottom",
    col_resist2: str = "trendln_resist2",
    col_breakout: str = "trendln_breakout",
    col_breakdown: str = "trendln_breakdown",
):
    """
    Build a parallel trend channel for the segment. Adds:
      - midline (regression)
      - top/bottom (quantile envelopes)
      - resist2 (97.5% quantile)
      - breakout (max residual line / hard top)
      - breakdown (min residual line / hard bottom)

    Extrapolates mid, top, resist2, breakout, and breakdown forward until index i.
    Bottom is kept only over the slice.

    Returns (data, bool) where bool = True if smooth_col is above breakout at i.
    """
    # ensure float output columns exist
    for c in (col_mid, col_top, col_bot, col_resist2, col_breakout, col_breakdown):
        if c not in data.columns:
            data[c] = np.full(len(data), np.nan, dtype=float)
        else:
            if data[c].dtype != float:
                data[c] = data[c].astype(float)

    if i <= 0 or i >= len(data):
        return data, False
    if "W_SenB_Consol_Start_Price" not in data.columns or price_col not in data.columns:
        return data, False

    ts_i = data.index[i]
    ts_end_target = ts_i - pd.Timedelta(days=end_offset_days)
    end_pos = data.index.get_indexer([ts_end_target], method="pad")
    if not end_pos.size or end_pos[0] == -1:
        return data, False
    end_idx = data.index[end_pos[0]]

    # last start before i
    mask = data.loc[:data.index[i], "W_SenB_Consol_Start_Price"] == True
    if not mask.any():
        return data, False
    start_idx = mask[mask].index[-1]

    if start_idx >= end_idx:
        return data, False

    df_slice = data.loc[start_idx:end_idx]
    x = np.arange(len(df_slice))
    y = df_slice[price_col].values

    # regression fit
    a, b = np.polyfit(x, y, 1)
    mid = a * x + b

    # residuals
    resid = y - mid
    up_off = np.nanquantile(resid, upper_q)
    lo_off = np.nanquantile(resid, lower_q)
    r2_off = np.nanquantile(resid, 0.975)
    breakout_off = np.nanmax(resid)
    breakdown_off = np.nanmin(resid)

    # channel lines over slice
    top = mid + up_off
    bot = mid + lo_off
    resist2 = mid + r2_off
    breakout = mid + breakout_off
    breakdown = mid + breakdown_off

    # write slice
    data.loc[start_idx:end_idx, col_mid] = mid
    data.loc[start_idx:end_idx, col_top] = top
    data.loc[start_idx:end_idx, col_bot] = bot
    data.loc[start_idx:end_idx, col_resist2] = resist2
    data.loc[start_idx:end_idx, col_breakout] = breakout
    data.loc[start_idx:end_idx, col_breakdown] = breakdown

    # extrapolate everything except bottom to i
    if end_idx < data.index[i]:
        future_df = data.loc[end_idx:data.index[i]]
        x_future = np.arange(len(df_slice), len(df_slice) + len(future_df))

        mid_future = a * x_future + b
        top_future = mid_future + up_off
        resist2_future = mid_future + r2_off
        breakout_future = mid_future + breakout_off
        breakdown_future = mid_future + breakdown_off

        data.loc[end_idx:data.index[i], col_mid] = mid_future
        data.loc[end_idx:data.index[i], col_top] = top_future
        data.loc[end_idx:data.index[i], col_resist2] = resist2_future
        data.loc[end_idx:data.index[i], col_breakout] = breakout_future
        data.loc[end_idx:data.index[i], col_breakdown] = breakdown_future

    # check if smooth_col is above breakout at i
    above_breakout = False
    if smooth_col in data.columns and not pd.isna(data.loc[data.index[i], col_breakout]):
        if data.loc[data.index[i], smooth_col] > data.loc[data.index[i], col_breakout]:
            above_breakout = True

    return data, above_breakout
