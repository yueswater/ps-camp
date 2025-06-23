from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from ps_camp.db.base import Base


class ReferendumVote(Base):
    __tablename__ = "referendum_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referendum_id = Column(UUID(as_uuid=True), nullable=False)
    vote = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(UTC))
