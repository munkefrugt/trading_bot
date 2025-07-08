from trade import Trade

def sell_check(open_trades, data, i, cash, sell_markers):
    current_date = data.index[i]
    close = data['Close'].iloc[i]

    for trade in open_trades[:]:
        # Emergency exit
        if close < trade.stoploss:
            print(f"💥 EMERGENCY EXIT on {current_date.date()} | Close={close:.2f} < Stoploss={trade.stoploss:.2f}")
            trade.close(exit_date=current_date, exit_price=close)
            cash += trade.exit_price * trade.quantity
            sell_markers.append((current_date, close))
            open_trades.remove(trade)
            continue

        # Main decision flow
        mode = getattr(trade, 'stoploss_mode', 'relaxed')

        if mode == 'tight':
            if should_exit_on_tight(data, i):
                print(f"⛔ Exit based on tight hold logic on {current_date.date()}")
                trade.close(exit_date=current_date, exit_price=close)
                cash += trade.exit_price * trade.quantity
                sell_markers.append((current_date, close))
                open_trades.remove(trade)

        elif mode == 'relaxed':
            if is_relaxed_conditions(data, i):
                ema_50 = data['EMA_50'].iloc[i]
                trade.stoploss = ema_50
                trade.stoploss_mode = 'relaxed'
                print(f"🕊️ Stay relaxed — EMA 50 stoploss at {ema_50:.2f}")
            elif is_warning_signs(data, i):
                tenkan = data['D_Tenkan_sen'].iloc[i]
                trade.stoploss = tenkan
                trade.stoploss_mode = 'tight'
                print(f"⚠️ Tightening stoploss — switching to Tenkan at {tenkan:.2f}")
            elif should_exit_on_relaxed(data, i):
                print(f"⛔ Exit from relaxed mode on {current_date.date()}")
                trade.close(exit_date=current_date, exit_price=close)
                cash += trade.exit_price * trade.quantity
                sell_markers.append((current_date, close))
                open_trades.remove(trade)

    return open_trades, cash, sell_markers


# One correct definition of should_exit_on_tight
def should_exit_on_tight(data, i):
    try:
        chikou = data['D_Chikou_span'].iloc[i]
        chikou_index = i - 26
        past_cloud_top = data['D_Senkou_span_A'].iloc[chikou_index]
        past_cloud_bottom = data['D_Senkou_span_B'].iloc[chikou_index]
        past_close = data['Close'].iloc[chikou_index]

        price = data['Close'].iloc[i]
        senkou_a = data['D_Senkou_span_A'].iloc[i]
        senkou_b = data['D_Senkou_span_B'].iloc[i]

        weekly_red = data['W_HA_Close'].iloc[i] < data['W_HA_Open'].iloc[i]

        chikou_collides = (
            chikou < past_close or
            chikou < past_cloud_top or
            chikou < past_cloud_bottom
        )

        deep_in_cloud = price < min(senkou_a, senkou_b)

        return weekly_red or chikou_collides or deep_in_cloud
    except:
        return False

def should_exit_on_relaxed(data, i):
    try:
        chikou = data['D_Chikou_span'].iloc[i]
        chikou_index = i - 26
        past_close = data['Close'].iloc[chikou_index]

        daily_red = data['HA_Close'].iloc[i] < data['HA_Open'].iloc[i]
        weak_chikou_dip = chikou < past_close

        return daily_red and weak_chikou_dip
    except:
        return False

def is_relaxed_conditions(data, i):
    try:
        # Minimal placeholder version
        return True
    except:
        return False

def is_warning_signs(data, i):
    try:
        # Minimal placeholder version
        return False
    except:
        return False
