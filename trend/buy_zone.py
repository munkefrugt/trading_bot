# trend/buy_zone.py

import pandas as pd
import config

from trend.senb_consolidation import mark_consolidation_zone
from trend.regression_line import build_regression_from_last_adjusted_start
from trend.flatness import calc_flatness_from_last_adjusted_start
from trend.count_cross_regline import count_regline_crosses_consolidation
from trend.senb_flat import check_senb_flat  # kept
from trend.consolidation_extend import extend_consolidation_start_by_height  # NEW

# Tunables (override via config if you like)
FLAT_THRESHOLD = getattr(config, "FLAT_THRESHOLD", 0.04)              # 8w local flatness gate
BREAKOUT_PCT = getattr(config, "BREAKOUT_PCT", 0.01)
SEN_A_BUFFER = getattr(config, "SEN_A_BUFFER", 0.01)
LOOKBACK_W = getattr(config, "LOOKBACK_W", 8)

# Long-flat requirement before entry
LONG_FLAT_MIN_WEEKS = getattr(config, "LONG_FLAT_MIN_WEEKS", 16)
LONG_FLAT_THRESHOLD = getattr(config, "LONG_FLAT_THRESHOLD", 0.04)

# Consolidation extension knobs (simple second marker)
CONSOL_EXT_MONTHS_BACK    = getattr(config, "CONSOL_EXT_MONTHS_BACK", 6)
CONSOL_EXT_HEIGHT_TOL_PCT = getattr(config, "CONSOL_EXT_HEIGHT_TOL_PCT", 0.03)
CONSOL_EXT_MIN_GAP_DAYS   = getattr(config, "CONSOL_EXT_MIN_GAP_DAYS", 21)
CONSOL_EXT_FWD_SCAN_DAYS  = getattr(config, "CONSOL_EXT_FWD_SCAN_DAYS", 120)


# --- Helper: detect a “recent flat base” that ended within N weeks ---
def find_recent_flat_base(
    w: pd.DataFrame,
    w_pos: int,
    lookback_w: int = 8,
    flat_threshold: float = 0.04,
    recency_weeks: int = 3,
    col: str = "W_Senkou_span_B_future",
):
    """
    Scan back up to `recency_weeks` from the current weekly index for any complete
    `lookback_w` window whose flatness ratio < `flat_threshold`.
    Returns: (found: bool, flat_window_end_wpos: int | None)
    """
    if w_pos - lookback_w < 0:
        return False, None

    start_wpos = max(lookback_w, w_pos - recency_weeks)
    for t in range(w_pos, start_wpos - 1, -1):  # most-recent first
        seg = w[col].iloc[t - lookback_w: t]
        m = seg.mean()
        if len(seg) == lookback_w and pd.notna(m) and m != 0:
            rng = (seg.max() - seg.min()) / m
            if rng < flat_threshold:
                return True, t
    return False, None


