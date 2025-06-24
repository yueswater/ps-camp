import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from ps_camp.sql_models.vote_model import Vote


class VoteSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_vote(self, user_id: str, voted_party_id: str) -> Vote:
        vote = Vote(
            id=str(uuid.uuid4()),
            user_id=user_id,
            voted_party_id=voted_party_id,
        )
        self.db.add(vote)
        self.db.commit()
        self.db.refresh(vote)
        return vote

    def has_voted(self, user_id: str) -> bool:
        return self.db.query(Vote).filter_by(user_id=user_id).first() is not None

    def get_vote_by_user(self, user_id: str) -> Vote:
        return self.db.query(Vote).filter_by(user_id=user_id).first()

    def get_all_votes(self) -> list[Vote]:
        return self.db.query(Vote).all()

    def get_party_vote_counts(self) -> dict[str, int]:
        results = (
            self.db.query(Vote.voted_party_id, func.count())
            .group_by(Vote.voted_party_id)
            .all()
        )
        return {party_id: count for party_id, count in results}
