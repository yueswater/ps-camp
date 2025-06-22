from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID

from ps_camp.utils.password_hasher import PasswordHasher


@dataclass
class Party:
    party_id: UUID
    party_icon: str
    partyname: str
    fullname: str
    hashed_password: str
    role: str
    members: List[Dict[str, str]] = field(default_factory=list)
    leader: str
    draft: str
    posts: List[str] = field(default_factory=list)
    coins: int = 10000
    passwordHasher: PasswordHasher = field(init=False, repr=False)

    # Post-init hook to initialize internal password hasher
    def __post_init__(self):
        self.passwordHasher = PasswordHasher()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "party_id": self.party_id,
            "party_icon": self.party_icon,
            "partyname": self.partyname,
            "fullname": self.fullname,
            "password_hashed": self.passwordHasher.hash_password(self.hashed_password),
            "role": self.role,
            "members": self._format_members(self.members),
            "leader": self.leader,
            "draft": self.draft,
            "posts": self._format_posts(self.posts),
            "coins": self.coins,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Party":
        return cls(
            party_id=data["party_id"],
            party_icon=data["party_icon"],
            partyname=data["partyname"],
            fullname=data["fullname"],
            hashed_password=data["hashed_password"],
            role=data["role"],
            members=data.get("members", []),
            leader=data["leader"],
            draft=data["draft"],
            posts=data.get("posts", []),
            coins=data.get("coins", 10000),
        )

    @staticmethod
    def _format_members(members: List[Dict[str, str]]) -> str:
        lines = ["Member list:\n"]
        for member in members:
            for title, name in member.items():
                lines.append(f"{title}: {name}")
        return "\n".join(lines)

    @staticmethod
    def _format_posts(posts: List[str]) -> str:
        if not posts:
            return "無貼文可顯示"
        lines = ["貼文列表"]
        for i, post in enumerate(posts):
            lines.append(f"第 {i + 1} 則貼文：\n{post}")
        return "\n".join(lines)
