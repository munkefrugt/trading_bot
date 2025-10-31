# signals/core.py
import pandas as pd
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct

from .trendline_crossings import trendline_crossings

#(name, fn, keep_checking) 
SIGNALS = [
    ("senb_w_future_flat_base", senb_w_future_flat_base, False),
    ("senb_w_future_slope_pct", senb_w_future_slope_pct, False),
    ("trendline_crossings", trendline_crossings, True),
]


def start_signal_sequence(data: pd.DataFrame, i: int) -> bool:
    """
    Sequential signal processor with state carry-over.

    - Each signal keeps its state from the previous bar unless reset.
    - A signal function runs only when:
        • all previous signals are active, AND
        • it’s not already True (unless keep_checking=True).
    - Once all signals are True → gold_star.
    """
    if i <= 0 or i >= len(data):
        return False

    # --- Ensure required columns exist ---
    for name, _, _ in SIGNALS:
        if name not in data:
            data[name] = False
    for col in ["gold_star", "sequence_lost"]:
        if col not in data:
            data[col] = False

    # --- Iterate through signals ---
    for idx, (name, fn, keep_checking) in enumerate(SIGNALS):
        prev_state = bool(data.at[data.index[i - 1], name])

        # Check if all previous signals are active at this index
        previous_signals = [s for s, _, _ in SIGNALS[:idx]]
        all_previous_on = all(bool(data.at[data.index[i], s]) for s in previous_signals) if previous_signals else True

        # --- Decide if this function should run ---
        if all_previous_on:
            if not prev_state or keep_checking:
                # run the function
                data.at[data.index[i], name] = fn(data, i)
            else:
                # carry state forward
                data.at[data.index[i], name] = True
        else:
            # carry forward previous state if earlier ones aren’t ready
            data.at[data.index[i], name] = prev_state

    # --- Mark gold star if all signals are True ---
    all_on = all(bool(data.at[data.index[i], s]) for s, _, _ in SIGNALS)
    data.at[data.index[i], "gold_star"] = all_on

    if all_on:
        print(f"🌟 GOLD STAR at {pd.to_datetime(data.index[i]).date()}")
        # reset previous row so the sequence doesn't immediately restart
        for s, _, _ in SIGNALS:
            data.at[data.index[i], s] = False


    return all_on
