from abc import ABC, abstractmethod
from datetime import datetime
import websocket

from src.main.scanners.ScannerBase import ScannerBase
from src.main.data_generators.PriceDataGeneratorBase import PriceDataGeneratorBase
from src.main.strategies.StrategyBase import StrategyBase
from src.main.data_streams.DataStreamBase import DataStreamBase
from src.main.trading_clients.TradingClientBase import TradingClientBase

class TradingManagerBase(ABC):

    scanner: ScannerBase
    price_data_generator: PriceDataGeneratorBase
    strategy: StrategyBase
    data_stream: DataStreamBase
    trading_client: TradingClientBase
    ws: websocket.WebSocketApp
    key: str
    secret_key: str
    socket_url: str
    market_open: datetime
    market_close: datetime

    def __init__(self, 
                 scanner, 
                 price_data_generator, 
                 strategy, data_stream, 
                 trading_client, 
                 key, 
                 secret_key, 
                 socket_url,
                 market_open,
                 market_close):
        self.scanner = scanner
        self.price_data_generator = price_data_generator
        self.strategy = strategy
        self.data_stream = data_stream
        self.trading_client = trading_client
        self.key = key
        self.secret_key = secret_key
        self.socket_url = socket_url
        self.market_open = market_open
        self.market_close = market_close
        self.ws = websocket.WebSocketApp(self.socket_url, 
                                         on_open=self.on_open, 
                                         on_message=self.handle_message, 
                                         on_close=self.on_close)

    @abstractmethod
    def handle_message(self):
        pass

    @abstractmethod
    def _process_data(self):
        pass

    @abstractmethod
    def wait_for_data(self):
        pass

    @abstractmethod
    def on_open(self):
        pass

    @abstractmethod
    def on_close(self):
        pass

    @abstractmethod
    def apply_strategy(self):
        pass

    @abstractmethod
    def execute_trading_action(self):
        pass