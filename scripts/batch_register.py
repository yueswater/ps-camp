import json
import logging
from uuid import UUID

from tqdm import tqdm

from ps_camp.app import app, map_role_to_owner_type
from ps_camp.db.base import Base
from ps_camp.db.session import get_db_session
from ps_camp.repos.bank_sql_repo import BankSQLRepository
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.sql_models.user_model import User
from ps_camp.utils.password_hasher import PasswordHasher


def main():
    with app.app_context():
        logging.debug(f"目前已註冊資料表：{list(Base.metadata.tables.keys())}")

        with open(
            "./src/ps_camp/static/data/private/batch_users.json", encoding="utf-8"
        ) as f:
            users = json.load(f)

        logging.debug(f"正在批次註冊 {len(users)} 位用戶，請耐心等候")
        hasher = PasswordHasher()

        with get_db_session() as db:
            user_repo = UserSQLRepository(db)
            bank_repo = BankSQLRepository(db)

            for u in tqdm(users, desc="註冊使用者中"):
                if user_repo.get_by_username(u["username"]):
                    logging.warning(f"{u['username']} 已存在，略過。")
                    continue

                user = User(
                    id=UUID(u["id"]),
                    username=u["username"],
                    fullname=u["fullname"],
                    hashed_password=hasher.hash_password(u["password"]),
                    role=u["role"],
                    coins=u["coins"],
                    affiliation_id=None,
                    affiliation_type=None,
                )
                user_repo.add(user)

                if u["role"] != "member":
                    bank_repo.create_account(
                        owner_id=u["id"],
                        owner_type=map_role_to_owner_type(u["role"]),
                        initial_balance=u["coins"],
                    )
                logging.info(f"已新增：{u['fullname']}（{u['role']}）")


if __name__ == "__main__":
    main()
