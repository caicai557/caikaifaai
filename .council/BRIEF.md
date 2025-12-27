# BRIEF (Single Source of Truth)

> 当前开发任务的单一事实来源

## 项目

**cesi-telegram-multi**: Telegram Web A 多开 + 双向自动翻译 + 智能自动化

## 当前任务

**Telegram 自动化功能增强：关键词监听、自定义延时、自动回复、一键建群**

## 问题陈述

- **当前状态**: Telegram 多开仅支持消息拦截与翻译，缺少自动化运营能力
  - 用户需手动监控关键词触发的消息
  - 无法自定义回复延迟（避免机器人检测）
  - 无法自动回复特定消息（如客户咨询）
  - 无法批量创建群组（运营场景）

- **目标状态**:
  - 关键词监听：自动检测指定关键词并触发回调
  - 自定义延时：模拟人工打字延迟（可配置范围，如 2-5 秒）
  - 自动回复：根据规则库自动响应消息
  - 一键建群：批量创建 Telegram 群组（支持模板配置）

- **非目标**:
  - 不做机器学习/AI 智能回复（仅规则匹配）
  - 不做垃圾消息过滤（仅监听和响应）
  - 不做语音/视频消息处理（仅文本）
  - 不做跨平台支持（仅 Telegram Web A）

## 用户故事

### US1: 关键词监听
作为 Telegram 运营人员，
我希望自动监控包含特定关键词的消息（如 "价格", "合作"），
以便及时响应重要客户咨询。

**验收标准**:
- [ ] AC1.1: 支持配置多个关键词（精确匹配 + 正则表达式）
- [ ] AC1.2: 检测到关键词时触发回调函数
- [ ] AC1.3: 回调包含消息内容、发送者、时间戳
- [ ] AC1.4: 支持忽略大小写/emoji 干扰

### US2: 自定义延时
作为 Telegram 自动化用户，
我希望在发送消息前添加随机延迟（如 2-5 秒），
以便避免被 Telegram 检测为机器人。

**验收标准**:
- [ ] AC2.1: 支持配置延时范围（如 min=2s, max=5s）
- [ ] AC2.2: 延迟时间从配置范围内随机选择
- [ ] AC2.3: 支持禁用延时（delay=0）
- [ ] AC2.4: 延时期间显示"正在输入"状态（可选）

### US3: 自动回复
作为 Telegram 客服，
我希望根据预设规则自动回复常见问题（如 FAQ），
以便提高响应效率。

**验收标准**:
- [ ] AC3.1: 支持配置规则库（关键词 → 回复模板）
- [ ] AC3.2: 支持模板变量（如 {sender_name}, {time}）
- [ ] AC3.3: 支持多条规则匹配时的优先级设置
- [ ] AC3.4: 支持禁用自动回复（enabled=false）
- [ ] AC3.5: 日志记录所有自动回复记录

### US4: 一键建群
作为 Telegram 社群运营，
我希望批量创建群组（如 10 个主题讨论群），
以便快速搭建社群矩阵。

**验收标准**:
- [ ] AC4.1: 支持模板配置（群组名、描述、成员列表）
- [ ] AC4.2: 批量创建群组（支持指定数量）
- [ ] AC4.3: 支持设置群组头像（可选）
- [ ] AC4.4: 创建后返回群组 ID/邀请链接
- [ ] AC4.5: 创建失败时提供错误日志

## 任务树

```
Phase 7: Telegram 自动化功能增强
├── 7.1 [src/telegram_multi/automation/] 核心自动化模块 (复杂度: 中等)
│   ├── 7.1.1 [automation/__init__.py] 模块初始化
│   ├── 7.1.2 [automation/keyword_monitor.py] 关键词监听器
│   ├── 7.1.3 [automation/delay_manager.py] 延时管理器
│   ├── 7.1.4 [automation/auto_responder.py] 自动回复引擎
│   └── 7.1.5 [automation/group_creator.py] 群组创建器
│
├── 7.2 [src/telegram_multi/config.py] 配置层扩展 (复杂度: 简单)
│   ├── 7.2.1 AutomationConfig (关键词、延时、回复规则)
│   └── 7.2.2 GroupTemplateConfig (群组模板)
│
├── 7.3 [src/telegram_multi/message_interceptor.py] 消息拦截器增强 (复杂度: 中等)
│   └── 7.3.1 集成关键词监听和自动回复钩子
│
├── 7.4 [tests/test_automation_*.py] 测试覆盖 (复杂度: 中等)
│   ├── 7.4.1 [tests/test_keyword_monitor.py] 关键词监听测试
│   ├── 7.4.2 [tests/test_delay_manager.py] 延时管理测试
│   ├── 7.4.3 [tests/test_auto_responder.py] 自动回复测试
│   └── 7.4.4 [tests/test_group_creator.py] 群组创建测试
│
└── 7.5 [run_telegram.py] CLI 集成 (复杂度: 简单)
    └── 7.5.1 添加自动化功能启动参数
```

