import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 載入環境變數
load_dotenv()

# 設定匯入路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from ps_camp.db.session import create_sqlite_engine, create_postgres_engine
from ps_camp.sql_models import User
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.npc_model import NPC

# 初始化連線
sqlite_engine = create_sqlite_engine()
postgres_engine = create_postgres_engine()

sqlite_session = Session(bind=sqlite_engine)
postgres_session = Session(bind=postgres_engine)

# 匯入使用者
users = sqlite_session.query(User).all()
print(f"\n🔍 Users to migrate: {len(users)}")
for user in users:
    print(f"   -> user: {user.username}")
    postgres_session.merge(user)
postgres_session.commit()

# 建立 username → UUID 對照表
username_to_id = {user.username: user.id for user in users}

# 匯入 NPC
npcs = sqlite_session.query(NPC).all()
print(f"\n🔍 NPCs to migrate: {len(npcs)}")
for npc in npcs:
    print(f"   -> npc: {npc.name}")
    postgres_session.merge(npc)
postgres_session.commit()

# 匯入貼文
posts = sqlite_session.query(Post).all()
print(f"\n🔍 Posts to migrate: {len(posts)}")
for post in posts:
    print(f"   -> post title: {post.title}, by: {post.created_by}")

    # 將 created_by 從 username 轉為對應 UUID
    if post.created_by in username_to_id:
        post.created_by = username_to_id[post.created_by]
    else:
        print(f"⚠️ 無對應使用者 {post.created_by}，跳過")
        continue

    postgres_session.merge(post)

postgres_session.commit()
print("\n✅ Migration completed successfully.")
