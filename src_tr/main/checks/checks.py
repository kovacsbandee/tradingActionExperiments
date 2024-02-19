from datetime import datetime, timedelta

def check_trading_day(trading_day: datetime) -> datetime:
    if trading_day.strftime('%A') == 'Sunday' or trading_day.strftime('%A') == 'Saturday':
        raise ValueError(f"Trading day is {trading_day}. Choose a weekday.")
    else:
        return trading_day
