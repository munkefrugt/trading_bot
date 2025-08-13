# trend/w_senb_flat_to_rise.py
import numpy as np

def _linreg_slope(y: np.ndarray) -> float:
    """Least-squares slope (price units per bar)."""
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    A = np.vstack([x, np.ones(n)]).T
    slope, _ = np.linalg.lstsq(A, y.astype(float), rcond=None)[0]
    return float(slope)

def flat_to_rise(
    data,
    i: int,
    *,
    min_flat_weeks: int = 12,           # flat lookback
    max_flat_slope_pct: float = 5e-5,   # |prev slope| <= this (e.g. 0.005%/bar)
    max_flat_range_pct: float = 0.01,   # (max-min)/avg <= 1% keeps it “flat”
    ramp_weeks: int = 3,                # recent-ramp window to measure “turn up”
    min_curr_slope_pct: float = 1e-4,   # current slope >= this (0.01%/bar)
    slope_jump_min_pct: float = 7e-5,   # current - previous slope >= this
    breakout_over_max_pct: float = 0.003, # now above flat MAX by 0.3%
    confirm_bars: int = 1,              # consecutive bars meeting “rise”
    shift_weeks: int = 26,              # Ichimoku shift
    return_details: bool = False,
):
    """
    Stricter 'flat -> rise' for W_Senkou_span_B (shifted):
      1) A real flat base (low slope *and* tight range).
      2) Significant slope change vs prior window (ramp up).
      3) First close above the flat max by a margin (first-cross).
      4) Optional consecutive-bar confirmation.

    Writes debug columns and a boolean 'SenB_breakout_strict' on the row i.
    Returns (data, triggered) or (data, (triggered, details)) if return_details.
    """
    shift = shift_weeks * 7
    flat_bars = min_flat_weeks * 7
    ramp_bars = ramp_weeks * 7

    if i < flat_bars or i - ramp_bars < 0 or i >= len(data):
        if return_details:
            return data, (False, {})
        return data, False

    # Future-aligned weekly spans at "now"
    senb_future = data['W_Senkou_span_B'].shift(-shift)

    # Flat window = [i - flat_bars, i)
    flat_win = senb_future.iloc[i - flat_bars:i].to_numpy()
    flat_win = flat_win[~np.isnan(flat_win)]
    if len(flat_win) < max(5, flat_bars // 2):
        if return_details:
            return data, (False, {})
        return data, False

    flat_avg = float(np.mean(flat_win))
    flat_max = float(np.max(flat_win))
    if not np.isfinite(flat_avg) or flat_avg == 0.0:
        if return_details:
            return data, (False, {})
        return data, False

    # “Prev slope” from the earlier part of flat window (exclude ramp area)
    prev_end = i - ramp_bars
    prev_win = senb_future.iloc[i - flat_bars:prev_end].to_numpy()
    prev_win = prev_win[~np.isnan(prev_win)]
    if len(prev_win) < 5:
        prev_win = flat_win  # fallback

    prev_slope = _linreg_slope(prev_win)               # price units per bar
    prev_slope_pct = prev_slope / flat_avg             # % per bar

    # Current “ramp” slope over recent ramp window
    curr_win = senb_future.iloc[i - ramp_bars:i].to_numpy()
    curr_win = curr_win[~np.isnan(curr_win)]
    curr_slope = _linreg_slope(curr_win)
    curr_slope_pct = curr_slope / flat_avg

    # Flatness checks
    flat_range_pct = (np.max(flat_win) - np.min(flat_win)) / flat_avg
    flatness_ok = (abs(prev_slope_pct) <= max_flat_slope_pct) and (flat_range_pct <= max_flat_range_pct)

    # Slope change significance
    slope_jump_ok = (curr_slope_pct >= min_curr_slope_pct) and ((curr_slope_pct - prev_slope_pct) >= slope_jump_min_pct)

    # Breakout vs *flat max* + margin (reduces false flags during flat)
    now = float(senb_future.iloc[i])
    prev_val = float(senb_future.iloc[i - 7]) if i - 7 >= 0 else now
    level_ok = now > flat_max * (1 + breakout_over_max_pct)

    # First-cross only (so you don’t get multiple stars in the ramp)
    prev_level_ok = float(senb_future.iloc[i - 1]) > flat_max * (1 + breakout_over_max_pct) if i - 1 >= 0 else False
    first_cross_ok = not prev_level_ok

    # Debounce: consecutive bars meeting *slope+level*
    col = 'SenB_strict_breakout_count'
    if col not in data.columns:
        data[col] = 0
    if slope_jump_ok and level_ok:
        prev_count = int(data[col].iloc[i - 1]) if i > 0 else 0
        data.at[data.index[i], col] = prev_count + 1
    else:
        data.at[data.index[i], col] = 0

    triggered = bool(flatness_ok and slope_jump_ok and level_ok and first_cross_ok and int(data.at[data.index[i], col]) >= confirm_bars)

    # Debug / plotting helpers
    for k, v in dict(
        SenB_flat_avg=flat_avg,
        SenB_flat_max=flat_max,
        SenB_prev_slope_pct=prev_slope_pct,
        SenB_curr_slope_pct=curr_slope_pct,
        SenB_flat_range_pct=flat_range_pct,
        SenB_level_ok=level_ok,
        SenB_first_cross=first_cross_ok,
        SenB_breakout_strict=triggered,
    ).items():
        if k not in data.columns:
            data[k] = np.nan if 'pct' in k or 'avg' in k or 'max' in k or 'range' in k else False
        data.at[data.index[i], k] = v

    if return_details:
        details = {
            "flat_avg": flat_avg,
            "flat_max": flat_max,
            "prev_slope_pct": prev_slope_pct,
            "curr_slope_pct": curr_slope_pct,
            "flat_range_pct": flat_range_pct,
            "level_ok": level_ok,
            "first_cross_ok": first_cross_ok,
            "confirm_count": int(data.at[data.index[i], col]),
        }
        return data, (triggered, details)

    return data, triggered
