from __future__ import print_function

from abc import ABCMeta, abstractmethod

from ..exceptions import CannotInstallModuleRequirements


try:
    # Python 2
    from urlparse import urlparse
except ImportError:
    # Python 3
    from urllib.parse import urlparse


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
                raise CannotInstallModuleRequirements(
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
            raise CannotInstallModuleRequirements(
                "Unable to install packages for module %r (%s)..." % (
                    module, pkgs_required))


class BackendBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, config):
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
