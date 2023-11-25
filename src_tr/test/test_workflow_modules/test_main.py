import os
from typing import List
from dotenv import load_dotenv
from src_tr.test.test_workflow_modules.TestTradingClient import TestTradingClient
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

nasdaq_stickers = get_nasdaq_stickers(file_path=STICKER_CSV_PATH)

trading_day = check_trading_day('2023-11-20')
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
initial_capital = float(trading_client.cash)
data_generator = PriceDataGeneratorMain(recommended_sticker_list=recommended_sticker_list)
strategy = StrategyWithStopLoss(ma_short=5,
                        ma_long=5,
                        rsi_len=12,
                        stop_loss_perc=0.0,
                        epsilon=0.0015,
                        initial_capital=initial_capital
                        )
trading_manager = TestTradingManager(data_generator=data_generator,
                                     strategy=strategy,
                                     trading_client=trading_client,
                                     api_key='test_key',
                                     secret_key='test_secret',
                                     rsi_threshold=20,
                                     minutes_before_trading_start=2
                                     )

# itt for loopban 'szimuláljuk' a websocketet
# ...