def check_buy_zone_and_apply(data, i, w_pos):
    """
    Encapsulates CASE 1 (Buy Zone) logic.
    Mutates and returns `data`. Safe no-op if preconditions aren’t met.
    """
    if i < 0 or i >= len(data) or w_pos is None or w_pos <= 0:
        return data

    w = config.ichimoku_weekly
    if w_pos >= len(w):
        return data

    current_date = data.index[i]

    # Pull daily fields
    D_close = data.at[current_date, 'D_Close']
    Ema_200 = data.at[current_date, 'EMA_200']

    # Pull weekly fields (current and prev)
    w_row = w.iloc[w_pos]
    w_senA = w_row['W_Senkou_span_A']
    w_senB = w_row['W_Senkou_span_B']
    w_senA_future = w_row['W_Senkou_span_A_future']
    w_senB_future = w_row['W_Senkou_span_B_future']
    w_senA_future_prev = w['W_Senkou_span_A_future'].iloc[w_pos - 1]
    w_senB_future_prev = w['W_Senkou_span_B_future'].iloc[w_pos - 1]

    # Local (8w) flatness around current point
    if w_pos - LOOKBACK_W < 0:
        return data
    w_senB_past = w['W_Senkou_span_B_future'].iloc[w_pos - LOOKBACK_W: w_pos]
    flat_base_avg = w_senB_past.mean()
    if not pd.notna(flat_base_avg) or flat_base_avg == 0:
        return data
    senb_flat_range = (w_senB_past.max() - w_senB_past.min()) / flat_base_avg

    # Early trend direction check
    if not (w_senB_future > w_senB_future_prev):
        return data

    # Long flat stretch gate (e.g., last 16w)
    long_flat_ok, long_flat_range, long_flat_avg = check_senb_flat(
        w,
        w_pos,
        min_weeks=LONG_FLAT_MIN_WEEKS,
        flat_threshold=LONG_FLAT_THRESHOLD,
        col="W_Senkou_span_B_future",
    )
    # flag for visibility
    data.at[current_date, 'long_flat_senb'] = bool(long_flat_ok)

    # Recent-flat detector (≤3 weeks)
    recent_flat, recent_flat_wpos = find_recent_flat_base(
        w, w_pos, lookback_w=LOOKBACK_W, flat_threshold=FLAT_THRESHOLD, recency_weeks=3
    )
    data.at[current_date, "recent_flat_base"] = bool(recent_flat)
    if recent_flat and recent_flat_wpos is not None:
        data.at[current_date, "recent_flat_base_w_end_idx"] = int(recent_flat_wpos)

    # Confirmation gates
    sen_a_confirm = (w_senA_future > w_senB_future * (1 + SEN_A_BUFFER))
    slope_EMA_365_flat = abs(data['EMA_365_slope_%'].iloc[i]) < 7
    slope_EMA_2y_flat = abs(data['EMA_2y_slope_%'].iloc[i]) < 3

    # Weekly SenB slope estimate (projected 26w ahead; same as before)
    w_sen_b_future_slope_estimate = data['W_Senkou_span_B_slope_pct'].iloc[i + 26*7]
    slope_ok = 2 < float(w_sen_b_future_slope_estimate) < 5

    # Wiggle room: either currently flat OR recently-flat-with-slope
    flat_gate_ok = (senb_flat_range < FLAT_THRESHOLD) or (recent_flat and slope_ok)

    buy_gates = (
        True
        # long_flat_ok and                    # optional hard gate (disabled)
        and D_close > w_senA
        and D_close > w_senB
        and D_close > Ema_200
        and flat_gate_ok                      # was: senb_flat_range < FLAT_THRESHOLD
        # and w_senB_future > flat_base_avg * (1 + BREAKOUT_PCT)
        # and w_senA_future > w_senA_future_prev
        # and w_senB_future > w_senB_future_prev
        # and sen_a_confirm
        and slope_ok                          # healthy rise requirement
        # and slope_EMA_365_flat
        # and slope_EMA_2y_flat
    )

    if not buy_gates:
        return data

    # Final actions when entering buy zone
    future_index = i + (26 * 7)
    future_date = None
    if future_index < len(data):
        future_date = data.index[future_index]
        data.at[future_date, 'W_SenB_Future_flat_to_up_point'] = True

    data.at[data.index[i], 'Real_uptrend_start'] = True
    data.at[current_date, 'Uptrend'] = True
    data.at[current_date, 'Trend_Buy_Zone'] = True
    print(f"📈 Entering Buy Zone: {current_date} (W_SenA confirmed & price in/above D cloud)")

    if future_date is not None:
        data = mark_consolidation_zone(data, current_date=future_date)

    # --- NEW: simple second consolidation marker (half-year lookback, similar height) ---
    data = extend_consolidation_start_by_height(
        data,
        current_index=i,
        source_flag_col="W_SenB_Consol_Start_Price_Adjusted",
        target_flag_col="W_SenB_Consol_start_Adj_jump_6_months",
        y_col="D_Close",
        months_back=CONSOL_EXT_MONTHS_BACK,
        height_tol_pct=CONSOL_EXT_HEIGHT_TOL_PCT,
        min_gap_days=CONSOL_EXT_MIN_GAP_DAYS,
        forward_scan_days=CONSOL_EXT_FWD_SCAN_DAYS
    )

    if not data["W_SenB_Consol_start_Adj_jump_6_months"].fillna(False).any():
        # copy seed into target if somehow missing
        seed_mask = data.get("W_SenB_Consol_Start_Price_Adjusted", pd.Series(False, index=data.index)).fillna(False)
        if seed_mask.any():
            data["W_SenB_Consol_start_Adj_jump_6_months"] = False
            data.loc[seed_mask.idxmax(), "W_SenB_Consol_start_Adj_jump_6_months"] = True

    # Build regression using (possibly) earlier start
    data, r_2 = build_regression_from_last_adjusted_start(
        data,
        current_index=i,
        out_col="Regline_from_last_adjusted",
        flag_col="W_SenB_Consol_start_Adj_jump_6_months",
        min_points=5,
    )
    print(r_2)

    # Flatness metric on extended window
    flatness = calc_flatness_from_last_adjusted_start(
        data,
        current_index=i,
        y_col="D_Close",
        flag_col="W_SenB_Consol_start_Adj_jump_6_months",
        min_points=5,
    )
    if flatness is not None:
        data.loc[current_date, "Flatness_ratio"] = flatness
        print("Flatness:", flatness)

    # Crossing density using your existing utility
    crosses = count_regline_crosses_consolidation(
        data,
        price_col="EMA_50",
        line_col="Regline_from_last_adjusted",
        flag_col="W_SenB_Consol_start_Adj_jump_6_months",
        end_index=i,
    )
    data.at[current_date, "regline_crosses"] = float(crosses)
    data.at[current_date, "regline_aproved"] = bool((crosses > 2) or (r_2 is not None and r_2 > 0.9))

    return data
