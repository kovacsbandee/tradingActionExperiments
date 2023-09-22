from datetime import datetime, timedelta

# TODO:
def save_experiment_data():
    '''
    This method saves the experiment_data dictionary into the data_store.
    :return: nothing
    '''
    pass

# TODO:
def load_experiment_data():
    '''
    This one loads the previous file!
    :return: experiment_data
    '''
    pass

def calculate_scanning_day(trading_day: datetime) -> datetime:
    if (trading_day - timedelta(days=1)).strftime('%A') == 'Sunday':
        return trading_day - timedelta(days=3)
    else:
        return trading_day - timedelta(days=1)