from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from ps_camp.models.party import Party


@dataclass
class Comments:
    comment_by: Party
    comment_at: datetime
    comment_content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_by": self.comment_by.partyname,  # only expose partyname, not full object
            "comment_at": self.comment_at.isoformat(),
            "comment_content": self.comment_content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comments":
        return cls(
            comment_by=data["comment_by"],
            comment_at=data["comment_at"],
            comment_content=data["comment_content"],
        )


@dataclass
class Post:
    post_id: UUID
    title: str
    category: List[str]
    created_by: Party
    created_at: datetime
    content: str
    likes: int = 0
    dislikes: int = 0
    comments: List[Comments] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": str(self.post_id),
            "title": self.title,
            "category": self.category,
            "created_by": self.created_by.partyname,
            "created_at": self.created_at.isoformat(),
            "content": self.content,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "comments": [c.to_dict() for c in self.comments],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Post":
        return cls(
            post_id=data["post_id"],
            title=data["title"],
            category=data.get("category", []),
            created_by=data["created_by"],
            created_at=data["created_at"],
            content=data["content"],
            likes=data.get("likes", 0),
            dislikes=data.get("dislikes", 0),
            comments=[Comments.from_dict(c) for c in data.get("comments", [])],
        )
