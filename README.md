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

## Set project configs/config-default.json properly

Based on the config-default-example.json template

# Running

On Unix systems:

```sh
source YOUR_ARBITRARY_VENV_DIR/trading_venv/bin/activate
set -a # if you used unix environment variables in your .env file
source .env # if you used unix environment variables in your .env file
python src_tr/test/test_workflow_modules/test_main.py
```

