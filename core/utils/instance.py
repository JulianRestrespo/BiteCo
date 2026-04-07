import os


def get_instance_name():
    return os.getenv("INSTANCE_NAME", "local-dev")