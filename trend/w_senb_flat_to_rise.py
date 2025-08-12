# w_senb_flat_to_rise.py
import numpy as np
import pandas as pd

DEFAULTS = dict(
    shift_weeks=26,
    flat_window_weeks=12,
    # thresholds are now PERCENT per bar (e.g., 0.00005 = 0.005% per bar)
    eps_slope_pct=5e-5,         # |slope| <= 0.005%/bar counts as near-flat
    min_pos_slope_pct=1e-4,     # > 0.01%/bar counts as rising
    min_break_above_flat=0.005, # 0.5% above flat base
    confirm_bars=1,             # start with 1; raise to 2 if too noisy
    sen_a_buffer=0.01
)

def _linreg_slope(y: np.ndarray) -> float:
    if len(y) < 2:
        return 0.0
    x = np.arange(len(y), dtype=float)
    A = np.vstack([x, np.ones(len(x))]).T
    slope, _ = np.linalg.lstsq(A, y.astype(float), rcond=None)[0]
    return float(slope)  # price units per bar

def ensure_column(df: pd.DataFrame, col: str, default=0):
    if col not in df.columns:
        df[col] = default

def detect_senb_flat_to_rise(data: pd.DataFrame, i: int, config: dict | None = None):
    C = {**DEFAULTS, **(config or {})}

    current_date = data.index[i]
    shift = C["shift_weeks"] * 7
    flat_window = C["flat_window_weeks"] * 7

    senb_future = data['W_Senkou_span_B'].shift(-shift)
    sena_future = data['W_Senkou_span_A'].shift(-shift)

    if i - flat_window < 0 or i - 7 < 0:
        ensure_column(data, 'SenB_breakout_count', 0)
        data.at[current_date, 'SenB_breakout_count'] = 0
        return data, False

    senb_past = senb_future.iloc[i - flat_window:i].to_numpy()
    flat_base_avg = float(np.mean(senb_past)) if len(senb_past) else np.nan
    slope_abs = _linreg_slope(senb_past)                 # price units / bar
    slope_pct = slope_abs / flat_base_avg if flat_base_avg else 0.0  # %/bar

    senb_now = float(senb_future.iloc[i])
    senb_prev = float(senb_future.iloc[i - 7])
    sena_now = float(sena_future.iloc[i])

    near_flat = abs(slope_pct) <= C["eps_slope_pct"]
    breakout_level = senb_now > flat_base_avg * (1 + C["min_break_above_flat"])
    slope_turn_up = (slope_pct > C["min_pos_slope_pct"]) and (senb_now >= senb_prev)

    # Daily price filter (same as before)
    price_ok = (
        data['D_Close'].iloc[i - 1] >= min(data['D_Senkou_span_A'].iloc[i - 1], data['D_Senkou_span_B'].iloc[i - 1]) and
        data['D_Close'].iloc[i]     >= min(data['D_Senkou_span_A'].iloc[i],     data['D_Senkou_span_B'].iloc[i])
    )
    sen_a_confirm = sena_now > senb_now * (1 + C["sen_a_buffer"])

    ensure_column(data, 'SenB_breakout_count', 0)
    if slope_turn_up and breakout_level:
        prev = int(data['SenB_breakout_count'].iloc[i - 1]) if i > 0 else 0
        data.at[current_date, 'SenB_breakout_count'] = prev + 1
    else:
        data.at[current_date, 'SenB_breakout_count'] = 0

    # Debug columns
    for k, v in dict(
        SenB_flat_base_avg=flat_base_avg,
        SenB_slope_pct=slope_pct,
        SenB_near_flat=near_flat,
        SenB_breakout_level=breakout_level,
        SenB_slope_turn_up=slope_turn_up,
        SenB_price_ok=price_ok,
        SenB_SenA_confirm=sen_a_confirm,
    ).items():
        ensure_column(data, k, np.nan if "avg" in k or "slope" in k else False)
        data.at[current_date, k] = v

    triggered = (
        near_flat and breakout_level and slope_turn_up and price_ok and sen_a_confirm
        and int(data.at[current_date, 'SenB_breakout_count']) >= C["confirm_bars"]
    )

    if triggered:
        future_index = i + shift
        if future_index < len(data):
            data.at[data.index[future_index], 'W_SenB_Future_flat_to_up_point'] = True

    return data, triggered
