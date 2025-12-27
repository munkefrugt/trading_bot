# signals/core.py

from .SignalSequence import SignalSequence
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
from .trendline_crossings import trendline_crossings
from .BB_recent_squeeze import BB_recent_squeeze

# plain list of signal functions (ORDER MATTERS)
SIGNALS = [
    senb_w_future_flat_base,
    senb_w_future_slope_pct,
    trendline_crossings,
    # BB_recent_squeeze,
]

# global storage of sequences
list_of_signal_sequences = []


def check_signal_sequence(data, i, symbol="BTC-USD"):
    global list_of_signal_sequences

    # ----------------------------------------------------------
    # 1️⃣ ALWAYS allow starting new sequences
    # ----------------------------------------------------------
    first_func = SIGNALS[0]
    new_seq = SignalSequence(start_index=i, symbol=symbol)

    if first_func(data, i, new_seq):
        new_seq.active = True
        new_seq.states_dict[first_func] = True
        list_of_signal_sequences.append(new_seq)
        print(
            f"🟢 New SignalSequence started at {data.index[i].date()} | seq={new_seq.id}"
        )

    # ----------------------------------------------------------
    # 2️⃣ Advance ALL active sequences
    # ----------------------------------------------------------
    for seq in list_of_signal_sequences:
        if not seq.active:
            continue

        for func in SIGNALS:
            if not seq.states_dict.get(func, False):
                if func(data, i, seq):
                    seq.states_dict[func] = True
                    print(
                        f"✅ {func.__name__} triggered at {data.index[i].date()} | seq={seq.id}"
                    )
                break  # only advance one step per bar

    # ----------------------------------------------------------
    # 3️⃣ Check if ANY sequence completed
    # ----------------------------------------------------------
    winners = [
        s
        for s in list_of_signal_sequences
        if s.active and all(s.states_dict.get(func, False) for func in SIGNALS)
    ]

    if winners:
        winner = winners[0]  # first across the line wins

        data.at[data.index[i], "gold_star"] = True
        print(f"🌟 GOLD STAR at {data.index[i].date()} | seq={winner.id}")

        # terminate all sequences (winner included)
        for s in list_of_signal_sequences:
            s.active = False

        return True

    return False
