# signals/helpers/segments.py
import pandas as pd


def get_segment_bounds(
    data: pd.DataFrame,
    i: int,
    start_offset_days: int = 10,
    end_offset_days: int = 1,
):
    """
    Returns (start_idx, end_idx) for the consolidation segment.
    start_offset_days lets you begin the segment *before* the actual
    W_SenB_Consol_Start_Price to get more context for pivot + trendline building.
    """

    # --------------------------------------
    # 1) Find the true consolidation anchor
    # --------------------------------------
    mask = data.loc[: data.index[i], "W_SenB_Consol_Start_Price"] == True
    if not mask.any():
        return None, None

    true_start_idx = mask[mask].index[-1]

    # --------------------------------------
    # 2) Move start earlier by offset days
    # --------------------------------------
    ts_true_start = true_start_idx
    ts_start_target = ts_true_start - pd.Timedelta(days=start_offset_days)

    start_pos = data.index.get_indexer([ts_start_target], method="pad")
    if start_pos[0] == -1:
        start_idx = true_start_idx  # fallback
    else:
        start_idx = data.index[start_pos[0]]

    # --------------------------------------
    # 3) Compute end boundary
    # --------------------------------------
    ts_i = data.index[i]
    ts_end_target = ts_i - pd.Timedelta(days=end_offset_days)

    end_pos = data.index.get_indexer([ts_end_target], method="pad")
    if end_pos[0] == -1:
        return None, None

    end_idx = data.index[end_pos[0]]

    # sanity
    if start_idx >= end_idx:
        return None, None

    return start_idx, end_idx
