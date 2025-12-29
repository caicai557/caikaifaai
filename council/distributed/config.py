from dataclasses import dataclass
import os
from typing import Tuple


@dataclass
class CeleryConfig:
    broker_url: str = os.environ.get(
        "CELERY_BROKER_URL",
        "amqp://guest:guest@localhost:5672//",
    )
    result_backend: str = os.environ.get(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/0",
    )
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: Tuple[str, ...] = ("json",)
    timezone: str = "UTC"
    enable_utc: bool = True

    def to_dict(self) -> dict:
        return {
            "broker_url": self.broker_url,
            "result_backend": self.result_backend,
            "task_serializer": self.task_serializer,
            "result_serializer": self.result_serializer,
            "accept_content": list(self.accept_content),
            "timezone": self.timezone,
            "enable_utc": self.enable_utc,
        }
