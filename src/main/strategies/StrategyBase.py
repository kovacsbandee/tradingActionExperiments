from abc import ABC, abstractmethod
import pandas as pd

class StrategyBase(ABC):
    
    def __init__(self, 
                 sticker_data: dict, 
                 ma_short: int, 
                 ma_long: int):
        self.sticker_data = sticker_data
        self.ma_short = ma_short
        self.ma_long = ma_long

    def add_strategy_specific_indicators(self):
        averaged_cols = ["close", "volume"]
        for sticker in self.sticker_data['stickers'].keys():
            trading_day_data = self.sticker_data['stickers'][sticker]['trading_day_data']
            indicators = list()
            for col in averaged_cols:
                indicators.append(col)
                short_ind_col = f'{col}_ma{self.ma_short}'
                trading_day_data[short_ind_col] = self.add_rolling_average(price_time_series=trading_day_data, 
                                                                           col=col, window_length=self.ma_short)
                indicators.append(short_ind_col)
                trading_day_data[f'{short_ind_col}_grad'] = self.add_gradient(price_time_series=trading_day_data, 
                                                                              col=short_ind_col)
                indicators.append(f'{short_ind_col}_grad')
                '''
                sticker_df[f'{short_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df,
                                                                    col=f'{short_ind_col}_grad')
                indicators.append(f'{short_ind_col}_grad2')
                '''
                long_ind_col = f'{col}_ma{self.ma_long}'
                trading_day_data[long_ind_col] = self.add_rolling_average(price_time_series=trading_day_data, 
                                                                          col=col, window_length=self.ma_long)
                indicators.append(long_ind_col)
                trading_day_data[f'{long_ind_col}_grad'] = self.add_gradient(price_time_series=trading_day_data, 
                                                                             col=long_ind_col)
                indicators.append(f'{long_ind_col}_grad')
                '''
                sticker_df[f'{long_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df, col=f'{long_ind_col}')
                indicators.append(f'{long_ind_col}_grad2')
                '''

    def add_rolling_average(self, price_time_series: pd.DataFrame, col: str, window_length: int):
        return price_time_series[col].rolling(window_length, center=False).mean()

    def add_gradient(price_time_series: pd.DataFrame, col: str):
        return price_time_series[col].diff()
    
    @abstractmethod
    def apply_strategy():
        pass