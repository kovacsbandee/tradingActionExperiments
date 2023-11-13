from datetime import datetime
from typing import List
from polygon import RESTClient
from polygon.rest.models import PreviousCloseAgg

client = RESTClient(api_key="Rdcy29x7wooeMAlqKIsnTfDiHOaz0J_d")

apple = "AAPL"
tesla = "TSLA"
microsoft = "MSFT"

# List Aggregates (Bars)
aggs = []
for a in client.list_aggs(ticker=apple, multiplier=1, timespan="minute", from_="2023-11-10", to="2023-11-10", limit=50000):
    aggs.append(a.__dict__)

for x in range(0, 10):
    print(aggs[x]['open'])

apple_prevclose: List[PreviousCloseAgg] = client.get_previous_close_agg(ticker=apple),
#tesla_prevclose: List[PreviousCloseAgg] = client.get_previous_close_agg(ticker=tesla),
#microsoft_prevclose: List[PreviousCloseAgg] = client.get_previous_close_agg(ticker=microsoft)

epoch_time = apple_prevclose[0].timestamp
date_object = datetime.utcfromtimestamp(epoch_time / 1000)
formatted_date = date_object.strftime("%Y-%m-%d %H:%M:%S UTC")

print(f'Datetime: {formatted_date}, previous close price: {apple_prevclose[0].close}')


## Get Last Trade
#trade = client.get_last_trade(ticker=ticker)
#print(trade)
#
## List Trades
#trades = client.list_trades(ticker=ticker, timestamp="2022-01-04")
#for trade in trades:
#    print(trade)
#
## Get Last Quote
#quote = client.get_last_quote(ticker=ticker)
#print(quote)
#
## List Quotes
#quotes = client.list_quotes(ticker=ticker, timestamp="2022-01-04")
#for quote in quotes:
#    print(quote)