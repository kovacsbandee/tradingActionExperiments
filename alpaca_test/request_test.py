import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.models.bars import BarSet
import pandas as pd
from pandas import DataFrame

load_dotenv()

ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET_KEY)

symbol = ["AAPL"]
timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

bars_request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=timeframe
)

latest_bars = client.get_stock_bars(bars_request)
print(latest_bars.df)

