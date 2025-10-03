# signals/core.py
import pandas as pd

from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
from .trendline_crossings import trendline_crossings
# from .chikou_free import chikou_free

months = 14

# define signals in a readable way
SIGNAL_ORDER = [
    {"name": "senb_w_future_flat_base", "fn": senb_w_future_flat_base, "ttl": 7*4*months},
    {"name": "senb_w_future_slope_pct", "fn": senb_w_future_slope_pct, "ttl": 7*4*months},
    {"name": "trendline_crossings", "fn": trendline_crossings, "ttl": 7*4*months},
    # {"name": "chikou_free", "fn": chikou_free, "ttl": 7*4*months},
]


def _ensure_state_cols(data: pd.DataFrame):
    """Make sure TTL and state columns exist in the DataFrame."""
    for sig in SIGNAL_ORDER:
        if sig["name"] not in data.columns:
            data[sig["name"]] = False
        ttl_col = f"{sig['name']}__ttl"
        if ttl_col not in data.columns:
            data[ttl_col] = -1
    if "all_signals_on" not in data.columns:
        data["all_signals_on"] = False


def get_signals(data: pd.DataFrame, i: int) -> bool:
    if i <= 0 or i >= len(data):
        return False

    _ensure_state_cols(data)

    prev_all = bool(data.iloc[i - 1]["all_signals_on"]) if i > 0 else False
    all_on = True
    row_idx = data.index[i]

    for sig in SIGNAL_ORDER:
        name = sig["name"]
        fn = sig["fn"]
        ttl_bars = sig["ttl"]
        ttl_col = f"{name}__ttl"

        if not all_on:
            data.at[row_idx, name] = False
            data.at[row_idx, ttl_col] = -1
            continue

        prev_ttl = int(data.iloc[i - 1][ttl_col]) if i > 0 else -1

        if i <= prev_ttl:  # still valid inside TTL
            active = True
            new_ttl = prev_ttl
        else:  # TTL expired → check the function
            if fn(data, i):
                active = True
                new_ttl = i + ttl_bars
            else:
                active = False
                new_ttl = -1

        data.at[row_idx, name] = active
        data.at[row_idx, ttl_col] = new_ttl

        if not active:
            all_on = False

    data.at[row_idx, "all_signals_on"] = all_on

    # 🌟 GOLD STAR handling
    if all_on and not prev_all:
        try:
            print(f"🌟 GOLD STAR formed at {pd.to_datetime(row_idx).date()}")
        except Exception:
            pass

        # mark the gold star day
        if "gold_star" not in data.columns:
            data["gold_star"] = False
        data.at[row_idx, "gold_star"] = True

        # reset ALL signals + TTLs so next star can appear
        for sig in SIGNAL_ORDER:
            name = sig["name"]
            data.at[row_idx, name] = False
            data.at[row_idx, f"{name}__ttl"] = -1
        data.at[row_idx, "all_signals_on"] = False
        
    return all_on


def reset_signal_state(data: pd.DataFrame):
    """Clear all TTLs and signals in the DataFrame."""
    _ensure_state_cols(data)
    for sig in SIGNAL_ORDER:
        data[sig["name"]] = False
        data[f"{sig['name']}__ttl"] = -1
    data["all_signals_on"] = False
