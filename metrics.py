import numpy as np

def analyze_performance(trades):
    if not trades:
        print("No trades to analyze.")
        return

    closed_trades = [t for t in trades if t.exit_price is not None]
    wins = [t for t in closed_trades if t.profit() > 0]
    losses = [t for t in closed_trades if t.profit() <= 0]
    profits = [t.profit() for t in closed_trades]

    win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
    avg_win_usd = np.mean([t.profit() for t in wins]) if wins else 0
    avg_loss_usd = np.mean([t.profit() for t in losses]) if losses else 0

    avg_win_pct = np.mean([t.profit_pct() for t in wins]) if wins else 0
    avg_loss_pct = np.mean([t.profit_pct() for t in losses]) if losses else 0

    equity_win_impacts = [get_equity_pct_change(t) for t in wins]
    equity_loss_impacts = [get_equity_pct_change(t) for t in losses]

    avg_equity_win = np.mean(equity_win_impacts) if equity_win_impacts else 0
    avg_equity_loss = np.mean(equity_loss_impacts) if equity_loss_impacts else 0

    profit_factor = sum([t.profit() for t in wins]) / abs(sum([t.profit() for t in losses])) if losses else float('inf')
    total_return = sum(profits)

    total_days_held = sum([(t.exit_date - t.entry_date).days or 1 for t in closed_trades])
    avg_daily_return = total_return / total_days_held if total_days_held > 0 else 0

    equity_curve = np.cumsum(profits)
    peak = np.maximum.accumulate(equity_curve)
    drawdown = peak - equity_curve
    max_drawdown = np.max(drawdown)
    max_drawdown_pct = max_drawdown / np.max(peak) * 100 if np.max(peak) > 0 else 0

    # Streaks
    streaks = {'win': 0, 'loss': 0, 'max_win': 0, 'max_loss': 0}
    current = 0
    for t in closed_trades:
        p = t.profit()
        if p > 0:
            current = current + 1 if current >= 0 else 1
            streaks['max_win'] = max(streaks['max_win'], current)
        else:
            current = current - 1 if current <= 0 else -1
            streaks['max_loss'] = max(streaks['max_loss'], abs(current))

    print("\n📊 PERFORMANCE METRICS")
    print(f"Win Rate:              {win_rate:.2f}%")
    print(f"Avg Win:               {avg_win_usd:.2f} USD ({avg_win_pct:.2f}% of entry)")
    print(f"Avg Loss:              {avg_loss_usd:.2f} USD ({avg_loss_pct:.2f}% of entry)")
    print(f"Avg Equity Win Impact: {avg_equity_win:.2f}%")
    print(f"Avg Equity Loss Impact:{avg_equity_loss:.2f}%")
    print(f"Profit Factor:         {profit_factor:.2f}  how much you earn for every dollar you lose")
    print(f"Total Return:          {total_return:.2f}")
    print(f"Max Drawdown USD:      {max_drawdown:.2f}")
    print(f"Max Drawdown %:        {max_drawdown_pct:.2f}%")
    print(f"Max Win Streak:        {streaks['max_win']}")
    print(f"Max Loss Streak:       {streaks['max_loss']}")
    print(f"Avg Daily Return:       {avg_daily_return:.2f} USD/day")


def print_return_distribution(trades, bucket_size=5):
    print("\n📈 TRADE RETURN DISTRIBUTION")
    print("📊 PERFORMANCE METRICS (win/loss per trade! not entire account!):")
    closed_trades = [t for t in trades if t.exit_price is not None]
    pct_returns = [round(t.profit_pct(), 2) for t in closed_trades]

    if not pct_returns:
        print("No closed trades to analyze.")
        return

    min_pct = int(min(pct_returns) // bucket_size * bucket_size)
    max_pct = int(max(pct_returns) // bucket_size * bucket_size + bucket_size)

    buckets = {}
    for i in range(min_pct, max_pct, bucket_size):
        label = f"{i}% to {i+bucket_size}%"
        buckets[label] = []

    for t in closed_trades:
        pct = round(t.profit_pct(), 2)
        duration = (t.exit_date - t.entry_date).days or 1
        bucket_key = f"{int(pct // bucket_size * bucket_size)}% to {int((pct // bucket_size + 1) * bucket_size)}%"
        if bucket_key in buckets:
            buckets[bucket_key].append(duration)

    for label, durations in buckets.items():
        if not durations:
            continue
        if len(durations) == 1:
            print(f"{label:24} | 1 | {durations[0]} days")
        else:
            avg_duration = sum(durations) / len(durations)
            print(f"{label:24} | {len(durations)} | Avg duration: {avg_duration:.1f} days")

    big_winners = [((t.exit_date - t.entry_date).days or 1) for t in closed_trades if t.profit_pct() > 10]
    losers = [((t.exit_date - t.entry_date).days or 1) for t in closed_trades if t.profit_pct() <= 0]

    if big_winners:
        avg_big_winner_duration = sum(big_winners) / len(big_winners)
        print(f"\n⏱️ Avg Duration of Winners >10%: {avg_big_winner_duration:.2f} days")

    if losers:
        avg_loser_duration = sum(losers) / len(losers)
        print(f"⏱️ Avg Duration of Losing Trades: {avg_loser_duration:.2f} days")


def get_equity_pct_change(trade):
    if trade.exit_price is not None and trade.entry_equity:
        return (trade.profit() / trade.entry_equity) * 100
    return 0

def print_trade_results(trades):
    print("\nTRADE RESULTS:")
    for t in trades:
        if not t.is_open():
            equity_impact = get_equity_pct_change(t)
            duration = (t.exit_date - t.entry_date).days or 1
            print(f"Trade from {t.entry_date.date()} to {t.exit_date.date()} "
                  f"({duration} days): {t.profit():.2f} USD "
                  f"({t.profit_pct():.2f}%) | Equity Impact: {equity_impact:.2f}%")
