# trendline_maker/treat_extrema.py

import numpy as np
from scipy.ndimage import gaussian_filter1d


def smooth_series(y_raw):
    """Return σ2 and σ5 smoothed versions."""
    return (gaussian_filter1d(y_raw, sigma=2), gaussian_filter1d(y_raw, sigma=5))


def find_local_extrema_trend_aware(y):
    """Find detrended highs/lows."""
    x = np.arange(len(y))

    # detrending
    m, b = np.polyfit(x, y, 1)
    r = y - (m * x + b)

    lows, highs = [], []

    for i in range(1, len(r) - 1):
        if r[i] < r[i - 1] and r[i] < r[i + 1]:
            lows.append(i)
        if r[i] > r[i - 1] and r[i] > r[i + 1]:
            highs.append(i)

    return lows, highs, m, b


def snap_extrema(ext2, ext5, max_distance):
    """Snap small σ2 extrema to nearest σ5 extrema."""
    snapped = []
    overridden = []

    if len(ext5) == 0:
        return ext2[:], overridden

    for i in ext2:
        nearest = min(ext5, key=lambda j: abs(j - i))
        if abs(nearest - i) <= max_distance:
            snapped.append(nearest)
            overridden.append(i)

    return sorted(set(snapped)), sorted(set(overridden))


def merge_extrema(cluster_ext, remaining_ext):
    """Merge snapped + remaining extrema."""
    return sorted(set(cluster_ext) | set(remaining_ext))
