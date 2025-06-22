import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection URL (SQLite here, can change to PostgreSQL, MySQL, etc.)
# DATABASE_URL = "sqlite:///src/ps_camp/db/camp.db"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///src/ps_camp/db/camp.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for dependency injection (e.g. FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
