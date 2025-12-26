# SPEC: 双语翻译功能增强

> 规划者: Claude Opus 4.5 | 状态: 待审批

## 1. 问题陈述

### 当前状态

Telegram 多开翻译功能存在以下不足：

| 问题 | 影响 |
|------|------|
| 翻译替换原文 | 用户无法看到原文，失去上下文 |
| 目标语言硬编码 | 无法自定义翻译方向 |
| 发送消息无翻译 | 用户不知道对方会看到什么 |
| 历史消息不处理 | 切换聊天后无翻译 |

### 目标状态

实现**双语显示**翻译系统：
- 收到消息：原文 + 翻译同时显示
- 发送消息：预览翻译结果后发送
- 聊天记录：历史消息也双语显示
- 可配置：翻译方向用户自定义
- 免费：使用 Google Translate 免费 API

### 非目标

- ❌ 付费翻译服务集成 (DeepL 等)
- ❌ 语音/图片翻译
- ❌ 翻译质量评估
- ❌ 多语言自动检测切换

## 2. 用户故事

```
作为 Telegram 用户，
我希望 收到外语消息时自动翻译并双语显示，
以便 我能同时看到原文和翻译，确保理解准确。

作为 Telegram 用户，
我希望 发送消息前看到翻译预览，
以便 我确认对方会收到正确的翻译内容。

作为 Telegram 用户，
我希望 自定义翻译的源语言和目标语言，
以便 适应不同的聊天对象。
```

## 3. 任务树

```
双语翻译功能增强
├── 3.1 配置层增强
│   ├── [config.py] 添加 display_mode 字段 (bilingual/replace/original)
│   └── [config.py] 添加 show_translation_header 字段
│
├── 3.2 JS 注入脚本重构
│   ├── [message_interceptor.py] get_injection_script() 接受配置参数
│   ├── [message_interceptor.py] 动态生成 CONFIG 对象
│   └── [message_interceptor.py] 移除硬编码语言
│
├── 3.3 双语显示实现
│   ├── [message_interceptor.py] 修改 overlay 结构为双语格式
│   ├── [message_interceptor.py] 添加原文/翻译分隔样式
│   └── [message_interceptor.py] 支持折叠/展开原文
│
├── 3.4 发送消息翻译预览
│   ├── [message_interceptor.py] 监听输入框内容变化
│   ├── [message_interceptor.py] 实时显示翻译预览气泡
│   └── [message_interceptor.py] 发送确认前显示双语
│
├── 3.5 历史消息处理
│   ├── [message_interceptor.py] 页面加载时扫描已有消息
│   ├── [message_interceptor.py] 聊天切换时重新扫描
│   └── [message_interceptor.py] 添加批量翻译队列
│
└── 3.6 测试覆盖
    ├── [test_message_interceptor.py] 双语显示测试
    ├── [test_message_interceptor.py] 配置注入测试
    └── [test_message_interceptor.py] 发送预览测试
```

## 4. 验收标准

### 4.1 功能验收

| ID | 标准 | 验证方法 |
|:--:|------|----------|
| AC1 | 收到消息显示原文+翻译 | 手动测试 |
| AC2 | 翻译目标语言可配置 | 单元测试 |
| AC3 | 发送前显示翻译预览 | 手动测试 |
| AC4 | 历史消息自动翻译 | 手动测试 |
| AC5 | 使用免费 Google API | 代码审查 |

### 4.2 技术验收

| ID | 标准 | 验证方法 |
|:--:|------|----------|
| TC1 | `just verify` 通过 | CI |
| TC2 | 新增测试覆盖 ≥90% | pytest-cov |
| TC3 | 无硬编码语言 | grep 检查 |
| TC4 | JS 脚本 < 500 行 | wc -l |

## 5. 技术设计

### 5.1 配置扩展

```python
# config.py
class TranslationConfig(BaseModel):
    enabled: bool = False
    provider: str = "google"
    source_lang: str = "auto"      # 用户语言
    target_lang: str = "en"        # 对方语言
    display_mode: str = "bilingual"  # 新增: bilingual/replace/original
    show_header: bool = True         # 新增: 显示翻译标题
```

### 5.2 JS 注入重构

```python
# message_interceptor.py
def get_injection_script(self) -> str:
    """生成动态配置的 JS 脚本"""
    config_json = json.dumps({
        "enabled": self.config.enabled,
        "sourceLang": self.config.source_lang,
        "targetLang": self.config.target_lang,
        "displayMode": self.config.display_mode,
        "showHeader": self.config.show_header,
    })
    return f"""
    (function() {{
      const CONFIG = {config_json};
      // ... 脚本逻辑
    }})();
    """
```

### 5.3 双语显示格式

```
┌─────────────────────────────────┐
│ 🌐 翻译                         │  ← 可选标题
├─────────────────────────────────┤
│ Hello, how are you today?       │  ← 原文 (可折叠)
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ 你好，你今天怎么样？             │  ← 翻译
└─────────────────────────────────┘
```

### 5.4 发送预览

```
┌─────────────────────────────────┐
│ 输入框: 你好朋友                │
├─────────────────────────────────┤
│ 📤 预览: Hello friend           │  ← 实时翻译预览
└─────────────────────────────────┘
```

## 6. 风险点

| 风险 | 严重性 | 缓解措施 |
|------|:------:|----------|
| Google API 限流 | 高 | 缓存 + 指数退避 + 批量队列 |
| DOM 结构变化 | 中 | 多选择器兜底 + 容错处理 |
| 性能影响 | 中 | 防抖 + 虚拟滚动区域限制 |
| 翻译延迟 | 低 | Loading 状态 + 骨架屏 |
| 原文检测错误 | 低 | 显示原文，用户可对比 |

## 7. 验证命令

```bash
# TDD 阶段
just tdd

# 实现后验证
just verify

# 手动测试
python run_telegram.py --config telegram.yaml --instance test
```

## 8. 模型分发建议

| 阶段 | 模型 | 任务 |
|------|------|------|
| 审计 | Gemini Pro | 检查现有 JS 脚本与 Telegram DOM 兼容性 |
| TDD | Gemini Flash | 编写配置扩展和 JS 生成测试 |
| 实现 | Gemini Flash | 实现配置层和 JS 脚本重构 |
| 审查 | Codex | 安全审查 + 边界对齐 |

## 9. 排期建议

```
Phase 4.1: 配置层增强 + 测试
Phase 4.2: JS 双语显示 + 测试
Phase 4.3: 发送预览 + 测试
Phase 4.4: 历史消息 + 测试
Phase 4.5: 集成测试 + 手动验证
```

---

**审批状态**: ⏳ 待用户确认

**下一步**: 用户确认后执行 `/tdd` 开始 TDD 流程
