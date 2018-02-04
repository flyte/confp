from __future__ import print_function

from importlib import import_module

from .config import load_config, validate_module_config

from jinja2 import Environment


BACKENDS = {}


def configure_backend(name, config):
    backend_module = import_module('confp.backends.%s' % config['type'])
    config = validate_module_config(backend_module.CONFIG_SCHEMA, config)
    BACKENDS[name] = backend_module.Backend(config)
    BACKENDS[name].connect()


def main():
    config = load_config('config.example.yml')
    env = Environment()
    for name, be_config in config['backends'].items():
        configure_backend(name, be_config)
        env.globals[name] = BACKENDS[name].get_val

    for templ_config in config['templates']:
        context = {}
        for key, var_config in templ_config.get('vars', {}).items():
            context[key] = BACKENDS[var_config['backend']].get_val(
                var_config['key'])
        with open(templ_config['src']) as f:
            template = env.from_string(f.read())

        rendered = template.render(context)
        try:
            with open(templ_config['dest']) as f:
                existing = f.read()
        except OSError:
            existing = ''
        if existing != rendered:
            with open(templ_config['dest'], 'w') as f:
                f.write(rendered)
            print('Updated the file at %r.' % templ_config['dest'])
        else:
            print('File at %r did not need updating.' % templ_config['dest'])


if __name__ == '__main__':
    main()
    for backend in BACKENDS.values():
        backend.disconnect()
