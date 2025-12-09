import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def plot_clean_extrema_with_trendlines(
    x,
    y_raw,
    y_s2,
    y_s5,
    y_s15,
    y_s25,
    y_s50,
    lows_remaining,
    highs_remaining,
    lows_cluster,
    highs_cluster,
    support,
    resistance,
    m2,
    b2,
    m5,
    b5,
    support_pivots=None,
    resistance_pivots=None,
    support_reg=None,
    resistance_reg=None,
):
    """
    Core plot visualizer for hybrid trendline pipeline.
    x can be datetime64 or numeric.
    """

    # =====================================================
    # Utility: turn input into a valid NumPy extrema array
    # =====================================================
    def to_np_extrema(arr):
        if arr is None:
            return np.empty((0, 2))
        if isinstance(arr, list):
            arr = np.array(arr)
        if isinstance(arr, np.ndarray):
            if arr.size == 0:
                return np.empty((0, 2))
            if arr.ndim == 1:
                # Single point [idx, price]
                if len(arr) == 2:
                    return arr.reshape(1, 2)
                return np.empty((0, 2))
            return arr
        try:
            arr = np.array(arr)
            if arr.ndim == 1 and len(arr) == 2:
                return arr.reshape(1, 2)
            return arr
        except:
            return np.empty((0, 2))

    # Convert all extrema sets:
    lows_remaining = to_np_extrema(lows_remaining)
    highs_remaining = to_np_extrema(highs_remaining)
    lows_cluster = to_np_extrema(lows_cluster)
    highs_cluster = to_np_extrema(highs_cluster)
    support_pivots = to_np_extrema(support_pivots)
    resistance_pivots = to_np_extrema(resistance_pivots)

    # Ensure x is an array (Pandas index → NumPy)
    x = np.array(x)

    # =====================================================
    # Utility: safely iterate over trendline lists
    # =====================================================
    def iter_lines(lines):
        """
        Returns a list of (m,b) tuples.
        Handles None, empty lists, weird nested cases.
        """
        if lines is None:
            return []
        out = []
        try:
            for line in lines:
                if line is None:
                    continue
                line = np.array(line)
                if line.size == 2:
                    out.append((float(line[0]), float(line[1])))
        except:
            return []
        return out

    plt.figure(figsize=(14, 7))

    # --- RAW PRICE ---
    plt.plot(x, y_raw, label="Raw price", color="black", linewidth=1.5)

    # --- SMOOTH LAYERS ---
    plt.plot(x, y_s2, label="Smooth 2", linewidth=0.8)
    plt.plot(x, y_s5, label="Smooth 5", linewidth=0.8)
    plt.plot(x, y_s15, label="Smooth 15", linewidth=0.8)
    plt.plot(x, y_s25, label="Smooth 25", linewidth=0.8)
    plt.plot(x, y_s50, label="Smooth 50", linewidth=0.8)

    # --- EXTREMA: remaining ---
    if lows_remaining.shape[0] > 0:
        plt.scatter(
            x[lows_remaining[:, 0].astype(int)],
            lows_remaining[:, 1],
            color="blue",
            s=40,
            label="Lows (remaining)",
        )

    if highs_remaining.shape[0] > 0:
        plt.scatter(
            x[highs_remaining[:, 0].astype(int)],
            highs_remaining[:, 1],
            color="red",
            s=40,
            label="Highs (remaining)",
        )

    # --- EXTREMA: clusters ---
    if lows_cluster.shape[0] > 0:
        plt.scatter(
            x[lows_cluster[:, 0].astype(int)],
            lows_cluster[:, 1],
            color="cyan",
            s=50,
            label="Low cluster",
        )

    if highs_cluster.shape[0] > 0:
        plt.scatter(
            x[highs_cluster[:, 0].astype(int)],
            highs_cluster[:, 1],
            color="magenta",
            s=50,
            label="High cluster",
        )

    # --- SUPPORT & RESISTANCE LINES ---
    for m, b in iter_lines(support):
        plt.plot(x, m * np.arange(len(x)) + b, color="green", linewidth=2)

    for m, b in iter_lines(resistance):
        plt.plot(x, m * np.arange(len(x)) + b, color="orange", linewidth=2)

    # --- REGRESSION LINES ---
    if support_reg is not None:
        m_reg, b_reg = support_reg
        plt.plot(x, m_reg * np.arange(len(x)) + b_reg, "g--", label="Support reg")

    if resistance_reg is not None:
        m_reg, b_reg = resistance_reg
        plt.plot(x, m_reg * np.arange(len(x)) + b_reg, "r--", label="Resistance reg")

    # --- PIVOTS: support & resistance ---
    if support_pivots.shape[0] > 0:
        plt.scatter(
            x[support_pivots[:, 0].astype(int)],
            support_pivots[:, 1],
            color="green",
            s=80,
            marker="X",
            label="Support pivots",
        )

    if resistance_pivots.shape[0] > 0:
        plt.scatter(
            x[resistance_pivots[:, 0].astype(int)],
            resistance_pivots[:, 1],
            color="orange",
            s=80,
            marker="X",
            label="Resistance pivots",
        )

    # --- LABELING ---
    plt.title("Hybrid Trendline Detector (Clean Extrema + Trendlines)")
    plt.legend()
    plt.grid(True)

    # --- DATE AXIS (if x contains datetime64) ---
    try:
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)
    except:
        pass

    plt.tight_layout()
    plt.show()
