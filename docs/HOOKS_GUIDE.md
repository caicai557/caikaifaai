# Council Hooks 机制开发指南

> **版本**: 1.0.0
> **日期**: 2026-01-01

---

## 概述

Council Hooks 是一套在代理生命周期特定节点触发的确定性治理机制，实现 AI 执行力的安全约束。

## 核心钩子类型

| 钩子 | 触发时机 | 功能 |
|-----|---------|-----|
| **SessionStart** | 会话启动 | 环境初始化、状态恢复 |
| **PreToolUse** | 工具执行前 | 安全拦截、RBAC 检查 |
| **PostToolUse** | 工具执行后 | 代码质量门禁、自愈触发 |

---

## 快速开始

```python
from council.hooks import (
    HookManager,
    HookContext,
    HookType,
    SessionStartHook,
    PreToolUseHook,
    PostToolUseHook,
)

# 1. 创建管理器
manager = HookManager()

# 2. 注册钩子
manager.register(SessionStartHook(working_dir="."))
manager.register(PreToolUseHook())
manager.register(PostToolUseHook(enable_lint=True))

# 3. 创建上下文
context = HookContext(
    hook_type=HookType.PRE_TOOL_USE,
    session_id="my-session",
    agent_name="coder",
    tool_name="bash",
    tool_args={"command": "ls -la"},
)

# 4. 触发钩子
result = await manager.trigger_pre_tool(context)
if result.action == HookAction.BLOCK:
    print(f"Blocked: {result.message}")
```

---

## 安全规则

### PreToolUseHook 拦截规则

**危险命令** (硬性阻止):
- `rm -rf /`
- `dd if=`
- `mkfs`
- `DROP TABLE`
- `eval()` / `exec()`

**敏感路径** (禁止访问):
- `.ssh/`
- `.env*`
- `secrets/`
- `/etc/passwd`

### sudo_token 授权

危险操作可通过 sudo_token 授权：

```python
hook = PreToolUseHook(sudo_token="my-secret-token")
# 或动态设置
hook.set_sudo_token("authorized")
```

---

## 质量门禁配置

```python
hook = PostToolUseHook(
    working_dir=".",
    enable_format=True,   # ruff format
    enable_lint=True,     # ruff check
    enable_test=False,    # pytest (默认关闭)
    max_retries=3,        # 自愈最大重试次数
)
```

---

## API 参考

### HookResult

```python
@dataclass
class HookResult:
    action: HookAction     # ALLOW | BLOCK | MODIFY | RETRY
    message: str
    metadata: Dict[str, Any]
    error: Optional[str]
```

### HookContext

```python
@dataclass
class HookContext:
    hook_type: HookType
    session_id: str
    agent_name: str
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    working_dir: str
```

---

## 相关文档

- [CLAUDE.md](../CLAUDE.md) - 项目规范
- [AGENTS.md](../AGENTS.md) - Agent 权限矩阵
