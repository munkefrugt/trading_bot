# trend/senb_consolidation.py (ultra-simple)

import pandas as pd
import config
from kneed import KneeLocator

def find_senb_cliff(window, direction="decreasing"):
    """
    Detects the 'cliff point' in a SenB window (steep → flat change).
    Returns the index inside the window, or None if nothing found.
    """
    if len(window) < 3:  # need at least 3 points
        return None

    x = list(range(len(window)))
    y = window.values

    try:
        knee = KneeLocator(x, y, curve="convex", direction=direction)
        return knee.knee
    except Exception:
        return None

def mark_senb_edge_simple(
    data: pd.DataFrame,
    current_date: pd.Timestamp | str
    
)-> pd.DataFrame:

    if not isinstance(current_date, pd.Timestamp):
        current_date = pd.to_datetime(current_date)

    w = config.ichimoku_weekly
    #senb_col = "W_Senkou_span_B_future" if use_future_span else "W_Senkou_span_B"
    w_sen_A_fut  = w["W_Senkou_span_A"]
    w_sen_B_fut = w["W_Senkou_span_B"]
    anchor_weeks = 12
    rise_pos = w.index.get_loc(current_date)
    
    anchor_pos = max(1, rise_pos- anchor_weeks)


 
    back_trace_pos = anchor_pos
    start_pos = anchor_pos  
    # backtrace from anchor to find dropoff point. 
    while  back_trace_pos > 0:
        cur_senA = w_sen_A_fut.iloc[back_trace_pos]
        cur_senB = w_sen_B_fut.iloc[back_trace_pos]
        prev_senA = w_sen_A_fut.iloc[back_trace_pos -1]
        prev_senB = w_sen_B_fut.iloc[back_trace_pos -1]
        # senB / A cross
        if (prev_senB > prev_senA) and (cur_senB >= cur_senA):
            start_pos = back_trace_pos
            break
        # did senB make breakout down witin the last 5 weeks?
        lb = 6  # lookback window
        win_start = max(0, back_trace_pos - lb)
        window = w_sen_B_fut.iloc[win_start:back_trace_pos+1]

        cliff_idx = find_senb_cliff(window, direction="decreasing")
        if cliff_idx is not None:
            start_pos = win_start + cliff_idx
            break

        
        
        back_trace_pos -= 1
        


    start_week = w.index[start_pos]
    data.loc[start_week, "W_SenB_Consol_Start_SenB"] = True

    # mark price 26w earlier
    aligned_pos = start_pos - 26
    if aligned_pos >= 0:
        aligned_week = w.index[aligned_pos]
        data.loc[aligned_week, "W_SenB_Consol_Start_Price"] = True

    return data
