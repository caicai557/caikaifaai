"""
Tests for distributed queue configuration.
"""

import pytest


def test_celery_config_defaults():
    from council.distributed.config import CeleryConfig

    cfg = CeleryConfig()
    assert "amqp://" in cfg.broker_url or "redis://" in cfg.broker_url
    assert cfg.result_backend


def test_make_celery_app():
    from council.distributed.celery_app import HAS_CELERY, make_celery_app

    if not HAS_CELERY:
        pytest.skip("Celery not installed")

    app = make_celery_app("council-test")
    assert app.main == "council-test"
