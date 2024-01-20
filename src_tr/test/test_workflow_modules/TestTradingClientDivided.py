from src_tr.main.enums_and_constants.trading_constants import POS_OUT, POS_LONG, SYMBOL_FREE_CASH, QTY, SIDE
from .TestTradingClient import TestTradingClient

class TestTradingClientDivided(TestTradingClient):
    
    def initialize_positions(self):
        for e in self.symbol_list:
            self.positions[e['symbol']] = {
                QTY : 0,
                SIDE : POS_OUT,
                SYMBOL_FREE_CASH : self.total_free_cash / len(self.symbol_list)
            }
        
    def get_max_cash_by_symbol(self, symbol: str):
        return self.positions[symbol][SYMBOL_FREE_CASH]
    
    def submit_order(self, symbol: str, qty: int, price: float):
        qty = qty if qty * price <= self.positions[symbol][SYMBOL_FREE_CASH] else self.positions[symbol][SYMBOL_FREE_CASH] / price
        long_amount = qty * price
        self.positions[symbol][SYMBOL_FREE_CASH] -= long_amount
        self.positions[symbol][QTY] = qty
        self.positions[symbol][SIDE ] = POS_LONG
        self.total_free_cash -= long_amount
        print(f"Buy order completed. \nSymbol:{symbol} \nPrice at buy:{price} \nAmount bought:{qty} \nInvestment: ${long_amount}"
              f"\nTotal cash: ${self.total_free_cash}")
    
    def close_position(self, symbol: str, price: float):
        sell_amount = self.positions[symbol][QTY] * price
        self.positions[symbol][SYMBOL_FREE_CASH] += sell_amount
        self.positions[symbol][QTY] = 0
        self.positions[symbol][SIDE ] = POS_OUT
        self.total_free_cash += sell_amount
        print(f"Position closed. \nSymbol:{symbol} \nPrice at sell:{price} \nCurrent cash for symbol: ${self.positions[symbol][SYMBOL_FREE_CASH]}"
              f"\nTotal cash: ${self.total_free_cash}")