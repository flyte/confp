from __future__ import absolute_import

import logging

from . import BackendBase
from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException


LOG = logging.getLogger(__name__)

REQUIREMENTS = (
    'python-etcd',
)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update({
    'host': dict(type='string', required=True, empty=False),
    'port': dict(type='integer', default=2379, min=1, max=65535),
    'protocol': dict(type='string', default='https', empty=False)
})


class Backend(BackendBase):
    def connect(self):
        import etcd
        self.etcd = etcd
        self.db = etcd.Client(
            host=self.config['host'],
            port=self.config['port'],
            protocol=self.config['protocol']
        )

    def disconnect(self):
        LOG.debug('Disconnecting from etcd server')

    def get_val(self, key):
        LOG.debug(
            'Getting value of key %r from etcd server at %s:%s',
            key, self.config['host'], self.config['port'])
        try:
            val = self.db.get(key).value
        except self.etcd.EtcdKeyNotFound:
            raise KeyNotFoundException('Key %r was not found in etcd.' % key)
        return val
