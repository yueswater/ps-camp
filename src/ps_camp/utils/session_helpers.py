from functools import wraps
from flask import session, g
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.db.session import get_db

def refresh_user_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" in session:
            db = next(get_db())
            user_repo = UserSQLRepository(db)
            user = user_repo.get_by_id(session["user"]["id"])
            if user:
                session["user"].update({
                    "fullname": user.fullname,
                    "coins": user.coins,
                    "role": user.role,
                })
                g.user = user
        return func(*args, **kwargs)
    return wrapper