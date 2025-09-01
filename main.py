# main.py
import numpy as np
import pandas as pd
import config
from backtest import run_backtest
from plot import plot_price_with_indicators
from metrics import analyze_performance, print_return_distribution, print_trade_results
from calc_indicators import compute_heikin_ashi, compute_ichimoku, compute_bollinger_bands, compute_HMA
from get_data import extend_weekly_index, fetch_btc_weekly_data, fetch_btc_data
from identify_bb_squeeze import identify_bb_squeeze_percentile
from align_data_time import get_data_with_indicators_and_time_alignment

def main():
    print("💬 Mr. TradeBotCoach Reminder: Before changing strategy logic, update logbook.txt and consult readchatgpt.txt.")

    # --- Weekly context (in config) ---
    weekly_data = fetch_btc_weekly_data().add_prefix("W_")
    config.weekly_data = weekly_data
    config.weekly_data_HA = compute_heikin_ashi(weekly_data, prefix="W_", weekly=True)
    weekly_data_HA = config.weekly_data_HA

    config.weekly_bb = compute_bollinger_bands(weekly_data, period=20, std_dev=2, prefix="W_")
    config.weekly_bb = identify_bb_squeeze_percentile(config.weekly_bb, bb_width_col="W_BB_Width_20", window=52, pct=0.15)

    config.weekly_HMA = compute_HMA(weekly_data, periods=[14, 25, 50, 100], prefix="W_")

    # --- Daily data + indicators aligned with weekly ---
    data = get_data_with_indicators_and_time_alignment()

    # --- Column init lives here now ---
    BOOL_COLS = [
        'Uptrend', 'Trend_Buy_Zone',
        'W_SenB_Future_flat_to_up_point', 'W_SenB_Trend_Dead',
        'Real_uptrend_start', 'Real_uptrend_end',
        'Searching_micro_trendline', 'Searching_macro_trendline',
        'Start_of_Dead_Trendline',
        'W_SenB_Consol_Start_SenB',
        'W_SenB_Consol_Start_Price',
        'W_SenB_Consol_Start_Price_Adjusted',
    ]
    FLOAT_COLS = [
        'Regline_from_last_adjusted',  # numeric regression line for plotting
    ]

    def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
        for col in BOOL_COLS:
            if col not in df.columns:
                df[col] = False
            else:
                df[col] = df[col].fillna(False).astype(bool)
        for col in FLOAT_COLS:
            if col not in df.columns:
                df[col] = np.nan
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    data = ensure_columns(data)

    # --- Run backtest on prepared data ---
    data, buys, sells, trades, equity, cash = run_backtest(data)
    print(f"{len(buys)} buy signals, {len(sells)} sell signals")

    # --- Plot ---
    plot_price_with_indicators(
        data,
        buy_signals=buys,
        sell_signals=sells,
        trades=trades,
        equity_curve=equity,
        cash_series=cash,
        weekly_data_HA=weekly_data_HA
    )

    # --- Metrics ---
    print_trade_results(trades)
    analyze_performance(trades)
    print_return_distribution(trades)

if __name__ == "__main__":
    main()
