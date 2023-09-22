from datetime import datetime, timedelta

def check_trading_day(trading_day: datetime) -> datetime:
    trading_day = datetime.strptime(trading_day, '%Y-%m-%d')
    if trading_day.strftime('%A') == 'Sunday' or trading_day.strftime('%A') == 'Saturday':
        # TODO: error helyet automatizálni kellene a trading day választását
        raise ValueError(f'Trading day is {trading_day}. Choose a weekday.')
    else:
        return trading_day