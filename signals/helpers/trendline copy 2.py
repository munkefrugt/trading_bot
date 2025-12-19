# signals/helpers/trendline.py
import numpy as np
import pandas as pd
from types import SimpleNamespace


def build_trend_channel_for_segment(
    data: pd.DataFrame,
    start_idx,
    end_idx,
    i,
    price_col: str = "D_Close",
    smooth_col: str = "D_Close_smooth",
    upper_q: float = 0.90,
    lower_q: float = 0.10,
    # col_mid: str = "trendln_mid",
    # col_top: str = "trendln_top",
    # col_bot: str = "trendln_bottom",
    # col_resist2: str = "trendln_resist2",
    # col_breakout: str = "trendln_breakout",
    # col_breakdown: str = "trendln_breakdown",
    return_regression: bool = False,
    extrapolate: bool = False,
):
    """
    Build the trend channel for the segment [start_idx : end_idx].

    Adds midline regression + parallel top/bottom envelopes.
    Extrapolates mid/top/resist2/breakout/breakdown forward to i.

    If return_regression=True, returns regression parameters
    used to build the channel.
    """

    # --------------------------------------------------
    # Ensure output columns exist
    # --------------------------------------------------
    for c in (
        col_mid,
        col_top,
        col_bot,
        col_resist2,
        col_breakout,
        col_breakdown,
    ):
        if c not in data.columns:
            data[c] = np.nan

    df_slice = data.loc[start_idx:end_idx]
    y = df_slice[price_col].values
    x = np.arange(len(df_slice))

    # --------------------------------------------------
    # Regression (midline)
    # --------------------------------------------------
    m, b = np.polyfit(x, y, 1)
    mid = m * x + b

    # --------------------------------------------------
    # Residual envelopes
    # --------------------------------------------------
    resid = y - mid
    up_off = np.nanquantile(resid, upper_q)
    lo_off = np.nanquantile(resid, lower_q)
    r2_off = np.nanquantile(resid, 0.975)
    breakout_off = np.nanmax(resid)
    breakdown_off = np.nanmin(resid)

    top = mid + up_off
    bot = mid + lo_off
    resist2 = mid + r2_off
    breakout = mid + breakout_off
    breakdown = mid + breakdown_off

    # --------------------------------------------------
    # Write over segment
    # --------------------------------------------------
    data.loc[start_idx:end_idx, col_mid] = mid
    data.loc[start_idx:end_idx, col_top] = top
    data.loc[start_idx:end_idx, col_bot] = bot
    data.loc[start_idx:end_idx, col_resist2] = resist2
    data.loc[start_idx:end_idx, col_breakout] = breakout
    data.loc[start_idx:end_idx, col_breakdown] = breakdown

    # --------------------------------------------------
    # Extrapolate forward to i
    # --------------------------------------------------
    if extrapolate == True:
        if end_idx < data.index[i]:
            future_df = data.loc[end_idx : data.index[i]]
            x_future = np.arange(len(df_slice), len(df_slice) + len(future_df))

            mid_f = m * x_future + b

            data.loc[end_idx : data.index[i], col_mid] = mid_f
            data.loc[end_idx : data.index[i], col_top] = mid_f + up_off
            data.loc[end_idx : data.index[i], col_resist2] = mid_f + r2_off
            data.loc[end_idx : data.index[i], col_breakout] = mid_f + breakout_off
            data.loc[end_idx : data.index[i], col_breakdown] = mid_f + breakdown_off

    # --------------------------------------------------
    # Breakout boolean (kept for backward compatibility)
    # --------------------------------------------------
    above_breakout = False
    if (
        smooth_col in data.columns
        and not pd.isna(data.at[data.index[i], col_breakout])
        and data.at[data.index[i], smooth_col] > data.at[data.index[i], col_breakout]
    ):
        above_breakout = True

    if return_regression:
        reg = SimpleNamespace(
            m=m,
            b=b,
            up_offset=up_off,
            low_offset=lo_off,
            r2_offset=r2_off,
            breakout_offset=breakout_off,
            breakdown_offset=breakdown_off,
        )
        return data, reg

    return data, above_breakout
