class KeyNotFoundException(Exception):
    pass


class ConfigValidationException(Exception):
    pass


class CannotInstallModuleRequirements(Exception):
    pass


class NoBackendSupport(Exception):
    pass
