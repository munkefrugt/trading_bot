# 📋 TODO: Trading Bot Strategy Improvements

## 🧠 Strategy Logic Improvements

- [ ] Refine **Buy Signal**:
  - Add condition: `chikou > close_26_back`
  - Ensure **Chikou Span** is clearly above:
    - All candlesticks in the past 26 periods
    - The cloud (Senkou A & B)
  - !!!Ensure "clear sight" from Chikou to current price (no cloud or candle interference)

- [ ] Refine **Sell Signal**:
  - Add **cloud reversal** detection
  - Add **Chikou Span** falling below close_26_back or into cloud
  - Optional: Add condition for future cloud turning negative

- [ ] Improve **Stop Loss**:
  - Use **Senkou B** as stop loss
  - Optionally implement **trailing stop loss**

## 📊 Performance Metrics

- [ ] Calculate and display:
  - [ ] **sharpe ratio?** or some other similiar metric that can beused with relatively few trades and outliers like one big winner.


## ✅ General Enhancements

- [ ] Log results more clearly
- [ ] Make plots optionally show:
  - Chikou vs past candles
  - Buy/sell reasons
  - Equity curve with drawdowns



📅 Remember to update `logbook.txt` with results and document any major changes in `readmechatgpt.txt`.

💬 *Mr. TradeBotCoach Reminder: One improvement at a time, then test!*


get nest trades to work, and try with more pairs.

I have to have something like if im too far from the original breakout i gotta wait for the next one. 
I should also integrate the weekly cloud. 
I should also make a trendchannel from around where i start the trade. and let id form and then jump out when the channel is broken. 
In that way i can cut out of trades with less losses and a lot faster. 
maybe also a minimum take home like if it rises 10% and drops to 5% then sell before it comes out. or something like that. 
consider pyramidding. 
or pyramiding sell.? if thats a thing. like sell of 50% shen i gain 15% and then let the rest run. so i will come out more than even. 
there is something about the way i set initial stoploss that affects position size. might not be optimal

trade differnt coins at the same time
try BB it should coorporate

make sure i dont try to break out of a channel top like bitcoin usd jul 16 2015. 
make channels. and buy at the bottom. 