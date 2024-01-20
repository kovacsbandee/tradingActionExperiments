from .TestTradingClient import TestTradingClient

class TestTradingClientDivided(TestTradingClient):
    
    def initialize_positions(self):
        for e in self.symbol_list:
            self.positions[e['symbol']] = {
                'quantity' : 0,
                'side' : 'out',
                'symbol_free_cash' : self.total_free_cash / len(self.symbol_list)
            }
        
    def get_max_cash_by_symbol(self, symbol: str):
        return self.positions[symbol]['symbol_free_cash']
    
    def submit_order(self, symbol: str, qty: int, price: float):
        qty = qty if qty * price <= self.positions[symbol]['symbol_free_cash'] else self.positions[symbol]['symbol_free_cash'] / price
        long_amount = qty * price
        self.positions[symbol]['symbol_free_cash'] -= long_amount
        self.positions[symbol]['quantity'] = qty
        self.positions[symbol]['side' ] = 'long'
        self.total_free_cash -= long_amount
        print(f"Buy order completed. \nSymbol:{symbol} \nPrice at buy:{price} \nAmount bought:{qty} \nInvestment: ${long_amount}"
              f"\nTotal cash: ${self.total_free_cash}")
    
    def close_position(self, symbol: str, price: float):
        sell_amount = self.positions[symbol]['quantity'] * price
        self.positions[symbol]['symbol_free_cash'] += sell_amount
        self.positions[symbol]['quantity'] = 0
        self.positions[symbol]['side' ] = 'out'
        self.total_free_cash += sell_amount
        print(f"Position closed. \nSymbol:{symbol} \nPrice at sell:{price} \nCurrent cash for symbol: ${self.positions[symbol]['symbol_free_cash']}"
              f"\nTotal cash: ${self.total_free_cash}")