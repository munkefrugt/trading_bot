# buy.py
import config
import pandas as pd
from trade import Trade
from bb_bottleneck_expansion import bb_bottleneck_expansion


def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):
    """
    ENTRY (simple & testable):
      - EMA staircase (9 > 20 > 50 > 100 > 200 > 365)
      - Weekly BB squeeze recently + (confirmed expansion OR price breakout)

    STOP:
      - Stoploss at EMA200 at entry.
    """

    current_date = data.index[i]
    close = data["D_Close"].iloc[i]

    # === Daily EMAs ===
    ema_9 = data["EMA_9"].iloc[i]
    ema_20 = data["EMA_20"].iloc[i]
    ema_50 = data["EMA_50"].iloc[i]
    ema_100 = data["EMA_100"].iloc[i]
    ema_200 = data["EMA_200"].iloc[i]
    ema_365 = data["EMA_365"].iloc[i]

    # === Daily BB (kept in case you want to re-enable mid/upper checks) ===
    bb_upper = data["D_BB_Upper_20"].iloc[i]
    D_BB_middle = data["D_BB_Middle_20"].iloc[i]
    close_above_upper_bb = close > bb_upper  # not used in the minimal rule

    # === Ichimoku (kept for future filters; not used in minimal rule) ===
    chiko_span = data["D_Close"].iloc[i]
    D_sen_A = data["D_Senkou_span_A"].iloc[i]
    D_sen_B = data["D_Senkou_span_B"].iloc[i]
    above_daily_cloud = close > max(D_sen_A, D_sen_B)

    D_sen_A_future = data["D_Senkou_span_A_future"].iloc[i]
    D_sen_B_future = data["D_Senkou_span_B_future"].iloc[i]
    D_sen_B_future_prev = data["D_Senkou_span_B_future"].iloc[i - 1]
    D_future_cloud_green = D_sen_A_future > D_sen_B_future
    D_sen_B_rising = D_sen_B_future > D_sen_B_future_prev

    W_sen_A = data["W_Senkou_span_A"].iloc[i]
    W_sen_B = data["W_Senkou_span_B"].iloc[i]
    above_weekly_cloud = close > max(W_sen_A, W_sen_B)

    # Chikou above price 26 days ago
    chikou_above_price = chiko_span > data["D_Close"].iloc[i - 26]

    # Donchian (not used now; kept)
    DC_1_year = data["DC_Upper_365"].iloc[i - 1]
    DC_26 = data["DC_Upper_26"].iloc[i - 1]

    above_DC_year_line = close > DC_1_year
    above_DC_26_line = close > DC_26
    # Extra signals you might reuse later
    w_tenkan_sen = data["W_Tenkan_sen"].iloc[i]
    w_kijun_sen = data["W_Kijun_sen"].iloc[i]
    ema50_rising = data["EMA_50"].iloc[i] > data["EMA_50"].iloc[i - 1]

    # === Weekly HMA (from config) ===
    w_hma = config.weekly_HMA  # weekly-indexed DF

    # map daily date -> most recent weekly date
    wk_idx = w_hma.index.asof(current_date)  # returns the last index <= current_date (or NaT)

    if pd.isna(wk_idx):
        # not enough history yet; bail out gracefully
        return open_trades, cash, buy_markers, trades, data

    w_hma_14  = w_hma.loc[wk_idx, "W_HMA_14"]
    w_hma_25  = w_hma.loc[wk_idx, "W_HMA_25"]
    w_hma_50  = w_hma.loc[wk_idx, "W_HMA_50"]
    w_hma_100 = w_hma.loc[wk_idx, "W_HMA_100"]

    # === Weekly BB squeeze/expansion (from separate module) ===
    # Pass the daily timestamp; the module maps to the right weekly bar.
    bb_ok, bbinfo = bb_bottleneck_expansion(
        current_date,
        min_weeks=8,         # tune later
        max_weeks=30,        # tune later
        tight_quantile=0.25, # 25th percentile tightness
        flat_window=5,       # weeks around squeeze to assess flatness
        flat_slope=0.0015,   # "flat" threshold for the middle band slope
        expand_ratio=1.8,    # how much wider vs squeeze to call "expanded"
        expand_confirm_weeks=4,  # steady increase weeks (allow 1 down)
    )
    had_tight = bool(bbinfo.get("was_tight", False))
    price_breakout = bool(bbinfo.get("price_breakout", False))
    weekly_squeeze_condition = bool(bb_ok or (had_tight and price_breakout))

    # === Minimal BUY condition ===
    buy_signal = (
        not open_trades     
        # use only ichimoku
        # coarse filter(weekly stuff):
        # Note: Senkou B vs. Donchian Breakout
        # A yearly Donchian breakout with a flat-channel condition and a weekly Senkou B rising from a long flat period are essentially the same concept.

        # Flat Senkou B = market has consolidated in a range.

        # Senkou B turns up = breakout and start of a new long-term trend.

        # This removes the need to build a separate “flat channel detector,” since Senkou B naturally encodes both the flat base and the shift in trend.

        # fine filter (daily stuff):

        # use the trendcheck as buy function!!!!!!!!!!!!!!
         
        #chikou (clear sky path. )
        #and above_DC_year_line # weekly chikou
        #and chikou_above_price
        and above_DC_26_line

        #cloud stuff
        #and above_daily_cloud
        and D_future_cloud_green
       
    )

    if buy_signal:
        # === Risk management ===
        stoploss_price = float(ema_200)  # simple, reproducible stop
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity  # risk 2% per trade
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            if cash >= cost:
                print(
                    f"✅ BUY [{current_date}] @ {close:.2f} "
                    f"(EMA staircase + weekly BB squeeze breakout/expansion)"
                )
                trade = Trade(
                    entry_date=current_date,
                    entry_price=close,
                    quantity=quantity,
                    stoploss=stoploss_price,
                    entry_equity=equity,
                )
                trades.append(trade)
                open_trades.append(trade)
                buy_markers.append((current_date, close))
                cash -= cost

    return open_trades, cash, buy_markers, trades, data


