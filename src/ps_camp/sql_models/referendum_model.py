from uuid import uuid4

from sqlalchemy import Boolean, Column, String

from ps_camp.db.base import Base


class Referendum(Base):
    __tablename__ = "referendums"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)
