from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.post_service import PostService


def get_post_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PostService:
    return PostService(db=db, settings=settings)
