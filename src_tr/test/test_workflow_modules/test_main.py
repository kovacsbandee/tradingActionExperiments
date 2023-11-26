import os
from typing import List
from dotenv import load_dotenv
from datetime import datetime

from src_tr.test.test_workflow_modules.TestTradingClient import TestTradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import websocket
#import logging
#logging.basicConfig(level=logging.DEBUG)

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_stickers
from src_tr.main.scanners.PreMarketScanner import PreMarketScanner
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.test.test_workflow_modules.TestTradingManager import TestTradingManager

# 1) Scanner inicializálása -> watchlist létrehozás
load_dotenv()
STICKER_CSV_PATH = os.environ["STICKER_CSV_PATH"]
ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET_KEY)

nasdaq_stickers = get_nasdaq_stickers(file_path=STICKER_CSV_PATH)
start = datetime(2023, 11, 15, 0, 0)
end = datetime(2023, 11, 15, 23, 59)

trading_day = check_trading_day(start.strftime('%Y-%m-%d'))
scanning_day = calculate_scanning_day(trading_day)
scanner = PreMarketScanner(trading_day=trading_day,
                           scanning_day=scanning_day,
                           stickers=nasdaq_stickers,
                           lower_price_boundary=10,
                           upper_price_boundary=400,
                           price_range_perc_cond=10,
                           avg_volume_cond=25000)
# initialize sticker list:
scanner.calculate_filtering_stats()
recommended_sticker_list: List[dict] = scanner.recommend_premarket_watchlist()

# rec_st_list = ['AAPL', 'TSLA']

trading_client = TestTradingClient(init_cash=26000, sticker_list=recommended_sticker_list)
trading_client.initialize_positions()
data_generator = PriceDataGeneratorMain(recommended_sticker_list=recommended_sticker_list)
strategy = StrategyWithStopLoss(ma_short=5,
                        ma_long=12,
                        rsi_len=12,
                        stop_loss_perc=0.0,
                        epsilon=0.0015
                        )
trading_manager = TestTradingManager(data_generator=data_generator,
                                     strategy=strategy,
                                     trading_client=trading_client,
                                     api_key='test_key',
                                     secret_key='test_secret',
                                     rsi_threshold=20,
                                     minutes_before_trading_start=45
                                     )
data_generator.initialize_sticker_dict()

def download_daily_data(symbol, start, end):
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

    bars_request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end
    )
    latest_bars = client.get_stock_bars(bars_request).data
    daily_data_list = _convert_data(latest_bars, symbol)
    return daily_data_list

def _convert_data(latest_bars: dict, symbol: str):
    bar_list = []
    for e in latest_bars[symbol]:
        bar_list.append({
        'T': 'b',
        't': e.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'S': e.symbol,
        'o': e.open
    })
    return bar_list

all_stickers_daily_data: List[List] = []

for symbol in recommended_sticker_list:
    daily_data = download_daily_data(symbol=symbol['symbol'], start=start, end=end)
    all_stickers_daily_data.append(daily_data)
    
i = 0
while i < len(all_stickers_daily_data[0]):
    minute_bars = []
    for sticker_daily_data in all_stickers_daily_data:
        minute_bars.append(sticker_daily_data[i])
    trading_manager.handle_message(ws=None, message=minute_bars)
    minute_bars = []
    i += 1