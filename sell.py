from trade import Trade

import config
import pandas as pd
def sell_check(open_trades, data, i, cash, sell_markers):
    if i == 0:
        return open_trades, cash, sell_markers

    current_date = data.index[i]

    # === Daily EMA lines ===
    ema_9 = data['EMA_9'].iloc[i]
    ema_20 = data['EMA_20'].iloc[i]
    ema_50 = data['EMA_50'].iloc[i]
    ema_100 = data['EMA_100'].iloc[i]
    ema_200 = data['EMA_200'].iloc[i]
    ema_365 = data['EMA_365'].iloc[i]

    close = data['D_Close'].iloc[i]

    prev_close = data['D_Close'].iloc[i - 1]
    prev_ema50 = data['EMA_50'].iloc[i - 1]
    D_sen_A_future = data['D_Senkou_span_A_future'].iloc[i]
    D_sen_B_future = data['D_Senkou_span_B_future'].iloc[i]
    D_sen_A = data['D_Senkou_span_A'].iloc[i]
    D_sen_B = data['D_Senkou_span_B'].iloc[i]

    # === Weekly HMA (from config) ===
    w_hma = config.weekly_HMA  # weekly-indexed DF

    # map daily date -> most recent weekly date
    wk_idx = w_hma.index.asof(current_date)  # returns the last index <= current_date (or NaT)

    if pd.isna(wk_idx):
        # not enough history yet; bail out gracefully
        return open_trades, cash, sell_markers

    w_hma_14  = w_hma.loc[wk_idx, "W_HMA_14"]
    w_hma_25  = w_hma.loc[wk_idx, "W_HMA_25"]
    w_hma_50  = w_hma.loc[wk_idx, "W_HMA_50"]
    w_hma_100 = w_hma.loc[wk_idx, "W_HMA_100"]

    # Weekly Heikin-Ashi values (optional extra filter)
    w_open = data['W_HA_Open'].iloc[i]
    w_close = data['W_HA_Close'].iloc[i]
    ha_red = w_close < w_open
    kijun_sen = data['D_Kijun_sen'].iloc[i]
    # Sell only when the DAILY CLOSE crosses from above/at to below EMA50
    close_crossed_down_ema50 = (prev_close >= prev_ema50) and (close < ema_50)

    # If you want HA confirmation as well, use: (close_crossed_down_ema50 and ha_red)
    # sell signals: 
    w_tenkan_sen = data['W_Tenkan_sen'].iloc[i]
    should_sell = close_crossed_down_ema50
    close_under_kijun_2_days = (
        data['D_Close'].iloc[i] < kijun_sen and
        data['D_Close'].iloc[i -1] < kijun_sen 
    )
    broke_into_cloud = (close < D_sen_A or close < D_sen_B)
    d_tenkan_sen = data['D_Tenkan_sen'].iloc[i]
    should_sell
    
    for trade in open_trades[:]:
        if (#close_crossed_down_ema50 and 
            close < d_tenkan_sen
            #broke_into_cloud
            #w_hma_14 < w_hma_25
            #ema_9 < ema_20
            #close < w_tenkan_sen
            #(close_under_kijun_2_days or D_sen_A_future < D_sen_B_future)

        ):
            print(f"⛔ SELL triggered on {current_date.date()} (close cross below EMA50)")
            trade.close(exit_date=current_date, exit_price=close)
            cash += trade.exit_price * trade.quantity
            sell_markers.append((current_date, close))
            open_trades.remove(trade)

    return open_trades, cash, sell_markers
