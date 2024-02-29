import os
from dotenv import load_dotenv
from datetime import date
import schedule
import time
import websocket

from alpaca.trading.client import TradingClient

from src_tr.main.data_sources.run_params import param_dict
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

# WS
WEBSOCKET_APP = None

# nap elején
def define_dates():
    global trading_day, scanning_day
    trading_day = check_trading_day(date.today())
    scanning_day = calculate_scanning_day(trading_day)

def reset_components():
    pass

def initialize_components():
    pass

def initialize_websocket():
    global WEBSOCKET_APP
    WEBSOCKET_APP = websocket.WebSocketApp(url=SOCKET_URL, 
                            on_open=trading_manager.on_open,
                            on_message=trading_manager.handle_message,
                            on_close=trading_manager.on_close,
                            on_error=trading_manager.on_error,
                            on_ping=trading_manager.on_ping,
                            on_pong=trading_manager.on_pong)

def create_daily_watchlist():
    pass

# kapcsolatszakadás esetére load_daily_watchlist

def open_websocket_connection():
    pass


# nap végén
def close_open_positions():
    pass

def close_websocket_connection():
    pass

def process_trading_day_data():
    pass


def run_scheduler():
    # if today is not market_holiday or not holiday
    schedule.every().monday.at("15:30").do()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Received KeyboardInterrupt, closing...")
            #close()
            break