#!/usr/bin/env python3
# pip install yfinance pandas plotly

import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go


# --------- Robust normalization ---------
def normalize_yf_ohlc(df: pd.DataFrame, ticker: str | None = None) -> pd.DataFrame:
    """
    Return a DataFrame with single-level columns:
    Open, High, Low, Close, (optional Volume).
    Works whether df has a MultiIndex with the ticker on any level or not.
    """
    if not isinstance(df.columns, pd.MultiIndex):
        # Single-level already
        out = df.copy()
    else:
        # Build columns by searching for OHLCV names across *any* level,
        # optionally filtering by ticker if provided.
        want = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        sel = {}
        cols = list(df.columns)

        def _matches(col, name):
            # name equals any level (case-insensitive, stripped)
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
            candidates = [c for c in cols if _matches(c, name) and _has_ticker(c, ticker)]
            if not candidates and ticker is not None:
                # fallback: ignore ticker filter if strict match failed
                candidates = [c for c in cols if _matches(c, name)]
            if candidates:
                sel[name] = df.loc[:, candidates[0]]

        if not {"Open", "High", "Low", "Close"}.issubset(sel.keys()):
            raise ValueError(
                f"Could not extract OHLC from MultiIndex columns. "
                f"Found keys: {list(sel.keys())}. Columns sample: {cols[:6]}"
            )

        out = pd.DataFrame(sel, index=df.index)

    # Prefer adjusted close if present and Close is missing; otherwise keep Close.
    if "Adj Close" in out.columns and "Close" not in out.columns:
        out = out.rename(columns={"Adj Close": "Close"})
    # Keep only what we have
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in out.columns]
    return out[keep]


def compute_weekly_ohlc_from_daily(df_daily: pd.DataFrame, week_rule: str = "W-FRI") -> pd.DataFrame:
    """
    df_daily: columns Open, High, Low, Close, optional Volume; DateTimeIndex.
    """
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
    df[f"{prefix}BB_Upper_{period}"]  = ma + std_mult * std
    df[f"{prefix}BB_Lower_{period}"]  = ma - std_mult * std
    df[f"{prefix}BB_Width_{period}"]  = df[f"{prefix}BB_Upper_{period}"] - df[f"{prefix}BB_Lower_{period}"]


def identify_bb_squeeze(df: pd.DataFrame, bb_width_col: str, threshold: float = 0.7, window: int = 52) -> None:
    """
    Marks squeeze where width < rolling_mean(width) * threshold.
    Example: threshold=0.7 means width is below 70% of its rolling mean.
    """
    w = df[bb_width_col]
    roll = w.rolling(window=window, min_periods=window).mean()
    df["bb_squeeze"] = (w < (roll * threshold))


def add_squeeze_shading(fig, df: pd.DataFrame, upper_col: str, lower_col: str,
                        name="BB Squeeze", fillcolor="rgba(255,0,255,0.18)"):
    """
    Shade only the segments where bb_squeeze==True between upper & lower bands.
    """
    if "bb_squeeze" not in df.columns or not df["bb_squeeze"].any():
        return
    mask = df["bb_squeeze"].fillna(False)
    # group consecutive True runs
    group_id = (mask != mask.shift()).cumsum()
    for _, seg in df[mask].groupby(group_id):
        fig.add_trace(go.Scatter(
            x=seg.index, y=seg[upper_col], mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=seg.index, y=seg[lower_col], mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor=fillcolor,
            name=name, hoverinfo="skip"
        ), row=1, col=1)


# --------- Main ---------
def main():
    ticker = "BTC-USD"

    # Tip: group_by="column" gives single-level columns most of the time,
    # but we normalize robustly anyway.
    raw = yf.download(
        tickers=ticker,
        start="2014-01-01",
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",  # can be "column" or "ticker"; both handled below
    )
    if raw.empty:
        raise SystemExit("No data from Yahoo.")

    # Normalize to OHLCV single-level
    df = normalize_yf_ohlc(raw, ticker=ticker)

    # Ensure DateTimeIndex
    df.index = pd.to_datetime(df.index)

    # Weekly OHLC
    dfw = compute_weekly_ohlc_from_daily(df, week_rule="W-FRI")

    # Weekly BB(20)
    period = 20
    prefix = "W_"
    add_bollinger(dfw, period=period, std_mult=2.0, prefix=prefix)

    # Squeeze flags
    width_col = f"{prefix}BB_Width_{period}"
    identify_bb_squeeze(dfw, bb_width_col=width_col, threshold=0.7, window=52)  # 52 weeks, 70% of avg
    # ---- Plot ----
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True,
                        subplot_titles=[f"{ticker} — Weekly BB & Squeezes"])

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=dfw.index, open=dfw["Open"], high=dfw["High"], low=dfw["Low"], close=dfw["Close"],
        name="Weekly", increasing_line_color="green", decreasing_line_color="red", opacity=0.9
    ), row=1, col=1)

    # Bands
    mid_col = f"{prefix}BB_Middle_{period}"
    up_col  = f"{prefix}BB_Upper_{period}"
    lo_col  = f"{prefix}BB_Lower_{period}"

    fig.add_trace(go.Scatter(x=dfw.index, y=dfw[mid_col], mode="lines",
                             name=f"BB Mid ({period})", line=dict(width=1.5, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=dfw.index, y=dfw[up_col], mode="lines",
                             name=f"BB Upper ({period})", line=dict(width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=dfw.index, y=dfw[lo_col], mode="lines",
                             name=f"BB Lower ({period})", line=dict(width=1)), row=1, col=1)

    # Shade squeezes
    add_squeeze_shading(fig, dfw, upper_col=up_col, lower_col=lo_col, name="BB Squeeze")

    # Optional: markers on midline where squeeze is True
    pts = dfw[dfw["bb_squeeze"] & dfw[mid_col].notna()]
    if not pts.empty:
        fig.add_trace(go.Scatter(
            x=pts.index, y=pts[mid_col], mode="markers", name="Squeeze Points",
            marker=dict(size=9, symbol="star")
        ), row=1, col=1)

    fig.update_layout(
        title=f"{ticker} — Weekly Bollinger Band Squeezes",
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=False)),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )

    fig.show()

    print("Weekly rows:", len(dfw))
    print("Squeeze weeks:", int(dfw["bb_squeeze"].sum()))
    if dfw["bb_squeeze"].any():
        print("First squeeze:", dfw.index[dfw["bb_squeeze"]].min())
        print("Last  squeeze:", dfw.index[dfw["bb_squeeze"]].max())


if __name__ == "__main__":
    main()
