from sqlalchemy.orm import Session

from ps_camp.sql_models.referendum_model import Referendum


class ReferendumSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_referendums(self) -> list[Referendum]:
        return self.db.query(Referendum).filter_by(active=True).all()

    def get_by_id(self, referendum_id: str) -> Referendum:
        return self.db.query(Referendum).filter_by(id=referendum_id).first()
