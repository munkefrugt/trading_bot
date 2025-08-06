import pandas as pd
import numpy as np
from prophet import Prophet
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

def smooth_series(series, window):
    """Centered rolling mean smoothing."""
    return series.rolling(window=window, center=True).mean()

def find_elbows_from_trend(trend, threshold_factor=1.2, distance=20):
    """
    Detect elbows purely from Prophet trend curvature (second derivative peaks).
    """
    slope = trend.diff()
    slope_smooth = smooth_series(slope, 5)
    acceleration = slope_smooth.diff()

    std_acc = np.nanstd(acceleration)
    elbows, _ = find_peaks(np.abs(acceleration), height=std_acc * threshold_factor, distance=distance)
    return elbows, acceleration

def merge_elbow_clusters(elbows, acceleration, min_gap=30):
    """Merge elbow points that are too close, keeping the strongest (highest |accel|)."""
    if len(elbows) == 0:
        return []

    merged = []
    cluster = [elbows[0]]

    for e in elbows[1:]:
        if e - cluster[-1] <= min_gap:
            cluster.append(e)
        else:
            best = max(cluster, key=lambda idx: abs(acceleration[idx]))
            merged.append(best)
            cluster = [e]

    # finalize last cluster
    best = max(cluster, key=lambda idx: abs(acceleration[idx]))
    merged.append(best)
    return merged

def get_all_trendlines(data, price_col="D_Close", debug=False, plot_debug=False):
    """
    Generate Prophet trendlines & elbows across dataset in 2-year chunks.
    Adds continuous 'Prophet_Trend' and elbow markers.
    """
    data = data.copy()
    data['Prophet_Trend'] = np.nan
    data['Elbow'] = False
    data['Segment_ID'] = np.nan

    step_back = int(0.2 * 365)   # ~20% overlap
    window_days = 730
    seg_id = 0
    start_idx = 0

    while True:
        end_idx = start_idx + window_days
        if end_idx > len(data):
            break

        df_slice = data.iloc[start_idx:end_idx].copy()
        prophet_input = pd.DataFrame({'ds': df_slice.index, 'y': df_slice[price_col].values})
        model = Prophet(daily_seasonality=True)
        model.fit(prophet_input)
        forecast = model.predict(model.make_future_dataframe(periods=0))
        trend = pd.Series(forecast['yhat'].values, index=df_slice.index)

        trend_smooth = smooth_series(trend, 15)
        elbows, accel = find_elbows_from_trend(trend_smooth)
        elbows = merge_elbow_clusters(elbows, accel, min_gap=30)

        # assign continuously
        data.loc[df_slice.index, 'Prophet_Trend'] = trend_smooth.values
        data.loc[df_slice.index, 'Segment_ID'] = seg_id + 1
        for e in elbows:
            data.loc[df_slice.index[e], 'Elbow'] = True

        if debug:
            print(f"{df_slice.index[0].date()} to {df_slice.index[-1].date()} -> {len(elbows)} elbows")

        if plot_debug:
            plt.figure(figsize=(12,5))
            plt.plot(trend_smooth, label='Smoothed Trend', color='orange')
            plt.plot(accel, label='Acceleration (2nd Derivative)', color='purple')
            plt.scatter(trend_smooth.index[elbows], trend_smooth.iloc[elbows], color='red', label='Elbows')
            plt.axhline(y=np.nanstd(accel)*1.2, color='gray', linestyle='--', label='Threshold')
            plt.legend()
            plt.title(f"Debug Segment: {df_slice.index[0].date()} - {df_slice.index[-1].date()}")
            plt.show()

        seg_id += 1

        if len(elbows) > 0:
            last_elbow_idx = elbows[-1] + start_idx
            start_idx = max(0, last_elbow_idx - step_back)
        else:
            start_idx += 365

    # Final 2 years (continuous)
    final_idx = max(0, len(data) - window_days)
    df_final = data.iloc[final_idx:].copy()
    prophet_input_final = pd.DataFrame({'ds': df_final.index, 'y': df_final[price_col].values})
    model_final = Prophet(daily_seasonality=True)
    model_final.fit(prophet_input_final)
    forecast_final = model_final.predict(model_final.make_future_dataframe(periods=0))
    trend_final = pd.Series(forecast_final['yhat'].values, index=df_final.index)
    trend_smooth_final = smooth_series(trend_final, 15)
    elbows_final, accel_final = find_elbows_from_trend(trend_smooth_final)
    elbows_final = merge_elbow_clusters(elbows_final, accel_final, min_gap=30)

    data.loc[df_final.index, 'Prophet_Trend'] = trend_smooth_final.values
    data.loc[df_final.index, 'Segment_ID'] = seg_id + 1
    for e in elbows_final:
        data.loc[df_final.index[e], 'Elbow'] = True

    # Ensure continuous line (fill small gaps caused by smoothing)
    data['Prophet_Trend'] = data['Prophet_Trend'].interpolate().ffill()

    return data
