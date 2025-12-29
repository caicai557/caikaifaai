# Docker 沙箱使用指南

## 目的
提供隔离的开发环境，防止智能体生成的代码对宿主机造成危害（如 `rm -rf /` 等危险操作）。

## 快速开始

### 1. 启动沙箱
```bash
# 启动所有沙箱容器
docker-compose up -d

# 检查状态
docker-compose ps
```

### 2. 在沙箱中执行命令

#### Node.js 沙箱
```bash
# 进入容器
docker-compose exec nodejs-sandbox sh

# 安装依赖
docker-compose exec nodejs-sandbox pnpm install

# 运行测试
docker-compose exec nodejs-sandbox pnpm test

# 运行构建
docker-compose exec nodejs-sandbox pnpm build
```

#### Python 沙箱
```bash
# 执行 Python 脚本
docker-compose exec python-sandbox python tools/batch_executor.py config.yaml

# 安装 Python 依赖
docker-compose exec python-sandbox pip install -r requirements.txt
```

#### PTC Runner 沙箱选择
```bash
# 使用 Docker 沙箱
PTC_SANDBOX_PROVIDER=docker python scripts/ptc_runner.py --code 'print("hello")'

# 使用 E2B 沙箱 (需要 E2B_API_KEY)
E2B_API_KEY=your_key PTC_SANDBOX_PROVIDER=e2b \
  python scripts/ptc_runner.py --code 'print("hello")'

# 使用本地沙箱
PTC_SANDBOX_PROVIDER=local python scripts/ptc_runner.py --code 'print("hello")'
```

#### 分布式队列（Redis + RabbitMQ + Celery）
```bash
# 启动队列服务与 Worker
docker-compose up -d redis rabbitmq celery-worker

# 查看 Worker 日志
docker-compose logs -f celery-worker
```

RabbitMQ 管理面板: http://localhost:15672 (guest/guest)

#### 测试运行器（只读模式）
```bash
# 运行测试（安全的只读模式）
docker-compose run --rm test-runner pnpm test -- --coverage
```

### 3. 停止沙箱
```bash
# 停止所有容器
docker-compose down

# 清理所有数据（包括 volumes）
docker-compose down -v
```

## 安全特性

### ✅ 容器隔离
- 每个沙箱运行在独立的容器中
- 使用 bridge 网络隔离
- 最小化容器权限（cap_drop: ALL）

### ✅ 文件系统保护
- 敏感文件（.env, .secrets）通过 volume 排除
- 测试运行器使用只读挂载
- 使用 tmpfs 存储临时文件

### ✅ 权限限制
- no-new-privileges 防止权限升级
- 移除所有 Linux capabilities
- 仅添加必要的最小权限（CHOWN, SETUID 等）

## 工作流集成

### 六步自愈循环中的使用

```bash
# Step 1: PRD 生成（宿主机）
/prd_generate "功能描述"

# Step 2: 架构审计（宿主机）
/audit_design "架构审计"

# Step 3: TDD 测试（宿主机）
/tdd_tests "生成测试"

# Step 4: 批量执行（沙箱中）
docker-compose exec python-sandbox python tools/batch_executor.py plan.yaml

# Step 5: 自愈校验（沙箱中）
docker-compose exec nodejs-sandbox pnpm test -- --coverage

# Step 6: 检查点（宿主机）
/checkpoint "任务完成"
```

## 智能体命令包装

### 创建沙箱别名
在 `~/.bashrc` 或 `.claude/settings.json` 中添加：

```bash
# 沙箱命令别名
alias pnpm-safe="docker-compose exec nodejs-sandbox pnpm"
alias npm-safe="docker-compose exec nodejs-sandbox npm"
alias python-safe="docker-compose exec python-sandbox python"
alias test-safe="docker-compose run --rm test-runner pnpm test"
```

### 在 AGENTS.md 中强制使用
更新规则：
```markdown
## 安全约束（强制）
- 所有 npm/pnpm 命令 → 使用 pnpm-safe 别名
- 所有 python 脚本 → 使用 python-safe 别名
- 所有测试运行 → 使用 test-safe 别名
```

## 故障排查

### 容器无法启动
```bash
# 查看日志
docker-compose logs nodejs-sandbox

# 重建容器
docker-compose up -d --force-recreate nodejs-sandbox
```

### 文件权限问题
```bash
# 在容器中修复权限
docker-compose exec nodejs-sandbox chown -R node:node /workspace
```

### 依赖安装失败
```bash
# 清理 node_modules volume 重新安装
docker-compose down -v
docker-compose up -d
docker-compose exec nodejs-sandbox pnpm install
```

## 性能优化

### 使用命名 volumes
- `node_modules` volume 持久化依赖，避免重复安装
- `test_results` volume 保存测试结果

### 减少镜像大小
- 使用 alpine 基础镜像
- 多阶段构建（如需生产镜像）

## 限制与注意事项

### ⚠️  不适用场景
- 需要访问宿主机 GPU 的任务
- 需要特权模式的操作（如 Docker-in-Docker）
- 需要访问宿主机硬件设备

### ✅ 最佳实践
- 定期清理未使用的 volumes: `docker volume prune`
- 监控容器资源使用: `docker stats`
- 在 CI/CD 中使用相同的沙箱环境

## 扩展配置

### 添加数据库沙箱
在 `docker-compose.yml` 中添加：
```yaml
postgres-sandbox:
  image: postgres:15-alpine
  environment:
    POSTGRES_PASSWORD: dev_password_only
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - dev-network
```

### 添加 Redis 沙箱
```yaml
redis-sandbox:
  image: redis:7-alpine
  networks:
    - dev-network
```
