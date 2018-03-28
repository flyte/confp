from os import environ
from contextlib import contextmanager

import pytest

from confp.backends import env
from confp.exceptions import KeyNotFoundException


@pytest.fixture
def backend():
    """
    Create a minimally configured backend instance.
    """
    config = dict(
        type='env',
        prefix=''
    )
    return env.Backend(config)


@contextmanager
def env_var(key, value):
    """
    Set an env var and clean up afterwards.
    """
    environ[key] = value
    try:
        yield
    finally:
        del environ[key]


def test_connect(backend):
    """
    These functions should just return True on this backend.
    """
    assert backend.connect()


def test_disconnect(backend):
    """
    These functions should just return True on this backend.
    """
    assert backend.disconnect()


def test_get_val(backend):
    """
    Should return the environment variable we set.
    """
    key = 'test_get_val'
    test_val = 'this is a test'
    with env_var(key, test_val):
        assert backend.get_val(key) == test_val


def test_get_missing_val(backend):
    """
    Should raise a KeyNotFoundException if the env var doesn't exist.
    """
    key = 'test_get_missing_val'
    assert key not in environ
    with pytest.raises(KeyNotFoundException):
        backend.get_val(key)
