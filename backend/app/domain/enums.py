from enum import Enum


class Platform(str, Enum):
    LINKEDIN = "LINKEDIN"
    X = "X"


class PostStatus(str, Enum):
    DRAFT_CREATED = "DRAFT_CREATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SCHEDULED = "SCHEDULED"
    POSTED = "POSTED"


class ApprovalAction(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EDITED = "EDITED"


class PublishStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
