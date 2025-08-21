import config
import pandas as pd
from trade import Trade
from bb_bottleneck_expansion import bb_bottleneck_expansion
def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):

    
    current_date = data.index[i]
    close = data['D_Close'].iloc[i]
    w_ha = config.weekly_data_HA
    # === Indicators ===
    # === Daily EMA lines ===
    ema_9 = data['EMA_9'].iloc[i]
    ema_20 = data['EMA_20'].iloc[i]
    ema_50 = data['EMA_50'].iloc[i]
    ema_100 = data['EMA_100'].iloc[i]
    ema_200 = data['EMA_200'].iloc[i]
    ema_365 = data['EMA_365'].iloc[i]
    

    # === Bollinger Bands ===
    bb_upper = data['D_BB_Upper_20'].iloc[i]
    D_BB_middle = data['D_BB_Middle_20'].iloc[i]
    weekly_bb = config.weekly_bb
    close_above_upper_bb = close > bb_upper


    # === Ichimoku ===
    chiko_span = data['D_Close'].iloc[i]
    D_sen_A = data['D_Senkou_span_A'].iloc[i]
    D_sen_B = data['D_Senkou_span_B'].iloc[i]
    above_daily_cloud = close > max(D_sen_A, D_sen_B)
    D_sen_A_future = data['D_Senkou_span_A_future'].iloc[i]
    D_sen_B_future = data['D_Senkou_span_B_future'].iloc[i]
    D_sen_B_future_prev = data['D_Senkou_span_B_future'].iloc[i - 1]
    D_futere_cloud_green = D_sen_A_future > D_sen_B_future

    W_sen_A = data['W_Senkou_span_A'].iloc[i]
    W_sen_B = data['W_Senkou_span_B'].iloc[i]
    above_weekly_cloud = close > max(W_sen_A, W_sen_B)
    D_sen_B_rising = D_sen_B_future > D_sen_B_future_prev

    #chikou above the price 26 days ago 
    chikou_above_price = chiko_span > data['D_Close'].iloc[i - 26]
    
    DC_1_year = data['DC_Upper_365'].iloc[i-1]

    above_DC_year_line = close > DC_1_year
    w_tenkan_sen = data['W_Tenkan_sen'].iloc[i]
    ema50_rising = data['EMA_50'].iloc[i] > data['EMA_50'].iloc[i - 1]
    # === Buy Condition ===
    bb_expansion, info = bb_bottleneck_expansion(i, min_weeks=5, max_weeks=20)
    weekly_BB_upper_rising = False
    # if weekly_bb[current_date]['W_BB_Upper_20'] > weekly_bb[current_date - pd.Timedelta(days=7)]['W_BB_Upper_20']:
    #     weekly_BB_upper_rising = True
    just_crossed_above_mid_bb = False
    cross_idx = recent_cross_above_midbb_index(data, i)
    if cross_idx is not None:
        just_crossed_above_mid_bb = not_too_far_from_cross(data, i, cross_idx, max_pct=0.03)

    buy_signal = (
        # #above_DC_year_line and

        not open_trades    
        and ema_9 > ema_20> ema_50 > ema_100 > ema_200 > ema_365
        and bb_expansion
        # #close_above_upper_bb and       # BB breakout
        #and above_weekly_cloud     
        #and close > w_tenkan_sen        
        # above_daily_cloud    and
        #and D_futere_cloud_green 
        # chikou_above_price and
        #and has_recently_broken_out_of_cloud(data, i) 
        #and weekly_BB_upper_rising 
        #and just_crossed_above_mid_bb
        # two_consecutive_above_midbb(data, i) and
        #bb_expansion (not working yet)
        #and recent_cross_above_midbb_index(data, i, lookback=5)
        # the new strategy will be something like this: 
        #1st filter (in trend check ichimoku weekly)
    
        #2nd filter: -
        # - weekly BB upperband going upwards (forget weekly lower)
        # - price above weekly middle line

        #3rd filter - 
        # the weekly BB is going up and the price is above the W_BB-middle line 

        # for the sell : if weekly the BB-middle line is crossed we sell. 

    )

    if buy_signal:
        # === Risk Management ===
        stoploss_price = ema_200
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity  # Risk 2% per trade
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            # === Check cash and execute trade ===
            if cash >= cost:
                print(f"✅ BUY [{current_date}] @ {close:.2f} (BB breakout, above cloud)")
                trade = Trade(
                    entry_date=current_date,
                    entry_price=close,
                    quantity=quantity,
                    stoploss=stoploss_price,
                    entry_equity=equity
                )
                trades.append(trade)
                open_trades.append(trade)
                buy_markers.append((current_date, close))
                cash -= cost

    return open_trades, cash, buy_markers, trades, data

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
    m0 = data['D_BB_Middle_20'].iloc[i]
    m1 = data['D_BB_Middle_20'].iloc[i-1]
    c0 = data['D_Close'].iloc[i]
    c1 = data['D_Close'].iloc[i-1]
    return (c1 > m1) and (c0 > m0)

def recent_cross_above_midbb_index(data, i, lookback=10):
    start = max(1, i - lookback)
    for j in range(i, start-1, -1):
        c, m = data['D_Close'].iloc[j], data['D_BB_Middle_20'].iloc[j]
        c_prev, m_prev = data['D_Close'].iloc[j-1], data['D_BB_Middle_20'].iloc[j-1]
        if (c > m) and (c_prev <= m_prev):
            return j
    return None

def not_too_far_from_cross(data, i, cross_idx, max_pct=0.03):
    if cross_idx is None:
        return False
    cross_basis = data['D_BB_Middle_20'].iloc[cross_idx]
    curr = data['D_Close'].iloc[i]
    if cross_basis <= 0: 
        return False
    return (curr - cross_basis) / cross_basis <= max_pct

def chikou_free(data, i, window=26):
    if i - window < 0:
        return False
    chikou = data['D_Close'].iloc[i]
    past_price = data['D_Close'].iloc[i - window]
    past_span_a = data['D_Senkou_span_A'].iloc[i - window]
    past_span_b = data['D_Senkou_span_B'].iloc[i - window]
    return (chikou > past_price) and (chikou > max(past_span_a, past_span_b))
