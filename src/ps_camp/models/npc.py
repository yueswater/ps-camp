from dataclasses import dataclass
from typing import Any, Dict
from uuid import UUID


@dataclass
class NPC:
    npc_id: UUID
    npc_name: str
    npc_desc: str
    npc_party: str
    npc_pic: str

    def to_dict(self) -> Dict[str, Any]:
        # Serialize NPC data into a dictionary
        return {
            "npc_id": str(self.npc_id),
            "npc_name": self.npc_name,
            "npc_desc": self.npc_desc,
            "npc_party": self.npc_party,
            "npc_pic": self.npc_pic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        # Reconstruct an NPC instance from dictionary data
        return cls(
            npc_id=UUID(data["npc_id"]),
            npc_name=data["npc_name"],
            npc_desc=data["npc_desc"],
            npc_party=data["npc_party"],
            npc_pic=data["npc_pic"],
        )
