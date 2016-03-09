import importlib
import json


def class_for_name(module_name, class_name):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def load_config(config_path):
    with open(config_path) as config_file:
        return json.load(config_file)
