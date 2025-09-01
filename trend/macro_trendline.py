# trend.macro_trendline.py
import numpy as np
import pandas as pd


def _find_local_maxima(prices: pd.Series, k: int) -> list:
    """Indices of strict local maxima with k bars lower on each side."""
    peaks = []
    for j in range(k, len(prices) - k):
        v = prices.iloc[j]
        if v > prices.iloc[j - k:j].max() and v > prices.iloc[j + 1:j + k + 1].max():
            peaks.append(j)
    return peaks


def build_macro_trendline_from_last_X(
    data: pd.DataFrame,
    current_index: int,
    column_name: str = "Macro_trendline_from_X",
    peak_flag_col: str = "Macro_peak",
    broken_flag_col: str = "Macro_trendline_Broken",
    k: int = 7,                    # local-max window (weeks on each side for daily data)
    breakout_pct: float = 0.005,   # closes must be > line*(1+breakout_pct)
    confirm_bars: int = 2,         # consecutive confirming closes
    force_non_positive_slope: bool = True,
    fit_tail_extra_days: int = 14  # include peaks this many days past first Real_uptrend_start
):
    """
    Build a descending-or-flat *upper resistance* from the most recent
    Start_of_Dead_Trendline (X). The line is defined ONLY by tops between X and
    a window that extends slightly past the first Real_uptrend_start.
    Slope = the tightest envelope through X that stays at/above all selected peaks:

        slope = min(0, max( (y_i - y0) / (t_i) ))   if force_non_positive_slope
                max( (y_i - y0) / (t_i) )           otherwise

    The line is ALWAYS projected to `current_index`. It ends only when a breakout
    is confirmed by `confirm_bars` closes above the line by `breakout_pct`.
    """
    if "D_Close" not in data.columns:
        raise ValueError("DataFrame must contain 'D_Close'.")

    idx = data.index
    end_pos = current_index if isinstance(current_index, int) else idx.get_loc(current_index)

    # --- anchor X ---
    red_mask = (data.get("Start_of_Dead_Trendline", False) == True) & (idx <= idx[end_pos])
    red_indices = idx[red_mask]
    if len(red_indices) == 0:
        return data, False
    start_label = red_indices[-1]
    start_pos = idx.get_loc(start_label)

    # --- choose fit window end (allow a bit past first Real_uptrend_start) ---
    fit_end_pos = end_pos
    if "Real_uptrend_start" in data.columns:
        after_x = data.loc[idx[start_pos:end_pos], "Real_uptrend_start"]
        rus = after_x[after_x == True]
        if len(rus) > 0:
            rus_pos = idx.get_loc(rus.index[0])
            fit_end_pos = min(end_pos, rus_pos + max(0, int(fit_tail_extra_days)))

    # ensure columns
    if column_name not in data.columns:
        data[column_name] = np.nan
    if peak_flag_col not in data.columns:
        data[peak_flag_col] = False
    if broken_flag_col not in data.columns:
        data[broken_flag_col] = False
    if "Macro_trendline_end" not in data.columns:
        data["Macro_trendline_end"] = False

    # not enough room → draw flat from X just to avoid gaps
    if fit_end_pos <= start_pos + k:
        y0 = float(data["D_Close"].iloc[start_pos])
        span = end_pos - start_pos + 1
        if span > 0:
            data.loc[idx[start_pos:end_pos + 1], column_name] = y0 + 0.0 * np.arange(span, dtype=float)
        return data, False

    # --- collect peaks in [start_pos, fit_end_pos], exclude tiny confirm tail ---
    prices_fit = data["D_Close"].iloc[start_pos:fit_end_pos + 1].copy()
    tail_exclude = max(int(k), int(confirm_bars))
    if len(prices_fit) <= tail_exclude:
        return data, False
    prices_for_peaks = prices_fit.iloc[: len(prices_fit) - tail_exclude]

    rel_peaks = _find_local_maxima(prices_for_peaks, k=int(k))
    peak_positions = [start_pos] + [start_pos + p for p in rel_peaks]

    # fallback: include highest close pre-tail so we always have 2 points
    if len(peak_positions) < 2 and len(prices_for_peaks) > 0:
        pmax_rel = int(np.argmax(prices_for_peaks.values))
        peak_positions.append(start_pos + pmax_rel)

    peak_positions = sorted(set(peak_positions))
    if len(peak_positions) < 2:
        y0 = float(data["D_Close"].iloc[start_pos])
        span = end_pos - start_pos + 1
        data.loc[idx[start_pos:end_pos + 1], column_name] = y0 + 0.0 * np.arange(span, dtype=float)
        return data, False

    # mark peaks for plotting
    data.loc[idx[peak_positions], peak_flag_col] = True

    # --- compute tight upper-envelope slope through X using only peaks ---
    t = np.array([p - start_pos for p in peak_positions], dtype=float)
    y0 = float(data["D_Close"].iloc[start_pos])
    y = data["D_Close"].iloc[peak_positions].astype(float).values

    mask = t > 0
    if not np.any(mask):
        span = end_pos - start_pos + 1
        data.loc[idx[start_pos:end_pos + 1], column_name] = y0 + 0.0 * np.arange(span, dtype=float)
        return data, False

    cand_slopes = (y[mask] - y0) / t[mask]
    slope = float(np.max(cand_slopes))
    if force_non_positive_slope:
        slope = min(slope, 0.0)

    # --- project from X → current_index (always; keep extending until breakout) ---
    span = end_pos - start_pos + 1
    line_vals = y0 + slope * np.arange(span, dtype=float)
    data.loc[idx[start_pos:end_pos + 1], column_name] = line_vals

    # --- breakout detection on tail ---
    if end_pos - (confirm_bars - 1) >= 0:
        tail_closes = data["D_Close"].iloc[end_pos - confirm_bars + 1 : end_pos + 1]
        tail_line   = data[column_name].iloc[end_pos - confirm_bars + 1 : end_pos + 1]
        breakout = bool((tail_closes > tail_line * (1.0 + float(breakout_pct))).all())  
    else:
        breakout = False

    if breakout:
        data.at[idx[end_pos], broken_flag_col] = True
        data.at[idx[end_pos], "Macro_trendline_end"] = True

    return data, breakout
