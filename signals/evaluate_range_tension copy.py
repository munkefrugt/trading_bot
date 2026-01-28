# signals/evaluate_regline.py

import numpy as np
import pandas as pd
from signals.helpers.trend_regression import find_trend_regression


def evaluate_regline(
    data: pd.DataFrame,
    i: int,
    seq,
    price_col: str = "D_Close",
    smooth_col: str = "smooth_s10",
) -> bool:
    """
    Freeze a regression line from segment start to pivot breakout
    and record regline ↔ smooth crossings (timestamps only).

    Geometry + observation.
    Advances the sequence ONLY if enough crossings exist.
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

    # --------------------------------------------------
    # 2) Build regression (pure helper)
    # --------------------------------------------------
    reg = find_trend_regression(
        data=data,
        start_ts=start_ts,
        end_ts=end_ts,
        price_col=price_col,
    )

    if reg is None:
        return False

    # --------------------------------------------------
    # 3) Store frozen regline geometry
    # --------------------------------------------------
    seq.helpers["trend_reg_frozen"] = True
    seq.helpers["trend_reg_start_ts"] = start_ts
    seq.helpers["trend_reg_end_ts"] = end_ts
    seq.helpers["trend_reg_m"] = reg.m
    seq.helpers["trend_reg_b"] = reg.b

    # --------------------------------------------------
    # 4) Count crossings vs smooth
    # --------------------------------------------------
    segment = data.loc[start_ts:end_ts]

    if smooth_col not in segment.columns:
        seq.helpers["trend_reg_cross_ts"] = []
        seq.helpers["trend_reg_cross_count"] = 0
        return False

    x = np.arange(len(segment))
    reg_vals = reg.m * x + reg.b
    smooth_vals = segment[smooth_col].values

    diff = smooth_vals - reg_vals
    signs = np.sign(diff)
    signs[signs == 0] = np.nan  # avoid fake crossings

    valid = ~np.isnan(signs[1:]) & ~np.isnan(signs[:-1])
    cross_idx = np.where(valid & (signs[1:] * signs[:-1] < 0))[0] + 1
    cross_ts = segment.index[cross_idx].tolist()

    # --------------------------------------------------
    # 5) Store geometry + crossing info
    # --------------------------------------------------
    seq.helpers["trend_reg_x"] = x
    seq.helpers["trend_reg_y"] = reg_vals
    seq.helpers["trend_reg_cross_ts"] = cross_ts
    seq.helpers["trend_reg_cross_count"] = len(cross_ts)

    # --------------------------------------------------
    # 6) Gate: require sufficient interaction with regline
    # --------------------------------------------------
    return len(cross_ts) >= 4
