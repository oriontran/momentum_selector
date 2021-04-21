# Quantitative Momentum Selector
Uses IEX Cloud infrastructure to query for percent return of companies from the
S&P500 (optionally NASDAQ or any other index fund). Calculates percentile for 
each ticker of return percentage over 4 time periods (one year, six month, 
three month, and one month). Uses moving average to confirm momentum of ticker 
and returns a csv of highest momentum tickers 
