from typing import List

class TestTradingClient():
    
    def __init__(self, init_cash, symbol_list, mode):
        self.total_free_cash: int = init_cash
        self.symbol_list: List[dict] = symbol_list
        self.mode = mode
        self.positions: dict = {}

    """
        self.positions = {
            symbol: {
                qty: 33.32,
                side: 'long'
            }
        }
    """
    
    def initialize_positions(self):
        for e in self.symbol_list:
            self.positions[e['symbol']] = {
                'quantity': 0,
                'side': 'out'
            }
    
    def get_position_by_symbol(self, symbol: str):
        return self.positions[symbol]['side']
    
    def submit_order(self, symbol: str, qty: int, price: float):
        long_amount = qty * price
        self.total_free_cash -= long_amount
        self.positions[symbol] = {
            'quantity': qty,
            'side': 'long'
        }
        print(f"Buy order completed. \nSymbol:{symbol} \nPrice at buy:{price} \nAmount bought:{qty} \nCurrent cash: {self.total_free_cash}")
    
    def close_position(self, symbol: str, price: float):
        sell_amount = self.positions[symbol]['quantity'] * price
        self.total_free_cash += sell_amount
        self.positions[symbol]['quantity'] = 0
        self.positions[symbol]['side'] = 'out'
        print(f"Position closed. \nSymbol:{symbol} \nPrice at sell:{price} \nCurrent cash: {self.total_free_cash}")
