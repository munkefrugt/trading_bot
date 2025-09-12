# trend/causal_slope.py
import numpy as np
import pandas as pd
from typing import Optional, Tuple

def _trailing_poly_value_and_slope(
    w: pd.DataFrame, w_pos: int, col: str, window: int, degree: int
) -> Optional[Tuple[float, float]]:
    if w_pos < 0 or w_pos >= len(w) or col not in w.columns:
        return None
    start = w_pos - window + 1
    if start < 0:
        return None

    y = w[col].iloc[start: w_pos + 1].astype(float).to_numpy()
    if y.size < 2 or not np.all(np.isfinite(y)):
        return None

    n = y.size
    d = max(1, min(degree, n - 1))
    x = np.arange(n, dtype=float)

    try:
        coeffs = np.polyfit(x, y, d)
    except Exception:
        return None

    fitted_last = float(np.polyval(coeffs, n - 1))
    dcoeffs = np.polyder(coeffs)
    slope_abs = float(np.polyval(dcoeffs, n - 1))   # units of y per week
    mean_level = float(np.mean(y))
    if not np.isfinite(mean_level) or abs(mean_level) < 1e-12:
        return None

    slope_pct = (slope_abs / mean_level) * 100.0    # %/week
    return fitted_last, slope_pct


def trailing_poly_gate_with_stamp(
    w: pd.DataFrame,
    w_pos: int,
    current_date,
    *,
    col: str = "W_Senkou_span_B_future",
    window: int = 9,
    degree: int = 2,
    threshold_pct: float = 1.0,                 # your ≥1% rule
    fit_col: str = "W_SenB_trailing_poly",
    slope_col: str = "W_SenB_trailing_slope_pct",
    stamp_if: bool = False,                     # pass “other conditions OK” (excluding slope)
    stamp_bars: int = 4,                        # show ~1 month behind the star
    only_fill_nans: bool = True,                # keep earlier segments untouched
) -> bool:
    """
    ONE-CALL helper for trend_check:
      - computes causal trailing slope at w_pos, writes current fit/slope to w[fit_col]/w[slope_col]
      - returns slope_ok (slope_pct >= threshold_pct)
      - if slope_ok and `stamp_if` are both True: stamps a *causal* segment of length `stamp_bars`
        behind w_pos into the same columns (NaNs elsewhere), preserving prior segments if wanted.
    """
    # ensure columns exist
    if fit_col not in w.columns:
        w[fit_col] = np.nan
    if slope_col not in w.columns:
        w[slope_col] = np.nan

    res = _trailing_poly_value_and_slope(w, w_pos, col, window, degree)
    if res is None:
        # write NaNs at current position, no stamp
        w.at[current_date, fit_col] = float("nan")
        w.at[current_date, slope_col] = float("nan")
        return False

    fit_now, slope_now = res
    w.at[current_date, fit_col]  = float(fit_now)
    w.at[current_date, slope_col] = float(slope_now)

    slope_ok = bool(slope_now >= threshold_pct)

    # Stamp a clean, short trail behind the star (causal per-bar)
    if slope_ok and stamp_if and stamp_bars > 0:
        seg_start = max(0, w_pos - stamp_bars + 1)
        for pos in range(seg_start, w_pos + 1):
            idx = w.index[pos]
            # causal: recompute using data up to `pos`
            r = _trailing_poly_value_and_slope(w, pos, col, window, degree)
            if r is None:
                continue
            fit_val, slope_pct = r

            if only_fill_nans:
                if pd.notna(w.at[idx, fit_col]):
                    pass
                else:
                    w.at[idx, fit_col] = float(fit_val)

                if pd.notna(w.at[idx, slope_col]):
                    pass
                else:
                    w.at[idx, slope_col] = float(slope_pct)
            else:
                w.at[idx, fit_col] = float(fit_val)
                w.at[idx, slope_col] = float(slope_pct)

    return slope_ok
