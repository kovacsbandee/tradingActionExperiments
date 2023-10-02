import os
from datetime import datetime
from dotenv import load_dotenv
import websocket, json
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pandas as pd

load_dotenv()


ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]

wss_client = StockDataStream(api_key=ALPACA_KEY, secret_key=ALPACA_SECRET_KEY)

#rest_client = StockHistoricalDataClient(api_key=ALPACA_KEY, secret_key=ALPACA_SECRET_KEY)
#timeframe = TimeFrame(amount=20, unit=TimeFrameUnit.Hour)
#apple_data  = rest_client.get_stock_bars(
#    StockBarsRequest(symbol_or_symbols="AAPL", timeframe=timeframe
#))
#print(pd.DataFrame(apple_data))

# async handler
async def quote_data_handler(data):
    # quote data will arrive here
    data = pd.DataFrame(data)
    print(data)

wss_client.subscribe_quotes(quote_data_handler, "AAPL")

wss_client.run()