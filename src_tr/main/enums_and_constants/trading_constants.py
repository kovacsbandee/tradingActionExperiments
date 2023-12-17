# generic constants
SYMBOL = 'symbol'

# sticker_dict constants
STICKER_DF = 'sticker_dataframe'
IND_PRICE = 'indicator_price'
PREV_DAY_DATA = 'prev_day_data'
PRICE_RANGE_PERC = 'price_range_perc'
AVG_VOLUME = 'avg_volume'
VOLUME_RANGE_RATIO = 'volume_range_ratio'
AVG_OPEN = 'avg_open'
STD_OPEN = 'std_open'
SCANNING_DAY = 'scanning_day'

# Bar data constants
OPEN = 'o'
CLOSE = 'c'

# sticker_df column name constants:
POSITION = 'position'
TRADING_ACTION = 'trading_action'
CURRENT_CAPITAL = 'current_capital'
STOP_LOSS_OUT_SIGNAL = 'stop_loss_out_signal'
OPEN_SMALL_IND_COL = 'open_small_indicator'
OPEN_BIG_IND_COL = 'open_big_indicator'
OPEN_NORM = 'open_norm'
RSI = 'rsi'
GAIN = 'gain'
LOSS = 'loss'
GAIN_LOSS = 'gain_loss'
AVG_GAIN = 'avg_gain'
AVG_LOSS = 'avg_loss'
AMOUNT_SOLD = 'amount_sold'
AMOUNT_BOUGHT = 'amount_bought'

# sticker_df column value constants:
POS_OUT = 'out'
# itt javaslom, hogy a 'buy' és 'sell' szó lekerüljön innen, mert megtévesztő a pozíció leírása esetlében, hogy action is társul hozzá
POS_LONG_BUY = 'long'
POS_SHORT_SELL = 'short'

ACT_NO_ACTION = 'no_action'
ACT_BUY_NEXT_LONG = 'buy_next_long_position'
ACT_BUY_PREV_SHORT = 'buy_previous_short_position'
ACT_SELL_PREV_LONG = 'sell_previous_long_position'
ACT_SELL_NEXT_SHORT = 'sell_next_short_position'

STOP_LOSS_NONE = 'no_stop_loss_out_signal'
STOP_LOSS_LONG = 'stop_loss_long'
STOP_LOSS_SHORT = 'stop_loss_short'

# sticker position index constants:
PREV_LONG_BUY_POSITION_INDEX = 'previous_long_buy_position_index'
PREV_SHORT_SELL_POSITION_INDEX = 'previous_short_sell_position_index'