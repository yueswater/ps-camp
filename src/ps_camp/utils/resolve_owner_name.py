from sqlalchemy.orm import Session

from src.ps_camp.repos.user_sql_repo import UserSQLRepository


def resolve_owner_name(owner_id: str, db: Session) -> str:
    user_repo = UserSQLRepository(db)
    user = user_repo.get_by_id(owner_id)
    if not user:
        return "未知使用者"

    if user.role == "admin":
        return "中央銀行"
    elif user.role == "party":
        return f"{user.fullname}（政黨）"
    elif user.role == "interest_group":
        return f"{user.fullname}（利團）"
    else:
        return user.fullname
