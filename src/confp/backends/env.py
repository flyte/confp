import logging
import os

from . import BackendBase
from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException


LOG = logging.getLogger(__name__)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update({
    'prefix': dict(type='string', default='')
})


def get_vars(prefix):
    return {key[len(prefix):]: value for key, value in os.environ.items()
            if key.startswith(prefix)}


class Backend(BackendBase):
    def connect(self):
        return True

    def disconnect(self):
        return True

    def get_val(self, key):
        LOG.debug('Getting value of key %r from environment', key)
        key = '%s%s' % (self.config.get('prefix', ''), key)
        try:
            return os.environ[key]
        except KeyError:
            raise KeyNotFoundException(
                'No environment variable exists with key %r.' % key)
