from os import environ


def get_setting(key: str, *args):
    try:
        return environ[key]
    except KeyError:
        try:
            return args[0]
        except IndexError:
            raise KeyError(f"{key} must be set")


def get_setting_secret(key: str, *args):
    try:
        secret_file = environ[key + "_FILE"]
    except KeyError:
        return get_setting(key, *args)
    else:
        with open(secret_file) as f:
            return f.read().strip()
