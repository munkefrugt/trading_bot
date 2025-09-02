# trend/flatness.py
import pandas as pd
import numpy as np
from typing import Optional

def calc_flatness_from_last_adjusted_start(
    data: pd.DataFrame,
    current_index: int | pd.Timestamp,
    y_col: str = "D_Close",
    flag_col: str = "W_SenB_Consol_Start_Price_Adjusted",
    min_points: int = 5,
) -> Optional[float]:
    """
    Calculate flatness ratio (std/mean) of y_col between the last True flag
    and current_index. Lower = flatter.
    Returns None if not enough points or invalid mean.
    """
    if y_col not in data.columns or flag_col not in data.columns:
        return None

    idx = data.index
    end_pos = current_index if isinstance(current_index, int) else idx.get_loc(current_index)

    flags = data[flag_col].fillna(False).astype(bool)
    eligible = flags.iloc[: end_pos + 1]
    if not eligible.any():
        return None

    start_label = eligible[eligible].index[-1]
    start_pos = idx.get_loc(start_label)

    window = data[y_col].iloc[start_pos : end_pos + 1].astype(float).dropna()
    if len(window) < min_points or window.mean() == 0:
        return None

    return float(window.std() / window.mean())
