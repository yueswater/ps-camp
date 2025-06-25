from datetime import datetime

import pytz
from pytz import utc


def taipei_now():
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.now(tz)
    print("[taipei_now] Called:", now.isoformat())
    return now


def humanize_time_diff(created_at):
    tz = pytz.timezone("Asia/Taipei")

    if created_at.tzinfo is None:
        created_at = utc.localize(created_at).astimezone(tz)
    else:
        created_at = created_at.astimezone(tz)

    now = datetime.now(tz)
    diff = now - created_at

    if diff.total_seconds() < 60:
        return "剛剛"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} 分鐘前"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)} 小時前"
    elif diff.days == 1:
        return "昨天"
    elif diff.days < 7:
        return f"{diff.days} 天前"
    else:
        return created_at.strftime("%m月%d日")
