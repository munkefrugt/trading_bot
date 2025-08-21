#!/usr/bin/env python3
# pip install yfinance pandas plotly

import numpy as np
import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go


# ---------- Helpers ----------
def normalize_yf_ohlc(df: pd.DataFrame, ticker: str | None = None) -> pd.DataFrame:
    """Return single-level OHLC(V). Works with yfinance's multiindex too."""
    if not isinstance(df.columns, pd.MultiIndex):
        out = df.copy()
    else:
        want = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        sel = {}
        cols = list(df.columns)

        def _matches(col, name):
            for part in col:
                if isinstance(part, str) and part.strip().lower() == name.lower():
                    return True
            return False

        def _has_ticker(col, t):
            if t is None:
                return True
            t_up = t.upper()
            for part in col:
                if isinstance(part, str) and part.strip().upper() == t_up:
                    return True
            return False

        for name in want:
            cands = [c for c in cols if _matches(c, name) and _has_ticker(c, ticker)]
            if not cands and ticker is not None:
                cands = [c for c in cols if _matches(c, name)]
            if cands:
                sel[name] = df.loc[:, cands[0]]

        if not {"Open", "High", "Low", "Close"}.issubset(sel.keys()):
            raise ValueError("Could not extract OHLC from MultiIndex columns.")

        out = pd.DataFrame(sel, index=df.index)

    if "Adj Close" in out.columns and "Close" not in out.columns:
        out = out.rename(columns={"Adj Close": "Close"})

    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in out.columns]
    return out[keep]


def compute_weekly_ohlc_from_daily(df_daily: pd.DataFrame, week_rule: str = "W-FRI") -> pd.DataFrame:
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    if "Volume" in df_daily.columns:
        agg["Volume"] = "sum"
    wk = df_daily.resample(week_rule).agg(agg)
    wk = wk.dropna(subset=["Open", "High", "Low", "Close"])
    return wk


def add_bollinger(df: pd.DataFrame, period: int = 20, std_mult: float = 2.0, prefix: str = "W_") -> None:
    ma = df["Close"].rolling(period).mean()
    std = df["Close"].rolling(period).std(ddof=0)
    df[f"{prefix}BB_Middle_{period}"] = ma
    df[f"{prefix}BB_Upper_{period}"] = ma + std_mult * std
    df[f"{prefix}BB_Lower_{period}"] = ma - std_mult * std
    df[f"{prefix}BB_Width_{period}"] = df[f"{prefix}BB_Upper_{period}"] - df[f"{prefix}BB_Lower_{period}"]


def rolling_percentile(s: pd.Series, window: int) -> pd.Series:
    """Percentile rank of the last value within each trailing window."""
    def _pct(x):
        last = x[-1]
        n = len(x)
        if n <= 1:
            return np.nan
        return (np.sum(x <= last) - 1) / (n - 1)
    return s.rolling(window, min_periods=window).apply(_pct, raw=True)


# ---------- Bubble start detection ----------
def identify_bubble_starts(
    df: pd.DataFrame,
    period: int = 20,
    prefix: str = "W_",
    long_base_weeks: int = 104,  # baseline for width percentile
    setup_window: int = 26,      # lookback to confirm "recent quiet/tight"
    tight_pct: float = 0.40,     # width percentile considered "tight"
    hi_pct_cross: float = 0.85,  # width percentile cross-up that signals expansion
    roc_weeks: int = 4,          # momentum window
    roc_min: float = 0.25,       # +25% over roc_weeks
    nh_weeks: int = 52,          # new high lookback
    min_gap_weeks: int = 12,     # cool-down between bubble starts
):
    """
    Labels df['bubble_start'] when a new bubble likely begins:
      - recent quiet (width pct <= tight_pct at any time in setup_window),
      - AND width percentile crosses above hi_pct_cross,
      - AND (close > upper band OR 52w breakout OR strong ROC).
    """
    up = f"{prefix}BB_Upper_{period}"
    mid = f"{prefix}BB_Middle_{period}"
    lo = f"{prefix}BB_Lower_{period}"
    width = f"{prefix}BB_Width_{period}"

    # Width percentile vs long baseline
    df["bb_width_pct"] = rolling_percentile(df[width], long_base_weeks)

    # Recent quiet/tight presence
    recent_min_pct = df["bb_width_pct"].rolling(setup_window, min_periods=setup_window).min()
    had_recent_tight = (recent_min_pct <= tight_pct).fillna(False).astype(bool)

    # Expansion: percentile cross-up
    cross_up = (df["bb_width_pct"] >= hi_pct_cross) & (df["bb_width_pct"].shift(1) < hi_pct_cross)
    cross_up = cross_up.fillna(False).astype(bool)

    # Momentum / breakout confirmations
    close_above_upper = (df["Close"] > df[up]).fillna(False).astype(bool)
    n_week_high = df["Close"] >= df["Close"].rolling(nh_weeks, min_periods=nh_weeks).max()
    n_week_high = n_week_high.fillna(False).astype(bool)
    roc = df["Close"] / df["Close"].shift(roc_weeks) - 1.0
    strong_roc = (roc >= roc_min).fillna(False).astype(bool)

    confirm = (close_above_upper | n_week_high | strong_roc)

    raw_signal = (had_recent_tight & cross_up & confirm).astype(bool)

    # Keep only the first bar of each run and enforce cool-down gap
    # first-of-run
    first_of_run = raw_signal & (~raw_signal.shift(1).fillna(False))
    first_of_run = first_of_run.astype(bool)

    # cool-down: reject if a previous start was within min_gap_weeks
    bubble_start = pd.Series(False, index=df.index, dtype=bool)
    last_idx = None
    for ts, is_start in first_of_run.items():
        if not is_start:
            continue
        if last_idx is None or (ts - last_idx).days >= 7 * min_gap_weeks:
            bubble_start.loc[ts] = True
            last_idx = ts

    df["bubble_start"] = bubble_start

    # Optional: early heads-up (softer thresholds)
    early_cross = (df["bb_width_pct"] >= 0.70) & (df["bb_width_pct"].shift(1) < 0.70)
    early_heads_up = (had_recent_tight & early_cross & (n_week_high | strong_roc)).fillna(False).astype(bool)
    df["bubble_early"] = early_heads_up & (~bubble_start)


