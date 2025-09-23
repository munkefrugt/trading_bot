# signals/core.py
from typing import Callable, List, Tuple
import pandas as pd

from .ema50_over_200 import ema50_over_200
from .ema200_over_2y import ema200_over_2y
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
Signal = Tuple[str, Callable[[pd.DataFrame, int], bool], int]

SIGNAL_ORDER: List[Signal] = [
    #("ema50_over_200", ema50_over_200, 90),
    #("ema200_over_2y", ema200_over_2y, 60),
    ("senb_w_future_flat_base", senb_w_future_flat_base, 7*8),
    ("senb_w_future_slope_pct", senb_w_future_slope_pct, 7*8),


]

# in-memory TTL state
_valid_until: List[int] = []  # i-index (inclusive) until active

def reset_signal_state():
    global _valid_until 
    _valid_until = [-1] * len(SIGNAL_ORDER)

def _ensure_state_size():
    global _valid_until
    n = len(SIGNAL_ORDER)
    if len(_valid_until) < n:
        _valid_until.extend([-1] * (n - len(_valid_until)))
    elif len(_valid_until) > n:
        _valid_until = _valid_until[:n]

def get_signals(data: pd.DataFrame, i: int) -> bool:
    if i <= 0 or i >= len(data):
        return False

    _ensure_state_size()

    prev_all = bool(data.iloc[i-1].get("all_signals_on")) if ("all_signals_on" in data.columns and i > 0 and pd.notna(data.iloc[i-1].get("all_signals_on"))) else False

    all_on = True
    for signal_idx, (name, fn, ttl_bars) in enumerate(SIGNAL_ORDER, start=1):
        col = name  

        if not all_on:
            data.at[data.index[i], col] = False
            continue

        fired_now = bool(fn(data, i))
        if fired_now:
            _valid_until[signal_idx - 1] = i + max(0, int(ttl_bars))
            active = True
        else:
            active = (i <= _valid_until[signal_idx - 1])
        #store state
        data.at[data.index[i], col] = active
        if not active:
            all_on = False

    data.at[data.index[i], "all_signals_on"] = all_on

    if all_on and not prev_all:
        try:
            print(f"🌟 GOLD STAR formed at {data.index[i].date()}")
        except Exception:
            pass

    return all_on
