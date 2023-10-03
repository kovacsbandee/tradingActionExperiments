import os
from dotenv import load_dotenv
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest


load_dotenv()

ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET_KEY)

# multi symbol request - single symbol is similar
multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=["SPY", "GLD", "TLT"])

latest_multisymbol_quotes = client.get_stock_bars(multisymbol_request_params)
print(latest_multisymbol_quotes["GLD"].low)

