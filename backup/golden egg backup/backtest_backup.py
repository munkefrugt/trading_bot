from trade import Trade
from get_data import fetch_btc_data, fetch_btc_weekly_data, extend_weekly_index
from analyse import compute_ema, compute_ichimoku , extend_index, compute_heikin_ashi
from align_data_time import get_data_with_indicators_and_time_alignment
from sell import sell_check
import pandas as pd

def run_backtest():
    data = get_data_with_indicators_and_time_alignment()

    # === Initialize variables for backtesting ===

    trades = []
    buy_markers = []
    sell_markers = []
    open_trades = []

    cash_series = []

    equity_series = []
    equity_index = []

    cash = 10000  # Starting capital
 

    for i in range(52, len(data) - 26):
        # === Current date and price ===
        current_date = data.index[i]
        close = data['Close'].iloc[i]
        if pd.isna(close):
            print(f"⛔ End of valid data at {data.index[i].date()}")
            break

        # === Equity snapshot before any new trades or exits ===
        current_equity = cash + sum(t.quantity * close for t in open_trades)
        equity_series.append(current_equity)
        equity_index.append(current_date)
        cash_series.append(cash)

        # Indicator values
        ema_50 = data['EMA_50'].iloc[i]
        ema_200 = data['EMA_200'].iloc[i]
        tenkan = data['D_Tenkan_sen'].iloc[i]
        kijun = data['D_Kijun_sen'].iloc[i]
        chikou = data['D_Chikou_span'].iloc[i]
        senkou_a = data['D_Senkou_span_A'].iloc[i]
        senkou_b = data['D_Senkou_span_B'].iloc[i]
        senkou_a_future = data['D_Senkou_span_A'].iloc[i + 26]
        senkou_b_future = data['D_Senkou_span_B'].iloc[i + 26]
        senkou_b_future_prev = data['D_Senkou_span_A'].iloc[i - 25]

        close_26_back = data['Close'].iloc[i - 26] if i >= 26 else None

        cloud_future_is_green = senkou_a_future > senkou_b_future
        cloud_future_is_upgoing = senkou_a_future > senkou_b_future_prev
        
        # === Chikou Span logic ===
        # 26 bars ago, we look at the past price range (at that old index)
        chikou_index = i - 26

        # Extract the highest high in the 26 bars leading up to that point
        chikou_clearance_level = data['High'].iloc[chikou_index - 26 : chikou_index].max()

        # The Chikou line (today's close) must be above that past congestion
        chikou_has_clear_sight = chikou > chikou_clearance_level
        
        # === Trading logic ===
        # Buy condition
        ema_200_past = data['EMA_200'].iloc[i-5]

        ema200_is_rising = ema_200 > ema_200_past

        buy_signal = (  
            #course_filter and
            close > ema_50 > ema_200 and
            cloud_future_is_green and
            cloud_future_is_upgoing and
            close > max(senkou_a, senkou_b) and 
            tenkan > kijun and
            chikou > close_26_back and 
            chikou_has_clear_sight and
            ema200_is_rising
        )


        # Sell condition
        sell_signal = (
            chikou < close_26_back
        )

        # Position sizing based on stoploss and risk

        if buy_signal and not open_trades:
            stoploss_price = ema_200
            risk_per_unit = close - stoploss_price
            if risk_per_unit > 0:
                equity = cash + sum((close - t.entry_price) * t.quantity for t in open_trades)
                max_risk = 0.02 * equity
                quantity = max_risk / risk_per_unit
                cost = quantity * close

                if cash >= cost:
                    print("BUY SIGNAL detected!")
                    print(f"[{current_date}] Buy @ {close:.2f}, Chikou: {chikou:.2f} vs Future Cloud: {senkou_a_future:.2f}/{senkou_b_future:.2f}")
                    trade = Trade(
                        entry_date=current_date,
                        entry_price=close,
                        quantity=quantity,
                        stoploss=stoploss_price,
                        entry_equity = current_equity
                    )
                    trades.append(trade)
                    open_trades.append(trade)
                    buy_markers.append((current_date, close))
                    cash -= cost    


                    
        ## # === Check for existing trades ===
        # # Check each open trade for stoploss or sell signal
        # for trade in open_trades[:]:
        #     if trade.is_stopped_out(close):
        #         print(f"💥 STOPLOSS on {current_date.date()} | Close={close:.2f} | Stoploss={trade.stoploss:.2f}")
        #         trade.close(exit_date=current_date, exit_price=close)
        #         cash += trade.exit_price * trade.quantity
        #         sell_markers.append((current_date, close))
        #         open_trades.remove(trade)

        #     elif sell_signal:
        #         print(f"🔻 SELL SIGNAL on {current_date.date()} | Chikou={chikou:.2f} vs Close={close:.2f} | Trade Entry: {trade.entry_date.date()} @ {trade.entry_price:.2f}")
        #         trade.close(exit_date=current_date, exit_price=close)
        #         cash += trade.exit_price * trade.quantity
        #         sell_markers.append((current_date, close))
        #         open_trades.remove(trade)
        open_trades, cash, sell_markers = sell_check( # det er måske bedre med bare chikou!!!
            open_trades=open_trades,
            data=data,
            i=i,
            cash=cash,
            sell_markers=sell_markers
        )


    equity_df = pd.Series(equity_series, index=equity_index, name="Equity")
    equity_df = equity_df.reindex(data.index).ffill().fillna(method="bfill")
    cash_df = pd.Series(cash_series, index=equity_index, name="Cash")
    return data, buy_markers, sell_markers, trades, equity_df, cash_df