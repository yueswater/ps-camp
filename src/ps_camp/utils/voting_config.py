import os
from pathlib import Path

from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_vote_open_time():
    return isoparse(os.getenv("VOTE_OPEN_TIME"))


def get_vote_close_time():
    return isoparse(os.getenv("VOTE_CLOSE_TIME"))


def get_register_close_time():
    return isoparse(os.getenv("REGISTER_CLOSE_TIME"))


def get_upload_close_time():
    return isoparse(os.getenv("UPLOAD_CLOSE_TIME"))

def get_camp_deadlines():
    start_date_str = os.getenv("CAMP_START_DATE", "2025-07-11")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    third_day = start_date + timedelta(days=2)
    deadline = datetime.combine(third_day + timedelta(days=1), datetime.min.time())
    return deadline.replace(tzinfo=timezone.utc)