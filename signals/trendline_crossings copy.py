import numpy as np
import pandas as pd

from signals.helpers.segments import get_segment_bounds
from signals.helpers.weekly_pivot_update import weekly_pivot_update
from signals.helpers.pivot_line_builder import build_pivot_trendlines
from .helpers.trendline import build_trend_channel_for_segment
from .helpers.trendline_eval import trendline_eval


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
    EMA_9 = data.iloc[i]["EMA_9"]
    EMA_20 = data.iloc[i]["EMA_20"]

    resistance_val = res_m * x + res_b

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

    # TODO use this to qualify the trendline:
    # ADD regression trendlines
    data, D_Close_smooth_breakout = build_trend_channel_for_segment(
        data, start_idx=start_idx, end_idx=end_idx, i=i
    )
    # --- Evaluate number of crossings ---
    # TODO fix! dose it evaluate the full segment or by each i?
    eval_out = trendline_eval(
        data,
        start_ts=start_idx,
        end_ts=data.index[i],
        pivot_m=res_m,
    )

    if not eval_out:
        return False

    crossings = eval_out["crossings"]
    parallel_ok = eval_out["parallel"]

    # ----------------------------------------------------------
    # 4) Breakout condition

    if EMA_9 > resistance_val and parallel_ok and crossings > 3:
        breakout = True
    else:
        breakout = False

    return breakout
