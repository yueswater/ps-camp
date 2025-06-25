import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from ps_camp.sql_models.referendum_vote_model import ReferendumVote


class ReferendumVoteSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_vote(self, user_id: str, referendum_id: str, vote: str) -> ReferendumVote:
        rv = ReferendumVote(
            id=str(uuid.uuid4()),
            user_id=user_id,
            referendum_id=referendum_id,
            vote=vote,
        )
        self.db.add(rv)
        self.db.commit()
        self.db.refresh(rv)
        return rv

    def get_votes_by_user(self, user_id: str) -> list[ReferendumVote]:
        return self.db.query(ReferendumVote).filter_by(user_id=user_id).all()

    def has_voted_for(self, user_id: str, referendum_id: str) -> bool:
        return (
            self.db.query(ReferendumVote)
            .filter_by(user_id=user_id, referendum_id=referendum_id)
            .first()
            is not None
        )

    def get_vote_counts(self) -> dict[str, int]:
        results = (
            self.db.query(ReferendumVote.vote, func.count())
            .group_by(ReferendumVote.vote)
            .all()
        )
        return {vote.lower(): count for vote, count in results}

    def get_vote_counts_by_referendum_ids(
        self, referendum_ids: list[str]
    ) -> dict[str, dict[str, int]]:
        if not referendum_ids:
            return {}

        vote_map = {"agree": "yes", "disagree": "no"}
        results = (
            self.db.query(
                ReferendumVote.referendum_id,
                ReferendumVote.vote,
                func.count().label("count"),
            )
            .filter(ReferendumVote.referendum_id.in_(referendum_ids))
            .group_by(ReferendumVote.referendum_id, ReferendumVote.vote)
            .all()
        )

        counts: dict[str, dict[str, int]] = {}
        for ref_id, vote, count in results:
            if ref_id not in counts:
                counts[ref_id] = {"yes": 0, "no": 0}
            vote_key = vote_map.get(vote.lower())
            if vote_key:
                counts[ref_id][vote_key] = count

        return counts
