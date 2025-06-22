import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ps_camp.db.base import Base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found")

engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_sqlite_engine():
    sqlite_url = "sqlite:///src/ps_camp/db/camp.db"
    return create_engine(sqlite_url, connect_args={"check_same_thread": False}, future=True)


def create_postgres_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("環境變數 DATABASE_URL 未設定")
    return create_engine(db_url, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
