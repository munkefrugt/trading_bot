# backtest.py
from trend.trend_check import trend_check
from trade import Trade
from sell import sell_check
from buy import buy_check
import pandas as pd
import numpy as np
from signals.core import get_signals

def run_backtest(data: pd.DataFrame):
    """
    Assumes `data` already has all required columns initialized in main().
    """
    trades, buy_markers, sell_markers, open_trades = [], [], [], []
    cash_series, equity_series, equity_index = [], [], []
    cash = 10000  # Starting capital

    for i in range(52, len(data) - 26):
        current_date = data.index[i]
        close = data['D_Close'].iloc[i]
        if pd.isna(close):
            print(f"⛔ End of valid data at {data.index[i].date()}")
            break

        # === Equity snapshot before trades ===
        current_equity = cash + sum(t.quantity * close for t in open_trades)
        equity_series.append(current_equity)
        equity_index.append(current_date)
        cash_series.append(cash)

 
        # === Buy Check only if Uptrend ===
        #if data['Uptrend'].iloc[i]:
        if  get_signals(data,i):
            print(f"🚀 Buy trigger (Gold Star) at {data.index[i].date()}")
            open_trades, cash, buy_markers, trades, data = buy_check(
                open_trades=open_trades,
                data=data,
                i=i,
                cash=cash,
                buy_markers=buy_markers,
                equity=current_equity,
                trades=trades
            )

        # === Sell Check ===
        open_trades, cash, sell_markers = sell_check(
            open_trades=open_trades,
            data=data,
            i=i,
            cash=cash,
            sell_markers=sell_markers
        )

    equity_df = pd.Series(equity_series, index=equity_index, name="Equity")
    cash_df = pd.Series(cash_series, index=equity_index, name="Cash")
    equity_df = equity_df.reindex(data.index).where(data['D_Close'].notna())
    cash_df = cash_df.reindex(data.index).where(data['D_Close'].notna())

    return data, buy_markers, sell_markers, trades, equity_df, cash_df
