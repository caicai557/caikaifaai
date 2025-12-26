# BRIEF (Single Source of Truth)

> 当前开发任务的单一事实来源

## 项目

**cesi-telegram-multi**: Telegram Web A 多开 + 双向自动翻译

## 当前任务

**双语翻译功能增强** (Phase 4.x)

详细规格: [SPEC.md](./SPEC.md)

## 验收标准

- [ ] 收到消息显示原文 + 翻译（双语）
- [ ] 发送消息前显示翻译预览
- [ ] 翻译目标语言可配置（非硬编码）
- [ ] 历史消息自动翻译
- [ ] 使用免费 Google Translate API
- [ ] `just verify` 通过

## 任务树 (简化)

```
4.1 配置层增强
    └── config.py: display_mode, show_header

4.2 JS 双语显示
    └── message_interceptor.py: 原文+翻译格式

4.3 发送预览
    └── message_interceptor.py: 输入框翻译预览

4.4 历史消息
    └── message_interceptor.py: 加载时扫描

4.5 测试覆盖
    └── test_message_interceptor.py: 新增测试
```

## 模型分发 (标准六步流程)

| 阶段 | 模型 | 命令 | 占比 |
|------|------|------|:----:|
| 1. PM 规划 | Claude Opus 4.5 | `/plan` | 5% |
| 2. 架构审计 | Gemini 3 Pro | `/audit` | 5% |
| 3. TDD 测试 | Gemini 3 Flash | `/tdd` | 80% |
| 4. 最小实现 | Gemini 3 Flash | `/impl` | 80% |
| 5. 验证裁决 | - | `/verify` | - |
| 6. 代码审查 | Codex 5.2 | `/review` | 10% |

## 开发命令

```bash
# 读取完整规格
cat .council/SPEC.md

# TDD 模式
/tdd "双语翻译 Phase 4.1 配置层"

# 实现
/impl "配置层 display_mode"

# 验证
just verify
```

## 约束

- 每个文件 < 200 行改动
- 必须有对应测试
- 使用 `async/await`
- 无硬编码语言代码

## 相关文档

- [SPEC.md](./SPEC.md): 完整技术规格
- [CODEMAP.md](../CODEMAP.md): 项目架构
- [NOTES.md](./NOTES.md): 开发笔记
