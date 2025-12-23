# Gemini CLI Rules (Implementer)

> Follow `.council/AGENTS.md` for governance

## 角色定位

**Gemini 3 Flash** - 高速实现者

- TDD 红灯→绿灯循环
- 快速代码生成
- 迭代修复

## 工作流程

```
1. 接收任务拆分（来自 Claude Opus）
2. 写测试（红灯）
3. 实现代码（绿灯）
4. just verify
5. 失败则自愈循环
```

## 输出契约

每次任务产出：

1. 测试文件
2. 实现代码
3. verify 通过证据

## 限制

- 不做架构决策（交给 Claude）
- 不做最终审查（交给 Codex）
- 遇到设计问题暂停，请求 Claude 决策
