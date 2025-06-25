import os

from dateutil.parser import isoparse


def get_register_close_time():
    return isoparse(os.getenv("REGISTER_CLOSE_TIME"))
