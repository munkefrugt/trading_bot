# identify_bb_squeeze.py
from __future__ import annotations
import pandas as pd
from typing import Optional, Literal
import config

Mode = Literal["ratio", "percentile"]

def _auto_width_col(df: pd.DataFrame) -> str:
    """
    Find a Bollinger Band width column. Prefers weekly-style names like 'W_BB_Width_20',
    otherwise returns the first column containing 'BB_Width'.
    """
    candidates = [c for c in df.columns if isinstance(c, str) and "BB_Width" in c]
    if not candidates:
        raise ValueError("No 'BB_Width' column found in DataFrame.")
    # prefer weekly if present
    weekly = [c for c in candidates if c.startswith("W_")]
    return weekly[0] if weekly else candidates[0]


def identify_bb_squeeze(
    df: pd.DataFrame,
    bb_width_col: Optional[str] = None,
    *,
    mode: Mode = "percentile",
    # -- ratio mode params:
    ratio_threshold: float = 0.6,
    ratio_window: int = 20,
    # -- percentile mode params:
    pct_window: int = 52,
    pct: float = 0.15,
    # -- general:
    output_debug: bool = False,
    squeeze_col: str = "bb_squeeze",
) -> pd.DataFrame:
    """
    Add a boolean column marking Bollinger Band squeeze periods.

    Parameters
    ----------
    df : pd.DataFrame
        Must include a BB width column like 'W_BB_Width_20'.
    bb_width_col : str, optional
        Column name for BB width. If None, auto-detects the first column containing 'BB_Width'.
    mode : {'ratio','percentile'}, default 'percentile'
        'ratio'      -> width < ratio_threshold * rolling_mean(width) over ratio_window.
        'percentile' -> width < rolling pct-quantile over pct_window.
    ratio_threshold : float, default 0.6
        Used only in 'ratio' mode. Larger -> more squeezes.
    ratio_window : int, default 20
        Rolling window for mean in 'ratio' mode.
    pct_window : int, default 52
        Rolling window (in bars) for quantile in 'percentile' mode.
    pct : float, default 0.15
        Quantile used in 'percentile' mode (bottom 15% of recent widths).
    output_debug : bool, default False
        If True, also writes helper columns ('_bb_ratio', '_bb_quantile') when applicable.
    squeeze_col : str, default 'bb_squeeze'
        Name of output boolean column.

    Returns
    -------
    pd.DataFrame
        Same df with a new boolean column `squeeze_col`.
    """
    if bb_width_col is None:
        bb_width_col = _auto_width_col(df)

    if mode == "ratio":
        roll_mean = df[bb_width_col].rolling(window=ratio_window, min_periods=ratio_window).mean()
        ratio = df[bb_width_col] / roll_mean
        df[squeeze_col] = ratio < ratio_threshold
        if output_debug:
            df[f"{bb_width_col}_rollmean_{ratio_window}"] = roll_mean
            df[f"{bb_width_col}_ratio"] = ratio

    elif mode == "percentile":
        # rolling quantile per-row (requires pandas >= 1.5)
        q = df[bb_width_col].rolling(window=pct_window, min_periods=pct_window).quantile(pct)
        df[squeeze_col] = df[bb_width_col] < q
        if output_debug:
            df[f"{bb_width_col}_q{int(pct*100)}_{pct_window}"] = q
            df[f"{bb_width_col}_ratio2q"] = df[bb_width_col] / q

    else:
        raise ValueError("mode must be 'ratio' or 'percentile'")

    # Fill initial NaNs (before window fills) as False
    df[squeeze_col] = df[squeeze_col].fillna(False)
    return df


# Convenience wrappers (optional)
def identify_bb_squeeze_ratio(
    df: pd.DataFrame,
    bb_width_col: Optional[str] = None,
    *,
    threshold: float = 0.6,
    window: int = 20,
    output_debug: bool = False,
    squeeze_col: str = "bb_squeeze",
) -> pd.DataFrame:
    return identify_bb_squeeze(
        df,
        bb_width_col=bb_width_col,
        mode="ratio",
        ratio_threshold=threshold,
        ratio_window=window,
        output_debug=output_debug,
        squeeze_col=squeeze_col,
    )


def identify_bb_squeeze_percentile(
    df: pd.DataFrame,
    bb_width_col: Optional[str] = None,
    *,
    window: int = 52,
    pct: float = 0.15,
    output_debug: bool = False,
    squeeze_col: str = "bb_squeeze",
) -> pd.DataFrame:
    return identify_bb_squeeze(
        df,
        bb_width_col=bb_width_col,
        mode="percentile",
        pct_window=window,
        pct=pct,
        output_debug=output_debug,
        squeeze_col=squeeze_col,
    )

# Percentile mode (recommended)
#weekly_bb = identify_bb_squeeze_percentile(weekly_bb, bb_width_col="W_BB_Width_20", window=52, pct=0.15)

# Or ratio mode
#weekly_bb = identify_bb_squeeze_ratio(weekly_bb, bb_width_col="W_BB_Width_20", threshold=0.6, window=20)
