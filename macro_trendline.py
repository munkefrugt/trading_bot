# macro_trendline.py
import numpy as np
import pandas as pd

def _find_local_maxima(prices: pd.Series, k: int) -> list:
    peaks = []
    for j in range(k, len(prices) - k):
        v = prices.iloc[j]
        if v > prices.iloc[j-k:j].max() and v > prices.iloc[j+1:j+k+1].max():
            peaks.append(j)
    return peaks

def build_macro_trendline_from_last_X(
    data: pd.DataFrame,
    current_index: int,
    column_name: str = 'Macro_trendline_from_X',
    peak_flag_col: str = 'Macro_peak',
    broken_flag_col: str = 'Macro_trendline_Broken',
    k: int = 7,                    # one week on each side
    breakout_pct: float = 0.005,   # 0.5%
    confirm_bars: int = 2,         # N closes above line
    force_non_positive_slope: bool = True,
    max_days: int = 21
):
    if 'D_Close' not in data.columns:
        raise ValueError("DataFrame must contain 'D_Close'.")

    idx = data.index
    end_pos = current_index if isinstance(current_index, int) else idx.get_loc(current_index)

    # --- find last red X (Start_of_Dead_Trendline) at/before current ---
    red_mask = (data['Start_of_Dead_Trendline'] == True) & (idx <= idx[end_pos])
    red_indices = idx[red_mask]
    if len(red_indices) == 0:
        return data, False
    start_label = red_indices[-1]
    start_pos = idx.get_loc(start_label)

    # --- cap the fitting window at first Real_uptrend_start after X (if exists) ---
    fit_end_pos = end_pos
    if 'Real_uptrend_start' in data.columns:
        after_x = data.loc[idx[start_pos:end_pos], 'Real_uptrend_start']
        rus = after_x[after_x == True]
        if len(rus) > 0:
            fit_end_pos = idx.get_loc(rus.index[0])

    # need some room for confirmed peaks
    if fit_end_pos <= start_pos + k:
        return data, False

    # ensure columns
    for col in (column_name,):
        if col not in data.columns:
            data[col] = np.nan
    for col in (peak_flag_col, broken_flag_col):
        if col not in data.columns:
            data[col] = False

    # --- collect peaks only in [start_pos, fit_end_pos] (exclude tail near fit_end_pos) ---
    prices_fit = data['D_Close'].iloc[start_pos:fit_end_pos+1].copy()
    tail_exclude = max(k, confirm_bars)
    if len(prices_fit) <= tail_exclude:
        return data, False
    prices_for_peaks = prices_fit.iloc[:len(prices_fit) - tail_exclude]

    rel_peaks = _find_local_maxima(prices_for_peaks, k=k)
    peak_positions = [start_pos] + [start_pos + p for p in rel_peaks]  # include X

    # fallback: add highest close inside fit range (pre-tail) if needed
    if len(peak_positions) < 2 and len(prices_for_peaks) > 0:
        pmax_rel = int(np.argmax(prices_for_peaks.values))
        peak_positions.append(start_pos + pmax_rel)

    peak_positions = sorted(set(peak_positions))
    data.loc[idx[peak_positions], peak_flag_col] = True

    # --- fit line constrained through X, slope ≤ 0 (down/flat) ---
    t = np.array([p - start_pos for p in peak_positions], dtype=float)
    y0 = float(data['D_Close'].iloc[start_pos])
    y = data['D_Close'].iloc[peak_positions].astype(float).values

    den = float(np.sum(t**2))
    slope = (np.sum(t * (y - y0)) / den) if den > 0 else 0.0
    if force_non_positive_slope:
        slope = min(slope, 0.0)

    # project line from X → current_index (not just fit_end_pos)
    span = end_pos - start_pos + 1
    line_vals = y0 + slope * np.arange(span, dtype=float)
    data.loc[idx[start_pos:end_pos+1], column_name] = line_vals

    # --- breakout detection at tail of projection ---
    tail_closes = data['D_Close'].iloc[end_pos - confirm_bars + 1 : end_pos + 1]
    tail_line   = data[column_name].iloc[end_pos - confirm_bars + 1 : end_pos + 1]
    breakout = (tail_closes > tail_line * (1 + breakout_pct)).all()

    if breakout:
        data.at[idx[end_pos], broken_flag_col] = True

     
    if data['Real_uptrend_start'].any():
        current_date = data.index[current_index]
        last_uptrend_start_idx = data.index[data['Real_uptrend_start']].max()
        days_past = (current_date - last_uptrend_start_idx).days

        if days_past > max_days:
            data.at[idx[end_pos], 'Macro_trendline_end'] = True    
            data.at[idx[end_pos], broken_flag_col] = True
            breakout = True  # force end
            print(f"🔍 Macro trendline ended at {current_date} due to search limit.")



    return data, bool(breakout)
