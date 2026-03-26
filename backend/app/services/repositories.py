from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Approval, Post, PublishLog, SocialAccount, User
from app.domain.enums import Platform, PostStatus


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: str) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_or_create_demo_user(self, user_id: str) -> User:
        user = self.get(user_id)
        if user:
            return user
        user = User(id=user_id, email=f"{user_id}@example.com", full_name="Demo Reviewer")
        self.db.add(user)
        self.db.flush()
        return user


class PostRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, post: Post) -> Post:
        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)
        return post

    def get(self, post_id: str) -> Optional[Post]:
        return self.db.get(Post, post_id)

    def list_posts(self, status: Optional[PostStatus] = None) -> list[Post]:
        query = select(Post).order_by(Post.created_at.desc())
        if status:
            query = query.where(Post.status == status)
        return list(self.db.scalars(query).all())


class ApprovalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, approval: Approval) -> Approval:
        self.db.add(approval)
        self.db.flush()
        self.db.refresh(approval)
        return approval


class PublishLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, log: PublishLog) -> PublishLog:
        self.db.add(log)
        self.db.flush()
        self.db.refresh(log)
        return log


class SocialAccountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_user_platform(self, user_id: str, platform: Platform) -> Optional[SocialAccount]:
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.platform == platform,
        )
        return self.db.scalar(query)

    def add(self, account: SocialAccount) -> SocialAccount:
        self.db.add(account)
        self.db.flush()
        self.db.refresh(account)
        return account
