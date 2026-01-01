#!/usr/bin/env python3
"""
AI Council 开发资料文档生成器
自动汇总和整理理事会开发最佳实践文档
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict


class CouncilDocsGenerator:
    """理事会文档生成器"""

    def __init__(self, council_dir: Path = Path(".council")):
        self.council_dir = council_dir
        self.output_dir = council_dir / "docs"
        self.output_dir.mkdir(exist_ok=True)

    def collect_metadata(self) -> Dict:
        """收集文档元数据"""
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "documents": {},
            "stats": {
                "total_docs": 0,
                "prompts_count": 0,
                "routines_count": 0
            }
        }

        # 扫描 Markdown 文档
        for md_file in self.council_dir.glob("*.md"):
            metadata["documents"][md_file.name] = {
                "path": str(md_file),
                "size_kb": md_file.stat().st_size / 1024,
                "modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
            }
            metadata["stats"]["total_docs"] += 1

        # 扫描 prompts
        prompts_dir = self.council_dir / "prompts"
        if prompts_dir.exists():
            metadata["stats"]["prompts_count"] = len(list(prompts_dir.glob("*.md")))

        # 扫描 routines
        routines_dir = self.council_dir / "routines"
        if routines_dir.exists():
            metadata["stats"]["routines_count"] = len(list(routines_dir.glob("*.py")))

        return metadata

    def generate_index(self) -> str:
        """生成索引页"""
        content = """# AI Council 开发资料中心

> 自动生成于 {timestamp}

## 📚 文档导航

### 🎯 核心架构

| 文档 | 说明 | 状态 |
|------|------|------|
| [AGENTS.md](../AGENTS.md) | Agent 治理宪法：权限矩阵、模型路由、Token 优化 | ✅ 核心 |
| [CODEMAP.md](../../CODEMAP.md) | 项目代码地图：模块结构、依赖关系 | ✅ 必读 |
| [SOP.md](../SOP.md) | 六步自愈循环标准操作程序 | ✅ 流程 |
| [DECISIONS.md](../DECISIONS.md) | 架构决策日志 (ADL) | ✅ 记录 |

### 🔧 最佳实践

| 文档 | 说明 | 状态 |
|------|------|------|
| [TOKEN_SAVING_PRACTICES.md](../TOKEN_SAVING_PRACTICES.md) | Token 节省最佳实践 | ✅ 优化 |
| [MCP_PHILOSOPHY.md](../MCP_PHILOSOPHY.md) | MCP 协议通信工业标准 | ✅ 理念 |
| [MCP_BEST_PRACTICES.md](../MCP_BEST_PRACTICES.md) | MCP 使用最佳实践 | ✅ 实操 |

### 🤖 模型专用指南

| 文档 | 说明 | 目标模型 |
|------|------|----------|
| [CLAUDE.md](../CLAUDE.md) | Claude Code 规则与角色定位 | Claude Opus 4.5 |
| [CODEX.md](../CODEX.md) | Codex 审查与修复指南 | Codex 5.2 |
| [GEMINI.md](../GEMINI.md) | Gemini 实现与审计指南 | Gemini Pro/Flash |

### 📝 Prompts 模板

| 文件 | 用途 | 模型 |
|------|------|------|
| [audit_gemini.md](../prompts/audit_gemini.md) | 架构审计 | Gemini Pro |
| [plan_codex.md](../prompts/plan_codex.md) | PM 规划 | Codex |
| [tdd_gemini_flash.md](../prompts/tdd_gemini_flash.md) | TDD 测试 | Gemini Flash |
| [implement_gemini_flash.md](../prompts/implement_gemini_flash.md) | 最小实现 | Gemini Flash |
| [review_codex.md](../prompts/review_codex.md) | 代码审查 | Codex |
| [delegate_general.md](../prompts/delegate_general.md) | 模型委托 | 通用 |

### 📋 合约与规范

| 文档 | 说明 |
|------|------|
| [CONTRACTS.md](../CONTRACTS.md) | API 合约定义 |
| [SPEC.md](../SPEC.md) | 功能规格说明 |
| [BRIEF.md](../BRIEF.md) | 任务简报 (Task Ledger) |
| [NOTES.md](../NOTES.md) | 会话笔记 (Progress Ledger) |

---

## 🚀 快速开始

### 新手入门流程

