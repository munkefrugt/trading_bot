# align_data_time.py

from calc_indicators import (
    compute_heikin_ashi,
    compute_ichimoku,
    compute_ema,
    extend_index,
    compute_bollinger_bands,
)
from get_data import extend_weekly_index, fetch_btc_weekly_data, fetch_btc_data
import pandas as pd
import numpy as np
import config
from math_helpers import smooth_savgol


def get_data_with_indicators_and_time_alignment():
    # Fetch and prefix daily data
    data = fetch_btc_data()
    data.columns = [f"D_{col}" for col in data.columns]

    # Weekly data should already be derived + prefixed at the source.
    # DO NOT re-prefix it here.
    weekly_raw = (
        fetch_btc_weekly_data()
    )  # expected columns: W_Open, W_High, W_Low, W_Close, ...

    # --- Daily indicators ---
    data["EMA_9"] = compute_ema(data, 9)
    data["EMA_20"] = compute_ema(data, 20)
    data["EMA_50"] = compute_ema(data, 50)
    data["EMA_100"] = compute_ema(data, 100)
    data["EMA_200"] = compute_ema(data, 200)
    data["EMA_365"] = compute_ema(data, 365)
    data["EMA_2y"] = compute_ema(data, 365 * 2)

    slope_window = getattr(config, "EMA_SLOPE_WINDOW_DAYS", 28)
    for p in (9, 20, 50, 100, 200, 365, "2y"):
        col = f"EMA_{p}"
        if col in data.columns:
            data[f"{col}_slope_%"] = (
                (data[col] - data[col].shift(slope_window))
                / data[col].shift(slope_window)
                * 100
            )

    # Daily BB
    bb_daily = compute_bollinger_bands(data, period=20, std_dev=2, prefix="D_")
    data["D_BB_Middle_20"] = bb_daily["D_BB_Middle_20"]
    data["D_BB_Upper_20"] = bb_daily["D_BB_Upper_20"]
    data["D_BB_Lower_20"] = bb_daily["D_BB_Lower_20"]
    data["D_BB_Width_20"] = bb_daily["D_BB_Width_20"]

    period = 365
    data["DC_Upper_365"] = data["D_High"].rolling(window=period).max()
    data["DC_Lower_365"] = data["D_Low"].rolling(window=period).min()
    data["DC_Middle_365"] = (data["DC_Upper_365"] + data["DC_Lower_365"]) / 2

    data["DC_Upper_26"] = data["D_High"].rolling(window=26).max()
    data["DC_Lower_26"] = data["D_Low"].rolling(window=26).min()
    data["DC_Middle_26"] = (data["DC_Upper_26"] + data["DC_Lower_26"]) / 2

    # Extend daily index for future cloud
    future_days = 26 * 7
    data = extend_index(data, future_days=future_days)

    # --- Heikin-Ashi (weekly) ---
    # Use the already-computed weekly HA from config if available; otherwise compute with correct schema.
    ha_weekly = getattr(config, "weekly_data_HA", None)
    if ha_weekly is None:
        ha_weekly = compute_heikin_ashi(weekly_raw, prefix="W_", weekly=True)

    ha_weekly_daily = ha_weekly.reindex(data.index, method="ffill")

    # Weekly raw forward-filled onto daily index
    weekly_daily = weekly_raw.reindex(data.index, method="ffill")

    data = pd.concat([data, ha_weekly_daily, weekly_daily], axis=1)

    # --- Weekly Ichimoku ---
    ichimoku_weekly = getattr(config, "ichimoku_weekly", None)
    if ichimoku_weekly is None:
        weekly_extended = extend_weekly_index(weekly_raw)
        config.ichimoku_weekly = compute_ichimoku(
            weekly_extended, prefix="W_", weekly=True
        )
        ichimoku_weekly = config.ichimoku_weekly

    ichimoku_weekly_daily = ichimoku_weekly.reindex(data.index).interpolate(
        method="time"
    )
    data = pd.concat([data, ichimoku_weekly_daily], axis=1)

    # Mask W_Tenkan and W_Kijun where daily data is missing
    if "W_Tenkan_sen" in data.columns:
        data["W_Tenkan_sen"] = data["W_Tenkan_sen"].where(data["D_Close"].notna())
    if "W_Kijun_sen" in data.columns:
        data["W_Kijun_sen"] = data["W_Kijun_sen"].where(data["D_Close"].notna())

    # Drop future Chikou_span values
    cutoff_days = 26 * 2 * 7  # 364 days
    cutoff_index = len(data) - cutoff_days
    if "W_Chikou_span" in data.columns and cutoff_index > 0:
        data.loc[data.index[cutoff_index:], "W_Chikou_span"] = np.nan

    # --- Daily Ichimoku ---
    ichimoku_daily = compute_ichimoku(data)
    data = pd.concat([data, ichimoku_daily], axis=1)

    return data
