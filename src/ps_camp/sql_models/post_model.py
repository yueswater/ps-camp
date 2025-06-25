from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from ps_camp.db.base import Base
from ps_camp.utils.humanize_time_diff import taipei_now


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=taipei_now)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="my_posts")
    likes = Column(MutableList.as_mutable(JSON), default=list, nullable=False)
    replies = Column(MutableList.as_mutable(JSON), nullable=False, default=list)
