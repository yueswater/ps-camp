from typing import Any, Dict, List, Optional
from uuid import UUID

from ps_camp.repos.party_repo import Party, PartyRepository


class PartyData(PartyRepository):
    def __init__(self):
        self.party_repo: Dict[UUID, Party] = {}

    def add_party(self, party: Party) -> Party:
        if party.party_id in self.party_repo:
            raise ValueError("政黨已加入")
        self.party_repo[party.party_id] = party

    def delete_party(self, party_id: UUID) -> None:
        if party_id not in self.party_repo:
            raise ValueError("查無此政黨！")

        del self.party_repo[party_id]

    def update_party(self, party_id: UUID, update_data: Dict[str, Any]) -> Party:
        party = self.party_repo.get(party_id)

        if not party:
            raise ValueError("查無此政黨！")
        else:
            for k, v in update_data.items():
                if hasattr(party, k):
                    setattr(party, k, v)

        return party

    def get_all(self) -> List[Party]:
        return list(self.party_repo.values())

    def get_by_party_id(self, party_id: UUID) -> Optional[Party]:
        party = self.party_repo.get(party_id)

        if not party:
            return None
        else:
            return party

    def get_by_party_name(self, party_name: UUID) -> Optional[Party]:
        for party in self.party_repo.values():
            if party_name == party.partyname:
                return party
            else:
                return None
