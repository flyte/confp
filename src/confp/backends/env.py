import logging
from os import environ as env

from . import BackendBase
from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException


LOG = logging.getLogger(__name__)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update({
    'prefix': dict(type='string', default='')
})


def get_vars(prefix):
    return {key[len(prefix):]: value for key, value in env.items()
            if key.startswith(prefix)}


class Backend(BackendBase):
    def connect(self):
        return True

    def disconnect(self):
        return True

    def get_val(self, key):
        key = '%s%s' % (self.config.get('prefix', ''), key)
        LOG.debug('Getting value of key %r from environment', key)
        try:
            return env[key]
        except KeyError:
            raise KeyNotFoundException(
                'No environment variable exists with key %r.' % key)

    def get_all(self):
        prefix = self.config.get('prefix', '')
        LOG.debug('Geting all values with prefix %r from environment', prefix)
        return get_vars(prefix)
