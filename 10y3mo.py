import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

# Specify if the input data is monthly or weekly
data_frequency = 'monthly'  # Change to 'monthly' for monthly data
weekly_end_date = 150
monthly_end_date = 36

# Define a function to get data up to the trough for each period
def get_data_to_trough(df):
    for col in df.columns:
        trough_index = df[col].idxmin()
        df[col] = df[col].loc[:trough_index]
    return df

# Specify your custom start dates here
start_dates = {
    'weekly': ['1969-01-03', '1973-02-23', '1980-09-12', '1989-05-26', '2000-04-07','2006-07-21', '2019-03-22'],
    'monthly': ['1969-12-31', '1973-03-31', '1978-10-31', '1989-05-31', '2000-07-31','2006-02-28', '2019-03-31']
}

# Load the data
df = pd.read_excel(f'10y3mo_{data_frequency}.xlsx')

# Convert start_dates to datetime
start_dates = [pd.to_datetime(date) for date in start_dates[data_frequency]]

# Create a dictionary to hold DataFrames for each series
dfs = {col: pd.DataFrame() for col in df.columns if col not in ['date', '10y3mo']}

end_date = weekly_end_date if data_frequency == 'weekly' else monthly_end_date
print(end_date)
for start_date in start_dates:
    # Slice the original DataFrame to get the rows for this period
    if data_frequency == 'weekly':
        period_df = df.loc[(df['date'] >= start_date) & (df['date'] <= start_date + timedelta(weeks=end_date))].copy()
    elif data_frequency == 'monthly':
        period_df = df.loc[(df['date'] >= start_date) & (df['date'] <= start_date + pd.DateOffset(months=end_date))].copy()

   
    # Normalize the data to 100 at the start of the period
    for col in period_df.columns:
        if col not in ['date', '10y3mo']:
            period_df[col + '_norm'] = 100 * period_df[col] / period_df.iloc[0][col]
   
    # Create a new column for the week or month number
    period_df['period_num'] = (period_df['date'] - start_date).dt.days // (7 if data_frequency == 'weekly' else 30)

    # Group by the period number and aggregate other columns
    period_df = period_df.groupby('period_num').mean()  # or use some other aggregation function

    # Rename the normalized series and add them to the corresponding DataFrames
    for col, df_ in dfs.items():
        if 'spx' in col.lower():
            period_df_copy = get_data_to_trough(period_df.copy())
            df_[start_date] = period_df_copy[col + '_norm']
        else:
            df_[start_date] = period_df[col + '_norm']

# Plot the data
fig, axs = plt.subplots(len(dfs), 1, figsize=(10, 15))  # One row per series

spx_df = dfs['spx']

for i, (col, df_) in enumerate(dfs.items()):
    ax = axs[i]

    # Plot the data
    for start_date in start_dates:
        # Limit the data to the same range as the corresponding SPX period
        if col != 'spx':  # Skip the first DataFrame (SPX)
            end_week = spx_df[start_date].dropna().index[-1]  # Get the last week of the SPX period
            df_[start_date] = df_[start_date].loc[:end_week]  # Limit the data to this range
        
        line, = ax.plot(df_[start_date], label=start_date.date())  # use .date() to remove time component

        # Check if line is the 'Current' line before creating a marker
        if line.get_label() == '2022-10-28':
            line.set_linewidth(2.5)
            line.set_color('000000')
            line.set_label('Current')

    # Format legend dates
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='best')

    # Set title
    ax.set_title(f'{col} Following 10Y3M Inversion', fontweight='bold')

    # Set x-axis limit
    ax.set_xlim(0, end_date)

plt.xlabel(f'{data_frequency.capitalize()}s to Trough')
plt.tight_layout()
plt.show()
