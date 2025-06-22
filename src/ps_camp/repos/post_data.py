from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ps_camp.models.post import Post
from ps_camp.repos.post_repo import PostRepository


class PostData(PostRepository):
    def __init__(self):
        # Internal in-memory storage for posts
        self.post_repo: Dict[UUID, Post] = {}

    def add(self, post: Post) -> None:
        if post.post_id in self.post_repo:
            raise ValueError("文章已存在於列表中")
        self.post_repo[post.post_id] = post

    def delete(self, post_id: UUID) -> None:
        if post_id not in self.post_repo:
            raise ValueError("查無此文章！")
        del self.post_repo[post_id]

    def update(self, post: Post, update_data: Dict[str, Any]) -> None:
        if post.post_id not in self.post_repo:
            raise ValueError("查無此文章！")

        # Apply updates to the existing post
        for k, v in update_data.items():
            if hasattr(post, k):
                setattr(post, k, v)

    def get_all(self) -> List[Post]:
        return list(self.post_repo.values())

    def get_by_post_id(self, post_id: UUID) -> Optional[Post]:
        return self.post_repo.get(post_id)

    def get_by_post_title(self, title: str) -> List[Post]:
        return [post for post in self.post_repo.values() if title in post.title]

    def search(self, keyword: str) -> List[Post]:
        # Search across multiple fields
        return [
            post
            for post in self.post_repo.values()
            if keyword in post.title
            or keyword in post.content
            or any(keyword in cat for cat in post.category)
        ]

    def filter(
        self,
        title: Optional[str] = None,
        category: Optional[str] = None,
        created_by: Optional[str] = None,
        created_at: Optional[datetime] = None,
        content: Optional[str] = None,
        likes: Optional[int] = None,
        dislikes: Optional[int] = None,
        comments: Optional[str] = None,
    ) -> List[Post]:
        result = list(self.post_repo.values())

        # Apply filtering based on non-None fields
        if title:
            result = [p for p in result if title in p.title]
        if category:
            result = [p for p in result if category in p.category]
        if created_by:
            result = [p for p in result if created_by in p.created_by.partyname]
        if created_at:
            result = [p for p in result if p.created_at.date() == created_at.date()]
        if content:
            result = [p for p in result if content in p.content]
        if likes is not None:
            result = [p for p in result if p.likes >= likes]
        if dislikes is not None:
            result = [p for p in result if p.dislikes >= dislikes]
        if comments:
            result = [
                p
                for p in result
                if any(comments in c.comment_content for c in p.comments)
            ]

        return result
