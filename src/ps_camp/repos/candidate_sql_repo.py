from sqlalchemy.orm import Session

from ps_camp.sql_models.candidate_model import Candidate


class CandidateSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, candidate: Candidate) -> None:
        self.db.add(candidate)

    def get_by_id(self, candidate_id: str) -> Candidate | None:
        return self.db.query(Candidate).filter_by(id=candidate_id).first()

    def get_all(self) -> list[Candidate]:
        return self.db.query(Candidate).all()

    def get_by_party_id(self, party_id: str) -> list[Candidate]:
        return self.db.query(Candidate).filter_by(party_id=party_id).all()

    def delete(self, candidate: Candidate) -> None:
        self.db.delete(candidate)
