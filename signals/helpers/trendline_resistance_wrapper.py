from ..trendline_maker.trendline_pipeline import fit_trendlines_hybrid


def get_resistance_line(prices):
    (_, resistance, *_) = fit_trendlines_hybrid(prices)
    if resistance is None:
        return None
    return resistance  # (slope, intercept)
