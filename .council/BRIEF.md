# BRIEF (Single Source of Truth)

> 当前开发任务的单一事实来源

## 项目

**cesi-telegram-multi**: Telegram Web A 多开 + 双向自动翻译 + CLI 架构重构

## 当前任务

**CLI 重构修复与完善：修复高风险项、补充测试覆盖、向后兼容**

## 问题陈述

**当前状态**（基于 2025-12-27 /review 报告）:
- 🔴 **核心功能回归**: `BrowserContext.start()` 是 stub，不会真正启动浏览器
- 🔴 **生命周期缺陷**: CLI 启动后无 keep-alive，进程立即退出
- 🟡 **兼容性破坏**: 旧 CLI 参数 `--instances/-n, --source/-s` 完全失效
- 🟢 **退出码语义**: 失败场景返回 0，自动化无法识别
- 📊 **测试覆盖不足**: 67% < 90% 目标（cli_main.py 0%, browser_context.py 73%）

**目标状态**:
1. ✅ **核心功能恢复**: `BrowserContext.start()` 抛出 `NotImplementedError`（明确标识未实现）
2. ✅ **生命周期管理**: `launch` 命令添加 keep-alive（等待 KeyboardInterrupt）
3. ✅ **向后兼容**: 添加旧参数兼容层或清晰迁移提示
4. ✅ **退出码规范**: 失败场景返回非 0 退出码
5. ✅ **测试覆盖**: cli_main.py 达到 90%+ 覆盖率

**非目标**:
- ❌ 不实现完整的 Playwright 启动逻辑（Phase 5 任务）
- ❌ 不重构现有 run_telegram.py 的旧逻辑（仅兼容层）
- ❌ 不修改其他模块的测试覆盖率（聚焦 CLI 模块）

## 用户故事

### US1: 明确未实现状态（核心功能标识）
**作为** 开发者，
**我希望** `BrowserContext.start()` 抛出 `NotImplementedError`，
**以便** 明确知道这是 stub 而非可用功能。

**验收标准**:
- [ ] AC1.1: `BrowserContext.start()` 抛出 `NotImplementedError("BrowserContext.start() not implemented - use Phase 5 launcher")`
- [ ] AC1.2: 相关测试捕获该异常并验证消息内容
- [ ] AC1.3: `launch` 命令调用时向用户展示清晰错误

### US2: 进程生命周期管理（Keep-Alive）
**作为** 用户，
**我希望** `launch` 命令启动后保持运行直到 Ctrl+C，
**以便** 浏览器实例持续运行（当 start() 实现后）。

**验收标准**:
- [ ] AC2.1: `launch_instances` 添加无限循环等待 KeyboardInterrupt
- [ ] AC2.2: Ctrl+C 优雅退出并打印 "Stopped by user"
- [ ] AC2.3: 异常退出时返回非 0 退出码

### US3: 向后兼容（迁移提示）
**作为** 旧版用户，
**我希望** 使用 `--instances` 参数时看到清晰的迁移指南，
**以便** 快速了解新 CLI 用法。

**验收标准**:
- [ ] AC3.1: 检测到旧参数时打印迁移提示（不失败）
- [ ] AC3.2: 提示包含示例命令和配置文件模板
- [ ] AC3.3: 提供快速启动命令（如 `python run_telegram.py launch --all`）

### US4: 退出码规范化
**作为** 自动化脚本，
**我希望** CLI 在失败时返回非 0 退出码，
**以便** 准确检测执行状态。

**验收标准**:
- [ ] AC4.1: 实例不存在时 `sys.exit(1)`
- [ ] AC4.2: 配置加载失败时 `sys.exit(1)`
- [ ] AC4.3: `launch_instances` 抛出异常时传播到 `cli_main`

### US5: 测试覆盖完善
**作为** 质量守门员，
**我希望** cli_main.py 测试覆盖率 ≥ 90%，
**以便** 保证 CLI 核心逻辑的可靠性。

**验收标准**:
- [ ] AC5.1: 新增 `tests/test_cli_main.py` 覆盖命令分发逻辑
- [ ] AC5.2: 测试 `check` 命令成功/失败路径
- [ ] AC5.3: 测试 `launch` 命令异常处理
- [ ] AC5.4: 总覆盖率从 67% → 90%+

## 任务树

```
Phase: CLI 重构修复 (6 个子任务)
├── 6.1 [browser_context.py] 修改 start() 抛出 NotImplementedError (简单)
│   └── 影响: src/telegram_multi/browser_context.py:33-44
│   └── 测试: tests/test_browser_context.py (新增异常测试)
│
├── 6.2 [launch.py] 添加 keep-alive 生命周期管理 (简单)
│   └── 影响: src/telegram_multi/cli/commands/launch.py:38-50
│   └── 测试: tests/test_cli_launch.py (新增 KeyboardInterrupt 测试)
│
├── 6.3 [cli_main.py] 修复退出码语义 (简单)
│   └── 影响: src/telegram_multi/cli/cli_main.py:30-32, launch.py:26-32
│   └── 测试: tests/test_cli_main.py (新增退出码测试)
│
├── 6.4 [run_telegram.py, parser.py] 添加旧参数兼容层 (中等)
│   └── 影响: run_telegram.py:1-15, cli/parser.py:5-25
│   └── 测试: tests/test_cli_parser.py (新增兼容测试)
│
├── 6.5 [test_cli_main.py] 新增 CLI 主入口测试 (中等)
│   └── 影响: tests/test_cli_main.py (新建)
│   └── 覆盖: check/launch/list/stop 命令分发逻辑
│
└── 6.6 [verify] 验证覆盖率 ≥ 90% (简单)
    └── 运行: just verify
    └── 目标: 总覆盖率 67% → 90%+
```

