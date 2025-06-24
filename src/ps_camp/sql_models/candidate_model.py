from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from ps_camp.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True)
    party_id = Column(String, ForeignKey("users.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # ⬅ 新增這行
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
