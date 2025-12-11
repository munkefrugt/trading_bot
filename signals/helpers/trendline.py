# signals/helpers/trendline.py
import numpy as np
import pandas as pd


def build_trend_channel_for_segment(
    data: pd.DataFrame,
    start_idx,
    end_idx,
    i,
    price_col: str = "D_Close",
    smooth_col: str = "D_Close_smooth",
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
    Build the trend channel for the segment [start_idx : end_idx].
    Adds midline regression + parallel top/bottom envelopes.
    Extrapolates mid/top/resist2/breakout/breakdown forward to i.
    """

    # ensure output columns exist
    for c in (col_mid, col_top, col_bot, col_resist2, col_breakout, col_breakdown):
        if c not in data.columns:
            data[c] = np.nan

    df_slice = data.loc[start_idx:end_idx]
    y = df_slice[price_col].values
    x = np.arange(len(df_slice))

    # ---- regression: midline ----
    a, b = np.polyfit(x, y, 1)
    mid = a * x + b

    # ---- residuals ----
    resid = y - mid
    up_off = np.nanquantile(resid, upper_q)
    lo_off = np.nanquantile(resid, lower_q)
    r2_off = np.nanquantile(resid, 0.975)
    breakout_off = np.nanmax(resid)
    breakdown_off = np.nanmin(resid)

    # ---- channel lines over slice ----
    top = mid + up_off
    bot = mid + lo_off
    resist2 = mid + r2_off
    breakout = mid + breakout_off
    breakdown = mid + breakdown_off

    # write over slice
    data.loc[start_idx:end_idx, col_mid] = mid
    data.loc[start_idx:end_idx, col_top] = top
    data.loc[start_idx:end_idx, col_bot] = bot
    data.loc[start_idx:end_idx, col_resist2] = resist2
    data.loc[start_idx:end_idx, col_breakout] = breakout
    data.loc[start_idx:end_idx, col_breakdown] = breakdown

    # ---- extrapolate forward to i (except bottom) ----
    if end_idx < data.index[i]:
        future_df = data.loc[end_idx : data.index[i]]
        x_future = np.arange(len(df_slice), len(df_slice) + len(future_df))

        mid_future = a * x_future + b
        top_future = mid_future + up_off
        resist2_future = mid_future + r2_off
        breakout_future = mid_future + breakout_off
        breakdown_future = mid_future + breakdown_off

        data.loc[end_idx : data.index[i], col_mid] = mid_future
        data.loc[end_idx : data.index[i], col_top] = top_future
        data.loc[end_idx : data.index[i], col_resist2] = resist2_future
        data.loc[end_idx : data.index[i], col_breakout] = breakout_future
        data.loc[end_idx : data.index[i], col_breakdown] = breakdown_future

    # ---- breakout boolean ----
    above_breakout = False
    if smooth_col in data.columns and not pd.isna(data.at[data.index[i], col_breakout]):
        if data.at[data.index[i], smooth_col] > data.at[data.index[i], col_breakout]:
            above_breakout = True

    return data, above_breakout
