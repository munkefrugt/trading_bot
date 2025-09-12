# trend/senb_flat.py
import pandas as pd

def check_senb_flat(
    w: pd.DataFrame,
    w_pos: int,
    min_weeks: int = 10,
    flat_threshold: float = 0.04,
    col: str = "W_Senkou_span_B_future",
):
    """Return (flat_ok, flat_range, flat_avg) for W_SenB over the past `min_weeks`."""
    if w_pos - min_weeks < 0:
        return False, None, None
    window = w[col].iloc[w_pos - min_weeks : w_pos]
    flat_avg = window.mean()
    if not pd.notna(flat_avg) or flat_avg == 0:
        return False, None, None
    flat_range = (window.max() - window.min()) / flat_avg
    return (flat_range <= flat_threshold), float(flat_range), float(flat_avg)
