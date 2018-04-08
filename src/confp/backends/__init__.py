from __future__ import print_function
import logging

from abc import ABCMeta, abstractmethod

from .. import exceptions


try:
    # Python 2
    from urlparse import urlparse
except ImportError:
    # Python 3
    from urllib.parse import urlparse


LOG = logging.getLogger(__name__)


def install_missing_requirements(module):
    """
    Some of the modules require external packages to be installed. This gets
    the list from the `REQUIREMENTS` module attribute and attempts to
    install the requirements using pip.
    :param module: Backend module
    :type module: ModuleType
    :return: None
    :rtype: NoneType
    """
    reqs = getattr(module, "REQUIREMENTS", [])
    if not reqs:
        print("Module %r has no extra requirements to install." % module)
        return
    import pkg_resources
    pkgs_installed = pkg_resources.WorkingSet()
    pkgs_required = []
    for req in reqs:
        if req.startswith("git+"):
            url = urlparse(req)
            params = {x[0]: x[1] for x in map(
                lambda y: y.split('='), url.fragment.split('&'))}
            try:
                pkg = params["egg"]
            except KeyError:
                raise exceptions.CannotInstallModuleRequirements(
                    "Package %r in module %r must include '#egg=<pkgname>'" % (
                        req, module))
        else:
            pkg = req
        if pkgs_installed.find(pkg_resources.Requirement.parse(pkg)) is None:
            pkgs_required.append(req)
    if pkgs_required:
        from pip.commands.install import InstallCommand
        from pip.status_codes import SUCCESS
        cmd = InstallCommand()
        result = cmd.main(pkgs_required)
        if result != SUCCESS:
            raise exceptions.CannotInstallModuleRequirements(
                "Unable to install packages for module %r (%s)..." % (
                    module, pkgs_required))


class BackendBase(object):
    __metaclass__ = ABCMeta

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
            'Key %r not found in backend %r. Falling back to default value.',
            key, self.name)
        return default
