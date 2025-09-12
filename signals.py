# signals/core.py
import pandas as pd
from typing import Callable, List, Tuple
import math

# Import your lamp functions (implement separately)
from .senb_up_after_flat import senb_up_after_flat_base
from .bb_up_from_flat import bb_up_from_flat
from .chikou_free import chikou_free
from .clear_trendline_breakout import clear_trendline_breakout

Lamp = Tuple[str, Callable[[pd.DataFrame, int], bool], int]  # (name, fn, ttl_bars)

# You can tweak TTLs to control how long each lamp stays "armed"/valid
LAMP_ORDER: List[Lamp] = [
    ("Lamp1_SenB_up_after_flat", senb_up_after_flat_base, 60),  # ~3 months on daily bars
    ("Lamp2_BB_up_from_flat",    bb_up_from_flat,          20),  # ~1 month
    ("Lamp3_Chikou_free",        chikou_free,              40),
    ("Lamp4_Clear_TL_breakout",  clear_trendline_breakout, 10),
]

def _col_valid_until(name: str) -> str:
    return f"{name}_valid_until_i"

def _col_active(name: str) -> str:
    return f"{name}_active"

def _get_prev_valid_until(data: pd.DataFrame, i: int, name: str) -> int:
    if i <= 0:
        return -1
    col = _col_valid_until(name)
    if col in data.columns:
        val = data.iloc[i-1].get(col)
        # handle NaN gracefully
        if isinstance(val, (int, float)) and not math.isnan(val):
            return int(val)
    return -1

def _set_row(data: pd.DataFrame, i: int, col: str, val):
    data.at[data.index[i], col] = val

def _activate(data: pd.DataFrame, i: int, name: str, valid_until_i: int):
    _set_row(data, i, _col_active(name), True)
    _set_row(data, i, _col_valid_until(name), int(valid_until_i))

def _deactivate(data: pd.DataFrame, i: int, name: str, prev_valid_until_i: int):
    _set_row(data, i, _col_active(name), False)
    # carry previous window forward so plots/debugging can see it
    if prev_valid_until_i >= 0:
        _set_row(data, i, _col_valid_until(name), int(prev_valid_until_i))

def get_signals(data: pd.DataFrame, i: int) -> bool:
    """
    Ordered, stateful lamp pipeline with TTL.
    Each lamp can fire and remain active for `ttl_bars` to 'wait' for subsequent lamps.
    Returns True only if all lamps are active at index i.
    Writes:
      - per-lamp: <LampName>_active (bool), <LampName>_valid_until_i (int)
      - final: Gold_Star (bool)
    """
    if i <= 0 or i >= len(data):
        return False

    all_on = True

    for (name, fn, ttl_bars) in LAMP_ORDER:
        prev_valid_until = _get_prev_valid_until(data, i, name)

        # If *any prior lamp* in order is inactive at this bar, we should not even try later lamps.
        # But to keep their debug columns consistent, we still propagate previous valid_until.
        # We detect that via all_on flag.
        if not all_on:
            _deactivate(data, i, name, prev_valid_until)
            continue

        # Try to fire this lamp now
        fired_now = bool(fn(data, i))
        if fired_now:
            valid_until = i + max(0, int(ttl_bars))
            _activate(data, i, name, valid_until)
        else:
            # If within previous validity window, remain active (waiting)
            if i <= prev_valid_until:
                _activate(data, i, name, prev_valid_until)
            else:
                _deactivate(data, i, name, prev_valid_until)
                all_on = False  # stop the chain; later lamps won't be evaluated

    _set_row(data, i, "Gold_Star", all_on)
    return all_on
