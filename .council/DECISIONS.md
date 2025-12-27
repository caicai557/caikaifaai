# Architectural Decisions Log (ADL)

## ADL-006: Hub-and-Spoke Event Architecture

- **Date**: 2025-12-27
- **Decision**: Implement Hub-and-Spoke architecture with Event-Driven (Pub/Sub) mechanism
- **Context**:
  - Need to decouple multiple autonomous agents (Coder, QA, Planner).
  - Direct point-to-point communication leads to $O(N^2)$ complexity.
  - Need automated, reactive workflows ("Surgical Room" metaphor).
- **Alternatives**:
  - Direct Agent-to-Agent calls → High coupling, hard to scale.
  - Shared Database Polling → High latency, inefficient.
- **Consequences**:
  - **Decoupling**: Agents only know `Hub` and `Event`.
  - **Automation**: Events trigger downstream tasks automatically.
  - **Single Source of Truth**: Hub holds `DualLedger` context.
  - **Token Saving**: PTC-friendly `Event.create()` reduces verbosity.
- **Trade-offs**:
  - ⚠️ Synchronous execution blocks Hub (future: async queue).
  - ⚠️ In-memory event history lost on restart (future: persistence).
- **API Contract**:

  ```python
  class Hub:
    def subscribe(event_type: EventType, callback: Callable)
    def publish(event: Event)
    def get_context() -> str

  class Event:
    @classmethod
    def create(type_str, source, **kwargs) -> Event
  ```

---

## ADL-005: 翻译系统设计与多提供商支持

- **Date**: 2025-12-24
- **Decision**: 使用抽象基类 + 工厂模式实现多提供商翻译系统
- **Context**:
  - 需要支持多个翻译服务（Google, DeepL, 本地离线）
  - 不同提供商有不同的 API 和限制
  - 避免提供商锁定，允许灵活切换
- **Alternatives**:
  - 单一 GoogleTranslator 类 → 无扩展性，难以添加新提供商
  - 条件语句路由 → 违反开闭原则，代码复杂度高
- **Consequences**:
  - 新提供商只需继承 Translator + 注册
  - 缓存策略统一在抽象类（可覆盖）
  - 错误处理一致（失败返回原文本）
- **Trade-offs**:
  - ⚠️ 循环导入风险：translator.py 导入 google.py（需监控）
  - ✅ 配置驱动：provider 切换无需代码改动
- **API Contract**:

  ```python
  class Translator(ABC):
    def translate(text, src_lang, dest_lang) -> str
    def batch_translate(texts, src_lang, dest_lang) -> List[str]
    def clear_cache() -> None

  class TranslatorFactory:
    @classmethod
    def register_provider(name: str, provider_class: type) -> None
    @classmethod
    def create(config: TranslationConfig) -> Translator
  ```

- **Cache Key Strategy**:
  - ✅ 使用 MD5(text) 代替 text[:50]
  - 避免长文本前缀相同导致的碰撞
  - 缓存键格式：`src_lang:dest_lang:md5_hash`

---

## ADL-004: 浏览器上下文与实例管理分离

- **Date**: 2025-12-24
- **Decision**: 将 BrowserContext 和 InstanceManager 作为独立模块
- **Context**:
  - BrowserContext：纯数据模型（配置容器）
  - InstanceManager：业务逻辑（容器管理 + 端口分配）
  - 避免早期将 Playwright 耦合到配置层
- **Alternatives**:
  - 单一 Instance 类同时承载数据 + 业务逻辑 → 违反单一职责原则
  - BrowserContext 直接继承自 Playwright Browser → 强耦合，难以测试
- **Consequences**:
  - BrowserContext 可独立测试（无需 Playwright）
  - InstanceManager 可扩展（支持未来的资源管理）
  - 端口自动分配防止冲突（9222 起始，递增）
- **API Contract**:

  ```python
  BrowserContext(
    instance_id: str,              # 必需
    profile_path: str,             # 必需
    browser_config: BrowserConfig, # 默认为 BrowserConfig()
    target_url: str = "https://web.telegram.org/a/",
    port: Optional[int] = None
  )

  InstanceManager.add_instance(config: InstanceConfig) -> BrowserContext
  InstanceManager.get_instance(instance_id: str) -> Optional[BrowserContext]
  InstanceManager.remove_instance(instance_id: str) -> None
  InstanceManager.list_instances() -> List[str]
  InstanceManager.from_config(config: TelegramConfig) -> InstanceManager
  ```

---

## ADL-003: Telegram Multi Config 设计

- **Date**: 2025-12-24
- **Decision**: 使用 Pydantic v2 + YAML 加载实现配置管理
- **Context**:
  - 支持多实例隔离（各实例独立配置）
  - 支持多翻译提供商（google/deepl/local 切换）
  - 需要运行时验证（profile_path, instance_id 必需）
- **Alternatives**:
  - dataclass - 不支持自定义验证逻辑
  - 原始 dict - 容易出现配置错误，无类型检查
- **Consequences**:
  - 自动 YAML→Python 对象转换
  - 验证失败时抛 `ValidationError`（Pydantic 标准）
  - 类型提示友好（IDE 自动完成）
- **API Contract**:

  ```python
  TranslationConfig: provider ∈ {google, deepl, local}
  InstanceConfig: id: str, profile_path: str (required)
  BrowserConfig: headless: bool, executable_path: Optional[str]
  TelegramConfig: List[InstanceConfig], BrowserConfig
  TelegramConfig.from_yaml(file_path: str) -> TelegramConfig
  ```

---

## ADL-001: 契约变更规则

- **Date**: 2025-12-24
- **Decision**: 任何异常类型/语义契约变化必须同时满足：
  1. 更新 `.council/CONTRACTS.md`
  2. 更新/新增 `tests/test_contracts.py`
  3. 在本文件记录原因与替代方案
- **Context**: 防止"悄悄改契约"导致 API 破坏性变更
- **Alternatives**: 无强制门禁（不推荐）
- **Consequences**: 保证契约变更可追溯、可审计

---

## ADL-002: divide() 异常类型选择

- **Date**: 2025-12-24
- **Decision**: `divide(a, b)` 在 `b == 0` 时抛出 `ZeroDivisionError`
- **Context**: 与 Python 原生行为一致（`1/0` 抛出 `ZeroDivisionError`）
- **Alternatives**:
  - `ValueError` - 语义为"非法参数"，但与生态不一致
  - 返回 `None` / `float('inf')` - 隐藏错误，不推荐
- **Consequences**:
  - 调用方可用 `except ZeroDivisionError` 捕获
  - 与 Python 标准行为一致，学习成本低
