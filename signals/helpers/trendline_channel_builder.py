# signals/helpers/trendline_channel_builder.py
import numpy as np
import pandas as pd


def build_trend_channel(
    data: pd.DataFrame,
    i: int,
    price_col="D_Close",
    smooth_col="D_Close_smooth",
    end_offset_days=1,
    col_mid="trendln_mid",
    col_top="trendln_top",
    col_bot="trendln_bottom",
    col_resist2="trendln_resist2",
    col_breakout="trendln_breakout",
    col_breakdown="trendln_breakdown",
    upper_q=0.90,
    lower_q=0.10,
):
    """
    Build regression + quantile channel.
    DOES NOT check breakout.
    Returns: data, lines_dict
    """

    # ensure float columns
    for c in (col_mid, col_top, col_bot, col_resist2, col_breakout, col_breakdown):
        if c not in data.columns:
            data[c] = np.full(len(data), np.nan, dtype=float)

    ts_i = data.index[i]
    ts_end_target = ts_i - pd.Timedelta(days=end_offset_days)
    end_pos = data.index.get_indexer([ts_end_target], method="pad")
    if not end_pos.size or end_pos[0] == -1:
        return data, None
    end_idx = data.index[end_pos[0]]

    mask = data.loc[:ts_i, "W_SenB_Consol_Start_Price"] == True
    if not mask.any():
        return data, None
    start_idx = mask[mask].index[-1]

    if start_idx >= end_idx:
        return data, None

    df_slice = data.loc[start_idx:end_idx]
    x = np.arange(len(df_slice))
    y = df_slice[price_col].values

    # regression
    a, b = np.polyfit(x, y, 1)
    mid = a * x + b

    # residuals
    resid = y - mid
    top = mid + np.nanquantile(resid, upper_q)
    bot = mid + np.nanquantile(resid, lower_q)
    resist2 = mid + np.nanquantile(resid, 0.975)
    breakout_line = mid + np.nanmax(resid)
    breakdown_line = mid + np.nanmin(resid)

    # write slice
    data.loc[start_idx:end_idx, col_mid] = mid
    data.loc[start_idx:end_idx, col_top] = top
    data.loc[start_idx:end_idx, col_bot] = bot
    data.loc[start_idx:end_idx, col_resist2] = resist2
    data.loc[start_idx:end_idx, col_breakout] = breakout_line
    data.loc[start_idx:end_idx, col_breakdown] = breakdown_line

    # extrapolate forward
    if end_idx < ts_i:
        future_df = data.loc[end_idx:ts_i]
        x_future = np.arange(len(df_slice), len(df_slice) + len(future_df))
        mid_f = a * x_future + b

        data.loc[end_idx:ts_i, col_mid] = mid_f
        data.loc[end_idx:ts_i, col_top] = mid_f + (top[-1] - mid[-1])
        data.loc[end_idx:ts_i, col_resist2] = mid_f + (resist2[-1] - mid[-1])
        data.loc[end_idx:ts_i, col_breakout] = mid_f + (breakout_line[-1] - mid[-1])
        data.loc[end_idx:ts_i, col_breakdown] = mid_f + (breakdown_line[-1] - mid[-1])

    # return a clean dict of current channel values
    return data, {
        "mid": data.loc[ts_i, col_mid],
        "top": data.loc[ts_i, col_top],
        "bot": data.loc[ts_i, col_bot],
        "resist2": data.loc[ts_i, col_resist2],
        "breakout": data.loc[ts_i, col_breakout],
        "breakdown": data.loc[ts_i, col_breakdown],
    }
