#align_data_time.py

from calc_indicators import compute_heikin_ashi, compute_ichimoku, compute_ema, extend_index, compute_bollinger_bands
from get_data import extend_weekly_index, fetch_btc_weekly_data, fetch_btc_data
import pandas as pd
import numpy as np
import config


def get_data_with_indicators_and_time_alignment():
    # Fetch and prefix daily data
    data = fetch_btc_data()
    data.columns = [f"D_{col}" for col in data.columns]

    # Fetch and prefix weekly data
    weekly_raw = fetch_btc_weekly_data()
    weekly_raw.columns = [f"W_{col}" for col in weekly_raw.columns]

    # --- Daily indicators ---
    data['EMA_9'] = compute_ema(data, 9)
    data['EMA_20'] = compute_ema(data, 20)
    data['EMA_50'] = compute_ema(data, 50)
    data['EMA_100'] = compute_ema(data, 100)
    data['EMA_200'] = compute_ema(data, 200)
    data['EMA_365'] = compute_ema(data, 365)


    # Add Bollinger Bands (Daily)
    bb_daily = compute_bollinger_bands(data, period=20, std_dev=2, prefix="D_")
    data['D_BB_Middle_20'] = bb_daily['D_BB_Middle_20']
    data['D_BB_Upper_20'] = bb_daily['D_BB_Upper_20']
    data['D_BB_Lower_20'] = bb_daily['D_BB_Lower_20']
    data['D_BB_Width_20'] = bb_daily['D_BB_Width_20'] 
    
    period = 365
    data['DC_Upper_365'] = data['D_High'].rolling(window=period).max()
    data['DC_Lower_365'] = data['D_Low'].rolling(window=period).min()
    data['DC_Middle_365'] = (data['DC_Upper_365'] + data['DC_Lower_365']) / 2

    # Extend daily index by 182 days (26 weeks) for future Ichimoku cloud
    future_days = 26 * 7
    data = extend_index(data, future_days=future_days)


    # --- Heikin-Ashi (weekly) ---
    ha_weekly = compute_heikin_ashi(weekly_raw, weekly=True)
    ha_weekly_daily = ha_weekly.reindex(data.index, method='ffill')

    # Fill missing weekly values with forward fill
    weekly_daily = weekly_raw.reindex(data.index, method='ffill')

    data = pd.concat([data, ha_weekly_daily,weekly_daily], axis=1)

    # --- Weekly Ichimoku ---
    weekly_extended = extend_weekly_index(weekly_raw)
    config.ichimoku_weekly = compute_ichimoku(weekly_extended, weekly=True)
    ichimoku_weekly = config.ichimoku_weekly
    ichimoku_weekly_daily = ichimoku_weekly.reindex(data.index).interpolate(method='time')
    data = pd.concat([data, ichimoku_weekly_daily], axis=1)

    # Mask W_Tenkan and W_Kijun where daily data is missing
    data['W_Tenkan_sen'] = data['W_Tenkan_sen'].where(data['D_Close'].notna())
    data['W_Kijun_sen'] = data['W_Kijun_sen'].where(data['D_Close'].notna())

    # Drop future Chikou_span values
    cutoff_days = 26 * 2 * 7  # 364 days
    cutoff_index = len(data) - cutoff_days
    if 'W_Chikou_span' in data.columns and cutoff_index > 0:
        data.loc[data.index[cutoff_index:], 'W_Chikou_span'] = np.nan

    # --- Daily Ichimoku ---
    ichimoku_daily = compute_ichimoku(data)
    data = pd.concat([data, ichimoku_daily], axis=1)


    return data
