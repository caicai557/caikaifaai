#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def update_dockerfile() -> None:
    path = ROOT / "Dockerfile"
    content = read_text(path)
    old = 'pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir -e .'
    new = (
        'pip install --no-cache-dir -e ".[dev,distributed]" '
        "|| pip install --no-cache-dir -e ."
    )
    if old in content:
        content = content.replace(old, new, 1)
        write_text(path, content)


def update_compose() -> None:
    path = ROOT / "docker-compose.yml"
    content = read_text(path)
    if "caicai-redis" not in content:
        marker = "  # ==========================================================================\n  # 测试运行器沙箱"
        insert = """  # ==========================================================================
  # Distributed Queue - Redis
  # ==========================================================================
  redis:
    image: redis:7-alpine
    container_name: caicai-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]
    networks:
      - dev-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

  # ==========================================================================
  # Distributed Queue - RabbitMQ
  # ==========================================================================
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: caicai-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - dev-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

  # ==========================================================================
  # Celery Worker
  # ==========================================================================
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: caicai-celery-worker
    volumes:
      - ./:/app
      - /app/.venv
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    depends_on:
      - rabbitmq
      - redis
    networks:
      - dev-network
    command: celery -A council.distributed.tasks worker -l info

"""
        if marker not in content:
            raise ValueError("Marker not found for insertion in docker-compose.yml")
        content = content.replace(marker, insert + marker, 1)

    if "redis_data:" not in content:
        content = content.replace(
            "  test_results:\n    driver: local\n\nnetworks:",
            "  test_results:\n    driver: local\n  redis_data:\n"
            "    driver: local\n  rabbitmq_data:\n    driver: local\n\nnetworks:",
            1,
        )

    write_text(path, content)


def update_docs() -> None:
    path = ROOT / "docs" / "DOCKER_SANDBOX.md"
    content = read_text(path)
    if "分布式队列" in content:
        return
    marker = "#### 测试运行器（只读模式）"
    insert = """#### 分布式队列（Redis + RabbitMQ + Celery）
```bash
# 启动队列服务与 Worker
docker-compose up -d redis rabbitmq celery-worker

# 查看 Worker 日志
docker-compose logs -f celery-worker
```

RabbitMQ 管理面板: http://localhost:15672 (guest/guest)

"""
    if marker not in content:
        raise ValueError("Marker not found for docs insertion")
    content = content.replace(marker, insert + marker, 1)
    write_text(path, content)


def main() -> None:
    update_dockerfile()
    update_compose()
    update_docs()


if __name__ == "__main__":
    main()
