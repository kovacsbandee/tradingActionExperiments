'''
Vajon meg lehetne oldani, hogy ha már van aznapra scanner_stats és kimentett daily_price_df a kiválasztott symbol-okra,
akkor ha kézzel befejezzük a program futását és űjra elindítjuk, akkor check-olja, hogy mi van már meg és onna folytatja?
Ez sokat tudna dobni a fejlesztésen szerinte, de nem tudom, hogy meg lehet-e csinálni....
'''

import os
from typing import List
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
import websocket
#import logging
#logging.basicConfig(level=logging.DEBUG)

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_symbols
from src_tr.main.scanners.PreMarketScanner import PreMarketScanner
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from tradingActionExperiments.src_tr.main.trading_algorithms.TradingAlgorithmWithStopLoss import TradingAlgorithmWithStopLoss
from src_tr.main.trading_managers.TradingManagerMain import TradingManagerMain

# 1) Scanner inicializálása -> watchlist létrehozás
load_dotenv()
ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]

nasdaq_symbols = get_nasdaq_symbols(file_path=SYMBOL_CSV_PATH)

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)
trading_day = check_trading_day('2023-12-28')
scanning_day = calculate_scanning_day(trading_day)

scanner = PreMarketScanner(trading_day=trading_day,
                           scanning_day=scanning_day,
                           symbols=nasdaq_symbols,
                           lower_price_boundary=10,
                           upper_price_boundary=400,
                           price_range_perc_cond=10,
                           avg_volume_cond=25000)

# initialize symbol list:
scanner.calculate_filtering_stats()
recommended_symbol_list: List[dict] = scanner.recommend_premarket_watchlist()

# rec_st_list = ['AAPL', 'TSLA']

data_generator = PriceDataGeneratorMain(recommended_symbol_list=recommended_symbol_list)

trading_algorithm = TradingAlgorithmWithStopLoss(ma_short=5,
                                ma_long=12,
                                rsi_len=12,
                                stop_loss_perc=0.0,
                                epsilon=0.0015,
                                trading_day=trading_day)

trading_manager = TradingManagerMain(data_generator=data_generator,
                                     trading_algorithm=trading_algorithm,
                                     trading_client=trading_client,
                                     api_key=ALPACA_KEY,
                                     secret_key=ALPACA_SECRET_KEY,
                                     rsi_threshold=20,
                                     minutes_before_trading_start=2)

ws = websocket.WebSocketApp(url=SOCKET_URL, 
                            on_open=trading_manager.on_open,
                            on_message=trading_manager.handle_message,
                            on_close=trading_manager.on_close,
                            on_error=trading_manager.on_error,
                            on_ping=trading_manager.on_ping,
                            on_pong=trading_manager.on_pong)

#FONTOS!
# TRADING DAY-T UPDATELNI KELL (NAPONTA, NYILVÁN)

if __name__ == "__main__":
    try:
        ws.run_forever(reconnect=True, ping_interval=30, ping_timeout=10)
    except Exception as e:
        print(e)
        print("WebSocket connection closed.")
        #ws.close()