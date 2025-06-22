from typing import Any, Dict, List, Optional
from uuid import UUID

from ps_camp.models.npc import NPC
from ps_camp.repos.npc_repo import NPCRepository


class NPCData(NPCRepository):
    def __init__(self):
        # In-memory repository for NPCs
        self.npc_repo: Dict[UUID, NPC] = {}

    def add(self, npc: NPC) -> None:
        if npc.npc_id in self.npc_repo:
            raise ValueError("請勿重複加入 NPC")
        self.npc_repo[npc.npc_id] = npc

    def delete(self, npc_id: UUID) -> None:
        if npc_id not in self.npc_repo:
            raise ValueError("查無此 NPC！")
        del self.npc_repo[npc_id]

    def update(self, npc: NPC, update_data: Dict[str, Any]) -> None:
        if npc.npc_id not in self.npc_repo:
            raise ValueError("查無此 NPC！")

        # Apply updates to the existing NPC object
        for k, v in update_data.items():
            if hasattr(npc, k):
                setattr(npc, k, v)

    def get_by_npc_id(self, npc_id: UUID) -> Optional[NPC]:
        return self.npc_repo.get(npc_id)

    def get_by_npc_name(self, npc_name: str) -> List[NPC]:
        return [npc for npc in self.npc_repo.values() if npc_name in npc.npc_name]

    def get_all(self) -> List[NPC]:
        return list(self.npc_repo.values())
