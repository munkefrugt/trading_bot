# signals/SignalSequence.py
import uuid

class SignalSequence:
    def __init__(self, start_index,symbol=None):
        self.id = str(uuid.uuid4())[:8]
        self.start_index = start_index
        self.entry_signal_time = None
        self.gold_star_time = None
        self.symbol = symbol
        self.states_dict = {
            "senb_w_future_flat_base": False,
            "senb_w_future_slope_pct": False,
            "trendline_crossings": False
        }

        self.helpers = {
        "W_SenB_Consol_Start_Price": None,
        "W_SenB_Consol_Start_SenB": None,
        "W_SenB_Future_slope_ok_point": None,
        "trendline_crossings_count": 0,
        # etc.
        }
        self.active = False
