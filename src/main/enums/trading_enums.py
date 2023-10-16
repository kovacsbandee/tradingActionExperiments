from enum import Enum

class TradingActionEnum(Enum):
    BUY_LONG = 'buy_long'
    BUY_SHORT = 'buy_short'
    SELL_LONG = 'sell_long'
    SELL_SHORT = 'sell_short'
    BUY_SHORT_SELL_LONG = 'buy_short_sell_long'
    SELL_LONG_BUY_SHORT = 'sell_long_buy_short'