from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from ps_camp.db.base import Base


class ReferendumVote(Base):
    __tablename__ = "referendum_votes"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    referendum_id = Column(String, nullable=False)
    vote = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
