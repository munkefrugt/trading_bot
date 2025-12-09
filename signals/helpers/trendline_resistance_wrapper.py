import numpy as np
from .trendline_maker.trendline_pipeline import fit_trendlines_hybrid


def get_resistance_line(prices: np.ndarray):
    """
    Clean wrapper: returns only the resistance line (slope, intercept)
    from the prototype trendline module.
    """

    (
        support,
        resistance,
        *rest,
        # ignore everything else
    ) = fit_trendlines_hybrid(prices)

    if resistance is None:
        return None, None

    slope, intercept = resistance
    return slope, intercept
