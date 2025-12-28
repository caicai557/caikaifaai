# AI Council 最佳实践 (2025)

> 基于行业最新研究

## 🎯 核心发现

根据 Anthropic 内部研究：

- **90.2% 性能提升**: 多智能体 vs 单智能体
- **32.3% Token 削减**: 通过模型分层
- **2.8-4.4x 速度**: 并行协调

## 🏗️ 架构模式

### Orchestrator-Worker Pattern

```
Orchestrator (Opus/Gemini Pro)
    ├─> Worker 1 (Sonnet/Flash)
    ├─> Worker 2 (Sonnet/Flash)
    └─> Worker 3 (Sonnet/Flash)
```

**原则**:
- Orchestrator: 规划+路由（只读权限）
- Workers: 单一任务（窄权限）
- 小模型执行，大模型协调

### Hub-and-Spoke 事件架构

解耦智能体通信，复杂度从 O(N²) 降到 O(N)

### 程序化工具调用 (PTC)

Token 节省约 98.7%：

```python
# 编写脚本批量处理，替代自然语言循环
import glob
for f in glob.glob('data/*.json'):
    process(f)
```

## 🔀 模型选择

| 模型 | 任务分解 | 稳定性 | 推荐场景 |
|------|---------|--------|----------|
| Claude | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 规划、生成 |
| Gemini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 协调、审计 |

## 🎓 委托最佳实践

### 错误示例 ❌

```
"研究半导体短缺"  # 过于模糊
```

### 正确示例 ✅

```
任务: 收集 2023-2025 半导体数据
目标: 分析供应链影响
输出: JSON 格式
工具: WebSearch (限 3 源)
边界: 仅汽车芯片
```

## 🔒 安全原则

⚠️ **权限蔓延是不安全自主性的最快路径**

- 从 deny-all 开始
- 仅允许必需命令
- 敏感操作需确认
- 阻止危险命令

## ⚡ Token 优化

### 1. 渐进式工具加载

节省 ~95% 初始上下文

### 2. Session 预算管理

```
200k 预算分配:
- 需求理解: 10k
- 信息查询: 15k
- 代码实现: 20k
- 审查修复: 10k
- 预留: 140k
```

## 📚 参考资源

### 官方文档

- [Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Claude Agent SDK (2025)](https://skywork.ai/blog/claude-agent-sdk-best-practices-ai-agents-2025/)
- [Azure AI Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)

### 开源项目

- [claude-flow](https://github.com/ruvnet/claude-flow)
- [ccswarm](https://github.com/nwiizo/ccswarm)
- [wshobson/agents](https://github.com/wshobson/agents)

---

**最后更新**: 2025-12-27
