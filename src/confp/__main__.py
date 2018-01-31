from __future__ import print_function

from importlib import import_module

from .config import get_confp_config

from jinja2 import Template


def main():
    config = get_confp_config()
    backend = import_module('confp.backends.%s' % config['backend'])
    variables = backend.get_vars(config['prefix'])
    with open(config['template']) as f:
        template = Template(f.read())
    with open(config['destination'], 'w') as f:
        f.write(template.render(**variables))
    print('Config file written to %s' % config['destination'])

if __name__ == '__main__':
    main()
