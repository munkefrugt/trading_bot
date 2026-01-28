# signals/evaluate_range_tension.py

import numpy as np
import pandas as pd
from signals.helpers.trend_regression import find_trend_regression


def evaluate_range_tension(
    data: pd.DataFrame,
    i: int,
    seq,
    price_col: str = "D_Close",
    smooth_col: str = "smooth_s10",
    ema_col: str = "EMA_50",
    min_regline_crosses: int = 4,
    min_ema_crosses: int = 4,
) -> bool:
    """
    Evaluate whether sufficient range tension has built up
    before the pivot breakout.

    Tension is defined as repeated oscillation between
    independent smooth structures inside the same segment.

    Instruments:
      - smooth ↔ regression line
      - smooth ↔ EMA

    No direction, no trigger logic.
    """

    # --------------------------------------------------
    # 1) Require frozen segment + breakout
    # --------------------------------------------------
    start_ts = seq.helpers.get("segment_start_ts")
    end_ts = seq.helpers.get("pivot_break_ts")

    if start_ts is None or end_ts is None:
        return False

    if start_ts not in data.index or end_ts not in data.index:
        return False

    segment = data.loc[start_ts:end_ts]

    if smooth_col not in segment.columns:
        return False

    # --------------------------------------------------
    # 2) Regression line (instrument)
    # --------------------------------------------------
    reg = find_trend_regression(
        data=data,
        start_ts=start_ts,
        end_ts=end_ts,
        price_col=price_col,
    )

    if reg is None:
        return False

    x = np.arange(len(segment))
    reg_vals = reg.m * x + reg.b

    smooth_vals = segment[smooth_col].values

    # smooth ↔ regline crossings
    diff_reg = smooth_vals - reg_vals
    signs = np.sign(diff_reg)
    signs[signs == 0] = np.nan

    valid = ~np.isnan(signs[1:]) & ~np.isnan(signs[:-1])
    reg_cross_idx = np.where(valid & (signs[1:] * signs[:-1] < 0))[0] + 1
    reg_cross_ts = segment.index[reg_cross_idx].tolist()
    reg_cross_count = len(reg_cross_ts)

    # --------------------------------------------------
    # 3) Smooth ↔ EMA crossings (instrument)
    # --------------------------------------------------
    ema_cross_count = 0

    if ema_col in segment.columns:
        diff_ema = smooth_vals - segment[ema_col].values
        signs = np.sign(diff_ema)
        signs[signs == 0] = np.nan

        valid = ~np.isnan(signs[1:]) & ~np.isnan(signs[:-1])

        ema_cross_idx = np.where(valid & (signs[1:] * signs[:-1] < 0))[0] + 1
        ema_cross_ts = segment.index[ema_cross_idx].tolist()
        ema_cross_count = len(ema_cross_ts)

    # --------------------------------------------------
    # 4) Store tension diagnostics
    # --------------------------------------------------
    seq.helpers["range_tension_regline_crosses"] = reg_cross_count
    seq.helpers["range_tension_ema_crosses"] = ema_cross_count
    seq.helpers["range_tension_regline_cross_ts"] = reg_cross_ts
    seq.helpers["range_tension_ema_cross_ts"] = ema_cross_ts
    seq.helpers["range_tension_segment_len"] = len(segment)

    # also store regline geometry for plotting
    seq.helpers["trend_reg_frozen"] = True
    seq.helpers["trend_reg_start_ts"] = start_ts
    seq.helpers["trend_reg_end_ts"] = end_ts
    seq.helpers["trend_reg_m"] = reg.m
    seq.helpers["trend_reg_b"] = reg.b
    seq.helpers["trend_reg_x"] = x
    seq.helpers["trend_reg_y"] = reg_vals

    # --------------------------------------------------
    # 5) Gate: sufficient tension required
    # --------------------------------------------------
    if reg_cross_count >= min_regline_crosses and ema_cross_count >= min_ema_crosses:
        print("ema_cross_count")
        print(ema_cross_count)
        return True
