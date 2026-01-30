# plot/plot_sequences.py

import numpy as np
import plotly.graph_objects as go


def plot_signal_sequences(fig, data, signal_sequences, row=1, col=1):
    """
    Plot structural elements from SignalSequence objects.
    This function ONLY adds traces to fig.

    Legend behavior:
    - One legend entry per structural TYPE (umbrella legend)
    - Clicking a legend item toggles ALL traces of that type
    """

    if not signal_sequences:
        return

    # --------------------------------------------------
    # legend helper (show legend once per group)
    # --------------------------------------------------
    if not hasattr(fig, "_legend_flags"):
        fig._legend_flags = set()

    def show_legend_once(key):
        if key in fig._legend_flags:
            return False
        fig._legend_flags.add(key)
        return True

    for seq in signal_sequences:
        # --------------------------------------------------
        # 0) SignalSequence START marker
        # --------------------------------------------------
        if seq.start_index is not None:
            ts = data.index[seq.start_index]

            key = "signal_seq_start"
            fig.add_trace(
                go.Scatter(
                    x=[ts],
                    y=[data.loc[ts, "D_Close"]],
                    mode="markers",
                    marker=dict(
                        symbol="triangle-up",
                        size=8,
                        color="rgba(0, 180, 255, 0.9)",
                    ),
                    name="Sequence start",
                    legendgroup=key,
                    showlegend=show_legend_once(key),
                ),
                row=row,
                col=col,
            )

        # --------------------------------------------------
        # 1) Frozen trend regression + diagnostics
        # --------------------------------------------------
        if seq.helpers.get("trend_reg_frozen"):

            start_ts = seq.helpers.get("trend_reg_start_ts")
            end_ts = seq.helpers.get("trend_reg_end_ts")
            m = seq.helpers.get("trend_reg_m")
            b = seq.helpers.get("trend_reg_b")

            if (
                m is not None
                and start_ts is not None
                and end_ts is not None
                and start_ts in data.index
                and end_ts in data.index
            ):
                segment = data.loc[start_ts:end_ts]

                reg_y = seq.helpers.get("trend_reg_y")
                if reg_y is None:
                    x = np.arange(len(segment))
                    reg_y = m * x + b

                # --- regression line ---
                key = "trend_regression"
                fig.add_trace(
                    go.Scatter(
                        x=segment.index,
                        y=reg_y,
                        mode="lines",
                        line=dict(
                            color="rgba(0, 120, 255, 0.7)",
                            width=2,
                            dash="dot",
                        ),
                        name="Trend regression",
                        legendgroup=key,
                        showlegend=show_legend_once(key),
                    ),
                    row=row,
                    col=col,
                )

                # --- regline ↔ smooth crossings ---
                cross_ts = seq.helpers.get("range_tension_regline_cross_ts", [])
                smooth_col = "smooth_s10"

                if cross_ts:
                    cross_ts = [ts for ts in cross_ts if ts in segment.index]
                    cross_y = (
                        segment.loc[cross_ts, smooth_col]
                        if smooth_col in segment.columns
                        else segment.loc[cross_ts, "D_Close"]
                    )

                    key = "reg_smooth_cross"
                    fig.add_trace(
                        go.Scatter(
                            x=cross_ts,
                            y=cross_y,
                            mode="markers",
                            marker=dict(symbol="x", size=8, color="black"),
                            name="Reg ↔ Smooth cross",
                            legendgroup=key,
                            showlegend=show_legend_once(key),
                        ),
                        row=row,
                        col=col,
                    )

                # --- EMA ↔ smooth crossings ---
                ema_cross_ts = seq.helpers.get("range_tension_ema_cross_ts", [])
                ema_col = "EMA_50"

                if ema_cross_ts:
                    ema_cross_ts = [ts for ts in ema_cross_ts if ts in segment.index]
                    ema_cross_y = (
                        segment.loc[ema_cross_ts, smooth_col]
                        if smooth_col in segment.columns
                        else segment.loc[ema_cross_ts, "D_Close"]
                    )

                    key = "ema_smooth_cross"
                    fig.add_trace(
                        go.Scatter(
                            x=ema_cross_ts,
                            y=ema_cross_y,
                            mode="markers",
                            marker=dict(
                                symbol="circle",
                                size=7,
                                color="rgba(200, 50, 50, 0.9)",
                            ),
                            name="EMA ↔ Smooth cross",
                            legendgroup=key,
                            showlegend=show_legend_once(key),
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

            key = "pivot_resistance"
            fig.add_trace(
                go.Scatter(
                    x=segment.index,
                    y=y,
                    mode="lines",
                    line=dict(color="rgba(255, 80, 80, 0.6)", width=1.5),
                    name="Pivot resistance",
                    legendgroup=key,
                    showlegend=show_legend_once(key),
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

            key = "pivot_support"
            fig.add_trace(
                go.Scatter(
                    x=segment.index,
                    y=y,
                    mode="lines",
                    line=dict(color="rgba(80, 200, 120, 0.5)", width=1.2),
                    name="Pivot support",
                    legendgroup=key,
                    showlegend=show_legend_once(key),
                ),
                row=row,
                col=col,
            )

        # --------------------------------------------------
        # 4) Pivot DAILY CLOSE break marker
        # --------------------------------------------------
        break_ts = seq.helpers.get("pivot_break_ts")

        if break_ts is not None and break_ts in data.index:
            key = "pivot_breakout"
            fig.add_trace(
                go.Scatter(
                    x=[break_ts],
                    y=[data.loc[break_ts, "D_Close"]],
                    mode="markers",
                    marker=dict(symbol="star", size=12, color="purple"),
                    name="Pivot breakout",
                    legendgroup=key,
                    showlegend=show_legend_once(key),
                ),
                row=row,
                col=col,
            )

        # --------------------------------------------------
        # 5) Paired WEEKLY BB ↔ PIVOT marker
        # --------------------------------------------------
        pair_ts = seq.helpers.get("bb_pivot_pair_ts")

        if pair_ts is not None and pair_ts in data.index:
            key = "bb_pivot_pair"
            fig.add_trace(
                go.Scatter(
                    x=[pair_ts],
                    y=[data.loc[pair_ts, "D_Close"]],
                    mode="markers",
                    marker=dict(symbol="diamond", size=11, color="orange"),
                    name="BB ↔ Pivot pair",
                    legendgroup=key,
                    showlegend=show_legend_once(key),
                ),
                row=row,
                col=col,
            )
