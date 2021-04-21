import pandas as pd
import requests
import math
from scipy.stats import percentileofscore as pscore
from statistics import mean as mean

import xlsxwriter
IEX_CLOUD_API_TOKEN = 'Tpk_059b97af715d417d9f49f50b51b1c448'


# Create ticker chunks of 100
def split_tickers(list_tickers, n):
    chunks = []
    for j in range(0, len(list_tickers), n):
        yield list_tickers[j:j + n]


# Function for acquiring portfolio size
def port_input():
    # while True:
    #     try:
    #         size = float(input("What is the value of your portfolio: "))
    #         break
    #     except ValueError:
    #         print("Invalid number. Please try again.")
    # return size
    return 100000

# Create csv object using a csv file
stocks = pd.read_csv('starter_stuff/S&P500_Holdings.csv')

# For future reference: single api call url and the base batch url before modification
"""
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/stats?token={IEX_CLOUD_API_TOKEN}'
batch = https://sandbox.iexapis.com/stable/stock/market/batch?symbols=aapl,tsla&types=quote,news,chart&range=1m&last=5
"""

# Create dataframe and column labels
my_cols = ['Ticker', 'Price', 'Market Cap',
           '1 Year Percent Return', '1 Year Return Percentile',
           '6 Month Percent Return', '6 Month Return Percentile',
           '3 Month Percent Return', '3 Month Return Percentile',
           '1 Month Percent Return', '1 Month Return Percentile',
           'MA Confirmation', 'Average Percentile Ranking',
           '% of Portfolio', 'Number of Shares to Buy']
data_frame = pd.DataFrame(columns=my_cols)

# Create chunks of 100 tickers and using each chunk...
for chunk in split_tickers(stocks['Symbol'], 100):
    # Create batch api url using the list of tickers in stocks
    holdings_string = ','.join(chunk)
    batch_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={holdings_string}' \
                f'&types=price,stats&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_url).json()

    # For every ticker in the chunk of 100...
    for ticker in chunk:
        if ticker in data:
            # Acquire data
            price = data[ticker]['price']
            market_cap = data[ticker]['stats']['marketcap']
            month1 = data[ticker]['stats']['month1ChangePercent']
            month3 = data[ticker]['stats']['month3ChangePercent']
            month6 = data[ticker]['stats']['month6ChangePercent']
            year1 = data[ticker]['stats']['year1ChangePercent']
            MA200 = data[ticker]['stats']['day200MovingAvg']
            MA50 = data[ticker]['stats']['day50MovingAvg']
            confirm = True if MA50 > MA200 else False
            # Add entry to dataframe
            data_frame = data_frame.append(
                pd.Series(
                    [
                        ticker, price, market_cap,
                        year1, 'N/A',
                        month6, 'N/A',
                        month3, 'N/A',
                        month1, 'N/A',
                        confirm, 'N/A',
                        'N/A', 'N/A'
                    ],
                    index=my_cols
                ),
                ignore_index=True
            )

# Calculate relative percentile for each each time period's percent change
time_periods = ['1 Year', '6 Month', '3 Month', '1 Month']
for row in data_frame.index:
    for time in time_periods:
        percent_change = f'{time} Percent Return'
        return_percentile = f'{time} Return Percentile'
        data_frame.loc[row, return_percentile] = \
            pscore(data_frame[percent_change], data_frame.loc[row, percent_change])/100

# Calculate the mean percentile ranking over all time periods
for row in data_frame.index:
    percentiles = []
    for time in time_periods:
        percentiles.append(data_frame.loc[row, f'{time} Return Percentile'])
    data_frame.loc[row, 'Average Percentile Ranking'] = mean(percentiles)/100

# Sort data frame to display Highest Average Percentile Ranking confirming momentum with MA position
data_frame.sort_values('Average Percentile Ranking', ascending=False, inplace=True)
data_frame = data_frame[:50]
data_frame.reset_index(inplace=True, drop=True)

# Calculate aggregated market cap of all tickers in data frame, determine size of portfolio positions (number of shares)
# based on market cap relative to the total aggregated amount
total_market_cap = sum(data_frame['Market Cap'])
portfolio_size = port_input()
for i in range(len(data_frame)):
    percentage = data_frame.loc[i, 'Market Cap']/total_market_cap
    data_frame.loc[i, '% of Portfolio'] = percentage
    position_size = portfolio_size * percentage
    shares = math.floor(position_size/data_frame.loc[i, "Price"])
    data_frame.loc[i, "Number of Shares to Buy"] = shares

# Load data into xlsx file
writer = pd.ExcelWriter('momentum_trades.xlsx', engine='xlsxwriter')
data_frame.to_excel(writer, "Recommended Trades", index=False)

# Determine colors and create format templates for xlsx writer
background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
    {
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

dollar_format = writer.book.add_format(
    {
        'num_format': '$0.00',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

int_format = writer.book.add_format(
    {
        'num_format': '0',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

percent_format = writer.book.add_format(
    {
        'num_format': '0.000%',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

# Apply formatting to each excel column
formatting = {
    'A': ['Ticker', string_format],
    'B': ['Price', dollar_format],
    'C': ['Market Cap', dollar_format],
    'D': ['1 Year Percent Return', percent_format],
    'E': ['1 Year Return Percentile', percent_format],
    'F': ['6 Month Percent Return', percent_format],
    'G': ['6 Month Return Percentile', percent_format],
    'H': ['3 Month Percent Return', percent_format],
    'I': ['3 Month Return Percentile', percent_format],
    'J': ['1 Month Percent Return', percent_format],
    'K': ['1 Month Return Percentile', percent_format],
    'L': ['MA Confirmation', string_format],
    'M': ['Average Percentile Ranking', percent_format],
    'N': ['% of Portfolio', percent_format],
    'O': ['Number of Shares to Buy', int_format]
}

for key in formatting.keys():
    # Apply formatting to each column
    writer.sheets['Recommended Trades'].set_column(f'{key}:{key}', 25, formatting[key][1])

    # Overwrite the column title
    writer.sheets['Recommended Trades'].write(f'{key}1', formatting[key][0], formatting[key][1])

writer.save()