from celery import Celery
from backend.app.core.config import get_settings
settings = get_settings()

celery_app = Celery(
    "rod_calc",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL
)

celery_app.conf.update(
    task_routes={
        "backend.app.tasks.calc_rod": {"queue": "rod"}
    },
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
) 