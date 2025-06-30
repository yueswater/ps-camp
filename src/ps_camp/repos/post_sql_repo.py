import logging
import os
from uuid import UUID

from datetime import datetime, time, timedelta
from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ps_camp.repos.bank_sql_repo import BankSQLRepository
from ps_camp.sql_models.bank_model import OwnerType, TransactionType
from ps_camp.sql_models.post_model import Post
from ps_camp.utils.humanize_time_diff import taipei_now

load_dotenv()

def calculate_post_fee(created_time: datetime) -> int:
    # Assume that the camp period starts at 00:00 of Day 1
    CAMP_START_DATE_STR = os.getenv("CAMP_START_DATE", "2025-07-01")  # fallback 可保留
    CAMP_START_DATE = datetime.strptime(CAMP_START_DATE_STR, "%Y-%m-%d").replace(
        hour=0, minute=0, second=0
    ).astimezone(tz=created_time.tzinfo)
    delta = created_time - CAMP_START_DATE
    day_number = delta.days + 1  # Day 1 = Day 1

    # Make sure to take effect only on days 1 to 4
    base_fee_map = {1: 30, 2: 60, 3: 90, 4: 120}
    bonus_fee_map = {1: 5, 2: 15, 3: 30, 4: 45}
    base_fee = base_fee_map.get(day_number, 1000)  # After day 4, return to fixed fee
    bonus_fee = bonus_fee_map.get(day_number, 0)

    # Primetime check
    golden_start = time(18, 0)
    golden_end = time(21, 0)
    if golden_start <= created_time.time() <= golden_end:
        return base_fee + bonus_fee
    return base_fee

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
            logging.error(
                f"無法找到帳戶: user_id={owner_id}, type={owner_type}, admin_id={self.ADMIN_ID}"
            )
            raise ValueError("找不到帳戶（政黨或中央）")

        # Calculate the fee based on the time of issuance
        created_time = post.created_at or taipei_now()
        fee = calculate_post_fee(created_time)

        self.bank_repo.create_transaction(
            from_account=user_account,
            to_account=admin_account,
            amount=fee,
            note=f"發文自動扣款（{fee}）",
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