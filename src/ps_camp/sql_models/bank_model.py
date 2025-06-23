import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ps_camp.db.base import Base


class OwnerType(enum.Enum):
    user = "user"
    party = "party"
    group = "group"
    admin = "admin"


class TransactionType(enum.Enum):
    post_cost = "post_cost"
    transfer = "transfer"
    distribute = "distribute"
    post_penalty = "post_penalty"
    initial_grant = "initial_grant"
    system_adjustment = "system_adjustment"


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(String, primary_key=True)
    owner_id = Column(String, nullable=False)
    owner_type = Column(Enum(OwnerType), nullable=False)
    account_number = Column(String, unique=True, nullable=False)
    balance = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    outgoing_transactions = relationship(
        "Transaction",
        back_populates="from_account",
        foreign_keys="Transaction.from_account_id",
    )
    incoming_transactions = relationship(
        "Transaction",
        back_populates="to_account",
        foreign_keys="Transaction.to_account_id",
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    from_account_id = Column(String, ForeignKey("bank_accounts.id"))
    to_account_id = Column(String, ForeignKey("bank_accounts.id"))
    amount = Column(BigInteger, nullable=False)
    note = Column(String, nullable=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    from_account = relationship(
        "BankAccount",
        foreign_keys=[from_account_id],
        back_populates="outgoing_transactions",
    )
    to_account = relationship(
        "BankAccount",
        foreign_keys=[to_account_id],
        back_populates="incoming_transactions",
    )
