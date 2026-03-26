from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_post_service
from app.core.config import Settings, get_settings
from app.domain.enums import Platform
from app.domain.schemas import OAuthStartResponse
from app.integrations.oauth import OAuthService
from app.services.post_service import PostService

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get("/{platform}/start", response_model=OAuthStartResponse)
def start_oauth(
    platform: Platform,
    user_id: str = Query(...),
    settings: Settings = Depends(get_settings),
) -> OAuthStartResponse:
    service = OAuthService(settings)
    url, state = service.create_authorization_url(platform, user_id)
    return OAuthStartResponse(authorization_url=url, state=state)


@router.get("/x/callback")
async def x_callback(
    code: str,
    state: str,
    service: PostService = Depends(get_post_service),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    try:
        user_id = state.split(":", 1)[0]
        oauth = OAuthService(settings)
        tokens = await oauth.exchange_code(Platform.X, code)
        service.upsert_social_account(user_id, Platform.X, account_identifier="me", tokens=tokens)
        return {"message": "X account connected.", "user_id": user_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str,
    state: str,
    service: PostService = Depends(get_post_service),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    try:
        user_id = state.split(":", 1)[0]
        oauth = OAuthService(settings)
        tokens = await oauth.exchange_code(Platform.LINKEDIN, code)
        service.upsert_social_account(user_id, Platform.LINKEDIN, account_identifier="me", tokens=tokens)
        return {"message": "LinkedIn account connected.", "user_id": user_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
