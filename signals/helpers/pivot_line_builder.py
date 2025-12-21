# signals/helpers/pivot_line_builder.py
import numpy as np
from signals.trendline_maker.trendline_builder import best_pivot_trendline


def build_pivot_trendlines(data, start_idx, end_ts, seq):
    segment = data.loc[start_idx:end_ts]
    y_raw = segment["D_Close"].values

    pivot_lows_ts = segment.index[segment["pivot_support_price"].notna()].tolist()
    pivot_highs_ts = segment.index[segment["pivot_resistance_price"].notna()].tolist()

    pivot_lows = [segment.index.get_loc(ts) for ts in pivot_lows_ts]
    pivot_highs = [segment.index.get_loc(ts) for ts in pivot_highs_ts]

    x_full = np.arange(len(y_raw))

    support_line = None
    resistance_line = None

    if len(pivot_lows) >= 2:
        sup_m, sup_b, *_ = best_pivot_trendline(x_full, y_raw, pivot_lows, support=True)
        if sup_m is not None:
            support_line = (sup_m, sup_b)

    if len(pivot_highs) >= 2:
        res_m, res_b, *_ = best_pivot_trendline(
            x_full, y_raw, pivot_highs, support=False
        )
        if res_m is not None:
            resistance_line = (res_m, res_b)

    # ---- store STRUCTURE ----
    if support_line is not None:
        seq.helpers["pivot_support_m"], seq.helpers["pivot_support_b"] = support_line

    if resistance_line is not None:
        seq.helpers["pivot_resistance_m"], seq.helpers["pivot_resistance_b"] = (
            resistance_line
        )

    if support_line or resistance_line:
        seq.helpers["pivot_start_ts"] = segment.index[0]
        seq.helpers["pivot_end_ts"] = segment.index[-1]

    return support_line, resistance_line
