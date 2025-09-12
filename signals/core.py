# signals/core.py
import pandas as pd
from typing import Callable, List, Tuple
import math

# === Test lamps (only these two for now) ===
from .ema50_over_200 import ema50_over_200
from .ema200_over_2y import ema200_over_2y

# from .senb_up_after_flat import senb_up_after_flat_base
# from .bb_up_from_flat import bb_up_from_flat
# from .chikou_free import chikou_free
# from .clear_trendline_breakout import clear_trendline_breakout

Lamp = Tuple[str, Callable[[pd.DataFrame, int], bool], int]  # (name, fn, ttl_bars)

# TTLs let a lamp "wait" for the next one
LAMP_ORDER: List[Lamp] = [
    ("Lamp1_EMA50_over_200", ema50_over_200, 30),  # ~1.5 months (daily)
    ("Lamp2_EMA200_over_2y", ema200_over_2y, 60),  # ~3 months
    # ("Lamp3_SenB_up_after_flat", senb_up_after_flat_base, 60),
    # ("Lamp4_BB_up_from_flat",    bb_up_from_flat,          20),
    # ("Lamp5_Chikou_free",        chikou_free,              40),
    # ("Lamp6_Clear_TL_breakout",  clear_trendline_breakout, 10),
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
    if prev_valid_until_i >= 0:
        _set_row(data, i, _col_valid_until(name), int(prev_valid_until_i))

def get_signals(data: pd.DataFrame, i: int) -> bool:
    """
    Ordered, stateful lamp pipeline with TTL.
    Returns True only if all lamps are active at index i.
    Writes per-lamp <name>_active, <name>_valid_until_i, and final Gold_Star.
    Also prints when Gold_Star transitions from False -> True.
    """
    if i <= 0 or i >= len(data):
        return False

    # previous gold state (for transition print)
    prev_gold = False
    if "Gold_Star" in data.columns and i > 0:
        prev_val = data.iloc[i-1].get("Gold_Star")
        prev_gold = bool(prev_val) if pd.notna(prev_val) else False

    all_on = True

    for (name, fn, ttl_bars) in LAMP_ORDER:
        prev_valid_until = _get_prev_valid_until(data, i, name)

        if not all_on:
            _deactivate(data, i, name, prev_valid_until)
            continue

        fired_now = bool(fn(data, i))
        if fired_now:
            valid_until = i + max(0, int(ttl_bars))
            _activate(data, i, name, valid_until)
        else:
            if i <= prev_valid_until:
                _activate(data, i, name, prev_valid_until)
            else:
                _deactivate(data, i, name, prev_valid_until)
                all_on = False  # stop chain

    _set_row(data, i, "Gold_Star", all_on)

    # print only on False -> True transition
    if all_on and not prev_gold:
        print(f"🌟 GOLD STAR formed at {data.index[i].date()}")

    return all_on
