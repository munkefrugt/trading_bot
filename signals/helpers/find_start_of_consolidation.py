# helpers/signals/find_start_of_consolidation.py

import pandas as pd

SLOPE_COL = "W_Senkou_span_B_slope_pct"
SLOPE_ABS_THRESHOLD = 2.0  # %


def find_start_of_consolidation(data: pd.DataFrame, i: int, seq) -> bool:
    """
    Find and lock the start of a consolidation phase for this SignalSequence.

    Logic:
    - Walk backward from i until |W_Senkou_span_B_slope_pct| > threshold
    - Mark that point as SenB consolidation start
    - Anchor a price-based start ~26 calendar weeks earlier (snap backward)
    - Fallback: highest D_Close_smooth 3–12 months back

    Fires ONCE per sequence and then returns True forever for that seq.
    """

    # Already locked for this sequence → advance immediately
    if getattr(seq, "consolidation_start_index", None) is not None:
        return True

    if i <= 0 or i >= len(data) or SLOPE_COL not in data.columns:
        return False

    j = i
    candidate_idx = None
    candidate_val = -float("inf")

    while j > 0:
        slope = data.at[data.index[j], SLOPE_COL]

        # --- Track fallback candidate (price-based) ---
        if "D_Close_smooth" in data.columns:
            close_smooth = data.at[data.index[j], "D_Close_smooth"]
            weeks_back = (data.index[i] - data.index[j]).days / 7

            if (
                weeks_back >= 12
                and pd.notna(close_smooth)
                and close_smooth > candidate_val
            ):
                candidate_val = close_smooth
                candidate_idx = data.index[j]

        # --- Primary SenB slope break detection ---
        if pd.notna(slope) and abs(slope) > SLOPE_ABS_THRESHOLD:
            time_senb_rise = data.index[j]
            data.loc[time_senb_rise, "W_SenB_Consol_Start_SenB"] = True

            # Anchor ~26 calendar weeks earlier (snap backward)
            anchor_time_target = time_senb_rise - pd.Timedelta(weeks=26)
            idx = data.index.get_indexer([anchor_time_target], method="pad")

            if idx.size and idx[0] != -1:
                seg_start_idx = idx[0]
                seg_start_time = data.index[seg_start_idx]
                data.loc[seg_start_time, "W_SenB_Consol_Start_Price"] = True
                seq.consolidation_start_index = seg_start_idx

            return True  # ✅ COMMIT

        j -= 1

    # === Fallback: no SenB slope break found ===
    if candidate_idx is not None:
        delta = data.index[i] - candidate_idx
        if pd.Timedelta(weeks=12) <= delta <= pd.Timedelta(weeks=52):
            data.loc[candidate_idx, "W_SenB_Consol_Start_Price"] = True
            seq.consolidation_start_index = data.index.get_loc(candidate_idx)
            return True  # ✅ COMMIT

    return False
