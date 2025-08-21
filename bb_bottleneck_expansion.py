# bb_bottleneck_expansion.py
import numpy as np
import pandas as pd
import config

def _linreg_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    return float(np.polyfit(x, y, 1)[0])

def _map_date_to_week_idx(date: pd.Timestamp, weekly_index: pd.DatetimeIndex) -> int | None:
    """
    Map a daily timestamp to the most recent weekly bar index (<= date).
    Returns None if everything is after the last weekly bar.
    """
    if not isinstance(date, pd.Timestamp):
        date = pd.Timestamp(date)
    pos = weekly_index.searchsorted(date, side="right") - 1
    return int(pos) if pos >= 0 else None

def bb_bottleneck_expansion(
    date_or_index,
    min_weeks: int = 5,
    max_weeks: int = 20,
    tight_quantile: float = 0.25,
    flat_window: int = 5,
    flat_slope: float = 0.0015,
    expand_ratio: float = 1.8,
    expand_confirm_weeks: int = 4,
):
    """
    Detect a 3-stage pattern on WEEKLY Bollinger Bands using config.weekly_bb:
      1) Long tight squeeze (bandwidth in lower quantile)
      2) Flat-ish middle band around squeeze
      3) Expansion (bandwidth rising and current BW >= expand_ratio * squeeze_bw)

    Also returns `price_breakout` (weekly close > weekly upper band) so you can allow
    an OR-condition: (tight squeeze recently) AND (expansion OR price_breakout).
    """
    wb = getattr(config, "weekly_bb", None)
    if wb is None:
        return False, {"error": "config.weekly_bb is None"}

    req = ["W_BB_Upper_20", "W_BB_Middle_20", "W_BB_Lower_20"]
    for c in req:
        if c not in wb.columns:
            return False, {"error": f"Missing column {c} in weekly_bb"}

    # Try to get a weekly close series
    weekly_px = None
    w_df = getattr(config, "weekly_data_HA", None)
    if isinstance(w_df, pd.DataFrame):
        for cand in ("W_Close", "W_HA_Close", "Close", "HA_Close"):
            if cand in w_df.columns:
                weekly_px = w_df[cand]
                break
    # Fallback: if weekly_bb happens to have Close
    if weekly_px is None and "W_Close" in wb.columns:
        weekly_px = wb["W_Close"]

    # Figure out weekly index i_w corresponding to the given daily date/index
    if isinstance(date_or_index, (int, np.integer)):
        # Assume caller passed the DAILY integer i, so we need a date
        # The caller should prefer passing a Timestamp to avoid ambiguity.
        return False, {"error": "Pass a Timestamp/index date, not a daily int index"}
    i_w = _map_date_to_week_idx(pd.Timestamp(date_or_index), wb.index)
    if i_w is None or i_w >= len(wb):
        return False, {"reason": "date before first weekly bar or out of range"}

    # Extract arrays
    U = wb["W_BB_Upper_20"].to_numpy()
    M = wb["W_BB_Middle_20"].to_numpy()
    L = wb["W_BB_Lower_20"].to_numpy()

    # Bandwidth (relative to middle; eps avoid div0)
    eps = 1e-12
    BW = (U - L) / np.maximum(np.abs(M), eps)

    # Need history
    if i_w < max_weeks or i_w < min_weeks:
        return False, {"reason": "not enough weekly history", "i_w": i_w}

    # Window where a squeeze could have occurred *before* current week
    start, end = i_w - max_weeks, i_w - min_weeks
    if end <= start:
        return False, {"reason": "bad window", "start": start, "end": end}

    # Find tightest week inside the window
    local_slice = slice(start, end + 1)
    squeeze_rel = int(np.argmin(BW[local_slice]))
    squeeze_idx = start + squeeze_rel
    squeeze_bw = float(BW[squeeze_idx])

    # Define "tight" threshold using up to ~2 years of BW history
    hist_start = max(0, i_w - 104)
    tight_threshold = float(np.quantile(BW[hist_start:i_w + 1], tight_quantile))
    was_tight = squeeze_bw <= tight_threshold

    # Middle line flatness around the squeeze peak
    half = max(1, flat_window // 2)
    seg = M[max(0, squeeze_idx - half): squeeze_idx + half + 1]
    mid_slope = abs(_linreg_slope(seg)) if len(seg) >= 2 else 0.0
    mid_flat = mid_slope <= flat_slope

    # Current expansion vs squeeze
    curr_bw = float(BW[i_w])
    expanded_enough = curr_bw >= expand_ratio * squeeze_bw

    # Steady expansion confirmation
    recent = BW[max(0, i_w - max(1, expand_confirm_weeks)): i_w + 1]
    inc_count = int(np.sum(np.diff(recent) > 0)) if len(recent) >= 2 else 0
    steadily_expanding = inc_count >= max(0, len(recent) - 2)  # allow 1 down week

    # Price breakout (weekly close above upper band)
    price_breakout = False
    if weekly_px is not None:
        try:
            w_close = float(weekly_px.iloc[i_w])
            price_breakout = w_close > float(U[i_w])
        except Exception:
            price_breakout = False

    # Final decision
    ok = bool(was_tight and mid_flat and expanded_enough and steadily_expanding)

    return ok, {
        "i_w": i_w,
        "squeeze_idx": int(squeeze_idx),
        "squeeze_date": str(wb.index[squeeze_idx]),
        "confirm_date": str(wb.index[i_w]),
        "squeeze_bw": squeeze_bw,
        "curr_bw": curr_bw,
        "tight_threshold": tight_threshold,
        "mid_slope": float(mid_slope),
        "was_tight": bool(was_tight),
        "mid_flat": bool(mid_flat),
        "expanded_enough": bool(expanded_enough),
        "steadily_expanding": bool(steadily_expanding),
        "price_breakout": bool(price_breakout),
    }

__all__ = ["bb_bottleneck_expansion"]
