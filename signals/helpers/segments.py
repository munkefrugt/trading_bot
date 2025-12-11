# signals/helpers/segments.py
import pandas as pd


def get_segment_bounds(data: pd.DataFrame, i: int, end_offset_days: int = 1):
    """
    Returns (start_idx, end_idx) for the consolidation segment ending at row i.
    """

    # --- Find start ---
    mask = data.loc[: data.index[i], "W_SenB_Consol_Start_Price"] == True
    if not mask.any():
        return None, None

    start_idx = mask[mask].index[-1]

    # --- Compute end ---
    ts_i = data.index[i]
    ts_end_target = ts_i - pd.Timedelta(days=end_offset_days)

    end_pos = data.index.get_indexer([ts_end_target], method="pad")
    if end_pos[0] == -1:
        return None, None

    end_idx = data.index[end_pos[0]]

    if start_idx >= end_idx:
        return None, None

    return start_idx, end_idx
