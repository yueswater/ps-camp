import logging
from uuid import uuid4

from tqdm import tqdm

from ps_camp.app import app
from ps_camp.db.base import Base
from ps_camp.db.session import get_db_session
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.sql_models.user_model import User
from ps_camp.utils.password_hasher import PasswordHasher

# Define the number of selections
AREAS = {
    "a": 134,
    "b": 133,
    "c": 134,
    "npc": 120,
}


def generate_users():
    hasher = PasswordHasher()
    users = []

    total_users = sum(AREAS.values())
    with tqdm(total=total_users, desc="產生帳號中") as pbar:
        for prefix, total in AREAS.items():
            for i in range(1, total + 1):
                suffix = f"{i:03}"
                username = f"{prefix}{suffix}"
                users.append(
                    User(
                        id=uuid4(),
                        username=username,
                        fullname=username,
                        hashed_password=hasher.hash_password("vote"),
                        role="voter",
                        coins=0,
                        affiliation_id=None,
                        affiliation_type=None,
                    )
                )
                pbar.update(1)
    return users


def main():
    with app.app_context():
        logging.debug(f"目前已註冊資料表：{list(Base.metadata.tables.keys())}")

        users = generate_users()
        logging.debug(f"正在批次註冊 {len(users)} 位用戶，請耐心等候")

        with get_db_session() as db:
            user_repo = UserSQLRepository(db)

            for user in tqdm(users, desc="寫入資料庫中"):
                if user_repo.get_by_username(user.username):
                    logging.warning(f"{user.username} 已存在，略過。")
                    continue

                user_repo.add(user)
                logging.info(f"已新增：{user.fullname}（{user.role}）")


if __name__ == "__main__":
    main()
