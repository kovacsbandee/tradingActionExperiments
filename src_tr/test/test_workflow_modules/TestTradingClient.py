from typing import List

from src_tr.main.enums_and_constants.trading_constants import POS_OUT, POS_LONG_BUY

class TestTradingClient():
    
    def __init__(self, init_cash, sticker_list) -> None:
        self.cash: int = init_cash
        self.positions: dict = {}
        self.sticker_list: List[dict] = sticker_list
    
    """
        self.positions = {
            symbol: {
                qty: 33.32,
                side: 'long'
            }
        }
    """
    
    def initialize_positions(self):
        '''
        Initializes the position dictionary, with quantity 0, and side out.
        '''
        for e in self.sticker_list:
            self.positions[e['symbol']] = {
                'qty': 0,
                'side': POS_OUT
            }
    
    def get_position_by_symbol(self, symbol: str):
        '''
        Returns the latest side for each symbol.
        '''
        return self.positions[symbol]['side']
    
    def submit_order(self, symbol: str, qty: int, price: float):
        '''
        Emulates submitting the order to the trading client.
        '''
        long_amount = qty * price
        self.cash -= long_amount
        self.positions[symbol] = {
            'qty': qty,
            'side': POS_LONG_BUY
        }
        print(f"Buy order completed. \nSymbol:{symbol} \nPrice at buy:{price} \nAmount bought:{qty} \nCurrent cash: {self.cash}")
    
    def close_position(self, symbol: str, price: float):
        '''
        Emualtes closing the position for a symbol.
        '''
        sell_amount = self.positions[symbol]['qty'] * price
        self.cash += sell_amount
        self.positions[symbol]['qty'] = 0
        self.positions[symbol]['side'] = POS_OUT
        print(f"Position closed. \nSymbol:{symbol} \nPrice at sell:{price} \nCurrent cash: {self.cash}")
