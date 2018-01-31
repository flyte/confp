import os


def get_confp_config():
    return dict(
        template=os.environ['CONFP_TEMPLATE'],
        destination=os.environ['CONFP_DESTINATION'],
        prefix=os.environ.get('CONFP_PREFIX', ''),
        backend=os.environ.get('CONFP_BACKEND', 'env')
    )
