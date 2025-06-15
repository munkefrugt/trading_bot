import pandas as pd

def compute_heikin_ashi(data):
    """
    Takes OHLCV dataframe and returns Heikin-Ashi OHLC dataframe.
    """
    ha = pd.DataFrame(index=data.index)
    
    ha['Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4

    ha['Open'] = 0.0  # placeholder, filled below
    ha['High'] = 0.0
    ha['Low'] = 0.0

    for i in range(len(data)):
        if i == 0:
            ha.iat[0, ha.columns.get_loc('Open')] = (data['Open'].iloc[0] + data['Close'].iloc[0]) / 2
        else:
            ha.iat[i, ha.columns.get_loc('Open')] = (ha['Open'].iloc[i-1] + ha['Close'].iloc[i-1]) / 2

        ha.iat[i, ha.columns.get_loc('High')] = max(data['High'].iloc[i], ha['Open'].iloc[i], ha['Close'].iloc[i])
        ha.iat[i, ha.columns.get_loc('Low')] = min(data['Low'].iloc[i], ha['Open'].iloc[i], ha['Close'].iloc[i])

    return ha