```bash
# 1. 阅读核心文档（按顺序）
1. CODEMAP.md      # 理解项目整体结构
2. AGENTS.md       # 理解治理规则和模型路由
3. SOP.md          # 理解开发流程

# 2. 根据角色选择指南
- 规划任务 → 查看 CLAUDE.md + prompts/plan_codex.md
- 审计代码 → 查看 GEMINI.md + prompts/audit_gemini.md
- 实现功能 → 查看 GEMINI.md + prompts/implement_gemini_flash.md
- 代码审查 → 查看 CODEX.md + prompts/review_codex.md

# 3. 执行标准流程
just dev "<任务描述>"   # 自动执行六步流程
```

### 关键命令速查

```bash
# 验证门禁（唯一质量裁决）
just verify              # compile + lint + test

# 六步自愈循环
/plan "<需求>"          # 1. PM 规划 (Claude)
/audit "<模块>"         # 2. 架构审计 (Gemini Pro)
/tdd "<范围>"           # 3. TDD 测试 (Gemini Flash)
/impl "<范围>"          # 4. 最小实现 (Gemini Flash)
just verify              # 5. 验证裁决
/review                  # 6. 代码审查 (Codex)

# 发布前检查
just ship               # verify + review + git log
```

---

## 🎯 最佳实践核心原则 (2025)

### 1. 模型路由优化

| 模型 | 占比 | 适用场景 | 上下文 |
|------|------|----------|--------|
| **Claude Opus 4.5** | 5% | 规划总控、关键决策、长程推理 | 200k |
| **Codex 5.2** | 10% | 代码审查、漏洞发现、边界对齐 | - |
| **Gemini 3 Pro** | 5% | 深度审计、前端开发、工具使用 | 1M |
| **Gemini 3 Flash** | 80% | TDD、实现、迭代修复 | 1M |

### 2. Token 节省策略

```text
✅ 使用批量脚本处理 ≥3 处修改
✅ 使用 ruff/black 自动修复 lint 错误
✅ 使用 PTC (程序化工具调用) 代替自然语言循环
✅ Session 保持在 50k tokens 以下 (25% 预算)

❌ 禁止逐个 Edit 修改重复代码
❌ 禁止多次 Web 搜索相似内容
❌ 禁止重复写长报告
```

### 3. 安全边界

```text
🟢 Level 0: Read, Analysis (无需确认)
🟡 Level 1: Write, Edit (非破坏性，无需确认)
🔴 Level 2: Destructive, Network (必须确认)
⛔ Level 3: Secrets (严禁触碰)
```

### 4. 共识算法 (Wald Sequential)

```python
π = P(任务成功 | 当前证据)

if π ≥ 0.95:   → 提交 (git commit)
elif π ≤ 0.05: → 终止 (人工干预)
else:          → 继续迭代 (收集证据)
```

---

## 📊 架构决策参考

查看 [DECISIONS.md](../DECISIONS.md) 了解关键架构决策：

- **ADL-006**: Hub-and-Spoke 事件驱动架构
- **ADL-005**: 翻译系统多提供商设计
- **ADL-004**: 浏览器上下文与实例管理分离
- **ADL-003**: Pydantic v2 + YAML 配置管理

---

## 🔗 行业最佳实践 (2025)

### Multi-Agent 协作模式

- **Orchestrator-Worker Pattern**: 使用 Opus 作为协调者，Sonnet 作为工作者并行执行
- **Token 优化**: 多智能体架构实现 32.3% Token 削减，2.8-4.4x 速度提升
- **工具按需加载**: 避免初始加载所有工具，使用 `tool_search` 动态发现

### 模型选择对比

| 维度 | Claude | Gemini |
|------|--------|--------|
| **任务分解** | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐ 良好 |
| **稳定性** | ⭐⭐⭐ 一般（输出多样性高） | ⭐⭐⭐⭐ 良好 |
| **协调能力** | ⭐⭐⭐ 不推荐（精确度不足） | ⭐⭐⭐⭐⭐ 优秀 (ADK) |
| **生成质量** | ⭐⭐⭐⭐⭐ 优秀（工作者） | ⭐⭐⭐⭐ 良好 |

**推荐**: Claude 适合大局规划和内容生成，Gemini 适合精确协调和工具集成

### 委托最佳实践

```markdown
❌ 错误: "研究半导体短缺"（过于模糊）
✅ 正确:
- 目标：收集 2023-2025 半导体短缺的供应链数据
- 输出格式：JSON 列表，包含 {{日期, 地区, 缺货量, 来源}}
- 工具：使用 WebSearch, 限制 3 个来源
- 边界：仅关注汽车芯片，排除消费电子
```

