# trendline_maker/trendline_builder.py

import numpy as np


def best_pivot_trendline(x, y, extrema, support=True):
    """
    Multi-A / Multi-B trendline selector:
      - S/R rule
      - vertical proximity rule
      - minimum pivot distance (10%)
      - span bonus
      - touch bonus
      - RETURNS DEBUG CANDIDATES FOR PLOTTING
    """

    extrema = np.array(extrema, dtype=int)
    if len(extrema) < 2:
        return (None, None, None, None, None, None, [], [], None)

    # ------------------------------------------------------------
    # Regression line (baseline slope)
    # ------------------------------------------------------------
    m_reg, b_reg = np.polyfit(x, y, 1)
    reg_line = m_reg * x + b_reg

    L = len(x)
    min_dx = int(L * 0.10)
    y_std = np.std(y)
    touch_threshold = y_std * 0.10

    candidate_lines = []  # list of (slope, intercept)
    valid_lines = []  # list of (slope, intercept)
    debug_total_candidates = 0
    debug_valid_lines = 0

    best_score = np.inf
    best_params = (None, None, None, None)
    best_line = None

    # ------------------------------------------------------------
    # Try every pivot as A
    # ------------------------------------------------------------
    for pivot_A in extrema:
        far_mask = np.abs(extrema - pivot_A) >= min_dx
        B_list = extrema[far_mask]
        if len(B_list) == 0:
            continue

        # --------------------------------------------------------
        # Test each pivot B
        # --------------------------------------------------------
        for pivot_B in B_list:
            debug_total_candidates += 1

            i, j = pivot_A, pivot_B
            slope = (y[j] - y[i]) / (j - i)
            intercept = y[i] - slope * i
            line = slope * x + intercept

            # Track as a candidate
            candidate_lines.append((slope, intercept))

            # ----------------------------
            # S/R RULE
            # ----------------------------
            if support:
                if np.any(line[extrema] > y[extrema]):
                    continue
            else:
                if np.any(line[extrema] < y[extrema]):
                    continue

            # ----------------------------
            # Vertical proximity rule
            # ----------------------------
            if support:
                vertical_gap = np.min(y[extrema] - line[extrema])
            else:
                vertical_gap = np.min(line[extrema] - y[extrema])

            if vertical_gap > y_std * 0.4:
                continue

            debug_valid_lines += 1
            valid_lines.append((slope, intercept))

            # ----------------------------
            # Touch bonus
            # ----------------------------
            dist = np.abs(y[extrema] - line[extrema])
            touches = np.sum(dist < touch_threshold)
            touch_bonus = touches * 0.5

            # ----------------------------
            # Score
            # ----------------------------
            slope_error = abs(slope - m_reg)
            vertical_penalty = vertical_gap * 0.5
            span = abs(pivot_B - pivot_A)

            score = slope_error + vertical_penalty - span * 0.001 - touch_bonus

            if score < best_score:
                best_score = score
                best_params = (slope, intercept, pivot_A, pivot_B)
                best_line = (slope, intercept)

    # ------------------------------------------------------------
    # Debug print
    # ------------------------------------------------------------
    print("---- Multi-A Multi-B Trendline ----")
    print(f"Regression slope: {m_reg}")
    print(f"Candidates tested: {debug_total_candidates}")
    print(f"Valid S/R lines: {debug_valid_lines}")
    if best_line:
        print(
            f"Best A: {best_params[2]}, Best B: {best_params[3]}, Best slope: {best_params[0]}"
        )
    else:
        print("NO VALID TRENDLINE FOUND")
    print("------------------------------------")

    slope, intercept, A, B = best_params

    return (
        slope,
        intercept,
        A,
        B,
        m_reg,
        b_reg,
        candidate_lines,
        valid_lines,
        best_line,
    )
