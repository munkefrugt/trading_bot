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
    # 5) Cross detection (EVENT)
    # --------------------------------------------------

    cross = prev_val <= resistance_val and curr_val > resistance_val

    # if not cross:
    #     cross = cross_back_check(
    #         data=data,
    #         breakout_col=breakout_col,
    #         i=i,
    #         start_idx=start_idx,
    #         res_m=res_m,
    #         res_b=res_b,
    #         seq=seq,
    #     )

    if cross and not seq.helpers.get("trend_reg_frozen", False):
        freeze_ts = data.index[i - 1]

        reg = find_trend_regression(
            data,
            start_ts=start_idx,
            end_ts=freeze_ts,
        )

        if reg is None:
            return False

            # 🔍 DEBUG PRINT (TEMPORARY)
        print(
            f"📐 REG FROZEN | seq={seq.id} | "
            f"cross={data.index[i].date()} | "
            f"window=[{reg.start_ts.date()} → {reg.end_ts.date()}] | "
            f"m={reg.m:.5f}"
        )

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
    # 6) Breakout condition (UNCHANGED semantics)
    # --------------------------------------------------
    return curr_val > resistance_val


def cross_back_check(
    data,
    breakout_col,
    i,
    start_idx,
    res_m,
    res_b,
    seq,
):
    # Do not recover if already frozen
    if seq.helpers.get("trend_reg_frozen", False):
        return False

    curr_val = data.iloc[i][breakout_col]
    ts_now = data.index[i]
    x_now = data.index.get_loc(ts_now)
    resistance_now = res_m * x_now + res_b

    # If we're not above resistance, nothing to recover
    if curr_val <= resistance_now:
        return False

    # Search backwards inside the active segment
    window = data.iloc[start_idx : i + 1]

    for j in range(len(window) - 1, 0, -1):
        ts_j = window.index[j]
        ts_prev = window.index[j - 1]

        x_j = data.index.get_loc(ts_j)
        x_prev = data.index.get_loc(ts_prev)

        prev_val = window.iloc[j - 1][breakout_col]
        curr_val = window.iloc[j][breakout_col]

        if prev_val <= res_m * x_prev + res_b and curr_val > res_m * x_j + res_b:
            # store recovered cross location
            seq.helpers["recovered_cross_i"] = data.index.get_loc(ts_j)
            seq.helpers["recovered_cross_time"] = ts_j
            return True

    return False
