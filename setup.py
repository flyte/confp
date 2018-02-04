from setuptools import setup, find_packages


setup(
    name='confp',
    version='0.0.4',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'jinja2',
        'pyyaml',
        'cerberus'
    ]
)
