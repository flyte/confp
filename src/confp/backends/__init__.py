import logging
from abc import ABC, abstractmethod

from .. import exceptions

LOG = logging.getLogger(__name__)


class BackendBase(ABC):
    def __init__(self, name, config):
        self.name = name
        self.config = config

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def get_val(self, key):
        pass

    def get_all(self):
        raise exceptions.NoBackendSupport()

    def get_val_default(self, key, default):
        """
        Get a value from the backend, but fall back to the default value if
        the key doesn't exist.
        """
        try:
            return self.get_val(key)
        except exceptions.KeyNotFoundException:
            pass
        LOG.info(
            "Key %r not found in backend %r. Falling back to default value.",
            key,
            self.name,
        )
        return default
