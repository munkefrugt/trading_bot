# signals/ trendline_crossings.py

import numpy as np
import pandas as pd

from signals.helpers.segments import get_segment_bounds
from signals.helpers.weekly_pivot_update import weekly_pivot_update
from signals.helpers.pivot_line_builder import build_pivot_trendlines
from signals.helpers.trend_regression import find_trend_regression


def trendline_crossings(data: pd.DataFrame, i: int, seq) -> bool:
    """
    Detect breakout via dominant pivot resistance line.

    Design rules:
    - Pivot logic may mutate `data`
    - Trendline logic MUST NOT mutate `data`
    - All trendline / regime state is written to `seq`
    """

    # --------------------------------------------------
    # 1) Consolidation segment
    # --------------------------------------------------
    start_idx, end_idx = get_segment_bounds(
        data, i, start_offset_days=20, end_offset_days=1
    )
    if start_idx is None or i == 0:
        return False

    end_ts = data.index[i]

    # --------------------------------------------------
    # 2) Weekly pivot STRUCTURE update (authority)
    # --------------------------------------------------
    if i % 7 == 0:
        data = weekly_pivot_update(data, start_idx, end_ts)
        build_pivot_trendlines(data, start_idx, end_ts, seq)

        end_ts_reg = seq.helpers.get("last_res_pivot_ts")
        if end_ts_reg is not None:
            reg = find_trend_regression(
                data,
                start_ts=start_idx,
                end_ts=end_ts_reg,
            )

        if reg is None:
            return False

        # ---- store STRUCTURE in seq (not data) ----
        seq.helpers.update(
            {
                "pivot_cross_i": i,
                "pivot_cross_time": data.index[i],
                "trend_reg_frozen": True,
                "trend_reg_start_ts": reg.start_ts,
                "trend_reg_end_ts": reg.end_ts,
                "trend_reg_m": reg.m,
                "trend_reg_b": reg.b,
                # optional diagnostics
                "trend_reg_up_offset": reg.up_offset,
                "trend_reg_low_offset": reg.low_offset,
            }
        )

    # --------------------------------------------------
    # 3) Dominant resistance
    # --------------------------------------------------
    res_m = seq.helpers.get("pivot_resistance_m")
    res_b = seq.helpers.get("pivot_resistance_b")
    if res_m is None:
        return False

    x = data.loc[start_idx:end_ts].index.get_loc(end_ts)
    resistance_val = res_m * x + res_b

    # --------------------------------------------------
    # 4) Breakout column
    # --------------------------------------------------
    breakout_col = "EMA_9"
    prev_val = data.iloc[i - 1][breakout_col]
    curr_val = data.iloc[i][breakout_col]

    # --------------------------------------------------
    # 5) Slope diagnostics (OBSERVATION ONLY)
    # --------------------------------------------------
    reg_m = seq.helpers.get("trend_reg_m")
    res_m = seq.helpers.get("pivot_resistance_m")

    angle_between_lines = None

    if reg_m is not None and res_m is not None:
        angle_between_lines = np.degrees(
            np.arctan(abs((res_m - reg_m) / (1 + reg_m * res_m)))
        )

    reg_angle = None
    res_angle = None

    if reg_m is not None:
        reg_angle = np.degrees(np.arctan(reg_m))

    if res_m is not None:
        res_angle = np.degrees(np.arctan(res_m))

    # --------------------------------------------------
    # 6) Breakout condition (UNCHANGED semantics)
    # --------------------------------------------------
    #
    is_breakout = curr_val > resistance_val  # and angle_between_lines < 10

    if is_breakout and angle_between_lines is not None:
        print(
            f"📐 ANGLES | seq={seq.id} | "
            f"θ_between={angle_between_lines:.1f}° | "
            f"reg_angle={reg_angle:.1f}° | "
            f"res_angle={res_angle:.1f}° | "
            f"reg_m={reg_m:.5f} | res_m={res_m:.5f}"
        )
    return is_breakout
