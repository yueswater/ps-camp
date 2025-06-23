from sqlalchemy.orm import Session

from ps_camp.sql_models.npc_model import NPC


class NPCSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, npc: NPC) -> NPC:
        self.db.add(npc)
        self.db.commit()
        self.db.refresh(npc)
        return npc

    def get_by_id(self, npc_id: str) -> NPC | None:
        return self.db.query(NPC).filter(NPC.id == npc_id).first()

    def get_all(self) -> list[NPC]:
        return self.db.query(NPC).all()

    def delete(self, npc_id: str) -> None:
        npc = self.get_by_id(npc_id)
        if npc:
            self.db.delete(npc)
            self.db.commit()
