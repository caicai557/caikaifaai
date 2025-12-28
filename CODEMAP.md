# 代码地图 (Code Map)

> 本文档提供项目的整体结构视图，帮助 AI 智能体快速理解项目上下文。

## 项目概览

| 字段 | 值 |
|------|-----|
| **项目名称** | cesi-telegram-multi |
| **项目类型** | Python 后端应用 |
| **主要用途** | Telegram Web A 多开 + 双向自动翻译 |
| **Python 版本** | 3.12+ |
| **架构模式** | Async/await + 消息拦截 + 翻译管道 |

## 目录结构

```
cesi-telegram-multi/
├── src/
│   ├── telegram_multi/           # 核心模块
│   │   ├── config.py             # Pydantic 配置模型
│   │   ├── browser_context.py    # 浏览器上下文包装器
│   │   ├── instance_manager.py   # 多实例生命周期管理
│   │   ├── translator.py         # 翻译抽象层 + 工厂
│   │   ├── message_interceptor.py # 消息拦截 + JS 注入
│   │   └── translators/
│   │       ├── __init__.py
│   │       └── google.py         # Google 翻译实现
│   ├── seabox/                   # API 服务器模块 (FastAPI)
│   ├── config.py                 # 全局特性开关
│   └── calculator.py             # 工具模块
├── tests/
│   ├── test_telegram_config.py   # 配置系统测试 (23)
│   ├── test_browser_context.py   # 浏览器上下文测试 (9)
│   ├── test_instance_manager.py  # 实例管理器测试 (11)
│   ├── test_translator.py        # 翻译抽象层测试 (13)
│   ├── test_translators_google.py # Google 翻译测试 (10)
│   ├── test_message_interceptor.py # 消息拦截测试
│   └── ...
├── .council/                     # 多模型理事会配置
├── .claude/                      # Claude Code 配置
├── justfile                      # 构建命令
└── pyproject.toml                # 项目元数据
```

## 核心模块详解

### 1. config.py (Phase 1) ✅

```python
# 配置模型层级
TranslationConfig   # 翻译配置 (provider, source_lang, target_lang)
BrowserConfig       # 浏览器配置 (headless, executable_path)
InstanceConfig      # 单实例配置 (id, profile_path, translation)
TelegramConfig      # 全局配置 + YAML 加载
```

**契约**:
- `TranslationConfig.provider` ∈ {google, deepl, local}
- `TelegramConfig.load_from_yaml()` 支持多实例配置

### 2. browser_context.py (Phase 2) ✅

```python
class BrowserContext(BaseModel):
    instance_id: str        # 实例唯一标识
    profile_path: str       # 用户数据目录 (隔离)
    browser_config: BrowserConfig
    target_url: str = "https://web.telegram.org/a/"
    port: int               # 调试端口
```

**契约**:
- 每实例独立 `user_data_dir`
- 默认目标 URL: Telegram Web A

### 3. instance_manager.py (Phase 2) ✅

```python
class InstanceManager:
    def add_instance(config: InstanceConfig) -> BrowserContext
    def get_instance(instance_id: str) -> Optional[BrowserContext]
    def remove_instance(instance_id: str) -> bool
    def list_instances() -> List[str]

    @classmethod
    def from_config(config: TelegramConfig) -> InstanceManager
```

**契约**:
- 端口自动分配 (9222 起始，递增)
- `from_config()` 批量加载实例

### 4. translator.py (Phase 3) ✅

```python
class Translator(ABC):
    @abstractmethod
    async def translate(text: str, source: str, target: str) -> str
    async def batch_translate(texts: List[str], ...) -> List[str]
    def clear_cache() -> None

class TranslatorFactory:
    @staticmethod
    def create(config: TranslationConfig) -> Translator
    @staticmethod
    def register_provider(name: str, cls: Type[Translator])
```

**契约**:
- 翻译失败时返回原文本 (优雅降级)
- 支持动态注册提供商

### 5. translators/google.py (Phase 3) ✅

```python
class GoogleTranslator(Translator):
    def __init__(max_retries=3, backoff_factor=0.5)
    async def translate(text, source, target, enabled=True) -> str
```

**契约**:
- 缓存键使用 MD5 哈希 (避免碰撞)
- 指数退避重试 (max_retries=3)
- `enabled=False` 时直接返回原文本

### 6. message_interceptor.py (Phase 4) ✅

```python
class MessageType(Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class Message(BaseModel):
    message_type: MessageType
    content: str
    sender: Optional[str]
    timestamp: Optional[str]
    translated_content: Optional[str]

class MessageInterceptor:
    def __init__(config: TranslationConfig, translator=None)
    async def intercept(message: Message) -> Message
    def get_injection_script() -> str  # 返回浏览器端 JS
    def register_callback(callback: Callable)
```

**契约**:
- 双向翻译 (incoming: target→source, outgoing: source→target)
- `get_injection_script()` 返回 DOM 监听 JS 代码

## 开发进度

| Phase | 模块 | 状态 | 测试数 |
|:-----:|------|:----:|:------:|
| 1 | config.py | ✅ | 23 |
| 2 | browser_context.py | ✅ | 9 |
| 2 | instance_manager.py | ✅ | 11 |
| 3 | translator.py | ✅ | 13 |
| 3 | translators/google.py | ✅ | 10 |
| 4 | message_interceptor.py | ✅ | ~20 |
| 5 | CLI 工具 | ⏳ | - |
| 6 | Dashboard | ⏳ | - |

**总测试数**: 107 tests

## 待开发 (Phase 5-6)

### Phase 5: CLI 工具

```
src/telegram_multi/
├── cli/
│   ├── __init__.py
│   ├── launch_instance.py    # 单实例启动
│   └── launch_multi.py       # 多实例启动

# 入口点
run_telegram.py               # CLI 主入口
```

**预期功能**:
```bash
# 单实例
python run_telegram.py --config telegram.yaml --instance acc1

# 多实例
python run_telegram.py --config telegram.yaml --all
```

### Phase 6: Dashboard

```
src/telegram_multi/
├── dashboard/
│   ├── __init__.py
│   ├── server.py             # FastAPI 服务器
│   └── templates/            # HTML 模板

run_dashboard.py              # Dashboard 入口
```

**预期功能**:
- 实例状态监控
- 翻译统计
- 日志查看

## 依赖关系

```
telegram_multi/
├── config.py                 # 无依赖
├── browser_context.py        # → config.py
├── instance_manager.py       # → config.py, browser_context.py
├── translator.py             # → config.py
├── translators/google.py     # → translator.py
└── message_interceptor.py    # → config.py, translator.py
```

## 常用命令

```bash
# 安装
pip install -e ".[telegram]"      # 基础功能
pip install -e ".[telegram-full]" # 含 DeepL + Argos
pip install -e ".[dev]"           # 开发工具

# 测试
just test                         # 运行所有测试
just verify                       # compile + lint + test

# 开发
just tdd                          # TDD 模式
just impl                         # 实现模式
```

## 配置示例

```yaml
# telegram.yaml
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

  - id: account2
    profile_path: ./profiles/acc2
    translation:
      enabled: true
      provider: google
      source_lang: en
      target_lang: zh
```

## 下一步开发建议

1. **Phase 5 CLI**: 创建 `launch_instance.py` 和 `launch_multi.py`
2. **Playwright 集成**: 实现实际的浏览器启动逻辑
3. **JS 注入测试**: 在真实 Telegram Web A 中测试拦截脚本
4. **DeepL 提供商**: 实现 `translators/deepl.py`
