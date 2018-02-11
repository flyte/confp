from __future__ import print_function

import logging
from logging.config import dictConfig
from argparse import ArgumentParser
from importlib import import_module
from time import sleep
from subprocess import check_call, CalledProcessError

from .config import load_config, validate_module_config
from .backends import install_missing_requirements

import jinja2


BACKENDS = {}
LOG = logging.getLogger(__name__)


def configure_logging(config):
    global LOG
    dictConfig(config)
    LOG = logging.getLogger('confp.%s' % __name__)
    LOG.info('Logger configured with settings from config file.')


def configure_backend(name, config):
    backend_module = import_module('confp.backends.%s' % config['type'])
    config = validate_module_config(backend_module.CONFIG_SCHEMA, config)
    install_missing_requirements(backend_module)
    BACKENDS[name] = backend_module.Backend(config)
    BACKENDS[name].connect()


def evaluate_template(env, config):
    # Get any values which have been set in 'vars'
    LOG.debug('Fetching values for template global vars')
    context = {}
    for key, var_config in config.get('vars', {}).items():
        context[key] = BACKENDS[var_config['backend']].get_val(
            var_config['key'])

    # Read the template
    with open(config['src']) as f:
        template = env.from_string(f.read())

    # Render the template
    LOG.debug('Rendering the template')
    rendered = template.render(context)

    # Read the existing config file, if it exists
    # @TODO: Optionally create the config in a temp file first and move it
    #        into place if the test is successful.
    try:
        with open(config['dest']) as f:
            existing = f.read()
    except (OSError, IOError):
        # It probably didn't exist, so we'll try creating/replacing it anyway
        LOG.warning(
            'Unable to read dest file at %r. Will attempt to create it.',
            config['dest'])
        existing = None

    # Compare our rendered template with the existing config file
    if existing == rendered:
        # Nothing changed
        LOG.info('File at %r does not need updating.', config['dest'])
        return
    # Replace the config with our newly rendered one
    with open(config['dest'], 'w') as f:
        f.write(rendered)
    LOG.warning('Updated the file at %r.', config['dest'])

    try:
        check_cmd = jinja2.Template(config['check_cmd']).render(**config)
        check_call(check_cmd, shell=True)
    except KeyError:
        LOG.debug(
            'check_cmd not set for this template, so skipping the check.')
    except CalledProcessError:
        LOG.debug(
            'Check on file %r failed, reverting to old version.',
            config['dest'])
        with open(config['dest'], 'w') as f:
            f.write(existing)

    LOG.warning('Running restart command %r', config['restart_cmd'])
    check_call(config['restart_cmd'], shell=True)

    # @TODO: Set ownership and permissions


def main():
    p = ArgumentParser()
    p.add_argument('config_path')
    p.add_argument('--loop', type=int, default=None)
    args = p.parse_args()

    config = load_config(args.config_path)
    try:
        configure_logging(config['logging'])
    except KeyError:
        LOG.warning('No \'logging\' section set in config. Using default settings.')

    env = jinja2.Environment()
    for name, be_config in config['backends'].items():
        LOG.debug('Configuring backend %r', name)
        configure_backend(name, be_config)
        env.globals[name] = BACKENDS[name].get_val

    try:
        while True:
            for templ_config in config['templates']:
                LOG.debug('Evaluating template for %r', templ_config['dest'])
                try:
                    evaluate_template(env, templ_config)
                except Exception:
                    LOG.exception(
                        'Exception while evaluating template for dest %r.',
                        templ_config['dest'])
            if args.loop is None:
                break
            LOG.debug('Sleeping for %s second(s)...', args.loop)
            sleep(args.loop)
    except KeyboardInterrupt:
        LOG.critical('Quitting due to keyboard interrupt. Bye!')
    finally:
        for backend in BACKENDS.values():
            backend.disconnect()


if __name__ == '__main__':
    main()
