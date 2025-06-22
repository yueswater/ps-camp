from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ps_camp.models.post import Post


class PostRepository(ABC):
    @abstractmethod
    def add(self, post: Post) -> None:
        pass

    @abstractmethod
    def delete(self, post_id: UUID) -> None:
        pass

    @abstractmethod
    def update(self, post: Post, update_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_by_post_id(self, post_id: UUID) -> Optional[Post]:
        pass

    @abstractmethod
    def get_by_post_title(self, title: str) -> List[Post]:
        pass

    @abstractmethod
    def search(self, keyword: str) -> List[Post]:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_all(self) -> List[Post]:
        pass
