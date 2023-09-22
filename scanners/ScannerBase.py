from typing import List
from datetime import datetime
from abc import ABC, abstractmethod

class ScannerBase(ABC):
    
    project_path: str
    name: str
    trading_day: datetime
    scanning_day: datetime
    stickers: List[str]
    lower_price_boundary: float
    upper_price_boundary: float
    price_range_perc_cond: int
    avg_volume_cond: int
    pre_market_stats: List
    recommended_stickers: List

    def __init__(self, project_path, name, trading_day, scanning_day, stickers, lower_price_boundary,
                 upper_price_boundary, price_range_perc_cond, avg_volume_cond):
        self.project_path = project_path
        self.name = name
        self.trading_day = trading_day
        self.scanning_day = scanning_day # TODO: lehet, hogy származtatni kéne? egyszerűbb lenne...
        self.stickers = stickers
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.price_range_perc_cond = price_range_perc_cond
        self.avg_volume_cond = avg_volume_cond
        
    @abstractmethod
    def get_pre_market_stats(self, sticker: str)  -> dict:
        pass
    
    @abstractmethod
    def get_filtering_stats(self, save_csv: bool = False) -> List:
        pass
    
    @abstractmethod
    def recommend_premarket_watchlist(self) -> List:
        pass