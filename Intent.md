README_INTENT.md
1. Core idea / hypothesis

The main idea is that after Weekly Senkou Span B (SenB) has been flat for a prolonged period (months), the market often enters a regime where trendlines become meaningful and can be trusted.

Once SenB has been flat long enough, it makes sense to actively look for trend structure rather than treating price as mostly noisy.

This strategy is designed to capture rare but large regime shifts, not frequent trades.

2. Trendline validity criteria (entry context)

A trendline is considered valid only if several independent conditions agree:

The trendline roughly aligns with a regression line

A Gaussian-smoothed price series (window ≈ 10) crosses the regression line 4 or more times

Fewer crossings → likely noise

More crossings → structure is respected

There must be clear pivots distributed along the trendline

Not just 1–2 touches

Pivots should be spread out in time

Price must not be “flying” over the data

Especially just before a breakout

No sharp vertical moves that invalidate the idea of a respected structure

Only when these conditions are met is the trendline considered proper.

3. Multiple sequence starts (trendline search robustness)

Trendline detection is not based on a single start point.

Instead, multiple sequences are run in parallel, each starting at a slightly different time around a consolidation start point.

A consolidation start point is identified first

From this region, several sequences are initialized, each with a different start index

Each sequence independently:

Searches for pivots

Fits regression-aligned trendlines

Evaluates Gaussian crossings and structure quality

Purpose:

Avoid overfitting to one arbitrary start time

Capture a variety of valid trendline geometries

Increase robustness of breakout detection

Trendlines that appear consistently across multiple sequences are considered stronger candidates.

This improves breakout quality by ensuring the structure is stable under small shifts in initialization.

4. Breakout and entry logic

Entry occurs on a breakout of a validated trendline

Stop loss is placed near the trendline (support / resistance)

Position size is calculated so that:

Maximum loss per trade = 2% of total equity

This ensures:

Fixed risk

No emotional position sizing

Survivability across many trades

5. Exit logic (profit taking)
Primary exit

Watch for the formation of a proper counter trendline (support → sell line)

This sell/support line must also be validated:

Regression alignment

Multiple Gaussian crossings

Exit when this sell/support line breaks

Alternative / additional scaling-out logic

Sell ½ of the position after +20%

Sell ¼ after +50%

Sell remaining ¼ after +100%

This:

Locks in profits

Reduces psychological pressure

Allows participation in very large moves

6. Strategy scope (important)

This is a rare-event strategy.

Markets may be flat for long periods

Valid breakouts may occur only a few times per decade per asset

Version 2 should scan many stocks and cryptocurrencies simultaneously to find these rare setups

The goal is to catch large directional moves, not to trade often.

7. Explicit non-goals / open questions

Exact definition of “flat SenB” may change

Gaussian window length (≈10) is experimental

Regression and crossing thresholds may need tuning

Scaling-out vs. single-exit logic is not fully decided

These are open design choices, not bugs.

8. What “done” means for v1

Version 1 is considered done when:

Trendline detection works on historical data

Risk management is correct and enforced

Entry and exit logic can be backtested end-to-end

Results are interpretable, even if not perfect

Perfection is not the goal — clarity is.

Final note (why this file exists)

This document captures intent, assumptions, and design philosophy so that:

Future me can resume without rebuilding the mental model

AI can help extend or refactor the system without guessing intent

The project can be paused safely without being lost