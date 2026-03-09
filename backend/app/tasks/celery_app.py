from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "leadflow",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.agent_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    "outbound-email-agent": {
        "task": "app.tasks.agent_tasks.run_outbound_email_agent",
        "schedule": settings.AGENT_OUTBOUND_INTERVAL_SECONDS,
    },
    "reply-handler-agent": {
        "task": "app.tasks.agent_tasks.run_reply_handler_agent",
        "schedule": settings.AGENT_REPLY_HANDLER_INTERVAL_SECONDS,
    },
    "lead-scoring-agent": {
        "task": "app.tasks.agent_tasks.run_lead_scoring_agent",
        "schedule": settings.AGENT_SCORING_INTERVAL_SECONDS,
    },
    "daily-send-counter-reset": {
        "task": "app.tasks.agent_tasks.reset_daily_send_counts",
        "schedule": crontab(hour=0, minute=0),
    },
}
