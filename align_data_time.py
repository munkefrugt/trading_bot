# align_data_time.py

import pandas as pd
import numpy as np
import config

from calc_indicators import (
    compute_heikin_ashi,
    compute_ichimoku,
    compute_ema,
    extend_index,
    compute_bollinger_bands,
)

from get_data import extend_weekly_index
from math_helpers import smooth_savgol


def get_data_with_indicators_and_time_alignment():
    """
    Align daily + weekly data and compute indicators.
    Assumes daily and weekly data already exist in config.
    """

    # =========================
    # Fetch data from config
    # =========================
    daily = getattr(config, "daily_data", None)
    weekly_raw = getattr(config, "weekly_data", None)

    if daily is None or weekly_raw is None:
        raise RuntimeError(
            "Daily / weekly data missing in config.\n"
            "Fetch data in main.py before calling alignment."
        )

    # =========================
    # Prepare daily data
    # =========================
    data = daily.copy()
    data.columns = [f"D_{col}" for col in data.columns]

    # =========================
    # Daily EMAs
    # =========================
    for p in (9, 20, 50, 100, 200, 365):
        data[f"EMA_{p}"] = compute_ema(data, p)

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

    # =========================
    # Daily Bollinger Bands
    # =========================
    bb_daily = compute_bollinger_bands(data, period=20, std_dev=2, prefix="D_")
    data = pd.concat([data, bb_daily], axis=1)

    # =========================
    # Donchian Channels
    # =========================
    data["DC_Upper_365"] = data["D_High"].rolling(365).max()
    data["DC_Lower_365"] = data["D_Low"].rolling(365).min()
    data["DC_Middle_365"] = (data["DC_Upper_365"] + data["DC_Lower_365"]) / 2

    data["DC_Upper_26"] = data["D_High"].rolling(26).max()
    data["DC_Lower_26"] = data["D_Low"].rolling(26).min()
    data["DC_Middle_26"] = (data["DC_Upper_26"] + data["DC_Lower_26"]) / 2

    # =========================
    # Extend daily index (future cloud)
    # =========================
    future_days = 26 * 7
    data = extend_index(data, future_days=future_days)

    # =========================
    # Weekly Heikin-Ashi
    # =========================
    ha_weekly = getattr(config, "weekly_data_HA", None)
    if ha_weekly is None:
        ha_weekly = compute_heikin_ashi(weekly_raw, prefix="W_", weekly=True)

    ha_weekly_daily = ha_weekly.reindex(data.index, method="ffill")

    # =========================
    # Weekly raw → daily
    # =========================
    weekly_daily = weekly_raw.reindex(data.index, method="ffill")

    data = pd.concat([data, ha_weekly_daily, weekly_daily], axis=1)

    # =========================
    # Weekly Ichimoku
    # =========================
    ichimoku_weekly = getattr(config, "ichimoku_weekly", None)

    if ichimoku_weekly is None:
        weekly_extended = extend_weekly_index(weekly_raw)
        ichimoku_weekly = compute_ichimoku(weekly_extended, prefix="W_", weekly=True)
        config.ichimoku_weekly = ichimoku_weekly

    ichimoku_weekly_daily = ichimoku_weekly.reindex(data.index).interpolate(
        method="time"
    )

    data = pd.concat([data, ichimoku_weekly_daily], axis=1)

    # Mask weekly lines where daily data is missing
    if "W_Tenkan_sen" in data.columns:
        data["W_Tenkan_sen"] = data["W_Tenkan_sen"].where(data["D_Close"].notna())
    if "W_Kijun_sen" in data.columns:
        data["W_Kijun_sen"] = data["W_Kijun_sen"].where(data["D_Close"].notna())

    # Drop future Chikou values
    cutoff_days = 26 * 2 * 7
    cutoff_index = len(data) - cutoff_days
    if "W_Chikou_span" in data.columns and cutoff_index > 0:
        data.loc[data.index[cutoff_index:], "W_Chikou_span"] = np.nan

    # =========================
    # Daily Ichimoku
    # =========================
    ichimoku_daily = compute_ichimoku(data)
    data = pd.concat([data, ichimoku_daily], axis=1)

    return data
