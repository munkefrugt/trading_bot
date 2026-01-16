# signals/SignalSequence.py

import uuid


class SignalSequence:
    def __init__(self, start_index, symbol=None):
        self.id = str(uuid.uuid4())[:8]
        self.start_index = start_index
        self.entry_signal_time = None
        self.gold_star_time = None
        self.symbol = symbol

        # --------------------------------------------------
        # Signal progression state (ordered, boolean)
        # --------------------------------------------------
        self.states_dict = {
            "senb_w_future_flat_base": False,
            "senb_w_future_slope_pct": False,
            "trendline_crossings": False,
            "find_pivotline_cross": False,
            "evaluate_regline": False,
            "BB_recent_squeeze": False,
            "BB_cross_paired_with_trendline_cross": False,
        }

        # --------------------------------------------------
        # Persistent STRUCTURAL state (facts, not opinions)
        # --------------------------------------------------
        self.helpers = {
            # ---- BB ↔ Pivot pairing ----
            "bb_pivot_pair_ts": None,
            # ---- Pivot regime ----
            "pivot_support_m": None,
            "pivot_support_b": None,
            "pivot_resistance_m": None,
            "pivot_resistance_b": None,
            "pivot_start_ts": None,
            "pivot_end_ts": None,
            "last_res_pivot_ts": None,
            # ---- Pivot breakout ----
            "pivot_break_val": None,
            "pivot_break_ts": None,
            # ---- Consolidation / segment ----
            "segment_start_ts": None,
            # ---- Frozen regression line ----
            "trend_reg_frozen": False,
            "trend_reg_start_ts": None,
            "trend_reg_end_ts": None,
            "trend_reg_m": None,
            "trend_reg_b": None,
            # ---- Regline ↔ smooth crossings ----
            "trend_reg_cross_ts": None,  # list[pd.Timestamp]
            "trend_reg_cross_count": None,
            # ---- Active pivot-cross candidate ----
            "active_pivot_cross_time": None,
            "active_pivot_cross_source": None,  # "live" | "recovered"
        }

        self.active = False
