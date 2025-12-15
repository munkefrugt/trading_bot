import numpy as np
import pandas as pd

from signals.helpers.segments import get_segment_bounds
from signals.helpers.weekly_pivot_update import weekly_pivot_update
from signals.helpers.pivot_line_builder import build_pivot_trendlines


def trendline_crossings(data: pd.DataFrame, i: int, seq) -> bool:
    """
    Detect breakout via dominant pivot resistance line.
    Pivot structure (m, b) is stored in SignalSequence (state).
    Pivot lines written to data are for plotting/debugging ONLY.
    """

    # ----------------------------------------------------------
    # 1) Consolidation segment
    # ----------------------------------------------------------
    start_idx, end_idx = get_segment_bounds(
        data, i, start_offset_days=20, end_offset_days=1
    )
    if start_idx is None:
        return False

    end_ts = data.index[i]
    check_interval = 7

    # ----------------------------------------------------------
    # 2) Weekly pivot STRUCTURE update (authority)
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
    # 3) Evaluate dominance EVERY BAR (logic)
    # ----------------------------------------------------------
    res_m = seq.helpers.get("pivot_resistance_m")
    res_b = seq.helpers.get("pivot_resistance_b")

    if res_m is None:
        return False

    x = data.loc[start_idx:end_ts].index.get_loc(end_ts)
    price = data.iloc[i]["D_Close"]
    resistance_val = res_m * x + res_b

    if price > resistance_val:
        seq.helpers["trendline_crossings_count"] += 1
    else:
        seq.helpers["trendline_crossings_count"] = 0

    # ----------------------------------------------------------
    # 4) Breakout condition
    # ----------------------------------------------------------
    if seq.helpers["trendline_crossings_count"] >= 2:
        seq.states_dict["trendline_crossings"] = True
        breakout = True
    else:
        breakout = False

    # ----------------------------------------------------------
    # 5) OPTIONAL: write pivot lines to data (PLOTTING ONLY)
    # ----------------------------------------------------------
    seg_idx = data.loc[start_idx:end_ts].index
    x_vals = np.arange(len(seg_idx))

    # --- Resistance line ---
    if res_m is not None:
        data.loc[start_idx:end_ts, "pivot_resistance_line"] = res_m * x_vals + res_b

    # --- Support line ---
    sup_m = seq.helpers.get("pivot_support_m")
    sup_b = seq.helpers.get("pivot_support_b")

    if sup_m is not None:
        data.loc[start_idx:end_ts, "pivot_support_line"] = sup_m * x_vals + sup_b

    return breakout
