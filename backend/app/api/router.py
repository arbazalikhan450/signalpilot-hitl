from fastapi import APIRouter

from app.api.routes.oauth import router as oauth_router
from app.api.routes.posts import router as posts_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(posts_router)
api_router.include_router(oauth_router)
