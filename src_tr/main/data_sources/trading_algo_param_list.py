param_list = [
    {
        "scanner_params" : {
            "windows" : {
                "short" : 12,
                "long" : 26,
                "signal" : 9
            }
        },
        "algo_params" : {
            "entry_signal" : "default",
            "entry_rsi" : {
                "overbought" : 70,
                "oversold" : 30
            },
            "entry_windows" : {
                "short" : 5,
                "long" : 12,
                "epsilon" : 0.0015
            },
            "entry_weighted" : True,
            "close_signal" : "AVG",
            "close_rsi" : {
                "overbought" : 70,
                "oversold" : 30
            },
            "close_window" : 5,
            "close_weighted" : True
        }
    },
    {
        "scanner_params" : {
            "windows" : {
                "short" : 12,
                "long" : 26,
                "signal" : 9
            }
        },
        "algo_params" : {
            "entry_signal" : "MACD",
            "entry_rsi" : None,
            "entry_windows" : {
                "short" : 12,
                "long" : 26,
                "signal" : 9
            },
            "entry_weighted" : True,
            "close_signal" : "ATR",
            "close_rsi" : None,
            "close_window" : 5,
            "close_weighted" : True 
        }
    }
]