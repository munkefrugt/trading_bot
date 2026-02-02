# signals/core.py

from .SignalSequence import SignalSequence
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
from .trendline_breakout import trendline_breakout
from .BB_recent_squeeze import BB_recent_squeeze

from .BB_cross_paired_with_trendline_cross import BB_cross_paired_with_trendline_cross
from .find_pivotline_cross import find_pivotline_cross
from .evaluate_range_tension import evaluate_range_tension

from .helpers.cloud_future_check import future_week_sena_below_senb
from .helpers.find_start_of_consolidation import find_start_of_consolidation

# ORDER MATTERS
SIGNALS = [
    senb_w_future_flat_base,
    find_start_of_consolidation,  # TODO spawn differnt starting points. ?
    trendline_breakout,
    find_pivotline_cross,
    evaluate_range_tension,  # TODO TO week. some trends pass that really shouldnt!
    # BB_recent_squeeze,
    # BB_cross_paired_with_trendline_cross,
    # TODO
    # I have to try to trade if a valid res line is broken.
    # maybe place the trade when it goes abit above the line to avoid fakeout?.
    # maybe the filter that price has to be above W sen A and W senB is to strict?
    #
    # TODO
]

# global sequence storage (all symbols)
list_of_signal_sequences = []

# anti-spam (per symbol)
MIN_BARS_BETWEEN_SEQS = 60


def check_signal_sequence(data, i, symbol="BTC-USD"):
    global list_of_signal_sequences

    # ----------------------------------------------------------
    # 1️⃣ Decide whether we are allowed to start a new sequence
    #    (SYMBOL-SPECIFIC)
    # ----------------------------------------------------------
    recent_active = any(
        s.active and s.symbol == symbol and (i - s.start_index) < MIN_BARS_BETWEEN_SEQS
        for s in list_of_signal_sequences
    )

    if not recent_active:
        first_func = SIGNALS[0]
        new_seq = SignalSequence(start_index=i, symbol=symbol)

        if first_func(data, i, new_seq):
            new_seq.active = True
            new_seq.states_dict[first_func] = True
            list_of_signal_sequences.append(new_seq)
            print(
                f"🟢 New SignalSequence started at {data.index[i].date()} | "
                f"symbol={symbol} | seq={new_seq.id}"
            )

    # ----------------------------------------------------------
    # 2️⃣ Advance ALL active sequences (same symbol only)
    #     + KILL SWITCH
    # ----------------------------------------------------------
    for seq in list_of_signal_sequences:
        if not seq.active or seq.symbol != symbol:
            continue

        # 🛑 Kill switch
        if seq.entry_signal_time is None and future_week_sena_below_senb(data, i):
            seq.active = False
            print(
                f"🛑 Sequence killed (weekly future SenA < SenB) at "
                f"{data.index[i].date()} | symbol={symbol} | seq={seq.id}"
            )
            continue

        # ▶️ Advance signals IN ORDER
        for func in SIGNALS:
            if not seq.states_dict.get(func, False):
                if func(data, i, seq):
                    seq.states_dict[func] = True
                    print(
                        f"✅ {func.__name__} triggered at {data.index[i].date()} | "
                        f"symbol={symbol} | seq={seq.id}"
                    )
                break

    # ----------------------------------------------------------
    # 3️⃣ Check if ANY sequence completed (same symbol)
    # ----------------------------------------------------------
    winners = [
        s
        for s in list_of_signal_sequences
        if s.active
        and s.symbol == symbol
        and all(s.states_dict.get(func, False) for func in SIGNALS)
    ]

    if winners:
        winner = winners[0]

        data.at[data.index[i], "gold_star"] = True
        print(
            f"🌟 GOLD STAR at {data.index[i].date()} | "
            f"symbol={symbol} | seq={winner.id}"
        )

        # terminate only sequences for THIS symbol
        for s in list_of_signal_sequences:
            if s.symbol == symbol:
                s.active = False

        return True

    return False
