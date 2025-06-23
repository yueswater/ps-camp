import os
import sys

from dotenv import load_dotenv
from sqlalchemy.orm import Session

# load environment variables
load_dotenv()

# set import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from ps_camp.db.session import create_postgres_engine, create_sqlite_engine
from ps_camp.sql_models import User
from ps_camp.sql_models.npc_model import NPC
from ps_camp.sql_models.post_model import Post

# initialize connections
sqlite_engine = create_sqlite_engine()
postgres_engine = create_postgres_engine()

sqlite_session = Session(bind=sqlite_engine)
postgres_session = Session(bind=postgres_engine)

# import users
users = sqlite_session.query(User).all()
print(f"\nUsers to migrate: {len(users)}")
for user in users:
    print(f"   -> user: {user.username}")
    postgres_session.merge(user)
postgres_session.commit()

# build username to uuid mapping
username_to_id = {user.username: user.id for user in users}

# import npcs
npcs = sqlite_session.query(NPC).all()
print(f"\nNPCs to migrate: {len(npcs)}")
for npc in npcs:
    print(f"   -> npc: {npc.name}")
    postgres_session.merge(npc)
postgres_session.commit()

# import posts
posts = sqlite_session.query(Post).all()
print(f"\n🔍 Posts to migrate: {len(posts)}")
for post in posts:
    print(f"   -> post title: {post.title}, by: {post.created_by}")

    # convert created_by from username to corresponding uuid
    if post.created_by in username_to_id:
        post.created_by = username_to_id[post.created_by]
    else:
        print(f"No matching user {post.created_by}, skipped")
        continue

    postgres_session.merge(post)

postgres_session.commit()
print("\nMigration completed successfully.")
