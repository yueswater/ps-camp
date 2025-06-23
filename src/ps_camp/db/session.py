import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

__all__ = ("SessionLocal", "get_db_session")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found")

is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    **(
        {"pool_size": 10, "max_overflow": 20, "pool_timeout": 60}
        if not is_sqlite
        else {}
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_sqlite_engine():
    sqlite_url = "sqlite:///src/ps_camp/db/camp.db"
    return create_engine(
        sqlite_url, connect_args={"check_same_thread": False}, future=True
    )


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


@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
