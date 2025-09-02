# trend/regression_line.py
import numpy as np
import pandas as pd
from typing import Tuple, Optional

def build_regression_from_last_adjusted_start(
    data: pd.DataFrame,
    current_index: int | pd.Timestamp,
    y_col_primary: str = "W_Tenkan_sen",
    y_col_fallback: str = "D_Close",
    out_col: str = "Regline_from_last_adjusted",
    flag_col: str = "W_SenB_Consol_Start_Price_Adjusted",
    r2_col: str = "r_2_values_for_regline",   # <— NEW
    min_points: int = 5,
) -> Tuple[pd.DataFrame, Optional[float]]:
    y_col = y_col_primary if y_col_primary in data.columns else y_col_fallback
    if y_col not in data.columns or flag_col not in data.columns:
        return data, None

    idx = data.index
    end_pos = current_index if isinstance(current_index, int) else idx.get_loc(current_index)

    flags = data[flag_col].fillna(False).astype(bool)
    eligible = flags.iloc[: end_pos + 1]
    if not eligible.any():
        return data, None

    start_label = eligible[eligible].index[-1]
    start_pos = idx.get_loc(start_label)

    y = data[y_col].iloc[start_pos : end_pos + 1].astype(float).copy()
    x = np.arange(len(y), dtype=float)

    valid = y.dropna()
    if len(valid) < min_points:
        return data, None

    mask_valid = y.notna().values
    x_valid = x[mask_valid]
    y_valid = y[mask_valid].values

    a, b = np.polyfit(x_valid, y_valid, deg=1)
    fitted = a * x + b

    # R²
    y_hat_valid = a * x_valid + b
    ss_res = np.sum((y_valid - y_hat_valid) ** 2)
    ss_tot = np.sum((y_valid - np.mean(y_valid)) ** 2)
    r2 = None if ss_tot == 0 else float(1.0 - (ss_res / ss_tot))

    # ensure cols
    if out_col not in data.columns:
        data[out_col] = np.nan
    if r2_col not in data.columns:
        data[r2_col] = np.nan

    # write fitted line across span
    span = idx[start_pos : end_pos + 1]
    data.loc[span, out_col] = fitted

    # mark start/end
    data.loc[start_label, f"{out_col}_Start"] = True
    data.loc[idx[end_pos], f"{out_col}_End"] = True

    # write R² ONLY at the day we computed it
    data.loc[idx[end_pos], r2_col] = np.nan if r2 is None else r2

    return data, r2
