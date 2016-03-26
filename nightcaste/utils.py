import importlib
import json


def class_for_name(module_name, class_name):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def get_class(class_specification):
    spec = class_specification.rsplit('.', 1)
    return class_for_name(spec[0], spec[1])


def load_config(config_path):
    with open(config_path) as config_file:
        return json.load(config_file)
