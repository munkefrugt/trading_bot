# math_helpers.py
import numpy as np
import pandas as pd

try:
    from scipy.signal import savgol_filter
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

def smooth_savgol(series: pd.Series,
                  window: int = 9,
                  polyorder: int = 2,
                  deriv: int = 0,
                  delta: float = 1.0) -> pd.Series:
    """
    Savitzky–Golay smoothing (and derivative if deriv>0).
    Falls back to simple rolling mean if SciPy isn't available.
    """
    s = pd.to_numeric(series, errors="coerce")
    if len(s.dropna()) == 0:
        return s

    # ensure odd window and > polyorder
    w = max(polyorder + 3, window)
    if w % 2 == 0:
        w += 1
    if w > len(s):
        w = len(s) - (1 - len(s) % 2)  # largest odd <= len(s)
        if w <= polyorder:
            return s.rolling(window=min(5, max(2, len(s)))).mean()

    if _HAS_SCIPY:
        arr = s.to_numpy()
        out = savgol_filter(arr, window_length=w, polyorder=polyorder,
                            deriv=deriv, delta=delta, mode="interp")
        return pd.Series(out, index=s.index)
    else:
        # fallback smoothing
        return s.rolling(window=w, min_periods=1, center=True).mean()
