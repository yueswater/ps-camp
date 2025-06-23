from uuid import uuid4

from sqlalchemy import BigInteger, Column, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ps_camp.db.base import Base
from ps_camp.sql_models.bank_model import OwnerType


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String, unique=True, nullable=False)
    fullname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    coins = Column(BigInteger, default=0)
    my_posts = relationship("Post", back_populates="user")
    affiliation_id = Column(String, nullable=True)
    affiliation_type = Column(Enum(OwnerType), nullable=True)
