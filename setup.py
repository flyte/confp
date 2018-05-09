from setuptools import setup, find_packages


setup(
    name='confp',
    version='0.2.4',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'jinja2',
        'pyyaml',
        'cerberus<1.2'
    ],
    entry_points=dict(
        console_scripts=[
            'confp = confp.__main__:main'
        ]
    )
)
