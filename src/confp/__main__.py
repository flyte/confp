from __future__ import print_function

import logging
import sys
from argparse import ArgumentParser
from functools import partial
from importlib import import_module
from logging.config import dictConfig
from subprocess import CalledProcessError, check_call
from time import sleep

import jinja2

from .filters import FILTERS
from .backends import install_missing_requirements
from .config import load_config, validate_module_config
from .exceptions import KeyNotFoundException, NoBackendSupport

BACKENDS = {}
LOG = logging.getLogger(__name__)


def get_logger(config):
    """
    Instantiate logger with provided config.
    """
    dictConfig(config)
    log = logging.getLogger("confp.%s" % __name__)
    log.info("Logger configured with settings from config file.")
    return log


def instantiate_backend(name, config):
    """
    Import the backend module and instantiate it with the provided config.
    """
    LOG.debug("Instantiating backend %r", name)
    backend_module = import_module("confp.backends.%s" % config["type"])
    config = validate_module_config(backend_module.CONFIG_SCHEMA, config)
    install_missing_requirements(backend_module)
    backend = backend_module.Backend(name, config)
    backend.connect()
    return backend


def get_backend_value(backend, key, default=None):
    """
    Get a value from the backend, optionally specifying a default in case the
    key doesn't exist.
    """
    if default is None:
        return backend.get_val(key)
    else:
        return backend.get_val_default(key, default)


def render_template(env, config, template_string=None):
    """
    Evaluate the template by getting all of the relevant values and rendering
    the template to the configured destination.
    """
    # Get any values which have been set in 'vars'
    LOG.debug("Fetching values for template global vars")
    context = {}
    for key, var_config in config.get("vars", {}).items():
        try:
            context[key] = BACKENDS[var_config["backend"]].get_val(var_config["key"])
        except KeyNotFoundException as exc:
            # Use default if one's set, else raise
            try:
                context[key] = var_config["default"]
            except KeyError:
                raise exc

    # Get dict containing all backend vars if supported
    for name, backend in BACKENDS.items():
        try:
            context["%s__all" % name] = backend.get_all()
        except NoBackendSupport:
            pass

    # Read the template if not provided
    if template_string is None:
        with open(config["src"]) as f:
            template = env.from_string(f.read())
    else:
        template = env.from_string(template_string)

    # Render the template
    LOG.debug("Rendering the template")
    return template.render(context)


def write_template_dest(rendered, config):
    # Read the existing config file, if it exists
    # @TODO: Optionally create the config in a temp file first and move it
    #        into place if the test is successful.
    try:
        with open(config["dest"]) as f:
            existing = f.read()
    except (OSError, IOError):
        # It probably didn't exist, so we'll try creating/replacing it anyway
        LOG.warning(
            "Unable to read dest file at %r. Will attempt to create it.", config["dest"]
        )
        existing = None

    # Compare our rendered template with the existing config file
    if existing == rendered:
        # Nothing changed
        LOG.info("File at %r does not need updating.", config["dest"])
        return

    # Replace the config with our newly rendered one
    with open(config["dest"], "w") as f:
        f.write(rendered)
    LOG.warning("Updated the file at %r.", config["dest"])

    # Run the check command if configured
    try:
        check_cmd = jinja2.Template(config["check_cmd"]).render(**config)
        check_call(check_cmd, shell=True)
    except KeyError:
        LOG.debug("check_cmd not set for this template, so skipping the check.")
    except CalledProcessError:
        LOG.debug("Check on file %r failed, reverting to old version.", config["dest"])
        with open(config["dest"], "w") as f:
            f.write(existing)

    # Run the restart command if configured
    if "restart_cmd" in config:
        LOG.warning("Running restart command %r", config["restart_cmd"])
        check_call(config["restart_cmd"], shell=True)

    # @TODO: Set ownership and permissions


def main_default(config_path, loop=None):
    global LOG
    LOG = logging.getLogger(__name__)

    config = load_config(config_path)
    try:
        LOG = get_logger(config["logging"])
    except KeyError:
        LOG.info("No 'logging' section set in config. Using default settings.")

    # Configure the Jinja2 environment with functions for each of the backends
    env = create_env(config)

    exit = 0
    # Main loop
    try:
        while True:
            for templ_config in config["templates"]:
                LOG.debug("Evaluating template for %r", templ_config["dest"])
                try:
                    rendered = render_template(env, templ_config)
                    write_template_dest(rendered, templ_config)
                except Exception:
                    LOG.exception(
                        "Exception while evaluating template for dest %r.",
                        templ_config["dest"],
                    )
                    exit = 1
            if loop is None:
                break
            LOG.debug("Sleeping for %s second(s)...", loop)
            sleep(loop)
    except KeyboardInterrupt:
        LOG.critical("Quitting due to keyboard interrupt. Bye!")
    except Exception:
        LOG.exception("Exception in main function:")
        exit = 1
    finally:
        for backend in BACKENDS.values():
            backend.disconnect()
    return exit


def create_env(config):
    # Configure the Jinja2 environment with functions for each of the backends
    env = jinja2.Environment()
    for name, be_config in config["backends"].items():
        BACKENDS[name] = instantiate_backend(name, be_config)
        env.globals[name] = partial(get_backend_value, BACKENDS[name])
    env.filters.update(FILTERS)
    return env


def render(config_path: str, template: str):
    """
    Renders the template with the config loaded from config_path
    """
    config = load_config(config_path)
    env = create_env(config)
    return render_template(env, {}, template_string=template)


def main_query(config_path, template):
    rendered = render(config_path, template)
    print(rendered)
    return 0


def main():
    p = ArgumentParser()
    p.add_argument("config_path")
    p.add_argument("--loop", type=int, default=None)
    p.add_argument("--template", default="")
    args = p.parse_args()
    if args.template:
        return main_query(args.config_path, args.template)
    return main_default(args.config_path, args.loop)


if __name__ == "__main__":
    sys.exit(main())
