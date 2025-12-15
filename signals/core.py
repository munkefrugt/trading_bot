from .SignalSequence import SignalSequence
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
from .trendline_crossings import trendline_crossings
from .BB_recent_squeeze import BB_recent_squeeze

# plain list of signal functions
SIGNALS = [
    senb_w_future_flat_base,
    senb_w_future_slope_pct,
    trendline_crossings,
    # BB_recent_squeeze,
]

list_of_signal_sequences = []


def check_signal_sequence(data, i, symbol="BTC-USD"):
    global list_of_signal_sequences

    # 1️⃣ find active sequence
    active_seq = next((s for s in list_of_signal_sequences if s.active), None)

    # ----------------------------------------------------------
    # 2️⃣ if none active → maybe start new one
    # ----------------------------------------------------------
    if active_seq is None:
        seq = SignalSequence(start_index=i, symbol=symbol)

        first_func = SIGNALS[0]
        if first_func(data, i, seq):
            seq.active = True
            seq.states_dict[first_func] = True
            list_of_signal_sequences.append(seq)
            print(f"🟢 New SignalSequence started at {data.index[i].date()}")
        return False

    # ----------------------------------------------------------
    # 3️⃣ advance sequence
    # ----------------------------------------------------------
    for func in SIGNALS:
        if not active_seq.states_dict.get(func, False):
            if func(data, i, active_seq):
                active_seq.states_dict[func] = True
                print(f"✅ {func.__name__} triggered at {data.index[i].date()}")
            break

    # ----------------------------------------------------------
    # 4️⃣ sequence complete?
    # ----------------------------------------------------------
    if all(active_seq.states_dict.get(func, False) for func in SIGNALS):
        active_seq.active = False
        data.at[data.index[i], "gold_star"] = True
        print(f"🌟 GOLD STAR at {data.index[i].date()}")
        return True

    return False
