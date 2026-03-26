from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_post_service
from app.domain.enums import PostStatus
from app.domain.schemas import ApprovalRequest, GeneratePostRequest, PostListResponse, PostResponse, PublishRequest, RejectRequest
from app.services.post_service import PostService

router = APIRouter(tags=["posts"])


@router.post("/generate-post", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def generate_post(payload: GeneratePostRequest, service: PostService = Depends(get_post_service)) -> PostResponse:
    try:
        return PostResponse.model_validate(service.generate_post(payload))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/posts", response_model=PostListResponse)
def get_posts(
    status_filter: Optional[PostStatus] = Query(default=None, alias="status"),
    service: PostService = Depends(get_post_service),
) -> PostListResponse:
    posts = service.list_posts(status_filter)
    return PostListResponse(items=[PostResponse.model_validate(post) for post in posts])


@router.post("/approve", response_model=PostResponse)
def approve_post(payload: ApprovalRequest, service: PostService = Depends(get_post_service)) -> PostResponse:
    try:
        return PostResponse.model_validate(service.approve_post(payload))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reject", response_model=PostResponse)
def reject_post(payload: RejectRequest, service: PostService = Depends(get_post_service)) -> PostResponse:
    try:
        return PostResponse.model_validate(service.reject_post(payload))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/publish", status_code=status.HTTP_202_ACCEPTED)
def publish_post(payload: PublishRequest, service: PostService = Depends(get_post_service)) -> dict[str, str]:
    try:
        service.enqueue_publish(payload.post_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Publish job queued."}
