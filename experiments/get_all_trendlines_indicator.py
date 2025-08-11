#get_all_trendlines_indicator.py
import pandas as pd
import numpy as np
from prophet import Prophet

def smooth_series(series, window):
    """Centered rolling mean smoothing."""
    return series.rolling(window=window, center=True).mean()

def get_all_trendlines(data, price_col="D_Close", debug=False):
    """
    Run Prophet annually with 2-year lookback, average overlaps,
    smooth the result, compute smoothed derivatives, and mark elbows.
    """
    data = data.copy()
    data['Prophet_Trend'] = np.nan
    data['Prophet_Slope'] = np.nan
    data['Prophet_Acceleration'] = np.nan
    data['Elbow'] = False
    data['Segment_ID'] = np.nan

    n = len(data)

    # Arrays to store summed predictions and counts for averaging
    trend_sum = np.zeros(n)
    trend_count = np.zeros(n)

    # --- Step 1: Prophet every year with 2-year window ---
    for start in range(0, n, 365):  
        window_start = max(0, start - 365)
        window_end = min(n, start + 365)
        df_window = data.iloc[window_start:window_end]

        prophet_input = pd.DataFrame({'ds': df_window.index, 'y': df_window[price_col].values})
        model = Prophet(daily_seasonality=True)
        model.fit(prophet_input)
        forecast = model.predict(model.make_future_dataframe(periods=0))
        trend = pd.Series(forecast['yhat'].values, index=df_window.index)

        # Add predictions into sum and count arrays
        for i, date in enumerate(df_window.index):
            idx = data.index.get_loc(date)
            trend_sum[idx] += trend.iloc[i]
            trend_count[idx] += 1

        if debug:
            print(f"Processed window: {df_window.index[0].date()} to {df_window.index[-1].date()}")

    # --- Step 2: Average overlapping predictions ---
    averaged_trend = trend_sum / np.where(trend_count == 0, 1, trend_count)
    data['Prophet_Trend'] = averaged_trend

    # --- Step 3: Smooth trend ---
    data['Prophet_Trend'] = smooth_series(data['Prophet_Trend'], 15)

    # --- Step 4: Compute smoothed slope and acceleration ---
    slope = data['Prophet_Trend'].diff()
    slope = smooth_series(slope, window=7)  # smooth slope
    data['Prophet_Slope'] = slope

    acceleration = slope.diff()
    acceleration = smooth_series(acceleration, window=5)  # smooth acceleration
    data['Prophet_Acceleration'] = acceleration

    # --- Step 5: Find elbows (filtered zero-crossings) ---
    min_slope_change = np.nanstd(slope) * 0.5  # require meaningful slope change
    zero_crossings = np.where(
        (np.sign(acceleration) != np.sign(acceleration.shift())) &
        (np.abs(slope) > min_slope_change)
    )[0]
    elbow_indices = [i for i in zero_crossings if not np.isnan(acceleration[i])]

    data.loc[data.index[elbow_indices], 'Elbow'] = True

    # --- Step 6: Assign segment IDs ---
    seg_id = 0
    for i in range(len(data)):
        if data['Elbow'].iloc[i]:
            seg_id += 1
        data.loc[data.index[i], 'Segment_ID'] = seg_id

    return data
