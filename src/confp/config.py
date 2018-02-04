import yaml
from cerberus import Validator

from .exceptions import ConfigValidationException


BASE_MODULE_SCHEMA = {
    'type': dict(type='string', required=True, empty=False)
}

CONFIG_SCHEMA = {
    'backends': dict(
        type='dict',
        required=True,
        keyschema=dict(type='string', regex='[a-zA-z][a-zA-Z0-9_]*'),
        valueschema=dict(
            type='dict', allow_unknown=True, schema=BASE_MODULE_SCHEMA)
    ),
    'templates': dict(
        type='list',
        schema={
            'src': dict(type='string', required=True, empty=False),
            'dest': dict(type='string', required=True, empty=False),
            'owner': dict(type='string', required=True, empty=False),
            'mode': dict(type='string', empty=False, default='0644'),
            'check_cmd': dict(type='string', empty=False),
            'restart_cmd': dict(type='string', empty=False),
            'vars': dict(
                type='dict',
                keyschema=dict(type='string', regex='[a-zA-z][a-zA-Z0-9_]*'),
                valueschema=dict(type='dict', schema={
                    'backend': dict(type='string', required=True, empty=False),
                    'key': dict(type='string', required=True, empty=False)
                })
            )
        }
    ),
    'logging': dict(type='dict', allow_unknown=True, schema={})
}


def load_config(path):
    validator = Validator(CONFIG_SCHEMA)
    with open(path) as f:
        config = yaml.load(f)
    if not validator.validate(config):
        raise ConfigValidationException(validator.errors)
    return validator.document


def validate_module_config(schema, config):
    validator = Validator(schema)
    if not validator.validate(config):
        raise ConfigValidationException(validator.errors)
    return validator.document
