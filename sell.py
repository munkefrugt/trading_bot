from trade import Trade
import config
import pandas as pd

def sell_check(open_trades, data, i, cash, sell_markers):
    if i == 0:
        return open_trades, cash, sell_markers

    current_date = data.index[i]
    close = data['D_Close'].iloc[i]

    # === Ichimoku lines ===
    D_sen_A_future = data['D_Senkou_span_A_future'].iloc[i]
    D_sen_B_future = data['D_Senkou_span_B_future'].iloc[i]
    D_sen_A = data['D_Senkou_span_A'].iloc[i]
    D_sen_B = data['D_Senkou_span_B'].iloc[i]
    kijun_sen = data['D_Kijun_sen'].iloc[i]
    d_tenkan_sen = data['D_Tenkan_sen'].iloc[i]

    # === Weekly HMA (from config) ===
    w_hma = config.weekly_HMA  # weekly-indexed DF
    wk_idx = w_hma.index.asof(current_date)
    if pd.isna(wk_idx):
        return open_trades, cash, sell_markers

    w_hma_14  = w_hma.loc[wk_idx, "W_HMA_14"]
    w_hma_25  = w_hma.loc[wk_idx, "W_HMA_25"]
    w_hma_50  = w_hma.loc[wk_idx, "W_HMA_50"]
    w_hma_100 = w_hma.loc[wk_idx, "W_HMA_100"]

    ema_9  = data['EMA_9'].iloc[i]

    # === Daily Heikin-Ashi (optional) ===
    w_open = data['W_HA_Open'].iloc[i]
    w_close = data['W_HA_Close'].iloc[i]
    ha_red = w_close < w_open

    # === SELL CONDITION: close below the entire daily cloud ===
    broke_below_cloud = ema_9 < min(D_sen_A, D_sen_B)

    for trade in open_trades[:]:
        if broke_below_cloud:
            #print(f"⛔ SELL triggered on {current_date.date()} (close below daily cloud)")
            trade.close(exit_date=current_date, exit_price=close)
            cash += trade.exit_price * trade.quantity
            sell_markers.append((current_date, close))
            open_trades.remove(trade)

    return open_trades, cash, sell_markers
