# trend/senb_consolidation.py

import numpy as np
import pandas as pd
import config
from kneed import KneeLocator

def find_senb_cliff(window, direction="decreasing"):
    if len(window) < 3:
        return None
    x = list(range(len(window)))
    y = window.values
    try:
        knee = KneeLocator(x, y, curve="convex", direction=direction)
        return knee.knee
    except Exception:
        return None



from scipy.signal import argrelextrema


def nearest_local_peak(series: pd.Series,
                       center_ts: pd.Timestamp,
                       window_days: int = 60,
                       order: int = 5) -> pd.Timestamp | None:
    """
    Find the nearest local maximum to center_ts within ±window_days
    using scipy.signal.argrelextrema.
    """
    if not isinstance(center_ts, pd.Timestamp):
        center_ts = pd.to_datetime(center_ts)

    if series.empty:
        return None

    # slice ±window_days
    start = center_ts - pd.Timedelta(days=window_days)
    end   = center_ts + pd.Timedelta(days=window_days)
    s = series.loc[start:end].dropna()
    if s.empty:
        return None

    # find local maxima
    arr = s.values
    idxs = argrelextrema(arr, np.greater, order=order)[0]

    if len(idxs) == 0:
        # fallback: highest point in the slice
        return s.idxmax()

    peak_times = s.iloc[idxs].index

    # choose nearest to center_ts (tie → highest value)
    deltas = np.abs((peak_times - center_ts).asi8)
    min_delta = deltas.min()
    candidates = peak_times[deltas == min_delta]
    if len(candidates) == 1:
        return candidates[0]
    else:
        return s.loc[candidates].idxmax()

def mark_senb_edge(data: pd.DataFrame, current_date: pd.Timestamp | str) -> pd.DataFrame:
    if not isinstance(current_date, pd.Timestamp):
        current_date = pd.to_datetime(current_date)

    w = config.ichimoku_weekly
    w_sen_A_fut  = w["W_Senkou_span_A"]
    w_sen_B_fut  = w["W_Senkou_span_B"]
    w_sen_B_pct  = w["W_Senkou_span_B_slope_pct"]

    anchor_weeks = 12
    rise_pos = w.index.get_loc(current_date)
    anchor_pos = max(1, rise_pos - anchor_weeks)

    back_trace_pos = anchor_pos
    start_pos = anchor_pos

    while back_trace_pos > 0:
        cur_senA  = w_sen_A_fut.iloc[back_trace_pos]
        cur_senB  = w_sen_B_fut.iloc[back_trace_pos]
        prev_senA = w_sen_A_fut.iloc[back_trace_pos - 1]
        prev_senB = w_sen_B_fut.iloc[back_trace_pos - 1]

        if (prev_senB > prev_senA) and (cur_senB >= cur_senA):
            start_pos = back_trace_pos
            break

        if w_sen_B_pct.iloc[back_trace_pos] > 1.0:
            start_pos = back_trace_pos
            break

        back_trace_pos -= 1

    start_week = w.index[start_pos]
    data.loc[start_week, "W_SenB_Consol_Start_SenB"] = True

    # price anchor 26w earlier → snap to nearest smoothed price peak within ±1 month
    aligned_pos = start_pos - 26
    if aligned_pos >= 0:
        aligned_week = w.index[aligned_pos]
        data.loc[aligned_week, "W_SenB_Consol_Start_Price"] = True

        smooth_col = "D_Close_smooth"
        if smooth_col in data.columns:
            peak_ts = nearest_local_peak(data[smooth_col], aligned_week,
                                        window_days=60, order=5)
            if peak_ts is not None:
                data.loc[peak_ts, "W_SenB_Consol_Start_Price_Adjusted"] = True

                # optional: if you only want the adjusted marker:
                # data.loc[aligned_week, "W_SenB_Consol_Start_Price"] = False

    return data
