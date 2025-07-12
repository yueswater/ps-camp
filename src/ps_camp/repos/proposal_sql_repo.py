from datetime import datetime
from sqlalchemy.orm import Session

from ps_camp.sql_models.proposal_model import Proposal


class ProposalSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, proposal: Proposal) -> None:
        self.db.add(proposal)

    def get_by_id(self, proposal_id: str) -> Proposal | None:
        return self.db.query(Proposal).filter_by(id=proposal_id).first()

    def get_all(self) -> list[Proposal]:
        return self.db.query(Proposal).all()

    def get_by_group_id(self, group_id: str) -> list[Proposal]:
        return self.db.query(Proposal).filter_by(group_id=group_id).all()

    def delete(self, proposal: Proposal) -> None:
        self.db.delete(proposal)

    def get_active_proposals(self) -> list[Proposal]:
        now = datetime.now()
        return self.db.query(Proposal).filter(Proposal.deadline >= now).all()