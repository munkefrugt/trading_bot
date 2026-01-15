# plot/plot_sequences.py

import numpy as np
import plotly.graph_objects as go


def plot_signal_sequences(fig, data, signal_sequences, row=1, col=1):
    """
    Plot structural elements from SignalSequence objects.
    This function ONLY adds traces to fig.
    """

    if not signal_sequences:
        return

    for seq in signal_sequences:

        # --------------------------------------------------
        # 1) Frozen trend regression
        # --------------------------------------------------
        if seq.helpers.get("trend_reg_frozen"):

            start_ts = seq.helpers["trend_reg_start_ts"]
            end_ts = seq.helpers["trend_reg_end_ts"]
            m = seq.helpers["trend_reg_m"]
            b = seq.helpers["trend_reg_b"]

            if m is not None and start_ts in data.index and end_ts in data.index:
                segment = data.loc[start_ts:end_ts]
                x = np.arange(len(segment))
                y = m * x + b

                fig.add_trace(
                    go.Scatter(
                        x=segment.index,
                        y=y,
                        mode="lines",
                        line=dict(
                            color="rgba(0, 120, 255, 0.7)",
                            width=2,
                            dash="dot",
                        ),
                        showlegend=False,
                        name=f"Reg {seq.id}",
                    ),
                    row=row,
                    col=col,
                )

        # --------------------------------------------------
        # 2) Pivot resistance
        # --------------------------------------------------
        res_m = seq.helpers.get("pivot_resistance_m")
        res_b = seq.helpers.get("pivot_resistance_b")
        start_ts = seq.helpers.get("pivot_start_ts")
        end_ts = seq.helpers.get("pivot_end_ts")

        if (
            res_m is not None
            and start_ts is not None
            and end_ts is not None
            and start_ts in data.index
            and end_ts in data.index
        ):
            segment = data.loc[start_ts:end_ts]
            x = np.arange(len(segment))
            y = res_m * x + res_b

            fig.add_trace(
                go.Scatter(
                    x=segment.index,
                    y=y,
                    mode="lines",
                    line=dict(color="rgba(255, 80, 80, 0.6)", width=1.5),
                    showlegend=False,
                    name=f"Pivot R {seq.id}",
                ),
                row=row,
                col=col,
            )

        # --------------------------------------------------
        # 3) Pivot support
        # --------------------------------------------------
        sup_m = seq.helpers.get("pivot_support_m")
        sup_b = seq.helpers.get("pivot_support_b")

        if (
            sup_m is not None
            and start_ts is not None
            and end_ts is not None
            and start_ts in data.index
            and end_ts in data.index
        ):
            segment = data.loc[start_ts:end_ts]
            x = np.arange(len(segment))
            y = sup_m * x + sup_b

            fig.add_trace(
                go.Scatter(
                    x=segment.index,
                    y=y,
                    mode="lines",
                    line=dict(color="rgba(80, 200, 120, 0.5)", width=1.2),
                    showlegend=False,
                    name=f"Pivot S {seq.id}",
                ),
                row=row,
                col=col,
            )

        # --------------------------------------------------
        # 4) Pivot DAILY CLOSE cross marker (STAR)
        # --------------------------------------------------
        break_ts = seq.helpers.get("pivot_break_ts")

        if break_ts is not None and break_ts in data.index:
            fig.add_trace(
                go.Scatter(
                    x=[break_ts],
                    y=[data.loc[break_ts, "D_Close"]],
                    mode="markers",
                    marker=dict(
                        symbol="star",
                        size=12,
                        color="purple",
                    ),
                    showlegend=False,
                    name=f"Breakout {seq.id}",
                ),
                row=row,
                col=col,
            )

        # --------------------------------------------------
        #  Paired WEEKLY BB ↔ PIVOT marker
        # --------------------------------------------------
        pair_ts = seq.helpers.get("bb_pivot_pair_ts")

        if pair_ts is not None and pair_ts in data.index:
            fig.add_trace(
                go.Scatter(
                    x=[pair_ts],
                    y=[data.loc[pair_ts, "D_Close"]],
                    mode="markers",
                    marker=dict(
                        symbol="diamond",
                        size=11,
                        color="orange",
                    ),
                    showlegend=False,
                    name=f"BB↔Pivot {seq.id}",
                ),
                row=row,
                col=col,
            )
