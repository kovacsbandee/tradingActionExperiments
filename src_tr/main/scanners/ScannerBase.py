from typing import List
from datetime import datetime
from abc import ABC, abstractmethod

class ScannerBase(ABC):
    
    #project_path: str
    name: str
    trading_day: datetime 
    scanning_day: datetime # nem kell, származtatjuk
    stickers: List[str]
    pre_market_stats: List
    recommended_stickers: List

    def __init__(self, 
                 #project_path, 
                 name, 
                 trading_day, 
                 scanning_day, 
                 stickers):
        #self.project_path = project_path
        self.name = name
        self.trading_day = trading_day
        self.scanning_day = scanning_day # TODO: lehet, hogy származtatni kéne? egyszerűbb lenne...
        self.stickers = stickers
        
    @abstractmethod
    def get_pre_market_stats(self, sticker: str)  -> dict:
        pass
    
    @abstractmethod
    def calculate_filtering_stats(self, save_csv: bool = False) -> List:
        pass
    
    @abstractmethod
    def recommend_premarket_watchlist(self) -> List:
        pass