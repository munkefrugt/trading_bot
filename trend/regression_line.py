# trend/regression_line.py
import numpy as np
import pandas as pd

def build_regression_from_last_adjusted_start(
    data: pd.DataFrame,
    current_index: int | pd.Timestamp,
    y_col_primary: str = "D_Close",
    y_col_fallback: str = "D_Close",
    out_col: str = "Regline_from_last_adjusted",
    flag_col: str = "W_SenB_Consol_Start_Price_Adjusted",
    min_points: int = 5,  # lower to ensure we actually draw something
) -> pd.DataFrame:
    y_col = y_col_primary if y_col_primary in data.columns else y_col_fallback
    if y_col not in data.columns or flag_col not in data.columns:
        return data

    idx = data.index
    end_pos = current_index if isinstance(current_index, int) else idx.get_loc(current_index)

    flags = data[flag_col].fillna(False).astype(bool)
    eligible = flags.iloc[: end_pos + 1]
    if not eligible.any():
        return data

    start_label = eligible[eligible].index[-1]
    start_pos = idx.get_loc(start_label)

    y = data[y_col].iloc[start_pos : end_pos + 1].astype(float).copy()
    x = np.arange(len(y), dtype=float)

    valid = y.dropna()
    if len(valid) < min_points:
        return data

    mask_valid = y.notna().values
    x_valid = x[mask_valid]
    y_valid = y[mask_valid].values

    a, b = np.polyfit(x_valid, y_valid, deg=1)  # OLS
    fitted = a * x + b  # <-- write across the whole span so it’s visible

    if out_col not in data.columns:
        data[out_col] = np.nan

    data.loc[idx[start_pos : end_pos + 1], out_col] = fitted
    # optional start/end markers:
    data.loc[start_label, f"{out_col}_Start"] = True
    data.loc[idx[end_pos], f"{out_col}_End"] = True
    return data
