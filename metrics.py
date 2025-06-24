import numpy as np

def analyze_performance(trades):
    if not trades:
        print("No trades to analyze.")
        return

    closed_trades = [t for t in trades if t.exit_price is not None]
    profits = [t.profit() for t in closed_trades]
    returns = [p / (t.entry_price * t.quantity) for p, t in zip(profits, closed_trades)]

    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]

    win_rate = len(wins) / len(profits) * 100 if profits else 0
    avg_win_usd = np.mean(wins) if wins else 0
    avg_loss_usd = np.mean(losses) if losses else 0

    win_returns = [r for r in returns if r > 0]
    loss_returns = [r for r in returns if r < 0]


    avg_win_pct = np.mean(win_returns) * 100 if win_returns else 0
    avg_loss_pct = np.mean(loss_returns) * 100 if loss_returns else 0


    profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf')
    total_return = sum(profits)

    # Max drawdown
    equity_curve = np.cumsum(profits)
    peak = np.maximum.accumulate(equity_curve)
    drawdown = peak - equity_curve
    max_drawdown = np.max(drawdown)
    max_drawdown_pct = max_drawdown / np.max(peak) * 100

    # Streaks
    streaks = {'win': 0, 'loss': 0, 'max_win': 0, 'max_loss': 0}
    current = 0
    for p in profits:
        if p > 0:
            current = current + 1 if current >= 0 else 1
            streaks['max_win'] = max(streaks['max_win'], current)
        else:
            current = current - 1 if current <= 0 else -1
            streaks['max_loss'] = max(streaks['max_loss'], abs(current))

    print("\n📊 PERFORMANCE METRICS")
    print(f"Win Rate:          {win_rate:.2f}%")
    print(f"Avg Win:           {avg_win_usd:.2f} USD ({avg_win_pct:.2f}%)")
    print(f"Avg Loss:          {avg_loss_usd:.2f} USD ({avg_loss_pct:.2f}%)")
    print(f"Profit Factor:     {profit_factor:.2f}  how much you earn for every dollar you lose")
    print(f"Total Return:      {total_return:.2f}")
    print(f"Max Drawdown USD:  {max_drawdown:.2f}")
    print(f"Max Drawdown %:    {max_drawdown_pct:.2f}%)")
    print(f"Max Win Streak:    {streaks['max_win']}")
    print(f"Max Loss Streak:   {streaks['max_loss']}")

def print_return_distribution(trades, bucket_size=5):
    print("\n📈 TRADE RETURN DISTRIBUTION")
    print("📊 PERFORMANCE METRICS (win/loss per trade! not intire account!):")
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

    for pct in pct_returns:
        bucket_key = f"{int(pct // bucket_size * bucket_size)}% to {int((pct // bucket_size + 1) * bucket_size)}%"
        if bucket_key in buckets:
            buckets[bucket_key].append(pct)

    # Print compact version
    for label, values in buckets.items():
        if not values:
            continue
        unique_values = sorted(set(values))
        if len(unique_values) == 1:
            print(f"{unique_values[0]:>6}%".rjust(16) + f" | {len(values)}")
        else:
            print(f"{label:16} | {len(values)}")
