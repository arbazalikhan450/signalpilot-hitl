from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.domain.enums import ApprovalAction, Platform, PostStatus, PublishStatus


class GeneratePostRequest(BaseModel):
    user_id: str
    topic: str = Field(min_length=3, max_length=255)
    tone: str = Field(min_length=2, max_length=100)
    platform: Platform
    schedule_for: Optional[datetime] = None


class PostResponse(BaseModel):
    id: str
    user_id: str
    topic: str
    tone: str
    platform: Platform
    content: str
    status: PostStatus
    scheduled_for: Optional[datetime]
    posted_at: Optional[datetime]
    llm_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    post_id: str
    reviewer_id: str
    notes: Optional[str] = None
    edited_content: Optional[str] = None
    schedule_for: Optional[datetime] = None


class RejectRequest(BaseModel):
    post_id: str
    reviewer_id: str
    notes: Optional[str] = None


class PublishRequest(BaseModel):
    post_id: str


class ApprovalResponse(BaseModel):
    id: str
    post_id: str
    reviewer_id: str
    action: ApprovalAction
    notes: Optional[str]
    edited_content: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PublishLogResponse(BaseModel):
    id: str
    post_id: str
    platform: Platform
    status: PublishStatus
    response_payload: dict[str, Any]
    error_message: Optional[str]
    attempt_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthStartResponse(BaseModel):
    authorization_url: str
    state: str


class PostListResponse(BaseModel):
    items: list[PostResponse]
