import numpy as np
from signals.helpers.weekly_pivot_update import weekly_pivot_update
from signals.helpers.pivot_line_builder import build_pivot_trendlines


def get_pivot_levels(data, i, seq, check_interval=7):
    """
    Returns current pivot resistance and support levels at bar i.
    Updates pivot structure weekly and stores it in seq.helpers.
    """

    start_idx = seq.start_index
    end_ts = data.index[i]

    # ----------------------------------------------------------
    # Weekly structure update
    # ----------------------------------------------------------
    if i > 0 and i % check_interval == 0:

        data = weekly_pivot_update(data, start_idx, end_ts)

        segment = data.loc[start_idx:end_ts]
        y_segment = segment["D_Close"].values

        pivot_lows_ts = segment.index[segment["pivot_support_price"].notna()].tolist()
        pivot_highs_ts = segment.index[
            segment["pivot_resistance_price"].notna()
        ].tolist()

        pivot_lows = [segment.index.get_loc(ts) for ts in pivot_lows_ts]
        pivot_highs = [segment.index.get_loc(ts) for ts in pivot_highs_ts]

        support_line, resistance_line = build_pivot_trendlines(
            y_segment, pivot_lows, pivot_highs
        )

        if support_line is not None:
            seq.helpers["pivot_support_m"], seq.helpers["pivot_support_b"] = (
                support_line
            )

        if resistance_line is not None:
            seq.helpers["pivot_resistance_m"], seq.helpers["pivot_resistance_b"] = (
                resistance_line
            )

        seq.helpers["pivot_line_last_update_i"] = i

    # ----------------------------------------------------------
    # Evaluate line at current bar
    # ----------------------------------------------------------
    res_m = seq.helpers.get("pivot_resistance_m")
    res_b = seq.helpers.get("pivot_resistance_b")
    sup_m = seq.helpers.get("pivot_support_m")
    sup_b = seq.helpers.get("pivot_support_b")

    if res_m is None:
        return None, None

    x = data.loc[seq.start_index : end_ts].index.get_loc(end_ts)

    resistance_val = res_m * x + res_b
    support_val = None

    if sup_m is not None:
        support_val = sup_m * x + sup_b

    return resistance_val, support_val
