from setuptools import setup, find_packages


setup(
    name='confp',
    version='0.0.7',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'jinja2',
        'pyyaml',
        'cerberus'
    ],
    entry_points=dict(
        console_scripts=[
            'confp = confp.__main__:main'
        ]
    )
)
