import os
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ps_camp.repos.bank_sql_repo import BankSQLRepository
from ps_camp.sql_models.bank_model import OwnerType, TransactionType
from ps_camp.sql_models.post_model import Post

load_dotenv()


class PostSQLRepository:
    def __init__(self, db: Session):
        self.db = db
        self.bank_repo = BankSQLRepository(db)
        self.ADMIN_ID = os.getenv("ADMIN_ID")
        if not self.ADMIN_ID:
            raise EnvironmentError("ADMIN_ID 環境變數未設定")

    def _commit(self):
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def add(self, post: Post, owner_id: UUID, owner_type: OwnerType):
        user_account = self.bank_repo.get_account_by_owner(owner_id, owner_type)
        admin_account = self.bank_repo.get_account_by_owner(
            self.ADMIN_ID, OwnerType.admin
        )

        if not user_account or not admin_account:
            raise ValueError("找不到帳戶（政黨或中央）")

        self.bank_repo.create_transaction(
            from_account=user_account,
            to_account=admin_account,
            amount=1000,
            note="發文自動扣款",
            transaction_type=TransactionType.post_cost,
        )

        self.db.add(post)
        self.db.commit()

    def get_by_id(self, post_id: UUID) -> Post | None:
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        return self.db.query(Post).filter(Post.id == post_id).first()

    def get_all(self, order_desc: bool = True) -> list[Post]:
        query = self.db.query(Post)
        if order_desc and hasattr(Post, "created_at"):
            query = query.order_by(Post.created_at.desc())
        return query.all()

    def delete(self, post_id: UUID) -> bool:
        post = self.get_by_id(post_id)
        if not post:
            return False
        self.db.delete(post)
        self._commit()
        return True

    def search(self, keyword: str) -> list[Post]:
        return (
            self.db.query(Post)
            .filter(
                or_(
                    Post.title.ilike(f"%{keyword}%"),
                    Post.content.ilike(f"%{keyword}%"),
                    Post.created_by.ilike(f"%{keyword}%"),
                )
            )
            .all()
        )

    def filter(
        self,
        title: str = None,
        category: str = None,
        created_by: str = None,
        content: str = None,
    ) -> list[Post]:
        query = self.db.query(Post)

        if title:
            query = query.filter(Post.title.ilike(f"%{title}%"))
        if category:
            query = query.filter(Post.category == category)
        if created_by:
            query = query.filter(Post.created_by.ilike(f"%{created_by}%"))
        if content:
            query = query.filter(Post.content.ilike(f"%{content}%"))

        return query.order_by(Post.created_at.desc()).all()
