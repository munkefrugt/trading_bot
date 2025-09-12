# trend/consolidation_extend.py
import pandas as pd
import numpy as np
from typing import Optional

def _last_true_at_or_before(data: pd.DataFrame, flag_col: str, i: int) -> Optional[int]:
    """Return the position of the last True in flag_col at or before i.
    If none exist ≤ i, return the position of the last True anywhere.
    If no True at all, return None.
    """
    if flag_col not in data.columns:
        return None
    flags = data[flag_col].fillna(False).astype(bool)
    if not flags.any():
        return None
    # slice up to i (inclusive)
    upto = flags.iloc[: i + 1]
    if upto.any():
        return data.index.get_loc(upto[upto].index[-1])
    # else fallback: last True anywhere
    return data.index.get_loc(flags[flags].index[-1])

def _pos_from_date(idx: pd.DatetimeIndex, dt: pd.Timestamp, side: str = "left") -> int:
    return int(np.searchsorted(idx.values, dt.to_datetime64(), side=side))

def extend_consolidation_start_by_height(
    data: pd.DataFrame,
    current_index: int,
    source_flag_col: str = "W_SenB_Consol_Start_Price_Adjusted",       # READ here
    target_flag_col: str = "W_SenB_Consol_start_Adj_jump_6_months",    # WRITE here
    y_col: str = "D_Close",
    months_back: int = 6,
    height_tol_pct: float = 0.03,   # 3% tolerance
    min_gap_days: int = 21,         # don't select too close to seed
    forward_scan_days: int = 120,   # cap scan length after the jump
) -> pd.DataFrame:
    """Jump ~`months_back` before the seed start (from `source_flag_col`),
    then scan FORWARD for the FIRST similar-height point (±`height_tol_pct`).
    If none is found, FALL BACK to the seed. Ensures exactly one True in `target_flag_col`.
    """
    if not (0 <= current_index < len(data)):
        return data
    if y_col not in data.columns or source_flag_col not in data.columns:
        return data

    idx = data.index
    if not isinstance(idx, pd.DatetimeIndex):
        # need dates to jump months
        return data

    # ensure target column exists and is boolean
    if target_flag_col not in data.columns:
        data[target_flag_col] = False
    else:
        data[target_flag_col] = data[target_flag_col].fillna(False).astype(bool)

    # 1) pick seed (last True at/before current_index; fallback to last True anywhere)
    seed_pos = _last_true_at_or_before(data, source_flag_col, current_index)
    if seed_pos is None:
        return data
    seed_idx = idx[seed_pos]

    # 2) reference height (y at seed)
    y_ref = pd.to_numeric(data[y_col].iloc[seed_pos], errors="coerce")
    if not np.isfinite(y_ref) or y_ref <= 0:
        # fallback to seed
        data[target_flag_col] = False
        data.at[seed_idx, target_flag_col] = True
        data.at[seed_idx, f"{target_flag_col}_FallbackSeed"] = True
        return data

    # 3) compute jump-back and forward-scan bounds
    seed_date = seed_idx
    jump_date = seed_date - pd.DateOffset(months=months_back)
    jump_pos = _pos_from_date(idx, jump_date, side="left")
    jump_pos = max(0, min(jump_pos, seed_pos))

    # end of scan cannot enter the last `min_gap_days` before seed,
    # and also must not exceed `forward_scan_days` after the jump date.
    scan_end_date_by_window = seed_date - pd.Timedelta(days=min_gap_days)
    scan_end_date_by_limit  = jump_date + pd.Timedelta(days=forward_scan_days)
    scan_end_date = min(scan_end_date_by_window, scan_end_date_by_limit)
    scan_end_pos = _pos_from_date(idx, scan_end_date, side="right") - 1
    scan_end_pos = max(0, min(scan_end_pos, seed_pos - 1))

    # 4) scan forward from jump_pos → scan_end_pos (inclusive) for first within tolerance
    candidate_found = False
    best_idx = seed_idx  # default fallback

    if jump_pos <= scan_end_pos:
        y_segment = pd.to_numeric(
            data[y_col].iloc[jump_pos:scan_end_pos + 1],
            errors="coerce"
        ).values
        rel_diff = np.abs(y_segment - y_ref) / y_ref
        ok_mask = np.isfinite(y_segment) & (rel_diff <= height_tol_pct)
        if ok_mask.any():
            first_ok_rel = int(np.argmax(ok_mask))  # earliest in time (oldest bar) that matches
            best_pos = jump_pos + first_ok_rel
            best_idx = idx[best_pos]
            candidate_found = True

    # 5) write exactly one True into TARGET
    data[target_flag_col] = False
    if candidate_found:
        data.at[best_idx, target_flag_col] = True
        data.at[best_idx, f"{target_flag_col}_MovedHalfYearForwardScan"] = True
        try:
            print(f"[ConsolExtend] seed={seed_date.date()} -> new={best_idx.date()} "
                  f"Δdays={(seed_date - best_idx).days}, tol={height_tol_pct*100:.1f}%")
        except Exception:
            pass
    else:
        data.at[seed_idx, target_flag_col] = True
        data.at[seed_idx, f"{target_flag_col}_FallbackSeed"] = True
        try:
            print(f"[ConsolExtend] no candidate; keep seed at {seed_date.date()} (tol {height_tol_pct*100:.1f}%)")
        except Exception:
            pass

    return data
