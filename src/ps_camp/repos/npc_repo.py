from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from ps_camp.models.npc import NPC


class NPCRepository(ABC):
    @abstractmethod
    def add(self, npc: NPC) -> None:
        pass

    @abstractmethod
    def delete(self, npc_id: UUID) -> None:
        pass

    @abstractmethod
    def update(self, npc: NPC, update_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_by_npc_id(self, npc_id: UUID) -> Optional[NPC]:
        pass

    @abstractmethod
    def get_by_npc_name(self, npc_name: str) -> List[NPC]:
        pass

    @abstractmethod
    def get_all(self) -> List[NPC]:
        pass