## 复杂度估算

| 任务 | 复杂度 | 工作量 | 风险 |
|------|--------|--------|------|
| 7.1.2 关键词监听 | 中等 | 3h | 低（纯逻辑） |
| 7.1.3 延时管理 | 简单 | 1h | 低 |
| 7.1.4 自动回复 | 中等 | 4h | 中（规则引擎） |
| 7.1.5 群组创建 | 复杂 | 6h | 高（需 Playwright API） |
| 7.2 配置层 | 简单 | 2h | 低 |
| 7.3 拦截器增强 | 中等 | 2h | 中（集成复杂度） |
| 7.4 测试 | 中等 | 5h | 低 |

**总工作量**: 约 23 小时

## 模型分发建议

| 阶段 | 模型 | 命令 | 理由 |
|------|------|------|------|
| **审计** | **Gemini 2.5 Pro** | `/audit "自动化模块设计"` | 影响 ≥3 模块，需要 2M 上下文审查整体架构 |
| **TDD-关键词监听** | Gemini 3 Flash | `/tdd "7.1.2 关键词监听"` | 高频测试编写 |
| **实现-关键词监听** | Gemini 3 Flash | `/impl "7.1.2 关键词监听"` | 快速迭代 |
| **TDD-自动回复** | Gemini 3 Flash | `/tdd "7.1.4 自动回复引擎"` | 规则引擎测试 |
| **实现-自动回复** | Gemini 3 Flash | `/impl "7.1.4 自动回复"` | 快速迭代 |
| **TDD-群组创建** | Gemini 3 Flash | `/tdd "7.1.5 群组创建器"` | Playwright API 测试 |
| **实现-群组创建** | Claude Opus 4.5 | `/impl "7.1.5 群组创建"` | 高复杂度 Playwright 逻辑 |
| **审查** | Codex 5.2 | `/review` | 代码质量把关 + 安全审计 |
| **验证** | - | `just verify` | 自动化门禁 |

## 下游命令

```bash
# 步骤 1: 全局架构审计（强制）
/audit "自动化模块整体设计"

# 步骤 2: TDD 开发关键词监听
/tdd "7.1.2 关键词监听器"

# 步骤 3: 实现关键词监听
/impl "7.1.2 关键词监听器"

# 步骤 4: TDD 开发自动回复
/tdd "7.1.4 自动回复引擎"

# 步骤 5: 实现自动回复
/impl "7.1.4 自动回复引擎"

# 步骤 6: TDD 开发群组创建（高复杂度）
/tdd "7.1.5 群组创建器"

# 步骤 7: 实现群组创建
/impl "7.1.5 群组创建器"

# 步骤 8: 验证
just verify

# 步骤 9: 代码审查
/review

# 步骤 10: 提交
/checkpoint "自动化功能增强完成"
```

## 技术设计

### 7.1.2 关键词监听器 (keyword_monitor.py)

```python
from typing import List, Callable, Pattern
import re
from pydantic import BaseModel

class KeywordRule(BaseModel):
    """关键词规则配置"""
    pattern: str  # 正则表达式或精确字符串
    is_regex: bool = False
    ignore_case: bool = True
    callback: Optional[Callable] = None

class KeywordMonitor:
    """关键词监听器"""
    def __init__(self, rules: List[KeywordRule]):
        self.rules = rules
        self._compiled_patterns = self._compile_rules()

    def _compile_rules(self) -> List[Pattern]:
        """预编译正则表达式"""
        ...

    def check(self, text: str) -> List[KeywordRule]:
        """检查文本是否匹配关键词"""
        ...

    def on_match(self, message: Message) -> None:
        """关键词匹配时触发回调"""
        ...
```

### 7.1.3 延时管理器 (delay_manager.py)

```python
import asyncio
import random
from pydantic import BaseModel

class DelayConfig(BaseModel):
    """延时配置"""
    enabled: bool = True
    min_delay: float = 2.0  # 秒
    max_delay: float = 5.0  # 秒
    show_typing: bool = False  # 是否显示"正在输入"

class DelayManager:
    """延时管理器"""
    def __init__(self, config: DelayConfig):
        self.config = config

    async def delay(self) -> None:
        """执行随机延时"""
        if not self.config.enabled:
            return
        wait_time = random.uniform(self.config.min_delay, self.config.max_delay)
        await asyncio.sleep(wait_time)
```

