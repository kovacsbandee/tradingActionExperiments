import os
from typing import List
from dotenv import load_dotenv
from datetime import date
from alpaca.trading.client import TradingClient
import websocket
#import logging
#logging.basicConfig(level=logging.DEBUG)

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_symbols
from src_tr.main.scanners.PreMarketScannerMain import PreMarketScannerMain
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmMain import TradingAlgorithmMain
from src_tr.main.trading_managers.TradingManagerMain import TradingManagerMain
from src_tr.main.utils.DataManager import DataManager
from src_tr.main.utils.data_loaders import download_scanning_day_alpaca_data
from src_tr.main.data_sources.sp500 import sp500
from src_tr.main.data_sources.run_params import param_dict

# 1) Scanner inicializálása -> watchlist létrehozás
load_dotenv()
ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]
MODE='live'
#SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]

#scanner_symbols = get_nasdaq_symbols(file_path=SYMBOL_CSV_PATH)

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)
trading_day = check_trading_day(date(2024, 2, 19))
scanning_day = calculate_scanning_day(trading_day)
run_id = "eMACD16-6-3_cAVG_eRSI10_cRSI70"
scanner_params = param_dict[run_id]['scanner_params']
algo_params = param_dict[run_id]['algo_params']

data_manager = DataManager(mode=MODE, trading_day=trading_day, scanning_day=scanning_day, run_id=run_id)

run_parameters = \
    {
        'run_id': run_id,
        'trading_day': trading_day.strftime('%Y_%m_%d'),
        'symbol_csvs': 'sp500',
        'init_cash': 10000,
        'lower_price_boundary': 10,
        'upper_price_boundary': 400,
        'price_range_perc_cond': 5,
        'avg_volume_cond': 10000,
        'ma_short': algo_params["entry_windows"]["short"],
        'ma_long': algo_params["entry_windows"]["long"],
        'entry_signal': algo_params["entry_windows"]["signal"] if "signal" in algo_params["entry_windows"] else 0.0,
        'epsilon': algo_params["entry_windows"]["epsilon"] if "epsilon" in algo_params["entry_windows"] else 0.0,
        'rsi_len': 12,
        'stop_loss_perc': 0.0,
        'macd_long' : scanner_params["windows"]["long"],
        'macd_short' : scanner_params["windows"]["short"],
        'signal_line' : scanner_params["windows"]["signal"]
    }

data_manager.create_daily_dirs()
data_manager.save_params(params=run_parameters)
daily_dir_name = f"{run_id}/{data_manager.daily_dir_name}"

data_loader = download_scanning_day_alpaca_data

scanner = PreMarketScannerMain(trading_day=trading_day,
                           scanning_day=scanning_day,
                           symbols=sp500,
                           scanner_params=scanner_params,
                           run_id=run_id,
                           daily_dir_name=daily_dir_name,
                           data_loader_func=data_loader,
                           key=ALPACA_KEY,
                           secret_key=ALPACA_SECRET_KEY)

# initialize symbol list:
recommended_symbol_list: List[dict] = scanner.recommend_premarket_watchlist()
data_manager.recommended_symbol_list = recommended_symbol_list

data_generator = PriceDataGeneratorMain(recommended_symbol_list=recommended_symbol_list)

trading_algorithm = TradingAlgorithmMain(trading_day=trading_day, daily_dir_name=daily_dir_name)

trading_manager = TradingManagerMain(data_generator=data_generator,
                                     trading_algorithm=trading_algorithm,
                                     algo_params=algo_params,
                                     trading_client=trading_client,
                                     api_key=ALPACA_KEY,
                                     secret_key=ALPACA_SECRET_KEY)

ws = websocket.WebSocketApp(url=SOCKET_URL, 
                            on_open=trading_manager.on_open,
                            on_message=trading_manager.handle_message,
                            on_close=trading_manager.on_close,
                            on_error=trading_manager.on_error)
                            #on_ping=trading_manager.on_ping,
                            #on_pong=trading_manager.on_pong)


if __name__ == "__main__":
    try:
        ws.run_forever(reconnect=True, ping_interval=30, ping_timeout=10)
    except Exception as e:
        print(e)
        print("WebSocket connection closed.")
        #ws.close()