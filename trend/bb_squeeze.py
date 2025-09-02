# trend/bb_squeeze.py
import pandas as pd
import numpy as np
from typing import Optional, Tuple

def check_bb_squeeze(
    w: pd.DataFrame,
    current_index: int | pd.Timestamp,
    lookback: int = 52,  # 1 year of weekly data
    upper_col: str = "W_BB_Upper_20",
    lower_col: str = "W_BB_Lower_20",
    mid_col: str = "W_BB_Middle_20",
    out_bandwidth: str = "W_BB_Bandwidth",
    out_percentile: str = "W_BB_SqueezePercentile",
) -> Tuple[pd.DataFrame, Optional[float], Optional[float]]:
    """
    Compute Bollinger Band squeeze metrics at current_index.

    - Bandwidth = (upper - lower) / middle
    - Percentile = rank of current bandwidth vs past lookback

    Returns updated df, bandwidth, percentile (0..1).
    """
    if not {upper_col, lower_col, mid_col} <= set(w.columns):
        return w, None, None

    idx = w.index
    pos = current_index if isinstance(current_index, int) else idx.get_loc(current_index)

    if pos < lookback:
        return w, None, None

    upper = w[upper_col].iloc[pos]
    lower = w[lower_col].iloc[pos]
    mid   = w[mid_col].iloc[pos]

    if pd.isna(upper) or pd.isna(lower) or pd.isna(mid) or mid == 0:
        return w, None, None

    # raw bandwidth
    bandwidth = (upper - lower) / mid

    # relative squeeze percentile
    history = ((w[upper_col] - w[lower_col]) / w[mid_col]).iloc[pos - lookback: pos+1].dropna()
    if history.empty:
        return w, bandwidth, None

    rank = (history <= bandwidth).sum()
    percentile = rank / len(history)

    # store in df
    if out_bandwidth not in w.columns:
        w[out_bandwidth] = np.nan
    if out_percentile not in w.columns:
        w[out_percentile] = np.nan

    w.at[idx[pos], out_bandwidth] = bandwidth
    w.at[idx[pos], out_percentile] = percentile

    return w, float(bandwidth), float(percentile)
