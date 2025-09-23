#!/usr/bin/env python3
# Auto trendlines (no external libs beyond numpy/pandas/matplotlib/yfinance) + breakout flags
# Works even if 'trendln' is flaky or missing.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

# ------------------ CONFIG ------------------
SYMBOL = "AAPL"       # e.g. "BTC-USD", "BRK-B", "TSLA"
PERIOD = "5y"        # e.g. "6mo", "1y", "5y", "60d" (for intraday)
INTERVAL = "1d"       # e.g. "1d", "1h", "15m", "5m", "1m" (Yahoo limits apply)
EXTREMUM_WINDOW = 3   # swing strictness; 2-5 is typical; larger = fewer, stronger swings
K_POINTS = 3          # how many recent swings to fit each line (>=2)
N_RES_LINES = 2       # how many most-recent resistance lines to draw
N_SUP_LINES = 2       # how many most-recent support    lines to draw
MARK_SWINGS = True
# --------------------------------------------

def find_swings(series: pd.Series, w: int, mode: str):
    """
    Confirmed swings by window rule:
      - 'high': value > all w left AND > all w right
      - 'low' : value < all w left AND < all w right
    Returns: np.ndarray of indices (0..N-1 in series-reset space)
    """
    x = series.values
    n = len(x)
    idxs = []
    for i in range(w, n - w):
        left = x[i - w:i]
        right = x[i + 1:i + 1 + w]
        if mode == "high":
            if x[i] > left.max() and x[i] > right.max():
                idxs.append(i)
        else:
            if x[i] < left.min() and x[i] < right.min():
                idxs.append(i)
    return np.asarray(idxs, dtype=int)

def fit_line(idxs, ys):
    """
    Least-squares line y = m*x + b over integer x = idxs.
    Returns (m, b) or (None, None) if not enough points.
    """
    if len(idxs) < 2:
        return None, None
    x = np.asarray(idxs, dtype=float)
    y = np.asarray(ys, dtype=float)
    m, b = np.polyfit(x, y, 1)
    return m, b

def line_at(m, b, i):
    return m * float(i) + b

def line_series(m, b, n):
    xs = np.arange(n, dtype=float)
    return m * xs + b

def build_lines_from_swings(series: pd.Series, swing_idxs: np.ndarray, k: int, how_many: int):
    """
    Build up to 'how_many' most recent lines fitted through last k swings.
    Returns list of dicts: [{'m':..., 'b':..., 'pts': np.ndarray}, ...] (most recent last)
    """
    lines = []
    if len(swing_idxs) < 2:
        return lines
    # we walk from the end, each time take last k swing points
    for end in range(len(swing_idxs)-1, max(-1, len(swing_idxs)-1 - how_many), -1):
        pts = swing_idxs[max(0, end - (k - 1)):end + 1]
        if len(pts) >= 2:
            m, b = fit_line(pts, series.iloc[pts])
            if m is not None:
                lines.append({"m": m, "b": b, "pts": pts})
    # reverse so older first, newest last
    return list(reversed(lines))

def detect_breakouts(close: pd.Series, lines: list, direction: str):
    """
    Simple last-bar breakout check against each line in 'lines'.
    direction: 'res' (check up-break) or 'sup' (check down-break)
    Returns list of (tag, line_dict) for lines that broke on last bar.
    """
    sigs = []
    n = len(close)
    if n < 2:
        return sigs
    c_prev, c_now = float(close.iloc[-2]), float(close.iloc[-1])
    i_prev, i_now = n - 2, n - 1
    for L in lines:
        m, b = L["m"], L["b"]
        y_prev = line_at(m, b, i_prev)
        y_now  = line_at(m, b, i_now)
        if direction == "res":
            if c_prev <= y_prev and c_now > y_now:
                sigs.append(("UP_BREAKOUT", L))
        else:  # 'sup'
            if c_prev >= y_prev and c_now < y_now:
                sigs.append(("DOWN_BREAKOUT", L))
    return sigs

def main():
    # 1) Data
    df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, auto_adjust=True).dropna()
    if df.empty:
        raise SystemExit("No data returned. Try a shorter PERIOD for intraday or a different symbol.")
    # use reset index for clean integer indexing while keeping dates for plotting
    dates = df.index
    close = df["Close"].astype(float).reset_index(drop=True)
    high  = df["High"].astype(float).reset_index(drop=True)
    low   = df["Low"].astype(float).reset_index(drop=True)
    n = len(close)

    # 2) Swings
    hi_idx = find_swings(high, w=EXTREMUM_WINDOW, mode="high")
    lo_idx = find_swings(low,  w=EXTREMUM_WINDOW, mode="low")

    # 3) Fit lines from recent swings
    res_lines = build_lines_from_swings(high, hi_idx, k=K_POINTS, how_many=N_RES_LINES)
    sup_lines = build_lines_from_swings(low,  lo_idx, k=K_POINTS, how_many=N_SUP_LINES)

    # 4) Breakouts on last bar
    up_breaks   = detect_breakouts(close, res_lines, direction="res")
    down_breaks = detect_breakouts(close, sup_lines, direction="sup")

    # 5) Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, close.values, label=f"{SYMBOL} Close", linewidth=1.2)

    # draw lines across full range
    for L in res_lines:
        y = line_series(L["m"], L["b"], n)
        ax.plot(dates, y, "-", linewidth=1.0, alpha=0.9, label="Resistance")
    for L in sup_lines:
        y = line_series(L["m"], L["b"], n)
        ax.plot(dates, y, "--", linewidth=1.0, alpha=0.9, label="Support")

    # mark swing points
    if MARK_SWINGS:
        if len(hi_idx):
            ax.scatter(dates[hi_idx], high.iloc[hi_idx], s=22, marker="v", label="Swing Highs")
        if len(lo_idx):
            ax.scatter(dates[lo_idx], low.iloc[lo_idx], s=22, marker="^", label="Swing Lows")

    # annotate breakouts
    if up_breaks or down_breaks:
        ax.scatter(dates[-1], close.iloc[-1], s=90, marker="o")
        tags = [t for t, _ in up_breaks + down_breaks]
        ax.text(dates[-1], close.iloc[-1], " " + ",".join(tags), va="bottom")

    ax.set_title(f"{SYMBOL} — auto trendlines (LSQ on swings) + breakout flags")
    ax.legend(loc="best")
    plt.tight_layout()
    plt.show()

    # 6) Print signals for your backtester
    if up_breaks or down_breaks:
        print("Signals:", [t for t, _ in up_breaks + down_breaks])
    else:
        print("No breakout on the last bar.")

if __name__ == "__main__":
    main()
