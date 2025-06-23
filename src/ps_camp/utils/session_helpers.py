from functools import wraps

from flask import g, session

from ps_camp.db.session import get_db_session
from ps_camp.repos.user_sql_repo import UserSQLRepository


def refresh_user_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" in session:
            with get_db_session() as db:
                user_repo = UserSQLRepository(db)
                user = user_repo.get_by_id(session["user"]["id"])
                if user:
                    session["user"].update(
                        {
                            "fullname": user.fullname,
                            "coins": user.coins,
                            "role": user.role,
                        }
                    )
                    g.user = user
        return func(*args, **kwargs)

    return wrapper
