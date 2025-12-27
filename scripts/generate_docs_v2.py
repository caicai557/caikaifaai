#!/usr/bin/env python3
"""
AI Council 开发资料文档生成器 v2
使用分段方式避免大字符串嵌套问题
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict


def collect_metadata(council_dir: Path) -> Dict:
    """收集文档元数据"""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "documents": {},
        "stats": {"total_docs": 0, "prompts_count": 0, "routines_count": 0},
    }

    for md_file in council_dir.glob("*.md"):
        metadata["documents"][md_file.name] = {
            "path": str(md_file),
            "size_kb": round(md_file.stat().st_size / 1024, 2),
            "modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
        }
        metadata["stats"]["total_docs"] += 1

    prompts_dir = council_dir / "prompts"
    if prompts_dir.exists():
        metadata["stats"]["prompts_count"] = len(list(prompts_dir.glob("*.md")))

    routines_dir = council_dir / "routines"
    if routines_dir.exists():
        metadata["stats"]["routines_count"] = len(list(routines_dir.glob("*.py")))

    return metadata


def generate_index() -> str:
    """生成索引文档"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parts = []
    parts.append(f"# AI Council 开发资料中心\n\n> 自动生成于 {now}\n\n")
    parts.append("## 📚 文档导航\n\n")
    parts.append("### 🎯 核心架构\n\n")
    parts.append("| 文档 | 说明 | 状态 |\n")
    parts.append("|------|------|------|\n")
    parts.append("| [AGENTS.md](../AGENTS.md) | Agent 治理宪法 | ✅ |\n")
    parts.append("| [CODEMAP.md](../../CODEMAP.md) | 项目代码地图 | ✅ |\n")
    parts.append("| [SOP.md](../SOP.md) | 六步自愈循环 SOP | ✅ |\n")
    parts.append("| [DECISIONS.md](../DECISIONS.md) | 架构决策日志 | ✅ |\n\n")

    parts.append("### 🔧 最佳实践\n\n")
    parts.append("| 文档 | 说明 |\n")
    parts.append("|------|------|\n")
    parts.append(
        "| [TOKEN_SAVING_PRACTICES.md](../TOKEN_SAVING_PRACTICES.md) | Token 优化 |\n"
    )
    parts.append("| [MCP_PHILOSOPHY.md](../MCP_PHILOSOPHY.md) | MCP 协议理念 |\n")
    parts.append(
        "| [MCP_BEST_PRACTICES.md](../MCP_BEST_PRACTICES.md) | MCP 实操指南 |\n\n"
    )

    parts.append("### 🤖 模型专用指南\n\n")
    parts.append("| 文档 | 目标模型 |\n")
    parts.append("|------|----------|\n")
    parts.append("| [CLAUDE.md](../CLAUDE.md) | Claude Opus 4.5 |\n")
    parts.append("| [CODEX.md](../CODEX.md) | Codex 5.2 |\n")
    parts.append("| [GEMINI.md](../GEMINI.md) | Gemini Pro/Flash |\n\n")

    parts.append("## 🚀 快速开始\n\n")
    parts.append("```bash\n")
    parts.append("# 验证门禁\n")
    parts.append("just verify\n\n")
    parts.append("# 六步流程\n")
    parts.append('/plan "需求"    # 1. PM 规划\n')
    parts.append('/audit "模块"   # 2. 架构审计\n')
    parts.append('/tdd "范围"     # 3. TDD\n')
    parts.append('/impl "范围"    # 4. 实现\n')
    parts.append("just verify      # 5. 裁决\n")
    parts.append("/review          # 6. 审查\n")
    parts.append("```\n\n")

    parts.append("## 🎯 模型路由策略\n\n")
    parts.append("| 模型 | 占比 | 场景 |\n")
    parts.append("|------|------|------|\n")
    parts.append("| Claude Opus 4.5 | 5% | 规划总控 |\n")
    parts.append("| Codex 5.2 | 10% | 代码审查 |\n")
    parts.append("| Gemini 3 Pro | 5% | 架构审计 |\n")
    parts.append("| Gemini 3 Flash | 80% | 快速实现 |\n\n")

    parts.append("---\n\n")
    parts.append(f"**最后更新**: {now}\n")

    return "".join(parts)


def generate_best_practices() -> str:
    """生成最佳实践文档"""
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


def main():
    """主函数"""
    print("🚀 开始生成 AI Council 开发资料文档...\n")

    council_dir = Path(".council")
    output_dir = council_dir / "docs"
    output_dir.mkdir(exist_ok=True)

    # 1. 收集元数据
    print("📊 收集文档元数据...")
    metadata = collect_metadata(council_dir)

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ 元数据: {metadata_file}")

    # 2. 生成索引
    print("\n📚 生成索引文档...")
    index_content = generate_index()
    index_file = output_dir / "INDEX.md"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)
    print(f"✅ 索引: {index_file}")

    # 3. 生成最佳实践
    print("\n🎯 生成最佳实践...")
    bp_content = generate_best_practices()
    bp_file = output_dir / "BEST_PRACTICES_2025.md"
    with open(bp_file, "w", encoding="utf-8") as f:
        f.write(bp_content)
    print(f"✅ 最佳实践: {bp_file}")

    # 4. 统计
    print("\n" + "=" * 60)
    print("📊 生成统计:")
    print(f"  - 总文档数: {metadata['stats']['total_docs']}")
    print(f"  - Prompts: {metadata['stats']['prompts_count']}")
    print(f"  - Routines: {metadata['stats']['routines_count']}")
    print(f"  - 输出目录: {output_dir}")
    print("=" * 60)

    print("\n✨ 文档生成完成！")
    print("\n📖 快速访问:")
    print(f"  - 索引: {index_file}")
    print(f"  - 最佳实践: {bp_file}")
    print(f"  - 元数据: {metadata_file}")


if __name__ == "__main__":
    main()
