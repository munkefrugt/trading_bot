# 📋 TODO: Trading Bot Strategy Improvements

## 🧠 Strategy Logic Improvements

- [ ] Refine **Buy Signal**:
  - Add condition: `chikou > close_26_back`
  - Ensure **Chikou Span** is clearly above:
    - All candlesticks in the past 26 periods
    - The cloud (Senkou A & B)
  - Ensure "clear sight" from Chikou to current price (no cloud or candle interference)

- [ ] Refine **Sell Signal**:
  - Add **cloud reversal** detection
  - Add **Chikou Span** falling below close_26_back or into cloud
  - Optional: Add condition for future cloud turning negative

- [ ] Improve **Stop Loss**:
  - Use **Senkou B** as stop loss
  - Optionally implement **trailing stop loss**

## 📊 Performance Metrics

- [ ] Calculate and display:
  - [ ] **Win rate**
  - [ ] **Risk/reward ratio**
  - [ ] **Maximum drawdown**
  - [ ] **Streaks** of wins/losses

## ✅ General Enhancements

- [ ] Log results more clearly
- [ ] Make plots optionally show:
  - Chikou vs past candles
  - Buy/sell reasons
  - Equity curve with drawdowns



📅 Remember to update `logbook.txt` with results and document any major changes in `readmechatgpt.txt`.

💬 *Mr. TradeBotCoach Reminder: One improvement at a time, then test!*
