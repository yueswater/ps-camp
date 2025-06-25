import os
from pathlib import Path

from dateutil.parser import isoparse
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print(f"[ENV PATH] {env_path}")
print(f"[ENV] VOTE_OPEN_TIME = {os.getenv('VOTE_OPEN_TIME')}")
print(f"[ENV] VOTE_CLOSE_TIME = {os.getenv('VOTE_CLOSE_TIME')}")


def get_vote_open_time():
    return isoparse(os.getenv("VOTE_OPEN_TIME"))


def get_vote_close_time():
    return isoparse(os.getenv("VOTE_CLOSE_TIME"))
