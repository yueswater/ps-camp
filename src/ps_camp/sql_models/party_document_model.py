from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from ps_camp.db.base import Base


class PartyDocument(Base):
    __tablename__ = "party_documents"

    id = Column(String, primary_key=True)
    party_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    cabinet_url = Column(String, nullable=True)
    alliance_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
