

from backtest import run_backtest
from plot import plot_price_with_indicators
from metrics import analyze_performance, print_return_distribution
from analyse import extend_index
def main():
    print("💬 Mr. TradeBotCoach Reminder: Before changing strategy logic, update logbook.txt and consult readchatgpt.txt.")
    data, ema_list, ichimoku, buys, sells, trades, equity , cash= run_backtest()
    print(f"{len(buys)} buy signals, {len(sells)} sell signals")
    plot_price_with_indicators(data, ema_list, ichimoku, buy_signals=buys, sell_signals=sells, trades=trades, equity_curve=equity, cash_series=cash)
    print("\nTRADE RESULTS:")
    for t in trades:
        if not t.is_open():
            print(f"Trade from {t.entry_date.date()} to {t.exit_date.date()}: "
                  f"{t.profit():.2f} USD ({t.profit_pct():.2f}%)")

    #analyse performance and print return distribution
    analyze_performance(trades)
    print_return_distribution(trades)
if __name__ == "__main__":
    main()