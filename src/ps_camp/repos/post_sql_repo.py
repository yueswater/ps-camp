from uuid import UUID
from sqlalchemy.orm import Session
from ps_camp.sql_models.post_model import Post


class PostSQLRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, post: Post) -> Post:
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_by_id(self, post_id: UUID) -> Post | None:
        return self.db.query(Post).filter(Post.id == post_id).first()

    def get_all(self) -> list[Post]:
        return self.db.query(Post).all()

    def delete(self, post_id: str) -> None:
        post = self.get_by_id(post_id)
        if post:
            self.db.delete(post)
            self.db.commit()
