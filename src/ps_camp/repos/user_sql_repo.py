from sqlalchemy.orm import Session

from ps_camp.sql_models.user_model import User


class UserSQLRepository:
    model = User

    def __init__(self, db: Session):
        self.db = db

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_users_by_ids(self, ids: list[str]) -> list[User]:
        if not ids:
            return []
        return self.db.query(User).filter(User.id.in_(ids)).all()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_all(self) -> list[User]:
        return self.db.query(User).all()

    def delete(self, user_id: str) -> None:
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
