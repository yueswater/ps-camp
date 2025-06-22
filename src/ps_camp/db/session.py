import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ps_camp.db.base import Base

# 預設使用 SQLite，如果有設定 DATABASE_URL 則使用該值（例如 PostgreSQL）
DATABASE_URL = os.getenv("DATABASE_URL")

# 建立 engine（future=True 是 SQLAlchemy 2.0 的標準寫法）
engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Session 工廠（由外部統一調用）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ✅ 額外提供兩個 engine 工廠函式給 migration script 使用
def create_sqlite_engine():
    sqlite_url = "sqlite:///src/ps_camp/db/camp.db"
    return create_engine(sqlite_url, connect_args={"check_same_thread": False}, future=True)


def create_postgres_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("環境變數 DATABASE_URL 未設定")
    return create_engine(db_url, future=True)


# ✅ FastAPI 或其他框架用的 DB 依賴注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
