# trend/count_cross_regline.py
import numpy as np
import pandas as pd

def count_regline_crosses_consolidation(
    df: pd.DataFrame,
    price_col: str = "EMA_50",
    line_col: str = "Regline_from_last_adjusted",
    flag_col: str = "W_SenB_Consol_Start_Price_Adjusted",
    end_index: int | None = None,
) -> int:
    """
    Deterministic cross counter (no fancy tolerance).
    Starts at the latest True in flag_col (<= end_index), then walks bar-by-bar.
    Writes:
      - Regline_cross_event (bool) : True only on bars where a cross happens
      - Regline_cross_count (int)  : 1..N on those bars, 0 elsewhere
    Returns total cross count up to end_index.
    """
    n = len(df)
    if n == 0:
        return 0
    if end_index is None:
        end_index = n - 1
    end_index = int(max(0, min(end_index, n - 1)))

    # find start at latest consolidation flag
    flags = df.get(flag_col)
    if flags is None:
        start = 0
    else:
        idx = np.flatnonzero(flags.astype(bool).fillna(False).to_numpy()[: end_index + 1])
        start = int(idx[-1]) if idx.size else 0

    # init outputs (overwrite each call for simplicity)
    df["Regline_cross_event"] = False
    df["Regline_cross_count"] = 0

    # find first valid row (non-NaN pair)
    i = start
    while i <= end_index:
        p = df.iloc[i][price_col]
        l = df.iloc[i][line_col]
        if pd.notna(p) and pd.notna(l):
            break
        i += 1
    if i > end_index:
        return 0

    # initial state
    prev_p = df.iloc[i][price_col]
    prev_l = df.iloc[i][line_col]
    above = bool(prev_p > prev_l)
    crosses = 0
    i += 1

    # walk forward
    while i <= end_index:
        p = df.iloc[i][price_col]
        l = df.iloc[i][line_col]
        if pd.isna(p) or pd.isna(l):
            i += 1
            continue

        if above:
            # look for down-cross: yesterday strictly above AND today <= line
            if (prev_p > prev_l) and (p <= l):
                crosses += 1
                df.at[df.index[i], "Regline_cross_event"] = True
                df.at[df.index[i], "Regline_cross_count"] = crosses
                above = False
        else:
            # look for up-cross: yesterday strictly below AND today >= line
            if (prev_p < prev_l) and (p >= l):
                crosses += 1
                df.at[df.index[i], "Regline_cross_event"] = True
                df.at[df.index[i], "Regline_cross_count"] = crosses
                above = True

        prev_p, prev_l = p, l
        i += 1

    return crosses
