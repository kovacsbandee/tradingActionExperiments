import argparse, json, os

parser = argparse.ArgumentParser("python trading_project_module_with_path.py")
parser.add_argument("--config", help="A config file with path")
args = parser.parse_args()
filename = "configs/config-default.json" if (args.config is None or args.config == "") else args.config
filename_full_path = os.path.join(os.path.dirname(__file__), filename)
print(f"Loading config file: {filename_full_path}")
if not os.path.isfile(filename_full_path):
    raise Exception("Config file not found")

f = open(filename_full_path)
config = json.load(f)
print(f"Config JSON loaded successfully: {config}")
