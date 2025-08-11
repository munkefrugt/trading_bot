#trend_channel_buy_helper.py
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from scipy.signal import argrelextrema, find_peaks

def find_confirmed_extrema(y, order=3):
    """Identify confirmed highs/lows with required confirmation window."""
    values = y.values
    length = len(values)
    maxima = argrelextrema(values, np.greater_equal, order=order)[0]
    minima = argrelextrema(values, np.less_equal, order=order)[0]
    maxima = [idx for idx in maxima if order <= idx < length - order]
    minima = [idx for idx in minima if order <= idx < length - order]
    return maxima, minima


def compute_latest_trend_channel(data, i, debug=False):
    """
    Compute latest trend channel & breakout check using Prophet over a 2-year window.
    Always stores the latest segment's channel lines in `data` for plotting.

    Returns:
        data (pd.DataFrame): with added 'Channel_Top', 'Channel_Bottom', 'Channel_Breakout'.
        breakout (bool): True if breakout detected at current index.
    """
    current_date = data.index[i]
    lookback_start = current_date - pd.Timedelta(days=730)  # 2-year lookback
    df_slice = data[(data.index >= lookback_start) & (data.index <= current_date)].copy()

    # Ensure storage columns exist
    if 'Channel_Top' not in data.columns:
        data['Channel_Top'] = np.nan
    if 'Channel_Bottom' not in data.columns:
        data['Channel_Bottom'] = np.nan
    if 'Channel_Breakout' not in data.columns:
        data['Channel_Breakout'] = None

    if len(df_slice) < 200:
        if debug: print(f"[{current_date}] Skipped: insufficient 2y history ({len(df_slice)} bars).")
        return data, False

    # === 1) Prophet trend fitting ===
    btc = pd.DataFrame({'ds': df_slice.index, 'y': df_slice['D_Close'].values})
    model = Prophet(daily_seasonality=True)
    model.fit(btc)
    forecast = model.predict(model.make_future_dataframe(periods=0))
    btc['trend'] = forecast['yhat'].values

    # === 2) Slope & acceleration ===
    btc['trend_smooth'] = btc['trend'].rolling(window=15, center=True).mean()
    btc['slope'] = btc['trend_smooth'].diff()
    btc['slope_smooth'] = btc['slope'].rolling(window=5, center=True).mean()
    btc['acceleration'] = btc['slope_smooth'].diff()

    # === 3) Detect elbows ===
    elbows, _ = find_peaks(np.abs(btc['acceleration']),
                           height=np.nanstd(btc['acceleration']) * 1.2,
                           distance=20)
    btc['segment'] = 0
    for j, idx in enumerate(elbows):
        btc.loc[idx:, 'segment'] = j + 1

    # === 4) Last segment ===
    last_seg_id = btc['segment'].iloc[-1]
    seg_df = btc[btc['segment'] == last_seg_id].copy()

    duration_days = (seg_df['ds'].iloc[-1] - seg_df['ds'].iloc[0]).days
    if duration_days < 30 or len(seg_df) < 20:
        if debug: print(f"[{current_date}] Skipped: segment too short ({duration_days}d).")
        return data, False

    # === 5) Extrema & regression ===
    maxima, minima = find_confirmed_extrema(seg_df['y'])
    if len(maxima) < 2 and len(minima) < 2:
        if debug: print(f"[{current_date}] No valid extrema (max={len(maxima)}, min={len(minima)}).")
        return data, False

    x = np.arange(len(seg_df)).reshape(-1, 1)
    y = seg_df['y'].values
    reg = LinearRegression().fit(x, y)
    base = reg.predict(x)
    residuals = y - base

    if len(maxima) >= 2:
        top_outer = base + max(residuals[m] for m in maxima)
    else:
        top_outer = np.full_like(base, np.nan)

    if len(minima) >= 2:
        bottom_outer = base + min(residuals[m] for m in minima)
    else:
        bottom_outer = np.full_like(base, np.nan)

    # === 6) Store latest segment channel in main DF ===
    # Map segment dates to main data index
    for date, top_val, bot_val in zip(seg_df['ds'], top_outer, bottom_outer):
        if date in data.index:  # ensure alignment
            data.at[date, 'Channel_Top'] = top_val
            data.at[date, 'Channel_Bottom'] = bot_val
            
    # === 7) Breakout detection ===
    close_now = data['D_Close'].iloc[i]
    top_now = data['Channel_Top'].iloc[i]
    bottom_now = data['Channel_Bottom'].iloc[i]
    breakout = False

    if not np.isnan(top_now) and close_now > top_now:
        data.loc[data.index[i], 'Channel_Breakout'] = 'up'
        breakout = True
        if debug: print(f"[{current_date}] ✅ Breakout UP: Close={close_now:.2f} > Top={top_now:.2f}")
    elif not np.isnan(bottom_now) and close_now < bottom_now:
        data.loc[data.index[i], 'Channel_Breakout'] = 'down'
        if debug: print(f"[{current_date}] ⚠️ Breakout DOWN: Close={close_now:.2f} < Bottom={bottom_now:.2f}")
    else:
        data.loc[data.index[i], 'Channel_Breakout'] = None
        if debug: print(f"[{current_date}] Price inside channel: Close={close_now:.2f}")

    return data, breakout
