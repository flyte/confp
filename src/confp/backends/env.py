import os


def get_vars(prefix):
    return {key[len(prefix):]: value for key, value in os.environ.items()
            if key.startswith(prefix)}
