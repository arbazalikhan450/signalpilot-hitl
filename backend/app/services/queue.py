from redis import Redis
from rq import Queue

from app.core.config import get_settings

settings = get_settings()
redis_conn = Redis.from_url(settings.redis_url)
publish_queue = Queue("publish", connection=redis_conn, default_timeout=300)
