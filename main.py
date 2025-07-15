
from analyse import compute_ema, extend_index
from backtest import run_backtest
from plot import plot_price_with_indicators
from metrics import analyze_performance, print_return_distribution,print_trade_results
from analyse import compute_heikin_ashi, compute_ichimoku
from get_data import extend_weekly_index, fetch_btc_weekly_data,fetch_btc_data


def main():
    print("💬 Mr. TradeBotCoach Reminder: Before changing strategy logic, update logbook.txt and consult readchatgpt.txt.")
    data_weekly = fetch_btc_weekly_data()
    data_weekly = extend_weekly_index(data_weekly)
    ha_weekly = compute_heikin_ashi(data_weekly)
    ichimoku_weekly = compute_ichimoku(data_weekly)
    data, buys, sells, trades, equity , cash= run_backtest()
    print(f"{len(buys)} buy signals, {len(sells)} sell signals")

    plot_price_with_indicators(
        data,
        buy_signals=buys,
        sell_signals=sells,
        trades=trades,
        equity_curve=equity,
        cash_series=cash,
        weekly_ha=ha_weekly,        # only if you still want it
        weekly_cloud=ichimoku_weekly  # only if you're still computing it
    )
    #===print trade resmetricsults==
    print_trade_results(trades)
    analyze_performance(trades)
    print_return_distribution(trades)

if __name__ == "__main__":
    main()