# =========================
# Helpers (kept from your original)
# =========================
def has_recently_broken_out_of_cloud(data, current_index, lookback=14):
    """
    Check if price has broken out of the Ichimoku cloud within the last `lookback` candles.
    Uses daily Senkou Span A/B columns.
    """
    for j in range(max(0, current_index - lookback), current_index + 1):
        price = data["D_Close"].iloc[j]
        senkou_a = data["D_Senkou_span_A"].iloc[j]
        senkou_b = data["D_Senkou_span_B"].iloc[j]

        cloud_top = max(senkou_a, senkou_b)
        cloud_bottom = min(senkou_a, senkou_b)

        if price > cloud_top or price < cloud_bottom:
            return True
    return False


def two_consecutive_above_midbb(data, i):
    if i < 1:
        return False
    m0 = data["D_BB_Middle_20"].iloc[i]
    m1 = data["D_BB_Middle_20"].iloc[i - 1]
    c0 = data["D_Close"].iloc[i]
    c1 = data["D_Close"].iloc[i - 1]
    return (c1 > m1) and (c0 > m0)


def recent_cross_above_midbb_index(data, i, lookback=10):
    start = max(1, i - lookback)
    for j in range(i, start - 1, -1):
        c, m = data["D_Close"].iloc[j], data["D_BB_Middle_20"].iloc[j]
        c_prev, m_prev = data["D_Close"].iloc[j - 1], data["D_BB_Middle_20"].iloc[j - 1]
        if (c > m) and (c_prev <= m_prev):
            return j
    return None


def not_too_far_from_cross(data, i, cross_idx, max_pct=0.03):
    if cross_idx is None:
        return False
    cross_basis = data["D_BB_Middle_20"].iloc[cross_idx]
    curr = data["D_Close"].iloc[i]
    if cross_basis <= 0:
        return False
    return (curr - cross_basis) / cross_basis <= max_pct


def chikou_free(data, i, window=26):
    if i - window < 0:
        return False
    chikou = data["D_Close"].iloc[i]
    past_price = data["D_Close"].iloc[i - window]
    past_span_a = data["D_Senkou_span_A"].iloc[i - window]
    past_span_b = data["D_Senkou_span_B"].iloc[i - window]
    return (chikou > past_price) and (chikou > max(past_span_a, past_span_b))
