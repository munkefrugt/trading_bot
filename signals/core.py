from .SignalSequence import SignalSequence
import pandas as pd
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
from .trendline_crossings import trendline_crossings
from .BB_recent_squeeze import BB_recent_squeeze

# just a plain list of signal functions, simple and clear
SIGNALS = [
    senb_w_future_flat_base,
    senb_w_future_slope_pct,
    trendline_crossings,
    #TODO. ændre trendline.py til kun at bruge toppe til at bygge trendlines. 
    #TODO insure it actualy had a squeeze in its signal sequeze object
    #BB_recent_squeeze,
]

list_of_signal_sequences = []


def check_signal_sequence(data, i, symbol="BTC-USD"):
    global list_of_signal_sequences

    # 1️⃣ find any active sequence or None
    active_seq_object = next((s for s in list_of_signal_sequences if s.active), None)

    # 2️⃣ if none active -> maybe start new one
    first_func = SIGNALS[0]
    if active_seq_object is None:
        if first_func(data, i): 
            # make new sequence object 
            seq = SignalSequence(start_index=i, symbol=symbol)
            seq.active = True
            # mark first signal as triggered
            seq.states_dict[first_func] = True
            # add to list
            list_of_signal_sequences.append(seq)
            print(f"🟢 New SignalSequence started at {data.index[i].date()}")
        return False

    # 3️⃣ loop over signals and trigger next one
    for func in SIGNALS:
        is_sequence_state = active_seq_object.states_dict.get(func, False)
        if not is_sequence_state:
            if func(data, i):
                active_seq_object.states_dict[func] = True
                print(f"✅ {func.__name__} triggered at {data.index[i].date()}")
            break

    # 4️⃣ check if all signals are done
    if all(active_seq_object.states_dict.get(func, False) for func in SIGNALS):
        active_seq_object.done = True
        active_seq_object.active = False
        data.at[data.index[i], "gold_star"] = True
        print(f"🌟 GOLD STAR at {data.index[i].date()}")
        return True

    return False
