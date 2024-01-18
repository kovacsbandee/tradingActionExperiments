from datetime import datetime, timedelta

def check_trading_day(trading_day: datetime) -> datetime:
    '''
    Checks if the trading day is a weekday, returns value error if trading_day is weekend,
    else trading_day.
    '''
    #trading_day = datetime.strptime(trading_day, '%Y-%m-%d')
    if trading_day.strftime('%A') == 'Sunday' or trading_day.strftime('%A') == 'Saturday':
        # de amúgy a pd.bdate_range csak munkanapot ad vissza, szóval redundáns is
        raise ValueError(f'Trading day is {trading_day}. Choose a weekday.')
    else:
        return trading_day
