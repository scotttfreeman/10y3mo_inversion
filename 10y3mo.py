import pandas as pd
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Define a function to get data up to the trough for each period
def get_data_to_trough(df):
    for col in df.columns:
        trough_index = df[col].idxmin()
        df[col] = df[col].loc[:trough_index]
    return df

# Load the data
df = pd.read_excel('10y3mo.xlsx')

def get_periods(df, override_start_dates=None):
    results = []

    if override_start_dates is not None:
        for date_str in override_start_dates:
            start_date = pd.to_datetime(date_str)  # Convert string to datetime
            end_date = start_date + timedelta(weeks=150)
            results.append({'start_date': start_date, 'end_date': end_date})
        return pd.DataFrame(results)

    in_period = False
    reached_neg_0025 = False
    reached_neg_001_in_20_weeks = False
    start_date = None
    end_date = None

    for i in range(len(df)):
        if not in_period and df.loc[i, '10y3mo'] < 0:
            in_period = True
            start_date = df.loc[i, 'date']
        elif in_period:
            if not reached_neg_001_in_20_weeks and df.loc[i, 'date'] - start_date > timedelta(weeks=20):
                in_period = False
                reached_neg_0025 = False
                start_date = None
                end_date = None
            elif not reached_neg_001_in_20_weeks and df.loc[i, '10y3mo'] <= -0.001 and df.loc[i, 'date'] - start_date <= timedelta(weeks=20):
                reached_neg_001_in_20_weeks = True
            elif df.loc[i, '10y3mo'] <= -0.0025:
                reached_neg_0025 = True
            elif reached_neg_001_in_20_weeks and reached_neg_0025 and df.loc[i, '10y3mo'] >= 0.01:
                in_period = False
                end_date = df.loc[i, 'date']
                results.append({'start_date': start_date, 'end_date': end_date})
                start_date = None
                end_date = None
                reached_neg_001_in_20_weeks = False
                reached_neg_0025 = False

    return pd.DataFrame(results)

# Provide your custom start dates here, or leave it as None to use the automatic period determination
override_start_dates = ['1969-01-03', '1973-02-23', '1980-09-12', '1989-05-26', '2000-04-07','2006-07-21', '2019-03-22']  # None for automatic period determination

results_df = get_periods(df, override_start_dates)

# The rest of your code remains the same

spx_df = pd.DataFrame()
cont_claims_df = pd.DataFrame()
initial_claims_df = pd.DataFrame()
print(results_df)

for i, row in results_df.iterrows():
    start_date = row['start_date']
    end_date = row['end_date']
    
    # Slice the original DataFrame to get the rows for this period
    period_df = df.loc[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()  
    
    # Normalize the data to 100 at the start of the period
    period_df['spx_norm'] = 100 * period_df['spx'] / period_df.iloc[0]['spx']
    period_df['cont_claims_norm'] = 100 * period_df['cont_claims'] / period_df.iloc[0]['cont_claims']
    period_df['initial_claims_norm'] = 100 * period_df['initial_claims'] / period_df.iloc[0]['initial_claims']

    # Index the data to weeks since the start of the period
    period_df.index = (period_df['date'] - start_date).dt.days // 7
    
    # Rename the normalized series and add them to the corresponding DataFrames
    spx_df[start_date] = period_df['spx_norm']
    cont_claims_df[start_date] = period_df['cont_claims_norm']
    initial_claims_df[start_date] = period_df['initial_claims_norm']
    # print(spx_df)
# Apply the function to your dataframes
spx_df = get_data_to_trough(spx_df)

# Add the current cycle to the dataframes
current_start_date = pd.to_datetime("2022-10-28")
current_end_date = current_start_date + timedelta(weeks=120)

current_period_df = df.loc[(df['date'] >= current_start_date) & (df['date'] <= current_end_date)].copy()

# Normalize the data to 100 at the start of the current period
current_period_df['spx_norm'] = 100 * current_period_df['spx'] / current_period_df.iloc[0]['spx']
current_period_df['cont_claims_norm'] = 100 * current_period_df['cont_claims'] / current_period_df.iloc[0]['cont_claims']
current_period_df['initial_claims_norm'] = 100 * current_period_df['initial_claims'] / current_period_df.iloc[0]['initial_claims']

# Index the data to weeks since the start of the current period
current_period_df.index = (current_period_df['date'] - current_start_date).dt.days // 7

# Add the current period data to the corresponding DataFrames
spx_df[current_start_date] = current_period_df['spx_norm']
cont_claims_df[current_start_date] = current_period_df['cont_claims_norm']
initial_claims_df[current_start_date] = current_period_df['initial_claims_norm']


# plot the data
fig, axs = plt.subplots(3, 1, figsize=(10,15))  # 3 rows, 1 column

dfs = [spx_df, cont_claims_df, initial_claims_df]
titles = ['S&P 500 Time to Trough Following 10Y3M Inversion', 'Path of Continued Claims Following 10Y3M Inversion', 'Path of Initial Claims Following 10Y3M Inversion']

for i, ax in enumerate(axs):
    df = dfs[i]
    title = titles[i]

    # Plot the data
    for col in df.columns:
        # Limit the data to the same range as the corresponding SPX period
        if i > 0:  # Skip the first DataFrame (SPX)
            end_week = spx_df[col].dropna().index[-1]  # Get the last week of the SPX period
            df[col] = df[col].loc[:end_week]  # Limit the data to this range

        line, = ax.plot(df[col], label=col.date())  # use .date() to remove time component

        # Check if line is the 'Current' line before creating a marker
        if line.get_label() == '2022-10-28':
            line.set_linewidth(2.5)
            line.set_color('000000')
            line.set_label('Current')
        else:
            # Add a circular marker at the trough (the end of the line)
            trough_week = df[col].dropna().index[-1]  # Get the last week (the trough)
            trough_value = df[col].loc[trough_week]  # Get the value at the trough
            ax.plot(trough_week, trough_value, 'o', color=line.get_color())  # Plot the marker with the same color as the line

        # After all lines have been plotted, modify their properties
        lines = ax.get_lines()  # get all lines
        for line in lines:
            if line.get_label() == '2022-10-28':
                line.set_linewidth(2.5)
                line.set_color('000000')
                line.set_label('Current')

    # Format legend dates
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='best')

    # Set title
    ax.set_title(title, fontweight='bold')

    # lines = ax.get_lines() # set line color, width
    # for line in lines:
    #     if line.get_label() == '2022-10-28':
    #         line.set_linewidth(2.5)
    #         line.set_color('#000000')
    #         line.set_label('Current')

    # plt.ylabel('Index = 100 on first week of inversion; dot markers = S&P trough')
    plt.xlabel('Weeks to Trough')

plt.tight_layout()
plt.show()
