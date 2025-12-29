from typing import Optional

from council.distributed.config import CeleryConfig

try:
    from celery import Celery

    HAS_CELERY = True
except ImportError:  # pragma: no cover - depends on optional dependency
    Celery = None
    HAS_CELERY = False


def make_celery_app(name: str = "council", config: Optional[CeleryConfig] = None):
    if not HAS_CELERY:
        raise ImportError("celery is required. Install with: pip install celery")

    cfg = config or CeleryConfig()
    app = Celery(name, broker=cfg.broker_url, backend=cfg.result_backend)
    app.conf.update(
        task_serializer=cfg.task_serializer,
        result_serializer=cfg.result_serializer,
        accept_content=list(cfg.accept_content),
        timezone=cfg.timezone,
        enable_utc=cfg.enable_utc,
        task_track_started=True,
        broker_connection_retry_on_startup=True,
    )
    return app
