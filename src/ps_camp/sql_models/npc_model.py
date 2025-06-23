import uuid

from sqlalchemy import Column, String

from ps_camp.db.base import Base


class NPC(Base):
    __tablename__ = "npcs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    party = Column(String, nullable=False)
    picture = Column(String, nullable=True)
