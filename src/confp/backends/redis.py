from __future__ import absolute_import

import logging

from . import BackendBase
from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException


LOG = logging.getLogger(__name__)

REQUIREMENTS = (
    'redis',
)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update({
    'host': dict(type='string', required=True, empty=False),
    'port': dict(type='integer', default=6379, min=1, max=65535),
    'db': dict(type='integer', default=0, min=0, max=15),
    'password': dict(type='string', empty=False),
    'decode_responses': dict(type='boolean', default=True)
})


class Backend(BackendBase):
    def connect(self):
        from redis import StrictRedis
        self.db = StrictRedis(
            host=self.config['host'],
            port=self.config['port'],
            db=self.config['db'],
            password=self.config.get('password'),
            decode_responses=self.config['decode_responses']
        )

    def disconnect(self):
        LOG.debug('Disconnecting from Redis server')

    def get_val(self, key):
        LOG.debug(
            'Getting value of key %r from redis server at %s:%s',
            key, self.config['host'], self.config['port'])
        var = self.db.get(key)
        if var is None:
            raise KeyNotFoundException('Key %r was not found in Redis.' % key)
        return var
