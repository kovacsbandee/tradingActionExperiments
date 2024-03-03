import os
from dotenv import load_dotenv
from datetime import date, datetime
import schedule
import time
import websocket
import traceback

from alpaca.trading.client import TradingClient

from src_tr.main.data_sources.run_params import param_dict
from src_tr.main.data_sources.sp500 import sp500
from src_tr.main.scanners.PreMarketScannerMain import PreMarketScannerMain
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmMain import TradingAlgorithmMain
from src_tr.main.trading_managers.TradingManagerMain import TradingManagerMain
from src_tr.main.utils.DataManager import DataManager
from src_tr.main.utils.utils import save_watchlist_bin, load_watchlist_bin
from src_tr.main.utils.data_loaders import download_scanning_day_alpaca_data
from src_tr.main.utils.utils import check_trading_day, calculate_scanning_day

load_dotenv()

# all-time constants
ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL = os.environ["SOCKET_URL"]
TRADING_CLIENT = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)
RUN_ID = "eMACD16-6-3_cAVG_eRSI10_cRSI70"
SCANNER_PARAMS = param_dict[RUN_ID]['scanner_params']
ALGO_PARAMS = param_dict[RUN_ID]['algo_params']
MODE = "live"
WEBSOCKET_APP = None

# daily components
trading_day = None
scanning_day = None
data_manager = None
run_parameters = None
scanner = None
recommended_symbol_list = None
data_generator = None
trading_algorithm = None
trading_manager = None

# on trading day start
def define_dates():
    global trading_day, scanning_day
    print(f"Setting trading day dates... {datetime.now()}")
    trading_day = check_trading_day(date.today())
    scanning_day = calculate_scanning_day(trading_day)
    print(f"Finished setting trading day dates @ {datetime.now()}")
    print(f"\t [Trading day: {trading_day}]\n\t[Scanning day: {scanning_day}]")

def reset_components():
    global data_manager, run_parameters, scanner, recommended_symbol_list, \
        data_generator, trading_algorithm, trading_manager
    if trading_day != 'holiday':
        print(f"Resetting previous trading components... {datetime.now()}")
        data_manager = None
        run_parameters = None
        scanner = None
        recommended_symbol_list = None
        data_generator = None
        trading_algorithm = None
        trading_manager = None
        print(f"Finished resetting previous trading components @ {datetime.now()}")
    else:
        print("Holiday")
        return

def initialize_components():
    global data_manager, run_parameters, scanner, recommended_symbol_list, \
        data_generator, trading_algorithm, trading_manager, \
        ALPACA_KEY, ALPACA_SECRET_KEY, SOCKET_URL, TRADING_CLIENT, RUN_ID, SCANNER_PARAMS, ALGO_PARAMS, MODE
    if trading_day != 'holiday':
        print(f"Initializing new trading components... {datetime.now()}")
        data_manager = DataManager(mode=MODE, trading_day=trading_day, scanning_day=scanning_day, run_id=RUN_ID)
        run_parameters = {
                            'run_id': RUN_ID,
                            'trading_day': trading_day.strftime('%Y_%m_%d'),
                            'symbol_csvs': 'sp500',
                            'init_cash': float(TRADING_CLIENT.get_account().cash),
                            'lower_price_boundary': 10,
                            'upper_price_boundary': 400,
                            'price_range_perc_cond': 5,
                            'avg_volume_cond': 10000,
                            'ma_short': ALGO_PARAMS["entry_windows"]["short"],
                            'ma_long': ALGO_PARAMS["entry_windows"]["long"],
                            'entry_signal': ALGO_PARAMS["entry_windows"]["signal"] if "signal" in ALGO_PARAMS["entry_windows"] else 0.0,
                            'epsilon': ALGO_PARAMS["entry_windows"]["epsilon"] if "epsilon" in ALGO_PARAMS["entry_windows"] else 0.0,
                            'rsi_len': 12,
                            'stop_loss_perc': 0.0,
                            'macd_long' : SCANNER_PARAMS["windows"]["long"],
                            'macd_short' : SCANNER_PARAMS["windows"]["short"],
                            'signal_line' : SCANNER_PARAMS["windows"]["signal"]
                        }
        data_manager.create_daily_dirs()
        data_manager.save_params(params=run_parameters)
        daily_dir_name = f"{RUN_ID}/{data_manager.daily_dir_name}"
        data_loader = download_scanning_day_alpaca_data
        scanner = PreMarketScannerMain(trading_day=trading_day,
                                scanning_day=scanning_day,
                                symbols=sp500,
                                scanner_params=SCANNER_PARAMS,
                                run_id=RUN_ID,
                                daily_dir_name=daily_dir_name,
                                data_loader_func=data_loader,
                                key=ALPACA_KEY,
                                secret_key=ALPACA_SECRET_KEY)
        recommended_symbol_list = scanner.recommend_premarket_watchlist()
        #save_watchlist_bin(recommended_symbol_list, trading_day)
        # NOTE: teszteléshez:
        #recommended_symbol_list = load_watchlist_bin(trading_day=trading_day)
        data_manager.recommended_symbol_list = recommended_symbol_list
        data_generator = PriceDataGeneratorMain(recommended_symbol_list=recommended_symbol_list)
        trading_algorithm = TradingAlgorithmMain(trading_day=trading_day, 
                                                 daily_dir_name=daily_dir_name, 
                                                 run_id=RUN_ID)
        trading_manager = TradingManagerMain(data_generator=data_generator,
                                            trading_algorithm=trading_algorithm,
                                            algo_params=ALGO_PARAMS,
                                            trading_client=TRADING_CLIENT,
                                            api_key=ALPACA_KEY,
                                            secret_key=ALPACA_SECRET_KEY,
                                            ws_close_func=close_websocket_connection)
        print(f"Finished initializing new trading components @ {datetime.now()}")
    else:
        print("Holiday")
        return

