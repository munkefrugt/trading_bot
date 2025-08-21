import pandas as pd
import config
from backtest import run_backtest
from plot import plot_price_with_indicators
from metrics import analyze_performance, print_return_distribution,print_trade_results
from calc_indicators import compute_heikin_ashi, compute_ichimoku,compute_bollinger_bands, compute_HMA
from get_data import extend_weekly_index, fetch_btc_weekly_data,fetch_btc_data
from identify_bb_squeeze import identify_bb_squeeze_percentile


from get_data import fetch_btc_weekly_data


def main():
    print("💬 Mr. TradeBotCoach Reminder: Before changing strategy logic, update logbook.txt and consult readchatgpt.txt.")

    weekly_data = fetch_btc_weekly_data()
    print("Weekly data :")

    weekly_data = weekly_data.add_prefix("W_")
    config.weekly_data = weekly_data

 
    config.weekly_data_HA = compute_heikin_ashi(weekly_data, prefix="W_", weekly=True)
    weekly_data_HA = config.weekly_data_HA
    
    config.weekly_bb = compute_bollinger_bands(weekly_data, period=20, std_dev=2, prefix="W_")
    weekly_bb = config.weekly_bb

    # indentify BB squeeze condition
    weekly_bb = identify_bb_squeeze_percentile(weekly_bb, bb_width_col="W_BB_Width_20", window=52, pct=0.15)

    config.weekly_HMA = compute_HMA(weekly_data, periods=[14,25,50,100], prefix="W_")
    #print("Weekly HMA computed.")
    #print(config.weekly_HMA["W_HMA_2"].head(10))

    data, buys, sells, trades, equity , cash= run_backtest()
    print(f"{len(buys)} buy signals, {len(sells)} sell signals")
    
    plot_price_with_indicators(
        data,
        buy_signals=buys,
        sell_signals=sells,
        trades=trades,
        equity_curve=equity,
        cash_series=cash,
        weekly_data_HA=weekly_data_HA
    )
    #===print trade resmetricsults==
    print_trade_results(trades)
    analyze_performance(trades)
    print_return_distribution(trades)

if __name__ == "__main__":
    main()