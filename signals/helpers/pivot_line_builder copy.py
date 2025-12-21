# signals/helpers/pivot_line_builder.py
import numpy as np
from signals.trendline_maker.trendline_builder import best_pivot_trendline


def build_pivot_trendlines(data, start_idx, end_ts, seq):
    """
    Build dominant pivot support + resistance lines from detected pivots
    and store them in seq.helpers.
    """

    segment = data.loc[start_idx:end_ts]
    y_raw = segment["D_Close"].values

    pivot_lows_ts = segment.index[segment["pivot_support_price"].notna()].tolist()
    pivot_highs_ts = segment.index[segment["pivot_resistance_price"].notna()].tolist()

    pivot_lows = [segment.index.get_loc(ts) for ts in pivot_lows_ts]
    pivot_highs = [segment.index.get_loc(ts) for ts in pivot_highs_ts]

    n = len(y_raw)
    x_full = np.arange(n)

    support_line = None
    resistance_line = None

    # ---- support from lows ----
    if len(pivot_lows) >= 2:
        sup_slope, sup_int, *_ = best_pivot_trendline(
            x_full, y_raw, pivot_lows, support=True
        )
        if sup_slope is not None:
            support_line = (sup_slope, sup_int)

    # ---- resistance from highs ----
    if len(pivot_highs) >= 2:
        res_slope, res_int, *_ = best_pivot_trendline(
            x_full, y_raw, pivot_highs, support=False
        )
        if res_slope is not None:
            resistance_line = (res_slope, res_int)

    # ---- store structure (state) ----
    if support_line is not None:
        seq.helpers["pivot_support_m"], seq.helpers["pivot_support_b"] = support_line

    if resistance_line is not None:
        seq.helpers["pivot_resistance_m"], seq.helpers["pivot_resistance_b"] = (
            resistance_line
        )

    # ----------------------------------------------------------
    # 5) OPTIONAL: write pivot lines to data (PLOTTING ONLY)
    # ----------------------------------------------------------
    # seg_idx = data.loc[start_idx:end_ts].index
    # x_vals = np.arange(len(seg_idx))

    # res_m = seq.helpers.get("pivot_resistance_m")
    # res_b = seq.helpers.get("pivot_resistance_b")
    # # --- Resistance line ---
    # if res_m is not None:
    #     data.loc[start_idx:end_ts, "pivot_resistance_line"] = res_m * x_vals + res_b

    # # --- Support line ---
    # sup_m = seq.helpers.get("pivot_support_m")
    # sup_b = seq.helpers.get("pivot_support_b")

    # if sup_m is not None:
    #     data.loc[start_idx:end_ts, "pivot_support_line"] = sup_m * x_vals + sup_b

    return support_line, resistance_line
