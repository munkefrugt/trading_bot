# trendline_maker/trendline_pipeline.py

import numpy as np

from .treat_extrema import (
    smooth_series,
    find_local_extrema_trend_aware,
    snap_extrema,
    merge_extrema,
)

from .trendline_builder import best_pivot_trendline


def fit_trendlines_hybrid(y_raw, cluster_bar_distance=8):
    x = np.arange(len(y_raw))

    # Smooth
    y_s2, y_s5 = smooth_series(y_raw)

    # σ2 extrema
    lows2_raw, highs2_raw, m2, b2 = find_local_extrema_trend_aware(y_s2)

    # σ5 extrema
    lows5, highs5, m5, b5 = find_local_extrema_trend_aware(y_s5)

    # Snap
    lows_cluster, lows_overridden = snap_extrema(lows2_raw, lows5, cluster_bar_distance)
    highs_cluster, highs_overridden = snap_extrema(
        highs2_raw, highs5, cluster_bar_distance
    )

    # Remaining
    lows_remaining = sorted(set(lows2_raw) - set(lows_overridden))
    highs_remaining = sorted(set(highs2_raw) - set(highs_overridden))

    # Merge
    lows_merged = merge_extrema(lows_cluster, lows_remaining)
    highs_merged = merge_extrema(highs_cluster, highs_remaining)

    # Support
    (
        sup_slope,
        sup_int,
        sup_A,
        sup_B,
        sup_mreg,
        sup_breg,
        sup_candidate_lines,
        sup_valid_lines,
        sup_best_line,
    ) = best_pivot_trendline(x, y_s2, lows_merged, support=True)

    # Resistance
    (
        res_slope,
        res_int,
        res_A,
        res_B,
        res_mreg,
        res_breg,
        res_candidate_lines,
        res_valid_lines,
        res_best_line,
    ) = best_pivot_trendline(x, y_s2, highs_merged, support=False)

    support = (sup_slope, sup_int) if sup_slope is not None else None
    resistance = (res_slope, res_int) if res_slope is not None else None

    return (
        support,
        resistance,
        lows_remaining,
        highs_remaining,
        lows_cluster,
        highs_cluster,
        y_s2,
        y_s5,
        lows_merged,
        highs_merged,
        m2,
        b2,
        m5,
        b5,
        (sup_A, sup_B),
        (res_A, res_B),
        (sup_mreg, sup_breg),
        (res_mreg, res_breg),
        sup_candidate_lines,
        sup_valid_lines,
        sup_best_line,
        res_candidate_lines,
        res_valid_lines,
        res_best_line,
    )
