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
    sticker_data: dict = dict()
    """
    sticker_data = {
        "trading_day" : ...,
        "stickers" : {
                "AAPL" : {
                    "trading_day_data"* : DataFrame,
                    "trading_day_sticker_stats"** : DataFrame
                    },
                "MSFT" : {},
        }
    }

    *trading_day_data:
                                open     high      low    close  adj close  volume                                                                       
    2023-09-11 09:30:00-04:00  10.760  11.0000  10.7600  10.9999    10.9999  204654
    2023-09-11 09:31:00-04:00  10.960  11.4500  10.9580  11.2500    11.2500   75499
    2023-09-11 09:32:00-04:00  11.240  11.2501  10.9400  11.0800    11.0800   52771
    2023-09-11 09:33:00-04:00  11.090  11.1100  11.0201  11.0300    11.0300   25000
    2023-09-11 09:34:00-04:00  11.030  11.0539  10.9674  10.9900    10.9900   41203

    **trading_day_sticker_stats:
    """
    sticker_df: dict = dict()
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
    
    def __init__(self,
                 recommended_sticker_list):
        self.recommended_sticker_list = recommended_sticker_list
        
    #@abstractmethod
    #def load_individual_sticker_data(self):
    #    pass
    
    @abstractmethod
    def load_watchlist_daily_price_data(self):
        pass

    @abstractmethod
    def update_sticker_df():
        pass