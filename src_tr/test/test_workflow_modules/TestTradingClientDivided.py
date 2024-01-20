from src_tr.main.enums_and_constants.trading_constants import POS_OUT, POS_LONG_BUY
from .TestTradingClient import TestTradingClient

class TestTradingClientDivided(TestTradingClient):
    
    def initialize_positions(self):
        for e in self.symbol_list:
            self.positions[e['symbol']] = {
                'qty': 0,
                'side': POS_OUT,
                'max_cash' : self.cash / len(self.symbol_list)
            }
        
    def get_max_cash_by_symbol(self, symbol: str):
        return self.positions[symbol]['max_cash']
    
    def submit_order(self, symbol: str, qty: int, price: float):
        qty = qty if qty * price <= self.positions[symbol]['max_cash'] else self.positions[symbol]['max_cash'] / price
        long_amount = qty * price
        self.positions[symbol]['max_cash'] -= long_amount
        self.positions[symbol]['qty'] = qty
        self.positions[symbol]['side'] = POS_LONG_BUY
        self.cash -= long_amount
        print(f"Buy order completed. \nSymbol:{symbol} \nPrice at buy:{price} \nAmount bought:{qty} \nInvestment: ${long_amount}"
              f"\nTotal cash: ${self.cash}")
    
    def close_position(self, symbol: str, price: float):
        sell_amount = self.positions[symbol]['qty'] * price
        self.positions[symbol]['max_cash'] += sell_amount
        self.positions[symbol]['qty'] = 0
        self.positions[symbol]['side'] = POS_OUT
        self.cash += sell_amount
        print(f"Position closed. \nSymbol:{symbol} \nPrice at sell:{price} \nCurrent cash for symbol: ${self.positions[symbol]['max_cash']}"
              f"\nTotal cash: ${self.cash}")