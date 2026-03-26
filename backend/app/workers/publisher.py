import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.post_service import PostService

settings = get_settings()
configure_logging(settings.log_level)


def publish_post_job(post_id: str) -> None:
    db = SessionLocal()
    try:
        service = PostService(db=db, settings=settings)
        asyncio.run(service.publish_post(post_id))
    finally:
        db.close()
