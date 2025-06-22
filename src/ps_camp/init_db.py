from ps_camp.db import Base, engine
from ps_camp.sql_models import User, Post, NPC


def init_db():
    print("🔧 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


if __name__ == "__main__":
    init_db()
