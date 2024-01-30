# Installation

## Requirements
- Python 3.11+

## Create & activate Python venv

On Unix systems:

```sh
python -m venv YOUR_ARBITRARY_VENV_DIR/trading_venv
source YOUR_ARBITRARY_VENV_DIR/trading_venv/bin/activate
```

Change directory to the project's root folder, then:

```sh
pip install -r requirements.txt
pip install -U polygon-api-client
```

## Set .env file

```sh
nano .env
```

Set the required environment variables, credentials in the .env file

## Create resources folder

mkdir ./src_tr/main/resources

## Create database folder

First, create your database folder (arbitrary path / folder name)
Change directory to this database folder, then:
```sh
mkdir scanner_stats
```

## Set project root's config.py properly

# Running

On Unix systems:

```sh
source YOUR_ARBITRARY_VENV_DIR/trading_venv/bin/activate
set -a # if you used unix environment variables in your .env file
source .env # if you used unix environment variables in your .env file
python src_tr/test/test_workflow_modules/test_main.py
```

# TODO:

1.) TradingManagerMain.py -> 93. sor
2.) Scanner-logika
  - tőzsdék szerint csoportosítani/szinkronizálni (melyik részvény melyiken érhető el)
  - pl. 2023-12-06 három vagy két részvénnyel, mindkét fajta stoplossal (mindenképp veszteséges, de különbözőképp)
