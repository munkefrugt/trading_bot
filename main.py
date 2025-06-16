from get_data import fetch_btc_data
from analyse import compute_heikin_ashi, compute_ema, compute_ichimoku
from plot import plot_heikin_ashi_with_indicators

def main():
    # Fetch BTC-USD daily data
    btc_data = fetch_btc_data()

    # Compute Heikin-Ashi candles
    ha_data = compute_heikin_ashi(btc_data)

    # Compute 200 EMA from original close prices
    ema200 = compute_ema(btc_data, period=200)
    ema50 = compute_ema(btc_data, period=50)
    # Compute Ichimoku indicators from original data
    ichimoku = compute_ichimoku(btc_data)

    # Plot everything
    plot_heikin_ashi_with_indicators(ha_data, [ema50, ema200], ichimoku)
    
if __name__ == "__main__":
    main()
