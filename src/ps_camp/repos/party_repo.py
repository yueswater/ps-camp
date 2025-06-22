from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from ps_camp.models.party import Party


class PartyRepository(ABC):
    @abstractmethod
    def add(self, party: Party) -> None:
        pass

    @abstractmethod
    def delete(self, party_id: UUID) -> None:
        pass

    @abstractmethod
    def update(self, party: Party, update_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_by_party_id(self, party_id: UUID) -> Optional[Party]:
        pass

    @abstractmethod
    def get_by_party_name(self, party_name: str) -> Optional[Party]:
        pass

    @abstractmethod
    def get_all(self) -> List[Party]:
        pass
