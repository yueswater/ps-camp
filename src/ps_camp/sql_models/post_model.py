from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ps_camp.db.base import Base
import uuid


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    category = Column(String)  # Stored as comma-separated string
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    author = relationship("User", backref="posts")
    replies = Column(Integer, default=0, nullable=False)
