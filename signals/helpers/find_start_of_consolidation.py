# helpers/signals/find_start_of_consolidation.py
import pandas as pd

SLOPE_COL = "W_Senkou_span_B_slope_pct"
SLOPE_ABS_THRESHOLD = 2.0  # %

def find_start_of_consolidation(data: pd.DataFrame, i: int):
    """
    Walk backward from i until |W_Senkou_span_B_slope_pct| > threshold.
    Mark that bar as consolidation start and set an anchor ≈ 26 calendar weeks earlier
    (snap to nearest available bar at/before that time).

    If no SenB slope point is found (ran out of data),
    use the highest D_Close_smooth within the past year
    as a fallback consolidation start, but only if it's
    at least 3 months older than the rise point.
    """

    if i <= 0 or i >= len(data) or SLOPE_COL not in data.columns:
        print(f"⚠️ Skipped find_start_of_consolidation: invalid i={i} or missing slope column.")
        return

    j = i
    found_senb_point = False
    candidate_idx = None
    candidate_val = -float("inf")

    print(f"\n🔎 Starting consolidation search at {data.index[i].date()}")

    while j > 0:
        slope = data.at[data.index[j], SLOPE_COL]

        # Track best smoothed close candidate (for fallback)
        if "D_Close_smooth" in data.columns:
            close_smooth = data.at[data.index[j], "D_Close_smooth"]
            weeks_back = (data.index[i] - data.index[j]).days / 7
            if weeks_back >= 12 and pd.notna(close_smooth) and close_smooth > candidate_val:
                candidate_val = close_smooth
                candidate_idx = data.index[j]

        # Debug trace every ~10 steps or at start/end
        #if j % 10 == 0 or j == i or j < 10:
        #    print(f"  ↩️  {data.index[j].date()} slope={slope} candidate={candidate_idx.date() if candidate_idx else None}")

        # Detect SenB slope break
        if pd.notna(slope) and abs(slope) > SLOPE_ABS_THRESHOLD:
            print(f"✅ Slope break found at {data.index[j].date()} slope={slope:.2f}")
            time_senb_rise = data.index[j]
            data.loc[time_senb_rise, "W_SenB_Consol_Start_SenB"] = True

            # 26 calendar weeks earlier → snap to nearest available bar at/before that time
            anchor_time_target = time_senb_rise - pd.Timedelta(weeks=26)
            idx = data.index.get_indexer([anchor_time_target], method="pad")
            if idx.size and idx[0] != -1:
                seg_start_time = data.index[idx[0]]
                data.loc[seg_start_time, "W_SenB_Consol_Start_Price"] = True
                print(f"   📍 Anchor marked at {seg_start_time.date()}")
            else:
                print("   ⚠️ No anchor found 26 weeks earlier.")
            found_senb_point = True
            break

        j -= 1

    # === Fallback if no SenB slope point was found ===
    if not found_senb_point:
        print("⚠️ No SenB slope point found — attempting fallback...")
        if candidate_idx is not None:
            delta = data.index[i] - candidate_idx
            print(f"   Candidate={candidate_idx.date()}, Δ={(delta.days)} days, val={candidate_val}")
            if pd.Timedelta(weeks=12) <= delta <= pd.Timedelta(weeks=52):
                data.loc[candidate_idx, "W_SenB_Consol_Start_Price"] = True
                print(f"🪶 Fallback global top marked at {candidate_idx.date()}")
            else:
                print("   ❌ Candidate rejected (too close or too far).")
        else:
            print("   ❌ No valid candidate found for fallback.")
