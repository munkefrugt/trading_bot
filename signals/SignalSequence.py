# signals/SignalSequence.py
import uuid


class SignalSequence:
    def __init__(self, start_index, symbol=None):
        self.id = str(uuid.uuid4())[:8]
        self.start_index = start_index
        self.entry_signal_time = None
        self.gold_star_time = None
        self.symbol = symbol

        self.states_dict = {
            "senb_w_future_flat_base": False,
            "senb_w_future_slope_pct": False,
            "trendline_crossings": False,
            "BB_recent_squeeze": False,
        }

        # Persistent structural helpers (STATE, not observations)
        self.helpers = {
            "trendline_crossings_count": 0,
            # Pivot line structure (dominant regime)
            "pivot_support_m": None,
            "pivot_support_b": None,
            "pivot_resistance_m": None,
            "pivot_resistance_b": None,
            "pivot_line_last_update_i": None,
            # ---- Trend regression lock (per pivot regime) ----
            "trend_reg_frozen": False,
            "trend_reg_start_ts": None,
            "trend_reg_end_ts": None,
        }

        self.active = False