### 7.1.4 自动回复引擎 (auto_responder.py)

```python
from typing import Dict, List
from pydantic import BaseModel

class ResponseRule(BaseModel):
    """回复规则"""
    trigger: str  # 触发关键词（支持正则）
    response_template: str  # 回复模板
    priority: int = 0  # 优先级（数字越大越优先）
    enabled: bool = True

class AutoResponder:
    """自动回复引擎"""
    def __init__(self, rules: List[ResponseRule]):
        self.rules = sorted(rules, key=lambda x: x.priority, reverse=True)

    def match(self, message: Message) -> Optional[ResponseRule]:
        """匹配最高优先级规则"""
        ...

    def render_response(self, rule: ResponseRule, context: Dict) -> str:
        """渲染回复模板"""
        # 支持 {sender_name}, {time} 等变量
        ...

    async def auto_reply(self, message: Message) -> Optional[str]:
        """自动生成回复"""
        ...
```

### 7.1.5 群组创建器 (group_creator.py)

```python
from typing import List, Optional
from pydantic import BaseModel
from playwright.async_api import Page

class GroupTemplate(BaseModel):
    """群组模板"""
    name_template: str  # 群组名（支持 {index} 变量）
    description: str
    avatar_path: Optional[str] = None
    initial_members: List[str] = []  # 成员用户名列表

class GroupCreator:
    """群组创建器"""
    def __init__(self, page: Page):
        self.page = page

    async def create_group(self, template: GroupTemplate, index: int = 0) -> str:
        """创建单个群组"""
        # 使用 Playwright 自动化操作
        # 1. 点击"新建群组"按钮
        # 2. 填写群组名称/描述
        # 3. 添加成员
        # 4. 上传头像（可选）
        # 5. 返回群组 ID/邀请链接
        ...

    async def batch_create(self, template: GroupTemplate, count: int) -> List[str]:
        """批量创建群组"""
        ...
```

### 7.2 配置层扩展

```python
# 在 src/telegram_multi/config.py 中添加

class AutomationConfig(BaseModel):
    """自动化功能配置"""
    keyword_monitoring: bool = False
    keywords: List[str] = []
    auto_reply_enabled: bool = False
    reply_rules: List[ResponseRule] = []
    delay_config: DelayConfig = Field(default_factory=DelayConfig)

class InstanceConfig(BaseModel):
    """扩展现有 InstanceConfig"""
    id: str
    profile_path: str
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)  # 新增
```

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **Telegram API 限制** | 高 | 添加速率限制（每分钟最多 20 条消息） |
| **群组创建失败** | 中 | 实现重试机制 + 详细错误日志 |
| **关键词误匹配** | 低 | 支持正则精确控制 + 测试覆盖 |
| **自动回复被检测** | 中 | 强制启用延时管理器 |
| **Playwright 稳定性** | 中 | 使用 try-catch + 优雅降级 |

## 测试策略

- **覆盖率要求**: 所有新模块 ≥90%
- **关键测试场景**:
  1. 关键词监听：精确匹配、正则匹配、大小写不敏感
  2. 延时管理：范围验证、禁用延时、异步执行
  3. 自动回复：规则优先级、模板渲染、多规则匹配
  4. 群组创建：单个创建、批量创建、失败重试

## 依赖关系

```
automation/
├── keyword_monitor.py    # 无外部依赖
├── delay_manager.py      # → asyncio
├── auto_responder.py     # → message_interceptor.py
└── group_creator.py      # → playwright, browser_context.py
```

## 验收检查清单

- [ ] 所有 AC (验收标准) 通过
- [ ] `just verify` 通过（编译 + lint + 测试）
- [ ] 测试覆盖率 ≥90%
- [ ] 代码审查通过（Codex 5.2）
- [ ] 文档更新（CODEMAP.md, NOTES.md）
- [ ] 配置示例（telegram.yaml 更新）

## 配置示例 (telegram.yaml)

```yaml
browser:
  headless: false
  executable_path: null

instances:
  - id: account1
    profile_path: ./profiles/acc1
    translation:
      enabled: true
      provider: google
      source_lang: zh
      target_lang: en
    automation:
      keyword_monitoring: true
      keywords:
        - "价格"
        - "合作"
        - "咨询"
      auto_reply_enabled: true
      reply_rules:
        - trigger: "价格"
          response_template: "感谢咨询！请查看我们的价格表：https://example.com/pricing"
          priority: 10
        - trigger: "合作"
          response_template: "感谢您的兴趣！请发送邮件至 partner@example.com"
          priority: 5
      delay_config:
        enabled: true
        min_delay: 2.0
        max_delay: 5.0
        show_typing: true
```
