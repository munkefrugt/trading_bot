
from analyse import compute_ema, extend_index
from analyse import compute_heikin_ashi, compute_ichimoku
from get_data import extend_weekly_index, fetch_btc_weekly_data,fetch_btc_data
import pandas as pd
import numpy as np

def get_data_with_indicators_and_time_alignment():
    data = fetch_btc_data()
    weekly = fetch_btc_weekly_data()

    # Daily indicators
    data['EMA_20'] = compute_ema(data, 20)
    data['EMA_50'] = compute_ema(data, 50)
    data['EMA_200'] = compute_ema(data, 200)

    period = 365
    data['DC_Upper_365'] = data['High'].rolling(window=period).max()
    data['DC_Lower_365'] = data['Low'].rolling(window=period).min()
    data['DC_Middle_365'] = (data['DC_Upper_365'] + data['DC_Lower_365']) / 2


    # Extend daily index by 182 days (26 weeks) for future Ichimoku cloud
    future_days = 26 * 7
    data = extend_index(data, future_days=future_days)

    # Compute and reindex Heikin-Ashi weekly to daily
    ha_weekly = compute_heikin_ashi(weekly).add_prefix('W_HA_')
    ha_weekly_daily = ha_weekly.reindex(data.index, method='ffill')
    data = pd.concat([data, ha_weekly_daily], axis=1)

    # Compute weekly Ichimoku and reindex to daily
    weekly = extend_weekly_index(weekly)
    ichimoku_weekly = compute_ichimoku(weekly).add_prefix('W_')
    ichimoku_weekly_daily = ichimoku_weekly.reindex(data.index).interpolate(method='time')
    data = pd.concat([data, ichimoku_weekly_daily], axis=1)
    data['W_Tenkan_sen'] = data['W_Tenkan_sen'].where(data['Close'].notna())
    data['W_Kijun_sen'] = data['W_Kijun_sen'].where(data['Close'].notna())
    cutoff_days = 26 * 2 * 7  # 364 days
    cutoff_index = len(data) - cutoff_days

    if 'W_Chikou_span' in data.columns and cutoff_index > 0:
        data.loc[data.index[cutoff_index:], 'W_Chikou_span'] = np.nan


    # Daily Ichimoku (after extending)
    ichimoku_daily = compute_ichimoku(data).add_prefix('D_')
    data = pd.concat([data, ichimoku_daily], axis=1)

    return data
