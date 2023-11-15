import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
import websocket
#import logging
#logging.basicConfig(level=logging.DEBUG)

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_stickers
from src_tr.main.scanners.AndrewAzizRecommendedScanner import AndrewAzizRecommendedScanner
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.trading_managers.TradingManagerMain import TradingManagerMain

# 1) Scanner inicializálása -> watchlist létrehozás
load_dotenv()
ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]
TEST_SYMBOL = "AAPL"

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)
trading_day = check_trading_day('2023-10-16')
scanning_day = calculate_scanning_day(trading_day)
scanner = AndrewAzizRecommendedScanner(name="AzizScanner",
                                       trading_day=trading_day,
                                       scanning_day=scanning_day,
                                       stickers=[TEST_SYMBOL],
                                       lower_price_boundary=10,
                                       upper_price_boundary=400,
                                       price_range_perc_cond=10,
                                       avg_volume_cond=25000,
                                       #std_close_lower_boundary_cond=0.25 #TODO: ezt számoljuk az előző napi Yahoo-adatokból
                                       )
rec_st_list = [TEST_SYMBOL] # TODO: ennek kell majd a scannerből jönnie (pl. scanner.recommended_sticker_list)

data_generator = PriceDataGeneratorMain(recommended_sticker_list=rec_st_list)
initial_capital = float(trading_client.get_account().cash)
strategy = StrategyWithStopLoss(ma_short=5,
                        ma_long=12,
                        stop_loss_perc=0.0,
                        epsilon=0.01,
                        initial_capital=initial_capital
                        )
trading_manager = TradingManagerMain(data_generator=data_generator,
                                     strategy=strategy,
                                     trading_client=trading_client,
                                     key=ALPACA_KEY,
                                     secret_key=ALPACA_SECRET_KEY
                                     )

ws = websocket.WebSocketApp(url=SOCKET_URL, 
                            on_open=trading_manager.on_open,
                            on_message=trading_manager.on_message,
                            on_close=trading_manager.on_close,
                            on_error=trading_manager.on_error,
                            on_ping=trading_manager.on_ping,
                            on_pong=trading_manager.on_pong
                            )

#FONTOS!
# TRADING DAY-T UPDATELNI KELL (NAPONTA, NYILVÁN)

if __name__ == "__main__":
    try:
        ws.run_forever(reconnect=True, ping_interval=30, ping_timeout=10)
    except Exception as e:
        print(e)
        print("WebSocket connection closed.")
        ws.close()