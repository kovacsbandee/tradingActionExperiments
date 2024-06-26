import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()

ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]

# paper=True enables paper trading
trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)

account = trading_client.get_account()
#position = trading_client.get_all_positions()
#trading_client.close_position('AAPL')
print(account.cash)
#print(position)

# preparing orders
market_order_data = MarketOrderRequest(
                   symbol="AAPL",
                   qty=200,
                   side=OrderSide.BUY,
                   time_in_force=TimeInForce.DAY
                   )

stop_order_data = StopOrderRequest(
                    symbol="AAPL",
                    qty=200,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                    stop_price=193.0
                    )

# Market order
market_order = trading_client.submit_order(
                order_data=stop_order_data
               )

print(market_order)