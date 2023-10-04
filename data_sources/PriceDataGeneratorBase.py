from typing import List
from datetime import datetime
from abc import ABC, abstractmethod
from pandas import DataFrame
from alpaca.data.historical import StockHistoricalDataClient

class PriceDataGeneratorBase(ABC):
    
    trading_day: datetime
    recommended_sticker_list: List[str]
    lower_price_boundary: int
    upper_price_boundary: int
    lower_volume_boundary: int
    prev_day_data: DataFrame
    prev_day_sticker_stats: dict
    trading_day_sticker_stats: dict
    """
    trading_day_sticker_stats = {
        'avg_close': ...,
        'avg_volume': ...,
        'price_range_perc': ...,
        'volume_range_ratio': ... 
    }
    """
    sticker_dict: dict = dict()
    """
    sticker_data = {
        "trading_day" : ...,
        "stickers" : {
                "AAPL" : {
                    "trading_day_data" : ...,
                    "trading_day_sticker_stats" : ...,
                    "prev_day_data" : ...,
                    "prev_day_stats" : ...,
                    },
                "MSFT" : {},
        }
    }
    """
    current_data_window: dict = dict()
    """
    NOTE: the current_data_window is a dictionary of dataframes, 
    where the key is the sticker symbol
    current_data_window = {
        'AAPL': [{"T":"b",
                "S":"AAPL",
                "o":171.68,
                "h":171.68,
                "l":171.585,
                "c":171.605,
                "v":1961,
                "t":"2023-10-03T18:16:00Z",
                "n":22,
                "vw":171.618957}],
        'MSFT': [],
        'TSLA': []
    }
    """
    data_window_size: int
    historical_data_client: StockHistoricalDataClient
    
    def __init__(self, trading_day, recommended_sticker_list, lower_price_boundary, 
                 upper_price_boundary, lower_volume_boundary, data_window_size,
                 historical_data_client):
        self.trading_day = trading_day
        self.recommended_sticker_list = recommended_sticker_list
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.lower_volume_boundary = lower_volume_boundary
        self.data_window_size = data_window_size
        self.historical_data_client = historical_data_client
        
    @abstractmethod
    def load_individual_sticker_data(self):
        pass
    
    @abstractmethod
    def load_watchlist_daily_price_data(self):
        pass