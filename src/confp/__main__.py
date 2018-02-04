from __future__ import print_function

from argparse import ArgumentParser
from importlib import import_module
from time import sleep

from .config import load_config, validate_module_config
from .backends import install_missing_requirements

from jinja2 import Environment


BACKENDS = {}


def configure_backend(name, config):
    backend_module = import_module('confp.backends.%s' % config['type'])
    config = validate_module_config(backend_module.CONFIG_SCHEMA, config)
    install_missing_requirements(backend_module)
    BACKENDS[name] = backend_module.Backend(config)
    BACKENDS[name].connect()


def evaluate_template(env, config):
    # Get any values which have been set in 'vars'
    context = {}
    for key, var_config in config.get('vars', {}).items():
        context[key] = BACKENDS[var_config['backend']].get_val(
            var_config['key'])

    # Read the template
    with open(config['src']) as f:
        template = env.from_string(f.read())

    # Render the template
    rendered = template.render(context)

    # Read the existing config file, if it exists
    try:
        with open(config['dest']) as f:
            existing = f.read()
    except OSError:
        # It probably didn't exist, so we'll try creating/replacing it anyway
        existing = None

    # Compare our rendered template with the existing config file
    if existing != rendered:
        # Replace the config with our newly rendered one
        with open(config['dest'], 'w') as f:
            f.write(rendered)
        print('Updated the file at %r.' % config['dest'])
    else:
        # Nothing changed
        print('File at %r did not need updating.' % config['dest'])


def main(config_path, loop=None):
    config = load_config(config_path)
    env = Environment()
    for name, be_config in config['backends'].items():
        configure_backend(name, be_config)
        env.globals[name] = BACKENDS[name].get_val

    for templ_config in config['templates']:
        evaluate_template(env, templ_config)

    if loop is not None:
        while True:
            sleep(loop)
            for templ_config in config['templates']:
                evaluate_template(env, templ_config)

    for backend in BACKENDS.values():
        backend.disconnect()


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('config_path')
    p.add_argument('--loop', type=int, default=None)
    args = p.parse_args()
    main(args.config_path, args.loop)
