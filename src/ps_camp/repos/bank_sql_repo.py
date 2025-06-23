import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ps_camp.sql_models.bank_model import (
    BankAccount,
    OwnerType,
    Transaction,
    TransactionType,
)


class BankSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_account_by_id(self, account_id: str) -> BankAccount | None:
        return self.db.query(BankAccount).filter(BankAccount.id == account_id).first()

    def get_accounts_by_ids(self, ids: list[str]) -> list[BankAccount]:
        if not ids:
            return []
        return self.db.query(BankAccount).filter(BankAccount.id.in_(ids)).all()

    def get_account_by_owner(self, owner_id: str, owner_type: OwnerType) -> BankAccount:
        print(
            f"[DEBUG] 查詢帳戶: owner_id={owner_id}, owner_type={owner_type} ({type(owner_type)})"
        )
        return (
            self.db.query(BankAccount)
            .filter_by(owner_id=str(owner_id), owner_type=owner_type.value)
            .first()
        )

    def get_account_by_number(self, account_number: str) -> BankAccount:
        return (
            self.db.query(BankAccount).filter_by(account_number=account_number).first()
        )

    def create_account(
        self, owner_id: str, owner_type: OwnerType, initial_balance: int = 0
    ) -> BankAccount:
        account = BankAccount(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            owner_type=owner_type,
            account_number=str(uuid.uuid4())[:8],
            balance=initial_balance,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_transactions(self, account_id: str) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(
                or_(
                    Transaction.from_account_id == account_id,
                    Transaction.to_account_id == account_id,
                )
            )
            .order_by(Transaction.created_at.desc())
            .all()
        )

    def create_transaction(
        self,
        from_account: BankAccount,
        to_account: BankAccount,
        amount: int,
        note: str = "",
        transaction_type: TransactionType = TransactionType.transfer,
    ) -> Transaction:
        if from_account.balance < amount:
            raise ValueError("Insufficient funds")

        from_account.balance -= amount
        to_account.balance += amount

        tx = Transaction(
            id=str(uuid.uuid4()),
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            amount=amount,
            note=note,
            transaction_type=transaction_type,
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx
