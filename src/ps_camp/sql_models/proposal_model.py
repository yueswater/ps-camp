from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from ps_camp.db.base import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(String, primary_key=True)
    group_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    file_url = Column(String, nullable=True)