### 安全原则

```text
⚠️ 权限蔓延是不安全自主性的最快路径
✅ 从 deny-all 开始，仅允许必需命令和目录
✅ 敏感操作需显式确认
✅ 阻止危险命令 (rm -rf, chmod -R, etc.)
```

---

## 📚 外部资源

### 官方文档
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Claude Agent SDK Best Practices (2025)](https://skywork.ai/blog/claude-agent-sdk-best-practices-ai-agents-2025/)
- [Microsoft AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)

### 开源项目参考
- [claude-flow](https://github.com/ruvnet/claude-flow) - 企业级 Agent 编排平台
- [ccswarm](https://github.com/nwiizo/ccswarm) - Git Worktree 隔离的多智能体系统
- [wshobson/agents](https://github.com/wshobson/agents) - Claude Code 智能自动化

### 技术博客
- [Claude Subagents 完整指南 (2025)](https://www.cursor-ide.com/blog/claude-subagents)
- [GPT vs Claude vs Gemini 编排对比](https://machine-learning-made-simple.medium.com/gpt-vs-claude-vs-gemini-for-agent-orchestration-b3fbc584f0f7)
- [AI Agent 编排框架对比](https://blog.n8n.io/ai-agent-orchestration-frameworks/)

---

## 🛠️ 维护指南

### 文档更新规则

```bash
# 1. 修改架构决策时
- 更新 DECISIONS.md (添加 ADL-XXX)
- 更新 CONTRACTS.md (如涉及 API 变更)
- 运行 python scripts/generate_council_docs.py

# 2. 添加新 Prompt 模板时
- 在 .council/prompts/ 创建新文件
- 在本索引添加条目
- 更新对应模型指南 (CLAUDE.md/GEMINI.md/CODEX.md)

# 3. 修改治理规则时
- 更新 AGENTS.md
- 通知所有理事会成员
- 运行 just verify 确保合规
```

### 自动化工具

```bash
# 生成此索引文档
python scripts/generate_council_docs.py

# 验证文档完整性
python scripts/validate_council_docs.py

# 导出为 PDF（需要 pandoc）
./scripts/export_docs_pdf.sh
```

---

**最后更新**: {timestamp}
**生成器版本**: 1.0.0
**维护者**: AI Council System
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return content

    def generate_best_practices_2025(self) -> str:
        """生成 2025 最佳实践汇总"""
        now = datetime.now().strftime("%Y-%m-%d")

        parts = []
        parts.append("# AI Council 最佳实践 (2025)\n\n")
        parts.append("> 基于行业最新研究\n\n")

        parts.append("## 🎯 核心发现\n\n")
        parts.append("根据 Anthropic 内部研究：\n\n")
        parts.append("- **90.2% 性能提升**: 多智能体 vs 单智能体\n")
        parts.append("- **32.3% Token 削减**: 通过模型分层\n")
        parts.append("- **2.8-4.4x 速度**: 并行协调\n\n")

        parts.append("## 🏗️ 架构模式\n\n")
        parts.append("### Orchestrator-Worker Pattern\n\n")
        parts.append("```\n")
        parts.append("Orchestrator (Opus/Gemini Pro)\n")
        parts.append("    ├─> Worker 1 (Sonnet/Flash)\n")
        parts.append("    ├─> Worker 2 (Sonnet/Flash)\n")
        parts.append("    └─> Worker 3 (Sonnet/Flash)\n")
        parts.append("```\n\n")

        parts.append("**原则**:\n")
        parts.append("- Orchestrator: 规划+路由（只读权限）\n")
        parts.append("- Workers: 单一任务（窄权限）\n")
        parts.append("- 小模型执行，大模型协调\n\n")

        parts.append("### Hub-and-Spoke 事件架构\n\n")
        parts.append("解耦智能体通信，复杂度从 O(N²) 降到 O(N)\n\n")

        parts.append("### 程序化工具调用 (PTC)\n\n")
        parts.append("Token 节省约 98.7%：\n\n")
        parts.append("```python\n")
        parts.append("# 编写脚本批量处理，替代自然语言循环\n")
        parts.append("import glob\n")
        parts.append("for f in glob.glob('data/*.json'):\n")
        parts.append("    process(f)\n")
        parts.append("```\n\n")

        parts.append("## 🔀 模型选择\n\n")
        parts.append("| 模型 | 任务分解 | 稳定性 | 推荐场景 |\n")
        parts.append("|------|---------|--------|----------|\n")
        parts.append("| Claude | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 规划、生成 |\n")
        parts.append("| Gemini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 协调、审计 |\n\n")

        parts.append("## 🎓 委托最佳实践\n\n")
        parts.append("### 错误示例 ❌\n\n")
        parts.append("```\n")
        parts.append('"研究半导体短缺"  # 过于模糊\n')
        parts.append("```\n\n")

        parts.append("### 正确示例 ✅\n\n")
        parts.append("```\n")
        parts.append("任务: 收集 2023-2025 半导体数据\n")
        parts.append("目标: 分析供应链影响\n")
        parts.append("输出: JSON 格式\n")
        parts.append("工具: WebSearch (限 3 源)\n")
        parts.append("边界: 仅汽车芯片\n")
        parts.append("```\n\n")

        parts.append("## 🔒 安全原则\n\n")
        parts.append("⚠️ **权限蔓延是不安全自主性的最快路径**\n\n")
        parts.append("- 从 deny-all 开始\n")
        parts.append("- 仅允许必需命令\n")
        parts.append("- 敏感操作需确认\n")
        parts.append("- 阻止危险命令\n\n")

        parts.append("## ⚡ Token 优化\n\n")
        parts.append("### 1. 渐进式工具加载\n\n")
        parts.append("节省 ~95% 初始上下文\n\n")

        parts.append("### 2. Session 预算管理\n\n")
        parts.append("```\n")
        parts.append("200k 预算分配:\n")
        parts.append("- 需求理解: 10k\n")
        parts.append("- 信息查询: 15k\n")
        parts.append("- 代码实现: 20k\n")
        parts.append("- 审查修复: 10k\n")
        parts.append("- 预留: 140k\n")
        parts.append("```\n\n")

        parts.append("## 📚 参考资源\n\n")
        parts.append("### 官方文档\n\n")
        parts.append(
            "- [Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)\n"
        )
        parts.append(
            "- [Claude Agent SDK (2025)](https://skywork.ai/blog/claude-agent-sdk-best-practices-ai-agents-2025/)\n"
        )
        parts.append(
            "- [Azure AI Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)\n\n"
        )

        parts.append("### 开源项目\n\n")
        parts.append("- [claude-flow](https://github.com/ruvnet/claude-flow)\n")
        parts.append("- [ccswarm](https://github.com/nwiizo/ccswarm)\n")
        parts.append("- [wshobson/agents](https://github.com/wshobson/agents)\n\n")

        parts.append("---\n\n")
        parts.append(f"**最后更新**: {now}\n")

        return "".join(parts)

    def generate_all(self):
        """生成所有文档"""
        print("🚀 开始生成 AI Council 开发资料文档...")

        # 1. 收集元数据
        print("\n📊 收集文档元数据...")
        metadata = self.collect_metadata()

        # 保存元数据
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, fp=f, ensure_ascii=False)
        print(f"✅ 元数据已保存: {metadata_file}")

        # 2. 生成索引页
        print("\n📚 生成索引文档...")
        index_content = self.generate_index()
        index_file = self.output_dir / "INDEX.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"✅ 索引已生成: {index_file}")

        # 3. 生成最佳实践
        print("\n🎯 生成 2025 最佳实践汇总...")
        bp_content = self.generate_best_practices_2025()
        if not bp_content.strip():
            raise RuntimeError("最佳实践内容为空，生成器已禁用或未正确生成。")
        bp_file = self.output_dir / "BEST_PRACTICES_2025.md"
        with open(bp_file, 'w', encoding='utf-8') as f:
            f.write(bp_content)
        print(f"✅ 最佳实践已生成: {bp_file}")

        # 4. 打印统计
        print("\n" + "="*60)
        print("📊 生成统计:")
        print(f"  - 总文档数: {metadata['stats']['total_docs']}")
        print(f"  - Prompts 模板: {metadata['stats']['prompts_count']}")
        print(f"  - Routines 脚本: {metadata['stats']['routines_count']}")
        print(f"  - 输出目录: {self.output_dir}")
        print("="*60)

        return {
            "metadata_file": str(metadata_file),
            "index_file": str(index_file),
            "best_practices_file": str(bp_file)
        }


if __name__ == "__main__":
    generator = CouncilDocsGenerator()
    results = generator.generate_all()

    print("\n✨ 文档生成完成！")
    print("\n📖 快速访问:")
    for name, path in results.items():
        print(f"  - {name}: {path}")
