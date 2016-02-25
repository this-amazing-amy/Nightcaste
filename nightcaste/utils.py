import importlib
import json


def class_for_name(module_name, class_name):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def load_config(config_path):
    config_file = open(config_path)
    try:
        return json.load(config_file)
    finally:
        config_file.close()
