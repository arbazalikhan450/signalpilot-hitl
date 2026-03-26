from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.metrics import POST_GENERATION_COUNTER, PUBLISH_COUNTER, WORKFLOW_DURATION
from app.core.security import TokenCipher
from app.db.models import Approval, Post, PublishLog, SocialAccount
from app.domain.enums import ApprovalAction, Platform, PostStatus, PublishStatus
from app.domain.schemas import ApprovalRequest, GeneratePostRequest, RejectRequest
from app.integrations.oauth import OAuthTokens
from app.integrations.social_clients import get_publisher
from app.services.llm import LLMPostGenerator
from app.services.queue import publish_queue
from app.services.repositories import (
    ApprovalRepository,
    PostRepository,
    PublishLogRepository,
    SocialAccountRepository,
    UserRepository,
)
from app.workflows.post_workflow import apply_review_transition, build_post_workflow

logger = structlog.get_logger(__name__)


class PostService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.user_repo = UserRepository(db)
        self.post_repo = PostRepository(db)
        self.approval_repo = ApprovalRepository(db)
        self.publish_log_repo = PublishLogRepository(db)
        self.social_account_repo = SocialAccountRepository(db)
        self.llm = LLMPostGenerator(settings)
        self.cipher = TokenCipher(settings.token_encryption_key)
        self.workflow = build_post_workflow()

    def generate_post(self, payload: GeneratePostRequest) -> Post:
        with WORKFLOW_DURATION.labels("generate_post").time():
            self.user_repo.get_or_create_demo_user(payload.user_id)
            generated = self.llm.generate(payload.topic, payload.tone, payload.platform)
            workflow_state = self.workflow.invoke({"scheduled_for": payload.schedule_for})
            post = Post(
                user_id=payload.user_id,
                platform=payload.platform,
                topic=payload.topic,
                tone=payload.tone,
                content=generated.content,
                status=PostStatus(workflow_state["status"]),
                scheduled_for=payload.schedule_for,
                llm_metadata=generated.metadata,
            )
            saved = self.post_repo.add(post)
            self.db.commit()
            POST_GENERATION_COUNTER.labels(platform=payload.platform.value, status="success").inc()
            logger.info("post_generated", post_id=saved.id, platform=payload.platform.value)
            return saved

    def list_posts(self, status: Optional[PostStatus] = None) -> list[Post]:
        return self.post_repo.list_posts(status=status)

    def approve_post(self, payload: ApprovalRequest) -> Post:
        post = self._require_post(payload.post_id)
        self.user_repo.get_or_create_demo_user(payload.reviewer_id)
        edited_content = payload.edited_content.strip() if payload.edited_content else None
        if edited_content:
            post.content = edited_content

        transition = apply_review_transition(PostStatus.APPROVED, payload.schedule_for or post.scheduled_for)
        post.status = PostStatus(transition["status"])
        post.scheduled_for = transition.get("scheduled_for")

        approval = Approval(
            post_id=post.id,
            reviewer_id=payload.reviewer_id,
            action=ApprovalAction.EDITED if edited_content else ApprovalAction.APPROVED,
            notes=payload.notes,
            edited_content=edited_content,
        )
        self.approval_repo.add(approval)
        self.db.commit()
        self.db.refresh(post)
        if post.status == PostStatus.APPROVED:
            publish_queue.enqueue("app.workers.publisher.publish_post_job", post.id)
        logger.info("post_approved", post_id=post.id, scheduled_for=str(post.scheduled_for))
        return post

    def reject_post(self, payload: RejectRequest) -> Post:
        post = self._require_post(payload.post_id)
        self.user_repo.get_or_create_demo_user(payload.reviewer_id)
        transition = apply_review_transition(PostStatus.REJECTED, post.scheduled_for)
        post.status = PostStatus(transition["status"])
        approval = Approval(
            post_id=post.id,
            reviewer_id=payload.reviewer_id,
            action=ApprovalAction.REJECTED,
            notes=payload.notes,
        )
        self.approval_repo.add(approval)
        self.db.commit()
        self.db.refresh(post)
        logger.info("post_rejected", post_id=post.id)
        return post

    def enqueue_publish(self, post_id: str) -> None:
        publish_queue.enqueue("app.workers.publisher.publish_post_job", post_id)

    async def publish_post(self, post_id: str) -> PublishLog:
        post = self._require_post(post_id)
        if post.status not in {PostStatus.APPROVED, PostStatus.SCHEDULED}:
            raise ValueError(f"Post {post_id} is not ready for publishing.")
        if post.scheduled_for and post.scheduled_for > datetime.utcnow():
            raise ValueError(f"Post {post_id} is scheduled for the future.")

        account = self.social_account_repo.get_for_user_platform(post.user_id, post.platform)
        if not account:
            raise ValueError(f"No connected {post.platform.value} account for user {post.user_id}.")

        publisher = get_publisher(post.platform, self.settings)
        access_token = self.cipher.decrypt(account.access_token_encrypted) or ""
        attempt = len(post.publish_logs) + 1

        try:
            result = await publisher.publish(access_token, post.content, account.account_identifier)
            post.status = PostStatus.POSTED
            post.posted_at = datetime.utcnow()
            log = PublishLog(
                post_id=post.id,
                platform=post.platform,
                status=PublishStatus.SUCCESS,
                response_payload=result.payload,
                attempt_number=attempt,
            )
            PUBLISH_COUNTER.labels(platform=post.platform.value, status="success").inc()
        except Exception as exc:
            log = PublishLog(
                post_id=post.id,
                platform=post.platform,
                status=PublishStatus.FAILED,
                response_payload={},
                error_message=str(exc),
                attempt_number=attempt,
            )
            PUBLISH_COUNTER.labels(platform=post.platform.value, status="failed").inc()
            logger.exception("post_publish_failed", post_id=post.id)
        self.publish_log_repo.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def upsert_social_account(self, user_id: str, platform: Platform, account_identifier: str, tokens: OAuthTokens) -> SocialAccount:
        self.user_repo.get_or_create_demo_user(user_id)
        account = self.social_account_repo.get_for_user_platform(user_id, platform)
        encrypted_access = self.cipher.encrypt(tokens.access_token)
        encrypted_refresh = self.cipher.encrypt(tokens.refresh_token) if tokens.refresh_token else None
        if account:
            account.access_token_encrypted = encrypted_access
            account.refresh_token_encrypted = encrypted_refresh
            account.token_expires_at = tokens.expires_at
            account.metadata_json = tokens.metadata
            account.account_identifier = account_identifier
        else:
            account = SocialAccount(
                user_id=user_id,
                platform=platform,
                account_identifier=account_identifier,
                access_token_encrypted=encrypted_access,
                refresh_token_encrypted=encrypted_refresh,
                token_expires_at=tokens.expires_at,
                metadata_json=tokens.metadata,
            )
            self.social_account_repo.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def _require_post(self, post_id: str) -> Post:
        post = self.post_repo.get(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found.")
        return post
