# signals/core.py

from .SignalSequence import SignalSequence
from .senb_w_future_flat_base import senb_w_future_flat_base
from .senb_w_future_slope_pct import senb_w_future_slope_pct
from .trendline_crossings import trendline_crossings
from .BB_recent_squeeze import BB_recent_squeeze
from .BB_daily_close_above_weekly_upper import BB_daily_close_above_weekly_upper
from .has_pivot_line_cross_D_close import has_pivot_line_cross_D_close

# ORDER MATTERS
SIGNALS = [
    senb_w_future_flat_base,
    senb_w_future_slope_pct,
    # TODO fix reg line make it as long as to the breakout or around there.
    # and use sigma 10 crossings to evaluate the regline
    trendline_crossings,
    BB_recent_squeeze,
    has_pivot_line_cross_D_close,
    # TODO Ichimoku warm up issue? first signal dosent show.
    BB_daily_close_above_weekly_upper,
    # TODO New plan:
    # So i gotta get 2 signals. Both the signal og BB upper crossing.
    # So something like, first there has to be have been a cross of daily and pivot line.
    #  and then not long after (14 days)an other cross of BB upper and dailyclose cross.
    # incorporate the recent squece into Sequence object. (maybe)
    # also make a failsafe like if a new peak BB is made abandone signal sequence.
]

# global sequence storage (all symbols)
list_of_signal_sequences = []

# anti-spam (per symbol)
MIN_BARS_BETWEEN_SEQS = 5


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
    # ----------------------------------------------------------
    for seq in list_of_signal_sequences:
        if not seq.active or seq.symbol != symbol:
            continue

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
