import numpy as np

def get_trend_line(
    data,
    current_index,
    column_name='Trendline_from_X',
    use_r2_check=False,
    r2_threshold=0.70,
    use_max_length_check=False,
    max_length=6*30,
    use_min_length_check=False,
    min_length=5*30,
    use_slope_drift_check=False,
    slope_drift_threshold=0.1
):
    """
    Fit a linear trendline from the latest Start_of_Dead_Trendline (red X) up to `current_index`.

    Parameters:
        data: DataFrame with 'D_Close' and 'Start_of_Dead_Trendline'
        current_index: Index (int) at which to end the regression
        column_name: Name of the column to store the fitted trendline
        use_r2_check: Enable/disable R² trend end detection
        r2_threshold: Minimum R² to trigger trend end
        use_max_length_check: Limit max bars used for trendline
        max_length: Max number of bars for a trendline
        use_slope_drift_check: Enable/disable slope drift detection
        slope_drift_threshold: Max allowed slope drift from initial value

    Returns:
        data: With updated trendline and flags
        trendline_end: Boolean indicating if trendline has ended
    """

    # Initialize columns
    if column_name not in data.columns:
        data[column_name] = np.nan
    if 'Initial_trend_slope' not in data.columns:
        data['Initial_trend_slope'] = np.nan

    # Find latest red X
    red_x_mask = data['Start_of_Dead_Trendline'] == True
    red_x_indices = data.index[red_x_mask & (data.index <= data.index[current_index])]

    if red_x_indices.empty:
        print(f"⚠️ No red X before {data.index[current_index].date()}")
        return data, False

    start_idx = red_x_indices[-1]
    start_i = data.index.get_loc(start_idx)
    length = current_index - start_i



    if current_index - start_i < 5:
        print(f"⚠️ Not enough data between X and current point ({data.index[start_i].date()} → {data.index[current_index].date()})")
        return data, False

    if use_max_length_check and current_index - start_i > max_length:
        print(f"🛑 Trendline search too long — max {max_length} bars from {data.index[start_i].date()}")
        return data, True

    # Get data and fit trendline
    y = data['D_Close'].iloc[start_i:current_index + 1].values
    x = np.arange(len(y))
    weights = np.linspace(2, 1, len(x))  # more weight on early points

    slope, intercept = np.polyfit(x, y, deg=1, w=weights)
    y_fit = slope * x + intercept

    data.loc[data.index[start_i:current_index + 1], column_name] = y_fit

    # Slope drift check
    if use_slope_drift_check:
        if np.isnan(data.at[start_idx, 'Initial_trend_slope']):
            data.at[start_idx, 'Initial_trend_slope'] = slope
            initial_slope = slope
        else:
            initial_slope = data.at[start_idx, 'Initial_trend_slope']

        slope_drift = abs(slope - initial_slope)
        if slope_drift > slope_drift_threshold:
            print(f"🛑 Slope drifted from {initial_slope:.4f} → {slope:.4f} at {data.index[current_index].date()}")
            return data, True

    # R² check
    trendline_end = False
    if use_r2_check:
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        if r_squared >= r2_threshold:
            trendline_end = True
            data.at[data.index[current_index], 'Trendline_End'] = True
            print(f"✅ Trendline ends at {data.index[current_index].date()} — R² = {r_squared:.3f}")
        else:
            print(f"⏳ Trendline still forming at {data.index[current_index].date()} — R² = {r_squared:.3f}")

    print(f"📉 Trendline (polyfit) from {data.index[start_i].date()} to {data.index[current_index].date()}")

    if use_min_length_check and  length < min_length :
        print(" find a longer trendline")
        return data, False

    if use_min_length_check and  length > max_length:
        print(f"🛑 Trendline search too long — max {max_length} bars from {data.index[start_i].date()}")
        return data, True
    
    return data, trendline_end

def find_trend_start_point(data, current_index, window_days=84):

    if current_index - window_days < 0:
        print("⚠️ Not enough data to look back for macro trend start.")
        return data

    price_window = data['D_Close'].iloc[current_index - window_days : current_index].dropna()

    if price_window.empty:
        print("⚠️ No valid prices in lookback window.")
        return data

    max_idx = price_window.index[np.argmax(price_window.values)]
    data.at[max_idx, 'Start_of_Dead_Trendline'] = True

    print(f"🟢 Start of dead trendline found at {max_idx.date()} (before {data.index[current_index].date()})")

    return data