# ---------- Plot helpers ----------
def add_flag_markers(fig, df: pd.DataFrame, flag_col: str, y_col: str, name: str, symbol: str):
    pts = df[df[flag_col].fillna(False)]
    if pts.empty:
        return
    fig.add_trace(go.Scatter(
        x=pts.index, y=pts[y_col], mode="markers", name=name,
        marker=dict(size=10, symbol=symbol)
    ))


# ---------- Main ----------
def main():
    ticker = "BTC-USD"
    start = "2014-01-01"
    period = 20
    prefix = "W_"

    raw = yf.download(
        tickers=ticker,
        start=start,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )
    if raw.empty:
        raise SystemExit("No data from Yahoo.")

    df = normalize_yf_ohlc(raw, ticker=ticker)
    df.index = pd.to_datetime(df.index)

    dfw = compute_weekly_ohlc_from_daily(df, week_rule="W-FRI")
    add_bollinger(dfw, period=period, std_mult=2.0, prefix=prefix)

    identify_bubble_starts(
        dfw,
        period=period,
        prefix=prefix,
        long_base_weeks=104,
        setup_window=26,
        tight_pct=0.40,
        hi_pct_cross=0.85,
        roc_weeks=4,
        roc_min=0.25,
        nh_weeks=52,
        min_gap_weeks=12,
    )

    mid = f"{prefix}BB_Middle_{period}"
    up = f"{prefix}BB_Upper_{period}"
    lo = f"{prefix}BB_Lower_{period}"

    fig = make_subplots(rows=1, cols=1, shared_xaxes=True,
                        subplot_titles=[f"{ticker} — Weekly BB & Bubble Starts"])

    # Price
    fig.add_trace(go.Candlestick(
        x=dfw.index, open=dfw["Open"], high=dfw["High"], low=dfw["Low"], close=dfw["Close"],
        name="Weekly", increasing_line_color="green", decreasing_line_color="red", opacity=0.9
    ))

    # Bands
    fig.add_trace(go.Scatter(x=dfw.index, y=dfw[mid], mode="lines",
                             name=f"BB Mid ({period})", line=dict(width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=dfw.index, y=dfw[up], mode="lines",
                             name=f"BB Upper ({period})", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=dfw.index, y=dfw[lo], mode="lines",
                             name=f"BB Lower ({period})", line=dict(width=1)))

    # Markers
    add_flag_markers(fig, dfw, "bubble_early", mid, "Bubble early", "diamond")
    add_flag_markers(fig, dfw, "bubble_start", mid, "Bubble start", "star")

    fig.update_layout(
        title=f"{ticker} — Bubble Formation Signals (weekly)",
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=False)),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=720,
    )
    fig.show()

    # Quick stats
    starts = dfw.index[dfw["bubble_start"]]
    print("Weekly rows:", len(dfw))
    print("Bubble starts:", len(starts))
    if len(starts):
        print("First start:", starts.min())
        print("Last  start:", starts.max())


if __name__ == "__main__":
    main()
