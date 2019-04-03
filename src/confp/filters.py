from ast import literal_eval
import json


def filter_bool(val):
    return bool(literal_eval(val))


def filter_json(val, **kwargs):
    return json.dumps(val, **kwargs)


def filter_yaml(val, **kwargs):
    import yaml

    return yaml.dump(val, **kwargs)


FILTERS = dict(bool=filter_bool, json=filter_json, yaml=filter_yaml)
