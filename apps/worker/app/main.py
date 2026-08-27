from celery import Celery
from apps.api.app.core.config import settings
celery_app = Celery("business_brain", broker=settings.redis_url)
