from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from ps_camp.db.base import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    voted_party_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
