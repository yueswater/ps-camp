# seed_referendums.py
from uuid import uuid4

from ps_camp.db.session import get_db_session
from ps_camp.sql_models.proposal_model import Proposal
from ps_camp.sql_models.referendum_model import Referendum


def seed_referendums():
    with get_db_session() as db:
        proposals = db.query(Proposal).all()

        for p in proposals:
            # 避免重複建立（title 相同視為重複）
            exists = db.query(Referendum).filter_by(title=p.title).first()
            if exists:
                continue

            ref = Referendum(
                id=str(uuid4()), title=p.title, description=p.description, active=True
            )
            db.add(ref)

        db.commit()
        print("Referendums seeded from proposals.")


if __name__ == "__main__":
    seed_referendums()
