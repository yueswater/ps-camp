import os
from pathlib import Path

from dateutil.parser import isoparse
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_vote_open_time():
    return isoparse(os.getenv("VOTE_OPEN_TIME"))


def get_vote_close_time():
    return isoparse(os.getenv("VOTE_CLOSE_TIME"))
