
from analyse import compute_ema, extend_index
from analyse import compute_heikin_ashi, compute_ichimoku
from get_data import extend_weekly_index, fetch_btc_weekly_data,fetch_btc_data
import pandas as pd

def get_data_with_indicators_and_time_alignment():
    data = fetch_btc_data()


    weekly = fetch_btc_weekly_data()

    ha_weekly = compute_heikin_ashi(weekly).add_prefix('W_HA_')
    ha_weekly_daily = ha_weekly.reindex(data.index, method='ffill')

 
    
    data = pd.concat([data, ha_weekly_daily], axis=1)

    data['EMA_20'] = compute_ema(data, 20)
    data['EMA_50'] = compute_ema(data, 50)
    data['EMA_200'] = compute_ema(data, 200)

    data = extend_index(data)

    ichimoku_daily = compute_ichimoku(data).add_prefix('D_')

    data = pd.concat([data, ichimoku_daily], axis=1)

    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.width', None)
    # pd.set_option('display.max_rows', 100)

    #print(data.tail(30))

    return data