## 技术设计方案

### 6.1 修改 `BrowserContext.start()`

```python
# src/telegram_multi/browser_context.py:33
async def start(self) -> None:
    """Launch the browser instance (Not Implemented).

    Raises:
        NotImplementedError: Actual Playwright launch logic pending Phase 5.
    """
    raise NotImplementedError(
        f"BrowserContext.start() not implemented for instance '{self.instance_id}'. "
        "This is a stub. Implement Playwright launch logic in Phase 5."
    )
```

### 6.2 添加 Keep-Alive

```python
# src/telegram_multi/cli/commands/launch.py:44
async def launch_instances(...) -> None:
    ...
    try:
        await asyncio.gather(*tasks)
        print("✨ All requested instances launched.")

        # Keep-alive: Wait until user interrupts
        print("Press Ctrl+C to stop all instances...")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    except Exception as e:
        print(f"❌ Error during launch: {e}")
        raise  # Propagate to cli_main for non-0 exit
```

### 6.3 退出码修复

```python
# src/telegram_multi/cli/cli_main.py:30
if args.command == "launch":
    try:
        await launch_instances(config, instance_id=args.instance, launch_all=args.all)
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        sys.exit(1)

# src/telegram_multi/cli/commands/launch.py:31
else:
    print(f"❌ Error: Instance '{instance_id}' not found in config.")
    sys.exit(1)  # Changed from return
```

### 6.4 旧参数兼容层

```python
# run_telegram.py (新增兼容检测)
import sys
if len(sys.argv) > 1 and sys.argv[1].startswith("--"):
    print("⚠️  旧 CLI 参数已弃用。请使用新命令:")
    print("   python run_telegram.py launch --all")
    print("   或配置文件: python run_telegram.py --config telegram.yaml launch --all")
    print("\n示例配置文件 (telegram.yaml):")
    print("  instances:")
    print("    - id: account1")
    print("      profile_path: ~/.telegram_profiles/account1")
    sys.exit(1)

from src.telegram_multi.cli.cli_main import main
asyncio.run(main())
```

## 模型分发

| 阶段 | 任务 | 模型 | 原因 | 占比 |
|------|------|------|------|:----:|
| **TDD** | 6.1 browser_context stub | Gemini Flash | 简单异常测试 | 10% |
| **实现** | 6.1 NotImplementedError | Gemini Flash | 简单修改 | 5% |
| **TDD** | 6.2 keep-alive 测试 | Gemini Flash | 异步生命周期测试 | 10% |
| **实现** | 6.2 keep-alive 逻辑 | Gemini Flash | 简单 while 循环 | 5% |
| **TDD** | 6.3 退出码测试 | Gemini Flash | CLI 集成测试 | 15% |
| **实现** | 6.3 退出码修复 | Gemini Flash | 简单修改 | 5% |
| **TDD** | 6.4 兼容层测试 | Gemini Flash | CLI 参数测试 | 10% |
| **实现** | 6.4 兼容层实现 | Gemini Flash | 简单参数检测 | 10% |
| **TDD** | 6.5 cli_main 测试 | Gemini Flash | 命令分发测试 | 15% |
| **实现** | 6.5 无需实现 | - | 仅测试 | 0% |
| **验证** | 6.6 verify | - | just verify | 5% |
| **审查** | 全部 | **Codex 5.2** | 代码质量把关 | 10% |

**总结**: 全程使用 **Gemini Flash** (90%) + **Codex 审查** (10%)

## 下游命令序列

```bash
# 1. 修复核心 stub (6.1)
/tdd "6.1 browser_context NotImplementedError"
/impl "6.1 browser_context NotImplementedError"

# 2. 生命周期管理 (6.2)
/tdd "6.2 launch keep-alive"
/impl "6.2 launch keep-alive"

# 3. 退出码规范 (6.3)
/tdd "6.3 CLI 退出码"
/impl "6.3 CLI 退出码"

# 4. 兼容层 (6.4)
/tdd "6.4 旧参数兼容"
/impl "6.4 旧参数兼容"

# 5. CLI 主入口测试 (6.5)
/tdd "6.5 cli_main 测试覆盖"

# 6. 验证
just verify

# 7. 审查
/review
```

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Keep-alive 阻塞测试运行 | 高 | 中 | 测试使用 `asyncio.wait_for` 限时 |
| 兼容层检测误报（误判新参数） | 中 | 低 | 精确匹配旧参数列表 (`--instances`, `--source`, `--target`) |
| NotImplementedError 导致现有测试失败 | 高 | 高 | 先修改测试，再修改代码（TDD） |
| 退出码修复影响现有流程 | 低 | 低 | `cli_main` 仅在失败时 `sys.exit(1)` |