def initialize_websocket():
    global WEBSOCKET_APP
    if WEBSOCKET_APP is None and trading_day != 'holiday':
        print(f"Initializing WebSocket app @ {datetime.now()}")
        WEBSOCKET_APP = websocket.WebSocketApp(url=SOCKET_URL, 
                                on_open=trading_manager.on_open,
                                on_message=trading_manager.handle_message,
                                on_close=trading_manager.on_close,
                                on_error=trading_manager.on_error,
                                on_ping=trading_manager.on_ping,
                                on_pong=trading_manager.on_pong)
    else:
        return

def reload_watchlist():
    global recommended_symbol_list
    recommended_symbol_list = load_watchlist_bin(trading_day)

def open_websocket_connection():
    global WEBSOCKET_APP
    if trading_day != 'holiday':
        print(f"Starting WebSocket app @ {datetime.now()}")
        WEBSOCKET_APP.run_forever()
    else:
        print("Holiday")
        return

# nap végén
def close_open_positions():
    global TRADING_CLIENT
    if trading_day != 'holiday':
        print(f"Closing all open positions... {datetime.now()}")
        TRADING_CLIENT.close_all_positions()
        print(f"All positions successfully closed @ {datetime.now()}")
    else:
        print("Holiday")
        return

def process_trading_day_data():
    global data_manager, scanner, data_generator, recommended_symbol_list
    if trading_day != 'holiday':
        print(f"Processing trading day data... {datetime.now()}")
        try:
            data_manager.save_daily_statistics_and_aggregated_plots(recommended_symbols=scanner.recommended_symbols,
                                                                    symbol_dict=data_generator.symbol_dict)
            data_manager.save_daily_charts(symbol_dict=data_generator.symbol_dict)
            print('Experiment ran successfully, with run id: ', data_manager.run_id, 'and run parameters', data_manager.run_parameters)
        except:
            traceback.print_exc()
    else:
        print("Holiday")
        return

def close_websocket_connection():
    global WEBSOCKET_APP
    if WEBSOCKET_APP is not None:
        WEBSOCKET_APP.close()
    print(f"WebSocket connection closed @ {datetime.now()}")


def run_scheduler():
    schedule.every().day.at("15:15:00").do(define_dates)
    schedule.every().day.at("15:15:05").do(reset_components)
    schedule.every().day.at("15:15:10").do(initialize_components)
    schedule.every().day.at("15:29:55").do(initialize_websocket)
    schedule.every().day.at("15:30:00").do(open_websocket_connection)
    #NOTE: WS close a TradingManagerMain.handle_message()-ben
    schedule.every().day.at("21:00:10").do(close_open_positions)
    schedule.every().day.at("21:05:00").do(process_trading_day_data)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Received KeyboardInterrupt, closing...")
            close_websocket_connection()
            break