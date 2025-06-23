from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from ps_camp.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True)
    party_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
