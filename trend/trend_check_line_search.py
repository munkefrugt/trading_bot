from trend.build_trend_line import get_trend_line, find_trend_start_point
from trend.macro_trendline import build_macro_trendline_from_last_X
#=== search for micro trendline ===
def check_micro_trendline(data, i, prev_date, current_date,price_above_or_inside_cloud):    
    if data.at[prev_date, 'Searching_micro_trendline']:
        data,mirco_trendline_end = get_trend_line(data, current_index=i)
        if mirco_trendline_end:
            data.at[current_date, 'Searching_micro_trendline'] = False
            #print(f"🔍 Micro trendline found at {current_date}")
            return data
        
        elif price_above_or_inside_cloud: 
            data.at[current_date, 'Searching_micro_trendline'] = False
            #print(f"🔍 Micro trendline search ended at {current_date} due to price in D_cloud.")
            data.at[current_date, 'Searching_macro_trendline'] = True

            return data
        
        else:
            data.at[current_date, 'Searching_micro_trendline'] = True
            #print(f"🔍 Continuing search for micro trendline at {current_date}.")
    
def check_macro_trendline(data, i, prev_date, current_date):    

        # === search for macro trendline ===
    if (data.at[prev_date, 'Searching_macro_trendline'] or data.at[current_date, 'Searching_macro_trendline']):

        # find last time Start_of_Dead_Trendline was True
        last_top_date = data.loc[data['Start_of_Dead_Trendline']].last_valid_index()
        if last_top_date is None:
            days_since_last_top = None
        else:
            days_since_last_top = (current_date - last_top_date).days


        time_ran_out = False
        if data['Real_uptrend_start'].any():
            last_start = data.index[data['Real_uptrend_start']].max()
            if (current_date - last_start).days > 14:
                time_ran_out = True
        
        # only search if 5 months have passed
        if days_since_last_top is not None and days_since_last_top >= 5*30:
            # data, macro_trendline_end = get_trend_line(
            #     data,
            #     current_index=i,
            #     column_name='Macro_trendline_from_X'
            # )

            data, macro_trendline_end = build_macro_trendline_from_last_X(
                data,
                current_index=i,
            )


            if macro_trendline_end:
                data.at[current_date, 'Searching_macro_trendline'] = False
                print(f"🛑 Macro trendline found at {current_date}")
                return data

            # elif time_ran_out:
            #     data.at[current_date, 'Searching_macro_trendline'] = False
            #     print(f"⏹ Macro trendline search ended at {current_date} (time limit reached)")
            #     return data

            else:
                data.at[current_date, 'Searching_macro_trendline'] = True
                #print(f"🔍 Continuing search for macro trendline at {current_date}.")
        
        # elif time_ran_out:
        #     data.at[current_date, 'Searching_macro_trendline'] = False
        #     print(f"⏹ Macro trendline search ended at {current_date} (time limit reached)")
        #     return data
        else:
            data.at[current_date, 'Searching_macro_trendline'] = True
         